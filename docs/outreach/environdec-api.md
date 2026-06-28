**To:** info@environdec.com / api@environdec.com
**Subject:** PCR metadata collaboration — structured requirement data for the EnvironDec ecosystem

Hi EnvironDec/IVL team,

I'm the developer of PCRbase (https://nickgogerty.github.io/pcrbase), an open database that currently holds 227 of your published PCRs as structured, machine-readable requirement data — extracted from your PDFs, normalised into 65 clause vocabulary keys, and mapped to the COMET carbon ontology. The pipeline runs quarterly and tracks version changes automatically.

227 PCRs is a lot, but there's a meaningful gap: 54 entries are metadata-only because they're c-PCRs without standalone PDF documents, and your listing API returns 401 for unauthenticated enumeration. I'm reaching out because I think there's a mutual benefit in a lightweight data-sharing arrangement: I give EnvironDec a structured, versioned feed of requirement metadata extracted from your PCRs (useful for your own search/filter tooling and for the growing CBAM/Green Deal compliance market); in exchange, I get either a read-only API key or a bulk export of current PCR metadata to close the 54-entry gap and stay current faster than scraping.

The data is CC BY 4.0 with full attribution back to EnvironDec as the source operator. No commercial use without your consent. I'm happy to add whatever licensing headers you need to the dataset.

Would a short call with your data/API team make sense? I can walk through the pipeline, the COMET mapping, and how EPD practitioners are using the structured data.

Nick Gogerty, PCRbase
nickgogerty@gmail.com
https://github.com/nickgogerty/pcrbase
