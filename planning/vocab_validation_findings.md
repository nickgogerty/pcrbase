# Bottom-Up Vocabulary Validation — Findings (Run 2026-06-17)

Hybrid approach in action: the **top-down seed** (v1-seed, 67 clause keys from ISO 14025/EN 15804) was tested against **real LLM extractions** (Haiku 4.5) across multiple programs and languages. The data now drives vocab changes.

## Corpus validated against
| Operator | Method family | Language | Docs extracted |
|---|---|---|---|
| EnvironDec | ISO 14067 | English | 20 (regex baseline) |
| EPD Norge (NPCR) | EN 15804 | **Norwegian** | 12 (LLM) |
| EU PEFCR | PEF | English | 1 (LLM) |
| IBU | EN 15804 | German | 1 (was an EPD, not a PCR — 0 clauses; see note) |

**Non-English proven:** Norwegian NPCRs extracted cleanly — English values + verbatim original-language source quotes, all span-verified. e.g. NPCR 020 concrete: operator "The Norwegian EPD Foundation", modules "A1-A3, A4 / A1-A3, A4-A5, C1-C4", declared units "1 m² / 1 tonne".

## Seed validation result
- **51 of 67 seed keys observed** in real LLM extractions → the top-down skeleton was largely correct.
- **15 clauses confirmed across BOTH EN15804 and PEF method families** → strong evidence the superset-skeleton design (one vocab, `applicable_to` flags) is robust across programs, not just an ISO-14025 table-of-contents.
- **16 seed keys unobserved** — split into two causes (below).

## Action items the data surfaced (vocab v2 candidates)

### A. False negatives — extractor folded into adjacent clauses (NOT prune)
These exist in the PCRs but the single-pass LLM rolled them into a neighbouring clause. Fix = targeted re-prompt, not deletion:
- `alloc.coproduct`, `alloc.recycling` — present in every EN15804 PCR (allocation section); LLM merged into prose
- `lcia.gwp_method`, `lcia.ef_indicators` — present; merged into `lcia.indicator_set`
- `cutoff.energy`, `cutoff.environmental` — present; merged into `cutoff.mass`/`cutoff.completeness`
- `dq.geographical`, `dq.technological` — present; merged into `dq.primary_share`/`dq.scoring`
- `unit.conversion`, `report.digital_format` — sparse but real

### B. Genuine bottom-up findings (real structural facts)
- **`id.cpc_code` absent from Norwegian NPCRs** — EPD Norge uses NS/NACE-style classification, not UN CPC. → vocab needs a generalized `id.classification_code` with a `scheme` qualifier (CPC | NACE | NS | CN), not a CPC-only field. **This is a real top-down miss the corpus caught.**
- **PEF-only clauses** (`lcia.ef_indicators`, `lcia.normalization`, `alloc.cff`) confirmed present only in PEFCR → validates the decision to isolate PEF in a `comet-pcf` sub-module (panel amendment A2).
- **`id.core_pcr_ref` heavily used (10 docs)** — EN15804 "Part B references Part A" structure is pervasive → the c-PCR/sub-PCR tiering (pcr_type) is essential, confirmed.

## Disambiguation finding (E3's warning, now empirical)
The IBU document pulled from epd-online was an **EPD (Umwelt-Produktdeklaration)**, not a PCR. The LLM extractor correctly returned **0 PCR-requirement clauses** — a useful built-in type-check. → harvesters must filter EPD-vs-PCR at acquisition; the extractor is a secondary guard.

## Recommended vocab v2 changes (for the bump)
1. Generalize `id.cpc_code` → `id.classification_code` + `classification_scheme`.
2. Add per-prompt clause-group passes (allocation, LCIA, data-quality) to recover the false-negative keys — the single-pass prompt under-segments dense sections.
3. Keep all 16 "unobserved" keys for now (none are confirmed-absent across the universe; only under-extracted).
4. Promote any recurring `unclassified` captures (none material this run).
