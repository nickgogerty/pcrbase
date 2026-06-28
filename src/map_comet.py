"""P4 COMET mapping — clause_key -> COMET target (reuse-first, decision D).
mapping_status: exact (existing class fits) | extended (new class needed) |
lossy (mapped w/ caveat) | unmapped (gap -> PR backlog).
target_kind: class | property | shacl (most PCR method clauses are SHACL
constraints on existing COMET classes, per panel R2).
"""
import sys, os, hashlib, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# clause_key -> (comet_target, target_kind, mapping_status, rationale)
#
# COMET CURIEs are validated against the shared registry vendored from
# CarbonSigProductHub/comet-carbonsig (comet/comet-registry.json). New terms use
# the comet-pcr: extension namespace defined there — NOT comet-pcf: (which is
# COMET-owned) and not the bogus comet-core: prefix. Run `validate_mapping()` or
# the test suite to catch drift.
MAPPING = {
    # G1 Identification -> PCR admin terms live in the comet-pcr extension
    "id.operator":      ("comet-pcr:PCRProgramOperator", "class", "extended", "comet-pcr: subclass of schema:Organization"),
    "id.program":       ("comet-pcr:program", "property", "extended", "Property of reified comet-pcr:PCRDocument"),
    "id.pcr_number":    ("comet-pcr:pcrNumber", "property", "extended", "Reifies comet-pcf:PCRReference stub"),
    "id.version":       ("comet-pcr:version", "property", "extended", "Reifies comet-pcf:PCRReference stub"),
    "id.pub_date":      ("comet-pcr:validFrom", "property", "extended", "Reifies comet-pcf:PCRReference stub"),
    "id.valid_until":   ("comet-pcr:validUntil", "property", "extended", "Reifies comet-pcf:PCRReference stub"),
    "id.cpc_code":      ("comet-pcr:scopeCPC", "property", "extended", "CPC scope code"),
    "id.geography":     ("comet-ef:GeographyScope", "class", "exact", "Existing COMET L2 class (not comet-core:)"),
    "id.language":      ("dcterms:language", "property", "exact", "Dublin Core, COMET-aligned"),
    "id.core_pcr_ref":  ("comet-pcr:supersedes", "property", "extended", "c-PCR/sub-PCR linkage"),
    "id.standard_basis":("comet-pcf:StandardRef", "class", "exact", "Existing (PACT crossSectoralStandardsUsed)"),

    # G3 Unit -> exact (existing COMET classes)
    "unit.type":        ("comet-pcf:FunctionalUnit", "class", "exact", "Existing L4 class"),
    "unit.value":       ("comet-pcf:FunctionalUnit", "shacl", "exact", "SHACL value constraint on FunctionalUnit (L4, not core)"),
    "unit.reference_flow":("comet-pcr:referenceFlow", "property", "extended", "comet-pcr reference-flow property on FunctionalUnit"),

    # G4 Boundary -> exact
    "boundary.type":    ("comet-pcf:SystemBoundary", "class", "exact", "Existing L4 class"),
    "boundary.modules_declared": ("comet-pcr:DeclaredModule", "class", "extended", "comet-pcr EN15804 module scheme"),

    # G5 Modules -> extended (DeclaredModule scheme)
    "modules.A1A3":     ("comet-pcr:DeclaredModule", "class", "extended", "comet-pcr A1-D enumeration"),
    "modules.D":        ("comet-pcr:DeclaredModule", "class", "extended", "comet-pcr A1-D enumeration"),

    # G6 Cut-off -> extended (new CutOffRule)
    "cutoff.mass":      ("comet-pcr:CutOffRule", "class", "extended", "comet-pcr class; SHACL threshold constraint"),

    # G7 Allocation -> exact class, SHACL constraint
    "alloc.coproduct":  ("comet-pcf:AllocationMethod", "shacl", "exact", "SHACL constraint on existing AllocationMethod"),
    "alloc.cff":        ("comet-pcr:CircularFootprintFormula", "class", "extended", "PEF CFF (comet-pcr)"),

    # G8 Data Quality -> exact (PACT DQI already in COMET)
    "dq.primary_share": ("comet-sc:PrimaryDataShare", "class", "exact", "Existing L3 class"),
    "dq.scoring":       ("comet-sc:DataQualityIndicator", "class", "exact", "Existing 5-dim DQI"),

    # G9 LCIA -> exact / extended
    "lcia.gwp_method":  ("comet-pcf:LCIAResult", "shacl", "exact", "SHACL: GWP100 method constraint"),
    "lcia.indicator_set":("comet-pcf:LCIAResult", "shacl", "exact", "SHACL: required indicators"),
    "lcia.ef_indicators":("comet-pcr:EFImpactCategory", "class", "extended", "PEF 16 indicators (comet-pcr)"),
    "lcia.biogenic":    ("comet-pcf:BiogenicCarbon", "class", "exact", "Existing class (ISO 14067 7.3.5); was mis-cased"),

    # G10 Scenarios -> extended
    "scenario.rsl":     ("comet-pcr:ReferenceServiceLife", "class", "extended", "comet-pcr EN15804 class"),

    # G11 Content -> extended
    "content.substances":("comet-pcr:ContentDeclaration", "class", "extended", "comet-pcr; SVHC/REACH"),

    # G12 Reporting -> exact
    "report.verification_type":("comet-ver:AssuranceLevel", "class", "exact", "Existing L6 class"),
}

