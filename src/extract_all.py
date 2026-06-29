"""P3 driver — extract clauses from downloaded PDFs into requirement table.
Backend selectable: 'llm' (Haiku 4.5, default) or 'regex' (deterministic).
Pulls per-version method_family from the pcr table (set by harvest).

PACING THROTTLE (added after a thermal-runaway shutdown):
  - --sleep N  : seconds to pause between documents (default 2.0)
  - --cooldown : every COOLDOWN_EVERY docs, take a longer COOLDOWN_SECS pause
  - thermal guard: on macOS, polls `pmset -g therm` / CPU pressure and pauses
    if the system reports thermal pressure, so a long run can't peg the CPU.
Defaults are conservative; pass --sleep 0 to disable for short runs.
"""
import sys, os, hashlib, datetime, time, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# pacing defaults (seconds)
DEFAULT_SLEEP = 2.0          # pause between docs
COOLDOWN_EVERY = 25          # every N docs ...
COOLDOWN_SECS = 30.0         # ... take a longer breather
THERMAL_POLL_EVERY = 10      # check thermal pressure every N docs


def _thermal_pressure() -> str:
    """Return macOS thermal state: 'nominal' | 'pressure' | 'unknown'.

    Two signals (either trips 'pressure'):
      1. `pmset -g therm` CPU_Speed_Limit < 100  → OS is already throttling.
      2. 1-minute load average > 2x core count   → sustained heavy CPU, a
         proactive proxy that fires BEFORE the OS throttles (the reactive
         pmset line only appears once throttling has begun).
    On non-macOS or any error, returns 'unknown' (no-op).
    """
    if sys.platform != "darwin":
        return "unknown"
    # signal 1 — OS thermal throttle (reactive)
    try:
        out = subprocess.run(["pmset", "-g", "therm"], capture_output=True,
                             text=True, timeout=5).stdout
        for line in out.splitlines():
            if "CPU_Speed_Limit" in line:
                val = int("".join(ch for ch in line.split("=")[-1] if ch.isdigit()) or "100")
                if val < 100:
                    return "pressure"
    except Exception:
        pass
    # signal 2 — sustained load (proactive)
    try:
        load1 = os.getloadavg()[0]
        ncpu = os.cpu_count() or 4
        if load1 > 2.0 * ncpu:
            return "pressure"
    except Exception:
        pass
    return "nominal" if sys.platform == "darwin" else "unknown"


def _thermal_guard(verbose=True):
    """Block until thermal pressure clears (max ~5 min), with backoff."""
    waited = 0.0
    while _thermal_pressure() == "pressure" and waited < 300:
        if verbose:
            print(f"  ⏸ thermal pressure detected — cooling down 20s (waited {waited:.0f}s)")
        time.sleep(20)
        waited += 20


def _get_extractor(backend):
    if backend == "regex":
        import extract as ex
    else:
        import extract_llm as ex
    return ex


def run(run_id=None, backend="llm", limit=None, operator=None,
        sleep_between=DEFAULT_SLEEP, cooldown_every=COOLDOWN_EVERY,
        cooldown_secs=COOLDOWN_SECS):
    run_id = run_id or f"extract-{backend}-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    ex = _get_extractor(backend)
    con = get_con()
    q = """SELECT d.doc_id, d.version_id, d.blob_path, p.method_family
           FROM source_document d
           JOIN pcr_version v ON d.version_id=v.version_id
           JOIN pcr p ON v.pcr_id=p.pcr_id
           WHERE d.mime='application/pdf'"""
    params = []
    if operator:
        q += " AND p.operator_id=?"; params.append(operator)
    docs = con.execute(q, params).fetchall()
    if limit:
        docs = docs[:limit]
    n_req = n_docs_done = 0
    for doc_id, version_id, blob_path, method_family in docs:
        if not os.path.exists(blob_path):
            continue
        if con.execute("SELECT 1 FROM requirement WHERE version_id=? LIMIT 1", [version_id]).fetchone():
            continue
        # ── thermal guard (periodic) ──────────────────────────────────────
        if backend == "llm" and n_docs_done and n_docs_done % THERMAL_POLL_EVERY == 0:
            _thermal_guard()
        try:
            recs = ex.extract_clauses(blob_path)
        except Exception as e:
            print(f"  ! extract failed {version_id}: {e}")
            # still pace after a failure so a tight error loop can't spin the CPU
            if sleep_between:
                time.sleep(sleep_between)
            continue
        for r in recs:
            req_id = "req-" + hashlib.md5(f"{version_id}|{r['clause_key']}|{r['source_page']}|{r['value_text'][:30]}".encode()).hexdigest()[:14]
            review = "needs_review" if (r["conf_bucket"] == "low" or not r["span_verified"]) else "unreviewed"
            # Properly separate original-language text from English translation:
            #   value_text_orig = verbatim source quote in original language (may be JA, NO, DE, etc.)
            #   value_text_en   = English value/translation from LLM (or same as orig if already EN)
            value_orig = r.get("value_text_orig") or r.get("value_text") or ""
            value_en   = r.get("value_text_en")   or r.get("value_text") or value_orig
            con.execute(
                """INSERT OR REPLACE INTO requirement
                (req_id, version_id, clause_group, clause_key, clause_vocab_version,
                 value_text_orig, value_text_en, normalized_value, applicable, confidence,
                 conf_bucket, source_page, source_span, span_verified, method_family,
                 extract_run_id, review_status, _run_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [req_id, version_id, r["clause_key"].split(".")[0], r["clause_key"], "v1-seed",
                 value_orig, value_en, r["normalized_value"], True, r["confidence"],
                 r["conf_bucket"], r["source_page"], r["source_span"], r["span_verified"],
                 method_family or "ISO14067", run_id, review, run_id])
            n_req += 1
        n_docs_done += 1
        print(f"  · {version_id}: {len(recs)} clauses")
        # ── pacing throttle ───────────────────────────────────────────────
        if sleep_between:
            time.sleep(sleep_between)
        if cooldown_every and n_docs_done % cooldown_every == 0:
            print(f"  ⏸ cooldown {cooldown_secs:.0f}s after {n_docs_done} docs")
            time.sleep(cooldown_secs)
    con.close()
    print(f"[{run_id}] extracted {n_req} requirements from {n_docs_done} new documents "
          f"(backend={backend}, sleep={sleep_between}s, cooldown={cooldown_secs}s/{cooldown_every})")
    return run_id


def _parse_kwargs(argv):
    """Parse positional [backend] [limit] [operator] + --sleep/--cooldown/--cooldown-every."""
    pos, kw = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--sleep":
            kw["sleep_between"] = float(argv[i + 1]); i += 2
        elif a == "--cooldown":
            kw["cooldown_secs"] = float(argv[i + 1]); i += 2
        elif a == "--cooldown-every":
            kw["cooldown_every"] = int(argv[i + 1]); i += 2
        else:
            pos.append(a); i += 1
    return pos, kw


if __name__ == "__main__":
    pos, kw = _parse_kwargs(sys.argv[1:])
    backend = pos[0] if len(pos) > 0 else "llm"
    lim = int(pos[1]) if len(pos) > 1 else None
    op = pos[2] if len(pos) > 2 else None
    run(backend=backend, limit=lim, operator=op, **kw)
