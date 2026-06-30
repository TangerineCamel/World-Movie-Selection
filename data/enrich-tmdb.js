// enrich-tmdb.js
// 读取 lion-metadata-82.json，用 imdbID 调 TMDB 换 tmdbId，仅新增 tmdbId 字段，输出 JS 数据文件。
// 运行： TMDB_KEY=你的key node enrich-tmdb.js
//
// 依赖：Node 18+（内置 fetch）。若 Node 较低需 `npm i node-fetch` 并自行引入。

const fs = require('fs');
const path = require('path');

// ============ 配置 ============
const INPUT_JSON = './data/lion-metadata-82.json';   // 输入 JSON 路径（按实际位置改）
const OUTPUT_JS  = './data/lion-metadata.js';         // 输出 JS 路径
const JS_VAR_NAME = 'lionList';                        // 导出的变量名（按 WMS 习惯改）
const TMDB_KEY = process.env.TMDB_KEY;                 // key 走环境变量，勿硬编码
const REQUEST_GAP_MS = 300;                            // 每次请求间隔，防限流
const MAX_RETRY = 3;                                   // 单条失败重试次数

if (!TMDB_KEY) {
  console.error('缺少 TMDB_KEY 环境变量。运行方式： TMDB_KEY=你的key node enrich-tmdb.js');
  process.exit(1);
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// 用 imdbID 换 tmdbId
async function fetchTmdbId(imdbId) {
  const url = `https://api.themoviedb.org/3/find/${imdbId}`
    + `?external_source=imdb_id&api_key=${TMDB_KEY}`;
  const res = await fetch(url);
  if (res.status === 429) {                 // 限流，抛出让上层重试
    throw { retryable: true, msg: 'rate limited (429)' };
  }
  if (!res.ok) throw { retryable: false, msg: `HTTP ${res.status}` };
  const data = await res.json();
  const hit = data.movie_results && data.movie_results[0];
  return hit ? hit.id : null;               // null = TMDB 未收录
}

async function fetchWithRetry(imdbId) {
  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    try {
      return await fetchTmdbId(imdbId);
    } catch (e) {
      if (e.retryable && attempt < MAX_RETRY) {
        await sleep(1000 * attempt);        // 退避
        continue;
      }
      throw new Error(e.msg || String(e));
    }
  }
}

async function main() {
  const raw = fs.readFileSync(path.resolve(INPUT_JSON), 'utf-8');
  const items = JSON.parse(raw);
  console.log(`读取 ${items.length} 条。开始补 tmdbId…`);

  let ok = 0, noTmdb = 0, fail = 0;
  const failed = [];

  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const imdb = it.imdbId;

    if (!imdb) {                            // 本身没 imdbID，跳过
      it.tmdbId = null;
      noTmdb++;
      console.log(`[${i + 1}/${items.length}] ${it.titleCN || it.titleFull} — 无 imdbID，跳过`);
      continue;
    }

    try {
      const tmdbId = await fetchWithRetry(imdb);
      it.tmdbId = tmdbId;                   // 唯一新增字段
      if (tmdbId) { ok++; console.log(`[${i + 1}/${items.length}] ${it.titleCN} → tmdbId ${tmdbId}`); }
      else { noTmdb++; console.log(`[${i + 1}/${items.length}] ${it.titleCN} — TMDB 未收录`); }
    } catch (e) {
      it.tmdbId = null;
      fail++;
      failed.push({ titleCN: it.titleCN, imdbId: imdb, error: e.message });
      console.warn(`[${i + 1}/${items.length}] ${it.titleCN} — 失败: ${e.message}`);
    }

    await sleep(REQUEST_GAP_MS);
  }

  // 写出 JS 文件
  const js = `// 自动生成：威尼斯金狮元数据（含 tmdbId）\n`
    + `const ${JS_VAR_NAME} = ${JSON.stringify(items, null, 2)};\n\n`
    + `if (typeof module !== 'undefined' && module.exports) { module.exports = ${JS_VAR_NAME}; }\n`;
  fs.writeFileSync(path.resolve(OUTPUT_JS), js, 'utf-8');

  console.log(`\n完成。成功 ${ok}｜未收录 ${noTmdb}｜失败 ${fail}`);
  console.log(`已写出：${OUTPUT_JS}（变量 ${JS_VAR_NAME}）`);
  if (failed.length) {
    console.log('\n失败清单（可手动补或重跑）：');
    failed.forEach(f => console.log(`  ${f.titleCN} (${f.imdbId}): ${f.error}`));
  }
}

main().catch(e => { console.error('脚本异常：', e); process.exit(1); });
