# PCRbase — Coverage & Representativeness Assessment

**Generated 2026-06-17 · benchmarked against the global PCR universe**

## TL;DR
PCRbase currently holds **43 PCRs across 4 programs** — an **indicative proof-of-pipeline, not a representative inventory**. It covers **~2.7% of the estimated global PCR universe** (~1,600 PCRs), or **~14% of the operators already hard-enumerated**. Completing it to a representative ~1,600-PCR inventory is a **~$15k / ~260-hour** effort whose binding constraint is **human review and adapter engineering, not compute** (LLM extraction for the entire universe costs **~$23**).

---

## 1. The critical denominator: PCRs ≠ EPDs
The single most important framing: **EPDs** (product declarations) number ~100,000+ globally; **PCRs** (the category *rules*) are ~100× fewer. ECO Platform reports **~33,009 EPDs** across 22 member operators (1-7-2025) — but those are governed by only an estimated **600–750 PCRs**. PCRbase inventories the **rules**, so the right denominator is PCRs.

## 2. Current holdings (hard counts)
| Operator | PCRs in DB | Method | Language |
|---|---|---|---|
| EnvironDec | 19 (of 247 enumerated) | ISO 14067 | EN |
| EPD Norge | 22 (of 30 enumerated) | EN 15804 | NO |
| EU PEFCR | 1 | PEF | EN |
| IBU | 1 (an EPD, disambiguation test) | EN 15804 | DE |
| **Total** | **43** | 3 method families | 3 languages |

## 3. The global PCR universe (the denominator)
| Segment | Est. PCRs | Status |
|---|---|---|
| ECO Platform members (EU construction, 22 ops) | 600–750 | EnvironDec+Norge hard-enumerated (277) |
| US programs (UL SPOT, ASTM, NSF, ICC-ES) | 230–400 | not yet touched |
| Asia-Pacific (KEITI Korea, JEMAI/SuMPO Japan, EPD AU) | 220–540 | largely gated / non-English |
| Latin America (Chile, Brazil, Mexico) | 50–100 | open, IES-linked |
| EU PEFCR + OEFSR | 30–40 | open (guidance ingested) |
| Sector schemes + EN 15804 c-PCRs | 100–200 | scattered |
| **GLOBAL TOTAL** | **~1,120–2,050 (mid ~1,586)** | wide error bars |

> Estimate confidence is **moderate**. Two segments are hard counts (EnvironDec 247, Norge 30); the rest are domain-expert estimates. Only per-operator enumeration (the P1 adapters) tightens it — which is exactly the method that produced the two hard counts.

## 4. Coverage scorecard
| Metric | Value | Reading |
|---|---|---|
| Coverage vs **global universe** (mid) | **2.7%** (range 2.1–3.8%) | indicative, not representative |
| Coverage vs **enumerated operators** (307 hard) | **14.0%** | shows the pipeline scales within a program |
| **Operators touched** | **4 / 17** segments | breadth gap is the main weakness |
| **Method families** | 3 / 3 (ISO 14067, EN 15804, PEF) | ✅ all major methods proven |
| **Languages** | 3 (EN, NO) + machine-translation proven | ✅ non-English path works |
| **Regions** | 1.5 / 5 (Europe + token global) | Americas & Asia absent |

**Verdict: representative of *method and language diversity*, NOT of *volume or geography*.** The architecture is validated end-to-end across the hard axes (method family, language, clause structure); what's missing is breadth of operators and raw record count.

## 5. What's missing (ranked by impact)
1. **US programs entirely absent** — UL SPOT alone is ~150–250 PCRs, multi-sector, open. Highest-value next adapter.
2. **Asia-Pacific absent** — KEITI + JEMAI are ~220–540 PCRs but **gated and non-English** (Korean/Japanese); needs translation + possibly manual/credentialed acquisition.
3. **EnvironDec only 19/247 ingested** — the enumeration is done; just need to run the downloader to completion (~$4 LLM, minutes of runtime).
4. **PEFCR corpus thin (1)** — ~30 adopted PEFCRs exist; needed to properly stress the PEF sub-module mapping.
5. **No sector schemes / c-PCRs** — ResponsibleSteel, ASI, GCCA concrete, EN 15804 product-TC c-PCRs.
6. **INIES (France) gated by JS** — needs a headless-browser adapter, not curl.

## 6. Resources & cost to complete (to ~1,586 PCRs)
| Item | Quantity | Cost |
|---|---|---|
| **LLM extraction** (Haiku 4.5, ~$0.015/PCR) | 1,543 remaining PCRs | **~$23** |
| **Human review** (stratified, ~8 min/PCR @ $60/h) | ~206 hours | **~$12,344** |
| **Adapter engineering** (~13 operators × 4 h @ $60/h) | ~52 hours | **~$3,120** |
| **One-time total** | | **~$15,487** |
| PDF storage | ~2.3 GB | negligible |
| **Quarterly re-harvest** (LLM only; living DB) | full universe | **~$24/quarter** |

### The cost structure is the headline finding
- **Compute is trivially cheap** — extracting the *entire* global universe with Haiku costs **~$23**. The LLM-extractor decision was correct: it removes cost as a constraint.
- **The binding constraints are human and engineering time** — ~80% of the cost is human review (quality gate on ontology-touching mappings, panel amendment A6) plus building the ~13 remaining operator adapters.
- **Living maintenance is ~$100/year in compute** — the quarterly re-harvest is essentially free; the recurring cost is human attention to harvest-health alerts and gated/non-English acquisition.

### Sensitivity
- Drop human review to **fully-automated + 5% audit** → one-time cost falls to **~$3.7k** (mostly adapters), but mapping fidelity risk rises (the exact tradeoff Round-5 attack #6 flagged).
- If Asia-Pacific gated programs require paid access or licensed translation, add **$2–5k** and treat as metadata-only until acquired (panel decision: keep in known universe, flagged `gated`).

## 7. Recommended path to "representative"
A defensible **representative v1** doesn't require all ~1,600. Target **~400–500 PCRs covering all 17 segments and 5 regions** — enough that every method family, region, and the top-10 operators by volume are present. Estimated **~$5–6k / ~90 hours**:
1. Finish EnvironDec (247) + EPD Norge (30) — **done-able today, ~$5 LLM**.
2. Add UL SPOT (US), 2–3 more ECO members, 30 PEFCRs, EPD Australasia — adapters.
3. Metadata-only records for KEITI/JEMAI (gated) so the known universe is complete even where ingestion isn't.
4. Stratified review of the ontology-touching mappings only.

At that point coverage vs global universe is **~30%** but coverage of **segments/regions/methods is ~100%** — which is what "representative" actually means for an ontology-mapping benchmark.
