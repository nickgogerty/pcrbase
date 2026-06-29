"""
Schema migration: add multilingual support columns to requirement and comet_mapping.

Run ONCE after extraction completes (when DB is not locked):
  python src/migrate_multilingual.py

Changes:
  requirement:   ADD COLUMN source_lang VARCHAR  (ISO 639-1 code: 'ja', 'no', 'de', 'en')
  comet_mapping: ADD COLUMN languages    VARCHAR  (comma-separated ISO 639-1 codes of PCR langs
                                                    that evidence this mapping, e.g. 'en,ja,no')
  NEW TABLE: comet_mapping_i18n
    Stores per-language clause labels for cross-lingual mapping browsing.
"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con

def run():
    c = get_con()
    run_id = "migrate-multilingual-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # ── 1. requirement.source_lang ──────────────────────────────────────────
    existing_req = [r[0] for r in c.execute("DESCRIBE requirement").fetchall()]
    if "source_lang" not in existing_req:
        c.execute("ALTER TABLE requirement ADD COLUMN source_lang VARCHAR DEFAULT 'en'")
        # Backfill: sumpo versions → 'ja', epd-norge versions → 'no', others → 'en'
        c.execute("""
            UPDATE requirement SET source_lang = 'ja'
            WHERE version_id LIKE 'sumpo-%'
        """)
        c.execute("""
            UPDATE requirement SET source_lang = 'no'
            WHERE version_id LIKE 'epd-norge-%'
            AND value_text_orig != value_text_en
        """)
        print("✓ requirement.source_lang added + backfilled")
    else:
        print("  requirement.source_lang already exists — skipping")

    # ── 2. comet_mapping.languages ──────────────────────────────────────────
    existing_cm = [r[0] for r in c.execute("DESCRIBE comet_mapping").fetchall()]
    if "languages" not in existing_cm:
        c.execute("ALTER TABLE comet_mapping ADD COLUMN languages VARCHAR DEFAULT 'en'")
        print("✓ comet_mapping.languages added")
    else:
        print("  comet_mapping.languages already exists — skipping")

    # ── 3. NEW TABLE: comet_mapping_i18n ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS comet_mapping_i18n (
            i18n_id      VARCHAR PRIMARY KEY,
            clause_key   VARCHAR,           -- FK → comet_mapping.clause_key
            lang         VARCHAR NOT NULL,  -- ISO 639-1: 'ja', 'no', 'de', 'en', ...
            label        VARCHAR,           -- human-readable clause label in this language
            description  VARCHAR,           -- clause description / usage note in this language
            example_orig VARCHAR,           -- verbatim example from a source PCR in this language
            example_en   VARCHAR,           -- English translation of example_orig
            source_pcr   VARCHAR,           -- pcr_id this example came from
            _loaded_at   TIMESTAMP DEFAULT now(),
            _run_id      VARCHAR
        )
    """)
    print("✓ comet_mapping_i18n table created (or already exists)")

    # ── 4. Seed JA labels for all 65 clause_keys ────────────────────────────
    # These are expert translations of the PCRbase clause vocabulary into Japanese
    JA_LABELS = {
        # G1 Identification
        "id.operator":         ("プログラムオペレーター",       "PCRを発行する団体・機関"),
        "id.program":          ("プログラム名",                  "EPD登録プログラムの名称"),
        "id.pcr_number":       ("PCR登録番号",                   "PCRの固有登録番号"),
        "id.version":          ("バージョン",                    "PCR文書のバージョン番号"),
        "id.pub_date":         ("発行日",                        "PCRの発行・公開日"),
        "id.expiry_date":      ("有効期限",                      "PCRの有効期限日"),
        "id.cpc_code":         ("CPCコード",                     "国連中央生産物分類コード"),
        "id.geography":        ("対象地域",                      "PCRが適用される地理的範囲"),
        "id.language":         ("文書言語",                      "PCR文書の言語"),
        # G2 Scope
        "scope.product_category":  ("製品カテゴリー定義",       "対象製品カテゴリーの定義・範囲"),
        "scope.intended_use":      ("意図した使用",              "PCRの意図する使用目的"),
        "scope.inclusions":        ("含まれるもの",              "システム境界に含まれる要素"),
        "scope.exclusions":        ("除外されるもの",            "システム境界から除外される要素"),
        "scope.comparability":     ("比較可能性",                "EPD間の比較可能性に関する規定"),
        "scope.target_audience":   ("対象者",                    "PCRが対象とする利用者"),
        # G3 Functional/Declared unit
        "unit.declared_unit":      ("宣言単位",                  "EPDの基準となる宣言単位"),
        "unit.reference_flow":     ("参照フロー",                "宣言単位に対応する参照フロー"),
        "unit.quantification":     ("定量化規則",                "宣言単位の定量化方法"),
        "unit.mass_reference":     ("質量基準",                  "質量に基づく参照単位の規定"),
        "unit.conversion":         ("換算係数",                  "単位換算に関する規定"),
        # G4 System boundary
        "boundary.modules_declared": ("宣言モジュール",          "宣言するライフサイクルモジュール"),
        "boundary.cut_off_desc":     ("カットオフルール説明",     "カットオフルールの詳細説明"),
        "boundary.unit_processes":   ("単位プロセス",            "考慮すべき単位プロセス"),
        # G5 Modules
        "modules.A1A3":  ("A1-A3 製造段階",    "原材料調達・輸送・製造モジュール"),
        "modules.A4A5":  ("A4-A5 建設段階",    "輸送・設置モジュール（建設製品）"),
        "modules.B1B7":  ("B1-B7 使用段階",    "使用段階全モジュール"),
        "modules.C1C4":  ("C1-C4 廃棄段階",    "解体・廃棄・処理・埋立モジュール"),
        "modules.D":     ("D モジュール",       "再利用・回収・リサイクルポテンシャル"),
        # G6 Cut-off
        "cutoff.mass_threshold":    ("質量カットオフ閾値",      "質量によるカットオフ閾値（%）"),
        "cutoff.energy_threshold":  ("エネルギーカットオフ閾値","エネルギーによるカットオフ閾値"),
        "cutoff.env_threshold":     ("環境影響カットオフ閾値",  "環境影響によるカットオフ閾値"),
        "cutoff.completeness":      ("完全性要件",               "インベントリの完全性に関する要件"),
        "cutoff.energy":            ("エネルギーカットオフ",     "エネルギーフローのカットオフ規定"),
        "cutoff.environmental":     ("環境カットオフ",           "環境フローのカットオフ規定"),
        # G7 Allocation
        "alloc.co_product":     ("副産物配分方法",  "副産物の配分方法（物理的・経済的等）"),
        "alloc.allocation_rule":("配分ルール",      "配分の適用ルールと優先順位"),
        "alloc.recycling":      ("リサイクル配分",  "リサイクル・回収に関する配分規定"),
        "alloc.multifunction":  ("多機能配分",      "多機能プロセスの配分方法"),
        # G8 Data quality
        "dq.temporal":       ("時間的代表性",   "データの時間的代表性要件"),
        "dq.geographical":   ("地理的代表性",   "データの地理的代表性要件"),
        "dq.technological":  ("技術的代表性",   "データの技術的代表性要件"),
        "dq.primary_data":   ("一次データ要件", "一次データ収集の要件"),
        "dq.background_db":  ("背景データベース","バックグラウンドデータベースの要件"),
        # G9 LCIA
        "lcia.method":         ("LCIA方法論",      "ライフサイクル影響評価の方法論"),
        "lcia.gwp_method":     ("GWP評価方法",     "地球温暖化ポテンシャルの評価方法"),
        "lcia.indicators":     ("影響指標",        "使用するLCA影響指標のセット"),
        "lcia.inventory_flows":("インベントリフロー","追跡すべき物質フロー"),
        "lcia.en15804_set":    ("EN15804指標セット","EN15804規定の環境影響指標セット"),
        # G10 Scenarios
        "scenario.rsl":        ("基準耐用年数",  "製品の基準耐用年数（RSL）"),
        "scenario.use":        ("使用シナリオ",  "使用段階のシナリオ定義"),
        "scenario.eol":        ("廃棄シナリオ",  "廃棄段階のシナリオ定義"),
        "scenario.transport":  ("輸送シナリオ",  "輸送に関するシナリオ定義"),
        # G11 Content
        "content.hazardous":        ("有害物質",         "有害物質の申告要件"),
        "content.biogenic_content": ("生物由来炭素含有量","生物由来炭素の含有量申告"),
        "content.declaration":      ("コンテンツ申告",   "製品コンテンツの申告要件"),
        "content.additional":       ("追加情報",         "EPDに含める追加情報の要件"),
        # G12 Reporting
        "report.validity_period":  ("有効期間",      "EPD・PCRの有効期間"),
        "report.review_panel":     ("レビューパネル","独立した検証・レビューパネルの要件"),
        "report.layout":           ("EPDレイアウト", "EPD文書のレイアウト・形式要件"),
        "report.digital_format":   ("デジタル形式",  "EPDのデジタルデータ形式（ILCD等）"),
        # Catch-all
        "unclassified":            ("未分類",        "分類されていないPCR要件"),
    }

    inserted = 0
    for clause_key, (label, description) in JA_LABELS.items():
        i18n_id = f"i18n-{clause_key.replace('.', '-')}-ja"
        existing = c.execute("SELECT 1 FROM comet_mapping_i18n WHERE i18n_id=?", [i18n_id]).fetchone()
        if not existing:
            c.execute("""
                INSERT INTO comet_mapping_i18n
                    (i18n_id, clause_key, lang, label, description, _run_id)
                VALUES (?, ?, 'ja', ?, ?, ?)
            """, [i18n_id, clause_key, label, description, run_id])
            inserted += 1
    print(f"✓ comet_mapping_i18n: {inserted} Japanese labels seeded")

    # ── 5. Seed EN labels too (canonical reference) ──────────────────────────
    EN_LABELS = {
        "id.operator": ("Program Operator", "Organisation that issues the PCR"),
        "id.program": ("Program Name", "Name of the EPD registration program"),
        "id.pcr_number": ("PCR Registration Number", "Unique PCR identifier"),
        "id.version": ("Version", "PCR document version number"),
        "id.pub_date": ("Publication Date", "Date the PCR was published"),
        "id.expiry_date": ("Expiry Date", "PCR validity expiry date"),
        "id.cpc_code": ("CPC Code", "UN Central Product Classification code"),
        "id.geography": ("Geography", "Geographic scope of the PCR"),
        "id.language": ("Document Language", "Language of the PCR document"),
        "scope.product_category": ("Product Category Definition", "Definition and scope of the product category"),
        "scope.intended_use": ("Intended Use", "Intended purpose and use of the PCR"),
        "scope.inclusions": ("Inclusions", "Elements included within the system boundary"),
        "scope.exclusions": ("Exclusions", "Elements excluded from the system boundary"),
        "scope.comparability": ("Comparability", "Provisions for EPD comparability"),
        "scope.target_audience": ("Target Audience", "Intended users of the PCR"),
        "unit.declared_unit": ("Declared Unit", "Reference unit for the EPD"),
        "unit.reference_flow": ("Reference Flow", "Reference flow corresponding to declared unit"),
        "unit.quantification": ("Quantification Rule", "Method for quantifying the declared unit"),
        "unit.mass_reference": ("Mass Reference", "Mass-based reference unit specification"),
        "unit.conversion": ("Conversion Factor", "Unit conversion specifications"),
        "boundary.modules_declared": ("Declared Modules", "Life-cycle modules included in the declaration"),
        "boundary.cut_off_desc": ("Cut-off Rule Description", "Detailed description of cut-off rules"),
        "boundary.unit_processes": ("Unit Processes", "Unit processes to be considered"),
        "modules.A1A3": ("A1-A3 Manufacturing", "Raw material supply, transport, and manufacturing modules"),
        "modules.A4A5": ("A4-A5 Construction", "Transport and installation modules (construction products)"),
        "modules.B1B7": ("B1-B7 Use Stage", "All use-stage modules"),
        "modules.C1C4": ("C1-C4 End of Life", "Deconstruction, waste processing, disposal modules"),
        "modules.D": ("Module D", "Reuse, recovery, and recycling potential"),
        "cutoff.mass_threshold": ("Mass Cut-off Threshold", "Cut-off threshold based on mass (%)"),
        "cutoff.energy_threshold": ("Energy Cut-off Threshold", "Cut-off threshold based on energy"),
        "cutoff.env_threshold": ("Environmental Cut-off Threshold", "Cut-off threshold based on environmental impact"),
        "cutoff.completeness": ("Completeness Requirement", "Requirements for inventory completeness"),
        "cutoff.energy": ("Energy Cut-off", "Energy flow cut-off specification"),
        "cutoff.environmental": ("Environmental Cut-off", "Environmental flow cut-off specification"),
        "alloc.co_product": ("Co-product Allocation", "Allocation method for co-products"),
        "alloc.allocation_rule": ("Allocation Rule", "Allocation rules and hierarchy"),
        "alloc.recycling": ("Recycling Allocation", "Allocation provisions for recycling/recovery"),
        "alloc.multifunction": ("Multifunctional Allocation", "Allocation for multifunctional processes"),
        "dq.temporal": ("Temporal Representativeness", "Temporal representativeness requirements for data"),
        "dq.geographical": ("Geographical Representativeness", "Geographical representativeness requirements"),
        "dq.technological": ("Technological Representativeness", "Technological representativeness requirements"),
        "dq.primary_data": ("Primary Data Requirements", "Requirements for primary data collection"),
        "dq.background_db": ("Background Database", "Background database requirements"),
        "lcia.method": ("LCIA Methodology", "Life cycle impact assessment methodology"),
        "lcia.gwp_method": ("GWP Method", "Global warming potential assessment method"),
        "lcia.indicators": ("Impact Indicators", "Set of LCA impact indicators to use"),
        "lcia.inventory_flows": ("Inventory Flows", "Material flows to be tracked"),
        "lcia.en15804_set": ("EN15804 Indicator Set", "Environmental indicators required by EN15804"),
        "scenario.rsl": ("Reference Service Life", "Reference service life of the product"),
        "scenario.use": ("Use Scenario", "Definition of use-stage scenario"),
        "scenario.eol": ("End-of-Life Scenario", "Definition of end-of-life scenario"),
        "scenario.transport": ("Transport Scenario", "Transport scenario specification"),
        "content.hazardous": ("Hazardous Substances", "Hazardous substance declaration requirements"),
        "content.biogenic_content": ("Biogenic Carbon Content", "Biogenic carbon content declaration"),
        "content.declaration": ("Content Declaration", "Product content declaration requirements"),
        "content.additional": ("Additional Information", "Requirements for additional EPD information"),
        "report.validity_period": ("Validity Period", "EPD/PCR validity period"),
        "report.review_panel": ("Review Panel", "Independent verification/review panel requirements"),
        "report.layout": ("EPD Layout", "EPD document layout and format requirements"),
        "report.digital_format": ("Digital Format", "Digital data format requirements (ILCD, etc.)"),
        "unclassified": ("Unclassified", "PCR requirement not yet classified into a clause group"),
    }
    en_inserted = 0
    for clause_key, (label, description) in EN_LABELS.items():
        i18n_id = f"i18n-{clause_key.replace('.', '-')}-en"
        existing = c.execute("SELECT 1 FROM comet_mapping_i18n WHERE i18n_id=?", [i18n_id]).fetchone()
        if not existing:
            c.execute("""
                INSERT INTO comet_mapping_i18n
                    (i18n_id, clause_key, lang, label, description, _run_id)
                VALUES (?, ?, 'en', ?, ?, ?)
            """, [i18n_id, clause_key, label, description, run_id])
            en_inserted += 1
    print(f"✓ comet_mapping_i18n: {en_inserted} English labels seeded")

    # ── 6. Update comet_mapping.languages to reflect JA evidence ────────────
    # After extraction completes, mark which clause_keys have JA-language evidence
    ja_keys = c.execute("""
        SELECT DISTINCT clause_key FROM requirement
        WHERE version_id LIKE 'sumpo-%' AND clause_key IS NOT NULL
    """).fetchall()
    if ja_keys:
        for (ck,) in ja_keys:
            c.execute("""
                UPDATE comet_mapping SET languages = 
                    CASE WHEN languages IS NULL OR languages = '' THEN 'en,ja'
                         WHEN languages NOT LIKE '%ja%' THEN languages || ',ja'
                         ELSE languages END
                WHERE clause_key = ?
            """, [ck])
        print(f"✓ comet_mapping.languages: flagged {len(ja_keys)} keys with JA evidence")
    else:
        print("  No sumpo requirements yet — run after extraction completes")

    c.commit()
    c.close()
    print(f"\n✓ Migration complete (run_id: {run_id})")


if __name__ == "__main__":
    run()
