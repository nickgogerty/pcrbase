"""PCRbase HTML dashboard generator — self-contained (inline CSS + SVG, no deps).
Queries pcrbase.duckdb and writes data/exports/dashboard.html.
Run: python src/dashboard.py  ->  open data/exports/dashboard.html
"""
import sys, os, datetime, html
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "exports", "dashboard.html")

PALETTE = ["#2dd4bf", "#60a5fa", "#f59e0b", "#a78bfa", "#f87171", "#34d399", "#fb923c", "#e879f9"]

# ── Newcomer tooltips: dict of term -> plain-language definition ──────────
# Auto-wrapped into the first occurrence in body prose by the inline JS below.
TOOLTIP_TERMS = {
    "PCR": "Product Category Rules \u2014 the methodology rulebook saying how to calculate and report the carbon footprint for a whole category of products. One PCR governs many EPDs.",
    "PCRs": "Product Category Rules \u2014 the methodology rulebooks for calculating product footprints. PCRbase inventories these (the rules), not the individual product declarations.",
    "EPD": "Environmental Product Declaration \u2014 one product's verified environmental label. A PCR defines the rules an EPD must follow; there are ~100\u00d7 more EPDs than PCRs.",
    "EPDs": "Environmental Product Declarations \u2014 verified per-product environmental labels (governed by PCRs).",
    "PEFCR": "Product Environmental Footprint Category Rules \u2014 the EU's method-specific category rules under its Product Environmental Footprint (PEF) framework.",
    "EAC": "Environmental Attribute Certificate \u2014 a tradeable proof of an environmental benefit (e.g. a carbon credit or renewable-energy certificate).",
    "COMET": "Carbon Ontology for Markets, Emissions & Trade \u2014 the shared vocabulary PCRbase maps every extracted rule onto, so data means the same thing across systems.",
    "ontology": "A shared, structured dictionary: an agreed list of terms and how they relate, so different systems mean the same thing by the same word.",
    "SHACL": "A W3C language for writing validation rules ('shapes') that check whether data follows the ontology's constraints \u2014 like a spell-checker for structured data.",
    "clause": "One normative requirement extracted from a PCR (e.g. 'declare modules A1\u2013A3'). PCRbase inventories rules at the clause level.",
    "requirement": "A single extracted rule-clause from a PCR document, with its source quote and a confidence score.",
    "span-verified": "The extractor located the exact verbatim sentence in the source PDF that backs this value \u2014 a guard against AI hallucination (panel rule A4).",
    "method family": "Which methodology standard a PCR follows \u2014 ISO 14067, EN 15804, or the EU PEF method.",
    "ISO 14067": "The international standard defining how to quantify a product's carbon footprint.",
    "EN 15804": "The European standard giving the core PCR for construction-product EPDs.",
    "assurance": "The level of confidence a verifier provides: 'limited' (lighter review) or 'reasonable' (deeper, audit-grade review).",
    "limited assurance": "A lighter-touch verification giving moderate confidence \u2014 the verifier checks for obvious errors but does less deep testing than 'reasonable' assurance.",
    "reasonable assurance": "Audit-grade verification giving high confidence \u2014 deeper, more rigorous testing than 'limited' assurance.",
    "Monte Carlo": "A statistical method that runs thousands of random simulations to estimate a range and its likely values, instead of a single guess.",
    "triangular": "A simple probability shape defined by three numbers \u2014 a low, a most-likely, and a high value \u2014 used here to model each segment's uncertain PCR count.",
    "P50": "The median \u2014 the middle of the simulated range, with a 50% chance the true value is higher and 50% lower.",
    "confidence interval": "A range that very likely contains the true value \u2014 here, a 90% interval means ~9 times out of 10 the real number falls inside it.",
    "provenance": "The traceable record of where each document came from and when it was retrieved (PCRbase stores a SHA-256 hash of every source PDF).",
    "CBAM": "EU Carbon Border Adjustment Mechanism \u2014 a charge on the embedded carbon of certain imports to match the EU's own carbon price.",
    "c-PCR": "A complementary PCR \u2014 a sub-rulebook that extends a parent PCR for a specific product type; often bundled inside the parent document.",
}

