"""Load seed data: clause vocab + operator registry into pcrbase.duckdb."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schema import init_db, get_con
import clause_vocab
import operator_registry

def main(run_id="seed-load"):
    init_db()
    con = get_con()
    # clause vocab
    con.executemany(
        "INSERT OR REPLACE INTO clause_vocab (clause_key, clause_group, label, pcr_native_altlabels, applicable_to, vocab_version) VALUES (?,?,?,?,?,?)",
        clause_vocab.rows(run_id),
    )
    # operators
    con.executemany(
        "INSERT OR REPLACE INTO operator (operator_id, name, country, region, listing_url, adapter_type, access, language, program_standard, notes, _run_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        operator_registry.rows(run_id),
    )
    nv = con.execute("SELECT count(*) FROM clause_vocab").fetchone()[0]
    no = con.execute("SELECT count(*) FROM operator").fetchone()[0]
    con.close()
    print(f"Loaded {nv} clause keys, {no} operators.")

if __name__ == "__main__":
    main()
