#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMDB 电影元数据抓取脚本
========================
用途：根据片单，从 TMDB 官方 API 抓取电影元数据 + 海报，
      汇总成 movies.json，供「政治光谱」demo 使用。

使用方法：
  1. pip install requests
  2. 把下面 API_KEY 换成你自己的 TMDB v3 密钥
  3. 在 MOVIE_LIST 里填片名（中文或英文都行，建议附上年份更精准）
  4. python fetch_movies.py
  5. 运行后生成：
       - movies.json        （所有电影数据）
       - posters/           （海报图片，w500 中等清晰度）
       - not_found.txt      （没搜到的片名，方便你换名字重试）

注意：API_KEY 不要写死后推到 GitHub。可以用环境变量，或推送前清空。
"""

import os
import json
import time
import requests

# ============================================================
# 1. 配置区 —— 你只需要改这两个地方
# ============================================================

# 你的 TMDB v3 API 密钥（建议先在 TMDB 重置一个新的再填）
# 更安全的做法：设环境变量 TMDB_API_KEY，下面这行就会自动读取
API_KEY = os.environ.get("TMDB_API_KEY", "在这里填你的key")

# 片单：边跑边往里加。格式可以是：
#   "电影名"                 —— 只给名字
#   ("电影名", 年份)          —— 给名字+年份（更精准，推荐用于重名片）
# 中英文都能搜。下面是一批示范片单（覆盖光谱 5 档），你可自由增删。
MOVIE_LIST = [
    # —— 偏左 / 纯左锚点 ——
    ("我是布莱克", 2016),          # Ken Loach，社会现实主义，批判福利制度
    ("对不起，我们错过了你", 2019),  # Ken Loach，零工经济批判
    ("寄生虫", 2019),              # 奉俊昊，阶级议题
    ("小丑", 2019),                # 阶级、社会失序
    ("华氏911", 2004),             # Michael Moore 政治纪录片
    # —— 中间 / 争议档 ——
    ("奥本海默", 2023),
    ("沙丘", 2021),
    ("芭比", 2023),
    ("音乐之声", 1965),
    ("阿甘正传", 1994),
    # —— 偏右 / 保守倾向锚点 ——
    ("美国狙击手", 2014),          # Clint Eastwood，常被读作保守/爱国叙事
    ("勇敢的心", 1995),
    ("壮志凌云：独行侠", 2022),
    ("战狼2", 2017),               # 民族主义叙事
    ("长津湖", 2021),              # 主旋律
]

# ============================================================
# 2. 以下是抓取逻辑 —— 一般不需要改
# ============================================================

BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"  # w500 = 中等清晰度，体积小、下载快
POSTER_DIR = "posters"
SLEEP = 0.3  # 每次请求间隔（秒），礼貌间隔，TMDB 完全允许

session = requests.Session()
session.params = {"api_key": API_KEY}


def search_movie(title, year=None):
    """按片名（可选年份）搜索，返回第一个匹配的电影 id。"""
    params = {"query": title, "language": "zh-CN"}
    if year:
        params["year"] = year
    r = session.get(f"{BASE}/search/movie", params=params, timeout=15)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0]["id"] if results else None


def get_details(movie_id):
    """取电影详情（中文优先），并通过 append_to_response 一次性带出演职员。"""
    params = {"language": "zh-CN", "append_to_response": "credits"}
    r = session.get(f"{BASE}/movie/{movie_id}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def extract_director(credits):
    """从 credits 里找出导演（可能有多位）。"""
    crew = credits.get("crew", [])
    directors = [c["name"] for c in crew if c.get("job") == "Director"]
    return directors


def download_poster(poster_path, movie_id):
    """下载海报到本地 posters/ 目录，返回本地文件名。"""
    if not poster_path:
        return None
    os.makedirs(POSTER_DIR, exist_ok=True)
    filename = f"{movie_id}{os.path.splitext(poster_path)[1]}"
    local_path = os.path.join(POSTER_DIR, filename)
    if os.path.exists(local_path):  # 已下载过就跳过
        return filename
    url = IMG_BASE + poster_path
    r = session.get(url, timeout=30)
    r.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(r.content)
    return filename


def main():
    if API_KEY in ("在这里填你的key", ""):
        print("❌ 请先在脚本顶部填入你的 TMDB API_KEY")
        return

    movies = []
    not_found = []

    for item in MOVIE_LIST:
        if isinstance(item, tuple):
            title, year = item
        else:
            title, year = item, None

        label = f"{title}" + (f" ({year})" if year else "")
        try:
            mid = search_movie(title, year)
            if not mid:
                # 带年份没搜到，去掉年份再试一次
                if year:
                    mid = search_movie(title, None)
            if not mid:
                print(f"⚠️  没搜到：{label}")
                not_found.append(label)
                time.sleep(SLEEP)
                continue

            d = get_details(mid)
            poster_file = download_poster(d.get("poster_path"), mid)
            directors = extract_director(d.get("credits", {}))

            movie = {
                "id": mid,
                "title_cn": d.get("title"),                    # 中文片名
                "title_original": d.get("original_title"),     # 原始片名
                "year": (d.get("release_date") or "")[:4],     # 年份
                "directors": directors,                        # 导演列表
                "genres": [g["name"] for g in d.get("genres", [])],
                "overview": d.get("overview"),                 # 剧情简介（中文）
                "tmdb_rating": d.get("vote_average"),          # TMDB 评分
                "tmdb_votes": d.get("vote_count"),
                "runtime": d.get("runtime"),
                "poster_file": poster_file,                    # 本地海报文件名
                "poster_path": d.get("poster_path"),           # TMDB 原始路径（备用）
                # —— 以下字段留空，后续做光谱判定时填入 ——
                "spectrum": None,        # 5 档之一：纯左/偏左/中立/偏右/纯右
                "spectrum_reason": "",   # 判定理由（一句话）
            }
            movies.append(movie)
            print(f"✅ {movie['title_cn']} ({movie['year']}) — 导演：{', '.join(directors) or '未知'}")

        except requests.HTTPError as e:
            print(f"❌ 请求出错 {label}：{e}")
            not_found.append(label)
        except Exception as e:
            print(f"❌ 处理出错 {label}：{e}")
            not_found.append(label)

        time.sleep(SLEEP)

    # 写出结果
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

    if not_found:
        with open("not_found.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(not_found))

    print("\n" + "=" * 40)
    print(f"完成：成功 {len(movies)} 部，失败 {len(not_found)} 部")
    print(f"数据已写入 movies.json")
    print(f"海报已存入 {POSTER_DIR}/")
    if not_found:
        print(f"没搜到的片名见 not_found.txt（可换个名字或加/去年份重试）")
    print("=" * 40)


if __name__ == "__main__":
    main()
