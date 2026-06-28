"""Clause vocabulary v1 — TOP-DOWN SEED (panel skeleton, 12 groups).
Derived from ISO 14025 §7, ISO 21930, EN 15804+A2 §6, and PEF/PEFCR guidance.
This is the SEED only — bottom-up validation against real harvested PCRs
(see validate_vocab.py) will add/rename/split keys and bump vocab_version.
applicable_to: which pcr_type/method_family a clause applies to (all = universal).
"""

VOCAB_VERSION = "v1-seed"

# (clause_key, clause_group, label, pcr_native_altlabels, applicable_to)
CLAUSES = [
    # G1 Identification
    ("id.operator",        "G1_Identification", "Program operator",            "programme operator;program holder", "all"),
    ("id.program",         "G1_Identification", "EPD programme name",          "programme;program", "all"),
    ("id.pcr_number",      "G1_Identification", "PCR registration number",     "PCR no;registration number;document number", "all"),
    ("id.version",         "G1_Identification", "PCR version/edition",         "version;edition;revision", "all"),
    ("id.pub_date",        "G1_Identification", "Publication/issue date",      "date of issue;publication date", "all"),
    ("id.valid_until",     "G1_Identification", "Validity/expiry date",        "valid until;expiry;date of expiry", "all"),
    ("id.cpc_code",        "G1_Identification", "Product classification code", "CPC;UN CPC;product category code", "all"),
    ("id.geography",       "G1_Identification", "Geographical scope",          "geography;region;applicability", "all"),
    ("id.language",        "G1_Identification", "Document language",           "language", "all"),
    ("id.core_pcr_ref",    "G1_Identification", "Reference to core PCR",       "core PCR;parent PCR;reference PCR", "cpcr,subpcr"),
    ("id.standard_basis",  "G1_Identification", "Governing standard(s)",       "based on;in accordance with;reference standard", "all"),

    # G2 Goal & Scope
    ("scope.intended_use",     "G2_GoalScope", "Intended use of EPD",             "intended use;intended application", "all"),
    ("scope.product_category", "G2_GoalScope", "Product category definition",     "product category;scope of products", "all"),
    ("scope.inclusions",       "G2_GoalScope", "Products included",               "covered products;in scope", "all"),
    ("scope.exclusions",       "G2_GoalScope", "Products excluded",               "out of scope;not covered", "all"),
    ("scope.comparability",    "G2_GoalScope", "Comparability statement",         "comparability;comparison rules", "all"),
    ("scope.target_audience",  "G2_GoalScope", "Target audience",                 "audience;intended audience", "all"),

    # G3 Functional / Declared unit
    ("unit.type",          "G3_Unit", "Functional vs declared unit",     "functional unit;declared unit", "all"),
    ("unit.value",         "G3_Unit", "Unit quantity & dimension",       "declared unit;reference unit", "all"),
    ("unit.reference_flow","G3_Unit", "Reference flow",                  "reference flow", "all"),
    ("unit.conversion",    "G3_Unit", "Conversion/quantification rules", "conversion factor;quantification", "all"),
    ("unit.mass_reference","G3_Unit", "Reference/declared mass",         "reference mass;mass per unit", "all"),

    # G4 System boundary
    ("boundary.type",          "G4_Boundary", "System boundary type",        "cradle-to-gate;cradle-to-grave;gate-to-gate", "all"),
    ("boundary.modules_declared","G4_Boundary","Life-cycle modules declared", "modules;life cycle stages", "all"),
    ("boundary.cut_off_desc",  "G4_Boundary", "Boundary description",        "system boundary;boundaries", "all"),
    ("boundary.unit_processes","G4_Boundary", "Included unit processes",     "processes included;included processes", "all"),

    # G5 Modules (EN15804 / 21930)
    ("modules.A1A3",   "G5_Modules", "Product stage A1-A3",          "product stage;A1-A3", "EN15804,ISO21930"),
    ("modules.A4A5",   "G5_Modules", "Construction stage A4-A5",     "construction process;A4-A5", "EN15804,ISO21930"),
    ("modules.B1B7",   "G5_Modules", "Use stage B1-B7",              "use stage;B1-B7", "EN15804,ISO21930"),
    ("modules.C1C4",   "G5_Modules", "End-of-life C1-C4",            "end of life;C1-C4", "EN15804,ISO21930"),
    ("modules.D",      "G5_Modules", "Module D benefits/loads",      "module D;benefits and loads beyond", "EN15804,ISO21930"),

    # G6 Cut-off & completeness
    ("cutoff.mass",        "G6_CutOff", "Mass cut-off threshold",       "mass cut-off;cut-off mass", "all"),
    ("cutoff.energy",      "G6_CutOff", "Energy cut-off threshold",     "energy cut-off", "all"),
    ("cutoff.environmental","G6_CutOff","Environmental cut-off",        "environmental relevance cut-off", "all"),
    ("cutoff.completeness","G6_CutOff", "Completeness requirement",     "completeness;coverage requirement", "all"),

    # G7 Allocation
    ("alloc.coproduct",    "G7_Allocation", "Co-product allocation rule",   "allocation;co-product allocation", "all"),
    ("alloc.recycling",    "G7_Allocation", "Recycling/EoL allocation",     "recycling allocation;end-of-life allocation", "all"),
    ("alloc.cff",          "G7_Allocation", "Circular Footprint Formula",   "CFF;circular footprint formula", "PEF"),
    ("alloc.byproduct",    "G7_Allocation", "By-product handling",          "by-product;waste handling", "all"),
    ("alloc.multifunction","G7_Allocation", "Multi-functionality solution", "multifunctionality;subdivision", "all"),

    # G8 Data quality requirements
    ("dq.temporal",        "G8_DataQuality", "Temporal representativeness",  "temporal;data age;reference year", "all"),
    ("dq.geographical",    "G8_DataQuality", "Geographical representativeness","geographical representativeness", "all"),
    ("dq.technological",   "G8_DataQuality", "Technological representativeness","technological representativeness", "all"),
    ("dq.primary_share",   "G8_DataQuality", "Primary/specific data share",  "primary data;specific data share", "all"),
    ("dq.scoring",         "G8_DataQuality", "Data quality rating method",   "DQR;data quality rating;pedigree", "all"),
    ("dq.background_db",   "G8_DataQuality", "Required background database",  "background data;LCI database", "all"),

    # G9 LCIA method & indicators
    ("lcia.gwp_method",    "G9_LCIA", "GWP characterization method",     "GWP;global warming potential method", "all"),
    ("lcia.indicator_set", "G9_LCIA", "Required impact indicators",      "impact categories;indicators", "all"),
    ("lcia.ef_indicators", "G9_LCIA", "PEF EF 3.x 16 indicators",        "EF indicators;environmental footprint indicators", "PEF"),
    ("lcia.en15804_set",   "G9_LCIA", "EN15804+A2 indicator set",        "core indicators;additional indicators", "EN15804"),
    ("lcia.inventory_flows","G9_LCIA","Resource use & waste flows",      "inventory indicators;resource use", "all"),
    ("lcia.biogenic",      "G9_LCIA", "Biogenic carbon accounting",      "biogenic carbon;biogenic CO2", "all"),
    ("lcia.normalization", "G9_LCIA", "Normalization/weighting",         "normalisation;weighting", "PEF"),

    # G10 Scenarios & RSL
    ("scenario.rsl",       "G10_Scenarios", "Reference service life",       "RSL;reference service life;service life", "EN15804,ISO21930"),
    ("scenario.use",       "G10_Scenarios", "Use-stage scenarios",          "use scenario;maintenance scenario", "EN15804,ISO21930"),
    ("scenario.eol",       "G10_Scenarios", "End-of-life scenarios",        "end-of-life scenario;disposal scenario", "EN15804,ISO21930"),
    ("scenario.transport", "G10_Scenarios", "Transport scenarios",          "transport scenario;A4 scenario", "EN15804,ISO21930"),

    # G11 Content & additional info
    ("content.declaration","G11_Content", "Content/material declaration",  "content declaration;material content", "all"),
    ("content.substances", "G11_Content", "Hazardous/SVHC substances",     "dangerous substances;SVHC;REACH", "all"),
    ("content.biogenic_content","G11_Content","Biogenic material content",  "biogenic content;renewable content", "all"),
    ("content.additional", "G11_Content", "Additional environmental info",  "additional information", "all"),

    # G12 Reporting & format
    ("report.layout",      "G12_Reporting", "EPD content/layout requirements","EPD layout;reporting requirements", "all"),
    ("report.digital_format","G12_Reporting","Digital data format",         "ILCD;EPD-XML;digital format", "all"),
    ("report.verification_type","G12_Reporting","Verification type",        "internal;external;independent verification", "all"),
    ("report.validity_period","G12_Reporting","EPD validity period",        "EPD validity;period of validity", "all"),
    ("report.review_panel","G12_Reporting", "Review/panel requirements",    "review panel;verifier qualification", "all"),

    # capture bucket (amendment A1) — anything not yet categorized
    ("unclassified",       "G0_Unclassified", "Unclassified requirement",  "", "all"),
]

def rows(run_id="seed"):
    return [(k, g, lbl, alt, app, VOCAB_VERSION) for (k, g, lbl, alt, app) in CLAUSES]

if __name__ == "__main__":
    from collections import Counter
    groups = Counter(c[1] for c in CLAUSES)
    print(f"Clause vocab {VOCAB_VERSION}: {len(CLAUSES)} keys across {len(groups)} groups")
    for g, n in sorted(groups.items()):
        print(f"  {g}: {n}")