TOOLTIP_CSS = """
.cterm{border-bottom:1px dotted currentColor;cursor:help;position:relative}
.cterm::after{content:attr(data-tip);position:absolute;left:0;top:1.6em;z-index:9999;width:max-content;max-width:280px;background:#0b1120;color:#e2e8f0;border:1px solid #2dd4bf;border-radius:8px;padding:9px 12px;font-size:12px;font-weight:400;line-height:1.5;letter-spacing:normal;text-transform:none;box-shadow:0 8px 24px rgba(0,0,0,.5);opacity:0;transform:translateY(-4px);pointer-events:none;transition:opacity .14s,transform .14s}
.cterm::before{content:"";position:absolute;left:10px;top:calc(1.6em - 5px);z-index:10000;border:5px solid transparent;border-bottom-color:#2dd4bf;opacity:0;transition:opacity .14s}
.cterm:hover::after,.cterm:focus::after,.cterm.cterm-open::after,.cterm:hover::before,.cterm:focus::before,.cterm.cterm-open::before{opacity:1;transform:translateY(0);pointer-events:auto}
.cterm[data-tip-align="right"]::after{left:auto;right:0}.cterm[data-tip-align="right"]::before{left:auto;right:10px}
.cterm-legend{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#94a3b8;border:1px dashed #334155;border-radius:20px;padding:4px 12px;margin:14px 0 0}
.cterm-legend b{color:#2dd4bf}
"""


def tooltip_js():
    """Inline JS: auto-wrap the first occurrence of each glossary term in prose."""
    import json as _json
    terms_json = _json.dumps(TOOLTIP_TERMS, ensure_ascii=False)
    return """
<script>
(function(){
  var G=""" + terms_json + """;
  var SKIP={H1:1,H2:1,H3:1,H4:1,TH:1,CODE:1,PRE:1,A:1,BUTTON:1,SCRIPT:1,STYLE:1,SVG:1,CANVAS:1};
  function esc(s){return s.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&");}
  var keys=Object.keys(G).sort(function(a,b){return b.length-a.length;});
  var used={}, rx=new RegExp("\\\\b("+keys.map(esc).join("|")+")\\\\b");
  function inSkip(n){for(var p=n.parentNode;p&&p.nodeType===1;p=p.parentNode){if(SKIP[p.tagName])return true;if(p.classList&&(p.classList.contains("cterm")||p.classList.contains("no-tip")))return true;}return false;}
  function wrap(tn){
    var t=tn.nodeValue, m=rx.exec(t); if(!m)return;
    var key=m[1];
    if(used[key]){var tail=document.createTextNode(t.slice(m.index+m[1].length));tn.nodeValue=t.slice(0,m.index+m[1].length);tn.parentNode.insertBefore(tail,tn.nextSibling);wrap(tail);return;}
    used[key]=1;
    var sp=document.createElement("span");sp.className="cterm";sp.setAttribute("data-tip",G[key]);sp.setAttribute("tabindex","0");sp.textContent=m[1];
    var fr=document.createDocumentFragment();
    if(m.index)fr.appendChild(document.createTextNode(t.slice(0,m.index)));
    fr.appendChild(sp);
    var after=document.createTextNode(t.slice(m.index+m[1].length));fr.appendChild(after);
    tn.parentNode.replaceChild(fr,tn);
    requestAnimationFrame(function(){var r=sp.getBoundingClientRect();if(r.left>window.innerWidth*0.6)sp.setAttribute("data-tip-align","right");});
    if(after.nodeValue)wrap(after);
  }
  function run(){
    var scope=document.querySelector(".wrap")||document.body;
    var w=document.createTreeWalker(scope,NodeFilter.SHOW_TEXT,{acceptNode:function(n){return(n.nodeValue&&n.nodeValue.trim()&&!inSkip(n))?1:2;}});
    var ns=[],x;while((x=w.nextNode()))ns.push(x);
    ns.forEach(function(n){if(Object.keys(used).length<keys.length&&n.parentNode)wrap(n);});
    var h=document.querySelector("header");
    if(h){var c=document.createElement("div");c.className="cterm-legend no-tip";c.innerHTML="\\uD83D\\uDCA1 New here? <b>Dotted</b> terms have plain-language explanations \\u2014 hover or tap.";h.appendChild(c);}
    document.addEventListener("click",function(e){var t=e.target.closest(".cterm");document.querySelectorAll(".cterm.cterm-open").forEach(function(el){if(el!==t)el.classList.remove("cterm-open");});if(t)t.classList.toggle("cterm-open");});
    document.addEventListener("keydown",function(e){if(e.key==="Escape")document.querySelectorAll(".cterm.cterm-open").forEach(function(el){el.classList.remove("cterm-open");});});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",run);else run();
})();
</script>
"""

def q(con, sql, params=None):
    return con.execute(sql, params or []).fetchall()

def esc(s):
    return html.escape(str(s)) if s is not None else ""

def donut(segments, size=160, stroke=26, center_label=""):
    """segments: list of (label, value, color). Returns SVG string."""
    total = sum(v for _, v, _ in segments) or 1
    r = (size - stroke) / 2
    cx = cy = size / 2
    circ = 2 * 3.141592653589793 * r
    offset = 0
    arcs = []
    for label, value, color in segments:
        frac = value / total
        dash = frac * circ
        arcs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash
    label_svg = (f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-size="26" '
                 f'font-weight="700" fill="#e2e8f0">{esc(center_label)}</text>'
                 f'<text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="11" '
                 f'fill="#94a3b8">total</text>') if center_label else ""
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(arcs)}{label_svg}</svg>'

