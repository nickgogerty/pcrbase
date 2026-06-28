# PCRbase Expert Panel — Round 4: Voting

Each expert ranks their top 3 priorities for what makes-or-breaks the project. Tally identifies where build effort and risk attention must concentrate.

## Candidate priorities (the things we could get wrong)
- C1 — Clause skeleton / controlled vocabulary quality (the comparability backbone)
- C2 — Enumeration completeness (finding the true universe of PCRs)
- C3 — Extraction accuracy + confidence calibration
- C4 — COMET mapping fidelity (reuse-first, SHACL, gap log)
- C5 — Bitemporal versioning / living-DB integrity
- C6 — Provenance to source clause (auditability)
- C7 — Graph generation correctness (SQL→RDF, SHACL valid)

## Ballots (rank 1=3pts, 2=2pts, 3=1pt)
| Expert | #1 | #2 | #3 |
|---|---|---|---|
| E1 Lindqvist | C1 | C4 | C2 |
| E2 Mehta | C4 | C1 | C6 |
| E3 Vásquez | C2 | C3 | C1 |
| E4 Becker | C5 | C6 | C7 |
| E5 Dubois | C6 | C4 | C1 |

## Tally
| Priority | Points | Rank |
|---|---|---|
| **C1 Clause skeleton** | 3+2+1+0+1 = **7** | **1** |
| **C4 COMET mapping fidelity** | 0+3+0+0+2 = **5** | **T-2** |
| **C6 Provenance/auditability** | 0+1+0+2+3 = **6** | **2** |
| C2 Enumeration | 1+0+3+0+0 = 4 | 4 |
| C5 Versioning | 0+0+0+3+0 = 3 | 5 |
| C3 Extraction | 0+0+2+0+0 = 2 | 6 |
| C7 Graph gen | 0+0+0+1+0 = 1 | 7 |

(Corrected: C6 = 6, C4 = 5.)

## Reading
1. **C1 Clause skeleton (7)** — unanimous top-3 except E4. If the controlled vocabulary is wrong/incomplete, everything downstream is incomparable. **Build and freeze v1 of the 120 clause_keys before extraction at scale.**
2. **C6 Provenance (6)** — auditability is the credibility currency; no requirement in the export without resolvable source span.
3. **C4 Mapping fidelity (5)** — the COMET-facing deliverable; reuse-first + gap log.
4. C2 enumeration is the critical *path* (must happen first) even though ranked 4th in *risk* — sequencing ≠ risk weight.

## Panel guidance from vote
- Invest disproportionately in C1 (skeleton design w/ E1 lead) and C6 (provenance plumbing w/ E4) early.
- Extraction (C3) ranked low risk *because* the confidence-flag + human-sampling design de-risks it — don't over-engineer the LLM step.
