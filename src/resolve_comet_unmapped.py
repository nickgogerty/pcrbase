#!/usr/bin/env python3
"""
Resolve unmapped COMET stubs in comet_mapping.
Maps each unmapped clause_key to the best available COMET target.
Strategy: exact → reuse existing COMET class/property; extended → reify/extend COMET;
          lossy → approximate fit with caveat; remains unmapped only if truly novel.
"""
import sys, os, uuid, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# ── Hand-crafted resolution table ────────────────────────────────────────────
# Each entry: clause_key -> (comet_target, target_kind, mapping_status, confidence, rationale, shacl_snippet)
# target_kind: class | property | shacl
# mapping_status: exact | extended | lossy
RESOLUTIONS = {
    # G1 Identification — mostly maps to proposed PCRDocument extensions
    "scope.product_category": (
        "comet-pcf:PCRDocument.scopeDescription",
        "property", "extended", 0.82,
        "Product category definition is a text property of PCRDocument (COMET v0.1 has PCRReference stub — extended to PCRDocument.scopeDescription)",
        "comet-pcf:PCRDocument sh:property [ sh:path comet-pcf:scopeDescription; sh:datatype xsd:string; sh:minCount 1 ] ."
    ),
    "scope.inclusions": (
        "comet-pcf:PCRDocument.inclusionScope",
        "property", "extended", 0.78,
        "Scope inclusions map to a text annotation on PCRDocument defining what product types are in scope.",
        None
    ),
    "scope.exclusions": (
        "comet-pcf:PCRDocument.exclusionScope",
        "property", "extended", 0.78,
        "Scope exclusions are the complement of inclusions — a PCRDocument annotation property.",
        None
    ),
    "scope.comparability": (
        "comet-pcf:ComparabilityStatement",
        "class", "extended", 0.80,
        "ISO 14025 §6.7.2 comparability statement. Extends COMET with a class linking PCRDocument to comparability conditions.",
        None
    ),
    "scope.intended_use": (
        "comet-pcf:PCRDocument.intendedUse",
        "property", "extended", 0.82,
        "Intended use / purpose of the EPD. Maps to a text property on PCRDocument.",
        None
    ),
    "scope.target_audience": (
        "comet-pcf:PCRDocument.targetAudience",
        "property", "extended", 0.75,
        "Target audience of the EPD — administrative annotation on PCRDocument.",
        None
    ),
    # G12 Reporting
    "report.validity_period": (
        "comet-pcf:PCRDocument.validityPeriod",
        "property", "extended", 0.85,
        "EPD/PCR validity period (years). Derivable from validFrom+validUntil on PCRDocument but some PCRs state it as an explicit policy rule.",
        "comet-pcf:PCRDocument sh:property [ sh:path comet-pcf:validityPeriodYears; sh:datatype xsd:integer; sh:minCount 0 ] ."
    ),
    "report.review_panel": (
        "comet-ver:ReviewPanel",
        "class", "extended", 0.82,
        "Third-party review / verification panel. Maps to comet-ver:ReviewPanel (verification layer). COMET v0.1 has comet-ver module — extended here.",
        None
    ),
    "report.layout": (
        "comet-pcf:EPDLayoutRequirement",
        "class", "extended", 0.70,
        "EPD content and layout requirements (which sections, tables, graphics required). Administrative class in comet-pcf.",
        None
    ),
    "report.digital_format": (
        "comet-pcf:DigitalFormatRequirement",
        "class", "extended", 0.75,
        "Digital data exchange format (ILCD+EPD XML, JSON-LD, etc.). New comet-pcf administrative class.",
        None
    ),
    # G4 System boundary
    "boundary.cut_off_desc": (
        "comet-pcf:CutOffRule",
        "class", "extended", 0.85,
        "Textual description of cut-off approach. Maps to comet-pcf:CutOffRule (proposed upstream addition — see gap_log). Extended mapping pending PR merge.",
        "comet-pcf:CutOffRule a owl:Class; rdfs:subClassOf comet:MethodParameter ."
    ),
    "boundary.unit_processes": (
        "comet-pcf:SystemBoundary.unitProcesses",
        "property", "extended", 0.78,
        "List of unit processes included in the system boundary. Property on comet-pcf:SystemBoundary.",
        None
    ),
    # G5 Modules
    "modules.A4A5": (
        "comet-pcf:DeclaredModule",
        "class", "extended", 0.88,
        "Construction stage modules A4 (transport) and A5 (installation). Maps to comet-pcf:DeclaredModule individuals (proposed upstream). Exact match pending PR.",
        None
    ),
    "modules.C1C4": (
        "comet-pcf:DeclaredModule",
        "class", "extended", 0.88,
        "End-of-life modules C1–C4. Maps to comet-pcf:DeclaredModule individuals.",
        None
    ),
    "modules.B1B7": (
        "comet-pcf:DeclaredModule",
        "class", "extended", 0.88,
        "Use stage modules B1–B7. Maps to comet-pcf:DeclaredModule individuals.",
        None
    ),
    # G6 Cut-off
    "cutoff.completeness": (
        "comet-pcf:CutOffRule.completenessThreshold",
        "property", "extended", 0.82,
        "Overall completeness criterion (e.g. ≥99% of mass/energy must be accounted). Property on CutOffRule.",
        None
    ),
    "cutoff.energy": (
        "comet-pcf:CutOffRule.energyThreshold",
        "property", "extended", 0.85,
        "Energy-based cut-off threshold (%). Property on CutOffRule alongside massThreshold.",
        None
    ),
    "cutoff.environmental": (
        "comet-pcf:CutOffRule.environmentalThreshold",
        "property", "extended", 0.78,
        "Environmental-significance cut-off (e.g. 1% of any impact category). Property on CutOffRule.",
        None
    ),
    # G7 Allocation
    "alloc.recycling": (
        "comet-pcf:CircularFootprintFormula",
        "class", "extended", 0.83,
        "Recycled content / recyclability allocation rule. Maps to comet-pcf-pef:CircularFootprintFormula (EN 15804+A2 CFF) for PEF/EN PCRs, or to a generic comet-pcf:RecyclingAllocationRule for ISO14067.",
        None
    ),
    "alloc.multifunction": (
        "comet-pcf:AllocationMethod.multifunctionRule",
        "property", "extended", 0.78,
        "Multi-output / co-product allocation rule. Property on comet-pcf:AllocationMethod specifying the co-product handling approach.",
        None
    ),
    # G8 Data quality
    "dq.background_db": (
        "comet-pcf:BackgroundDatabase",
        "class", "extended", 0.85,
        "Required background LCI database (ecoinvent, GaBi, etc.). New comet-pcf class — a DataQualityRequirement sub-type specifying background dataset constraints.",
        "comet-pcf:BackgroundDatabase a owl:Class; rdfs:subClassOf comet:DataQualityRequirement ."
    ),
    "dq.temporal": (
        "comet-pcf:DataQualityRequirement.temporalRepresentativeness",
        "property", "extended", 0.85,
        "Temporal representativeness requirement (e.g. data not older than 5 years). Property on DataQualityRequirement.",
        None
    ),
    "dq.geographical": (
        "comet-pcf:DataQualityRequirement.geographicalRepresentativeness",
        "property", "extended", 0.85,
        "Geographical representativeness requirement. Property on DataQualityRequirement.",
        None
    ),
    "dq.technological": (
        "comet-pcf:DataQualityRequirement.technologicalRepresentativeness",
        "property", "extended", 0.82,
        "Technological representativeness requirement. Property on DataQualityRequirement.",
        None
    ),
    # G9 LCIA
    "lcia.en15804_set": (
        "comet-pcf:EN15804ImpactSet",
        "class", "extended", 0.88,
        "The EN 15804+A2 mandatory impact category set (16 indicators + 8 resource/waste flows). New comet-pcf class as a named set of EFImpactCategory individuals.",
        "comet-pcf:EN15804ImpactSet a owl:Class; rdfs:subClassOf comet-pcf:ImpactCategorySet ."
    ),
    "lcia.inventory_flows": (
        "comet-pcf:InventoryFlowRequirement",
        "class", "extended", 0.80,
        "Required elementary flow inventory (waste, resource, water flows). New class in comet-pcf linking PCRDocument to required flow types.",
        None
    ),
    # G10 Scenarios
    "scenario.eol": (
        "comet-pcf:EndOfLifeScenario",
        "class", "extended", 0.85,
        "End-of-life scenario specification. New comet-pcf class — subclass of comet-pcf:Scenario.",
        "comet-pcf:EndOfLifeScenario a owl:Class; rdfs:subClassOf comet-pcf:Scenario ."
    ),
    "scenario.use": (
        "comet-pcf:UseStageScenario",
        "class", "extended", 0.85,
        "Use-stage scenario (B1–B7). New comet-pcf class — subclass of comet-pcf:Scenario.",
        None
    ),
    "scenario.transport": (
        "comet-pcf:TransportScenario",
        "class", "extended", 0.82,
        "Transport scenario (A4/C2). New comet-pcf class.",
        None
    ),
    # G11 Content
    "content.declaration": (
        "comet-pcf:ContentDeclaration",
        "class", "extended", 0.85,
        "Material/substance content declaration table. New comet-pcf class — already proposed in gap_log.",
        "comet-pcf:ContentDeclaration a owl:Class; rdfs:comment 'A structured declaration of material composition.' ."
    ),
    "content.biogenic_content": (
        "comet-pcf:BiogenicCarbonStatement",
        "class", "extended", 0.85,
        "Biogenic carbon content declaration (EN 15804+A2 mandatory). New comet-pcf class linked from ProductCarbonFootprint.",
        None
    ),
    "content.additional": (
        "comet-pcf:AdditionalEnvironmentalInfo",
        "class", "extended", 0.72,
        "Optional additional environmental information section. Administrative annotation class.",
        None
    ),
    # G3 Unit
    "unit.mass_reference": (
        "comet:FunctionalUnit.massReference",
        "property", "extended", 0.80,
        "Mass-based reference for the functional/declared unit. Property on comet:FunctionalUnit.",
        None
    ),
    "unit.conversion": (
        "comet:FunctionalUnit.conversionFactor",
        "property", "extended", 0.78,
        "Unit conversion factor (e.g. density for volume↔mass). Property on comet:FunctionalUnit.",
        None
    ),
    # Unclassified
    "unclassified": (
        None,
        None, "unmapped", 0.0,
        "Catch-all bucket for requirements not yet assigned a clause_key. Remains unmapped until promoted in next vocab cycle.",
        None
    ),
}

