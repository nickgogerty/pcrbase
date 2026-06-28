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
MAPPING = {
    # G1 Identification -> mostly NEW core (PCR admin) = extended
    "id.operator":      ("comet-core:PCRProgramOperator", "class", "extended", "New: subclass of schema:Organization"),
    "id.program":       ("comet-pcf:PCRDocument.program", "property", "extended", "Property of reified PCRDocument"),
    "id.pcr_number":    ("comet-pcf:PCRDocument.pcrNumber", "property", "extended", "Reify PCRReference stub"),
    "id.version":       ("comet-pcf:PCRDocument.version", "property", "extended", "Reify PCRReference stub"),
    "id.pub_date":      ("comet-pcf:PCRDocument.validFrom", "property", "extended", "Reify PCRReference stub"),
    "id.valid_until":   ("comet-pcf:PCRDocument.validUntil", "property", "extended", "Reify PCRReference stub"),
    "id.cpc_code":      ("comet-pcf:PCRDocument.scopeCPC", "property", "extended", "CPC scope code"),
    "id.geography":     ("comet-core:GeographyScope", "class", "exact", "Existing COMET L1 class"),
    "id.language":      ("dcterms:language", "property", "exact", "Dublin Core, COMET-aligned"),
    "id.core_pcr_ref":  ("comet-pcf:PCRDocument.supersedes", "property", "extended", "c-PCR/sub-PCR linkage"),
    "id.standard_basis":("comet-pcf:StandardRef", "class", "exact", "Existing (PACT crossSectoralStandardsUsed)"),

    # G3 Unit -> exact (existing COMET classes)
    "unit.type":        ("comet-pcf:FunctionalUnit", "class", "exact", "Existing L4 class"),
    "unit.value":       ("comet:FunctionalUnit", "shacl", "exact", "SHACL value constraint on FunctionalUnit"),
    "unit.reference_flow":("comet-pcf:FunctionalUnit.referenceFlow", "property", "lossy", "No explicit reference-flow property yet"),

    # G4 Boundary -> exact
    "boundary.type":    ("comet-pcf:SystemBoundary", "class", "exact", "Existing L4 class"),
    "boundary.modules_declared": ("comet-pcf:DeclaredModule", "class", "extended", "New SKOS A1-D scheme"),

    # G5 Modules -> extended (DeclaredModule scheme)
    "modules.A1A3":     ("comet-pcf:DeclaredModule", "class", "extended", "New A1-D enumeration"),
    "modules.D":        ("comet-pcf:DeclaredModule", "class", "extended", "New A1-D enumeration"),

    # G6 Cut-off -> extended (new CutOffRule)
    "cutoff.mass":      ("comet-pcf:CutOffRule", "class", "extended", "New class; SHACL threshold constraint"),

    # G7 Allocation -> exact class, SHACL constraint
    "alloc.coproduct":  ("comet-pcf:AllocationMethod", "shacl", "exact", "SHACL constraint on existing AllocationMethod"),
    "alloc.cff":        ("comet-pcf-pef:CircularFootprintFormula", "class", "extended", "PEF sub-module (A2)"),

    # G8 Data Quality -> exact (PACT DQI already in COMET)
    "dq.primary_share": ("comet-sc:PrimaryDataShare", "class", "exact", "Existing L3 class"),
    "dq.scoring":       ("comet-sc:DataQualityIndicator", "class", "exact", "Existing 5-dim DQI"),

    # G9 LCIA -> exact / extended
    "lcia.gwp_method":  ("comet-pcf:LCIAResult", "shacl", "exact", "SHACL: GWP100 method constraint"),
    "lcia.indicator_set":("comet-pcf:LCIAResult", "shacl", "exact", "SHACL: required indicators"),
    "lcia.ef_indicators":("comet-pcf-pef:EFImpactCategory", "class", "extended", "PEF 16 indicators sub-module"),
    "lcia.biogenic":    ("comet-pcf:biogenicCarbon", "property", "exact", "Existing (ISO 14067 7.3.5)"),

    # G10 Scenarios -> extended
    "scenario.rsl":     ("comet-pcf:ReferenceServiceLife", "class", "extended", "New EN15804 class"),

    # G11 Content -> lossy/extended
    "content.substances":("comet-pcf:ContentDeclaration", "class", "extended", "New; SVHC/REACH"),

    # G12 Reporting -> exact
    "report.verification_type":("comet-ver:AssuranceLevel", "class", "exact", "Existing L6 class"),
}

def run(run_id=None):
    run_id = run_id or "map-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
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
