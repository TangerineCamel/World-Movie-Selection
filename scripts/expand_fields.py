#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把解析好的奥斯卡记录扩成完整字段结构(预留待补字段)。"""
import json

with open('/home/claude/twms/oscar_parsed.json', encoding='utf-8') as f:
    src = json.load(f)

out = []
for i, r in enumerate(src):
    out.append({
        # —— 已有字段 ——
        "id": f"oscar-{r['edition']}-{i}",   # 临时唯一 id
        "award": r['award'],                  # 奖项名
        "award_key": "oscar_best_picture",    # 奖项标识(程序用)
        "year": r['year'],                    # 年份(摄制年)
        "edition": r['edition'],              # 届次
        "type": r['type'],                    # 获奖 / 提名
        "title_cn": r['title_cn'],            # 中文名(维基,后续可用 TMDB 简中覆盖)
        "title_en": r['title_en'],            # 英文/原文名
        "lang": r['lang'],                    # 语言标记(非英语片才有)
        # —— 预留：待 TMDB 脚本批量补 ——
        "tmdb_id": None,                      # TMDB 影片 id
        "directors": [],                      # 导演
        "countries": [],                      # 制片国(地图/国别统计用)
        "poster": None,                       # 海报链接
        "tmdb_rating": None,                  # TMDB 评分
        "tmdb_title_cn": None,                # TMDB 简中译名(更贴国内)
        # —— 预留：待豆瓣补 ——
        "douban_id": None,                    # 豆瓣 subject id
        "douban_rating": None,                # 豆瓣评分
    })

with open('/home/claude/twms/twms_data.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"已扩展 {len(out)} 条记录,写入 twms_data.json")
print("\n字段结构示例(第1条):")
print(json.dumps(out[0], ensure_ascii=False, indent=2))
