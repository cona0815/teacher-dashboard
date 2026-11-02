"""作文批改：整班批次（老師 2026-11-02「拍照上傳要一張一張…一次只能做一人份，有什麼辦法」）
- 一次丟全班照片，或整疊掃描成一個 PDF（自動拆成一頁一頁）；依「每人幾頁」「從座號幾號開始」「空號」自動分份，座號可再改
- 依序排隊批改（一次一份、每份間隔 3 秒；AI 太忙〔HTTP 429〕等 30 秒重試，最多 3 次），老師可以先去做別的事
- 每份「查看」→ 老師改字、勾「老師已確認內容」才算完成（AI 只是草稿）；可合併所有已確認的批改單一起列印／存 PDF
- 單份批改與批次共用 esGradeOne()
python tools/essay_batch.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'esGradeOne' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 抽出「批改一份」 ----------
rep("""    $('esGoButton').addEventListener('click', async () => {
      const text = $('esText').value.trim();
      const esFiles = zoneFiles('esImages');
      const hasImages = esFiles.length > 0;
      if (!text && !hasImages) return showToast('請提供作文（拍照、PDF、貼圖或貼文字）。', true);""",
    """    // 批改一份作文：回傳批改單 HTML 與 AI 結果（單份批改與整班批次共用）
    async function esGradeOne(text, esFiles, seat) {
      const hasImages = esFiles.length > 0;
      if (!text && !hasImages) throw new Error('請提供作文（拍照、PDF、貼圖或貼文字）。');""")
rep("""      if (!document.querySelector('.esOut:checked')) return showToast('「輸出內容」至少要勾一項。', true);""",
    """      if (!document.querySelector('.esOut:checked')) throw new Error('「輸出內容」至少要勾一項。');""")
rep("""      ].filter(Boolean).join('\\n');
      busy($('esGoButton'), true);
      try {
        const imageParts = await filesToParts(esFiles, 0);""", """      ].filter(Boolean).join('\\n');
      {
        const imageParts = await filesToParts(esFiles, 0);""")
rep("""        if (!response.ok) throw new Error(`AI 回應錯誤（HTTP ${response.status}）`);
        const payload = await response.json();
        const resultText = (((payload.candidates || [])[0] || {}).content?.parts || []).map(p => p.text || '').join('');
        const data = extractJson(resultText);
        $('esStatus').textContent = '';""", """        if (!response.ok) { const err = new Error(`AI 回應錯誤（HTTP ${response.status}）`); err.status = response.status; throw err; }
        const payload = await response.json();
        const resultText = (((payload.candidates || [])[0] || {}).content?.parts || []).map(p => p.text || '').join('');
        const data = extractJson(resultText);
        $('esStatus').textContent = '';""")
rep("""        const typoSheet = esOut('typoSheet') ? esTypoSheetHtml(data) : '';""", """        const typoSheet = esOut('typoSheet') ? esTypoSheetHtml(data, seat) : '';""")
rep("""        $('esPreview').innerHTML = `<div class="sheet" style="position:relative">
          ${esOut('score') ? gradeBadge : ''}""", """        const html = `<div class="sheet" style="position:relative">
          ${esOut('score') ? gradeBadge : ''}""")
rep("""<span>座號：${escapeHtml($('esSeat').value.trim() || '＿＿＿')}</span><span>約 ${escapeHtml(String(data.wordCount || '—'))} 字</span>""",
    """<span>座號：${escapeHtml(seat || '＿＿＿')}</span><span>約 ${escapeHtml(String(data.wordCount || '—'))} 字</span>""")
rep("""        </div>${typoSheet}`;
        if (esOut('typoSheet') && !typoSheet) showToast('這篇沒有找到錯字，所以沒有產生訂正單。');
        esOnResult(data, band);
        showToast('✍️ 批改完成，請老師過目！');
      } catch (e) { if (e.message !== 'no-key') { $('esStatus').textContent = ''; showToast(e.message, true); } }
      busy($('esGoButton'), false);
    });""", """        </div>${typoSheet}`;
        return { html, data, band, noTypos: esOut('typoSheet') && !typoSheet };
      }
    }
    $('esGoButton').addEventListener('click', async () => {
      busy($('esGoButton'), true);
      try {
        const r = await esGradeOne($('esText').value.trim(), zoneFiles('esImages'), $('esSeat').value.trim());
        esBatchLeave();
        $('esPreview').innerHTML = r.html;
        if (r.noTypos) showToast('這篇沒有找到錯字，所以沒有產生訂正單。');
        esOnResult(r.data, r.band);
        showToast('✍️ 批改完成，請老師過目！');
      } catch (e) { if (e.message !== 'no-key') { $('esStatus').textContent = ''; showToast(e.message, true); } }
      busy($('esGoButton'), false);
    });""")
rep("""    function esTypoSheetHtml(data) {""", """    function esTypoSheetHtml(data, seat) {""")
rep("""        <div class="ws-meta"><span>題目：${escapeHtml($('esTopic').value.trim() || '＿＿＿＿＿')}</span><span>座號：${escapeHtml($('esSeat').value.trim() || '＿＿＿')}</span><span>共 ${rows.length} 個字</span></div>""",
    """        <div class="ws-meta"><span>題目：${escapeHtml($('esTopic').value.trim() || '＿＿＿＿＿')}</span><span>座號：${escapeHtml(seat || '＿＿＿')}</span><span>共 ${rows.length} 個字</span></div>""")

# ---------- 畫面 ----------
rep("""          <div class="warn">AI 批改是<strong>老師的助手草稿</strong>""", """          <details class="es-batch-box" id="esBatchBox">
            <summary>📚 整班批次批改（一次丟全班的照片或掃描 PDF）</summary>
            <div class="field" style="margin-top:8px"><label>全班作文（照片可以多選；整疊用影印機掃成一個 PDF 也可以，會自動一頁一頁拆開）</label>
              <input class="input" type="file" id="esBatchFiles" accept="image/*,.pdf,application/pdf" multiple></div>
            <div class="check-row" style="align-items:center">
              <label>每人 <select class="select" id="esBatchPer" style="width:auto;margin:0"><option>1</option><option>2</option><option>3</option><option>4</option></select> 頁</label>
              <label>從座號 <input class="input" id="esBatchStart" type="number" min="1" max="60" value="1" style="width:64px"> 開始</label>
              <label>空號 <input class="input" id="esBatchSkip" placeholder="例：5、12" style="width:110px"></label></div>
            <div class="hint">照片依檔名排序（手機照片就是拍照順序），分好後每份的座號都可以再改。請學生只寫座號、不要寫姓名。AI 只是草稿：每一份都要按「查看」核對，勾「老師已確認內容」才算完成。</div>
            <div id="esBatchList"></div>
            <button class="go-button" type="button" id="esBatchGo">▶ 開始批次批改</button>
            <div class="check-row" style="margin-top:6px"><button class="mini" type="button" id="esBatchPrint">🖨 合併已確認的批改單（一起列印／存 PDF）</button></div>
            <div class="status" id="esBatchStatus"></div>
          </details>
          <div class="warn">AI 批改是<strong>老師的助手草稿</strong>""")
rep("""    /* 📒 生詞本 */""", """    /* ✍️ 作文整班批次 */
    .es-batch-box { margin:10px 0; border:1.5px solid var(--line); border-radius:12px; padding:8px 10px; background:#fff; }
    .es-batch-box summary { cursor:pointer; font-weight:900; }
    .es-batch { width:100%; border-collapse:collapse; font-size:13px; margin:8px 0; }
    .es-batch td { border-bottom:1px solid var(--line); padding:4px 4px; vertical-align:middle; }
    .es-batch input { width:54px; padding:3px 6px; }
    .es-batch tr.viewing td { background:#fff6d8; }
    .es-batch .st-fail { color:#b3261e; font-weight:800; }
    .es-batch .st-ok { color:#1f7a52; font-weight:800; }
    /* 📒 生詞本 */""")

# ---------- 批次程式 ----------
rep("""    // ---- 批改單 v2：老師可直接改字；勾「老師已確認」才開放列印、才存進紀錄 ----""", """    // ---- 整班批次批改：一次丟全班照片或掃描 PDF，依座號排隊批改 ----
    const ES_BATCH = { items: [], running: false, stop: false, viewing: -1 };
    const esSleep = ms => new Promise(res => setTimeout(res, ms));
    // 每一頁一個檔案：照片照檔名排序；PDF 用 pdf-lib 拆成單頁
    async function esSplitPages(files) {
      const pages = [];
      const sorted = [...files].sort((a, b) => a.name.localeCompare(b.name, 'zh-Hant', { numeric: true }));
      for (const f of sorted) {
        if (/pdf/i.test(f.type) || /\\.pdf$/i.test(f.name)) {
          const src = await PDFLib.PDFDocument.load(await f.arrayBuffer(), { ignoreEncryption: true });
          for (let i = 0; i < src.getPageCount(); i += 1) {
            const doc = await PDFLib.PDFDocument.create();
            const [page] = await doc.copyPages(src, [i]);
            doc.addPage(page);
            pages.push(new File([await doc.save()], `${f.name} 第${i + 1}頁`, { type: 'application/pdf' }));
          }
        } else pages.push(f);
      }
      return pages;
    }
    async function esBatchPrepare() {
      if (ES_BATCH.running) return;
      const files = [...$('esBatchFiles').files];
      esBatchLeave();
      if (!files.length) { ES_BATCH.items = []; esBatchRender(); return; }
      $('esBatchStatus').textContent = '📄 整理頁面中…';
      let pages;
      try { pages = await esSplitPages(files); } catch (e) { $('esBatchStatus').textContent = ''; return showToast('有檔案打不開（PDF 可能有加密），請重新掃描或改用照片。', true); }
      const per = Number($('esBatchPer').value) || 1;
      const skip = new Set($('esBatchSkip').value.split(/[、,，\\s]+/).map(Number).filter(Boolean));
      let seat = Math.max(1, Number($('esBatchStart').value) || 1);
      const items = [];
      for (let i = 0; i < pages.length; i += per) {
        while (skip.has(seat)) seat += 1;
        items.push({ seat: String(seat), files: pages.slice(i, i + per), status: 'wait', html: '', data: null, band: '', rec: null, error: '' });
        seat += 1;
      }
      ES_BATCH.items = items;
      $('esBatchStatus').textContent = `共 ${pages.length} 頁，分成 ${items.length} 份。座號不對可以直接改。`;
      esBatchRender();
    }
    ['esBatchFiles', 'esBatchPer', 'esBatchStart', 'esBatchSkip'].forEach(id => $(id).addEventListener('change', esBatchPrepare));
    const ES_BATCH_LABEL = { wait: '⏳ 等待中', run: '🤖 批改中…', done: '🟡 待核對', ok: '✔ 已確認', fail: '⚠ 失敗' };
    function esBatchRender() {
      const items = ES_BATCH.items;
      if (!items.length) { $('esBatchList').innerHTML = ''; return; }
      const count = k => items.filter(x => x.status === k).length;
      $('esBatchList').innerHTML = `<table class="es-batch">${items.map((x, i) => `<tr class="${i === ES_BATCH.viewing ? 'viewing' : ''}">
          <td>座號 <input class="input es-bseat" data-i="${i}" value="${escapeHtml(x.seat)}"${x.status === 'run' ? ' disabled' : ''}></td>
          <td title="${escapeHtml(x.files.map(f => f.name).join('、'))}">${x.files.length} 頁</td>
          <td class="${x.status === 'fail' ? 'st-fail' : x.status === 'ok' ? 'st-ok' : ''}" title="${escapeHtml(x.error)}">${ES_BATCH_LABEL[x.status]}</td>
          <td style="text-align:right">${x.status === 'done' || x.status === 'ok' ? `<button class="mini" type="button" data-view="${i}">查看</button>` : x.status === 'fail' ? `<button class="mini" type="button" data-retry="${i}">重試</button>` : ''}</td></tr>`).join('')}</table>
        <div class="hint">完成 ${count('done') + count('ok')}／${items.length} 份（已確認 ${count('ok')}）${count('fail') ? `，⚠ 失敗 ${count('fail')} 份` : ''}</div>`;
    }
    $('esBatchList').addEventListener('input', e => {
      const box = e.target.closest('.es-bseat');
      if (box) ES_BATCH.items[Number(box.dataset.i)].seat = box.value.trim();
    });
    $('esBatchList').addEventListener('click', e => {
      const view = e.target.closest('[data-view]'), retry = e.target.closest('[data-retry]');
      if (view) esBatchView(Number(view.dataset.view));
      if (retry) { ES_BATCH.items[Number(retry.dataset.retry)].status = 'wait'; esBatchRender(); if (!ES_BATCH.running) esBatchRun(); }
    });
    // 離開正在看的那一份：把老師改過的批改單存回去
    function esBatchLeave() {
      const item = ES_BATCH.items[ES_BATCH.viewing];
      if (item && item.rec && esCurrent === item.rec) item.html = $('esPreview').innerHTML;
      ES_BATCH.viewing = -1;
    }
    function esBatchView(i) {
      esBatchLeave();
      const item = ES_BATCH.items[i];
      $('esSeat').value = item.seat;
      $('esPreview').innerHTML = item.html;
      if (item.rec) {
        esCurrent = item.rec;
        esCurrent.seat = item.seat;
        $('esConfirmLabel').hidden = false;
        $('esParentButton').hidden = false;
        esSetConfirmed(item.status === 'ok');
      } else {
        esOnResult(item.data, item.band);
        item.rec = esCurrent;
      }
      ES_BATCH.viewing = i;
      esBatchRender();
      $('esPreview').scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
    $('esConfirm').addEventListener('change', () => {
      const item = ES_BATCH.items[ES_BATCH.viewing];
      if (!item || esCurrent !== item.rec) return;
      item.status = $('esConfirm').checked ? 'ok' : 'done';
      item.html = $('esPreview').innerHTML;
      esBatchRender();
    });
    async function esBatchRun() {
      if (ES_BATCH.running) { ES_BATCH.stop = true; $('esBatchGo').textContent = '⏳ 這份做完就停…'; return; }
      if (!geminiKey()) return showToast('尚未設定 Gemini 金鑰，請先到工作台 AI 設定填入。', true);
      if (!ES_BATCH.items.some(x => x.status === 'wait' || x.status === 'fail')) return showToast(ES_BATCH.items.length ? '全部都批改好了。' : '請先選全班的作文照片或 PDF。', true);
      ES_BATCH.running = true; ES_BATCH.stop = false;
      $('esBatchGo').textContent = '⏸ 停止（這份做完就停）';
      if (esOut('typoSheet')) await vbLoadData().catch(() => null);
      for (const item of ES_BATCH.items) {
        if (ES_BATCH.stop) break;
        if (item.status !== 'wait' && item.status !== 'fail') continue;
        item.status = 'run'; esBatchRender();
        $('esBatchStatus').textContent = `🤖 正在批改座號 ${item.seat}…（可以先去做別的事，這個分頁不要關）`;
        for (let attempt = 0; ; attempt += 1) {
          try {
            const r = await esGradeOne('', item.files, item.seat);
            Object.assign(item, { status: 'done', html: r.html, data: r.data, band: r.band, rec: null, error: '' });
            break;
          } catch (e) {
            if (e.message === 'no-key') { item.status = 'wait'; ES_BATCH.stop = true; break; }
            if (e.status === 429 && attempt < 3) { $('esBatchStatus').textContent = '⏳ AI 這一分鐘太忙了，30 秒後自動再試…'; await esSleep(30000); continue; }
            Object.assign(item, { status: 'fail', error: e.message || '批改失敗' });
            break;
          }
        }
        esBatchRender();
        await esSleep(3000);   // 免費額度每分鐘有次數限制，一份一份慢慢送
      }
      ES_BATCH.running = false;
      $('esBatchGo').textContent = '▶ 開始批次批改';
      const done = ES_BATCH.items.filter(x => x.status === 'done' || x.status === 'ok').length, fail = ES_BATCH.items.filter(x => x.status === 'fail').length;
      $('esBatchStatus').textContent = `完成 ${done} 份${fail ? `、失敗 ${fail} 份（可以按「重試」）` : ''}。請逐份按「查看」核對。`;
      showToast(`整班批改：完成 ${done} 份${fail ? `、失敗 ${fail} 份` : ''}。`, !!fail);
    }
    $('esBatchGo').addEventListener('click', esBatchRun);
    $('esBatchPrint').addEventListener('click', () => {
      esBatchLeave();
      const ok = ES_BATCH.items.filter(x => x.status === 'ok');
      if (!ok.length) return showToast('還沒有「已確認」的批改單：請先按「查看」核對並勾「老師已確認內容」。', true);
      $('esPreview').innerHTML = ok.map(x => x.html).join('');
      $('esPreview').querySelectorAll('[contenteditable]').forEach(n => n.removeAttribute('contenteditable'));
      esCurrent = null;
      esSetConfirmed(true);
      esBatchRender();
      showToast(`已把 ${ok.length} 份已確認的批改單放進預覽，按「列印批改單」或「PDF」。`);
    });

    // ---- 批改單 v2：老師可直接改字；勾「老師已確認」才開放列印、才存進紀錄 ----""")

path.write_text(s, encoding='utf-8')
print('ok')
