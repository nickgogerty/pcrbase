**To:** JRC-EPLCA@ec.europa.eu
**Subject:** Structured PCR data for EPLCA — open database of 290 machine-readable Product Category Rules

Dear EPLCA team,

I've built PCRbase (https://nickgogerty.github.io/pcrbase), an open, versioned database of 290 Product Category Rules from 7 program operators including all 22 EU PEFCRs, mapped to the COMET carbon ontology. The data is freely available as static JSON, RDF/Turtle, and JSON-LD under CC BY 4.0.

The EPLCA platform is the authoritative reference for EU environmental footprint data, and I believe there's a natural integration point: PCRbase provides the machine-readable PCR/PEFCR requirement layer that EPLCA's ILCD datasets currently lack — specifically, the normative method rules (system boundary, allocation, LCIA indicator sets, cut-off thresholds) that govern how each dataset was built. For CBAM verifiers and Green Deal procurement officers, linking an ILCD process dataset to its governing PEFCR requirements is increasingly mandatory, and right now that link doesn't exist in structured form anywhere.

I'd like to explore whether PCRbase data could be integrated as a reference layer in EPLCA — either as a linked dataset (the PCR RDF graph references ILCD process UUIDs) or as a supplementary metadata feed. I'm also open to contributing the PEFCR requirement data directly to the EPLCA repository under whatever licence terms the JRC requires.

The full technical documentation, API, and source code are at https://github.com/nickgogerty/pcrbase. Happy to arrange a call with the EPLCA technical team at your convenience.

Nick Gogerty, PCRbase
nickgogerty@gmail.com
