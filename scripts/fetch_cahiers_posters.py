#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电影手册 61 部海报下载脚本
从 TMDB 按 tmdb_id 下载海报，命名为 {tmdb_id}.jpg，输出到 ./cahiers_posters/
然后你把这些 jpg 传到 OSS 的 posters/ 目录即可。

用法:
    1. 填入你的 TMDB API key(下方 TMDB_API_KEY)
       —— 你之前下载奥斯卡海报时应该已经有 key，在 scripts/fetch_wms_posters.py 里能找到
    2. python3 fetch_cahiers_posters.py
    3. 把 cahiers_posters/ 里的 jpg 传到 OSS posters/

依赖: pip install requests
"""

import os
import time
import requests

# ===== 填这里 =====
TMDB_API_KEY = "5d71ba15ace52c171577c1fa5df4c573"   # 从 scripts/fetch_wms_posters.py 里复制你已有的 key
# ==================

OUT_DIR = "cahiers_posters"
IMG_BASE = "https://image.tmdb.org/t/p/w500"   # w500 尺寸，和你奖项库一致

# 61 部的 tmdb_id（电影手册 2020-2025）
TMDB_IDS = [
    726041, 662401, 473033, 575448, 661935, 535550, 596881, 574094, 640561, 562299,  # 2020
    558582, 424277, 511819, 758866, 602334, 542178, 665753, 517815, 643352, 454527,  # 2021
    691214, 718032, 762504, 785398, 795811, 848950, 664996, 784611, 660709, 837602,  # 2022
    715742, 997294, 915935, 804095, 986280, 749136, 937085, 1000517, 812037, 1110135, 790416,  # 2023(11部)
    1063574, 839369, 1077647, 467244, 927547, 714889, 1156125, 1001434, 1032823, 1255171,  # 2024
    975324, 1054867, 1149614, 1220564, 1103551, 1317616, 1301218, 1254808, 1383289, 1178602,  # 2025
]

# 这些片你奖项库已有海报(坠落的审判/一战再战),可跳过不重下，但重下也无妨(同一张)
ALREADY_HAVE = {915935, 1054867}

def main():
    if TMDB_API_KEY == "你的TMDB_API_KEY":
        print("⚠️ 请先在脚本里填入你的 TMDB_API_KEY")
        print("   去 scripts/fetch_wms_posters.py 里复制你已有的 key")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"共 {len(TMDB_IDS)} 部，输出到 {OUT_DIR}/\n")

    ok, fail = 0, []
    for tid in TMDB_IDS:
        dst = os.path.join(OUT_DIR, f"{tid}.jpg")
        if os.path.exists(dst):
            print(f"  [跳过] {tid}.jpg 已存在")
            ok += 1
            continue
        try:
            # 查 TMDB 拿 poster_path
            url = f"https://api.themoviedb.org/3/movie/{tid}"
            r = requests.get(url, params={"api_key": TMDB_API_KEY, "language": "zh-CN"}, timeout=15)
            r.raise_for_status()
            poster_path = r.json().get("poster_path")
            if not poster_path:
                print(f"  [无海报] {tid} TMDB上没有poster_path")
                fail.append(tid)
                continue
            # 下载海报图
            img_url = IMG_BASE + poster_path
            img = requests.get(img_url, timeout=30)
            img.raise_for_status()
            with open(dst, "wb") as f:
                f.write(img.content)
            tag = " (奖项库已有,可不传)" if tid in ALREADY_HAVE else ""
            print(f"  [完成] {tid}.jpg{tag}")
            ok += 1
            time.sleep(0.3)  # 礼貌限速
        except Exception as e:
            print(f"  [出错] {tid}: {e}")
            fail.append(tid)

    print(f"\n完成 {ok}/{len(TMDB_IDS)}")
    if fail:
        print(f"失败/无海报 {len(fail)} 个: {fail}")
        print("这些需要你手动去 TMDB 网站找海报，或用别的来源。")
    print(f"\n下一步: 把 {OUT_DIR}/ 里的 jpg 传到 OSS 的 posters/ 目录(覆盖/新增)。")


if __name__ == "__main__":
    main()
