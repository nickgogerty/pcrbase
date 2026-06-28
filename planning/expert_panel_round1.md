# PCRbase Expert Panel — Round 1: Independent Proposals

**Question:** How do we build a maintained, versioned database of *all* PCRs found online — every requirement/value/feature extracted and mapped onto the COMET ontology (expanding COMET where needed) — covering ISO 14025 Type-III program PCRs, EN 15804 sub/c-PCRs, and EU PEFCRs, across all sectors at once, built for living re-harvest?

## Roster (MECE, 25 yrs each)

| # | Expert | Affiliation (illustrative) | Partition owned |
|---|---|---|---|
| E1 | **Dr. Astrid Lindqvist** | ex-EPD International / IVL Swedish Env. Research | LCA & EPD-program standards: what a PCR *is*, ISO 14025/14027/21930, EN 15804+A2, PEFCR method, requirement taxonomy |
| E2 | **Dr. Rajan Mehta** | W3C OWL WG, semantic-web consultant | Ontology engineering: requirement→COMET mapping, OWL/SHACL, namespace strategy, faithful core expansion |
| E3 | **Elena Vásquez** | web-scale harvesting + document-AI lead | Acquisition & extraction: enumerate every program online, harvest PDFs, LLM clause extraction, confidence scoring |
| E4 | **Tom Becker** | versioned-data systems architect | Database: system-of-record schema, temporal versioning, provenance-to-clause, DuckDB↔RDF generation, query layer |
| E5 | **Dr. Marie-Claire Dubois** | ISO TC207/SC7 contributor, EPD verifier | Governance & QA-legibility: mapping fidelity, "survives an auditor/regulator", COMET upstream change-management |

---

## E1 — Lindqvist (LCA/EPD standards)
**Proposal:** The unit of inventory is not "a PCR" but a *requirement clause*. A single PCR contains 40–120 normative clauses across a stable skeleton: functional/declared unit, system boundary, cut-off rules, allocation rules, declared modules (A1–A3, A4–A5, B1–B7, C1–C4, D), data quality requirements, reference service life, scenarios, content declaration, additional environmental info, calculation rules, and reporting format. **Model the skeleton first** — a canonical "PCR requirement taxonomy" — then every PCR is an instance that fills (or omits) skeleton slots. Critique of status quo: COMET's single `PCRReference` class is useless for comparison; it can't answer "which PCRs mandate economic allocation for co-products?" The whole point is comparability across programs.
**Hard warning:** PCR ≠ PEFCR structurally. PEFCRs carry EF impact categories (16 indicators), Circular Footprint Formula, benchmark + class. EN 15804 carries A1–D modules. ISO 14025 generic PCRs may carry neither. The skeleton must be a *superset* with `applicable_to` flags, or the mapping will be lossy.

## E2 — Mehta (ontology)
**Proposal:** Two-layer mapping. (1) A **PCR requirement is metadata about a method**, not a footprint datum — so most PCR clauses map to COMET *property-shape constraints* (SHACL) on existing L4/L3/L2 classes, NOT to new instance data. E.g. "PCR mandates mass allocation" = a SHACL constraint on `comet-pcf:AllocationMethod`; "declared unit = 1 m²" = constraint on `comet:FunctionalUnit`. (2) Where COMET lacks the hook, add classes to core: I already see needed additions — `PCRProgramOperator`, `PCRScope` (CPC/product-category code), `DeclaredModule` (A1–D enumeration), `CutOffRule`, `ReferenceServiceLife`, `Scenario`, and a reification of `PCRReference` into a structured class with versioning. Critique of status quo: COMET has no way to say "this footprint was computed *under* PCR X v2.1" — provenance from footprint→governing-PCR is missing. That link (`prov:wasGeneratedBy` / `comet-pcf:governedByPCR`) is the single most valuable addition.
**Namespace stance:** Reuse `comet-pcf:` and `comet-core:` where the concept is general; only genuinely PCR-administrative concepts (operator, program, registration number) justify new core classes. Avoid a quarantined ext namespace — Nick wants these upstream.

## E3 — Vásquez (acquisition/extraction)
**Proposal:** Enumeration is the hard part, not extraction. There is no master list. Build a **program-operator registry first** (~30–50 known operators: EPD International/Environdec, IBU, EPD Norge, EPD Danmark, INIES/FDES, EPD Italy, ITB, BRE, UL/SPOT, ASTM, NSF, EPD Australasia, ICC-ES, MRPI, DAPcons, Global EPD, KEITI Korea, JEMAI/EcoLeaf Japan, EPD Chile, EPD Latin America, plus EU EF/PEFCR registry). Each operator publishes a PCR *library page*. Harvest = per-operator adapter (sitemap/listing → PCR detail page → PDF). Then LLM extraction over PDFs into the skeleton schema with **per-field confidence + source-clause span**. Critique: a naive "crawl the web for PCRs" approach drowns in EPDs (the *products*) vs PCRs (the *rules*) — must disambiguate. Estimate: 1,500–4,000 distinct PCR documents globally once dedup'd across versions.
**Pitfall:** versioning chaos — same PCR republished with minor edits; need content-hash + semantic version detection. Non-English ≈ 40% of corpus.

## E4 — Becker (database)
**Proposal:** DuckDB as system-of-record with a **bitemporal-lite** model: `pcr` (identity), `pcr_version` (each published edition, `valid_from`/`valid_to`/`superseded_by`/`content_hash`), `requirement` (extracted clause, FK to version, `confidence`, `source_page`, `source_span`, `review_status`), `comet_mapping` (requirement→COMET class/property/SHACL, `mapping_status`, `mapping_confidence`), `source_document` (blob path, URL, retrieval timestamp, `access_status`). RDF/JSON-LD is a **generated artifact** from these tables (a deterministic exporter), never hand-maintained — that satisfies decision B. Critique of status quo: treating this as a flat spreadsheet loses version lineage and provenance, which is the entire value for a *maintained* DB. Everything immutable-append; corrections are new rows, not updates.
**Query layer:** DuckDB SQL for analytics; export to Turtle/JSON-LD for the COMET graph; optional SPARQL via a triplestore load later if needed.

## E5 — Dubois (governance/QA)
**Proposal:** Mapping fidelity is the project's reputational risk. Every requirement→COMET mapping must be **auditable to the source clause** and carry a `mapping_rationale`. Introduce a 4-state mapping ledger: `exact` (existing COMET class fits), `extended` (new COMET class proposed), `lossy` (mapped with caveat), `unmapped` (gap logged). The gap log *is* the COMET PR backlog. Critique of status quo: an LLM-only pipeline with no human gate will produce confident-wrong mappings that, if PR'd upstream, damage COMET's credibility with ISO/WBCSD. Sampling must be **stratified by confidence and by mapping_status** — 100% review of `extended`/`lossy` (they touch the ontology), sampled review of `exact`.
**Legibility test:** Can an EPD verifier open a PCRbase record and recognize their own PCR? If the skeleton uses COMET jargon instead of PCR-native field names, no. Keep PCR-native labels as `skos:altLabel` on every mapped field.

---

### Round 1 convergence signals
- Unit of record = **requirement clause**, not document (E1, E2, E4 agree).
- Most clauses are **SHACL constraints / method metadata**, not instance data (E2) — reframes "mapping onto COMET."
- **Enumeration via per-operator adapters** is the critical path (E3).
- **Bitemporal versioning + immutable append** for "living" (E4).
- **Gap log = COMET PR backlog**; 100% human review of ontology-touching mappings (E5).
- Open tension: skeleton as *superset across PCR/PEFCR/c-PCR* vs separate schemas (E1 flag).
