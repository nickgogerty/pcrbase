"""P3 extraction — section-anchored clause extractor with span verification (A4).

Pragmatic v1: deterministic, auditable extraction that locates evidence spans
for each clause_key using anchor phrases derived from the clause vocab + PCR
domain patterns. Each extracted requirement carries:
  - value_text (the evidence span actually found in the document)
  - normalized_value (parsed where structured: dates, %, enums)
  - confidence (heuristic: anchor specificity + value-pattern match)
  - source_page, source_span (char offsets within page)
  - span_verified (the normalized value is substring-verifiable in the span; A4)

This is the LLM-ready scaffold: swap _match_clause() for an LLM call returning
the same dict shape; the span-verification gate and DB plumbing stay identical.
"""
import re, fitz

# Anchor phrases per clause_key: (regex, base_confidence). Highly specific
# anchors get higher base confidence. Value extracted from surrounding window.
ANCHORS = {
    "id.pub_date":      [(r'PUBLICATION DATE[:\s]*(\d{4}-\d{2}-\d{2})', 0.95)],
    "id.valid_until":   [(r'VALID UNTIL[:\s]*(\d{4}-\d{2}-\d{2})', 0.95)],
    "id.pcr_number":    [(r'\bPCR\s*(\d{4}[:\-]\d{2,3})\b', 0.9)],
    "id.version":       [(r'VERSION[:\s]*(\d+\.\d+(?:\.\d+)?)', 0.9)],
    "id.cpc_code":      [(r'UN CPC\s*([0-9]{3,5})', 0.9)],
    "unit.value":       [(r'(?:declared|functional)\s+unit[^.]{0,120}', 0.7),
                         (r'\b1\s*(?:kg|tonne|m2|m3|m²|m³|piece|MJ|kWh)\b[^.]{0,80}', 0.55)],
    "unit.type":        [(r'\b(declared unit|functional unit)\b', 0.8)],
    "boundary.type":    [(r'\b(cradle[- ]to[- ]gate|cradle[- ]to[- ]grave|gate[- ]to[- ]gate|cradle[- ]to[- ]gate with options)\b', 0.85)],
    "boundary.modules_declared": [(r'\b(A1[-–]A3|A1, A2, A3|modules?\s+A1|B1[-–]B7|C1[-–]C4|module D)\b', 0.75)],
    "alloc.coproduct":  [(r'alloc[a-z]+[^.]{0,160}', 0.6)],
    "alloc.cff":        [(r'(circular footprint formula|CFF)[^.]{0,120}', 0.8)],
    "cutoff.mass":      [(r'cut[- ]off[^.]{0,140}', 0.6),
                         (r'(\d{1,2}\s?%)[^.]{0,40}(mass|cut[- ]off)', 0.7)],
    "dq.primary_share": [(r'(primary|specific) data[^.]{0,140}', 0.6)],
    "dq.scoring":       [(r'data quality (rating|requirement|indicator|DQR)[^.]{0,140}', 0.65)],
    "lcia.gwp_method":  [(r'(GWP[- ]?100|global warming potential)[^.]{0,120}', 0.7),
                         (r'(IPCC\s+AR\d|EF\s?3\.\d)[^.]{0,80}', 0.7)],
    "lcia.indicator_set":[(r'(impact categor|environmental impact indicator)[^.]{0,140}', 0.6)],
    "lcia.biogenic":    [(r'biogenic\s+(carbon|CO2|CO₂)[^.]{0,120}', 0.7)],
    "scenario.rsl":     [(r'(reference service life|RSL)[^.]{0,120}', 0.75)],
    "content.substances":[(r'(SVHC|REACH|dangerous substances|hazardous substance)[^.]{0,120}', 0.7)],
    "report.verification_type":[(r'(EPD\s+verification|independent verification|internal|external)[^.]{0,100}(verif)', 0.55),
                         (r'verification[^.]{0,40}(internal|external|independent)', 0.6)],
    "id.standard_basis":[(r'(ISO 14025|ISO 14040|ISO 14044|ISO 14067|ISO 21930|EN 15804)[^.]{0,80}', 0.75)],
}

NORMALIZERS = {
    "id.pub_date": lambda m: m,
    "id.valid_until": lambda m: m,
    "id.version": lambda m: m,
    "id.cpc_code": lambda m: m,
}

def extract_text_pages(pdf_path):
    doc = fitz.open(pdf_path)
    return [doc[i].get_text() for i in range(doc.page_count)]

def _conf_bucket(c):
    return "high" if c >= 0.85 else ("med" if c >= 0.6 else "low")

def extract_clauses(pdf_path):
    """Return list of requirement dicts for one PDF."""
    pages = extract_text_pages(pdf_path)
    out = []
    seen = set()
    for clause_key, patterns in ANCHORS.items():
        for pat, base_conf in patterns:
            rx = re.compile(pat, re.I)
            for pno, text in enumerate(pages, 1):
                m = rx.search(text)
                if not m:
                    continue
                span_text = m.group(0).strip()
                # captured normalized value if a group exists
                norm = None
                if m.groups():
                    norm = next((g for g in m.groups() if g), None)
                # span verification gate (A4): normalized value must appear in span
                span_verified = bool(norm and norm in span_text)
                conf = base_conf if (not norm or span_verified) else base_conf * 0.5
                key = (clause_key, pno)
                if key in seen:
                    continue
                seen.add(key)
                start = m.start()
                out.append({
                    "clause_key": clause_key,
                    "value_text": span_text[:500],
                    "normalized_value": norm,
                    "confidence": round(conf, 2),
                    "conf_bucket": _conf_bucket(conf),
                    "source_page": pno,
                    "source_span": f"{start}:{m.end()}",
                    "span_verified": span_verified,
                })
                break  # first hit per clause/pattern is enough
    return out

if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_pcr.pdf"
    recs = extract_clauses(path)
    print(f"Extracted {len(recs)} clause hits from {path}")
    for r in sorted(recs, key=lambda x: -x["confidence"]):
        print(f"  [{r['conf_bucket']:4}] {r['confidence']:.2f} {r['clause_key']:24} p{r['source_page']} | {r['value_text'][:70]!r}")
