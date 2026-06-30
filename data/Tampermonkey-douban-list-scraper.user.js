// ==UserScript==
// @name         豆瓣豆列 海报+元数据 一体抓取（威尼斯金狮奖）
// @namespace    qm.wms.douban.all
// @version      1.0
// @description  遍历豆列，每部抓 XL 超高清海报 + 元数据（名字/导演/年份/imdbID/类型/片长/评分）。自动探测页数，串行、断点续传、带延时。海报直接下载，元数据可导出 JSON/CSV。
// @author       QM
// @match        https://www.douban.com/doulist/156440531*
// @grant        GM_xmlhttpRequest
// @connect      doubanio.com
// @connect      nenya.doubanio.com
// @connect      img1.doubanio.com
// @connect      img2.doubanio.com
// @connect      img3.doubanio.com
// @connect      img9.doubanio.com
// @connect      movie.douban.com
// @connect      douban.com
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ============ 配置（换片单只改这两行 + 上面 @match 的ID）============
  const DOULIST_ID = '156440531';   // 威尼斯金狮奖
  const PAGE_SIZE = 25;
  // 页数自动探测，无需手填

  const MIN_DELAY = 3000;          // 详情页/海报之间延时
  const MAX_DELAY = 6000;
  const PAGE_DELAY = 2500;         // 豆列翻页延时
  const FILE_PREFIX = '威尼斯金狮';  // 海报文件名前缀（可留空）
  const STORAGE_KEY = 'qm_douban_all_venice_v1';

  // ============ 工具 ============
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const rand = (a, b) => a + Math.floor(Math.random() * (b - a));
  const log = (...a) => console.log('[海报+元数据]', ...a);
  const sanitize = s => (s || '').replace(/[\\/:*?"<>|]/g, ' ').replace(/\s+/g, ' ').trim();

  function loadState() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch { return null; } }
  function saveState(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
  function clearState() { localStorage.removeItem(STORAGE_KEY); }

  function fetchHTML(url) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: 'GET', url, headers: { 'Referer': 'https://movie.douban.com/' },
        onload: r => (r.status >= 200 && r.status < 400) ? resolve(r.responseText) : reject(new Error('HTTP ' + r.status)),
        onerror: () => reject(new Error('网络错误')), ontimeout: () => reject(new Error('超时')), timeout: 30000,
      });
    });
  }

  function downloadImage(url, filename) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: 'GET', url, responseType: 'blob', headers: { 'Referer': 'https://movie.douban.com/' },
        onload: r => {
          if (r.status >= 200 && r.status < 400 && r.response && r.response.size > 0) {
            const a = document.createElement('a'), objUrl = URL.createObjectURL(r.response);
            a.href = objUrl; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
            setTimeout(() => URL.revokeObjectURL(objUrl), 5000);
            resolve(r.response.size);
          } else reject(new Error('图片失败 HTTP ' + r.status));
        },
        onerror: () => reject(new Error('图片网络错误')), ontimeout: () => reject(new Error('图片超时')), timeout: 60000,
      });
    });
  }

  // ============ 解析 ============
  function splitTitle(full) {
    full = (full || '').replace(/\s+/g, ' ').trim();
    const m = full.match(/^([\u4e00-\u9fa5\u3000-\u303f0-9：，·！？、…—\-\s]+?)\s+([A-Za-z].*)$/);
    return m ? { titleCN: m[1].trim(), titleOriginal: m[2].trim() } : { titleCN: full, titleOriginal: '' };
  }

  // 探测总页数：读第一页分页栏
  function detectTotalPages(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    let max = 1;
    doc.querySelectorAll('.paginator a, .paginator span').forEach(el => {
      const n = parseInt(el.textContent.trim(), 10);
      if (!isNaN(n) && n > max) max = n;
    });
    // 兜底：从 a href 的 start 参数推算
    doc.querySelectorAll('.paginator a').forEach(a => {
      const m = (a.getAttribute('href') || '').match(/start=(\d+)/);
      if (m) { const pg = Math.floor(parseInt(m[1], 10) / PAGE_SIZE) + 1; if (pg > max) max = pg; }
    });
    return max;
  }

  function parsePage(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const items = [];
    doc.querySelectorAll('div.doulist-item').forEach(item => {
      const a = item.querySelector('div.title a');
      if (!a) return;
      const idm = (a.getAttribute('href') || '').match(/subject\/(\d+)/);
      if (!idm) return;
      const subjectId = idm[1];
      const fullTitle = (a.textContent || '').replace(/\s+/g, ' ').trim();
      const { titleCN, titleOriginal } = splitTitle(fullTitle);
      let director = '', year = '';
      const ab = item.querySelector('div.abstract');
      if (ab) {
        const dm = ab.textContent.match(/导演:\s*([^\n]+?)(?:\s{2,}|主演|类型|制片|年份|$)/);
        if (dm) director = dm[1].replace(/\s+/g, ' ').trim();
        const ym = ab.textContent.match(/年份:\s*(\d{4})/);
        if (ym) year = ym[1];
      }
      items.push({
        subjectId, titleFull: fullTitle, titleCN, titleOriginal, director, year,
        detailUrl: 'https://movie.douban.com/subject/' + subjectId + '/',
        photosUrl: 'https://movie.douban.com/subject/' + subjectId + '/photos?type=R',
        imdbId: '', directorDetail: '', genres: '', runtime: '', doubanRating: '',
        posterSize: 0, detailDone: false, posterDone: false, error: '',
      });
    });
    return items;
  }

  function parseDetail(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const r = { imdbId: '', directorDetail: '', genres: '', runtime: '', doubanRating: '' };
    const dirs = [...doc.querySelectorAll('a[rel="v:directedBy"]')].map(a => a.textContent.trim()).filter(Boolean);
    if (dirs.length) r.directorDetail = dirs.join(' / ');
    const genres = [...doc.querySelectorAll('span[property="v:genre"]')].map(s => s.textContent.trim()).filter(Boolean);
    if (genres.length) r.genres = genres.join(' / ');
    const rt = doc.querySelector('span[property="v:runtime"]');
    if (rt) r.runtime = (rt.getAttribute('content') || rt.textContent.replace(/\D/g, '') || '').trim();
    const rating = doc.querySelector('strong[property="v:average"]');
    if (rating) r.doubanRating = rating.textContent.trim();
    const info = doc.querySelector('#info');
    const infoText = info ? info.textContent : doc.body.textContent;
    const im = infoText.match(/IMDb:?\s*(tt\d+)/i);
    if (im) r.imdbId = im[1];
    return r;
  }

  // 海报墙 → 单张大图页 URL
  function parsePosterWall(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const li = doc.querySelector('ul.poster-col3 li');
    if (!li) return null;
    let photoId = li.getAttribute('data-id');
    const a = li.querySelector('a[href*="/photos/photo/"]');
    let pageUrl = a ? a.getAttribute('href') : null;
    if (!pageUrl && photoId) pageUrl = 'https://movie.douban.com/photos/photo/' + photoId + '/';
    if (!pageUrl) {
      const img = li.querySelector('img');
      if (img) { const sm = (img.getAttribute('src') || '').match(/\/p(\d+)\./); if (sm) { photoId = sm[1]; pageUrl = 'https://movie.douban.com/photos/photo/' + photoId + '/'; } }
    }
    return pageUrl ? { photoId, photoPageUrl: pageUrl } : null;
  }

  // 单张大图页 → 带签名 xl URL
  function parseXLUrl(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    let a = doc.querySelector('span.magnifier a[href*="/xl/"]') || doc.querySelector('a[href*="/view/photo/xl/"]');
    if (!a) return null;
    const href = a.getAttribute('href');
    return (href && href.indexOf('/xl/') !== -1) ? href : null;
  }

  // ============ CSV ============
  function toCSV(items) {
    const headers = ['subjectId', 'imdbId', 'titleCN', 'titleOriginal', 'titleFull', 'director', 'directorDetail', 'genres', 'runtime', 'year', 'doubanRating', 'posterSize', 'detailUrl'];
    const esc = v => { v = (v == null ? '' : String(v)); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    return '\ufeff' + [headers.join(',')].concat(items.map(it => headers.map(h => esc(it[h])).join(','))).join('\n');
  }
  function downloadText(text, filename, mime) {
    const blob = new Blob([text], { type: mime }), url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }

  // ============ UI ============
  let panel, statusLine, preview;
  function buildPanel() {
    panel = document.createElement('div');
    panel.style.cssText = `position:fixed; top:80px; right:20px; width:400px; max-height:80vh;
      background:#fff; border:1px solid #ccc; border-radius:8px; z-index:99999;
      box-shadow:0 4px 20px rgba(0,0,0,.15); font-size:13px; color:#333; display:flex; flex-direction:column; overflow:hidden;`;
    panel.innerHTML = `
      <div style="padding:10px 12px; background:#b8860b; color:#fff; font-weight:bold;">海报+元数据 · 威尼斯金狮</div>
      <div id="a-status" style="padding:8px 12px; border-bottom:1px solid #eee; line-height:1.5;">点「开始/继续」。</div>
      <div style="padding:8px 12px; display:flex; gap:6px; flex-wrap:wrap; border-bottom:1px solid #eee;">
        <button id="a-run" style="flex:1; padding:6px; cursor:pointer;">开始/继续</button>
        <button id="a-reset" style="flex:1; padding:6px; cursor:pointer;">重置</button>
        <button id="a-json" style="flex:1; padding:6px; cursor:pointer;" disabled>导出 JSON</button>
        <button id="a-csv" style="flex:1; padding:6px; cursor:pointer;" disabled>导出 CSV</button>
      </div>
      <div id="a-preview" style="overflow-y:auto; padding:6px 12px; flex:1; font-size:12px;"></div>
    `;
    document.body.appendChild(panel);
    statusLine = panel.querySelector('#a-status');
    preview = panel.querySelector('#a-preview');
    panel.querySelector('#a-run').onclick = run;
    panel.querySelector('#a-reset').onclick = () => { if (confirm('清空进度重新开始？')) { clearState(); data = []; renderPreview(); statusLine.textContent = '已重置。'; toggleExport(false); } };
    panel.querySelector('#a-json').onclick = () => downloadText(JSON.stringify(data, null, 2), `${DOULIST_ID}-metadata-${data.length}.json`, 'application/json');
    panel.querySelector('#a-csv').onclick = () => downloadText(toCSV(data), `${DOULIST_ID}-metadata-${data.length}.csv`, 'text/csv');
  }
  function toggleExport(on) { panel.querySelector('#a-json').disabled = !on; panel.querySelector('#a-csv').disabled = !on; }

  let data = [];
  function renderPreview() {
    preview.innerHTML = data.map((it, i) => {
      const imdb = it.imdbId ? `<span style="color:#2d7d46">${it.imdbId}</span>` : (it.detailDone ? '<span style="color:#c00">无IMDb</span>' : '<span style="color:#999">待</span>');
      const pos = it.posterDone ? '<span style="color:#2d7d46">●海报</span>' : (it.error ? '<span style="color:#c00">✕海报</span>' : '<span style="color:#999">○海报</span>');
      return `<div style="padding:3px 0; border-bottom:1px dotted #eee;">
        ${i + 1}. <b>${it.titleCN}</b> ${it.titleOriginal ? '<span style="color:#888">'+it.titleOriginal+'</span>' : ''} ${it.year} ${pos}
        <div style="color:#666; font-size:11px;">IMDb: ${imdb} ｜ ${it.directorDetail || it.director || '—'} ｜ ${it.genres || ''}</div>
        ${it.error ? `<div style="color:#c00; font-size:11px;">${it.error}</div>` : ''}
      </div>`;
    }).join('');
  }

  async function run() {
    const btn = panel.querySelector('#a-run');
    btn.disabled = true;
    try {
      let state = loadState();

      // 阶段一：建清单（自动探测页数）
      if (!state || !state.items || !state.items.length) {
        statusLine.textContent = '抓第 1 页并探测总页数…';
        const firstUrl = `https://www.douban.com/doulist/${DOULIST_ID}/?start=0&sort=time&playable=0&sub_type=`;
        const firstHtml = await fetchHTML(firstUrl);
        const totalPages = detectTotalPages(firstHtml);
        log('探测到总页数:', totalPages);
        let all = parsePage(firstHtml);
        for (let p = 1; p < totalPages; p++) {
          await sleep(PAGE_DELAY);
          statusLine.textContent = `抓豆列第 ${p + 1}/${totalPages} 页…`;
          const html = await fetchHTML(`https://www.douban.com/doulist/${DOULIST_ID}/?start=${p * PAGE_SIZE}&sort=time&playable=0&sub_type=`);
          all = all.concat(parsePage(html));
        }
        const seen = new Set();
        all = all.filter(i => seen.has(i.subjectId) ? false : (seen.add(i.subjectId), true));
        state = { items: all, totalPages, createdAt: Date.now() };
        saveState(state);
        log(`清单 ${all.length} 部`);
      }
      data = state.items;
      renderPreview();

      // 阶段二：逐部抓详情 + 海报
      for (let k = 0; k < state.items.length; k++) {
        const it = state.items[k];
        if (it.detailDone && it.posterDone) continue;

        const remain = state.items.filter(x => !(x.detailDone && x.posterDone)).length;
        statusLine.innerHTML = `处理 ${k + 1}/${state.items.length}　${it.titleCN}　<span style="color:#888">(剩 ${remain})</span>`;
        it.error = '';

        // 详情页
        if (!it.detailDone) {
          try {
            const html = await fetchHTML(it.detailUrl);
            Object.assign(it, parseDetail(html));
            it.detailDone = true;
          } catch (e) { it.error = '详情:' + e.message; }
          saveState(state); renderPreview();
          await sleep(rand(MIN_DELAY, MAX_DELAY));
        }

        // 海报（XL）
        if (!it.posterDone) {
          try {
            const wallHtml = await fetchHTML(it.photosUrl);
            const poster = parsePosterWall(wallHtml);
            if (!poster) throw new Error('无海报墙');
            const pageHtml = await fetchHTML(poster.photoPageUrl);
            const xlUrl = parseXLUrl(pageHtml);
            if (!xlUrl) throw new Error('无xl链接');
            const fname = sanitize(`${FILE_PREFIX} ${it.titleCN} ${it.year} ${it.subjectId}`) + '.jpg';
            it.posterSize = await downloadImage(xlUrl, fname);
            it.posterDone = true;
            it.photoId = poster.photoId;
          } catch (e) { it.error = (it.error ? it.error + ' / ' : '') + '海报:' + e.message; }
          saveState(state); renderPreview();
        }

        if (k < state.items.length - 1) await sleep(rand(MIN_DELAY, MAX_DELAY));
      }

      const noImdb = state.items.filter(i => i.detailDone && !i.imdbId).length;
      const failPoster = state.items.filter(i => !i.posterDone).length;
      const failDetail = state.items.filter(i => !i.detailDone).length;
      statusLine.innerHTML = `完成 ${state.items.length} 部`
        + (failDetail ? `；<span style="color:#c00">${failDetail} 详情失败</span>` : '')
        + (failPoster ? `；<span style="color:#c00">${failPoster} 海报失败</span>` : '')
        + (noImdb ? `；<span style="color:#e08a00">${noImdb} 无IMDb</span>` : '')
        + '（有失败可再点继续重试）';
      toggleExport(true);
      log('全部处理完毕');
    } catch (e) {
      statusLine.textContent = '出错：' + e.message; log(e);
    } finally { btn.disabled = false; }
  }

  function init() {
    buildPanel();
    const state = loadState();
    if (state && state.items && state.items.length) {
      data = state.items; renderPreview();
      const remain = state.items.filter(x => !(x.detailDone && x.posterDone)).length;
      statusLine.textContent = remain ? `已有清单 ${state.items.length} 部，剩 ${remain} 待处理。点「开始/继续」。` : `已全部完成 ${state.items.length} 部，可导出。`;
      if (!remain) toggleExport(true);
    }
    log('就绪');
  }
  if (document.readyState !== 'loading') init();
  else window.addEventListener('DOMContentLoaded', init);
})();
