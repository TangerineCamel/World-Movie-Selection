#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMS · TMDB 数据补全脚本
========================
读取 data/movies.js 里的电影记录，用 TMDB API 补全：
  海报、TMDB id、导演、制片国、TMDB 评分、TMDB 简中译名
然后写回 data/movies.js（含完整字段）。

用法：
  1. pip install requests
  2. 填入你的 TMDB v3 API key（或设环境变量 TMDB_API_KEY）
  3. 把本脚本放在 WMS/scripts/ 下，在 WMS/ 目录运行：
       python scripts/fetch_wms_posters.py
  4. 运行后 data/movies.js 会被更新（原文件先备份为 movies.js.bak）

说明：
  - 用「英文原名 + 年份」去 TMDB 搜索，最精准。
  - 海报用 w500（中等清晰度，在线链接，前端直接引用，不下载到本地）。
  - 制片国取 TMDB 的 production_countries，第一个为主（地图/国别统计用）。
  - 搜不到的会记进 not_found 列表，最后打印出来，方便你手动处理。
"""

import os
import re
import json
import time
import requests

API_KEY = os.environ.get("TMDB_API_KEY", "在这里填你的key")

# 路径：假设在 WMS/ 目录运行
DATA_PATH = "data/movies.js"

BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"
SLEEP = 0.3

session = requests.Session()
session.params = {"api_key": API_KEY}


def load_data(path):
    """从 movies.js 里抠出 JSON 数组（去掉 const TWMS_DATA = ... ; 包装）。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 找到第一个 [ 到最后一个 ] 之间的内容
    start = text.index("[")
    end = text.rindex("]") + 1
    return json.loads(text[start:end]), text[:start]


def save_data(path, records, prefix):
    """写回 movies.js，保持 const 包装；先备份。"""
    if os.path.exists(path):
        os.replace(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        # 用原来的前缀（const TWMS_DATA = 之类），没有就用默认
        head = prefix.strip() or "const WMS_DATA ="
        if not head.endswith("="):
            head = "const WMS_DATA ="
        f.write(head + " ")
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write(";")


def search_movie(title_en, year):
    """按英文名+年份搜 TMDB，返回第一个结果 id。"""
    params = {"query": title_en, "language": "zh-CN"}
    if year and str(year).isdigit():
        params["year"] = year
    r = session.get(f"{BASE}/search/movie", params=params, timeout=15)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results and year:
        # 带年份没搜到，去年份再试
        r = session.get(f"{BASE}/search/movie",
                        params={"query": title_en, "language": "zh-CN"}, timeout=15)
        r.raise_for_status()
        results = r.json().get("results", [])
    return results[0]["id"] if results else None


def get_details(mid):
    params = {"language": "zh-CN", "append_to_response": "credits"}
    r = session.get(f"{BASE}/movie/{mid}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def main():
    if API_KEY in ("在这里填你的key", ""):
        print("❌ 请先填入 TMDB API_KEY")
        return

    records, prefix = load_data(DATA_PATH)
    print(f"读取到 {len(records)} 条记录")

    not_found = []
    filled = 0

    for i, rec in enumerate(records):
        # 已经补过的跳过（断点续跑）
        if rec.get("tmdb_id"):
            continue
        title_en = rec.get("title_en", "")
        year = rec.get("year", "")[:4]
        label = f"{rec.get('title_cn','')} / {title_en} ({year})"
        try:
            mid = search_movie(title_en, year)
            if not mid:
                print(f"⚠️  没搜到：{label}")
                not_found.append(label)
                time.sleep(SLEEP)
                continue
            d = get_details(mid)
            crew = d.get("credits", {}).get("crew", [])
            directors = [c["name"] for c in crew if c.get("job") == "Director"]
            countries = [c["name"] for c in d.get("production_countries", [])]
            country_codes = [c["iso_3166_1"] for c in d.get("production_countries", [])]

            rec["tmdb_id"] = mid
            rec["directors"] = directors
            rec["countries"] = countries
            rec["country_codes"] = country_codes   # 国家代码（地图上色用）
            rec["poster"] = (IMG + d["poster_path"]) if d.get("poster_path") else None
            rec["tmdb_rating"] = d.get("vote_average")
            rec["tmdb_title_cn"] = d.get("title")   # TMDB 简中译名

            filled += 1
            print(f"✅ {rec['tmdb_title_cn']} ({year}) — {', '.join(directors) or '导演未知'} — {', '.join(countries) or '国别未知'}")
        except requests.HTTPError as e:
            print(f"❌ 请求出错 {label}：{e}")
            not_found.append(label)
        except Exception as e:
            print(f"❌ 处理出错 {label}：{e}")
            not_found.append(label)
        time.sleep(SLEEP)

    save_data(DATA_PATH, records, prefix)

    print("\n" + "=" * 44)
    print(f"完成：本次补全 {filled} 条")
    print(f"数据已写回 {DATA_PATH}（旧文件备份为 {DATA_PATH}.bak）")
    if not_found:
        print(f"\n以下 {len(not_found)} 部没搜到，建议手动核对英文名或年份：")
        for x in not_found:
            print(f"  - {x}")
    print("=" * 44)


if __name__ == "__main__":
    main()
