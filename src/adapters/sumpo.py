"""SuMPO EPD Japan adapter — ecoleaf-label.jp/en/pcr/

Program: SuMPO (Sustainable Management Promotion Organization)
Country: Japan  |  Language: Japanese (PDFs are _ja.pdf)
Standards: ISO21930:2007, ISO21930:2017, EN15804+A1, EN15804+A2
76 PCRs across 13 product fields. PDFs are publicly downloadable (no auth).

Strategy:
  1. Known listing of 76 detail-page IDs scraped 2026-06-29.
  2. Each detail page (/en/pcr/{id}) yields structured metadata via <dl>.
  3. PDF download link: href="/pcr/download/{download_id}" on the detail page.
  4. Download all PDFs (Japanese); LLM extractor handles JA→EN translation.

Returns list[dict] compatible with harvest.py P1/P2 pipeline.
"""

import re, time, hashlib, os
import requests
from bs4 import BeautifulSoup

OPERATOR_ID = "sumpo"
BASE        = "https://ecoleaf-label.jp"
HEADERS     = {
    "User-Agent": "Mozilla/5.0 (PCRbase research harvester; contact: nickgogerty@gmail.com)",
    "Accept-Language": "en-US,en;q=0.9",
}

# Full listing scraped 2026-06-29 — 76 PCRs
DETAIL_IDS = [
    78, 77, 68, 76, 75, 69, 74, 73, 72, 71,
     9, 24, 70, 25, 26, 67, 39, 66, 65, 64,
    63, 62, 47, 61, 60, 59, 42, 58, 46, 57,
     8, 28, 29, 31, 32, 33, 49, 35, 36, 37,
    38, 40, 41, 45, 43, 44, 48, 51, 50, 52,
    34, 55, 54, 18,  1,  2,  3,  4,  5,  6,
     7, 10, 11, 12, 13, 14, 15, 16, 17, 19,
    20, 21, 22, 27, 53, 30,
]

# Map SuMPO field labels → PCRbase sector strings
FIELD_MAP = {
    "Chemical products":                        "Chemical products",
    "Construction products":                    "Construction",
    "Electricity, steam & fuels":               "Energy",
    "Food & beverages":                         "Food & Beverages",
    "Furniture & other goods":                  "Furniture & Goods",
    "Infrastructure & buildings":               "Infrastructure",
    "Machinery & equipment":                    "Machinery & Equipment",
    "Metal, mineral, plastic & glass products": "Materials",
    "Paper and plastic products":               "Paper & Plastics",
    "Services":                                 "Services",
    "Textiles, footwear & apparel":             "Textiles",
    "Vehicles & transport equipment":           "Vehicles",
    "Others":                                   "Other",
}

def _method_family(standards: list[str]) -> str:
    """Infer method_family from compliance standards list."""
    s = " ".join(standards).upper()
    if "EN15804" in s or "EN 15804" in s:
        return "EN15804"
    # ISO21930 is the Japanese/international EPD standard — closest to ISO14067 family
    return "ISO14067"

def _pcr_type(pcr_number: str, title: str) -> str:
    t = (title or "").lower()
    n = (pcr_number or "").lower()
    if "core" in t or "core-pcr" in t:
        return "cpcr"
    if "sub-pcr" in t or "sub pcr" in n:
        return "subpcr"
    return "pcr"

def get(url: str, tries: int = 3) -> requests.Response | None:
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return None