def run():
    c = get_con()
    now = datetime.datetime.utcnow()
    run_id = f"resolve-comet-{now.strftime('%Y%m%d-%H%M%S')}"

    resolved = 0
    skipped = 0

    for clause_key, (target, kind, status, confidence, rationale, shacl) in RESOLUTIONS.items():
        # Check if there's an existing unmapped row
        existing = c.execute(
            "SELECT map_id FROM comet_mapping WHERE clause_key = ? AND mapping_status = 'unmapped'",
            [clause_key]
        ).fetchone()

        if not existing:
            # No unmapped row for this key — check if any row exists
            any_row = c.execute(
                "SELECT map_id, mapping_status FROM comet_mapping WHERE clause_key = ?",
                [clause_key]
            ).fetchone()
            if any_row:
                print(f"  SKIP {clause_key} — already has status={any_row[1]}")
                skipped += 1
                continue
            # No row at all — insert fresh
            map_id = str(uuid.uuid4())[:16]
        else:
            map_id = str(uuid.uuid4())[:16]

        if status == 'unmapped' and target is None:
            skipped += 1
            continue  # Leave unclassified as-is

        # Insert new resolved mapping row (append-only — new row supersedes old)
        c.execute("""
            INSERT INTO comet_mapping
                (map_id, clause_key, comet_target, target_kind, mapping_status,
                 mapping_confidence, rationale, shacl_snippet, reviewer, reviewed_at, _loaded_at, _run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), ?)
        """, [
            map_id, clause_key, target, kind, status,
            confidence, rationale, shacl,
            "pcrbase-resolver-v1", now, run_id
        ])
        print(f"  ✓ {clause_key:45s} → {status:8s} {target or 'None'}")
        resolved += 1

    print(f"\n✅  Resolved {resolved} unmapped clause_keys  |  Skipped {skipped}")

    # Verify new counts
    counts = c.execute("SELECT mapping_status, COUNT(*) FROM comet_mapping GROUP BY 1 ORDER BY 2 DESC").fetchall()
    print("\nUpdated mapping ledger:")
    for s, n in counts:
        print(f"  {s:12s} {n}")

    c.close()

if __name__ == "__main__":
    run()
