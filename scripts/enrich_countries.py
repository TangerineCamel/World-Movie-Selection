"""
enrich_countries.py
给金熊/金狮 metadata JS 补 mainCountry / productionCountries / originCountryRaw。
调 TMDB /movie/{tmdbId} 详情接口，不再用 /find。

用法：
  python3 scripts/enrich_countries.py bear   # 处理 golden_bear.js
  python3 scripts/enrich_countries.py lion   # 处理 lion_metadata.js
"""

import sys, json, re, ssl, time, urllib.request, os

# ─── 配置 ───────────────────────────────────────────────
API_KEY   = '5d71ba15ace52c171577c1fa5df4c573'
GAP       = 0.3
MAX_RETRY = 3
ctx       = ssl._create_unverified_context()

TARGETS = {
    'bear': {
        'input':    'data/golden_bear.js',
        'var_name': 'GOLDEN_BEAR_DATA',
        'output':   'data/golden_bear.js',
    },
    'lion': {
        'input':    'data/lion_metadata.js',
        'var_name': 'GOLDEN_LION_DATA',
        'output':   'data/lion_metadata.js',
    },
    'cannes': {
        'input':    'data/cannes_metadata.js',
        'var_name': 'CANNES_DATA',
        'output':   'data/cannes_metadata.js',
    },
}

