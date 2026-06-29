"""PCRbase end-to-end pipeline runner.
Usage:
  python src/pipeline.py seed                          # load clause vocab + operators
  python src/pipeline.py harvest <operator> [limit] [pages]  # enumerate + download
       operators: environdec | epd-norge | manual
  python src/pipeline.py extract [backend] [limit] [operator]  # PDF -> requirements
       backend: llm (Haiku 4.5, default) | regex (deterministic)
  python src/pipeline.py map                           # requirements -> COMET ledger + gap_log
  python src/pipeline.py export                        # -> RDF/Turtle + JSON-LD
  python src/pipeline.py validate                      # bottom-up vocab validation report
  python src/pipeline.py dashboard                     # generate HTML dashboard
  python src/pipeline.py status                        # dashboard
  python src/pipeline.py all [limit]                   # environdec seed->...->status
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd in ("seed", "all"):
        import load_seed; load_seed.main()
    if cmd == "harvest":
        import harvest
        op = sys.argv[2] if len(sys.argv) > 2 else "environdec"
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
        pages = int(sys.argv[4]) if len(sys.argv) > 4 else 25
        harvest.run_adapter(op, max_pages=pages, limit=lim)
    if cmd == "all":
        import harvest
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        harvest.run_adapter("environdec", max_pages=25, limit=lim)
    if cmd in ("extract", "all"):
        import extract_all
        backend = sys.argv[2] if (cmd == "extract" and len(sys.argv) > 2) else "llm"
        lim = int(sys.argv[3]) if (cmd == "extract" and len(sys.argv) > 3) else None
        op = sys.argv[4] if (cmd == "extract" and len(sys.argv) > 4) else None
        extract_all.run(backend=backend, limit=lim, operator=op)
    if cmd in ("map", "all"):
        import map_comet; map_comet.run()
    if cmd in ("export", "all"):
        import export_graph
        export_graph.export_turtle(); export_graph.export_jsonld()
    if cmd == "validate":
        import validate_vocab; validate_vocab.main()
    if cmd in ("coverage", "all"):
        import coverage; coverage.main()
    if cmd in ("dashboard", "all"):
        import dashboard; dashboard.build()
        import shutil, os
        shutil.copy(os.path.join(os.path.dirname(__file__),"../data/exports/dashboard.html"),
                    os.path.join(os.path.dirname(__file__),"../docs/dashboard.html"))
    if cmd in ("api", "all"):
        import generate_static_api; generate_static_api.run()
    if cmd in ("migrate", "all"):
        import migrate_multilingual; migrate_multilingual.run()
    if cmd in ("status", "all"):
        import status; status.main()

if __name__ == "__main__":
    main()
