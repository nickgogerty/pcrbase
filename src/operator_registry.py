"""Operator registry seed — the 'known universe' of PCR program operators.
URLs verified live where marked (HTTP 200 on 2026-06-17). Unverified ones are
best-known entry points to refine during P1 enumeration. access=gated means
metadata-only records (panel decision: keep in known universe, flag for later).
"""

VOCAB_VERSION = "v1-seed"

# operator_id, name, country, region, listing_url, adapter_type, access, language, program_standard
OPERATORS = [
    ("environdec",   "EPD International (EnvironDec)", "SE", "Global",   "https://www.environdec.com/pcr-library", "html", "open", "en", "ISO14025"),  # 200
    ("epd-norge",    "EPD Norge",                      "NO", "Europe",   "https://www.epd-norge.no/pcr/", "html", "open", "no", "EN15804"),  # 200
    ("inies",        "INIES (FDES/PEP)",               "FR", "Europe",   "https://www.inies.fr/", "html", "open", "fr", "EN15804"),  # 200
    ("ibu",          "IBU (Institut Bauen und Umwelt)","DE", "Europe",   "https://www.ibu-epd.com/en/published-epds/", "html", "open", "de", "EN15804"),  # 200
    ("eu-ef",        "EU Environmental Footprint (PEFCR)","EU","Europe", "https://green-business.ec.europa.eu/environmental-footprint-methods_en", "html", "open", "en", "PEF"),  # 200
    ("epd-italy",    "EPD Italy",                      "IT", "Europe",   "https://www.epditaly.it/en/pcr/", "html", "open", "it", "EN15804"),  # 200
    ("bre",          "BRE EN15804 (UK)",               "UK", "Europe",   "https://www.greenbooklive.com/", "html", "open", "en", "EN15804"),
    ("ul-spot",      "UL Environment / SPOT",          "US", "Americas", "https://spot.ul.com/", "html", "open", "en", "ISO14025"),
    ("astm",         "ASTM International EPD Program",  "US", "Americas", "https://www.astm.org/products-services/certification/epd-pcr.html", "manual", "open", "en", "ISO14025"),
    ("nsf",          "NSF International",               "US", "Americas", "https://www.nsf.org/", "manual", "open", "en", "ISO14025"),
    ("epd-australasia","EPD Australasia",               "AU", "Oceania",  "https://epd-australasia.com/", "html", "open", "en", "ISO14025"),
    ("icc-es",       "ICC-ES SAVE Program",            "US", "Americas", "https://icc-es.org/", "manual", "open", "en", "ISO14025"),
    ("mrpi",         "MRPI (Netherlands)",             "NL", "Europe",   "https://www.mrpi.nl/", "manual", "open", "nl", "EN15804"),
    ("dapcons",      "DAPcons (Spain)",                "ES", "Europe",   "https://www.csostenible.net/", "manual", "open", "es", "EN15804"),
    ("global-epd",   "Global EPD (AENOR)",             "ES", "Europe",   "https://www.aenor.com/", "manual", "open", "es", "EN15804"),
    ("keiti",        "KEITI (Korea EPD)",              "KR", "Asia",     "https://www.epd.or.kr/", "manual", "gated", "ko", "ISO14025"),
    ("jemai",        "JEMAI EcoLeaf (Japan)",          "JP", "Asia",     "https://ecoleaf-label.jp/", "manual", "gated", "ja", "ISO14025"),
    ("epd-chile",    "EPD Chile",                      "CL", "Americas", "https://www.epdchile.cl/", "manual", "open", "es", "ISO14025"),
    ("epd-latam",    "EPD Latin America",              "BR", "Americas", "https://epd-latinamerica.com/", "manual", "open", "pt", "ISO14025"),
    ("bau-epd",      "Bau EPD (Austria)",              "AT", "Europe",   "https://www.bau-epd.at/", "manual", "open", "de", "EN15804"),
    ("epd-ireland",  "EPD Ireland",                    "IE", "Europe",   "https://www.igbc.ie/epd-home/", "manual", "open", "en", "EN15804"),
    ("epd-turkey",   "EPD Turkey",                     "TR", "Europe",   "https://epdturkey.org/", "manual", "open", "tr", "EN15804"),
    ("itb",          "ITB (Poland)",                   "PL", "Europe",   "https://www.itb.pl/", "manual", "open", "pl", "EN15804"),
    ("the-norwegian-epd","Kebony/other regional",      "NO", "Europe",   "https://www.epd-norge.no/", "html", "open", "no", "EN15804"),
    ("us-epd",       "US EPD programs (NSF/ICC-ES/SCS/PCA)", "US", "Americas", "https://www.nsf.org/", "manual", "open", "en", "EN15804"),
    ("epdhub",       "EPD Hub",                        "GB", "Europe",   "https://www.epdhub.com/", "manual", "open", "en", "EN15804"),
]

def rows(run_id="seed"):
    return [(o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8], None, run_id) for o in OPERATORS]

if __name__ == "__main__":
    from collections import Counter
    print(f"Operator registry seed: {len(OPERATORS)} operators")
    print("By region:", dict(Counter(o[3] for o in OPERATORS)))
    print("By access:", dict(Counter(o[6] for o in OPERATORS)))
    print("By standard:", dict(Counter(o[8] for o in OPERATORS)))