def scrape_detail(page_id: int) -> dict | None:
    """Scrape one PCR detail page and return a harvest dict."""
    url = f"{BASE}/en/pcr/{page_id}"
    resp = get(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Metadata from <dl> ---
    dl = {}
    terms = soup.select("dl dt")
    defs  = soup.select("dl dd")
    for term, defn in zip(terms, defs):
        dl[term.get_text(strip=True)] = defn.get_text(" ", strip=True)

    pcr_number   = dl.get("PCR Registeration Number", "").strip()  # note: site typo
    status_raw   = dl.get("Status of Publication", "").strip()
    field_raw    = dl.get("Field", "").strip()
    pub_date_raw = dl.get("Publication Data", "").strip()  # site typo: "Data" not "Date"
    exp_date_raw = dl.get("Expiration Date", "").strip()
    standards_raw= dl.get("Additional Compliance Standards", "")

    # Title from <h2>
    h2 = soup.find("h2")
    title = h2.get_text(strip=True) if h2 else f"SuMPO PCR {page_id}"

    # Standards list
    standards = [s.strip() for s in re.split(r"[\n,;]+", standards_raw) if s.strip()]

    # PDF download links — latest and past
    pdf_links = []
    for section_h in soup.find_all("h3"):
        if "PCR" in section_h.get_text():
            ul = section_h.find_next("ul")
            if ul:
                for a in ul.find_all("a", href=re.compile(r"/pcr/download/")):
                    pdf_links.append({
                        "filename": a.get_text(strip=True),
                        "download_url": BASE + a["href"],
                    })

    # Latest is first in "Latest PCR" section
    latest_pdf = pdf_links[0] if pdf_links else None
    past_pdfs  = pdf_links[1:] if len(pdf_links) > 1 else []

    # Parse dates
    def parse_date(s):
        s = s.strip()
        m = re.match(r"(\d{4})/(\d{2})/(\d{2})", s)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            return s
        return None

    valid_from  = parse_date(pub_date_raw)
    valid_until = parse_date(exp_date_raw)
    is_valid    = "expired" not in status_raw.lower()
    access_status = "ingested" if latest_pdf else "gated"

    # Version label from PCR number (e.g. PA-SuMPO-PCR-01003-1-0-0 → 1.0.0)
    version_label = None
    vm = re.search(r"-(\d+)-(\d+)-(\d+)$", pcr_number)
    if vm:
        version_label = f"{vm.group(1)}.{vm.group(2)}.{vm.group(3)}"
    else:
        # Older format: PA-180000-AJ-08 → rev 08
        vm2 = re.search(r"-([A-Z]{2})-(\d+)$", pcr_number)
        version_label = f"rev{vm2.group(2)}" if vm2 else "1"

    return {
        "pcr_number":    pcr_number or f"SUMPO-{page_id}",
        "title":         title,
        "pcr_type":      _pcr_type(pcr_number, title),
        "method_family": _method_family(standards),
        "sector":        FIELD_MAP.get(field_raw, field_raw or None),
        "geography":     "Japan",
        "cpc_code":      None,  # SuMPO uses own classification codes not UN CPC
        "version_label": version_label,
        "valid_from":    valid_from,
        "valid_until":   valid_until,
        "source_url":    url,
        "pdf_url":       latest_pdf["download_url"] if latest_pdf else None,
        "pdf_filename":  latest_pdf["filename"] if latest_pdf else None,
        "access_status": access_status,
        "language":      "ja",
        "past_versions": past_pdfs,
        "standards":     standards,
        "is_valid":      is_valid,
        "_page_id":      page_id,
    }

def harvest(limit: int = 0, max_pages=None) -> list[dict]:
    """Main entry point for harvest.py. Returns list of PCR dicts."""
    ids = DETAIL_IDS[:limit] if limit else DETAIL_IDS
    results = []
    for i, page_id in enumerate(ids):
        print(f"  [{i+1}/{len(ids)}] scraping /en/pcr/{page_id} ...", end=" ", flush=True)
        rec = scrape_detail(page_id)
        if rec:
            print(f"✓ {rec['pcr_number']} — {rec['title'][:50]}")
            # Add operator_id and detail_url required by harvest.py
            rec["operator_id"] = OPERATOR_ID
            rec["detail_url"]  = rec["source_url"]
            results.append(rec)
        else:
            print(f"✗ failed")
        time.sleep(0.4)   # polite delay
    return results
