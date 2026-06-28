# PCRbase — COMET Gap Log

Evidence base for upstream COMET ontology PRs. Generated 2026-06-28.
Mappings with `extended` status are candidates for upstream PRs (threshold: ≥3 occurrences + human sign-off).

| clause_key | COMET Target | Kind | Status | Confidence | Rationale |
|---|---|---|---|---|---|
| `alloc.cff` | `comet-pcf-pef:CircularFootprintFormula` | class | extended | 0.80 | PEF sub-module (A2) |
| `alloc.coproduct` | `comet-pcf:AllocationMethod` | shacl | exact | 0.80 | SHACL constraint on existing AllocationMethod |
| `alloc.multifunction` | `comet-pcf:AllocationMethod.multifunctionRule` | property | extended | 0.78 | Multi-output / co-product allocation rule. Property on comet-pcf:AllocationMethod specifyi |
| `alloc.recycling` | `comet-pcf:CircularFootprintFormula` | class | extended | 0.83 | Recycled content / recyclability allocation rule. Maps to comet-pcf-pef:CircularFootprintF |
| `boundary.cut_off_desc` | `comet-pcf:CutOffRule` | class | extended | 0.85 | Textual description of cut-off approach. Maps to comet-pcf:CutOffRule (proposed upstream a |
| `boundary.modules_declared` | `comet-pcf:DeclaredModule` | class | extended | 0.80 | New SKOS A1-D scheme |
| `boundary.type` | `comet-pcf:SystemBoundary` | class | exact | 0.80 | Existing L4 class |
| `boundary.unit_processes` | `comet-pcf:SystemBoundary.unitProcesses` | property | extended | 0.78 | List of unit processes included in the system boundary. Property on comet-pcf:SystemBounda |
| `content.additional` | `comet-pcf:AdditionalEnvironmentalInfo` | class | extended | 0.72 | Optional additional environmental information section. Administrative annotation class. |
| `content.biogenic_content` | `comet-pcf:BiogenicCarbonStatement` | class | extended | 0.85 | Biogenic carbon content declaration (EN 15804+A2 mandatory). New comet-pcf class linked fr |
| `content.declaration` | `comet-pcf:ContentDeclaration` | class | extended | 0.85 | Material/substance content declaration table. New comet-pcf class — already proposed in ga |
| `content.substances` | `comet-pcf:ContentDeclaration` | class | extended | 0.80 | New; SVHC/REACH |
| `cutoff.completeness` | `comet-pcf:CutOffRule.completenessThreshold` | property | extended | 0.82 | Overall completeness criterion (e.g. ≥99% of mass/energy must be accounted). Property on C |
| `cutoff.energy` | `comet-pcf:CutOffRule.energyThreshold` | property | extended | 0.85 | Energy-based cut-off threshold (%). Property on CutOffRule alongside massThreshold. |
| `cutoff.environmental` | `comet-pcf:CutOffRule.environmentalThreshold` | property | extended | 0.78 | Environmental-significance cut-off (e.g. 1% of any impact category). Property on CutOffRul |
| `cutoff.mass` | `comet-pcf:CutOffRule` | class | extended | 0.80 | New class; SHACL threshold constraint |
| `dq.background_db` | `comet-pcf:BackgroundDatabase` | class | extended | 0.85 | Required background LCI database (ecoinvent, GaBi, etc.). New comet-pcf class — a DataQual |
| `dq.geographical` | `comet-pcf:DataQualityRequirement.geographicalRepresentativeness` | property | extended | 0.85 | Geographical representativeness requirement. Property on DataQualityRequirement. |
| `dq.primary_share` | `comet-sc:PrimaryDataShare` | class | exact | 0.80 | Existing L3 class |
| `dq.scoring` | `comet-sc:DataQualityIndicator` | class | exact | 0.80 | Existing 5-dim DQI |
| `dq.technological` | `comet-pcf:DataQualityRequirement.technologicalRepresentativeness` | property | extended | 0.82 | Technological representativeness requirement. Property on DataQualityRequirement. |
| `dq.temporal` | `comet-pcf:DataQualityRequirement.temporalRepresentativeness` | property | extended | 0.85 | Temporal representativeness requirement (e.g. data not older than 5 years). Property on Da |
| `id.core_pcr_ref` | `comet-pcf:PCRDocument.supersedes` | property | extended | 0.80 | c-PCR/sub-PCR linkage |
| `id.cpc_code` | `comet-pcf:PCRDocument.scopeCPC` | property | extended | 0.80 | CPC scope code |
| `id.geography` | `comet-core:GeographyScope` | class | exact | 0.80 | Existing COMET L1 class |
| `id.language` | `dcterms:language` | property | exact | 0.80 | Dublin Core, COMET-aligned |
| `id.operator` | `comet-core:PCRProgramOperator` | class | extended | 0.80 | New: subclass of schema:Organization |
| `id.pcr_number` | `comet-pcf:PCRDocument.pcrNumber` | property | extended | 0.80 | Reify PCRReference stub |
| `id.program` | `comet-pcf:PCRDocument.program` | property | extended | 0.80 | Property of reified PCRDocument |
| `id.pub_date` | `comet-pcf:PCRDocument.validFrom` | property | extended | 0.80 | Reify PCRReference stub |
| `id.standard_basis` | `comet-pcf:StandardRef` | class | exact | 0.80 | Existing (PACT crossSectoralStandardsUsed) |
| `id.valid_until` | `comet-pcf:PCRDocument.validUntil` | property | extended | 0.80 | Reify PCRReference stub |
| `id.version` | `comet-pcf:PCRDocument.version` | property | extended | 0.80 | Reify PCRReference stub |
| `lcia.biogenic` | `comet-pcf:biogenicCarbon` | property | exact | 0.80 | Existing (ISO 14067 7.3.5) |
| `lcia.ef_indicators` | `comet-pcf-pef:EFImpactCategory` | class | extended | 0.80 | PEF 16 indicators sub-module |
| `lcia.en15804_set` | `comet-pcf:EN15804ImpactSet` | class | extended | 0.88 | The EN 15804+A2 mandatory impact category set (16 indicators + 8 resource/waste flows). Ne |
| `lcia.gwp_method` | `comet-pcf:LCIAResult` | shacl | exact | 0.80 | SHACL: GWP100 method constraint |
| `lcia.indicator_set` | `comet-pcf:LCIAResult` | shacl | exact | 0.80 | SHACL: required indicators |
| `lcia.inventory_flows` | `comet-pcf:InventoryFlowRequirement` | class | extended | 0.80 | Required elementary flow inventory (waste, resource, water flows). New class in comet-pcf  |
| `modules.A1A3` | `comet-pcf:DeclaredModule` | class | extended | 0.80 | New A1-D enumeration |
| `modules.A4A5` | `comet-pcf:DeclaredModule` | class | extended | 0.88 | Construction stage modules A4 (transport) and A5 (installation). Maps to comet-pcf:Declare |
| `modules.B1B7` | `comet-pcf:DeclaredModule` | class | extended | 0.88 | Use stage modules B1–B7. Maps to comet-pcf:DeclaredModule individuals. |
| `modules.C1C4` | `comet-pcf:DeclaredModule` | class | extended | 0.88 | End-of-life modules C1–C4. Maps to comet-pcf:DeclaredModule individuals. |
| `modules.D` | `comet-pcf:DeclaredModule` | class | extended | 0.80 | New A1-D enumeration |
| `report.digital_format` | `comet-pcf:DigitalFormatRequirement` | class | extended | 0.75 | Digital data exchange format (ILCD+EPD XML, JSON-LD, etc.). New comet-pcf administrative c |
| `report.layout` | `comet-pcf:EPDLayoutRequirement` | class | extended | 0.70 | EPD content and layout requirements (which sections, tables, graphics required). Administr |
| `report.review_panel` | `comet-ver:ReviewPanel` | class | extended | 0.82 | Third-party review / verification panel. Maps to comet-ver:ReviewPanel (verification layer |
| `report.validity_period` | `comet-pcf:PCRDocument.validityPeriod` | property | extended | 0.85 | EPD/PCR validity period (years). Derivable from validFrom+validUntil on PCRDocument but so |
| `report.verification_type` | `comet-ver:AssuranceLevel` | class | exact | 0.80 | Existing L6 class |
| `scenario.eol` | `comet-pcf:EndOfLifeScenario` | class | extended | 0.85 | End-of-life scenario specification. New comet-pcf class — subclass of comet-pcf:Scenario. |
| `scenario.rsl` | `comet-pcf:ReferenceServiceLife` | class | extended | 0.80 | New EN15804 class |
| `scenario.transport` | `comet-pcf:TransportScenario` | class | extended | 0.82 | Transport scenario (A4/C2). New comet-pcf class. |
| `scenario.use` | `comet-pcf:UseStageScenario` | class | extended | 0.85 | Use-stage scenario (B1–B7). New comet-pcf class — subclass of comet-pcf:Scenario. |
| `scope.comparability` | `comet-pcf:ComparabilityStatement` | class | extended | 0.80 | ISO 14025 §6.7.2 comparability statement. Extends COMET with a class linking PCRDocument t |
| `scope.exclusions` | `comet-pcf:PCRDocument.exclusionScope` | property | extended | 0.78 | Scope exclusions are the complement of inclusions — a PCRDocument annotation property. |
| `scope.inclusions` | `comet-pcf:PCRDocument.inclusionScope` | property | extended | 0.78 | Scope inclusions map to a text annotation on PCRDocument defining what product types are i |
| `scope.intended_use` | `comet-pcf:PCRDocument.intendedUse` | property | extended | 0.82 | Intended use / purpose of the EPD. Maps to a text property on PCRDocument. |
| `scope.product_category` | `comet-pcf:PCRDocument.scopeDescription` | property | extended | 0.82 | Product category definition is a text property of PCRDocument (COMET v0.1 has PCRReference |
| `scope.target_audience` | `comet-pcf:PCRDocument.targetAudience` | property | extended | 0.75 | Target audience of the EPD — administrative annotation on PCRDocument. |
| `unit.conversion` | `comet:FunctionalUnit.conversionFactor` | property | extended | 0.78 | Unit conversion factor (e.g. density for volume↔mass). Property on comet:FunctionalUnit. |
| `unit.mass_reference` | `comet:FunctionalUnit.massReference` | property | extended | 0.80 | Mass-based reference for the functional/declared unit. Property on comet:FunctionalUnit. |
| `unit.reference_flow` | `comet-pcf:FunctionalUnit.referenceFlow` | property | lossy | 0.80 | No explicit reference-flow property yet |
| `unit.type` | `comet-pcf:FunctionalUnit` | class | exact | 0.80 | Existing L4 class |
| `unit.value` | `comet:FunctionalUnit` | shacl | exact | 0.80 | SHACL value constraint on FunctionalUnit |

## PR Priority Queue

Keys with ≥10 requirements and `extended` status:

| clause_key | COMET Target | Req Count |
|---|---|---|
| `id.version` | `comet-pcf:PCRDocument.version` | 241 |
| `id.valid_until` | `comet-pcf:PCRDocument.validUntil` | 238 |
| `id.program` | `comet-pcf:PCRDocument.program` | 226 |
| `scope.product_category` | `comet-pcf:PCRDocument.scopeDescription` | 226 |
| `id.pub_date` | `comet-pcf:PCRDocument.validFrom` | 223 |
| `id.pcr_number` | `comet-pcf:PCRDocument.pcrNumber` | 218 |
| `id.operator` | `comet-core:PCRProgramOperator` | 208 |
| `scope.inclusions` | `comet-pcf:PCRDocument.inclusionScope` | 182 |
| `id.cpc_code` | `comet-pcf:PCRDocument.scopeCPC` | 174 |
| `report.validity_period` | `comet-pcf:PCRDocument.validityPeriod` | 136 |
| `scope.exclusions` | `comet-pcf:PCRDocument.exclusionScope` | 109 |
| `boundary.modules_declared` | `comet-pcf:DeclaredModule` | 91 |
| `id.core_pcr_ref` | `comet-pcf:PCRDocument.supersedes` | 72 |
| `scenario.rsl` | `comet-pcf:ReferenceServiceLife` | 70 |
| `boundary.cut_off_desc` | `comet-pcf:CutOffRule` | 55 |
| `cutoff.mass` | `comet-pcf:CutOffRule` | 46 |
| `report.review_panel` | `comet-ver:ReviewPanel` | 45 |
| `content.declaration` | `comet-pcf:ContentDeclaration` | 34 |
| `scope.target_audience` | `comet-pcf:PCRDocument.targetAudience` | 34 |
| `scope.comparability` | `comet-pcf:ComparabilityStatement` | 33 |
| `scope.intended_use` | `comet-pcf:PCRDocument.intendedUse` | 31 |
| `boundary.unit_processes` | `comet-pcf:SystemBoundary.unitProcesses` | 30 |
| `content.substances` | `comet-pcf:ContentDeclaration` | 29 |
| `report.layout` | `comet-pcf:EPDLayoutRequirement` | 27 |
| `modules.A1A3` | `comet-pcf:DeclaredModule` | 22 |
| `modules.A4A5` | `comet-pcf:DeclaredModule` | 21 |
| `cutoff.completeness` | `comet-pcf:CutOffRule.completenessThreshold` | 20 |
| `alloc.recycling` | `comet-pcf:CircularFootprintFormula` | 18 |
| `modules.C1C4` | `comet-pcf:DeclaredModule` | 18 |
| `modules.B1B7` | `comet-pcf:DeclaredModule` | 16 |
| `modules.D` | `comet-pcf:DeclaredModule` | 16 |
| `alloc.cff` | `comet-pcf-pef:CircularFootprintFormula` | 13 |
| `dq.background_db` | `comet-pcf:BackgroundDatabase` | 12 |
| `lcia.ef_indicators` | `comet-pcf-pef:EFImpactCategory` | 10 |
| `scenario.eol` | `comet-pcf:EndOfLifeScenario` | 10 |