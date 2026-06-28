#!/usr/bin/env python3
"""
Generate static JSON API files for PCRbase GitHub Pages.
Output: docs/api/v1/{pcrs,operators,stats,search-index}.json
        docs/api/v1/by-method/{iso14067,en15804,pef}.json
        docs/api/v1/by-operator/{environdec,...}.json
        docs/api/v1/requirements/clause-summary.json
"""
import sys, os, json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "docs", "api", "v1")

def mkdirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ {os.path.relpath(path, ROOT)}")

def run():
    c = get_con()
    mkdirs(
        OUT,
        os.path.join(OUT, "by-method"),
        os.path.join(OUT, "by-operator"),
        os.path.join(OUT, "requirements"),
    )

    # ── 1. All PCRs ─────────────────────────────────────────────────────────
    rows = c.execute("""
        SELECT
            p.pcr_id, p.operator_id, p.pcr_number, p.title,
            p.pcr_type, p.method_family, p.sector, p.cpc_code, p.geography,
            COUNT(DISTINCT v.version_id) AS version_count,
            MAX(CASE WHEN s.version_id IS NOT NULL THEN 1 ELSE 0 END) AS has_pdf,
            MAX(v.valid_until::VARCHAR) AS valid_until_latest,
            MAX(v.source_url)          AS source_url_latest
        FROM pcr p
        JOIN pcr_version v ON v.pcr_id = p.pcr_id
        LEFT JOIN source_document s ON s.version_id = v.version_id
        GROUP BY p.pcr_id, p.operator_id, p.pcr_number, p.title,
                 p.pcr_type, p.method_family, p.sector, p.cpc_code, p.geography
        ORDER BY p.operator_id, p.pcr_id
    """).fetchall()

    cols = ["pcr_id","operator_id","pcr_number","title","pcr_type","method_family",
            "sector","cpc_code","geography","version_count","has_pdf",
            "valid_until_latest","source_url_latest"]

    all_pcrs = [dict(zip(cols, [str(x) if x is not None else None for x in r])) for r in rows]
    for p in all_pcrs:
        p["has_pdf"] = bool(int(p["has_pdf"] or 0))

    write(os.path.join(OUT, "pcrs.json"), all_pcrs)

    # ── 2. Operators ─────────────────────────────────────────────────────────
    op_rows = c.execute("""
        SELECT p.operator_id,
               COUNT(DISTINCT p.pcr_id)         AS pcr_count,
               COUNT(DISTINCT s.doc_id)          AS pdf_count,
               STRING_AGG(DISTINCT p.method_family, ',') AS method_families
        FROM pcr p
        LEFT JOIN pcr_version v ON v.pcr_id = p.pcr_id
        LEFT JOIN source_document s ON s.version_id = v.version_id
        GROUP BY p.operator_id
        ORDER BY pcr_count DESC
    """).fetchall()

    operators = []
    for r in op_rows:
        operators.append({
            "operator_id": r[0],
            "pcr_count":   int(r[1]),
            "pdf_count":   int(r[2]),
            "method_families": [x for x in (r[3] or "").split(",") if x],
        })
    write(os.path.join(OUT, "operators.json"), operators)

    # ── 3. By method ─────────────────────────────────────────────────────────
    method_map = {"ISO14067": "iso14067", "EN15804": "en15804", "PEF": "pef"}
    for method, slug in method_map.items():
        subset = [p for p in all_pcrs if p["method_family"] == method]
        write(os.path.join(OUT, "by-method", f"{slug}.json"), subset)

    # ── 4. By operator ───────────────────────────────────────────────────────
    for op in [r[0] for r in op_rows]:
        subset = [p for p in all_pcrs if p["operator_id"] == op]
        slug = op.lower().replace(" ", "-")
        write(os.path.join(OUT, "by-operator", f"{slug}.json"), subset)

    # ── 5. Search index ──────────────────────────────────────────────────────
    index = []
    for p in all_pcrs:
        tokens = " ".join(filter(None, [
            (p.get("title") or "").lower(),
            (p.get("operator_id") or "").lower(),
            (p.get("method_family") or "").lower(),
            (p.get("cpc_code") or "").lower(),
            (p.get("pcr_type") or "").lower(),
            (p.get("geography") or "").lower(),
            (p.get("pcr_number") or "").lower(),
        ]))
        index.append({
            "pcr_id":       p["pcr_id"],
            "operator_id":  p["operator_id"],
            "title":        p["title"],
            "pcr_type":     p["pcr_type"],
            "method_family":p["method_family"],
            "cpc_code":     p["cpc_code"],
            "has_pdf":      p["has_pdf"],
            "source_url":   p["source_url_latest"],
            "tokens":       tokens,
        })
    write(os.path.join(OUT, "search-index.json"), index)

    # ── 6. Stats ─────────────────────────────────────────────────────────────
    total_pcrs    = c.execute("SELECT COUNT(*) FROM pcr").fetchone()[0]
    total_pdfs    = c.execute("SELECT COUNT(*) FROM source_document").fetchone()[0]
    total_reqs    = c.execute("SELECT COUNT(*) FROM requirement").fetchone()[0]
    total_ops     = c.execute("SELECT COUNT(DISTINCT operator_id) FROM pcr").fetchone()[0]

    by_method = {r[0]: int(r[1]) for r in c.execute(
        "SELECT method_family, COUNT(*) FROM pcr GROUP BY 1").fetchall() if r[0]}
    by_type   = {r[0]: int(r[1]) for r in c.execute(
        "SELECT pcr_type, COUNT(*) FROM pcr GROUP BY 1").fetchall() if r[0]}
    by_op     = {r[0]: int(r[1]) for r in c.execute(
        "SELECT operator_id, COUNT(*) FROM pcr GROUP BY 1 ORDER BY 2 DESC").fetchall()}

    # COMET mapping
    comet = {r[0]: int(r[1]) for r in c.execute(
        "SELECT mapping_status, COUNT(*) FROM comet_mapping GROUP BY 1").fetchall()}

    stats = {
        "total_pcrs":        int(total_pcrs),
        "total_pdfs":        int(total_pdfs),
        "total_requirements":int(total_reqs),
        "total_operators":   int(total_ops),
        "by_method":         by_method,
        "by_type":           by_type,
        "by_operator":       by_op,
        "comet_mapping":     comet,
        "generated_at":      datetime.now(timezone.utc).isoformat(),
    }
    write(os.path.join(OUT, "stats.json"), stats)

    # ── 7. Clause summary ────────────────────────────────────────────────────
    groups = c.execute("""
        SELECT clause_group, COUNT(*) AS n FROM requirement GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()

    clause_summary = []
    for grp, cnt in groups:
        top_keys = c.execute("""
            SELECT clause_key, COUNT(*) AS n FROM requirement
            WHERE clause_group = ? GROUP BY 1 ORDER BY 2 DESC LIMIT 5
        """, [grp]).fetchall()
        clause_summary.append({
            "clause_group": grp,
            "count": int(cnt),
            "top_keys": [{"clause_key": r[0], "count": int(r[1])} for r in top_keys],
        })
    write(os.path.join(OUT, "requirements", "clause-summary.json"), clause_summary)

    c.close()

    files_written = 4 + len(method_map) + len(operators) + 2
    print(f"\n✅  {files_written} files written to docs/api/v1/")
    print(f"    PCRs: {total_pcrs} | PDFs: {total_pdfs} | Reqs: {total_reqs} | Operators: {total_ops}")

if __name__ == "__main__":
    run()
