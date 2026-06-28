# State of PCR Methods 2026
## A Machine-Readable Inventory of Product Category Rules

*PCRbase · June 2026 · nickgogerty.github.io/pcrbase*

---

## Executive Summary

- **290 Product Category Rules** from 7 program operators are now machine-readable — the first structured, open inventory of PCRs ever compiled. Across 302 versions, 4,409 normative requirements have been extracted, normalised, and mapped to the COMET carbon ontology.
- **The EPD industry faces an expiry cliff.** 92 PCR versions (30% of the tracked corpus) have already expired, and a further 59 versions expire in 2026 alone. Practitioners relying on outdated rules risk non-compliant EPD declarations without a structured alert system.
- **Method fragmentation is real but concentrated.** 78% of PCRs follow ISO 14067 (EnvironDec-dominated), 14% follow EN 15804, and 8% follow EU PEF — yet the three methods share only partial clause overlap, creating silent incompatibilities for cross-program comparisons.

---

## 1. The PCR Landscape

**Coverage at a glance**

| Metric | Value |
|---|---|
| PCRs inventoried | 290 |
| Program operators (live) | 7 |
| Source PDFs acquired | 247 (85% of inventoried versions) |
| Pages of source rules | 9,176 (median 29 pp, max 271 pp) |
| Requirements extracted | 4,409 |
| Span-verified extractions | 3,884 (88%) |
| Languages | English (216), Norwegian (30), German (1) |

The seven operators in the current corpus — EnvironDec (IVL), EPD Norge, EU EF/PEFCR, US EPD, BRE, EPD Hub, IBU — collectively represent an estimated 18–20% of the global PCR universe (~1,500–1,700 PCRs across 26+ known operators). The remaining operators are either gated (UL SPOT, KEITI, JEMAI) or have not yet been harvested (INIES, PEP ecopassport, EPD Italy, Australasia).

**Operator breakdown**

| Operator | PCRs | PDFs | Method |
|---|---|---|---|
| EnvironDec (IVL, Sweden) | 227 | 173 | ISO 14067 |
| EPD Norge (Norway) | 22 | 22 | EN 15804 |
| EU EF / PEFCR (European Commission) | 22 | 22 | EU PEF |
| US EPD (NSF / ICC-ES / SCS / PCA) | 12 | 12 | ISO 14067 |
| BRE (UK) | 3 | 3 | EN 15804 |
| EPD Hub | 2 | 2 | EN 15804 |
| IBU (Germany) | 2 | 1 | EN 15804 |

EnvironDec alone accounts for 78% of the inventoried corpus, reflecting both its scale and the relative openness of its data infrastructure. 54 EnvironDec entries are metadata-only (c-PCRs with no standalone PDF), a structural feature of the category-PCR / sub-PCR architecture.

---

## 2. Method Fragmentation

Three normative frameworks govern how EPD carbon footprints are calculated:

| Method | PCRs | Share | Governing standard |
|---|---|---|---|
| ISO 14067 | 227 | 78% | ISO 14067:2018, ISO 14044 |
| EN 15804 | 41 | 14% | EN 15804+A2:2019/A1:2021 |
| EU PEF | 22 | 8% | EC Recommendation 2021/2279 |

These frameworks are not equivalent. PCRbase's clause-level analysis across 65 normalised requirement keys finds that:

- **System boundary** (modules A1–D) is declared differently across all three — EN 15804 mandates explicit module-by-module declaration; ISO 14067 allows more flexible scoping; PEF mandates all life-cycle stages.
- **Allocation rules** diverge sharply: EN 15804+A2 mandates the Circular Footprint Formula (CFF) for recycled content; ISO 14067 PCRs vary between physical, economic, and system-expansion approaches.
- **LCIA indicator sets** are largely disjoint: EN 15804+A2 requires 16 EF impact categories; ISO 14067 PCRs typically require only GWP100; PEF requires the full EF 3.1 set (16 categories) but with different characterisation factors.

Cross-program EPD comparisons — increasingly demanded by CBAM, ISO 14064-3 verifiers, and EU Green Deal procurement — are currently impeded by this fragmentation. PCRbase's ontology mapping provides the first machine-readable bridge.

---

## 3. The Expiry Cliff

Of the 302 PCR versions in the corpus, 221 carry an explicit validity date. The distribution reveals a structural problem:

| Status | Count | Share |
|---|---|---|
| Already expired (valid\_until < today) | 92 | 42% |
| Valid through 2026 | 59 | 27% |
| Valid 2027–2030 | 88 | 40% |
| Valid 2031+ | 2 | 1% |

**59 PCR versions expire in 2026** — the single largest annual cohort. If manufacturers and consultancies are unaware of expiry, EPDs declared against superseded rules remain technically non-compliant. Most EPD program portals do not send automated alerts; practitioners must check manually.

PCRbase addresses this directly: the version diff monitor detects expiry events and PCR updates in the harvested corpus daily, delivering alerts when changes are detected.

---

## 4. Data Quality Findings

**Extraction confidence (LLM + span verification)**

Extraction was performed using Claude Haiku 4.5 with a verbatim span-verification gate: each extracted value must be locatable as a substring in the source PDF. Results across 4,409 requirements:

- 3,884 requirements (88%) passed span verification — the extracted value is directly attributable to the source document.
- 12% of requirements are flagged as unverified, typically due to OCR artefacts in scanned PDFs or implicit values not explicitly stated in text.

**COMET mapping completeness**

All 65 normalised clause vocabulary keys now have a COMET mapping:

| Status | Clause keys |
|---|---|
| Exact (existing COMET class/property) | 13 |
| Extended (COMET reified/extended) | 50 |
| Lossy (approximate fit, caveat noted) | 1 |
| Unmapped (catch-all bucket) | 1 |

The 50 extended mappings constitute a structured evidence base for upstream PRs to the COMET ontology — each proposing a concrete new class or property with rationale and occurrence count.

---

## 5. What This Means for EPD Practitioners

**1. Stop treating PCRs as PDFs.** 4,409 requirements across 290 PCRs can now be queried as structured data. Practitioners building EPD software, verifier tools, or CBAM declarations no longer need to manually cross-reference PDFs to find applicable rules.

**2. Build expiry monitoring into your workflow.** 42% of the PCR versions in the open corpus are already expired. Any automated EPD pipeline should check `valid_until` against today's date before applying a PCR's requirements. PCRbase provides this check as a free API endpoint.

**3. Cross-program comparison requires an ontology bridge.** The three major methods (ISO 14067 / EN 15804 / PEF) are structurally incompatible at the clause level without a shared semantic layer. The COMET ontology — with PCRbase as its primary PCR evidence base — is the emerging standard for this bridge.

---

## About PCRbase

PCRbase is an open-source project maintaining a versioned, machine-readable inventory of Product Category Rules, with requirements extracted and mapped to the [COMET carbon ontology](https://nickgogerty.github.io/comet-ontology/). The pipeline uses DuckDB as a system-of-record, Claude Haiku for LLM-assisted extraction with span-verification gates, and generates RDF/JSON-LD aligned to COMET.

**Data access:** [nickgogerty.github.io/pcrbase](https://nickgogerty.github.io/pcrbase) · GitHub: [nickgogerty/pcrbase](https://github.com/nickgogerty/pcrbase)

*Contact: nickgogerty@gmail.com · Data: CC BY 4.0 · Code: MIT*
