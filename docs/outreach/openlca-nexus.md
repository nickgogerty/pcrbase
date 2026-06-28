**To:** contact@openlca.org / nexus@greendelta.com
**Subject:** Structured PCR data integration for OpenLCA Nexus

Hi GreenDelta/Nexus team,

I've built PCRbase — an open, machine-readable database of 290 Product Category Rules across 7 program operators (EnvironDec, EPD Norge, EU PEFCR, IBU, BRE, US EPD, EPD Hub), with 4,409 normative requirements extracted via LLM and mapped to the COMET carbon ontology. The data is available as static JSON API, RDF/Turtle, and JSON-LD at https://nickgogerty.github.io/pcrbase.

OpenLCA users regularly need to identify which PCR governs their product category and what it requires — currently that means hunting PDFs manually. PCRbase could integrate directly into Nexus as a searchable PCR reference layer: structured metadata, version validity dates, clause-level requirements, and a "find PCR by CPC code / sector" endpoint that works without a server.

I'd welcome a 30-minute conversation about whether a PCRbase data feed would be useful to the Nexus team, and what format/schema would fit best. I'm also open to building a dedicated OpenLCA adapter. No commitment required on your end — I just want to make sure the data is genuinely useful to practitioners rather than sitting in a GitHub repo.

The full dataset, API documentation, and source pipeline are at https://github.com/nickgogerty/pcrbase.

Nick Gogerty, PCRbase
nickgogerty@gmail.com
