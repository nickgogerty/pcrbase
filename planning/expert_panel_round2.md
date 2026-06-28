# PCRbase Expert Panel — Round 2: Refinement (addressing Round 1 critiques)

Each expert now operationalizes, with concrete scales/schemas.

## E1 — Lindqvist: the canonical PCR requirement skeleton (superset)
Resolved tension: **one superset skeleton, `applicable_to` flags per field**. Top-level requirement groups (each decomposes to clauses):

| Group | Example clauses | Applies to |
|---|---|---|
| G1 Identification | operator, program, PCR number, version, pub/expiry date, CPC/UN-CPC code, geography, language | all |
| G2 Goal & Scope | intended use, product category definition, comparability statement | all |
| G3 Functional/Declared unit | unit, reference flow, quantification | all |
| G4 System boundary | cradle-to-gate / -grave, modules declared | all (module set differs) |
| G5 Modules | A1–A3, A4–A5, B1–B7, C1–C4, D | EN15804 / 21930 |
| G6 Cut-off & completeness | mass/energy/environmental cut-off thresholds | all |
| G7 Allocation | co-product rule, recycling (CFF for PEF), end-of-life | all |
| G8 Data quality requirements | temporal/geo/tech representativeness, primary-data share, DQR scoring | all |
| G9 LCIA method & indicators | GWP set, EF 3.1 16 indicators (PEF), EN15804+A2 indicator set | varies |
| G10 Scenarios & RSL | reference service life, use/EoL scenarios | EN15804 B/C |
| G11 Content & additional info | substances, biogenic carbon, dangerous substances | varies |
| G12 Reporting & format | EPD layout, digital format (ILCD/EPD-XML), verification type | all |

Every extracted `requirement` row = (pcr_version, group, clause_key, value_text, normalized_value, applicable_flag, confidence, source_span). `clause_key` is a controlled vocabulary (≈120 keys) — this is the comparability backbone.

## E2 — Mehta: mapping model + concrete COMET additions
Mapping target type per clause_key, three kinds:
1. **Instance-data clause** → maps to a COMET class/property (e.g. declared unit value).
2. **Method-constraint clause** → maps to a **SHACL shape** on a COMET class (e.g. "allocation MUST be mass-based" → `sh:hasValue comet-pcf:MassAllocation`).
3. **Administrative clause** → maps to **new core classes** (operator, program, registration).

Concrete proposed COMET additions (the PR backlog seed), reusing `comet-pcf:`/`comet-core:`:
- `comet-pcf:PCRDocument` (reify the stub `PCRReference`): properties `pcrNumber`, `version`, `validFrom`, `validUntil`, `supersedes`, `programOperator`, `scopeCPC`, `geography`, `language`, `governingStandard`.
- `comet-core:PCRProgramOperator` (subclass of `schema:Organization`).
- `comet-pcf:DeclaredModule` (SKOS scheme A1–D) — reused by both PCF and EAC.
- `comet-pcf:CutOffRule`, `comet-pcf:ReferenceServiceLife`, `comet-pcf:Scenario`.
- `comet-pcf:governedByPCR` (object property: `ProductCarbonFootprint → PCRDocument`) — **the keystone provenance link**.
- PEF extension: `comet-pcf:CircularFootprintFormula`, `comet-pcf:EFImpactCategory` (16 EF 3.1 indicators) — these may belong in a `comet-pcf` sub-module rather than core L4.
Addresses E5: each addition ships with `rdfs:label`, `rdfs:comment`, `skos:example`, alignment triples, and a SHACL shape — COMET's own PR requirements (Viz 10).

## E3 — Vásquez: harvester architecture + extraction pipeline
- **Operator registry table** seeded manually (~40 operators) with `listing_url`, `adapter_type` (sitemap | html_list | api | manual), `language`, `access` (open|gated).
- **Per-operator adapter** yields `{pcr_title, pcr_url, pdf_url, version_hint, last_seen}`. Generic fallback adapter for long-tail operators.
- **Dedup/version detection:** content-hash (pdf bytes) + fuzzy title+number match → cluster into `pcr` identity, each distinct hash = a `pcr_version`.
- **Extraction:** PDF→text (pymupdf; OCR fallback marker-pdf for scans) → chunk by skeleton group → LLM structured extraction into clause rows. Each field returns `{value, normalized, confidence 0–1, source_page, source_span}`.
- **Confidence calibration:** confidence buckets High ≥0.85 / Med 0.6–0.85 / Low <0.6; Low auto-queued for human review.
- **Non-English:** detect language, machine-translate to EN for the `value_text_en`, retain `value_text_orig`. EPD record keeps original language tag.
- **Gated/paywalled:** create `pcr` + `pcr_version` with metadata only, `access_status='gated'`, no requirement rows, flagged for manual acquisition.

## E4 — Becker: refined schema (bitemporal, immutable-append)
Core tables (DuckDB, all append-only; `_loaded_at`, `_run_id` on every row):
```
operator(operator_id, name, country, listing_url, adapter_type, access, ...)
pcr(pcr_id, operator_id, pcr_number, title, scope_cpc, geography, pcr_type{pcr|cpcr|subpcr|pefcr}, first_seen)
pcr_version(version_id, pcr_id, version_label, valid_from, valid_until, superseded_by, content_hash, source_url, retrieved_at, access_status)
source_document(doc_id, version_id, blob_path, mime, lang, pages, retrieved_at)
requirement(req_id, version_id, group, clause_key, value_text_orig, value_text_en, normalized_value, applicable, confidence, source_page, source_span, extract_run_id, review_status)
comet_mapping(map_id, clause_key|req_id, comet_target, target_kind{class|property|shacl}, mapping_status{exact|extended|lossy|unmapped}, mapping_confidence, rationale, shacl_snippet, reviewer, reviewed_at)
gap_log(gap_id, clause_key, description, proposed_comet_addition, pr_status)
review_queue(req_id|map_id, reason, priority, assigned, resolved)
```
RDF/JSON-LD exporter: deterministic SQL→Turtle templates, one named graph per `pcr_version`, COMET `@context` injected. Re-runnable, diffable.

## E5 — Dubois: QA gates + governance workflow
- **Stratified review:** 100% of `mapping_status ∈ {extended, lossy}`; 100% of `requirement.confidence < 0.6`; 10% random sample of High-confidence `exact`. Track inter-stage agreement to calibrate the extractor.
- **Mapping ledger states** drive the COMET PR pipeline: `extended`+`unmapped` aggregate into `gap_log` → grouped into upstream PRs by COMET layer/module (mirrors COMET Viz 10 PR workflow & labels).
- **Legibility:** every `clause_key` carries a PCR-native `altLabel`; mappings reviewed against "would the issuing program operator agree this is what their clause means?"
- **Provenance integrity:** no requirement enters the RDF export without a resolvable `source_document` + page/span. Unverifiable = excluded from export, kept in DB flagged.
- **Change management for living DB:** quarterly re-harvest diffs `content_hash`; new version → new `pcr_version` row + re-extract; superseded version retained (never deleted), `superseded_by` set.

### Round 2 outcome
Schema, skeleton (120 clause_keys), mapping model (instance/SHACL/admin), and concrete COMET additions are now operational. Remaining for Round 3: unify into one coherent build sequence and resolve where PEF additions live (core L4 vs sub-module).