# ─── ISO 3166-1 映射表（alpha-2 → {iso3, nameZh, nameEn}）───────────────────
# 来源：i18n-iso-countries 中文 locale，覆盖所有 TMDB 常见制片国
ISO_MAP = {
  "AF":{"iso3":"AFG","nameZh":"阿富汗","nameEn":"Afghanistan"},
  "AL":{"iso3":"ALB","nameZh":"阿尔巴尼亚","nameEn":"Albania"},
  "DZ":{"iso3":"DZA","nameZh":"阿尔及利亚","nameEn":"Algeria"},
  "AR":{"iso3":"ARG","nameZh":"阿根廷","nameEn":"Argentina"},
  "AM":{"iso3":"ARM","nameZh":"亚美尼亚","nameEn":"Armenia"},
  "AU":{"iso3":"AUS","nameZh":"澳大利亚","nameEn":"Australia"},
  "AT":{"iso3":"AUT","nameZh":"奥地利","nameEn":"Austria"},
  "AZ":{"iso3":"AZE","nameZh":"阿塞拜疆","nameEn":"Azerbaijan"},
  "BE":{"iso3":"BEL","nameZh":"比利时","nameEn":"Belgium"},
  "BO":{"iso3":"BOL","nameZh":"玻利维亚","nameEn":"Bolivia"},
  "BA":{"iso3":"BIH","nameZh":"波斯尼亚和黑塞哥维那","nameEn":"Bosnia and Herzegovina"},
  "BR":{"iso3":"BRA","nameZh":"巴西","nameEn":"Brazil"},
  "BG":{"iso3":"BGR","nameZh":"保加利亚","nameEn":"Bulgaria"},
  "KH":{"iso3":"KHM","nameZh":"柬埔寨","nameEn":"Cambodia"},
  "CA":{"iso3":"CAN","nameZh":"加拿大","nameEn":"Canada"},
  "CL":{"iso3":"CHL","nameZh":"智利","nameEn":"Chile"},
  "CN":{"iso3":"CHN","nameZh":"中国","nameEn":"China"},
  "CO":{"iso3":"COL","nameZh":"哥伦比亚","nameEn":"Colombia"},
  "HR":{"iso3":"HRV","nameZh":"克罗地亚","nameEn":"Croatia"},
  "CU":{"iso3":"CUB","nameZh":"古巴","nameEn":"Cuba"},
  "CZ":{"iso3":"CZE","nameZh":"捷克","nameEn":"Czech Republic"},
  "DK":{"iso3":"DNK","nameZh":"丹麦","nameEn":"Denmark"},
  "EG":{"iso3":"EGY","nameZh":"埃及","nameEn":"Egypt"},
  "EE":{"iso3":"EST","nameZh":"爱沙尼亚","nameEn":"Estonia"},
  "FI":{"iso3":"FIN","nameZh":"芬兰","nameEn":"Finland"},
  "FR":{"iso3":"FRA","nameZh":"法国","nameEn":"France"},
  "GE":{"iso3":"GEO","nameZh":"格鲁吉亚","nameEn":"Georgia"},
  "DE":{"iso3":"DEU","nameZh":"德国","nameEn":"Germany"},
  "GR":{"iso3":"GRC","nameZh":"希腊","nameEn":"Greece"},
  "HK":{"iso3":"HKG","nameZh":"中国香港","nameEn":"Hong Kong"},
  "HU":{"iso3":"HUN","nameZh":"匈牙利","nameEn":"Hungary"},
  "IN":{"iso3":"IND","nameZh":"印度","nameEn":"India"},
  "ID":{"iso3":"IDN","nameZh":"印度尼西亚","nameEn":"Indonesia"},
  "IR":{"iso3":"IRN","nameZh":"伊朗","nameEn":"Iran"},
  "IQ":{"iso3":"IRQ","nameZh":"伊拉克","nameEn":"Iraq"},
  "IE":{"iso3":"IRL","nameZh":"爱尔兰","nameEn":"Ireland"},
  "IL":{"iso3":"ISR","nameZh":"以色列","nameEn":"Israel"},
  "IT":{"iso3":"ITA","nameZh":"意大利","nameEn":"Italy"},
  "JP":{"iso3":"JPN","nameZh":"日本","nameEn":"Japan"},
  "KZ":{"iso3":"KAZ","nameZh":"哈萨克斯坦","nameEn":"Kazakhstan"},
  "KR":{"iso3":"KOR","nameZh":"韩国","nameEn":"South Korea"},
  "KG":{"iso3":"KGZ","nameZh":"吉尔吉斯斯坦","nameEn":"Kyrgyzstan"},
  "LV":{"iso3":"LVA","nameZh":"拉脱维亚","nameEn":"Latvia"},
  "LB":{"iso3":"LBN","nameZh":"黎巴嫩","nameEn":"Lebanon"},
  "LT":{"iso3":"LTU","nameZh":"立陶宛","nameEn":"Lithuania"},
  "LU":{"iso3":"LUX","nameZh":"卢森堡","nameEn":"Luxembourg"},
  "MK":{"iso3":"MKD","nameZh":"北马其顿","nameEn":"North Macedonia"},
  "MY":{"iso3":"MYS","nameZh":"马来西亚","nameEn":"Malaysia"},
  "MX":{"iso3":"MEX","nameZh":"墨西哥","nameEn":"Mexico"},
  "MD":{"iso3":"MDA","nameZh":"摩尔多瓦","nameEn":"Moldova"},
  "MN":{"iso3":"MNG","nameZh":"蒙古","nameEn":"Mongolia"},
  "MA":{"iso3":"MAR","nameZh":"摩洛哥","nameEn":"Morocco"},
  "NL":{"iso3":"NLD","nameZh":"荷兰","nameEn":"Netherlands"},
  "NZ":{"iso3":"NZL","nameZh":"新西兰","nameEn":"New Zealand"},
  "NG":{"iso3":"NGA","nameZh":"尼日利亚","nameEn":"Nigeria"},
  "NO":{"iso3":"NOR","nameZh":"挪威","nameEn":"Norway"},
  "PK":{"iso3":"PAK","nameZh":"巴基斯坦","nameEn":"Pakistan"},
  "PS":{"iso3":"PSE","nameZh":"巴勒斯坦","nameEn":"Palestine"},
  "PE":{"iso3":"PER","nameZh":"秘鲁","nameEn":"Peru"},
  "PH":{"iso3":"PHL","nameZh":"菲律宾","nameEn":"Philippines"},
  "PL":{"iso3":"POL","nameZh":"波兰","nameEn":"Poland"},
  "PT":{"iso3":"PRT","nameZh":"葡萄牙","nameEn":"Portugal"},
  "RO":{"iso3":"ROU","nameZh":"罗马尼亚","nameEn":"Romania"},
  "RU":{"iso3":"RUS","nameZh":"俄罗斯","nameEn":"Russia"},
  "SA":{"iso3":"SAU","nameZh":"沙特阿拉伯","nameEn":"Saudi Arabia"},
  "SN":{"iso3":"SEN","nameZh":"塞内加尔","nameEn":"Senegal"},
  "RS":{"iso3":"SRB","nameZh":"塞尔维亚","nameEn":"Serbia"},
  "SK":{"iso3":"SVK","nameZh":"斯洛伐克","nameEn":"Slovakia"},
  "SI":{"iso3":"SVN","nameZh":"斯洛文尼亚","nameEn":"Slovenia"},
  "ZA":{"iso3":"ZAF","nameZh":"南非","nameEn":"South Africa"},
  "ES":{"iso3":"ESP","nameZh":"西班牙","nameEn":"Spain"},
  "LK":{"iso3":"LKA","nameZh":"斯里兰卡","nameEn":"Sri Lanka"},
  "SE":{"iso3":"SWE","nameZh":"瑞典","nameEn":"Sweden"},
  "CH":{"iso3":"CHE","nameZh":"瑞士","nameEn":"Switzerland"},
  "SY":{"iso3":"SYR","nameZh":"叙利亚","nameEn":"Syria"},
  "TW":{"iso3":"TWN","nameZh":"台湾","nameEn":"Taiwan"},
  "TJ":{"iso3":"TJK","nameZh":"塔吉克斯坦","nameEn":"Tajikistan"},
  "TH":{"iso3":"THA","nameZh":"泰国","nameEn":"Thailand"},
  "TN":{"iso3":"TUN","nameZh":"突尼斯","nameEn":"Tunisia"},
  "TR":{"iso3":"TUR","nameZh":"土耳其","nameEn":"Turkey"},
  "TM":{"iso3":"TKM","nameZh":"土库曼斯坦","nameEn":"Turkmenistan"},
  "UA":{"iso3":"UKR","nameZh":"乌克兰","nameEn":"Ukraine"},
  "GB":{"iso3":"GBR","nameZh":"英国","nameEn":"United Kingdom"},
  "US":{"iso3":"USA","nameZh":"美国","nameEn":"United States"},
  "UZ":{"iso3":"UZB","nameZh":"乌兹别克斯坦","nameEn":"Uzbekistan"},
  "VE":{"iso3":"VEN","nameZh":"委内瑞拉","nameEn":"Venezuela"},
  "VN":{"iso3":"VNM","nameZh":"越南","nameEn":"Vietnam"},
  "XK":{"iso3":"XKX","nameZh":"科索沃","nameEn":"Kosovo"},

  # ── 历史消亡国家：硬编码默认继承国，可直接在现代地图上点亮 ──
  "XC":{"iso3":"CSK","nameZh":"捷克","nameEn":"Czech Republic"},   # 捷克斯洛伐克：TMDB的XC一律映射到捷克(CZ/CSK)
  "SU":{"iso3":"RUS","nameZh":"俄罗斯","nameEn":"Russia"},          # 苏联：映射到俄罗斯
  # YU（南斯拉夫）：不可硬编码默认继承国，必须逐部按语言/导演民族属核实（序正: RS 塞尔维亚、HR 克罗地亚、SI 斯洛文尼亚、MK 北马其顿...）
  # 护展到其他奖项时遇到YU必须人工核对，不可直接套用下面的默认展开
  "YU":{"iso3":"SRB","nameZh":"塞尔维亚","nameEn":"Serbia"},     # 假设性默认，实际需MANUAL_OVERRIDE覆盖
}

