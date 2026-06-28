"""Bottom-up clause-vocabulary validation across programs (panel hybrid approach).
Compares the top-down seed vocab (v1-seed) against what the LLM extractor actually
found across operators / method families. Surfaces:
  - clause_key coverage per operator (which seed keys are real & used)
  - seed keys NEVER observed (candidates to prune or that need better anchors)
  - 'unclassified' captures (candidates to PROMOTE into new keys, amendment A1)
  - method_family skew (PEF vs EN15804 vs ISO14067 specific clauses)
This is the artifact that drives the vocab_version bump.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con
import clause_vocab

def main():
    con = get_con()
    seed_keys = {c[0] for c in clause_vocab.CLAUSES}
    print("="*68)
    print("BOTTOM-UP VOCAB VALIDATION  (seed = v1-seed, %d keys)" % len(seed_keys))
    print("="*68)

    # only LLM-extracted requirements (backend tagged in extract_run_id)
    rows = con.execute("""
        SELECT clause_key, count(*) n, count(DISTINCT version_id) docs,
               avg(confidence) conf, sum(CASE WHEN span_verified THEN 1 ELSE 0 END) verif
        FROM requirement WHERE extract_run_id LIKE 'extract-llm%'
        GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()
    observed = {r[0] for r in rows}

    print("\n--- Coverage by clause (LLM extractions) ---")
    print(f"{'clause_key':28} {'hits':>5} {'docs':>5} {'avgConf':>8} {'span✓':>6}")
    for ck, n, docs, conf, verif in rows:
        flag = " *UNCLASSIFIED*" if ck == "unclassified" else ("" if ck in seed_keys else " *NEW*")
        print(f"{ck:28} {n:5} {docs:5} {conf:8.2f} {verif:6}{flag}")

    print("\n--- Seed keys NEVER observed (prune candidates / weak signal) ---")
    never = sorted(seed_keys - observed - {"unclassified"})
    print(f"  {len(never)} of {len(seed_keys)} seed keys unobserved:")
    for k in never:
        print("   -", k)

    print("\n--- Per-operator clause coverage (breadth across programs) ---")
    op_rows = con.execute("""
        SELECT p.operator_id, p.method_family,
               count(DISTINCT r.clause_key) keys, count(*) reqs,
               count(DISTINCT r.version_id) docs
        FROM requirement r
        JOIN pcr_version v ON r.version_id=v.version_id
        JOIN pcr p ON v.pcr_id=p.pcr_id
        WHERE r.extract_run_id LIKE 'extract-llm%'
        GROUP BY 1,2 ORDER BY 4 DESC
    """).fetchall()
    print(f"{'operator':14} {'method':10} {'keys':>5} {'reqs':>5} {'docs':>5}")
    for op, mf, keys, reqs, docs in op_rows:
        print(f"{op:14} {mf or '?':10} {keys:5} {reqs:5} {docs:5}")

    print("\n--- Clauses seen in MULTIPLE method families (cross-program robust) ---")
    cross = con.execute("""
        SELECT clause_key, count(DISTINCT p.method_family) fams,
               string_agg(DISTINCT p.method_family, ',') famlist
        FROM requirement r
        JOIN pcr_version v ON r.version_id=v.version_id
        JOIN pcr p ON v.pcr_id=p.pcr_id
        WHERE r.extract_run_id LIKE 'extract-llm%'
        GROUP BY 1 HAVING count(DISTINCT p.method_family) > 1
        ORDER BY 2 DESC LIMIT 20
    """).fetchall()
    for ck, fams, famlist in cross:
        print(f"  {ck:28} {fams} families: {famlist}")
    con.close()

if __name__ == "__main__":
    main()
