#!/usr/bin/env python3
"""
把 GoldenBear-XLarge 里的海报（按 douban subjectId 命名）
复制到 GoldenBear-TMDB 子文件夹，按 TMDB ID 重命名为 {tmdbId}.jpg
"""
import json, os, shutil, re

SRC_DIR   = "/Users/qm/Documents/WMS/posters_local/GoldenBear-XLarge"
DST_DIR   = "/Users/qm/Documents/WMS/posters_local/GoldenBear-TMDB"
JSON_FILE = "/Users/qm/Downloads/output_with_tmdb.json"

# 读取映射
with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

# subjectId -> tmdbId
subj2tmdb = {}
for item in data:
    sid = str(item.get("subjectId", "")).strip()
    tid = item.get("tmdbId")
    if sid and tid:
        subj2tmdb[sid] = str(tid)

print(f"映射条数: {len(subj2tmdb)}")

os.makedirs(DST_DIR, exist_ok=True)

copied = 0
skipped = 0

for fname in os.listdir(SRC_DIR):
    if not fname.lower().endswith(".jpg"):
        continue
    # 文件名末尾的数字即 subjectId（去掉 .jpg 后最后一段空格分隔的 token）
    stem = fname[:-4]  # 去掉 .jpg
    tokens = stem.rsplit(" ", 1)
    if len(tokens) < 2:
        print(f"  [SKIP] 无法解析: {fname}")
        skipped += 1
        continue
    subj_id = tokens[1].strip()
    if subj_id not in subj2tmdb:
        print(f"  [MISS] subjectId={subj_id}  {fname}")
        skipped += 1
        continue
    tmdb_id = subj2tmdb[subj_id]
    dst_fname = f"{tmdb_id}.jpg"
    shutil.copy2(os.path.join(SRC_DIR, fname), os.path.join(DST_DIR, dst_fname))
    print(f"  OK  {fname}  ->  {dst_fname}")
    copied += 1

print(f"\n完成: 复制 {copied} 张，跳过 {skipped} 张")
print(f"目标目录: {DST_DIR}")
