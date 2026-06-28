# PCRbase Expert Panel — Round 6: Final Adoption

**Panel verdict (5–0):** Adopt the clause-level inventory architecture — *"Decompose every PCR version into controlled requirement clauses; store in an append-only, version-tracked DuckDB system-of-record with full provenance to source clause; map each clause to COMET as existing-class / SHACL-constraint / new-core-class (reuse-first); generate the RDF/JSON-LD graph from the tables; feed ontology gaps to an evidence-gated upstream PR backlog; operate as a living DB with coverage-measured re-harvest."* — with all 8 Round-5 amendments mandatory.

## Definitions table (canonical concepts)
| Term | Definition |
|---|---|
| **PCR** | Product Category Rule: normative method requirements for an EPD of a product category (ISO 14025 Type III). |
| **c-PCR / sub-PCR** | Complementary rules refining a core PCR (esp. under EN 15804 + product-specific). |
| **PEFCR** | EU Product Environmental Footprint Category Rules (EF method, 16 indicators, CFF). |
| **clause_key** | A controlled-vocabulary identifier for one normative requirement category (~120, versioned). |
| **requirement** | One extracted clause instance for one PCR version: value + provenance + confidence. |
| **method_family** | `ISO14067 \| EN15804 \| PEF \| other` — prevents cross-method conflation. |
| **mapping_status** | `exact \| extended \| lossy \| unmapped` — the COMET-mapping ledger state. |
| **pcr_version** | One published edition of a PCR; the unit of versioning (`valid_from/until`, `content_hash`). |
| **known universe** | The explicit, sourced operator registry + enumerated PCR listings; coverage is measured, not assumed complete. |
| **gap_log** | Backlog of COMET additions; evidence-gated subset becomes upstream PRs. |

## Measurement / source stack
- **Operator registry** (manually seeded ~40): EPD International/Environdec, IBU, EPD Norge, EPD Danmark, EPD Italy, INIES/FDES, ITB, BRE, UL/SPOT, ASTM, NSF, EPD Australasia, ICC-ES, MRPI, DAPcons, Global EPD, KEITI (Korea), JEMAI/EcoLeaf (Japan), EPD Chile, EPD Latin America, Bau-EPD, EPD Ireland, EPD Turkey, + EU EF/PEFCR registry, + ISO 14025/21930/EN 15804 as the structural references.
- **Extraction:** pymupdf (text), marker-pdf (OCR fallback), LLM structured extraction, language detection + machine translation.
- **Ontology:** COMET v0.1 (pinned), OWL Turtle, SHACL, owl:imports for PEF sub-module.
- **DB:** DuckDB system-of-record → deterministic Turtle/JSON-LD exporter.

## Ranked candidate priorities (from Round 4 vote, with "why not #1")
| Rank | Priority | Why it's not higher |
|---|---|---|
| 1 | Clause skeleton (C1, 7 pts) | — (is #1; comparability backbone) |
| 2 | Provenance/auditability (C6, 6) | Depends on skeleton existing to attach provenance to |
| 3 | COMET mapping fidelity (C4, 5) | Downstream of skeleton + provenance |
| 4 | Enumeration (C2, 4) | Critical *path* but lower *risk* (coverage is measurable) |
| 5 | Versioning (C5, 3) | Downscoped to uni-temporal (A5); lightweight metadata |
| 6 | Extraction (C3, 2) | De-risked by confidence-flag + span-gate + human sampling |
| 7 | Graph generation (C7, 1) | Deterministic exporter; lowest risk |

## Implementation plan (risk-ordered) — see PLAN.md for detail
P0 Foundations → P1 Enumeration → P2 Acquisition → P3 Extraction → P4 COMET mapping → P5 Graph gen → P6 QA/review → P7 COMET PRs → P8 Living ops. Invest early in P0 (skeleton C1) and provenance plumbing (C6).

## Final panel statement
> Adopted 5–0. The architecture is sound and faithful to COMET's design (PCR clauses are predominantly *method constraints* — SHACL shapes on existing L4/L3/L2 classes — not new instance data, which is why reuse-first works). The single most valuable COMET contribution is the `comet-pcf:governedByPCR` provenance edge plus the reified `PCRDocument` class. **Noted reservations:** (1) "all PCRs online" is reframed to measurable coverage (A3) — the original goal as literally stated is unprovable; (2) PEF method must stay in a sub-module to avoid lossy core pollution (A2); (3) upstream PRs are evidence-gated and human-signed to protect COMET's credibility (A6). Panel "statistics" (corpus size 1,500–4,000, ~40 operators, ~120 clause_keys, ~40% non-English) are **illustrative expert estimates, not measured** — P1 enumeration produces the real numbers.
