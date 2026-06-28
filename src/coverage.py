"""Coverage assessment — how representative is PCRbase vs the global PCR universe?
Combines live DB counts with the researched universe denominator
(planning/global_pcr_universe.md) and produces:
  - coverage % at 3 scopes (ingested / enumerated / global universe)
  - gap analysis by operator and region
  - resource + cost estimate to complete
Writes a markdown report and returns a dict the dashboard consumes.
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# Researched universe denominators (see planning/global_pcr_universe.md).
# EPD counts are HARD (ECO Platform 1-7-2025). PCR estimates have error bars.
# Per-operator estimated PCR counts (rules, not EPDs):
UNIVERSE = {
    # operator_id : (display, est_pcrs_low, est_pcrs_high, enumerated_hard, region, access)
    "environdec":  ("Intl EPD System", 247, 340, 247, "Global", "open"),
    "epd-norge":   ("EPD Norway", 30, 30, 30, "Europe", "open"),
    "ibu":         ("IBU (Germany)", 30, 50, None, "Europe", "open"),
    "pep":         ("PEP ecopassport", 10, 20, None, "Europe", "open"),
    "epdhub":      ("EPD Hub", 15, 40, None, "Europe", "open"),
    "epd-italy":   ("EPD Italy", 20, 40, None, "Europe", "open"),
    "inies":       ("INIES (France)", 10, 30, None, "Europe", "gated"),
    "bre":         ("BRE (UK)", 10, 20, None, "Europe", "open"),
    "other_eco":   ("Other ECO Platform (14 ops)", 120, 200, None, "Europe", "open"),
    "ul-spot":     ("UL SPOT (USA)", 150, 250, None, "Americas", "gated"),
    "us-epd":      ("US EPD (NSF/ICC-ES/SCS/PCA)", 80, 150, None, "Americas", "open"),
    "keiti":       ("KEITI (Korea)", 100, 250, None, "Asia", "gated"),
    "jemai":       ("JEMAI/SuMPO (Japan)", 100, 250, None, "Asia", "gated"),
    "epd-au":      ("EPD Australasia", 20, 40, None, "Oceania", "open"),
    "latam":       ("EPD Chile/Brazil/Mexico", 50, 100, None, "Americas", "open"),
    "eu-ef":       ("EU PEFCR/OEFSR", 30, 40, 30, "Europe", "open"),
    "sector":      ("Sector schemes + c-PCRs", 100, 200, None, "Global", "mixed"),
}

# Resource/cost model assumptions (editable)
ASSUMP = {
    "llm_cost_per_pcr_usd": 0.015,      # Haiku 4.5: ~1 call, ~25k in + 3k out
    "pdf_storage_mb_per_pcr": 1.5,
    "adapter_build_hours": 4,           # eng hours per new operator adapter
    "human_review_min_per_pcr": 8,      # stratified sampling, not full
    "human_rate_usd_per_hr": 60,
    "reharvest_per_quarter_frac": 1.0,  # re-check all each quarter
}

# Per-segment metadata for representativeness: primary publication language and a
# sector-mix profile (fractions, sum≈1). Sources: operator scope pages + domain
# knowledge (see planning/global_pcr_universe.md). These are ESTIMATES with wide
# error bars; the language is the operator's primary publication language (most
# also issue EN). Sector buckets are deliberately coarse and defensible.
SECTORS = ["Construction", "Electronics/HVAC", "Food/Agriculture",
           "Cross-sector industrial", "Other consumer"]

# segment key : (primary_language, {sector: fraction})
SEG_META = {
    "environdec":   ("EN",    {"Construction": .55, "Food/Agriculture": .20, "Cross-sector industrial": .15, "Other consumer": .10}),
    "epd-norge":    ("NO",    {"Construction": 1.0}),
    "ibu":          ("DE",    {"Construction": 1.0}),
    "pep":          ("FR/EN", {"Electronics/HVAC": 1.0}),
    "epdhub":       ("EN",    {"Construction": .90, "Other consumer": .10}),
    "epd-italy":    ("IT",    {"Construction": 1.0}),
    "inies":        ("FR",    {"Construction": 1.0}),
    "bre":          ("EN",    {"Construction": 1.0}),
    "other_eco":    ("Other EU", {"Construction": 1.0}),
    "ul-spot":      ("EN",    {"Construction": .60, "Cross-sector industrial": .20, "Other consumer": .20}),
    "us-epd":       ("EN",    {"Construction": .85, "Cross-sector industrial": .15}),
    "keiti":        ("KO",    {"Construction": .40, "Electronics/HVAC": .20, "Food/Agriculture": .20, "Other consumer": .20}),
    "jemai":        ("JA",    {"Construction": .35, "Electronics/HVAC": .25, "Food/Agriculture": .20, "Other consumer": .20}),
    "epd-au":       ("EN",    {"Construction": 1.0}),
    "latam":        ("ES/PT", {"Construction": .90, "Food/Agriculture": .10}),
    "eu-ef":        ("EN",    {"Food/Agriculture": .40, "Other consumer": .35, "Cross-sector industrial": .25}),
    "sector":       ("EN",    {"Cross-sector industrial": 1.0}),
}


def _triangular_mode(low, high, enumerated):
    """Most-likely value for a segment's triangular distribution.

    Use the hard enumerated count when we have one (it is the floor truth);
    otherwise the midpoint of the expert low–high band.
    """
    if enumerated:
        # enumerated is the verified floor; mode sits at/above it but below high
        return max(low, min(enumerated, high))
    return (low + high) / 2.0


def monte_carlo_universe(trials=100_000, seed=42):
    """Monte-Carlo the global PCR total as a sum of independent per-segment
    triangular distributions. Returns percentile stats.

    Why this beats summing the lows and highs: naively adding every segment's
    low (and every high) assumes all segments are simultaneously at their
    extreme — perfect correlation. They are independent estimates, so the
    aggregate uncertainty partially cancels (central-limit effect). The Monte
    Carlo sum gives the statistically correct, tighter interval.
    """
    import random
    rng = random.Random(seed)
    totals = []
    segs = [(v[1], v[2], v[3]) for v in UNIVERSE.values()]  # (low, high, enum)
    for _ in range(trials):
        t = 0.0
        for low, high, enum in segs:
            if high <= low:
                t += low
                continue
            mode = _triangular_mode(low, high, enum)
            mode = min(max(mode, low), high)
            t += rng.triangular(low, high, mode)
        totals.append(t)
    totals.sort()

    def pct(p):
        idx = min(len(totals) - 1, max(0, int(round(p / 100.0 * (len(totals) - 1)))))
        return totals[idx]

    mean = sum(totals) / len(totals)
    return {
        "trials": trials,
        "mean": round(mean),
        "p5": round(pct(5)), "p25": round(pct(25)), "p50": round(pct(50)),
        "p75": round(pct(75)), "p95": round(pct(95)),
        "method": "sum of per-segment triangular(low, mode, high), independent",
    }

def main():
    con = get_con()
    db_by_op = dict(con.execute("SELECT operator_id, count(*) FROM pcr GROUP BY 1").fetchall())
    db_total = con.execute("SELECT count(*) FROM pcr").fetchone()[0]
    extracted = con.execute("SELECT count(DISTINCT version_id) FROM requirement").fetchone()[0]
    con.close()

    # map db operators to universe keys — count every operator present in the DB
    ingested = {k: db_by_op.get(k, 0) for k in db_by_op}
    # ensure the canonical universe keys exist even at zero
    for k in ("environdec", "epd-norge", "ibu", "eu-ef", "us-epd"):
        ingested.setdefault(k, db_by_op.get(k, 0))
    n_ingested = sum(ingested.values())

    univ_low = sum(v[1] for v in UNIVERSE.values())
    univ_high = sum(v[2] for v in UNIVERSE.values())
    univ_mid = (univ_low + univ_high) // 2
    enumerated_hard = sum(v[3] for v in UNIVERSE.values() if v[3])  # operators we've fully listed

    # coverage at three scopes
    cov_global_mid = 100 * n_ingested / univ_mid
    cov_global_low = 100 * n_ingested / univ_high
    cov_enumerated = 100 * n_ingested / enumerated_hard if enumerated_hard else 0

    # operators touched vs total
    ops_touched = sum(1 for k, v in ingested.items() if v > 0)
    ops_universe = len(UNIVERSE)

    # cost to complete (to universe mid)
    remaining = univ_mid - n_ingested
    llm_cost = remaining * ASSUMP["llm_cost_per_pcr_usd"]
    storage_gb = univ_mid * ASSUMP["pdf_storage_mb_per_pcr"] / 1024
    # adapters: ~17 distinct operator groups; ~13 still to build
    adapters_remaining = 13
    adapter_hours = adapters_remaining * ASSUMP["adapter_build_hours"]
    review_hours = remaining * ASSUMP["human_review_min_per_pcr"] / 60
    review_cost = review_hours * ASSUMP["human_rate_usd_per_hr"]
    eng_cost = adapter_hours * ASSUMP["human_rate_usd_per_hr"]
    quarterly_llm = univ_mid * ASSUMP["llm_cost_per_pcr_usd"] * ASSUMP["reharvest_per_quarter_frac"]

    # ── Statistical estimate of the global universe (Monte Carlo) ──────────
    mc = monte_carlo_universe()

    # ── Representativeness by LANGUAGE and by SECTOR ───────────────────────
    # Universe is apportioned using each segment's mid estimate; ingested uses
    # live DB counts. Coverage % = ingested_in_bucket / universe_mid_in_bucket.
    by_language = {}   # lang : {"universe_mid": x, "ingested": y}
    by_sector = {s: {"universe_mid": 0.0, "ingested": 0.0} for s in SECTORS}
    for k, v in UNIVERSE.items():
        seg_mid = (v[1] + v[2]) / 2.0
        seg_ing = ingested.get(k, 0)
        lang, sect_mix = SEG_META.get(k, ("EN", {"Cross-sector industrial": 1.0}))
        # language bucket
        bl = by_language.setdefault(lang, {"universe_mid": 0.0, "ingested": 0.0})
        bl["universe_mid"] += seg_mid
        bl["ingested"] += seg_ing
        # sector buckets (split the segment across its sector mix)
        for sect, frac in sect_mix.items():
            by_sector[sect]["universe_mid"] += seg_mid * frac
            by_sector[sect]["ingested"] += seg_ing * frac

    def _finish(d):
        out = []
        for key, vals in d.items():
            um = vals["universe_mid"]
            ing = vals["ingested"]
            out.append({
                "key": key,
                "universe_mid": round(um),
                "ingested": round(ing, 1),
                "coverage_pct": round(100 * ing / um, 1) if um else 0.0,
            })
        return sorted(out, key=lambda r: -r["universe_mid"])

    lang_rows = _finish(by_language)
    sector_rows = _finish(by_sector)
    # English-language share of the universe (representativeness headline)
    en_keys = {"EN", "FR/EN"}
    en_mid = sum(r["universe_mid"] for r in lang_rows if r["key"] in en_keys)
    en_share = round(100 * en_mid / univ_mid, 0) if univ_mid else 0
    # construction share (dominant-sector headline)
    constr = next((r for r in sector_rows if r["key"] == "Construction"), None)
    constr_share = round(100 * constr["universe_mid"] / univ_mid, 0) if (constr and univ_mid) else 0

    report = {
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ingested_total": n_ingested,
        "ingested_by_op": ingested,
        "extracted_docs": extracted,
        "universe_low": univ_low, "universe_high": univ_high, "universe_mid": univ_mid,
        "enumerated_hard": enumerated_hard,
        "coverage_global_pct_mid": round(cov_global_mid, 1),
        "coverage_global_pct_range": [round(cov_global_low, 1), round(100*n_ingested/univ_low, 1)],
        "coverage_of_enumerated_pct": round(cov_enumerated, 1),
        "operators_touched": ops_touched, "operators_universe": ops_universe,
        "remaining_pcrs": remaining,
        "universe_statistical": mc,
        "english_share_pct": en_share,
        "construction_share_pct": constr_share,
        "by_language": lang_rows,
        "by_sector": sector_rows,
        "cost": {
            "llm_extraction_usd": round(llm_cost, 0),
            "human_review_hours": round(review_hours, 0),
            "human_review_usd": round(review_cost, 0),
            "adapter_eng_hours": adapter_hours,
            "adapter_eng_usd": round(eng_cost, 0),
            "total_one_time_usd": round(llm_cost + review_cost + eng_cost, 0),
            "storage_gb": round(storage_gb, 1),
            "quarterly_reharvest_llm_usd": round(quarterly_llm, 0),
        },
        "universe_table": [
            {"key": k, "name": v[0], "low": v[1], "high": v[2],
             "enumerated": v[3], "region": v[4], "access": v[5],
             "ingested": ingested.get(k, 0)}
            for k, v in UNIVERSE.items()
        ],
        "assumptions": ASSUMP,
    }

    # write JSON for dashboard + markdown report
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "..", "data", "exports", "coverage.json"), "w") as f:
        json.dump(report, f, indent=2)

    # console summary
    print("="*66)
    print("PCRbase COVERAGE ASSESSMENT")
    print("="*66)
    print(f"\nIngested PCRs (PDF+extracted): {n_ingested}")
    print(f"  by operator: {ingested}")
    print(f"\nGlobal PCR universe (estimate): {univ_low:,}–{univ_high:,} (mid {univ_mid:,})")
    print(f"Enumerated hard-count operators: {enumerated_hard} PCRs")
    print(f"\nCOVERAGE:")
    print(f"  vs global universe (mid):   {cov_global_mid:.1f}%   [{report['coverage_global_pct_range'][0]}–{report['coverage_global_pct_range'][1]}%]")
    print(f"  vs enumerated operators:    {cov_enumerated:.1f}%")
    print(f"  operators touched:          {ops_touched}/{ops_universe}")
    print(f"\nTO COMPLETE (to ~{univ_mid:,} PCRs):")
    print(f"  remaining PCRs:             {remaining:,}")
    print(f"  LLM extraction:             ${report['cost']['llm_extraction_usd']:,.0f}")
    print(f"  human review (~{report['cost']['human_review_hours']:.0f} h):     ${report['cost']['human_review_usd']:,.0f}")
    print(f"  adapter eng ({adapters_remaining} ops, {adapter_hours} h): ${report['cost']['adapter_eng_usd']:,.0f}")
    print(f"  ── total one-time:          ${report['cost']['total_one_time_usd']:,.0f}")
    print(f"  storage:                    {report['cost']['storage_gb']} GB")
    print(f"  quarterly re-harvest (LLM): ${report['cost']['quarterly_reharvest_llm_usd']:,.0f}/qtr")
    print(f"\nSTATISTICAL UNIVERSE (Monte Carlo, {mc['trials']:,} trials, independent triangular):")
    print(f"  mean {mc['mean']:,}  ·  P50 {mc['p50']:,}  ·  90% CI [{mc['p5']:,}–{mc['p95']:,}]")
    print(f"\nREPRESENTATIVENESS:")
    print(f"  English-language share of universe: ~{en_share:.0f}%")
    print(f"  Construction share of universe:     ~{constr_share:.0f}%")
    print(f"  by language: " + ", ".join(f"{r['key']} {r['coverage_pct']}%" for r in lang_rows[:6]))
    print(f"  by sector:   " + ", ".join(f"{r['key']} {r['coverage_pct']}%" for r in sector_rows))
    return report

if __name__ == "__main__":
    main()
