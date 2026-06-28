# PCRbase

A maintained, versioned database of **Product Category Rules (PCRs)** found online, with every requirement extracted and mapped onto the **COMET ontology** (https://nickgogerty.github.io/comet-ontology/ontology.html) — expanding COMET where needed.

## Status (v0.2 — multi-program + LLM extractor — 2026-06-17)
End-to-end pipeline **proven across 4 programs and 2+ languages**: EnvironDec (EN), EPD Norge NPCR (Norwegian), EU PEFCR (PEF method), IBU. 52 PDFs ingested, LLM-extracted (Haiku 4.5), mapped, exported to COMET-aligned RDF/JSON-LD (8,370 triples).

| Stage | Module | Proven output |
|---|---|---|
| Schema | `src/schema.py` | 11-table DuckDB, append-only, uni-temporal |
| Clause vocab (top-down seed) | `src/clause_vocab.py` | 67 keys / 13 groups; validated bottom-up (51/67 observed) |
| Operator registry | `src/operator_registry.py` | 24 operators (22 open, 2 gated) |
| Adapters | `src/adapters/{environdec,epdnorge,manual_registry}.py` | EnvironDec (247 PCRs), EPD Norge (30 NPCRs), PEFCR+IBU (curated) |
| P1/P2 Harvest | `src/harvest.py` (adapter-generic) | 43 PCRs / 52 versions, PDFs w/ provenance + SHA-256 |
| **P3 Extract (LLM)** | `src/extract_llm.py` + `src/llm_client.py` | Haiku 4.5, per-field confidence + **verbatim span-verification gate (A4)**; non-English → English values + original-language quotes |
| P3 Extract (regex) | `src/extract.py` | deterministic fallback, same dict shape |
| P4 COMET map | `src/map_comet.py` | 53 clause_keys (35 exact / 35 extended / 24 unmapped), 40-item gap_log |
| P5 Graph gen | `src/export_graph.py` | 8,370-triple valid Turtle + JSON-LD, COMET @context |
| Vocab validation | `src/validate_vocab.py` | bottom-up coverage report (`planning/vocab_validation_findings.md`) |
| Dashboard | `src/status.py` | coverage / confidence / PR-backlog metrics |

### LLM extractor (Haiku 4.5)
`extract_llm.py` is a **drop-in replacement** for the regex extractor — identical output dict, identical span gate and DB plumbing. Auth uses the Hermes credential-pool OAuth token (`~/.hermes/auth.json`, provider `anthropic`, `anthropic-beta: oauth-2025-04-20` header); model `claude-haiku-4-5`. A raw `ANTHROPIC_API_KEY` env var takes precedence if set. Select backend: `python src/pipeline.py extract llm|regex [limit] [operator]`.

## Architecture (panel-adopted, 5–0)
**Clause-level inventory · COMET-as-constraints · generated graph · living & versioned.**
A PCR = a set of normative method requirements. Most clauses are **SHACL constraints on existing COMET classes**, not new instance data — which is why reuse-first works. DuckDB is the system-of-record; RDF/JSON-LD is **generated** from it (never hand-maintained).

See `PLAN.md` for the full plan and `planning/expert_panel_round{1..6}.md` for the deliberation.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install duckdb pymupdf requests langdetect rapidfuzz rdflib
python src/pipeline.py all 10      # seed -> harvest 10 -> extract -> map -> export -> status
```

## Key design decisions (locked with Nick)
- **All sectors at once**; PCR universe = ISO 14025 PCRs + EN 15804 sub/c-PCRs + EU PEFCRs (tiered by `pcr_type`).
- **Generated RDF/JSON-LD** aligned to COMET (DuckDB = source of truth).
- **LLM-assisted extraction**, per-field confidence + span-verification gate; human sampling later.
- **Reuse COMET first**, extend core where needed, upstream as evidence-gated PRs (≥3 occurrences + human sign-off).
- **Living DB**: versioned, timestamped, built for quarterly re-harvest with per-adapter health watchdog.

## COMET expansion backlog (the upstream PR seed)
Most-evidenced gaps from the first 20 PCRs (all the `extended` mappings reify COMET's single `PCRReference` stub into a structured, versioned `PCRDocument` + `CutOffRule`, `ReferenceServiceLife`, `DeclaredModule`, `ContentDeclaration`). The keystone addition is `comet-pcf:governedByPCR` linking a footprint to its governing PCR. PRs are **not** opened until human-reviewed.

## Next steps
1. Build remaining operator adapters (IBU, EPD Norge, INIES, EU PEFCR, …) — `harvest.py` is adapter-pluggable.
2. Swap the deterministic `extract._match_clause` for an LLM extractor (same dict shape; gate + DB plumbing unchanged).
3. Bottom-up clause-vocab validation: promote recurring `unclassified` clauses into new keys, bump `vocab_version`.
4. Stratified human review (100% extended/lossy + low-confidence; 10% high-confidence sample).
5. Quarterly re-harvest cron + coverage dashboard.
