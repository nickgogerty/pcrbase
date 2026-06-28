"""PCRbase status / coverage dashboard (success metrics, amendment A3)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

def main():
    con = get_con()
    def q(sql): return con.execute(sql).fetchall()
    print("="*64)
    print("PCRbase — STATUS")
    print("="*64)
    print("\nOperators (known universe):", q("SELECT count(*) FROM operator")[0][0],
          "| open:", q("SELECT count(*) FROM operator WHERE access='open'")[0][0],
          "| gated:", q("SELECT count(*) FROM operator WHERE access='gated'")[0][0])
    print("Clause vocab keys (v1-seed):", q("SELECT count(*) FROM clause_vocab")[0][0])
    print("\n--- Inventory ---")
    print("PCRs:", q("SELECT count(*) FROM pcr")[0][0],
          "| versions:", q("SELECT count(*) FROM pcr_version")[0][0],
          "| PDFs downloaded:", q("SELECT count(*) FROM source_document")[0][0])
    print("By pcr_type:", dict(q("SELECT pcr_type, count(*) FROM pcr GROUP BY 1")))
    print("\n--- Extraction (requirements) ---")
    print("Total:", q("SELECT count(*) FROM requirement")[0][0])
    print("By confidence bucket:", dict(q("SELECT conf_bucket, count(*) FROM requirement GROUP BY 1")))
    print("Span-verified:", q("SELECT count(*) FROM requirement WHERE span_verified")[0][0],
          "| needs review:", q("SELECT count(*) FROM requirement WHERE review_status='needs_review'")[0][0])
    print("\n--- COMET mapping ledger ---")
    for status, n in q("SELECT mapping_status, count(*) FROM comet_mapping GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {status:10} {n}")
    print("\n--- COMET PR backlog (gap_log, evidence-gated) ---")
    rows = q("SELECT clause_key, proposed_comet_addition, occurrence_count FROM gap_log ORDER BY occurrence_count DESC")
    for ck, add, occ in rows:
        gate = "PR-ready" if (occ or 0) >= 3 else "below-threshold"
        print(f"  [{occ:>3} occ | {gate:15}] {ck:22} -> {add}")
    print("\n--- Top extracted clauses (by frequency) ---")
    for ck, n in q("SELECT clause_key, count(*) FROM requirement GROUP BY 1 ORDER BY 2 DESC LIMIT 12"):
        print(f"  {n:>3}  {ck}")
    con.close()

if __name__ == "__main__":
    main()
