"""Backfill source-document metadata: page counts (from the PDF) and the
implicit language where the harvester left it NULL. Idempotent; safe to re-run.

  - pages: opened via PyMuPDF, recorded once.
  - lang:  NULL → inferred from the operator (EnvironDec & EU-EF publish in EN;
           langs explicitly set by the Norge/IBU adapters are left untouched).
Run: python src/backfill_docmeta.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# operator → default publication language for docs the harvester left NULL
OP_DEFAULT_LANG = {"environdec": "en", "eu-ef": "en", "ibu": "de", "epd-norge": "no"}


def main():
    import fitz  # PyMuPDF
    con = get_con()
    rows = con.execute("""
        SELECT s.doc_id, s.blob_path, s.pages, s.lang, p.operator_id
        FROM source_document s
        JOIN pcr_version v ON v.version_id = s.version_id
        JOIN pcr p ON p.pcr_id = v.pcr_id
    """).fetchall()
    n_pages = n_lang = n_missing = 0
    for doc_id, blob, pages, lang, op in rows:
        # pages
        if pages is None and blob and os.path.exists(blob):
            try:
                with fitz.open(blob) as d:
                    pc = d.page_count
                con.execute("UPDATE source_document SET pages=? WHERE doc_id=?", [pc, doc_id])
                n_pages += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  ! page count failed for {doc_id}: {exc}", file=sys.stderr)
        elif blob and not os.path.exists(blob):
            n_missing += 1
        # lang
        if not lang:
            inferred = OP_DEFAULT_LANG.get(op)
            if inferred:
                con.execute("UPDATE source_document SET lang=? WHERE doc_id=?", [inferred, doc_id])
                n_lang += 1
    con.close()
    print(f"backfilled pages on {n_pages} docs, lang on {n_lang} docs; "
          f"{n_missing} blob(s) missing on disk")


if __name__ == "__main__":
    main()
