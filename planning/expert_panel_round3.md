# PCRbase Expert Panel — Round 3: Synthesis (unified proposal)

The five experts converge on a single architecture: **"Clause-level inventory, COMET-as-constraints, generated graph, living & versioned."**

## Unified thesis
A PCR is a *set of normative method requirements*. PCRbase decomposes every PCR version into ~120 controlled `clause_key` requirements, stores them in an append-only bitemporal DuckDB system-of-record with full provenance to source clause, maps each clause to COMET (as an existing class, a SHACL constraint on a class, or a newly-proposed core class), and **generates** the RDF/JSON-LD graph aligned to COMET from those tables. Ontology-touching mappings feed a gap log that becomes the upstream COMET PR backlog. The DB is built to live: quarterly re-harvest, content-hash diffing, immutable version history.

## Resolved design decisions
1. **One superset skeleton** with `applicable_to` flags (not separate schemas per PCR/PEFCR/c-PCR). — E1+E2
2. **Three mapping kinds**: instance-data→class, method-constraint→SHACL shape, administrative→new core class. "Mapping onto COMET" is mostly SHACL constraints, not instance triples. — E2
3. **PEF-specific additions (CFF, 16 EF indicators) go in a `comet-pcf` PEF sub-module**, not core L4 — keeps ISO-14067-anchored core coherent (resolves E5's Round-0 dissent about lossy PEF mapping). Linked via `owl:imports`.
4. **Keystone addition**: `comet-pcf:governedByPCR` linking a footprint to its PCR — the provenance edge COMET lacks entirely.
5. **Reify `PCRReference`→`PCRDocument`** as the structured, versioned anchor class.
6. **Generated graph only** (decision B): deterministic SQL→Turtle/JSON-LD exporter, one named graph per PCR version.
7. **Stratified human review** (decision C): 100% of extended/lossy mappings and low-confidence extractions; sampled high-confidence.
8. **Reuse-first namespace** (decision D): map to existing `comet-pcf:`/`comet-core:` first; new classes only where nothing fits; all prepared as upstream PRs (decision E).

## Unified build sequence (phases)
- **P0 Foundations** — repo at `~/Projects/pcrbase`, pin comet-ontology as dependency, DuckDB schema, clause_key controlled vocabulary (the skeleton), operator registry seed.
- **P1 Enumeration** — per-operator adapters; build the *known universe* of PCRs (incl. gated metadata-only). Deliverable: populated `operator`/`pcr`/`pcr_version` with counts.
- **P2 Acquisition** — download open PDFs to blob store w/ provenance; flag gated; language detect.
- **P3 Extraction** — PDF→text→LLM clause extraction into `requirement` with confidence+span; machine-translate non-English.
- **P4 COMET mapping** — clause_key→COMET ledger; SHACL shapes; gap_log; reuse-first.
- **P5 Graph generation** — SQL→Turtle/JSON-LD exporter, COMET @context, per-version named graphs, SHACL validation.
- **P6 QA & review** — stratified human sampling, confidence calibration, legibility check.
- **P7 COMET PRs** — package gap_log into upstream PRs (OWL Turtle + SHACL + labels per COMET Viz 10).
- **P8 Living ops** — quarterly re-harvest cron, content-hash diff, version lineage, dashboards.

## What each expert contributes to the synthesis
- E1 → the 120-key clause skeleton + applicable_to superset
- E2 → mapping kinds + concrete COMET class additions + keystone provenance edge
- E3 → operator-registry-first enumeration + extraction/confidence pipeline
- E4 → bitemporal immutable schema + deterministic exporter
- E5 → mapping ledger states + stratified review + legibility + PR governance