# ── 逐条手动覆盖（key格式："var_name|titleCN"）──────────────────────────────
# 南斯拉夫片需逐部按语言/导演民族属确认继承国，不可套用默认YU映射。
MANUAL_OVERRIDE = {
    # 格式: "VAR_NAME|中文片名" -> {"iso2":..., "iso3":..., "name":..., "nameEn":...}
    "GOLDEN_BEAR_DATA|第一个工作": {"iso2":"RS","iso3":"SRB","name":"塞尔维亚","nameEn":"Serbia"},  # 屎建达导演，塞文对白
    "CANNES_DATA|地下":           {"iso2":"RS","iso3":"SRB","name":"塞尔维亚","nameEn":"Serbia"},  # 库斯图里察，塞语，虽联合制片含FR/DE/HU/CZ
    "CANNES_DATA|爸爸去出差":     {"iso2":"RS","iso3":"SRB","name":"塞尔维亚","nameEn":"Serbia"},  # 库斯图里察，塞语，萨拉热窝背景
}

def iso2_to_entry(iso2, tmdb_name_zh=''):
    entry = ISO_MAP.get(iso2)
    if entry:
        return {'iso2': iso2, 'iso3': entry['iso3'],
                'name': entry['nameZh'], 'nameEn': entry['nameEn']}
    # 未知：用 TMDB 中文名兜底
    return {'iso2': iso2, 'iso3': None,
            'name': tmdb_name_zh or iso2, 'nameEn': iso2}

