"""LLM extractor (Haiku 4.5) — drop-in replacement for extract.extract_clauses().
Returns the SAME dict shape as the deterministic extractor so extract_all.py,
the span gate, and DB plumbing are unchanged:
  {clause_key, value_text, normalized_value, confidence, conf_bucket,
   source_page, source_span, span_verified}

Method:
  1. pull per-page text (pymupdf)
  2. send the page-numbered text + the controlled clause vocabulary to Haiku
  3. Haiku returns, per clause it can find: value, a VERBATIM source_quote,
     the page number, and a self-confidence 0-1
  4. span-verification gate (A4): the returned source_quote MUST be found in the
     cited page text (normalized whitespace). If not -> span_verified=False and
     confidence is capped so it routes to human review. Self-confidence never
     gates export on its own.
"""
import re, json, fitz
import clause_vocab
import llm_client

# Build a compact clause menu for the prompt (key: label [applies_to])
def _clause_menu():
    lines = []
    for (k, g, lbl, alt, app) in clause_vocab.CLAUSES:
        if k == "unclassified":
            continue
        lines.append(f"- {k}: {lbl}" + (f" (alt: {alt})" if alt else ""))
    return "\n".join(lines)

CLAUSE_MENU = _clause_menu()

SYSTEM = (
    "You are an expert LCA/EPD analyst extracting normative requirements from a "
    "Product Category Rule (PCR) document. You return STRICT JSON only. For each "
    "requirement you can locate, you MUST copy a VERBATIM quote (10-200 chars) "
    "from the provided text as evidence, and give the 1-based page number it came "
    "from. Never invent values. If a clause is absent, omit it. Non-English text: "
    "extract the value, translate the value to English in value_en, keep the "
    "verbatim original-language quote in source_quote."
)

PROMPT_TMPL = """Extract PCR requirements from the text below.

CLAUSE KEYS (use ONLY these keys):
{menu}

Return JSON: {{"requirements":[{{"clause_key","value_en","normalized_value","source_quote","page","confidence"}}]}}
- value_en: concise English value/answer for the clause
- normalized_value: structured value if applicable (date YYYY-MM-DD, number, percent, enum) else null
- source_quote: VERBATIM substring copied from the text (original language), 10-200 chars
- page: 1-based page number where the quote appears
- confidence: your 0..1 confidence

TEXT (page markers as [[P{{n}}]]):
{body}
"""

def extract_text_pages(pdf_path, max_pages=40):
    doc = fitz.open(pdf_path)
    n = min(doc.page_count, max_pages)
    return [doc[i].get_text() for i in range(n)]

def _norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()

def _conf_bucket(c):
    return "high" if c >= 0.85 else ("med" if c >= 0.6 else "low")

def _build_body(pages, char_budget=22000):
    """Concatenate page-marked text within a char budget (keeps cost down)."""
    out, total = [], 0
    for i, t in enumerate(pages, 1):
        seg = f"[[P{i}]]\n{t}\n"
        if total + len(seg) > char_budget:
            # include a trimmed head of remaining page then stop
            out.append(seg[: max(0, char_budget - total)])
            break
        out.append(seg); total += len(seg)
    return "".join(out)

def extract_clauses(pdf_path, max_pages=40):
    pages = extract_text_pages(pdf_path, max_pages=max_pages)
    if not pages:
        return []
    page_norm = {i + 1: _norm_ws(t) for i, t in enumerate(pages)}
    body = _build_body(pages)
    prompt = PROMPT_TMPL.format(menu=CLAUSE_MENU, body=body)
    raw = llm_client.call([{"role": "user", "content": prompt}], system=SYSTEM,
                          max_tokens=3000, temperature=0)
    # parse JSON (tolerate code fences / leading prose)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    valid_keys = {c[0] for c in clause_vocab.CLAUSES}
    out, seen = [], set()
    for r in data.get("requirements", []):
        ck = r.get("clause_key")
        if ck not in valid_keys or ck == "unclassified":
            # unknown key -> capture as unclassified (bottom-up signal, amendment A1)
            ck = "unclassified"
        quote = (r.get("source_quote") or "").strip()
        page = r.get("page") or 0
        try: page = int(page)
        except (ValueError, TypeError): page = 0
        # span-verification gate (A4): quote must appear in cited page (or any page)
        nq = _norm_ws(quote)
        span_verified = bool(nq) and (
            (page in page_norm and nq in page_norm[page]) or
            any(nq in pt for pt in page_norm.values())
        )
        try:
            self_conf = float(r.get("confidence", 0.5))
        except (ValueError, TypeError):
            self_conf = 0.5
        # if span unverifiable, cap confidence so it routes to review
        conf = self_conf if span_verified else min(self_conf, 0.4)
        # locate span offsets in the cited page for provenance
        src_span = None
        if span_verified and page in page_norm:
            # best-effort offset in raw page text
            idx = _norm_ws(pages[page - 1]).find(nq) if page <= len(pages) else -1
            if idx >= 0:
                src_span = f"~{idx}:{idx + len(nq)}"
        key = (ck, page, nq[:40])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "clause_key": ck,
            "value_text": (r.get("value_en") or quote)[:500],
            "normalized_value": r.get("normalized_value"),
            "confidence": round(conf, 2),
            "conf_bucket": _conf_bucket(conf),
            "source_page": page,
            "source_span": src_span or "0:0",
            "span_verified": span_verified,
        })
    return out

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_pcr.pdf"
    recs = extract_clauses(path)
    print(f"LLM extracted {len(recs)} clause hits from {path}")
    for r in sorted(recs, key=lambda x: -x["confidence"]):
        v = "✓" if r["span_verified"] else "✗"
        print(f"  [{r['conf_bucket']:4}] {r['confidence']:.2f} {v} {r['clause_key']:24} p{r['source_page']} | {r['value_text'][:64]!r}")
