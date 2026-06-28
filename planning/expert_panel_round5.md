# PCRbase Expert Panel — Round 5: Devil's Advocate / Stress-Test

Every expert attacks the consensus as hard as possible. Each attack → rebuttal → verdict (SURVIVES / PARTIAL / FAILS). PARTIAL/FAILS produce **mandatory amendments** folded into the final plan.

## Attack 1 (E5 attacks C1) — "120 clause_keys is a fantasy; PCRs are too heterogeneous to fit one vocabulary"
**Rebuttal:** The skeleton is a *superset with applicable_to flags*, and ISO 14025 §7 + EN 15804 §6 already impose a near-universal structure. Programs deviate in *content*, not *category*. We allow an `other/uncategorized` clause bucket + a quarterly vocab-extension review.
**Verdict: PARTIAL.** → **Amendment A1:** ship clause vocab as **versioned** (`clause_vocab_version`), include an explicit `unclassified` capture bucket, and a review ritual to promote recurring unclassified clauses into new keys. Don't pretend v1 is complete.

## Attack 2 (E1 attacks C4) — "Mapping PEFCR onto an ISO-14067 core is lossy; you'll misrepresent EU method"
**Rebuttal:** Resolved in R3 — PEF additions live in a separate `comet-pcf` PEF sub-module via owl:imports, not forced into core. Lossy mappings are explicitly flagged `mapping_status='lossy'` with rationale and excluded from "exact" claims.
**Verdict: SURVIVES** — but → **Amendment A2:** PEFCR/EF-method clauses get a dedicated `method_family` tag (`ISO14067|EN15804|PEF|other`) on every requirement so cross-method comparisons are never silently conflated.

## Attack 3 (E3 attacks C2) — "'All PCRs online' is unfalsifiable; you can never prove completeness, so the headline goal is unmeetable"
**Rebuttal:** True — completeness is unprovable. Reframe the deliverable as **"the known universe": an explicit, sourced operator registry where coverage is measurable per-operator** (N operators enumerated, M with full PCR listings harvested). Completeness becomes a per-operator coverage metric, not a global absolute.
**Verdict: PARTIAL.** → **Amendment A3:** redefine the success metric as **operator-coverage + per-operator PCR-listing coverage**, published as a coverage dashboard. Drop any claim of absolute completeness. This directly answers the original-turn dissent.

## Attack 4 (E2 attacks C3) — "LLM extraction of normative legal-ish clauses will hallucinate thresholds (cut-off %, allocation rules) with high confidence — confidence scores are not calibrated"
**Rebuttal:** Valid and dangerous — a hallucinated "2% mass cut-off" is worse than a blank. Mitigations: (a) every numeric/normative value MUST carry a `source_span`; export pipeline rejects values whose span doesn't contain the value (regex/string verification gate). (b) Calibrate confidence against the human-reviewed sample; recompute thresholds.
**Verdict: PARTIAL.** → **Amendment A4:** add a **span-verification gate** — extracted normalized values (numbers, enums) must be substring-verifiable against the cited source span or they're auto-routed to review regardless of model confidence. Self-reported confidence alone never gates export.

## Attack 5 (E4 attacks C5) — "Bitemporal model is over-engineered; you'll spend the budget on versioning plumbing and never ship the inventory"
**Rebuttal:** Partly fair — full bitemporality is overkill. We need *uni-temporal version lineage* (when each PCR edition was valid + when we observed it), not transaction-time-vs-valid-time bitemporality. Simplify.
**Verdict: PARTIAL.** → **Amendment A5:** downscope to **uni-temporal version lineage** (`valid_from`/`valid_until`/`superseded_by` + `retrieved_at`/`content_hash`). Append-only, but no dual time axes. Ship inventory first; versioning is lightweight metadata, not a subsystem.

## Attack 6 (E5 attacks C6/whole) — "If you PR speculative ontology additions upstream from LLM-derived mappings, you risk polluting COMET and burning credibility with ISO/WBCSD"
**Rebuttal:** Exactly why the gap_log → PR pipeline has a 100% human gate on `extended`/`unmapped`, and PRs ship with COMET's own required artifacts (label, comment, example, alignment triples, SHACL). PRs are *proposals* into COMET's public RFC process (Viz 10), not direct commits.
**Verdict: SURVIVES** — → **Amendment A6:** no upstream PR is opened without (a) ≥N independent PCR occurrences justifying the addition (evidence threshold) and (b) human sign-off. Solo-occurrence gaps stay in `gap_log`, not PR'd.

## Attack 7 (E1 attacks scope) — "All sectors at once dilutes depth; you'll have shallow coverage everywhere and deep nowhere"
**Rebuttal:** Nick explicitly chose all-sectors. The clause skeleton is sector-agnostic, so breadth doesn't cost depth at the *requirement* level; sector-specific allocation/scenario rules are captured as clause values, not separate schemas. Construction will naturally dominate v1 by document count (largest corpus) — that emerges from the data, not from scoping.
**Verdict: SURVIVES** — → **Amendment A7:** add a `sector`/`cpc_code` facet to every PCR so depth-per-sector is *measurable*; report coverage by sector even though ingestion is all-at-once.

## Attack 8 (E3 attacks "living") — "Quarterly re-harvest will silently break when operators redesign their sites; the living DB rots without anyone noticing"
**Rebuttal:** Real operational risk. Adapters need health checks.
**Verdict: PARTIAL.** → **Amendment A8:** each adapter emits a **harvest health signal** (expected vs found PCR count per operator); a re-harvest run that drops >X% for an operator raises an alert rather than silently recording "0 PCRs." Build the watchdog into the cron from day one.

## Surviving consensus
The clause-level, COMET-as-constraints, generated-graph, living-versioned architecture **survives** — with 8 amendments (5 PARTIAL-driven changes, 3 reinforcing tags/gates). No FAILS. The biggest substantive changes: reframe success as **measurable coverage not absolute completeness** (A3), **span-verification gate** over raw confidence (A4), **downscope to uni-temporal** (A5), and **evidence-threshold + human gate before any upstream PR** (A6).

## Mandatory amendments summary
| # | Amendment | Folds into phase |
|---|---|---|
| A1 | Versioned clause vocab + `unclassified` bucket + promotion ritual | P0, P8 |
| A2 | `method_family` tag on every requirement | P0 schema, P3 |
| A3 | Success = operator + per-operator coverage metric; drop absolute-completeness claim | P1, P8 dashboard |
| A4 | Span-verification gate on normalized values (overrides confidence) | P3, P5 export |
| A5 | Downscope bitemporal → uni-temporal version lineage | P0 schema |
| A6 | Upstream PR requires evidence threshold (≥N occurrences) + human sign-off | P7 |
| A7 | `sector`/`cpc_code` facet for measurable per-sector depth | P0 schema, P8 |
| A8 | Per-adapter harvest health signal + drop alert | P1, P8 cron |
