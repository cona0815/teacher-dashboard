"""教材小工場「🗂 行政文書」分頁群（2026-11-01 升級規格書・組 B：G1–G6）
- G1 📑 成果報告：壹依據／貳目的／參辦理情形／肆參與人次（留空給老師填）／伍成效與檢討／陸活動照片（2×2）
- G2 📋 計畫書：五種類型；流程表、工作分配表、經費概算表（金額留空）；校外教學自動加安全段落
- G3 🗒 會議紀錄：錄音檔／逐字稿／白板照片三選一；待辦表（事項、負責、期限）可一鍵複製
- G4 📘 教案與觀議課：108 課綱教案（代碼請核對）、可套學校欄位；觀課 bullet 擴寫成表、議課紀錄
- G5 📅 教學進度表：不用 AI 也能用（手動單元清單→平均分配到有效週次）、可拖調、匯出 Excel
- G6 🧳 代課包：導師版／科任版（可列多班）；不設任何個別學生欄位
共同：預覽區可直接改字；勾「老師已核對」後，文件底部才出現「AI 協助草擬，內容已由老師核對」。
AI 一律繁體中文、臺灣公文慣用語、只回 JSON、不寫學生姓名、不猜數字。

python tools/upgrade_studio_docs_2026_11.py   （可重複執行：已套用的步驟會跳過）
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Studio.html'
s = path.read_text(encoding='utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)


CSS_ANCHOR = '''    @media print {
      body { background:#fff; }'''
HTML_ANCHOR = '''    </section>
  </main>'''
JS_ANCHOR = '''  </script>
  <script src="assets/version.js"></script>'''


def add_css(css):
    rep(CSS_ANCHOR, css + CSS_ANCHOR)


def add_html(html):
    # 早期版本 G1 少了 </section>：遇到就先補上
    if '      </div>\n  </main>' in s:
        rep('      </div>\n  </main>', '      </div>\n    </section>\n  </main>')
    rep(HTML_ANCHOR, '''    </section>
''' + html + '''    </section>
  </main>''')


def add_js(js):
    rep(JS_ANCHOR, js + JS_ANCHOR)


# =====================================================================
# G1：共用骨架＋📑 成果報告
# =====================================================================
def g1():
    # 分頁群與第一個分頁
    rep('''    <button class="tab-button" type="button" data-page="cm" hidden>💬 評語小幫手</button>''',
        '''    <button class="tab-button" type="button" data-page="cm" hidden>💬 評語小幫手</button>
    <span class="tab-group">🗂 行政文書</span>
    <button class="tab-button" type="button" data-page="report">📑 成果報告</button>''')

    # callGemini：imagePart 可以是陣列（多張照片／錄音＋照片）
    rep('''      if (imagePart) parts.push(imagePart);''',
        '''      if (Array.isArray(imagePart)) parts.push(...imagePart); else if (imagePart) parts.push(imagePart);''')

    # downloadPreview：匯出 Word／Excel 時拿掉畫面專用標記（例如未勾核對時的署名、已核對後的「請核對」）
    rep('''      const css = document.querySelector('style').textContent;
      const mime = format === 'xls' ? 'application/vnd.ms-excel' : 'application/msword';''',
        '''      const css = document.querySelector('style').textContent;
      const clone = host.cloneNode(true);
      clone.querySelectorAll('[data-export-hide="1"]').forEach(node => node.remove());
      clone.querySelectorAll('[contenteditable]').forEach(node => node.removeAttribute('contenteditable'));
      const mime = format === 'xls' ? 'application/vnd.ms-excel' : 'application/msword';''')
    rep('''.sheet{box-shadow:none;margin:0 auto;width:auto;min-height:0}</style></head><body>${host.innerHTML}</body></html>`;''',
        '''.sheet{box-shadow:none;margin:0 auto;width:auto;min-height:0}</style></head><body>${clone.innerHTML}</body></html>`;''')

    add_css('''    /* 🗂 行政文書（成果報告／計畫書／會議紀錄／教案／進度表／代課包） */
    .doc-sheet .ws-title { font-size:22px; }
    .doc-sheet[contenteditable="true"]:focus { outline:2px dashed #e0a21a; outline-offset:2px; }
    .doc-h { font-size:16.5px; font-weight:900; margin:14px 0 4px; }
    .doc-body { padding-left:1em; font-size:15px; }
    .doc-sub { font-weight:800; margin:6px 0 2px; }
    .doc-li { display:flex; gap:2px; margin:2px 0; }
    .doc-no { flex:0 0 auto; }
    .doc-table { width:100%; border-collapse:collapse; table-layout:fixed; margin:4px 0 8px; font-size:14px; }
    .doc-table th, .doc-table td { border:1px solid #333; padding:4px 6px; vertical-align:top; word-break:break-word; overflow-wrap:anywhere; }
    .doc-table th { background:#f0f0f0; font-weight:900; text-align:center; }
    .doc-table tr, .doc-photo-table tr { page-break-inside:avoid; break-inside:avoid; }
    .doc-photo-table { width:100%; border-collapse:collapse; table-layout:fixed; margin-top:6px; }
    .doc-photo-cell { width:50%; border:1px solid #333; padding:6px; vertical-align:top; text-align:center; }
    .doc-photo { display:block; width:100%; height:210px; object-fit:cover; }
    .doc-photo-empty { display:flex; align-items:center; justify-content:center; border:1.5px dashed #999; color:#888; font-size:13px; }
    .doc-photo-cap { font-size:13.5px; margin-top:4px; text-align:left; min-height:2em; }
    .doc-verify { color:#b25b00; font-size:12px; font-weight:700; }
    .doc-note { font-size:12.5px; color:#555; }
    .doc-ai-sign { margin-top:22px; padding-top:4px; border-top:1px solid #999; text-align:right; font-size:12px; color:#444; }
''')

    add_html('''
    <!-- 🗂 行政文書：📑 成果報告（G1） -->
    <section class="page" id="page-report">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="rpSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>活動名稱</label>
            <input class="input" id="rpName" placeholder="例：115 學年度閱讀推廣週"></div>
          <div class="field"><label>活動日期</label>
            <input class="input" id="rpDate" placeholder="例：115 年 10 月 15 日（星期三）"></div>
          <div class="field"><label>參加對象</label>
            <input class="input" id="rpTarget" placeholder="例：本校三至六年級學生"></div>
          <div class="field"><label>辦理單位</label>
            <input class="input" id="rpUnit" placeholder="例：教務處設備組"></div>
          <div class="field"><label>活動計畫（貼文字，或上傳計畫檔照片／PDF）</label>
            <textarea class="textarea" id="rpPlan" placeholder="貼上計畫的依據、目的、流程都可以"></textarea>
            <input class="input" type="file" id="rpPlanFiles" accept="image/*,.pdf,application/pdf" multiple style="margin-top:6px"></div>
          <div class="field"><label>執行狀況（幾句話就好）</label>
            <textarea class="textarea" id="rpExec" placeholder="例：分三個關卡進行，學生反應熱烈；下雨改到禮堂，動線有點擠。"></textarea></div>
          <div class="field"><label>活動照片（可多張，4 張剛好排滿 2×2；請避開學生正臉與名牌）</label>
            <input class="input" type="file" id="rpPhotos" accept="image/*" multiple></div>
          <button class="go-button" type="button" id="rpGoButton">🤖 產生成果報告</button>
          <div class="status" id="rpStatus"></div>
          <div class="hint">AI 依計畫與照片草擬六段成果報告。<strong>參與人次、金額等數字 AI 不會猜</strong>，表格留空給你填；照片說明是 AI 看圖寫的，會標「請核對」。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="rpCheckedLabel"><input type="checkbox" id="rpChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('rpPreview','成果報告','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('rpPreview','成果報告',false)">⬇ PDF</button>
            <span class="status" id="rpMeta">🟡 AI 草稿，請核對後再交出；預覽區可以直接點字修改。</span>
          </div>
          <div class="preview-host" id="rpPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 🗂 行政文書（2026-11 升級・組 B）：共用工具
    // ============================================================
    const DOC_SCHOOL_KEY = 'studioDocSchool';
    const DOC_UPPER = ['壹', '貳', '參', '肆', '伍', '陸', '柒', '捌', '玖', '拾', '拾壹', '拾貳'];
    const DOC_CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十'];
    const DOC_AI_RULES = [
      '寫作規範：一律使用繁體中文與臺灣學校公文慣用語（例：依據、辦理、實施、預期效益、請鑒核），語氣正式、精簡、條列清楚。',
      '不得出現任何學生姓名：提到學生一律寫「學生」「本班學生」「參與學生」等代稱；人員以職稱稱呼（例：教務主任、導師、承辦人），除非老師輸入裡已寫出教師姓名。',
      '不要猜任何數字：人次、人數、金額、經費、分數，老師沒有提供就留空字串 ""，絕對不要自己編。',
      '只回傳 JSON，不要加任何說明文字或 Markdown。'
    ].join('\n');
    function docCn(i) { return DOC_CN[i] || String(i + 1); }
    function docArr(v) {
      const list = Array.isArray(v) ? v : (v == null || v === '' ? [] : [v]);
      return list.filter(x => x != null && (typeof x === 'object' || String(x).trim() !== ''));
    }
    function docText(v) { return escapeHtml(v == null ? '' : String(v)).replace(/\n/g, '<br>'); }
    function docItems(list, style) {
      const items = docArr(list);
      const no = i => style === 'paren' ? `（${docCn(i)}）` : `${docCn(i)}、`;
      if (!items.length) return `<div class="doc-li"><span class="doc-no">${no(0)}</span><span>＿＿＿＿＿＿＿＿</span></div>`;
      return items.map((t, i) => `<div class="doc-li"><span class="doc-no">${no(i)}</span><span>${docText(typeof t === 'object' ? (t.text || t.content || JSON.stringify(t)) : t)}</span></div>`).join('');
    }
    function docSection(index, title, body) {
      return `<div class="doc-h">${DOC_UPPER[index]}、${escapeHtml(title)}</div><div class="doc-body">${body}</div>`;
    }
    // headers: [{ label, width }]；rows: 文字陣列（自動跳脫）；minRows：不足補空白列
    function docTable(headers, rows, minRows, cls) {
      const body = (rows || []).map(r => `<tr>${headers.map((h, i) => `<td>${docText(r[i]) || '&nbsp;'}</td>`).join('')}</tr>`);
      while (body.length < (minRows || 0)) body.push(`<tr>${headers.map(() => '<td>&nbsp;</td>').join('')}</tr>`);
      return `<table class="doc-table${cls ? ' ' + cls : ''}"><colgroup>${headers.map(h => `<col${h.width ? ` style="width:${h.width}"` : ''}>`).join('')}</colgroup>
        <tr>${headers.map(h => `<th>${escapeHtml(h.label)}</th>`).join('')}</tr>${body.join('')}</table>`;
    }
    function docHead(title, school, meta) {
      return `<div class="ws-head"><div class="ws-school">${escapeHtml(school || '＿＿＿＿＿＿國民小學')}</div><div class="ws-title">${escapeHtml(title)}</div></div>`
        + (meta && meta.length ? `<div class="ws-meta" style="flex-wrap:wrap;gap:4px 18px">${meta.map(m => `<span>${m}</span>`).join('')}</div>` : '');
    }
    function docSchool(id) {
      const v = ($(id).value || '').trim();
      if (v) { try { localStorage.setItem(DOC_SCHOOL_KEY, v); } catch (e) {} }
      return v;
    }
    document.querySelectorAll('.docSchool').forEach(input => {
      try { input.value = localStorage.getItem(DOC_SCHOOL_KEY) || ''; } catch (e) {}
      input.addEventListener('change', () => {
        document.querySelectorAll('.docSchool').forEach(other => { if (other !== input) other.value = input.value; });
        docSchool(input.id);
      });
    });
    // 把文件放進預覽區：整張可直接改字；底部署名要等老師勾「已核對」才出現
    function docRender(prefix, html, withSign) {
      const host = $(prefix + 'Preview');
      host.innerHTML = `<div class="sheet doc-sheet" contenteditable="true" spellcheck="false">${html}${withSign === false ? '' : '<div class="doc-ai-sign" contenteditable="false">AI 協助草擬，內容已由老師核對</div>'}</div>`;
      const cb = $(prefix + 'Checked');
      if (cb) cb.checked = false;
      docApplyConfirm(prefix);
    }
    function docApplyConfirm(prefix) {
      const cb = $(prefix + 'Checked');
      const on = !!(cb && cb.checked);
      const host = $(prefix + 'Preview');
      host.querySelectorAll('.doc-ai-sign').forEach(node => { node.style.display = on ? '' : 'none'; node.dataset.exportHide = on ? '0' : '1'; });
      host.querySelectorAll('.doc-verify').forEach(node => { node.style.display = on ? 'none' : ''; node.dataset.exportHide = on ? '1' : '0'; });
      const label = $(prefix + 'CheckedLabel');
      if (label) label.classList.toggle('ok', on);
    }
    function docBindConfirm(prefix) {
      const cb = $(prefix + 'Checked');
      cb.addEventListener('change', () => {
        if (!$(prefix + 'Preview').innerHTML.trim()) { cb.checked = false; return showToast('請先產生文件，再勾「老師已核對」。', true); }
        docApplyConfirm(prefix);
        if (cb.checked) showToast('已標示「AI 協助草擬，內容已由老師核對」，列印與下載都會帶這行。');
      });
    }
    // 共用 AI 呼叫：按鈕一定復原；沒金鑰時 callGemini 會 toast
    async function docAi(button, statusEl, prompt, partsFn) {
      busy(button, true);
      try {
        const parts = partsFn ? await partsFn() : [];
        const text = await callGemini(prompt, parts.length ? parts : null, statusEl);
        return extractJson(text);
      } catch (e) {
        statusEl.textContent = '';
        if (e.message !== 'no-key') showToast(e.message || String(e), true);
        return null;
      } finally { busy(button, false); }
    }
    // 照片放進文件用：縮到長邊 1000px 的 JPEG data URL（列印、PDF、Word 都帶得走）
    async function docImageUrl(file) {
      try {
        const bitmap = await createImageBitmap(file);
        const scale = Math.min(1, 1000 / Math.max(bitmap.width, bitmap.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(bitmap.width * scale);
        canvas.height = Math.round(bitmap.height * scale);
        canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/jpeg', 0.85);
      } catch (e) {
        return await new Promise(resolve => { const r = new FileReader(); r.onload = () => resolve(String(r.result)); r.onerror = () => resolve(''); r.readAsDataURL(file); });
      }
    }
    // 照片 2×2：用表格排（Word 也不跑版）；沒照片就留 4 格空框
    function docPhotoTable(urls, captions) {
      const caps = Array.isArray(captions) ? captions : [];
      const count = urls.length || 4;
      const cells = [];
      for (let i = 0; i < count; i += 1) {
        const url = urls[i];
        const cap = caps[i] ? String(caps[i]) : '';
        cells.push(`<td class="doc-photo-cell">${url
          ? `<img class="doc-photo" src="${url}" alt="活動照片 ${i + 1}" width="300">`
          : `<div class="doc-photo doc-photo-empty">照片 ${i + 1}（可在這裡貼上照片）</div>`}
          <div class="doc-photo-cap">${cap ? `${docText(cap)}<span class="doc-verify">（AI 看圖寫的說明，請核對）</span>` : '說明：＿＿＿＿＿＿＿＿＿＿'}</div></td>`);
      }
      if (cells.length % 2) cells.push('<td class="doc-photo-cell"></td>');
      const rows = [];
      for (let i = 0; i < cells.length; i += 2) rows.push(`<tr>${cells[i]}${cells[i + 1]}</tr>`);
      return `<table class="doc-photo-table">${rows.join('')}</table>`;
    }

    // ============================================================
    // 📑 成果報告（G1）
    // ============================================================
    $('rpGoButton').dataset.label = $('rpGoButton').textContent;
    attachZone('rpPlanFiles', { multiple: true });
    attachZone('rpPhotos', { multiple: true });
    docBindConfirm('rp');
    $('rpGoButton').addEventListener('click', async () => {
      const name = $('rpName').value.trim();
      if (!name) return showToast('請先填活動名稱。', true);
      const plan = $('rpPlan').value.trim();
      const exec = $('rpExec').value.trim();
      const planFiles = zoneFiles('rpPlanFiles');
      const photos = zoneFiles('rpPhotos').filter(f => (f.type || '').startsWith('image/')).slice(0, 12);
      if (!plan && !planFiles.length && !exec) return showToast('請貼活動計畫、上傳計畫檔照片，或寫幾句執行狀況。', true);
      const date = $('rpDate').value.trim();
      const target = $('rpTarget').value.trim();
      const unit = $('rpUnit').value.trim();
      const prompt = [
        '你是臺灣國小的資深行政教師，要替同事草擬一份「活動成果報告」。',
        DOC_AI_RULES,
        `活動名稱：${name}`,
        `活動日期：${date || '（未提供）'}；參加對象：${target || '（未提供）'}；辦理單位：${unit || '（未提供）'}`,
        plan ? `活動計畫內容：\n${plan}` : '',
        planFiles.length ? `附件的前 ${planFiles.length} 份是活動計畫檔（照片或 PDF），請從中讀出依據、目的與流程。` : '',
        exec ? `執行狀況（老師口述）：${exec}` : '',
        photos.length
          ? `接著附上的 ${photos.length} 張是活動照片（依序第 1 到第 ${photos.length} 張）。photoCaptions 請依序每張寫一句 15–30 字的說明，只描述照片裡看得到的事，不寫學生姓名、不寫班級座號。`
          : '這次沒有附活動照片，photoCaptions 回傳空陣列 []。',
        '各欄要求：basis 依據 1–3 條（資料沒寫就寫通用依據，例如「本校○○學年度校務發展計畫」）；purpose 目的 2–4 條；execution 的 time、place、target 盡量從資料抓，抓不到留空；flow 為活動流程（time、item），沒有時間就留空字串；outcomes 成效恰好 3 條；reviews 檢討恰好 2 條；improvements 改進建議 1–3 條。參與人次不要寫，由老師自己填。',
        '回傳格式：{"basis":[""],"purpose":[""],"execution":{"time":"","place":"","target":"","flow":[{"time":"","item":""}]},"outcomes":["","",""],"reviews":["",""],"improvements":[""],"photoCaptions":[""]}'
      ].filter(Boolean).join('\n');
      const data = await docAi($('rpGoButton'), $('rpStatus'), prompt, async () => [...await filesToParts(planFiles, 6), ...await filesToParts(photos, 12)]);
      if (!data) return;
      const photoUrls = (await Promise.all(photos.map(docImageUrl))).filter(Boolean);
      const ex = data.execution || {};
      const flowRows = docArr(ex.flow).map(r => typeof r === 'object' ? [r.time || '', r.item || r.content || ''] : ['', r]);
      const school = docSchool('rpSchool');
      const html = docHead(`${name}成果報告`, school, [`辦理單位：${escapeHtml(unit || '＿＿＿＿')}`, `活動日期：${escapeHtml(date || ex.time || '＿＿＿＿')}`])
        + docSection(0, '依據', docItems(data.basis))
        + docSection(1, '目的', docItems(data.purpose))
        + docSection(2, '辦理情形',
          `<div class="doc-li"><span class="doc-no">一、</span><span>時間：${docText(ex.time || date) || '＿＿＿＿＿＿'}</span></div>`
          + `<div class="doc-li"><span class="doc-no">二、</span><span>地點：${docText(ex.place) || '＿＿＿＿＿＿'}</span></div>`
          + `<div class="doc-li"><span class="doc-no">三、</span><span>對象：${docText(ex.target || target) || '＿＿＿＿＿＿'}</span></div>`
          + `<div class="doc-li"><span class="doc-no">四、</span><span>活動流程：</span></div>`
          + docTable([{ label: '時間', width: '28%' }, { label: '活動內容' }], flowRows, 3))
        + docSection(3, '參與人次',
          docTable([{ label: '參與對象', width: '40%' }, { label: '人次' }], [['學生', ''], ['教職員', ''], ['家長及來賓', ''], ['合計', '']], 0, 'doc-count-table')
          + '<div class="doc-note doc-verify">（人次請承辦老師依簽到表填寫，AI 不代填數字）</div>')
        + docSection(4, '成效與檢討',
          `<div class="doc-sub">一、成效</div>${docItems(docArr(data.outcomes).slice(0, 3), 'paren')}`
          + `<div class="doc-sub">二、檢討</div>${docItems(docArr(data.reviews).slice(0, 2), 'paren')}`
          + `<div class="doc-sub">三、改進建議</div>${docItems(data.improvements, 'paren')}`)
        + docSection(5, '活動照片', docPhotoTable(photoUrls, data.photoCaptions));
      docRender('rp', html);
      $('rpMeta').textContent = `🟡 AI 草稿（${photoUrls.length ? photoUrls.length + ' 張照片' : '未附照片，留 4 格空框'}），請核對後再勾「老師已核對」。`;
      showToast('📑 成果報告草稿完成，請過目。');
    });
''')


# =====================================================================
# G2：📋 計畫書
# =====================================================================
def g2():
    rep('''    <button class="tab-button" type="button" data-page="report">📑 成果報告</button>''',
        '''    <button class="tab-button" type="button" data-page="report">📑 成果報告</button>
    <button class="tab-button" type="button" data-page="plan">📋 計畫書</button>''')

    add_html('''
    <!-- 🗂 行政文書：📋 計畫書（G2） -->
    <section class="page" id="page-plan">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="plSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>計畫類型</label>
            <select class="select" id="plType">
              <option value="校內活動">校內活動</option>
              <option value="社團">社團</option>
              <option value="教師研習">教師研習</option>
              <option value="校外教學">校外教學</option>
              <option value="競賽">競賽</option>
            </select></div>
          <div class="field"><label>計畫名稱</label>
            <input class="input" id="plName" placeholder="例：115 學年度五年級校外教學"></div>
          <div class="field"><label>對象</label>
            <input class="input" id="plTarget" placeholder="例：五年級學生及隨隊教師"></div>
          <div class="field"><label>日期</label>
            <input class="input" id="plDate" placeholder="例：115 年 11 月 20 日（星期五）"></div>
          <div class="field"><label>地點</label>
            <input class="input" id="plPlace" placeholder="例：國立自然科學博物館"></div>
          <div class="field"><label>主辦／協辦單位（選填）</label>
            <input class="input" id="plUnit" placeholder="例：教務處；協辦：學務處、五年級學年"></div>
          <div class="field"><label>幾句想法</label>
            <textarea class="textarea" id="plIdea" placeholder="例：想結合自然課的生物單元，上午看展、下午做學習單，搭遊覽車。"></textarea></div>
          <div class="field"><label>經費</label>
            <select class="select" id="plBudget"><option value="有">有經費（列概算表，金額留空）</option><option value="無">無經費</option></select></div>
          <button class="go-button" type="button" id="plGoButton">🤖 產生計畫書</button>
          <div class="status" id="plStatus"></div>
          <div class="hint">輸出十段：依據、目的、辦理單位、對象、時間地點、活動流程表、工作分配表、經費概算表、預期效益、注意事項。<strong>經費表 AI 只列項目與單位，單價、金額留空</strong>；校外教學會自動加上安全須知、保險與家長同意書。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="plCheckedLabel"><input type="checkbox" id="plChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('plPreview','計畫書','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('plPreview','計畫書',false)">⬇ PDF</button>
            <span class="status" id="plMeta">🟡 AI 草稿，請核對後再交出；預覽區可以直接點字修改。</span>
          </div>
          <div class="preview-host" id="plPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 📋 計畫書（G2）
    // ============================================================
    const PL_TYPE_HINTS = {
      '校內活動': '一般校內活動：寫清楚活動方式、場地與宣導方式。',
      '社團': '社團計畫：寫出社團目標、招生方式（不寫學生名單）、上課時間與次數、課程規劃、成果發表方式。',
      '教師研習': '教師研習：寫出研習主題、講師（只寫職稱或「外聘講師」，姓名留給老師填）、研習時數登錄與簽到方式。',
      '校外教學': '校外教學：寫出交通方式、行程路線、分組與隨隊人員配置、雨天備案；safety 再列 2–4 條和這次行程有關的安全提醒。',
      '競賽': '競賽：寫出參賽資格、報名方式、比賽方式、評分標準、獎勵方式（獎品金額不要寫）。'
    };
    // 校外教學固定加上的安全段落（不靠 AI，確保一定有）
    const PL_TRIP_SAFETY = [
      '出發前實施行前安全教育，說明集合時間、地點、分組方式與緊急聯絡方式。',
      '依參加人數安排隨隊教師與志工，採分組管理；上下車及每次集合皆清點人數。',
      '租用遊覽車應查驗車齡、保險與駕駛資格，並於出發前實施車上逃生演練。',
      '備妥急救用品與緊急聯絡電話；學生健康狀況由導師事先掌握，不列入本計畫。'
    ];
    const PL_TRIP_INSURANCE = '參加學生及隨隊人員一律投保旅行平安保險（含意外醫療），保額與費用依學校規定辦理。';
    const PL_TRIP_CONSENT = '出發前發放家長同意書，請家長簽名後於期限內繳回；未繳回者不參加，由學校另行安排留校課程。';
    $('plGoButton').dataset.label = $('plGoButton').textContent;
    docBindConfirm('pl');
    $('plGoButton').addEventListener('click', async () => {
      const type = $('plType').value;
      const name = $('plName').value.trim();
      if (!name) return showToast('請先填計畫名稱。', true);
      const target = $('plTarget').value.trim();
      const date = $('plDate').value.trim();
      const place = $('plPlace').value.trim();
      const unit = $('plUnit').value.trim();
      const idea = $('plIdea').value.trim();
      const hasBudget = $('plBudget').value === '有';
      const isTrip = type === '校外教學';
      const prompt = [
        `你是臺灣國小的資深行政教師，要草擬一份「${type}」類型的活動計畫書。`,
        DOC_AI_RULES,
        `計畫名稱：${name}`,
        `對象：${target || '（未提供）'}；日期：${date || '（未提供）'}；地點：${place || '（未提供）'}；主辦／協辦：${unit || '（未提供，請依類型寫常見的處室）'}`,
        idea ? `承辦老師的想法：${idea}` : '',
        PL_TYPE_HINTS[type] || '',
        '各欄要求：basis 依據 1–3 條；purpose 目的 2–4 條；units.host 主辦單位、units.co 協辦單位；flow 活動流程 4–8 列（time 時間、content 內容、owner 負責單位或職稱），時間沒提供可寫「第一節」「上午」這類相對時間；duties 工作分配 3–6 列（task 工作項目、owner 負責人員職稱、detail 工作內容）；benefits 預期效益 2–4 條；notes 注意事項 2–4 條。',
        hasBudget
          ? 'budget 經費概算 3–6 列：只寫 item 項目、unit 單位（例：式、人、本、輛）、note 備註；qty 數量只有老師上面明確寫出時才填，否則留空字串；不要寫單價與金額。'
          : '本計畫無經費，budget 回傳空陣列 []。',
        isTrip ? 'safety：2–4 條針對這次行程的安全提醒（保險與家長同意書系統會自動加，不用寫）。' : 'safety 回傳空陣列 []。',
        '回傳格式：{"basis":[""],"purpose":[""],"units":{"host":"","co":""},"flow":[{"time":"","content":"","owner":""}],"duties":[{"task":"","owner":"","detail":""}],"budget":[{"item":"","unit":"","qty":"","note":""}],"benefits":[""],"notes":[""],"safety":[""]}'
      ].filter(Boolean).join('\n');
      const data = await docAi($('plGoButton'), $('plStatus'), prompt);
      if (!data) return;
      const units = data.units || {};
      const flowRows = docArr(data.flow).map(r => [r.time || '', r.content || r.item || '', r.owner || '']);
      const dutyRows = docArr(data.duties).map(r => [r.task || '', r.owner || '', r.detail || '']);
      const budgetRows = hasBudget ? docArr(data.budget).map(r => [r.item || '', r.unit || '', r.qty || '', '', '', r.note || '']) : [['本計畫無經費需求', '', '', '', '', '']];
      if (hasBudget) budgetRows.push(['合計', '', '', '', '', '']);
      const budgetHtml = docTable([{ label: '項目', width: '26%' }, { label: '單位', width: '10%' }, { label: '數量', width: '10%' }, { label: '單價（元）', width: '13%' }, { label: '金額（元）', width: '13%' }, { label: '備註' }], budgetRows, 0, 'doc-budget-table')
        + (hasBudget ? '<div class="doc-note doc-verify">（數量、單價、金額請依學校經費核算後填寫，AI 不代填）</div>' : '');
      const notesHtml = isTrip
        ? `<div class="doc-sub doc-trip-safety">一、安全須知</div>${docItems([...PL_TRIP_SAFETY, ...docArr(data.safety)], 'paren')}`
          + `<div class="doc-sub">二、保險</div><div class="doc-li"><span>${PL_TRIP_INSURANCE}</span></div>`
          + `<div class="doc-sub">三、家長同意書</div><div class="doc-li"><span>${PL_TRIP_CONSENT}</span></div>`
          + `<div class="doc-sub">四、其他注意事項</div>${docItems(data.notes, 'paren')}`
        : docItems(data.notes);
      const school = docSchool('plSchool');
      const html = docHead(`${name}計畫`, school, [`類型：${escapeHtml(type)}`])
        + docSection(0, '依據', docItems(data.basis))
        + docSection(1, '目的', docItems(data.purpose))
        + docSection(2, '辦理單位',
          `<div class="doc-li"><span class="doc-no">一、</span><span>主辦單位：${docText(units.host) || '＿＿＿＿＿＿'}</span></div>`
          + `<div class="doc-li"><span class="doc-no">二、</span><span>協辦單位：${docText(units.co) || '＿＿＿＿＿＿'}</span></div>`)
        + docSection(3, '對象', `<div class="doc-li"><span>${docText(target) || '＿＿＿＿＿＿'}</span></div>`)
        + docSection(4, '時間地點',
          `<div class="doc-li"><span class="doc-no">一、</span><span>時間：${docText(date) || '＿＿＿＿＿＿'}</span></div>`
          + `<div class="doc-li"><span class="doc-no">二、</span><span>地點：${docText(place) || '＿＿＿＿＿＿'}</span></div>`)
        + docSection(5, '活動流程表', docTable([{ label: '時間', width: '22%' }, { label: '內容' }, { label: '負責', width: '22%' }], flowRows, 3, 'doc-flow-table'))
        + docSection(6, '工作分配表', docTable([{ label: '工作項目', width: '24%' }, { label: '負責人員', width: '22%' }, { label: '工作內容' }], dutyRows, 3, 'doc-duty-table'))
        + docSection(7, '經費概算表', budgetHtml)
        + docSection(8, '預期效益', docItems(data.benefits))
        + docSection(9, '注意事項', notesHtml)
        + docSection(10, '本計畫經校長核可後實施，修正時亦同。', '');
      docRender('pl', html);
      $('plMeta').textContent = `🟡 AI 草稿（${type}${isTrip ? '，已加安全須知、保險、家長同意書' : ''}），請核對後再勾「老師已核對」。`;
      showToast('📋 計畫書草稿完成，請過目。');
    });
''')


# =====================================================================
# G3：🗒 會議紀錄
# =====================================================================
def g3():
    rep('''    <button class="tab-button" type="button" data-page="plan">📋 計畫書</button>''',
        '''    <button class="tab-button" type="button" data-page="plan">📋 計畫書</button>
    <button class="tab-button" type="button" data-page="minutes">🗒 會議紀錄</button>''')

    add_html('''
    <!-- 🗂 行政文書：🗒 會議紀錄（G3） -->
    <section class="page" id="page-minutes">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="mtSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>會議名稱</label>
            <input class="input" id="mtName" placeholder="例：115 學年度第 1 學期第 2 次學年會議"></div>
          <div class="field"><label>時間</label>
            <input class="input" id="mtTime" placeholder="例：115 年 10 月 22 日（三）13:30"></div>
          <div class="field"><label>地點</label>
            <input class="input" id="mtPlace" placeholder="例：五年一班教室"></div>
          <div class="field"><label>主席／紀錄</label>
            <div style="display:flex;gap:6px"><input class="input" id="mtChair" placeholder="主席"><input class="input" id="mtRecorder" placeholder="紀錄"></div></div>
          <div class="field"><label>出席人員（老師自己填，不會送給 AI）</label>
            <input class="input" id="mtAttend" placeholder="例：五年級全體導師、教務主任"></div>
          <div class="warn" style="margin:4px 0 10px">會議內容三選一（也可以混用）：<strong>錄音檔</strong>、<strong>逐字稿或筆記</strong>、<strong>白板／便利貼照片</strong>。</div>
          <div class="field"><label>① 錄音檔（m4a／mp3／webm，單檔 15MB 以內，約 15 分鐘）</label>
            <input class="input" type="file" id="mtAudio" accept="audio/*,.m4a,.mp3,.webm,.wav,.ogg"></div>
          <div class="field"><label>② 逐字稿或筆記文字</label>
            <textarea class="textarea" id="mtText" placeholder="貼上逐字稿、或會議中隨手記的重點"></textarea></div>
          <div class="field"><label>③ 白板／便利貼照片（可多張）</label>
            <input class="input" type="file" id="mtPhotos" accept="image/*" multiple></div>
          <button class="go-button" type="button" id="mtGoButton">🤖 整理成會議紀錄</button>
          <div class="status" id="mtStatus"></div>
          <div class="hint">AI 整理成：主席報告、討論事項（議題、討論摘要、決議）、臨時動議、待辦事項表（事項、負責、期限）、下次會議。期限與負責人<strong>會議沒講到就留空</strong>；學生姓名一律不寫。</div>
          <div class="es-records" id="mtTodoBox" hidden>
            <h4>📋 待辦條列（貼到工作台「AI 行政助理」就會變成任務草稿）</h4>
            <textarea class="textarea" id="mtTodoText" readonly style="min-height:110px"></textarea>
          </div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="mtCheckedLabel"><input type="checkbox" id="mtChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('mtPreview','會議紀錄','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('mtPreview','會議紀錄',false)">⬇ PDF</button>
            <button class="mini" type="button" id="mtTodoCopy">📋 複製待辦</button>
            <span class="status" id="mtMeta">🟡 AI 草稿，請核對後再交出；預覽區可以直接點字修改。</span>
          </div>
          <div class="preview-host" id="mtPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 🗒 會議紀錄（G3）：錄音／逐字稿／白板照片 → 會議紀錄＋待辦表
    // ============================================================
    const MT_AUDIO_TYPES = { mp3: 'audio/mpeg', mpeg: 'audio/mpeg', mpga: 'audio/mpeg', m4a: 'audio/mp4', mp4: 'audio/mp4', aac: 'audio/aac', webm: 'audio/webm', wav: 'audio/wav', ogg: 'audio/ogg' };
    // Gemini inline_data 認得 audio/mpeg、audio/mp4、audio/webm…；Windows 常把 m4a 標成 audio/x-m4a，送之前統一
    function mtAudioFile(file) {
      const ext = (String(file.name || '').split('.').pop() || '').toLowerCase();
      let type = MT_AUDIO_TYPES[ext] || file.type || 'audio/mpeg';
      if (/^audio\/(x-)?m4a$/.test(type)) type = 'audio/mp4';
      return type === file.type ? file : new File([file], file.name, { type });
    }
    $('mtGoButton').dataset.label = $('mtGoButton').textContent;
    attachZone('mtPhotos', { multiple: true });
    docBindConfirm('mt');
    $('mtGoButton').addEventListener('click', async () => {
      const name = $('mtName').value.trim();
      if (!name) return showToast('請先填會議名稱。', true);
      const audio = $('mtAudio').files[0] || null;
      const text = $('mtText').value.trim();
      const photos = zoneFiles('mtPhotos').filter(f => (f.type || '').startsWith('image/')).slice(0, 10);
      if (!audio && !text && !photos.length) return showToast('請提供錄音檔、逐字稿／筆記，或白板照片其中一種。', true);
      if (audio && audio.size > 15 * 1024 * 1024) return showToast(`錄音檔約 ${Math.round(audio.size / 1048576)}MB，超過 15MB 上限；請剪成幾段，或改貼逐字稿。`, true);
      const sources = [audio ? '錄音檔' : '', text ? '逐字稿／筆記' : '', photos.length ? `白板照片 ${photos.length} 張` : ''].filter(Boolean);
      const prompt = [
        '你是臺灣國小的資深行政教師，要把一場校內會議整理成正式的「會議紀錄」。',
        DOC_AI_RULES,
        `會議名稱：${name}；時間：${$('mtTime').value.trim() || '（未提供）'}；地點：${$('mtPlace').value.trim() || '（未提供）'}；主席：${$('mtChair').value.trim() || '（未提供）'}`,
        `這次提供的會議內容：${sources.join('、')}。`,
        audio ? '附件中的音訊是會議錄音：請完整聽完再整理，不需要逐字稿，只要整理出重點、討論與決議；聽不清楚的地方寫「（錄音不清，請核對）」。' : '',
        photos.length ? '附件中的圖片是會議白板或便利貼照片，請辨識上面的文字並整理。' : '',
        text ? `逐字稿／筆記：\n${text}` : '',
        '整理要求：chairReport 主席報告 1–4 條；discussions 討論事項，每案 topic 案由、summary 討論摘要（2–3 句，用「與會老師建議…」「經討論…」這類寫法，不寫誰說了什麼）、resolution 決議（會議沒做決議就寫「續議」）；motions 臨時動議（沒有就回傳空陣列）；todos 待辦事項，task 事項、owner 負責（職稱或處室；會議沒指定就留空）、due 期限（會議有講才填，沒講留空，不要自己訂日期）；nextMeeting 下次會議時間（沒講留空）。',
        '回傳格式：{"chairReport":[""],"discussions":[{"topic":"","summary":"","resolution":""}],"motions":[{"topic":"","resolution":""}],"todos":[{"task":"","owner":"","due":""}],"nextMeeting":""}'
      ].filter(Boolean).join('\n');
      const data = await docAi($('mtGoButton'), $('mtStatus'), prompt, async () => [...(audio ? await filesToParts([mtAudioFile(audio)], 1) : []), ...await filesToParts(photos, 10)]);
      if (!data) return;
      const caseHtml = (list, label) => {
        const items = docArr(list);
        if (!items.length) return '<div class="doc-li"><span>無。</span></div>';
        return items.map((c, i) => `<div class="doc-sub">${label}${docCn(i)}：${docText(c.topic) || '＿＿＿＿'}</div>`
          + (c.summary ? `<div class="doc-li" style="padding-left:1em"><span class="doc-no">說明：</span><span>${docText(c.summary)}</span></div>` : '')
          + `<div class="doc-li" style="padding-left:1em"><span class="doc-no"><b>決議：</b></span><span>${docText(c.resolution) || '＿＿＿＿'}</span></div>`).join('');
      };
      const todoRows = docArr(data.todos).map(t => [t.task || '', t.owner || '', t.due || '']);
      const school = docSchool('mtSchool');
      const html = docHead(/會議$/.test(name) ? `${name}紀錄` : `${name}會議紀錄`, school, [
          `時間：${escapeHtml($('mtTime').value.trim() || '＿＿＿＿')}`, `地點：${escapeHtml($('mtPlace').value.trim() || '＿＿＿＿')}`,
          `主席：${escapeHtml($('mtChair').value.trim() || '＿＿＿＿')}`, `紀錄：${escapeHtml($('mtRecorder').value.trim() || '＿＿＿＿')}`])
        + `<div class="doc-li" style="font-size:14px"><span class="doc-no">出席人員：</span><span>${docText($('mtAttend').value.trim()) || '＿＿＿＿＿＿＿＿＿＿＿＿（詳簽到表）'}</span></div>`
        + docSection(0, '主席報告', docItems(data.chairReport))
        + docSection(1, '討論事項', caseHtml(data.discussions, '案由'))
        + docSection(2, '臨時動議', caseHtml(data.motions, '臨時動議'))
        + docSection(3, '待辦事項', docTable([{ label: '事項' }, { label: '負責', width: '24%' }, { label: '期限', width: '22%' }], todoRows, 3, 'doc-todo-table'))
        + docSection(4, '下次會議', `<div class="doc-li"><span>${docText(data.nextMeeting) || '另行通知。'}</span></div>`)
        + '<div class="doc-h">散會</div>'
        + '<div class="ws-meta" style="margin-top:26px"><span>主席簽名：＿＿＿＿＿＿＿＿</span><span>紀錄簽名：＿＿＿＿＿＿＿＿</span></div>';
      docRender('mt', html);
      $('mtTodoBox').hidden = true;
      $('mtMeta').textContent = `🟡 AI 草稿（來源：${sources.join('、')}），請核對後再勾「老師已核對」。`;
      showToast('🗒 會議紀錄草稿完成，請過目。');
    });
    // 待辦一鍵複製成條列：讀預覽區目前的表格（老師改過的字也算）
    $('mtTodoCopy').addEventListener('click', async () => {
      const rows = [...$('mtPreview').querySelectorAll('.doc-todo-table tr')].slice(1)
        .map(tr => [...tr.cells].map(td => td.textContent.replace(/\s+/g, ' ').trim()))
        .filter(cells => cells[0]);
      if (!rows.length) return showToast('目前沒有待辦事項（先整理會議紀錄，或在待辦表填上事項）。', true);
      const title = $('mtName').value.trim();
      const text = [`【${title || '會議'}】會議待辦`, ...rows.map(([task, owner, due]) => `- ${task}${owner || due ? `（${[owner ? '負責：' + owner : '', due ? '期限：' + due : ''].filter(Boolean).join('；')}）` : ''}`)].join('\n');
      $('mtTodoText').value = text;
      $('mtTodoBox').hidden = false;
      let copied = false;
      try { await navigator.clipboard.writeText(text); copied = true; } catch (e) {
        try { $('mtTodoText').select(); copied = document.execCommand('copy'); } catch (err) {}
      }
      showToast(copied ? `已複製 ${rows.length} 項待辦，到工作台「AI 行政助理」貼上就能變成任務草稿。` : '瀏覽器不允許自動複製，請從左邊的框框手動複製。', !copied);
    });
''')


STEPS = [
    ('G1 成果報告', 'id="page-report"', g1),
    ('G2 計畫書', 'id="page-plan"', g2),
    ('G3 會議紀錄', 'id="page-minutes"', g3),
]

for label, marker, fn in STEPS:
    if marker in s:
        print('略過（已套用）：', label)
        continue
    fn()
    print('已套用：', label)

path.write_text(s, encoding='utf-8')
