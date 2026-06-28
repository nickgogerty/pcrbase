# PCRbase

**The open, machine-readable database of Product Category Rules (PCRs) — mapped to the COMET carbon ontology.**

🌐 **[pcrbase.nickgogerty.github.io](https://nickgogerty.github.io/pcrbase)** · 📊 [Dashboard](https://nickgogerty.github.io/pcrbase/dashboard.html) · 🔗 [COMET Ontology](https://nickgogerty.github.io/comet-ontology/)

---

## What is PCRbase?

PCRs (Product Category Rules) are the normative documents that govern how Environmental Product Declarations (EPDs) are calculated. They specify system boundaries, allocation rules, declared modules, LCIA methods, and data quality requirements for specific product categories.

**The problem:** There are ~1,500 PCRs globally across 26+ program operators (EnvironDec, IBU, EPD Norge, EU PEFCR, etc.) — but they exist only as PDFs, each 15–200 pages long, in 10+ languages, with no structured database.

**PCRbase solves this:** Every requirement extracted, normalized, and mapped to a shared semantic vocabulary.

---

## Current State

| Metric | Value |
|---|---|
| PCRs inventoried | **290** |
| Program operators | **7 live** (24 open in registry) |
| Source PDFs | **247** (w/ SHA-256 provenance) |
| Requirements extracted | **4,409** (88% span-verified) |
| Clause vocabulary keys | **67** across 12 groups |
| COMET mappings | **406** (exact / extended / lossy / unmapped) |
| Method families | ISO 14067 · EN 15804 · EU PEF |
| Languages | English · Norwegian · German |

---

## Data Access

### Static API (no key, no server)
```
GET https://nickgogerty.github.io/pcrbase/api/v1/pcrs.json
GET https://nickgogerty.github.io/pcrbase/api/v1/by-method/iso14067.json
GET https://nickgogerty.github.io/pcrbase/api/v1/by-operator/environdec.json
GET https://nickgogerty.github.io/pcrbase/api/v1/stats.json
GET https://nickgogerty.github.io/pcrbase/api/v1/search-index.json
```

### Downloads
| File | Description |
|---|---|
| [`docs/pcrbase.ttl`](docs/pcrbase.ttl) | RDF/Turtle, COMET-aligned, 8,370+ triples |
| [`docs/pcrbase.jsonld`](docs/pcrbase.jsonld) | JSON-LD with COMET @context |
| [`docs/api/v1/pcrs.json`](docs/api/v1/pcrs.json) | All PCR metadata as JSON |
| [`docs/coverage.json`](docs/coverage.json) | Coverage & extraction quality stats |

---

## Architecture

```
Operators ─► Adapters ─► PCR PDFs ─► LLM Extraction ─► DuckDB
(registry)   (harvest)   (blobs+SHA)   (Haiku, span-gate)   (system-of-record)
                                                                    │
                              ┌─────────────────────────────────────┤
                              ▼                                     ▼
                      COMET mapping ledger               Coverage dashboards
                      (exact/extended/lossy/unmapped)    (per operator/sector)
                              │
                              ▼
                   Generated RDF/JSON-LD (Turtle · JSON-LD)
```

- **DuckDB** is the append-only, versioned system-of-record. Never two write processes concurrently.
- **LLM extraction** (Claude Haiku 4.5) with per-field confidence + verbatim span-verification gate — if the extracted value can't be located in the source PDF, it's flagged low-confidence.
- **COMET mapping**: clause_key → COMET class/property/SHACL shape. Gaps feed upstream PRs (≥3 occurrences + human sign-off before opening).
- **Generated RDF**: DuckDB → Turtle/JSON-LD via `src/export_graph.py`. Never hand-maintained.

---

## Pipeline

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install duckdb pymupdf requests langdetect rapidfuzz rdflib

python src/pipeline.py all 10      # seed → harvest 10 → extract → map → export → status
python src/pipeline.py harvest environdec   # harvest one operator
python src/pipeline.py extract llm          # LLM extraction pass
python src/pipeline.py dashboard            # regenerate dashboard
python src/generate_static_api.py           # regenerate static API JSON files
```

---

## Operators in Registry

| Operator | PCRs | Status |
|---|---|---|
| EnvironDec (IVL) | 227 | ✅ Live |
| EPD Norge | 22 | ✅ Live |
| EU PEFCR | 22 | ✅ Live |
| US EPD (NSF/ICC-ES/SCS/PCA) | 12 | ✅ Live |
| BRE (UK) | 3 | ✅ Live |
| EPD Hub | 2 | ✅ Live |
| IBU (Germany) | 2 | ✅ Live |
| UL SPOT (USA) | — | 🔒 Gated |
| KEITI (Korea) | — | 🔒 Gated |
| INIES (France) | — | Not started |
| PEP ecopassport | — | Blocked (network) |
| + 15 more | — | Registry only |

---

## COMET Integration

PCRbase is the primary evidence base for PCR-related additions to the [COMET carbon ontology](https://nickgogerty.github.io/comet-ontology/). Proposed upstream additions:

- `comet-pcf:PCRDocument` — structured, versioned PCR anchor
- `comet-pcf:governedByPCR` — keystone link: ProductCarbonFootprint → PCRDocument
- `comet-core:PCRProgramOperator` — administrative identity
- `comet-pcf:DeclaredModule` — A1–D SKOS scheme
- `comet-pcf:CutOffRule`, `:ReferenceServiceLife`, `:Scenario`

PRs open only after human review + evidence threshold (≥3 PCR occurrences).

---

## Contributing

**Add a new operator:**
1. Open an issue with the operator name, listing URL, and access status (open/gated).
2. Or submit a PR adding an adapter in `src/adapters/`.

**Report an extraction error:** Open an issue with the PCR ID, clause_key, and correct value.

**Human review:** The `review_queue` table tracks items needing verification. Sample picks welcome.

---

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use with attribution.
Code: MIT.

---

*Built by [Nick Gogerty](https://github.com/nickgogerty) · PCRbase v0.2 · Data generated 2026-06-18*
