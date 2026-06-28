#!/usr/bin/env python3
"""
EPD Compliance Checker backend.
Accepts: ILCD XML, EPD JSON, or structured form data.
Uses Claude AI for unrecognized formats.
Checks declared fields against PCRbase requirement rows.

Called via: python src/epd_checker.py --input <file_or_json_string> [--pcr-id <id>]
Or imported as a library.
"""
import sys, os, json, re, argparse
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

# ── Field extractors ────────────────────────────────────────────────────────

def extract_ilcd_xml(content: str) -> dict:
    """Parse ILCD/EPD XML into a flat field dict."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return {'_parse_error': str(e)}

    ns_map = {
        'epd': 'http://www.iai.kit.edu/EPD/2013',
        'ilcd': 'http://lca.jrc.ec.europa.eu/ILCD/Process',
        'epd2': 'http://www.iai.kit.edu/EPD/2017',
    }

    def find_text(paths):
        for path in paths:
            for prefix, ns in ns_map.items():
                try:
                    el = root.find(path.replace(f'{prefix}:', f'{{{ns}}}'))
                    if el is not None and el.text:
                        return el.text.strip()
                except: pass
        return None

    fields = {}

    # PCR reference
    pcr_ref = find_text(['ilcd:modellingAndValidation/ilcd:complianceSystems/ilcd:compliance/ilcd:referenceToComplianceSystem'])
    if pcr_ref: fields['pcr_reference'] = pcr_ref

    # Declared unit / functional unit
    du = find_text(['ilcd:exchanges/ilcd:exchange/ilcd:referenceToFlowDataSet',
                    'epd:referenceToFunctionalUnit', 'epd2:referenceToFunctionalUnit'])
    if du: fields['declared_unit'] = du

    # System boundary / modules
    # Look for module declarations
    modules = []
    for tag in ['A1', 'A2', 'A3', 'A1-A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
                'C1', 'C2', 'C3', 'C4', 'D']:
        # search anywhere in XML text for module declarations
        if re.search(rf'\b{tag}\b', content):
            modules.append(tag)
    if modules:
        fields['declared_modules'] = modules

    # Allocation method
    alloc_match = re.search(r'(allocation|alloc)[^<]{0,80}(physical|economic|mass|system expansion|avoided|cut.?off)',
                             content, re.IGNORECASE)
    if alloc_match:
        fields['allocation_method'] = alloc_match.group(0)[:120].strip()

    # Program operator / PCR operator
    op_match = re.search(r'(EnvironDec|IBU|EPD Norge|EU PEFCR|BRE|US EPD|EPD Hub)', content, re.IGNORECASE)
    if op_match:
        fields['operator'] = op_match.group(1)

    fields['_format'] = 'ilcd_xml'
    return fields


def extract_epd_json(content: str) -> dict:
    """Parse structured EPD JSON."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return {'_parse_error': str(e)}

    fields = {'_format': 'json'}

    # Try common EPD JSON schemas
    for key in ['declaredUnit', 'declared_unit', 'referenceUnit', 'functionalUnit']:
        if key in data:
            fields['declared_unit'] = str(data[key])

    for key in ['pcr', 'pcrId', 'pcr_id', 'productCategoryRule', 'product_category_rule']:
        if key in data:
            fields['pcr_reference'] = str(data[key])

    for key in ['declaredModules', 'declared_modules', 'modules', 'systemBoundary']:
        if key in data:
            fields['declared_modules'] = data[key]

    for key in ['allocationMethod', 'allocation_method', 'allocation']:
        if key in data:
            fields['allocation_method'] = str(data[key])

    for key in ['operator', 'programOperator', 'program_operator']:
        if key in data:
            fields['operator'] = str(data[key])

    return fields


def extract_with_claude(content: str, content_type: str = 'unknown') -> dict:
    """Fall back to Claude Haiku for unrecognized formats (PDF text, freeform)."""
    try:
        from llm_client import call as llm_call
    except Exception as e:
        return {'_llm_error': str(e), '_format': 'unknown'}

    prompt = f"""Extract EPD compliance fields from the following {content_type} content.
Return a JSON object with these fields (omit any you cannot find):
- pcr_reference: the PCR document title/number/URL this EPD follows
- operator: the EPD program operator (e.g. EnvironDec, IBU, EPD Norge)
- declared_unit: the functional or declared unit (e.g. "1 kg", "1 m²")
- declared_modules: list of life-cycle modules declared (e.g. ["A1-A3", "C1-C4", "D"])
- allocation_method: how co-products are handled (e.g. "physical allocation", "system expansion")
- cutoff_threshold: mass/energy cutoff rule if stated
- valid_from: document valid from date
- valid_until: document expiry date
- lcia_methods: list of impact assessment methods used
- reference_service_life: if stated, the RSL value

Content:
{content[:4000]}

Return ONLY valid JSON, no markdown, no explanation."""

    try:
        response = llm_call([{"role": "user", "content": prompt}], max_tokens=800)
        raw = response.get('content', [{}])[0].get('text', '{}') if isinstance(response, dict) else str(response)
        return json.loads(raw)
    except Exception as e:
        return {'_llm_error': str(e), '_format': 'llm_fallback'}


# ── Compliance check ─────────────────────────────────────────────────────────

