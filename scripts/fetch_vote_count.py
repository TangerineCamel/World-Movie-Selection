#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMS · 补全 TMDB 投票数(vote_count)
====================================
不重新搜片，直接用已有的 tmdb_id 拉一次详情，补上 vote_count 字段
（评分可信度依据：多少人打了分）。

用法（WMS/ 目录，需代理）：
  export https_proxy=http://127.0.0.1:7890
  export http_proxy=http://127.0.0.1:7890
  export TMDB_API_KEY="你的key"
  python3 scripts/fetch_vote_count.py

特点：已有 vote_count 的跳过（断点续跑）；写回 data/movies.js（备份 .bak3）。
"""
import os, json, time, requests, shutil

DATA_PATH = "data/movies.js"
BASE = "https://api.themoviedb.org/3"
SLEEP = 0.25
API_KEY = os.environ.get("TMDB_API_KEY", "")


def load_data(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.index("[")
    end = text.rindex("]") + 1
    return json.loads(text[start:end]), text[:start]


def main():
    if not API_KEY:
        print("❌ 请先设置 TMDB_API_KEY 环境变量")
        return
    records, prefix = load_data(DATA_PATH)
    print(f"读取到 {len(records)} 条记录")

    filled, skipped, failed = 0, 0, []
    sess = requests.Session()
    sess.params = {"api_key": API_KEY}

    for rec in records:
        if rec.get("vote_count") is not None:   # 已补过
            skipped += 1
            continue
        mid = rec.get("tmdb_id")
        if not mid:
            continue
        try:
            r = sess.get(f"{BASE}/movie/{mid}", params={"language": "zh-CN"}, timeout=15)
            r.raise_for_status()
            d = r.json()
            rec["vote_count"] = d.get("vote_count")
            # 顺便同步一下评分（确保和人数对应同一次快照）
            rec["tmdb_rating"] = d.get("vote_average")
            filled += 1
            print(f"✅ {rec.get('title_cn','')} — {rec['tmdb_rating']}分 / {rec['vote_count']}人")
        except Exception as e:
            print(f"❌ {rec.get('title_cn','')} ({mid}): {e}")
            failed.append(rec.get("title_cn", ""))
        time.sleep(SLEEP)

    if os.path.exists(DATA_PATH):
        shutil.copy(DATA_PATH, DATA_PATH + ".bak3")
    head = prefix.strip() or "const WMS_DATA ="
    if not head.endswith("="):
        head = "const TWMS_DATA ="
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        f.write(head + " ")
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write(";")

    print("\n" + "=" * 44)
    print(f"完成：补全 {filled} 条，跳过 {skipped} 条")
    if failed:
        print(f"失败 {len(failed)} 条：{', '.join(failed)}")
    print("=" * 44)


if __name__ == "__main__":
    main()
