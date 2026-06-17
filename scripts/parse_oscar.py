#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json

with open('/home/claude/twms/oscar_raw.txt', encoding='utf-8') as f:
    lines = [l.rstrip() for l in f if l.strip()]

records = []
cur_year = None
cur_edition = None
first_in_edition = False

# 届次标题：2010年（第83届） 或 2020/21（第93届）
year_re = re.compile(r'^(\d{4}(?:/\d{2})?)[年]?\s*（第\s*(\d+)\s*届）')
# 影片行：《中文》（English） 可能后面跟 语言标记
film_re = re.compile(r'^《(.+?)》\s*[（(](.+?)[）)]')

for line in lines:
    if line == '2010年代':
        continue
    ym = year_re.match(line)
    if ym:
        cur_year = ym.group(1)
        cur_edition = int(ym.group(2))
        first_in_edition = True
        continue
    fm = film_re.match(line)
    if fm and cur_year:
        cn = fm.group(1).strip()
        en = fm.group(2).strip()
        # 语言标记：行尾的"韩语""日语"等
        lang = ''
        tail = line[fm.end():].strip()
        if tail:
            lang = tail
        # 第一部 = 获奖，其余 = 提名
        rec_type = '获奖' if first_in_edition else '提名'
        first_in_edition = False
        records.append({
            'award': '奥斯卡最佳影片',
            'year': cur_year,
            'edition': cur_edition,
            'type': rec_type,
            'title_cn': cn,
            'title_en': en,
            'lang': lang,
        })

with open('/home/claude/twms/oscar_parsed.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

# 摘要
print(f"总记录数: {len(records)}")
print(f"届数: {len(set(r['edition'] for r in records))}")
print(f"获奖: {sum(1 for r in records if r['type']=='获奖')}, 提名: {sum(1 for r in records if r['type']=='提名')}")
print(f"带语言标记的(非英语片): {sum(1 for r in records if r['lang'])}")
print("\n=== 抽查：2021第94届 ===")
for r in records:
    if r['edition'] == 94:
        print(f"  [{r['type']}] {r['title_cn']} ({r['title_en']}) {r['lang']}")
print("\n=== 抽查：非英语片 ===")
for r in records:
    if r['lang']:
        print(f"  {r['year']} [{r['type']}] {r['title_cn']} - {r['lang']}")
