"""PCRbase schema — DuckDB system-of-record.
Append-only, uni-temporal version lineage (panel amendment A5).
Every row carries _loaded_at / _run_id. Corrections = new rows, never updates.
"""
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "pcrbase.duckdb")

DDL = """
-- ── Operators (the known-universe registry) ──────────────────────────
CREATE TABLE IF NOT EXISTS operator (
    operator_id     VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    country         VARCHAR,
    region          VARCHAR,
    listing_url     VARCHAR,
    adapter_type    VARCHAR,   -- sitemap | html | api | manual
    access          VARCHAR,   -- open | gated
    language        VARCHAR,
    program_standard VARCHAR,  -- ISO14025 | EN15804 | PEF | mixed
    notes           VARCHAR,
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── PCR identity (stable across versions) ────────────────────────────
CREATE TABLE IF NOT EXISTS pcr (
    pcr_id          VARCHAR PRIMARY KEY,
    operator_id     VARCHAR REFERENCES operator(operator_id),
    pcr_number      VARCHAR,
    title           VARCHAR,
    pcr_type        VARCHAR,   -- pcr | cpcr | subpcr | pefcr
    method_family   VARCHAR,   -- ISO14067 | EN15804 | PEF | other
    sector          VARCHAR,
    cpc_code        VARCHAR,
    geography       VARCHAR,
    first_seen      TIMESTAMP DEFAULT now(),
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── PCR version (the unit of versioning) ─────────────────────────────
CREATE TABLE IF NOT EXISTS pcr_version (
    version_id      VARCHAR PRIMARY KEY,
    pcr_id          VARCHAR REFERENCES pcr(pcr_id),
    version_label   VARCHAR,
    valid_from      DATE,
    valid_until     DATE,
    superseded_by   VARCHAR,
    content_hash    VARCHAR,
    source_url      VARCHAR,
    retrieved_at    TIMESTAMP,
    access_status   VARCHAR,   -- ingested | gated | failed
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── Source documents (blob + provenance) ─────────────────────────────
CREATE TABLE IF NOT EXISTS source_document (
    doc_id          VARCHAR PRIMARY KEY,
    version_id      VARCHAR REFERENCES pcr_version(version_id),
    blob_path       VARCHAR,
    mime            VARCHAR,
    lang            VARCHAR,
    pages           INTEGER,
    sha256          VARCHAR,
    retrieved_at    TIMESTAMP,
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── Clause vocabulary (the comparability backbone; versioned A1) ─────
CREATE TABLE IF NOT EXISTS clause_vocab (
    clause_key          VARCHAR,
    clause_group        VARCHAR,
    label               VARCHAR,
    pcr_native_altlabels VARCHAR,
    applicable_to       VARCHAR,   -- comma list of pcr_type/method_family
    vocab_version       VARCHAR,
    _loaded_at          TIMESTAMP DEFAULT now(),
    PRIMARY KEY (clause_key, vocab_version)
);

-- ── Requirements (one extracted clause instance) ─────────────────────
CREATE TABLE IF NOT EXISTS requirement (
    req_id          VARCHAR PRIMARY KEY,
    version_id      VARCHAR REFERENCES pcr_version(version_id),
    clause_group    VARCHAR,
    clause_key      VARCHAR,
    clause_vocab_version VARCHAR,
    value_text_orig VARCHAR,
    value_text_en   VARCHAR,
    normalized_value VARCHAR,
    applicable      BOOLEAN,
    confidence      DOUBLE,
    conf_bucket     VARCHAR,    -- high | med | low
    source_page     INTEGER,
    source_span     VARCHAR,
    span_verified   BOOLEAN,    -- amendment A4
    method_family   VARCHAR,
    extract_run_id  VARCHAR,
    review_status   VARCHAR DEFAULT 'unreviewed',
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── COMET mapping ledger ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comet_mapping (
    map_id          VARCHAR PRIMARY KEY,
    clause_key      VARCHAR,
    comet_target    VARCHAR,
    target_kind     VARCHAR,    -- class | property | shacl
    mapping_status  VARCHAR,    -- exact | extended | lossy | unmapped
    mapping_confidence DOUBLE,
    rationale       VARCHAR,
    shacl_snippet   VARCHAR,
    reviewer        VARCHAR,
    reviewed_at     TIMESTAMP,
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── Gap log (the upstream COMET PR backlog) ──────────────────────────
CREATE TABLE IF NOT EXISTS gap_log (
    gap_id          VARCHAR PRIMARY KEY,
    clause_key      VARCHAR,
    description     VARCHAR,
    proposed_comet_addition VARCHAR,
    occurrence_count INTEGER,
    pr_status       VARCHAR DEFAULT 'open',
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── Review queue ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS review_queue (
    item_ref        VARCHAR,
    item_type       VARCHAR,    -- requirement | mapping
    reason          VARCHAR,
    priority        INTEGER,
    assigned        VARCHAR,
    resolved        BOOLEAN DEFAULT FALSE,
    _loaded_at      TIMESTAMP DEFAULT now(),
    _run_id         VARCHAR
);

-- ── Harvest health (per-adapter watchdog; amendment A8) ──────────────
CREATE TABLE IF NOT EXISTS harvest_health (
    run_id          VARCHAR,
    operator_id     VARCHAR,
    expected_count  INTEGER,
    found_count     INTEGER,
    delta_pct       DOUBLE,
    alert           BOOLEAN,
    ts              TIMESTAMP DEFAULT now()
);
"""

def get_con(db_path=DB_PATH):
    return duckdb.connect(db_path)

def init_db(db_path=DB_PATH):
    con = get_con(db_path)
    con.execute(DDL)
    tables = con.execute("SELECT table_name FROM information_schema.tables ORDER BY table_name").fetchall()
    con.close()
    return [t[0] for t in tables]

if __name__ == "__main__":
    tables = init_db()
    print("Initialized pcrbase.duckdb with tables:")
    for t in tables:
        print("  -", t)