def fetch_movie(tmdb_id):
    url = (f'https://api.themoviedb.org/3/movie/{tmdb_id}'
           f'?api_key={API_KEY}&language=zh-CN')
    for attempt in range(1, MAX_RETRY + 1):
        try:
            with urllib.request.urlopen(url, timeout=12, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < MAX_RETRY:
                time.sleep(attempt)
            else:
                raise e

def read_js(path, var_name):
    text = open(path, encoding='utf-8').read()
    # 提取 const VAR = [...]; 或 var VAR = [...];
    m = re.search(rf'(?:const|var)\s+{var_name}\s*=\s*(\[.*?\]);', text, re.DOTALL)
    if not m:
        raise ValueError(f'在 {path} 中找不到变量 {var_name}')
    return json.loads(m.group(1)), text

def write_js(path, var_name, items, original_text):
    new_json = json.dumps(items, ensure_ascii=False, indent=2)
    new_decl = f'const {var_name} = {new_json};'
    new_text = re.sub(
        rf'(?:const|var)\s+{var_name}\s*=\s*\[.*?\];',
        new_decl, original_text, flags=re.DOTALL
    )
    open(path, 'w', encoding='utf-8').write(new_text)

# ─── main ────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2 or sys.argv[1] not in TARGETS:
    print('用法: python3 scripts/enrich_countries.py bear|lion')
    sys.exit(1)

cfg = TARGETS[sys.argv[1]]
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

items, original_text = read_js(cfg['input'], cfg['var_name'])
print(f'读取 {len(items)} 条，开始补制片国…')

ok = no_country = 0
null_list = []

for i, it in enumerate(items):
    tid = it.get('tmdbId')
    if not tid:
        it['mainCountry'] = None
        it['productionCountries'] = []
        it['originCountryRaw'] = []
        no_country += 1
        null_list.append(it.get('titleCN','?'))
        print(f'[{i+1}/{len(items)}] {it.get("titleCN")} — 无 tmdbId，跳过')
        continue
    try:
        data = fetch_movie(tid)
        origin_raw = data.get('origin_country') or []
        prod_countries = data.get('production_countries') or []

        # 构建 productionCountries 列表
        pc_list = []
        for pc in prod_countries:
            iso2 = pc.get('iso_3166_1','')
            name_en = pc.get('name','')
            entry = iso2_to_entry(iso2, '')
            if not entry['nameEn'] or entry['nameEn'] == iso2:
                entry['nameEn'] = name_en
            pc_list.append(entry)

        # 主制片国
        main_iso2 = origin_raw[0] if origin_raw else (prod_countries[0]['iso_3166_1'] if prod_countries else None)
        if main_iso2:
            main_entry = iso2_to_entry(main_iso2)
            # MANUAL_OVERRIDE 覆盖（如YU片逐部确认）
            override_key = f"{cfg['var_name']}|{it.get('titleCN','')}"
            if override_key in MANUAL_OVERRIDE:
                main_entry = MANUAL_OVERRIDE[override_key]
            ok += 1
        else:
            main_entry = None
            no_country += 1
            null_list.append(it.get('titleCN','?'))

        it['mainCountry'] = main_entry
        it['productionCountries'] = pc_list
        it['originCountryRaw'] = origin_raw
        print(f'[{i+1}/{len(items)}] {it.get("titleCN")} → {main_iso2} ({main_entry["name"] if main_entry else "null"})')
    except Exception as e:
        it['mainCountry'] = None
        it['productionCountries'] = []
        it['originCountryRaw'] = []
        no_country += 1
        null_list.append(it.get('titleCN','?'))
        print(f'[{i+1}/{len(items)}] {it.get("titleCN")} — 失败: {e}')
    time.sleep(GAP)

write_js(cfg['output'], cfg['var_name'], items, original_text)
print(f'\n完成。成功 {ok} | mainCountry=null {no_country}')
if null_list:
    print('待人工补：', ', '.join(null_list))
print(f'已写出: {cfg["output"]}')
