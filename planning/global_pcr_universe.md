# Global PCR Universe — Research Data (2026-06-17)

## CRITICAL DISTINCTION: EPDs vs PCRs
- **EPD** = Environmental Product Declaration = one product's verified footprint. There are ~100,000+ globally.
- **PCR** = Product Category Rule = the *method rules* governing a category of EPDs. Far fewer.
- Ratio: one PCR governs tens-to-hundreds of EPDs. PCRbase inventories **PCRs (the rules)**, not EPDs.

## ECO Platform member operators (construction sector, EU-centric) — authoritative
Source: eco-platform.org/the-eco-epd-programs.html, status 1-7-2025. These are **EPD** counts:

| Operator | EPDs | Est. PCRs (rules) |
|---|---|---|
| environdec.com (Intl EPD System) | 12,749 | ~340 (247 enumerated + external) |
| pep-ecopassport.org | 4,740 | ~10–20 (PSR rules) |
| epd-global.no (EPD Norway) | 3,716 | ~30 (NPCR) |
| epdhub.com | 3,301 | ~15–40 |
| ibu-epd.com (IBU Germany) | 2,565 | ~30–50 (Part A + Part B PCRs) |
| epditaly.it | 1,906 | ~20–40 |
| mrpi.nl | 572 | ~10 |
| epddanmark.dk | 570 | ~10 |
| kiwa.com | 483 | ~10 |
| aenor.com (Global EPD) | 421 | ~15 |
| cer.rts.fi (RTS Finland) | 412 | ~10 |
| bregroup.com (BRE UK) | 379 | ~15 |
| itb.pl (ITB Poland) | 379 | ~10 |
| igbc.ie (EPD Ireland) | 221 | ~5 |
| cateb.cat (DAPconstrucción) | 190 | ~10 |
| ift-rosenheim.de | 143 | ~5 |
| bau-epd.at | 88 | ~10 |
| daphabitat.pt | 54 | ~5 |
| zag.si | 51 | ~5 |
| globalgreentag.com | 34 | ~5 |
| sugb.ch | 23 | ~5 |
| epdchina.cn | 12 | ~5 |
| **ECO Platform TOTAL** | **~33,009 EPDs** | **~600–750 PCRs** |

## NON-ECO Platform programs (the rest of the world — NOT in the list above)
These are major ISO 14025 Type-III operators outside the European construction platform:
- **UL Environment / SPOT** (USA) — multi-sector, ~150+ PCRs
- **ASTM International** (USA) — EPD program
- **NSF International** (USA)
- **ICC-ES SAVE** (USA, construction)
- **Smart EPD / EPD Hub** (now ECO member)
- **KEITI** (Korea Environmental Industry & Tech Institute) — large Korean program, gated
- **JEMAI EcoLeaf / SuMPO** (Japan) — large, Japanese
- **EPD Australasia** (also IES-linked)
- **EPD Chile, EPD Latin America, EPD Mexico** (IES-linked)
- **Environdec external PCRs** (regulation-mandated PCRs from other bodies)
- **CEN/national EN 15804 c-PCRs** (sub-PCRs under product TCs)
- **EU PEFCRs** (~30 adopted PEFCRs — separate method family)
- **EU PEF / OEFSR**
- **Sector schemes**: ResponsibleSteel, ASI (aluminium), worldsteel LCI, concrete (GCCA)

## Working estimate of the global PCR universe (the denominator)
| Segment | Est. PCRs |
|---|---|
| ECO Platform members (EU construction) | ~600–750 |
| US programs (UL, ASTM, NSF, ICC-ES) | ~250–400 |
| Asia-Pacific (KEITI, JEMAI/SuMPO, EPD Australasia) | ~300–600 (many gated/non-English) |
| Latin America (Chile, Brazil, Mexico) | ~50–100 |
| EU PEFCRs + OEFSRs | ~30–40 |
| Sector/industry schemes + c-PCRs | ~100–200 |
| **GLOBAL TOTAL (order-of-magnitude)** | **~1,500–2,500 distinct PCRs** |

Note: estimate has wide error bars. The only way to tighten it is per-operator enumeration (exactly what PCRbase P1 adapters do). EnvironDec alone gave a hard 247.

## Working-scraper update (2026-06-17, via Jina Reader r.jina.ai)
**Firecrawl key in ~/.hermes/.env is CORRUPTED** (contains literal `npx -y fir...` instead of an `fc-` token) → every Firecrawl/web_search/web_extract call 401s. Replaced with **Jina AI Reader** (no-auth, JS-rendering) in `src/scraper.py`. Confirmed facts:
- **PEFCR universe is small & bounded**: EU PEF page lists ~19 first-wave adopted PEFCRs + ~13 new/in-development/in-revision (Apparel & Footwear, Cut Flowers, Synthetic Turf, Aviation, Marine Fish, Space, Tourism, Feed, Beer, Pet Food, Dairy, …) → **~30–35 total PEFCRs**. Confirms prior estimate.
- **UL SPOT catalog is login-gated** (Jina returns the login wall) → confirmed `gated`, metadata-only. Same for KEITI/JEMAI.
- **EnvironDec hard count stays 247** (paginated adapter is the authority; Jina only renders page 1).
- ECO Platform member EPD totals (33,009 across 22 ops, 1-7-2025) re-confirmed via Jina.


