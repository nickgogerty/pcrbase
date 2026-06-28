"""EPD Norge adapter — reads the captured NPCR register (EN15804, Norwegian program).
The register page (epd-global.com/pcr/epd-norges-pcr-register/) is JS-rendered;
the harvested register snapshot lives in epdnorge_register.json. Re-snapshot via
browser console for refresh (see harvest_health). PDFs download direct (no auth).
"""
import os, json, re

HERE = os.path.dirname(__file__)
REGISTER = os.path.join(HERE, "epdnorge_register.json")

NUM_RE = re.compile(r'N?C?PCR[\s_-]*(\d{3})', re.I)
VER_RE = re.compile(r':?\s*(\d{4})\b')
EVNUM_RE = re.compile(r'(EPDCN-PCR-\d+)', re.I)

def _ddmmyyyy_to_iso(s):
    if not s: return None
    m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', s)
    if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # year-only or unparseable -> None (DATE column needs full YYYY-MM-DD)
    return None

def classify_type(title):
    t = title.lower()
    if "part a" in t: return "subpcr"   # Part A = general core rules
    if "c-pcr" in t: return "cpcr"
    return "pcr"

def harvest(max_pages=None, limit=None):
    with open(REGISTER) as f:
        reg = json.load(f)
    out = []
    for r in reg:
        title = r["title"]
        num_m = NUM_RE.search(title) or EVNUM_RE.search(title)
        pcr_number = num_m.group(0) if num_m else title[:20]
        ver_m = VER_RE.search(title)
        out.append({
            "operator_id": "epd-norge",
            "detail_url": "https://www.epd-global.com/pcr/epd-norges-pcr-register/",
            "title": title,
            "pcr_number": pcr_number.upper().replace("  ", " "),
            "pcr_type": classify_type(title),
            "valid_until": _ddmmyyyy_to_iso(r.get("val")),
            "cpc_code": None,
            "version_label": ver_m.group(1) if ver_m else None,
            "pdf_url": r["href"],
            "pdf_file_id": None,
            "all_file_ids": [],
            "language": "no",
            "method_family": "EN15804",
        })
    if limit:
        out = out[:limit]
    print(f"[epd-norge] {len(out)} NPCRs from register")
    return out

if __name__ == "__main__":
    import json as _j
    recs = harvest(limit=5)
    print(_j.dumps(recs, indent=2, ensure_ascii=False)[:1500])
