import json, re

CURRENT = {
'AD','AE','AF','AG','AI','AL','AM','AO','AQ','AR','AS','AT','AU','AW','AX','AZ',
'BA','BB','BD','BE','BF','BG','BH','BI','BJ','BL','BM','BN','BO','BQ','BR','BS','BT','BV','BW','BY','BZ',
'CA','CC','CD','CF','CG','CH','CI','CK','CL','CM','CN','CO','CR','CU','CV','CW','CX','CY','CZ',
'DE','DJ','DK','DM','DO','DZ',
'EC','EE','EG','EH','ER','ES','ET',
'FI','FJ','FK','FM','FO','FR',
'GA','GB','GD','GE','GF','GG','GH','GI','GL','GM','GN','GP','GQ','GR','GS','GT','GU','GW','GY',
'HK','HM','HN','HR','HT','HU',
'ID','IE','IL','IM','IN','IO','IQ','IR','IS','IT',
'JE','JM','JO','JP',
'KE','KG','KH','KI','KM','KN','KP','KR','KW','KY','KZ',
'LA','LB','LC','LI','LK','LR','LS','LT','LU','LV','LY',
'MA','MC','MD','ME','MF','MG','MH','MK','ML','MM','MN','MO','MP','MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ',
'NA','NC','NE','NF','NG','NI','NL','NO','NP','NR','NU','NZ',
'OM',
'PA','PE','PF','PG','PH','PK','PL','PM','PN','PR','PS','PT','PW','PY',
'QA',
'RE','RO','RS','RU','RW',
'SA','SB','SC','SD','SE','SG','SH','SI','SJ','SK','SL','SM','SN','SO','SR','SS','ST','SV','SX','SY','SZ',
'TC','TD','TF','TG','TH','TJ','TK','TL','TM','TN','TO','TR','TT','TV','TW','TZ',
'UA','UG','UM','US','UY','UZ',
'VA','VC','VE','VG','VI','VN','VU',
'WF','WS',
'XK',
'YE','YT',
'ZA','ZM','ZW'
}

FILES = [
    ('data/golden_bear.js', 'GOLDEN_BEAR_DATA', '金熊'),
    ('data/lion_metadata.js', 'GOLDEN_LION_DATA', '金狮'),
    ('data/cannes_metadata.js', 'CANNES_DATA', '戛纳'),
]

for fname, varname, label in FILES:
    text = open(fname, encoding='utf-8').read()
    m = re.search(rf'(?:const|var)\s+{varname}\s*=\s*(\[.*?\]);', text, re.DOTALL)
    items = json.loads(m.group(1))
    print(f'\n=== {label} ({fname}) ===')
    found = False
    for it in items:
        mc = it.get('mainCountry') or {}
        iso2 = mc.get('iso2', '')
        if iso2 and iso2 not in CURRENT:
            found = True
            print(f"  titleCN={it.get('titleCN')}  year={it.get('year')}")
            print(f"  mainCountry.iso2={iso2}")
            print(f"  originCountryRaw={it.get('originCountryRaw')}")
            print(f"  productionCountries={[p.get('iso2') for p in it.get('productionCountries',[])]}")
            print()
    if not found:
        print('  （无）')