def check_compliance(epd_fields: dict, pcr_id: str = None) -> dict:
    """Compare extracted EPD fields against PCRbase requirement rows."""
    c = get_con()

    # Find matching PCR if not specified
    if not pcr_id and epd_fields.get('operator'):
        op = epd_fields['operator'].lower().replace(' ', '-').replace('environdec', 'environdec')
        op_map = {
            'environdec': 'environdec', 'ivl': 'environdec',
            'ibu': 'ibu', 'epd norge': 'epd-norge', 'epd-norge': 'epd-norge',
            'bre': 'bre', 'bpf': 'bre',
            'eu pefcr': 'eu-ef', 'pefcr': 'eu-ef',
            'us epd': 'us-epd', 'epd hub': 'epdhub',
        }
        for k, v in op_map.items():
            if k in op:
                op = v; break
        # Get latest versions from that operator
        versions = c.execute("""
            SELECT v.version_id, p.title FROM pcr_version v
            JOIN pcr p ON v.pcr_id = p.pcr_id
            WHERE p.operator_id = ? ORDER BY v.valid_until DESC LIMIT 5
        """, [op]).fetchall()
    elif pcr_id:
        versions = c.execute("""
            SELECT v.version_id, p.title FROM pcr_version v
            JOIN pcr p ON v.pcr_id = p.pcr_id
            WHERE p.pcr_id = ? ORDER BY v.valid_until DESC LIMIT 1
        """, [pcr_id]).fetchall()
    else:
        versions = []

    checks = []
    matched_pcr = None

    if versions:
        version_id, pcr_title = versions[0]
        matched_pcr = pcr_title

        # Pull requirements for this version
        reqs = c.execute("""
            SELECT clause_key, clause_group, value_text_en, normalized_value, confidence
            FROM requirement WHERE version_id = ?
        """, [version_id]).fetchall()

        # Map clause_key → requirement
        req_map = {r[0]: r for r in reqs}

        # Check declared unit
        if 'declared_unit' in epd_fields and 'declared_unit' in req_map:
            r = req_map['declared_unit']
            match = epd_fields['declared_unit'].lower() in (r[2] or '').lower()
            checks.append({
                'field': 'declared_unit',
                'status': 'pass' if match else 'review',
                'epd_value': epd_fields['declared_unit'],
                'pcr_requirement': r[2],
                'note': 'Values match' if match else 'Declared unit differs from PCR — review required'
            })

        # Check declared modules
        if 'declared_modules' in epd_fields and 'modules_declared' in req_map:
            r = req_map['modules_declared']
            epd_mods = epd_fields['declared_modules']
            pcr_mods = r[2] or ''
            checks.append({
                'field': 'declared_modules',
                'status': 'info',
                'epd_value': epd_mods,
                'pcr_requirement': pcr_mods,
                'note': 'Manual verification recommended for module scope'
            })

        # Check allocation
        if 'allocation_method' in epd_fields and 'allocation_rule' in req_map:
            r = req_map['allocation_rule']
            checks.append({
                'field': 'allocation_method',
                'status': 'info',
                'epd_value': epd_fields['allocation_method'],
                'pcr_requirement': r[2],
                'note': 'Review allocation method against PCR rule'
            })

        # Flag missing required fields
        required_keys = ['declared_unit', 'system_boundary', 'modules_declared', 'allocation_rule', 'cutoff_rule']
        for key in required_keys:
            if key in req_map and key.replace('_rule', '_method').replace('_boundary', '') not in epd_fields:
                checks.append({
                    'field': key,
                    'status': 'missing',
                    'epd_value': None,
                    'pcr_requirement': req_map[key][2],
                    'note': f'Field not found in EPD — required by PCR'
                })

    c.close()

    status_counts = {'pass': 0, 'review': 0, 'missing': 0, 'info': 0}
    for chk in checks:
        status_counts[chk['status']] = status_counts.get(chk['status'], 0) + 1

    overall = 'pass' if status_counts['missing'] == 0 and status_counts['review'] == 0 else \
              'needs_review' if status_counts['missing'] == 0 else 'incomplete'

    return {
        'overall_status': overall,
        'matched_pcr': matched_pcr,
        'epd_fields_extracted': epd_fields,
        'checks': checks,
        'summary': status_counts
    }


def run_checker(input_text: str, pcr_id: str = None, filename: str = '') -> dict:
    """Main entry point: detect format, extract, check."""
    stripped = input_text.strip()

    # Detect format
    if stripped.startswith('<') and ('processDataSet' in stripped or 'EPD' in stripped or 'xml' in stripped.lower()):
        fields = extract_ilcd_xml(stripped)
    elif stripped.startswith('{') or stripped.startswith('['):
        fields = extract_epd_json(stripped)
    elif filename.lower().endswith('.pdf') or len(stripped) > 500:
        fields = extract_with_claude(stripped, content_type='PDF text' if filename.endswith('.pdf') else 'document')
    else:
        # Short form input — treat as structured key:value or use Claude
        fields = extract_with_claude(stripped, content_type='form input')

    if '_parse_error' in fields or '_llm_error' in fields:
        return {'error': fields.get('_parse_error') or fields.get('_llm_error'),
                'extracted_fields': fields}

    return check_compliance(fields, pcr_id=pcr_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EPD Compliance Checker')
    parser.add_argument('--input', '-i', help='Input file path or JSON string')
    parser.add_argument('--pcr-id', help='PCR ID to check against (optional — auto-detected if omitted)')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    args = parser.parse_args()

    if args.stdin:
        content = sys.stdin.read()
    elif args.input:
        if os.path.exists(args.input):
            with open(args.input) as f:
                content = f.read()
        else:
            content = args.input
    else:
        print("Usage: python src/epd_checker.py --input <file_or_string> [--pcr-id <id>]")
        sys.exit(1)

    result = run_checker(content, pcr_id=args.pcr_id,
                         filename=args.input if args.input and os.path.exists(args.input or '') else '')
    print(json.dumps(result, indent=2, default=str))