def hbars(rows, maxw=320, color="#60a5fa"):
    """rows: list of (label, value). Returns HTML bars."""
    mx = max((v for _, v in rows), default=1) or 1
    out = []
    for label, value in rows:
        w = int(maxw * value / mx)
        out.append(
            f'<div class="bar-row"><span class="bar-label">{esc(label)}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{w}px;background:{color}"></span></span>'
            f'<span class="bar-val">{value}</span></div>')
    return "".join(out)

def legend(segments):
    out = []
    for label, value, color in segments:
        out.append(f'<span class="leg"><span class="dot" style="background:{color}"></span>{esc(label)} <b>{value}</b></span>')
    return "".join(out)

def build():
    con = get_con()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # optional coverage report (from coverage.py)
    cov = None
    cov_path = os.path.join(os.path.dirname(__file__), "..", "data", "exports", "coverage.json")
    if os.path.exists(cov_path):
        try:
            with open(cov_path) as f:
                cov = __import__("json").load(f)
        except Exception:
            cov = None

    # headline metrics
    n_ops, n_open = q(con, "SELECT count(*), sum(CASE WHEN access='open' THEN 1 ELSE 0 END) FROM operator")[0]
    n_pcr = q(con, "SELECT count(*) FROM pcr")[0][0]
    n_ver = q(con, "SELECT count(*) FROM pcr_version")[0][0]
    n_doc = q(con, "SELECT count(*) FROM source_document")[0][0]
    n_req = q(con, "SELECT count(*) FROM requirement")[0][0]
    n_verif = q(con, "SELECT count(*) FROM requirement WHERE span_verified")[0][0]
    n_vocab = q(con, "SELECT count(*) FROM clause_vocab")[0][0]
    n_triples_est = q(con, "SELECT count(*) FROM requirement WHERE span_verified")[0][0]  # rough

    # distributions
    by_type = q(con, "SELECT pcr_type, count(*) FROM pcr GROUP BY 1 ORDER BY 2 DESC")
    by_op = q(con, "SELECT operator_id, count(*) FROM pcr GROUP BY 1 ORDER BY 2 DESC")
    conf = dict(q(con, "SELECT conf_bucket, count(*) FROM requirement GROUP BY 1"))
    mapping = q(con, "SELECT mapping_status, count(*) FROM comet_mapping GROUP BY 1 ORDER BY 2 DESC")
    backend = q(con, "SELECT CASE WHEN extract_run_id LIKE 'extract-llm%' THEN 'LLM (Haiku 4.5)' ELSE 'regex' END, count(*) FROM requirement GROUP BY 1 ORDER BY 2 DESC")
    method = q(con, """SELECT p.method_family, count(DISTINCT p.pcr_id)
                       FROM pcr p GROUP BY 1 ORDER BY 2 DESC""")

    # gap log (PR backlog)
    gaps = q(con, """SELECT clause_key, proposed_comet_addition, occurrence_count
                     FROM gap_log ORDER BY occurrence_count DESC LIMIT 14""")
    # top clauses
    topclauses = q(con, """SELECT clause_key, count(*) FROM requirement
                           GROUP BY 1 ORDER BY 2 DESC LIMIT 12""")
    # recent PCRs table
    recent = q(con, """SELECT p.operator_id, p.pcr_number, substr(p.title,1,60), p.pcr_type,
                              p.method_family, v.valid_until
                       FROM pcr p JOIN pcr_version v ON v.pcr_id=p.pcr_id
                       ORDER BY p._loaded_at DESC LIMIT 16""")
    # harvest health
    health = q(con, """SELECT operator_id, found_count, alert FROM harvest_health
                       WHERE run_id IN (SELECT max(run_id) FROM harvest_health GROUP BY operator_id)
                       ORDER BY found_count DESC""")

    # ── SOURCE DATA / corpus provenance ──────────────────────────────────
    doc_rows = q(con, "SELECT blob_path, pages, lang FROM source_document")
    src_total_bytes = sum(os.path.getsize(p) for p, _, _ in doc_rows if p and os.path.exists(p))
    src_pages = [pg for _, pg, _ in doc_rows if pg]
    src_total_pages = sum(src_pages)
    src_median_pages = sorted(src_pages)[len(src_pages) // 2] if src_pages else 0
    src_max_pages = max(src_pages) if src_pages else 0
    src_lang = q(con, "SELECT lang, count(*) FROM source_document GROUP BY 1 ORDER BY 2 DESC")
    # retrieval window
    retr_min, retr_max = q(con, "SELECT min(retrieved_at), max(retrieved_at) FROM source_document")[0]
    # validity / age of the underlying rules
    val_present = q(con, "SELECT count(*) FROM pcr_version WHERE valid_until IS NOT NULL")[0][0]
    val_min, val_max = q(con, "SELECT min(valid_until), max(valid_until) FROM pcr_version")[0]
    n_expired = q(con, "SELECT count(*) FROM pcr_version WHERE valid_until < CURRENT_DATE")[0][0]
    n_current = q(con, "SELECT count(*) FROM pcr_version WHERE valid_until >= CURRENT_DATE")[0][0]
    val_by_year = q(con, """SELECT CAST(EXTRACT(year FROM valid_until) AS INT), count(*)
                            FROM pcr_version WHERE valid_until IS NOT NULL
                            GROUP BY 1 ORDER BY 1""")
    # page-size distribution buckets
    page_buckets = []
    for lo, hi, lbl in [(0, 15, "1–14 pp"), (15, 30, "15–29 pp"), (30, 60, "30–59 pp"),
                        (60, 9999, "60+ pp")]:
        nb = q(con, "SELECT count(*) FROM source_document WHERE pages>=? AND pages<?", [lo, hi])[0][0]
        page_buckets.append((lbl, nb))
    con.close()

    # color maps
    type_seg = [(t, v, PALETTE[i % len(PALETTE)]) for i, (t, v) in enumerate(by_type)]
    conf_seg = [("high", conf.get("high", 0), "#34d399"), ("med", conf.get("med", 0), "#f59e0b"), ("low", conf.get("low", 0), "#f87171")]
    map_colors = {"exact": "#34d399", "extended": "#60a5fa", "lossy": "#f59e0b", "unmapped": "#f87171"}
    map_seg = [(s, v, map_colors.get(s, "#94a3b8")) for s, v in mapping]

    verif_pct = round(100 * n_verif / n_req) if n_req else 0

    # coverage section (optional)
    cov_html = ""
    if cov:
        c = cov
        cgl = c["coverage_global_pct_mid"]
        cgr = c["coverage_global_pct_range"]
        cen = c["coverage_of_enumerated_pct"]
        cost = c["cost"]
        # universe table sorted by high estimate
        urows = sorted(c["universe_table"], key=lambda x: -x["high"])
        utbody = ""
        for u in urows:
            ing = u["ingested"]
            enum = u["enumerated"]
            status = ("<span class='badge g-ready'>ingested</span>" if ing > 0
                      else ("<span class='badge g-below'>enumerated</span>" if enum
                            else "<span class='pill'>not started</span>"))
            acc = "🔒" if u["access"] == "gated" else ""
            utbody += (f"<tr><td>{esc(u['name'])} {acc}</td><td>{esc(u['region'])}</td>"
                       f"<td style='text-align:right'>{u['low']}–{u['high']}</td>"
                       f"<td style='text-align:right'>{ing or '—'}</td><td>{status}</td></tr>")

        # ── statistical estimate card (Monte Carlo) ──
        stat_html = ""
        mc = c.get("universe_statistical")
        if mc:
            span = max(mc["p95"] - mc["p5"], 1)
            def _x(v):  # position 0–100 across the p5..p95 axis
                return max(0, min(100, round(100 * (v - mc["p5"]) / span)))
            naive_low, naive_high = c["universe_low"], c["universe_high"]
            stat_html = f"""
  <div class="card full"><h3>How many PCRs exist globally? <span>— statistical estimate (Monte Carlo, {mc['trials']:,} trials)</span></h3>
    <div class="grid" style="grid-template-columns:1fr 1fr;margin-top:0">
      <div>
        <div style="font-size:13px;line-height:1.7;color:var(--mut)">
        Each of the {c['operators_universe']} segments is modelled as a <b>triangular(low, mode, high)</b> distribution (mode = hard enumerated count where known, else band midpoint), then summed over {mc['trials']:,} independent draws. Summing the segment lows/highs naively assumes every segment hits its extreme at once (perfect correlation); the independent sum is the statistically correct, tighter interval.</div>
        <div class="kpis" style="margin:14px 0 0">
          <div class="kpi" style="padding:10px 12px"><div class="n" style="font-size:22px">{mc['p50']:,}</div><div class="l">median (P50)</div></div>
          <div class="kpi" style="padding:10px 12px"><div class="n" style="font-size:22px">{mc['mean']:,}</div><div class="l">mean</div></div>
          <div class="kpi" style="padding:10px 12px"><div class="n" style="font-size:18px">{mc['p5']:,}–{mc['p95']:,}</div><div class="l">90% CI (P5–P95)</div></div>
        </div>
      </div>
      <div>
        <div class="note" style="margin-top:2px">distribution of the global total</div>
        <div style="position:relative;height:54px;margin:14px 0 6px">
          <div style="position:absolute;left:{_x(mc['p25'])}%;width:{_x(mc['p75'])-_x(mc['p25'])}%;top:14px;height:22px;background:#2dd4bf33;border:1px solid #2dd4bf;border-radius:4px"></div>
          <div style="position:absolute;left:{_x(mc['p50'])}%;top:8px;height:34px;width:2px;background:#2dd4bf"></div>
          <div style="position:absolute;left:0;top:24px;width:100%;height:2px;background:#1e293b"></div>
          <div style="position:absolute;left:{_x(mc['mean'])}%;top:12px;font-size:10px;color:#2dd4bf;transform:translateX(-50%)">▼</div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10.5px;color:var(--mut)">
          <span>P5 · {mc['p5']:,}</span><span>P50 · {mc['p50']:,}</span><span>P95 · {mc['p95']:,}</span></div>
        <div class="note" style="margin-top:12px">Naive sum-of-bands for comparison: <b>{naive_low:,}–{naive_high:,}</b> (±{round(100*(naive_high-naive_low)/2/c['universe_mid'])}%). Monte-Carlo 90% CI is <b>±{round(100*(mc['p95']-mc['p5'])/2/mc['p50'])}%</b> — uncertainty shrinks because segment errors partly cancel.</div>
      </div>
    </div>
  </div>"""

        # ── representativeness by language + sector ──
        repr_html = ""
        langs = c.get("by_language") or []
        sects = c.get("by_sector") or []
        if langs and sects:
            def covbar(rows, namer=lambda k: k):
                out = ""
                mxu = max((r["universe_mid"] for r in rows), default=1) or 1
                for r in rows:
                    uw = int(300 * r["universe_mid"] / mxu)
                    cov = r["coverage_pct"]
                    cw = int(uw * min(cov, 100) / 100)
                    out += (f'<div class="bar-row"><span class="bar-label" style="width:120px">{esc(namer(r["key"]))}</span>'
                            f'<span class="bar-track" style="background:#0f1727;position:relative">'
                            f'<span style="display:block;height:16px;width:{uw}px;background:#334155;border-radius:5px;position:absolute"></span>'
                            f'<span style="display:block;height:16px;width:{cw}px;background:#2dd4bf;border-radius:5px;position:absolute"></span></span>'
                            f'<span class="bar-val" style="width:88px;text-align:left">{r["universe_mid"]:,} · <b style="color:#2dd4bf">{cov:.0f}%</b></span></div>')
                return out
            en = c.get("english_share_pct", 0)
            cons = c.get("construction_share_pct", 0)
            repr_html = f"""
  <div class="card"><h3>Representativeness by language <span>— univ. (grey) vs ingested (teal)</span></h3>
    {covbar(langs)}
    <div class="note">~<b>{en:.0f}%</b> of the global PCR universe is English-first; the long tail is KO/JA (gated Asia), DE, IT, FR, ES/PT. PCRbase has proven non-English extraction (NO) but Asian-language coverage is <b>0%</b> — the biggest representativeness gap.</div>
  </div>
  <div class="card"><h3>Representativeness by sector <span>— univ. (grey) vs ingested (teal)</span></h3>
    {covbar(sects)}
    <div class="note">~<b>{cons:.0f}%</b> of all PCRs are <b>Construction</b> (EN 15804 dominance). PCRbase's ingested set skews to EnvironDec's cross-sector mix, so Food/Agriculture coverage is high while Electronics/HVAC (PEP-dominated) is near <b>0%</b>.</div>
  </div>"""

        cov_html = f"""
<h2 class="sec">Coverage &amp; representativeness <span class="tag">— vs the global PCR universe</span></h2>
<div class="kpis">
  <div class="kpi"><div class="n">{cgl}%</div><div class="l">of global universe (~{c['universe_mid']:,} PCRs)</div><div class="s">range {cgr[0]}–{cgr[1]}%</div></div>
  <div class="kpi"><div class="n">{cen}%</div><div class="l">of enumerated operators</div><div class="s">{c['enumerated_hard']} hard-counted PCRs</div></div>
  <div class="kpi"><div class="n">{c['operators_touched']}/{c['operators_universe']}</div><div class="l">segments touched</div><div class="s">3/3 method families · 3 langs</div></div>
  <div class="kpi"><div class="n">${cost['total_one_time_usd']:,.0f}</div><div class="l">to complete (~{c['universe_mid']:,} PCRs)</div><div class="s">LLM only ${cost['llm_extraction_usd']:,.0f}</div></div>
  <div class="kpi"><div class="n">{cost['human_review_hours']:.0f} h</div><div class="l">human review to complete</div><div class="s">the binding constraint</div></div>
  <div class="kpi"><div class="n">${cost['quarterly_reharvest_llm_usd']:,.0f}</div><div class="l">/quarter re-harvest (LLM)</div><div class="s">living-DB compute</div></div>
</div>
<div class="grid">
  <div class="card"><h3>Indicative, not representative <span>(why)</span></h3>
    <div class="note" style="font-size:13px;line-height:1.7">
    <b>EPDs ≠ PCRs.</b> ECO Platform reports ~33,009 <i>EPDs</i> across 22 operators — but those are governed by only ~600–750 <i>PCRs</i> (the rules PCRbase inventories). The global PCR universe is ~1,120–2,050 (mid ~1,586).<br><br>
    Current DB = <b>43 PCRs / 4 programs</b> → <b>{cgl}% of universe</b>. <br>
    But <b>method &amp; language diversity is fully proven</b>: all 3 method families (ISO 14067, EN 15804, PEF) and non-English extraction (Norwegian) work end-to-end. The gap is <b>volume &amp; geography</b> (no US/Asia yet), not capability.</div>
  </div>
  <div class="card"><h3>Cost structure to complete</h3>
    {hbars([("LLM extract", cost['llm_extraction_usd']), ("Adapter eng", cost['adapter_eng_usd']), ("Human review", cost['human_review_usd'])], color="#f59e0b")}
    <div class="note">Compute is trivially cheap (~$23 for the <i>entire</i> universe). The cost is human review (~80%) + building ~13 operator adapters. Living maintenance ≈ ${cost['quarterly_reharvest_llm_usd']*4:,.0f}/yr compute.</div>
  </div>
  <div class="card full"><h3>Global PCR universe — gap by segment</h3>
    <table><thead><tr><th>operator / segment</th><th>region</th><th style="text-align:right">est. PCRs</th><th style="text-align:right">ingested</th><th>status</th></tr></thead>
    <tbody>{utbody}</tbody></table>
    <div class="note">🔒 = gated / non-English (metadata-only until acquired). Estimates have wide error bars; only per-operator enumeration tightens them.</div>
  </div>
{stat_html}{repr_html}</div>
"""

    # gap rows
    gap_rows = ""
    for ck, add, occ in gaps:
        gate = "ready" if (occ or 0) >= 3 else "below"
        badge = f'<span class="badge {"g-ready" if gate=="ready" else "g-below"}">{"PR-ready" if gate=="ready" else "below thr."}</span>'
        gap_rows += f'<tr><td>{esc(ck)}</td><td class="mono">{esc(add or "—")}</td><td style="text-align:right">{occ}</td><td>{badge}</td></tr>'

    recent_rows = ""
    for op, num, title, ptype, mf, valid in recent:
        recent_rows += (f'<tr><td><span class="op op-{esc(op)}">{esc(op)}</span></td>'
                        f'<td class="mono">{esc(num)}</td><td>{esc(title)}</td>'
                        f'<td><span class="pill">{esc(ptype)}</span></td>'
                        f'<td>{esc(mf)}</td><td>{esc(valid or "—")}</td></tr>')

    health_rows = ""
    for op, found, alert in health:
        dotc = "#f87171" if alert else "#34d399"
        health_rows += f'<span class="leg"><span class="dot" style="background:{dotc}"></span>{esc(op)} <b>{found}</b></span>'

    # ── source-data / corpus provenance section ──
    def _d(dt):
        return dt.strftime("%Y-%m-%d") if dt else "—"
    lang_names = {"en": "English", "no": "Norwegian", "de": "German",
                  "fr": "French", "it": "Italian", None: "unlabelled"}
    lang_seg = [(lang_names.get(l, l or "unlabelled"), v, PALETTE[i % len(PALETTE)])
                for i, (l, v) in enumerate(src_lang)]
    src_mb = src_total_bytes / 1e6
    avg_mb = src_mb / n_doc if n_doc else 0
    pct_current = round(100 * n_current / (n_current + n_expired)) if (n_current + n_expired) else 0
    # validity-year bars (rules expiring per year — the 'age/freshness' signal)
    vy_max = max((n for _, n in val_by_year), default=1) or 1
    vy_bars = ""
    this_year = datetime.datetime.now().year
    for yr, n in val_by_year:
        w = int(260 * n / vy_max)
        past = yr < this_year
        col = "#f87171" if past else "#34d399"
        vy_bars += (f'<div class="bar-row"><span class="bar-label" style="width:42px">{yr}</span>'
                    f'<span class="bar-track"><span class="bar-fill" style="width:{w}px;background:{col}"></span></span>'
                    f'<span class="bar-val">{n}</span></div>')

    src_html = f"""
<h2 class="sec">Source data <span class="tag">— the underlying document corpus (provenance)</span></h2>
<div class="kpis">
  <div class="kpi"><div class="n">{n_doc}</div><div class="l">source PDFs on disk</div><div class="s">every blob SHA-256 hashed</div></div>
  <div class="kpi"><div class="n">{src_mb:,.0f} MB</div><div class="l">total corpus size</div><div class="s">~{avg_mb:.2f} MB/doc avg</div></div>
  <div class="kpi"><div class="n">{src_total_pages:,}</div><div class="l">pages of source rules</div><div class="s">median {src_median_pages} · max {src_max_pages} pp</div></div>
  <div class="kpi"><div class="n">{len(src_lang)}</div><div class="l">document languages</div><div class="s">{", ".join(lang_names.get(l, l or "?") for l, _ in src_lang[:3])}</div></div>
  <div class="kpi"><div class="n">{pct_current}%</div><div class="l">rules currently valid</div><div class="s">{n_current} current · {n_expired} expired</div></div>
  <div class="kpi"><div class="n">{_d(retr_min)}</div><div class="l">corpus harvested since</div><div class="s">latest {_d(retr_max)}</div></div>
</div>
<div class="grid">
  <div class="card"><h3>Document language <span>(of {n_doc} PDFs)</span></h3>
    <div class="donut-wrap">{donut(lang_seg, center_label=str(n_doc))}
    <div class="legends">{legend(lang_seg)}</div></div>
    <div class="note">Language is the document's publication language. Non-English rules (Norwegian, German) are extracted to English values with original-language verbatim quotes retained (span gate A4).</div></div>

  <div class="card"><h3>Document size <span>(pages per PDF)</span></h3>
    {hbars([(lbl, n) for lbl, n in page_buckets], color="#60a5fa")}
    <div class="note">{src_total_pages:,} pages total across {n_doc} documents · median {src_median_pages} pp · longest {src_max_pages} pp. Corpus footprint ~{src_mb:,.0f} MB on disk.</div></div>

  <div class="card"><h3>Age &amp; freshness <span>(PCR versions by valid-until year)</span></h3>
    {vy_bars}
    <div class="note"><span style="color:#34d399">green</span> = still valid · <span style="color:#f87171">red</span> = expired (valid-until &lt; today). {val_present} of {n_ver} versions carry an explicit validity date, spanning {_d(val_min)} → {_d(val_max)}. {n_expired} expired versions are kept deliberately (living, versioned history).</div></div>
</div>
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PCRbase — Dashboard</title>
<style>
:root{{--bg:#0b1120;--card:#131c2e;--card2:#0f1727;--bd:#1e293b;--tx:#e2e8f0;--mut:#94a3b8;--ac:#2dd4bf}}
*{{box-sizing:border-box}}
body{{margin:0;background:linear-gradient(160deg,#0b1120,#0d1424);color:var(--tx);font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 22px 60px}}
header{{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:6px}}
h1{{font-size:26px;margin:0;letter-spacing:-.5px}}
h1 .dot{{color:var(--ac)}}
.sub{{color:var(--mut);font-size:13px}}
.tag{{color:var(--mut);font-size:12px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:12px;margin:20px 0 8px}}
.kpi{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 16px}}
.kpi .n{{font-size:28px;font-weight:700;letter-spacing:-1px}}
.kpi .l{{color:var(--mut);font-size:12px;margin-top:2px}}
.kpi .s{{color:var(--ac);font-size:11px;margin-top:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-top:16px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px}}
.card h3{{margin:0 0 14px;font-size:14px;font-weight:600;color:#cbd5e1;letter-spacing:.2px}}
.card h3 span{{color:var(--mut);font-weight:400;font-size:12px}}
.donut-wrap{{display:flex;align-items:center;gap:18px;flex-wrap:wrap}}
.legends{{display:flex;flex-direction:column;gap:6px}}
.leg{{font-size:12px;color:var(--mut)}}.leg b{{color:var(--tx)}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:middle}}
.bar-row{{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:12px}}
.bar-label{{width:92px;color:var(--mut);text-align:right;flex-shrink:0}}
.bar-track{{flex:1;background:var(--card2);border-radius:5px;height:16px;overflow:hidden}}
.bar-fill{{display:block;height:16px;border-radius:5px}}
.bar-val{{width:36px;text-align:right;color:var(--tx);font-weight:600}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{text-align:left;color:var(--mut);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--bd);font-size:11px;text-transform:uppercase;letter-spacing:.4px}}
td{{padding:6px 8px;border-bottom:1px solid #16203200}}
tr:nth-child(even) td{{background:#0f172a55}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:#cbd5e1}}
.badge{{font-size:10.5px;padding:2px 7px;border-radius:20px;font-weight:600}}
.g-ready{{background:#064e3b;color:#6ee7b7}}.g-below{{background:#3f2d12;color:#fcd34d}}
.pill{{background:#1e293b;color:#cbd5e1;font-size:10.5px;padding:2px 8px;border-radius:20px}}
.op{{font-size:11px;padding:2px 7px;border-radius:6px;background:#1e293b;color:#cbd5e1}}
.full{{grid-column:1/-1}}
.barpct{{height:10px;background:var(--card2);border-radius:6px;overflow:hidden;margin-top:8px}}
.barpct>span{{display:block;height:10px;background:linear-gradient(90deg,#2dd4bf,#34d399)}}
footer{{color:var(--mut);font-size:11.5px;margin-top:26px;text-align:center}}
.note{{color:var(--mut);font-size:11.5px;margin-top:10px;line-height:1.5}}
.sec{{font-size:18px;margin:34px 0 4px;padding-top:18px;border-top:1px solid var(--bd);letter-spacing:-.3px}}
.sec .tag{{font-weight:400;font-size:13px}}
</style></head>
<body><div class="wrap">
<header>
  <div><h1>PCR<span class="dot">base</span> <span class="tag">· dashboard</span></h1>
  <div class="sub">Product Category Rule inventory → mapped onto the COMET ontology · <b style="color:var(--ac)">{n_pcr} PCRs</b> across {n_ops} operators</div></div>
  <div class="tag">generated {ts}</div>
</header>

<div class="kpis">
  <div class="kpi"><div class="n">{n_ops}</div><div class="l">operators (known universe)</div><div class="s">{n_open} open · {n_ops-n_open} gated</div></div>
  <div class="kpi"><div class="n">{n_pcr}</div><div class="l">PCRs inventoried</div><div class="s">{n_ver} versions</div></div>
  <div class="kpi"><div class="n">{n_doc}</div><div class="l">source PDFs</div><div class="s">w/ provenance + SHA-256</div></div>
  <div class="kpi"><div class="n">{n_req}</div><div class="l">requirements extracted</div><div class="s">{verif_pct}% span-verified</div></div>
  <div class="kpi"><div class="n">{n_vocab}</div><div class="l">clause vocab keys</div><div class="s">v1-seed · validated bottom-up</div></div>
  <div class="kpi"><div class="n">4</div><div class="l">programs live</div><div class="s">EN · NO · PEF · DE</div></div>
</div>
{src_html}
<div class="grid">
  <div class="card"><h3>PCRs by type</h3>
    <div class="donut-wrap">{donut(type_seg, center_label=str(n_pcr))}
    <div class="legends">{legend(type_seg)}</div></div></div>

  <div class="card"><h3>Extraction confidence <span>(span gate = A4)</span></h3>
    <div class="donut-wrap">{donut(conf_seg, center_label=str(n_req))}
    <div class="legends">{legend(conf_seg)}</div></div>
    <div class="barpct"><span style="width:{verif_pct}%"></span></div>
    <div class="note">{n_verif} of {n_req} requirements have a verbatim source quote located in the document.</div></div>

  <div class="card"><h3>COMET mapping ledger</h3>
    <div class="donut-wrap">{donut(map_seg, center_label=str(sum(v for _,v in mapping)))}
    <div class="legends">{legend(map_seg)}</div></div>
    <div class="note">exact = existing COMET class fits · extended = new class proposed · unmapped = gap → PR backlog</div></div>

  <div class="card"><h3>PCRs by operator</h3>{hbars([(o, v) for o, v in by_op], color="#60a5fa")}</div>

  <div class="card"><h3>Method family</h3>{hbars([(m or "?", v) for m, v in method], color="#a78bfa")}</div>

  <div class="card"><h3>Extractor backend</h3>{hbars([(b, v) for b, v in backend], color="#2dd4bf")}
    <div class="note">LLM extractor is a drop-in replacement (same dict shape + span gate).</div></div>

  <div class="card"><h3>Top extracted clauses</h3>{hbars([(c, v) for c, v in topclauses], color="#34d399")}</div>

  <div class="card"><h3>Harvest health <span>(A8 watchdog)</span></h3>
    <div class="legends" style="flex-direction:row;flex-wrap:wrap;gap:14px">{health_rows}</div>
    <div class="note">Latest found-count per operator adapter. Red = zero-result alert.</div></div>

  <div class="card full"><h3>COMET PR backlog <span>(gap_log · evidence-gated ≥3 occ)</span></h3>
    <table><thead><tr><th>clause key</th><th>proposed COMET addition</th><th style="text-align:right">occ</th><th>gate</th></tr></thead>
    <tbody>{gap_rows}</tbody></table></div>

  <div class="card full"><h3>Recent PCRs ingested</h3>
    <table><thead><tr><th>operator</th><th>number</th><th>title</th><th>type</th><th>method</th><th>valid until</th></tr></thead>
    <tbody>{recent_rows}</tbody></table></div>
</div>
{cov_html}

<footer>PCRbase v0.2 · DuckDB system-of-record → generated RDF/JSON-LD aligned to COMET · clause-level inventory, COMET-as-constraints, living &amp; versioned</footer>
</div></body></html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html_doc)
    print(f"Dashboard -> {os.path.abspath(OUT)}")
    return OUT

if __name__ == "__main__":
    build()
