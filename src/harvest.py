"""P1 enumeration + P2 acquisition pipeline.
Harvest an operator's PCR listing into pcr / pcr_version / source_document,
download open PDFs to data/blobs, record provenance + harvest health (A8).
"""
import sys, os, hashlib, time, uuid, datetime, requests
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con
from adapters import environdec, epdnorge, manual_registry, sumpo

# adapter registry: operator -> module with .harvest(max_pages, limit)
ADAPTERS = {
    "environdec": environdec,
    "epd-norge": epdnorge,
    "manual": manual_registry,
    "sumpo": sumpo,
}
# default method_family per operator (overridable per-record)
OP_METHOD = {"environdec": "ISO14067", "epd-norge": "EN15804", "sumpo": "ISO14067"}

BLOB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "blobs")
HEADERS = {"User-Agent": "Mozilla/5.0 (PCRbase research harvester)"}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def pcr_id_for(operator_id, pcr_number, title):
    base = f"{operator_id}|{pcr_number or title}"
    return operator_id + "-" + hashlib.md5(base.encode()).hexdigest()[:12]

def download_pdf(url, dest):
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
    except requests.RequestException:
        pass
    return False

def run_adapter(operator, max_pages=25, limit=None, download=True):
    adapter = ADAPTERS[operator]
    run_id = f"{operator}-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(BLOB_DIR, exist_ok=True)
    if operator == "manual":
        recs = adapter.harvest(limit=limit)
    else:
        recs = adapter.harvest(max_pages=max_pages, limit=limit)
    con = get_con()
    n_pcr = n_ver = n_doc = n_pdf = 0
    for d in recs:
        pid = pcr_id_for(d["operator_id"], d.get("pcr_number"), d.get("title"))
        vid = pid + "-" + (d.get("version_label") or "v0").replace(".", "_")
        method = d.get("method_family") or OP_METHOD.get(d["operator_id"], "ISO14067")
        geo = d.get("geography") or ("Global" if d["operator_id"] == "environdec" else None)
        sector = d.get("sector") or None
        exists = con.execute("SELECT 1 FROM pcr WHERE pcr_id=?", [pid]).fetchone()
        if not exists:
            con.execute(
                "INSERT INTO pcr (pcr_id, operator_id, pcr_number, title, pcr_type, method_family, sector, cpc_code, geography, _run_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                [pid, d["operator_id"], d.get("pcr_number"), d.get("title"), d.get("pcr_type", "pcr"),
                 method, sector, d.get("cpc_code"), geo, run_id])
            n_pcr += 1
        # version
        vexists = con.execute("SELECT 1 FROM pcr_version WHERE version_id=?", [vid]).fetchone()
        if not vexists:
            access = "ingested" if d.get("pdf_url") else "failed"
            con.execute(
                "INSERT INTO pcr_version (version_id, pcr_id, version_label, valid_until, source_url, retrieved_at, access_status, _run_id) VALUES (?,?,?,?,?,?,?,?)",
                [vid, pid, d.get("version_label"), d.get("valid_until"), d.get("detail_url"),
                 datetime.datetime.now(), access, run_id])
            n_ver += 1
        # download
        if download and d.get("pdf_url"):
            dest = os.path.join(BLOB_DIR, vid + ".pdf")
            if not os.path.exists(dest):
                if download_pdf(d["pdf_url"], dest):
                    n_pdf += 1
                    sha = sha256_file(dest)
                    con.execute("UPDATE pcr_version SET content_hash=? WHERE version_id=?", [sha, vid])
                    did = "doc-" + hashlib.md5(dest.encode()).hexdigest()[:12]
                    if not con.execute("SELECT 1 FROM source_document WHERE doc_id=?", [did]).fetchone():
                        lang = d.get("language")
                        con.execute(
                            "INSERT INTO source_document (doc_id, version_id, blob_path, mime, lang, sha256, retrieved_at, _run_id) VALUES (?,?,?,?,?,?,?,?)",
                            [did, vid, dest, "application/pdf", lang, sha, datetime.datetime.now(), run_id])
                        n_doc += 1
            time.sleep(0.4)
    # harvest health (A8)
    found = len(recs)
    con.execute("INSERT INTO harvest_health (run_id, operator_id, expected_count, found_count, delta_pct, alert) VALUES (?,?,?,?,?,?)",
                [run_id, operator, None, found, None, found == 0])
    con.close()
    print(f"[run {run_id}] harvested {found} recs | +{n_pcr} pcr, +{n_ver} versions, +{n_pdf} pdfs, +{n_doc} docs")
    return run_id

# backwards-compatible alias
def run_environdec(max_pages=25, limit=None, download=True):
    return run_adapter("environdec", max_pages=max_pages, limit=limit, download=download)

if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "environdec"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    mp = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    run_adapter(op, max_pages=mp, limit=lim)
