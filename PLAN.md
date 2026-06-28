# PCRbase — Project Plan

**A maintained, versioned database of all Product Category Rules (PCRs) found online, with every requirement extracted and mapped onto the COMET ontology (expanding COMET where needed).**

- **Status:** Plan — awaiting Nick's OK to scaffold (no code/commits yet).
- **Location:** `~/Projects/pcrbase` (local); COMET additions go upstream to `github.com/comet-ontology/comet` as PRs.
- **Authored by:** 5-expert MECE panel (25 yrs each), 6-round deliberation — transcripts in `planning/expert_panel_round{1..6}.md`.
- **COMET version pinned:** v0.1 Public Draft (https://nickgogerty.github.io/comet-ontology/ontology.html).

---

## 1. Goal & locked decisions

Build the **known universe** of PCRs as a living, queryable knowledge base. Each PCR decomposed into controlled requirement clauses, each clause mapped to COMET, the graph generated from the database, ontology gaps fed upstream as evidence-gated PRs.

| Decision | Locked value |
|---|---|
| A. Breadth | **All sectors at once** |
| B. Semantic layer | **Generated RDF/JSON-LD aligned to COMET** (DuckDB = system-of-record) |
| C. Extraction | **LLM-assisted, per-field confidence flags, human sampling later** |
| D. COMET expansion | **Reuse existing classes/namespace first → extend core where needed → upstream PR** |
| E. Location | **Local `~/Projects/pcrbase`, upstream as PR** |
| PCR universe | **ISO 14025 Type-III PCRs + EN 15804 sub/c-PCRs + EU PEFCRs**, tiered by `pcr_type` |
| Access | **Ingest where possible; paywalled → metadata-only, flagged, kept in known universe** |
| Lifecycle | **Living, versioned, timestamped; built for quarterly re-harvest** |

---

## 2. Architecture (panel verdict, adopted 5–0)

**Clause-level inventory · COMET-as-constraints · generated graph · living & versioned.**

A PCR is a set of normative *method requirements*. Most PCR clauses are **constraints on how a footprint is computed**, so they map to **SHACL shapes on existing COMET L4/L3/L2 classes**, not to new instance data. Three mapping kinds:

1. **Instance-data clause** → existing COMET class/property (e.g. declared unit value → `comet:FunctionalUnit`).
2. **Method-constraint clause** → **SHACL shape** on a COMET class (e.g. "mass allocation mandated" → constraint on `comet-pcf:AllocationMethod`).
3. **Administrative clause** → **new core class** (operator, program, registration number).

```
 Operators ─► Adapters ─► PCR docs (PDF) ─► Extraction ─► requirement rows ─┐
 (registry)   (harvest)   (blob+provenance)  (LLM+conf+span)                │
                                                                            ▼
                                                            DuckDB system-of-record
                                                            (append-only, versioned)
                                                                            │
                              ┌─────────────────────────────────────────────┤
                              ▼                                             ▼
                      COMET mapping ledger                          Coverage dashboards
                      (exact/extended/lossy/unmapped)               (per operator / sector)
                              │                │
                              ▼                ▼
                   Generated RDF/JSON-LD    gap_log ─► evidence-gated ─► COMET PRs
                   (Turtle, COMET @context)            human-signed       (upstream RFC)
                   SHACL-validated
```

---

## 3. Data model (DuckDB, append-only, uni-temporal — amendment A5)

Every row carries `_loaded_at`, `_run_id`. Corrections = new rows, never updates. Nothing deleted; superseded records retained.

| Table | Key columns |
|---|---|
| `operator` | operator_id, name, country, listing_url, adapter_type{sitemap\|html\|api\|manual}, access{open\|gated}, language |
| `pcr` | pcr_id, operator_id, pcr_number, title, pcr_type{pcr\|cpcr\|subpcr\|pefcr}, method_family{ISO14067\|EN15804\|PEF\|other}, sector, cpc_code, geography, first_seen |
| `pcr_version` | version_id, pcr_id, version_label, valid_from, valid_until, superseded_by, content_hash, source_url, retrieved_at, access_status{ingested\|gated\|failed} |
| `source_document` | doc_id, version_id, blob_path, mime, lang, pages, retrieved_at |
| `requirement` | req_id, version_id, clause_group, clause_key, clause_vocab_version, value_text_orig, value_text_en, normalized_value, applicable, confidence, conf_bucket, source_page, source_span, span_verified(bool), method_family, extract_run_id, review_status |
| `comet_mapping` | map_id, clause_key, comet_target, target_kind{class\|property\|shacl}, mapping_status{exact\|extended\|lossy\|unmapped}, mapping_confidence, rationale, shacl_snippet, reviewer, reviewed_at |
| `gap_log` | gap_id, clause_key, description, proposed_comet_addition, occurrence_count, pr_status |
| `clause_vocab` | clause_key, clause_group, label, pcr_native_altlabels, applicable_to, vocab_version |
| `review_queue` | item_ref, item_type, reason, priority, assigned, resolved |
| `harvest_health` | run_id, operator_id, expected_count, found_count, delta_pct, alert(bool), ts |

---

## 4. The PCR requirement skeleton (clause vocabulary — priority C1, build first)

~120 versioned `clause_key`s in 12 groups (superset with `applicable_to` flags + `unclassified` capture bucket — amendment A1). Full vocabulary drafted in P0; promoted/extended quarterly.

| Group | Clauses (examples) | Applies to |
|---|---|---|
| G1 Identification | operator, program, pcr_number, version, pub/expiry date, CPC code, geography, language | all |
| G2 Goal & Scope | intended use, product category def, comparability statement | all |
| G3 Functional/Declared unit | unit, reference flow, quantification rule | all |
| G4 System boundary | cradle-to-gate/-grave, modules declared | all |
| G5 Modules | A1–A3, A4–A5, B1–B7, C1–C4, D | EN15804/21930 |
| G6 Cut-off & completeness | mass/energy/environmental thresholds | all |
| G7 Allocation | co-product rule, recycling/CFF, end-of-life | all |
| G8 Data quality requirements | temporal/geo/tech representativeness, primary-data share, DQR | all |
| G9 LCIA method & indicators | GWP set, EN15804+A2 set, EF 3.1 16 indicators | varies |
| G10 Scenarios & RSL | reference service life, use/EoL scenarios | EN15804 B/C |
| G11 Content & additional info | substances, biogenic carbon, dangerous substances | varies |
| G12 Reporting & format | EPD layout, digital format (ILCD/EPD-XML), verification type | all |

---

## 5. COMET mapping & proposed expansions (reuse-first — decision D)

**Reuse existing COMET wherever a concept fits.** New core classes only where nothing fits; PEF-specific concepts in a `comet-pcf` PEF **sub-module** via `owl:imports` (amendment A2) to keep ISO-14067 core coherent.

### Seed PR backlog (evidence-gated, amendment A6 — only PR'd at ≥N occurrences + human sign-off)
| Proposed addition | Kind | Rationale |
|---|---|---|
| `comet-pcf:PCRDocument` (reify the v0.1 `PCRReference` stub) | class | Structured, versioned anchor; today PCRs are a single placeholder |
| `comet-pcf:governedByPCR` (`ProductCarbonFootprint → PCRDocument`) | object property | **Keystone** — COMET has no footprint→governing-PCR provenance edge |
| `comet-core:PCRProgramOperator` (subclass `schema:Organization`) | class | Administrative identity |
| `comet-pcf:DeclaredModule` (SKOS A1–D scheme) | class/scheme | Reused by PCF + EAC |
| `comet-pcf:CutOffRule`, `:ReferenceServiceLife`, `:Scenario` | classes | EN 15804 method requirements |
| `comet-pcf-pef:CircularFootprintFormula`, `:EFImpactCategory` (16) | sub-module | PEF method; isolated to avoid lossy core mapping |

Each PR ships COMET's required artifacts (Viz 10): `rdfs:label`, `rdfs:comment`, `skos:example`, `owl:equivalentClass` alignment, SHACL shape, layer/type/std/sector labels.

---

## 6. Phased build plan (risk-ordered)

| Phase | Deliverable | Key tasks | Lead |
|---|---|---|---|
| **P0 Foundations** | Repo + schema + clause vocab v1 | repo scaffold, pin COMET, DuckDB DDL, draft ~120 clause_keys, seed operator registry (~40) | E1+E4 |
| **P1 Enumeration** | Populated known universe + coverage metric | per-operator adapters, dedup/version clustering, gated→metadata-only, **harvest health signal (A8)** | E3 |
| **P2 Acquisition** | Blob store of source PDFs w/ provenance | download open PDFs, language detect, flag gated/failed | E3 |
| **P3 Extraction** | `requirement` rows w/ confidence + span | PDF→text (pymupdf/marker OCR), LLM clause extraction, MT for non-English, **span-verification gate (A4)** | E3 |
| **P4 COMET mapping** | Mapping ledger + gap_log | clause_key→COMET, SHACL shapes, reuse-first, status tagging | E2 |
| **P5 Graph generation** | RDF/JSON-LD aligned to COMET | deterministic SQL→Turtle/JSON-LD, COMET @context, per-version named graphs, SHACL validation | E4+E2 |
| **P6 QA & review** | Calibrated, sampled, legible inventory | stratified review (100% extended/lossy + conf<0.6, 10% high-conf exact), confidence calibration, legibility check | E5 |
| **P7 COMET PRs** | Upstream contribution set | aggregate gap_log by layer/module, evidence threshold, human sign-off, open PRs per Viz 10 | E5+E2 |
| **P8 Living ops** | Quarterly re-harvest + dashboards | cron re-harvest, content-hash diff, version lineage, coverage + health dashboards, vocab promotion ritual | E4+E3 |

**Sequencing note:** P0→P1→P2→P3 are linear; P4 can begin once clause vocab is frozen (parallel with P2/P3). Invest disproportionately in P0 skeleton (C1) and provenance plumbing (C6) — the panel's top-2 risks.

---

## 7. Success metrics (amendment A3 — measurable coverage, NOT absolute completeness)

- **Operator coverage:** N operators enumerated / known operators.
- **Per-operator PCR-listing coverage:** % of each operator's published PCR list harvested.
- **Sector coverage:** PCRs + clauses per sector (amendment A7).
- **Extraction quality:** span-verified %, human-sample agreement rate, confidence calibration curve.
- **Mapping quality:** % exact / extended / lossy / unmapped; gap_log → PR conversion.
- **Living health:** quarterly re-harvest delta, adapter health alerts resolved.

> "All PCRs online" is reframed as a **measured coverage dashboard**, since global completeness is unprovable (PCRs are revised, region-fragmented, partly paywalled).

---

## 8. Risks & open questions

| Risk | Mitigation |
|---|---|
| Clause vocab incomplete | Versioned vocab + `unclassified` bucket + quarterly promotion (A1) |
| LLM hallucinated thresholds | Span-verification gate overrides confidence (A4) |
| PEF method mis-mapped to ISO core | Separate PEF sub-module + `method_family` tag (A2) |
| Polluting COMET upstream | Evidence threshold + 100% human gate on ontology-touching PRs (A6) |
| Living DB silently rots | Per-adapter harvest health watchdog (A8) |
| Paywalled corpus invisible | Metadata-only records kept in known universe, flagged `gated` |

**Open questions for Nick (non-blocking — defaults assumed):**
1. LLM for extraction — use this Hermes model, or a dedicated cheaper extractor for the bulk pass? (default: cheaper extractor, sampled by stronger model)
2. Blob store — local filesystem under `pcrbase/data/blobs/` or external? (default: local)
3. Evidence threshold N for upstream PRs — default **3** independent PCR occurrences before a gap becomes a PR.
4. Do you want a SPARQL endpoint in v1, or is Turtle/JSON-LD export + DuckDB SQL sufficient? (default: export only; SPARQL later)

---

## 9. Next action
Awaiting Nick's OK to scaffold **P0** (repo + DuckDB schema + clause vocab v1 + operator registry seed + COMET pin). No commits without explicit request.
