import json, ssl, time, urllib.request, os, shutil, re

API_KEY = '5d71ba15ace52c171577c1fa5df4c573'
INPUT   = 'data/cannes-metadata-89.json'
OUTPUT  = 'data/cannes_metadata.js'
SRC_DIR = 'posters_local/Cannes-Xlarge'
DST_DIR = 'posters_local/Cannes-TMDB'
GAP     = 0.3
MAX_RETRY = 3

ctx = ssl._create_unverified_context()

def fetch_tmdb_id(imdb_id):
    url = f'https://api.themoviedb.org/3/find/{imdb_id}?external_source=imdb_id&api_key={API_KEY}'
    for attempt in range(1, MAX_RETRY + 1):
        try:
            with urllib.request.urlopen(url, timeout=10, context=ctx) as r:
                data = json.loads(r.read())
                results = data.get('movie_results', [])
                return results[0]['id'] if results else None
        except Exception as e:
            if attempt < MAX_RETRY:
                time.sleep(attempt)
            else:
                raise e

with open(INPUT, encoding='utf-8') as f:
    items = json.load(f)

print(f'读取 {len(items)} 条，开始补 tmdbId…')
ok = no_tmdb = fail = 0
failed = []

for i, it in enumerate(items):
    imdb = it.get('imdbId')
    if not imdb:
        it['tmdbId'] = None
        no_tmdb += 1
        print(f'[{i+1}/{len(items)}] {it["titleCN"]} — 无 imdbId，跳过')
        continue
    try:
        tid = fetch_tmdb_id(imdb)
        it['tmdbId'] = tid
        if tid:
            ok += 1
            print(f'[{i+1}/{len(items)}] {it["titleCN"]} → {tid}')
        else:
            no_tmdb += 1
            print(f'[{i+1}/{len(items)}] {it["titleCN"]} — TMDB 未收录')
    except Exception as e:
        it['tmdbId'] = None
        fail += 1
        failed.append({'titleCN': it['titleCN'], 'imdbId': imdb, 'error': str(e)})
        print(f'[{i+1}/{len(items)}] {it["titleCN"]} — 失败: {e}')
    time.sleep(GAP)

js = 'const CANNES_DATA = ' + json.dumps(items, ensure_ascii=False, indent=2) + ';\n'
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(js)

print(f'\n完成。成功 {ok} | 未收录 {no_tmdb} | 失败 {fail}')
print(f'输出: {OUTPUT}')
if failed:
    print('\n失败清单:')
    for x in failed:
        print(f'  {x["titleCN"]} ({x["imdbId"]}): {x["error"]}')

# ===== 复制并重命名海报 =====
print('\n开始复制海报…')
os.makedirs(DST_DIR, exist_ok=True)
sid2tmdb = {str(it['subjectId']): it.get('tmdbId') for it in items}

copied = skipped = 0
for fname in os.listdir(SRC_DIR):
    if not fname.lower().endswith('.jpg'):
        continue
    m = re.search(r'(\d+)\.jpg$', fname)
    if not m:
        print(f'  跳过（无法解析）: {fname}')
        continue
    sid = m.group(1)
    tid = sid2tmdb.get(sid)
    if not tid:
        print(f'  跳过（无 tmdbId）: {fname}')
        skipped += 1
        continue
    src = os.path.join(SRC_DIR, fname)
    dst = os.path.join(DST_DIR, f'{tid}.jpg')
    shutil.copy2(src, dst)
    copied += 1

print(f'海报复制完成：{copied} 张成功，{skipped} 张跳过')
print(f'目标目录: {DST_DIR}')