def validate_mapping():
    """Check every COMET target in MAPPING against the shared registry vendored
    from comet-carbonsig. Non-COMET CURIEs (dcterms:, schema:, …) are skipped.
    Returns the list of invalid CURIEs ([] = clean)."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comet"))
    from validate_curies import load_registry, validate_curies  # vendored
    targets = [t for (t, *_rest) in MAPPING.values()
               if t and t.split(":", 1)[0].startswith("comet")]
    result = validate_curies(targets, load_registry())
    return sorted(set(result["invalid"]))


def run(run_id=None):
    run_id = run_id or "map-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bad = validate_mapping()
    if bad:
        raise SystemExit(f"map_comet: {len(bad)} COMET target(s) not in the shared "
                         f"registry (run comet/sync_registry.py?): {bad}")
    con = get_con()
    # distinct clause_keys actually seen in extracted requirements
    keys = [r[0] for r in con.execute("SELECT DISTINCT clause_key FROM requirement").fetchall()]
    n_map = n_gap = 0
    for ck in keys:
        m = MAPPING.get(ck)
        occ = con.execute("SELECT count(*) FROM requirement WHERE clause_key=?", [ck]).fetchone()[0]
        if m:
            target, kind, status, rationale = m
        else:
            target, kind, status, rationale = (None, None, "unmapped", "No COMET target yet")
        map_id = "map-" + hashlib.md5(f"{ck}|{run_id}".encode()).hexdigest()[:12]
        con.execute(
            """INSERT OR REPLACE INTO comet_mapping
            (map_id, clause_key, comet_target, target_kind, mapping_status, mapping_confidence, rationale, _run_id)
            VALUES (?,?,?,?,?,?,?,?)""",
            [map_id, ck, target, kind, status, 0.8 if m else 0.0, rationale, run_id])
        n_map += 1
        # gap log for extended/unmapped/lossy (the PR backlog; evidence count A6)
        if status in ("extended", "unmapped", "lossy"):
            gap_id = "gap-" + hashlib.md5(ck.encode()).hexdigest()[:12]
            con.execute(
                """INSERT OR REPLACE INTO gap_log
                (gap_id, clause_key, description, proposed_comet_addition, occurrence_count, pr_status, _run_id)
                VALUES (?,?,?,?,?,?,?)""",
                [gap_id, ck, rationale, target, occ, "open", run_id])
            n_gap += 1
    con.close()
    print(f"[{run_id}] mapped {n_map} clause_keys | {n_gap} in gap_log (PR backlog)")
    return run_id

if __name__ == "__main__":
    run()
