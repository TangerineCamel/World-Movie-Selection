#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMS · 海报下载脚本
==================
读取 data/movies.js，把每条的 poster（TMDB 在线链接）下载到 posters/{tmdb_id}.jpg，
并把数据里的 poster 字段改成本地相对路径 posters/{tmdb_id}.jpg。
原 TMDB 链接保留到 poster_tmdb 字段（备份，以后重下用）。

用法（在 WMS/ 目录运行，需要代理能访问 image.tmdb.org）：
  export https_proxy=http://127.0.0.1:7890
  export http_proxy=http://127.0.0.1:7890
  python3 scripts/download_posters.py

特点：
  - 已下载的图自动跳过（断点续跑）。
  - 下载失败的会列出来，重跑即可补。
  - 运行后 data/movies.js 更新（旧文件备份为 .bak2）。
"""

import os
import json
import time
import requests

DATA_PATH = "data/movies.js"
POSTER_DIR = "posters"
SLEEP = 0.2


def load_data(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.index("[")
    end = text.rindex("]") + 1
    return json.loads(text[start:end]), text[:start]


def save_data(path, records, prefix):
    if os.path.exists(path):
        # 用 .bak2 避免覆盖上一步的 .bak
        import shutil
        shutil.copy(path, path + ".bak2")
    head = prefix.strip()
    if not head.endswith("="):
        head = "const WMS_DATA ="
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + " ")
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write(";")


def main():
    os.makedirs(POSTER_DIR, exist_ok=True)
    records, prefix = load_data(DATA_PATH)
    print(f"读取到 {len(records)} 条记录")

    failed = []
    downloaded = 0
    skipped = 0

    for rec in records:
        tmdb_id = rec.get("tmdb_id")
        poster = rec.get("poster")
        # 没有 tmdb_id 或没有海报链接的跳过
        if not tmdb_id or not poster:
            continue
        # 如果 poster 已经是本地路径了，说明这条处理过，跳过
        if poster.startswith(POSTER_DIR):
            skipped += 1
            continue

        local_name = f"{tmdb_id}.jpg"
        local_path = os.path.join(POSTER_DIR, local_name)
        rel_path = f"{POSTER_DIR}/{local_name}"

        # 文件已存在就不重下，只改字段
        if os.path.exists(local_path):
            rec["poster_tmdb"] = poster
            rec["poster"] = rel_path
            skipped += 1
            continue

        try:
            r = requests.get(poster, timeout=30)
            r.raise_for_status()
            with open(local_path, "wb") as imgf:
                imgf.write(r.content)
            rec["poster_tmdb"] = poster      # 备份原链接
            rec["poster"] = rel_path          # 改成本地路径
            downloaded += 1
            kb = len(r.content) // 1024
            print(f"✅ {rec.get('title_cn','')} → {rel_path} ({kb}KB)")
        except Exception as e:
            print(f"❌ 下载失败 {rec.get('title_cn','')} ({tmdb_id})：{e}")
            failed.append(f"{rec.get('title_cn','')} ({tmdb_id})")
        time.sleep(SLEEP)

    save_data(DATA_PATH, records, prefix)

    print("\n" + "=" * 44)
    print(f"完成：新下载 {downloaded} 张，跳过 {skipped} 张")
    print(f"海报存于 {POSTER_DIR}/，数据已更新 {DATA_PATH}")
    if failed:
        print(f"\n以下 {len(failed)} 张下载失败，重跑脚本可补：")
        for x in failed:
            print(f"  - {x}")
    print("=" * 44)


if __name__ == "__main__":
    main()
