"""EnvironDec (EPD International) adapter — the largest open PCR library.
Strategy (server-rendered HTML, no auth needed):
  1. Paginate /pcr-library?page=N  -> collect PCR detail URLs
  2. Each detail page yields: title, registration number, valid-until,
     UN CPC code, version text, and the PDF file-id (api.prod.environdec.com
     /api/v2/EPDLibrary/Files/{id}/Data)
Returns list of dicts; downloader (P2) fetches the PDFs.
"""
import re, time, requests
from html import unescape

BASE = "https://www.environdec.com"
LISTING = BASE + "/pcr-library"
HEADERS = {"User-Agent": "Mozilla/5.0 (PCRbase research harvester; contact: nickgogerty)"}

PCR_LINK_RE = re.compile(r'href="(/pcr-library/(?:pcr[0-9]|pcr_)[^"#?]*)"')
FILE_ID_RE  = re.compile(r'api\.prod\.environdec\.com/api/v2/EPDLibrary/Files/([0-9a-f-]{36})/Data')
TITLE_RE    = re.compile(r'<h1[^>]*>([^<]+)</h1>')
# Registration number rendered after a label; allow markup between label and value
REGNO_RE    = re.compile(r'Registration number[^0-9A-Za-z]{0,40}((?:PCR\s*)?\d{4}[:\-]\d{2,3}[A-Za-z0-9 .:\-/]{0,20})', re.I)
VALID_RE    = re.compile(r'Valid until[^0-9]{0,20}(\d{4}-\d{2}-\d{2})')
CPC_RE      = re.compile(r'UN CPC\s*([0-9]{3,5})')
VERSION_RE  = re.compile(r'[Vv]ersion\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)')
# Canonical PCR number from the detail URL slug, e.g. /pcr-library/pcr2019-11 -> 2019:11
URLNUM_RE   = re.compile(r'/pcr-library/pcr(\d{4})-(\d{2,3})')

def classify_type(url, title):
    t = (title or "").lower()
    u = url.lower()
    if "c-pcr" in u or "c-pcr" in t or "c-pcr" in t.replace(" ", ""):
        return "cpcr"
    if "sub-pcr" in u or "sub-pcr" in t:
        return "subpcr"
    return "pcr"

def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return None

def list_detail_urls(max_pages=25):
    urls = set()
    for page in range(1, max_pages + 1):
        html = get(f"{LISTING}?page={page}")
        if not html:
            continue
        found = PCR_LINK_RE.findall(html)
        for f in found:
            urls.add(BASE + f)
        if not found:
            break
        time.sleep(0.5)
    return sorted(urls)

def parse_detail(url):
    html = get(url)
    if not html:
        return None
    def first(rx):
        m = rx.search(html)
        return unescape(m.group(1).strip()) if m else None
    file_ids = list(dict.fromkeys(FILE_ID_RE.findall(html)))
    title = first(TITLE_RE)
    # Canonical number from URL slug (reliable), fall back to label regex
    um = URLNUM_RE.search(url)
    pcr_number = f"{um.group(1)}:{um.group(2)}" if um else first(REGNO_RE)
    return {
        "operator_id": "environdec",
        "detail_url": url,
        "title": title,
        "pcr_number": pcr_number,
        "pcr_type": classify_type(url, title),
        "valid_until": first(VALID_RE),
        "cpc_code": first(CPC_RE),
        "version_label": first(VERSION_RE),
        "pdf_file_id": file_ids[0] if file_ids else None,
        "pdf_url": (f"https://api.prod.environdec.com/api/v2/EPDLibrary/Files/{file_ids[0]}/Data"
                    if file_ids else None),
        "all_file_ids": file_ids,
    }

def harvest(max_pages=25, limit=None):
    urls = list_detail_urls(max_pages)
    print(f"[environdec] found {len(urls)} PCR detail URLs")
    if limit:
        urls = urls[:limit]
    out = []
    for i, u in enumerate(urls, 1):
        d = parse_detail(u)
        if d:
            out.append(d)
        if i % 10 == 0:
            print(f"[environdec] parsed {i}/{len(urls)}")
        time.sleep(0.3)
    return out

if __name__ == "__main__":
    import json, sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    recs = harvest(max_pages=2, limit=lim)
    print(json.dumps(recs, indent=2)[:3000])
