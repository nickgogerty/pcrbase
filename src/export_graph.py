"""P5 graph generation — deterministic DuckDB -> RDF/Turtle + JSON-LD,
aligned to COMET (decision B: generated layer, never hand-maintained).
One named graph per pcr_version. COMET @context injected.
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "exports")

PREFIXES = """@prefix comet: <https://comet.carbon/v1/core#> .
@prefix comet-pcf: <https://comet.carbon/v1/pcf#> .
@prefix comet-sc: <https://comet.carbon/v1/supplychain#> .
@prefix comet-ver: <https://comet.carbon/v1/ver#> .
@prefix pcrbase: <https://pcrbase.org/v1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") if s else ""

def export_turtle():
    con = get_con()
    os.makedirs(EXPORT_DIR, exist_ok=True)
    rows = con.execute("""
        SELECT v.version_id, p.pcr_number, p.title, p.pcr_type, p.cpc_code,
               v.version_label, v.valid_until, v.source_url, p.operator_id
        FROM pcr_version v JOIN pcr p ON v.pcr_id=p.pcr_id
    """).fetchall()
    lines = [PREFIXES]
    for (vid, num, title, ptype, cpc, vlabel, valid, url, op) in rows:
        subj = f"pcrbase:{vid}"
        lines.append(f"\n{subj} a comet-pcf:PCRDocument ;")
        lines.append(f'    dcterms:title "{esc(title)}" ;')
        if num:   lines.append(f'    comet-pcf:pcrNumber "{esc(num)}" ;')
        if vlabel:lines.append(f'    comet-pcf:version "{esc(vlabel)}" ;')
        if cpc:   lines.append(f'    comet-pcf:scopeCPC "{esc(cpc)}" ;')
        if valid: lines.append(f'    comet-pcf:validUntil "{valid}"^^xsd:date ;')
        lines.append(f'    comet-pcf:programOperator pcrbase:operator-{op} ;')
        if url:   lines.append(f'    prov:wasDerivedFrom <{url}> ;')
        # attach requirements as mapped triples (bilingual: orig + EN)
        reqs = con.execute("""
            SELECT r.clause_key, r.normalized_value, r.value_text_en, r.value_text_orig,
                   r.confidence, r.source_lang,
                   m.comet_target, m.target_kind, m.mapping_status
            FROM requirement r LEFT JOIN comet_mapping m ON r.clause_key=m.clause_key
            WHERE r.version_id=? AND r.span_verified=TRUE
        """, [vid]).fetchall()
        for (ck, norm, vtext_en, vtext_orig, conf, src_lang, target, kind, status) in reqs:
            val_en   = esc(norm or vtext_en or "")[:120]
            val_orig = esc(vtext_orig or "")[:120]
            src_lang = src_lang or "en"
            # English value always present; add original-language literal if different
            lang_tag = f"@{src_lang}" if src_lang != "en" else "@en"
            if val_orig and val_orig != val_en and src_lang != "en":
                lines.append(f'    pcrbase:hasRequirement [ '
                             f'pcrbase:clauseKey "{ck}" ; '
                             f'pcrbase:cometTarget "{esc(target)}" ; '
                             f'pcrbase:mappingStatus "{status}" ; '
                             f'pcrbase:confidence "{conf}"^^xsd:decimal ; '
                             f'pcrbase:value "{val_en}"@en ; '
                             f'pcrbase:valueOrig "{val_orig}"{lang_tag} ] ;')
            else:
                lines.append(f'    pcrbase:hasRequirement [ '
                             f'pcrbase:clauseKey "{ck}" ; '
                             f'pcrbase:cometTarget "{esc(target)}" ; '
                             f'pcrbase:mappingStatus "{status}" ; '
                             f'pcrbase:confidence "{conf}"^^xsd:decimal ; '
                             f'pcrbase:value "{val_en}"@en ] ;')
        # close
        lines[-1] = lines[-1].rstrip(" ;") + " ."
    con.close()
    out = os.path.join(EXPORT_DIR, "pcrbase.ttl")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    return out, len(rows)

def export_jsonld():
    con = get_con()
    os.makedirs(EXPORT_DIR, exist_ok=True)
    context = {
        "comet": "https://comet.carbon/v1/core#",
        "comet-pcf": "https://comet.carbon/v1/pcf#",
        "pcrbase": "https://pcrbase.org/v1/",
        "dcterms": "http://purl.org/dc/terms/",
    }
    graph = []
    rows = con.execute("""
        SELECT v.version_id, p.pcr_number, p.title, p.cpc_code, v.version_label, v.valid_until
        FROM pcr_version v JOIN pcr p ON v.pcr_id=p.pcr_id
    """).fetchall()
    for (vid, num, title, cpc, vlabel, valid) in rows:
        reqs = con.execute("""
            SELECT r.clause_key, r.normalized_value, r.value_text_en, r.confidence, m.comet_target, m.mapping_status
            FROM requirement r LEFT JOIN comet_mapping m ON r.clause_key=m.clause_key
            WHERE r.version_id=? AND r.span_verified=TRUE
        """, [vid]).fetchall()
        graph.append({
            "@id": f"pcrbase:{vid}",
            "@type": "comet-pcf:PCRDocument",
            "dcterms:title": title,
            "comet-pcf:pcrNumber": num,
            "comet-pcf:version": vlabel,
            "comet-pcf:scopeCPC": cpc,
            "comet-pcf:validUntil": valid,
            "pcrbase:hasRequirement": [
                {"pcrbase:clauseKey": ck, "pcrbase:cometTarget": tgt,
                 "pcrbase:mappingStatus": st, "pcrbase:confidence": conf,
                 "pcrbase:value": (norm or vtext or "")[:120]}
                for (ck, norm, vtext, conf, tgt, st) in reqs
            ],
        })
    con.close()
    doc = {"@context": context, "@graph": graph}
    out = os.path.join(EXPORT_DIR, "pcrbase.jsonld")
    with open(out, "w") as f:
        json.dump(doc, f, indent=2, default=str)
    return out, len(graph)

if __name__ == "__main__":
    ttl, n1 = export_turtle()
    jl, n2 = export_jsonld()
    print(f"Turtle  -> {ttl}  ({n1} PCRDocuments)")
    print(f"JSON-LD -> {jl}  ({n2} PCRDocuments)")
