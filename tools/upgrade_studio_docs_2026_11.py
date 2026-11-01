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


# =====================================================================
# G4：📘 教案與觀議課
# =====================================================================
def g4():
    rep('''    <button class="tab-button" type="button" data-page="minutes">🗒 會議紀錄</button>''',
        '''    <button class="tab-button" type="button" data-page="minutes">🗒 會議紀錄</button>
    <button class="tab-button" type="button" data-page="lesson">📘 教案與觀議課</button>''')

    add_css('''    .doc-blank-line { border-bottom:1px solid #555; height:30px; }
''')

    add_html('''
    <!-- 🗂 行政文書：📘 教案與公開授課觀議課紀錄（G4） -->
    <section class="page" id="page-lesson">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>要做什麼</label>
            <select class="select" id="lpMode"><option value="lesson">📘 教案（108 課綱格式）</option><option value="observe">👀 公開授課觀課＋議課紀錄</option></select></div>
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="lpSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>年級／領域</label>
            <div style="display:flex;gap:6px">
              <select class="select" id="lpGrade"><option value="一">一年級</option><option value="二">二年級</option><option value="三">三年級</option><option value="四">四年級</option><option value="五" selected>五年級</option><option value="六">六年級</option></select>
              <select class="select" id="lpSubject"><option>國語文</option><option>數學</option><option>英語文</option><option>自然科學</option><option>社會</option><option>生活課程</option><option>健康與體育</option><option>綜合活動</option><option>藝術</option><option>科技</option><option>本土語文</option></select></div></div>
          <div class="field"><label>單元名稱</label>
            <input class="input" id="lpUnit" placeholder="例：分數的加減"></div>
          <div id="lpLessonFields">
            <div class="field"><label>節數（每節 40 分鐘）</label>
              <input class="input" id="lpPeriods" type="number" min="1" max="8" value="2"></div>
            <div class="field"><label>教學重點或想法（選填）</label>
              <textarea class="textarea" id="lpIdea" placeholder="例：想用分組操作分數條，最後讓學生上台解題。"></textarea></div>
            <div class="field"><label>課本頁面照片（選填，可多張）</label>
              <input class="input" type="file" id="lpImages" accept="image/*,.pdf,application/pdf" multiple></div>
            <div class="field"><label>學校教案格式（選填：貼上學校教案的欄位名稱，一行一個，AI 照這些欄位填）</label>
              <textarea class="textarea" id="lpFormat" placeholder="例：&#10;單元名稱&#10;教材來源&#10;學生學習經驗分析&#10;教學目標&#10;教學資源"></textarea></div>
          </div>
          <div id="lpObserveFields" hidden>
            <div class="field"><label>教學者／觀課者／日期（可留白，印出後手寫）</label>
              <div style="display:flex;gap:6px"><input class="input" id="lpTeacher" placeholder="教學者"><input class="input" id="lpObserver" placeholder="觀課者"><input class="input" id="lpObsDate" placeholder="日期"></div></div>
            <div class="field"><label>觀課筆記（一行一條：教學者做了什麼、學生的反應）</label>
              <textarea class="textarea" id="lpBullets" style="min-height:140px" placeholder="例：&#10;用生活情境（分披薩）引起動機&#10;學生分組操作分數條，多數能說出等值分數&#10;有兩組在通分步驟卡住，老師巡視時個別提示&#10;請學生上台說明解法&#10;最後用出口卡檢核"></textarea></div>
          </div>
          <button class="go-button" type="button" id="lpGoButton">🤖 產生教案</button>
          <div class="status" id="lpStatus"></div>
          <div class="hint" id="lpHint">教案含：單元目標、學習表現、學習內容、核心素養、每節教學活動流程表（時間、教師活動、學生活動、評量、資源）、差異化教學、評量方式。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="lpCheckedLabel"><input type="checkbox" id="lpChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('lpPreview',lpFileName(),'doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('lpPreview',lpFileName(),false)">⬇ PDF</button>
            <span class="es-confirm" id="lpCodeHint">⚠ 學習表現、學習內容、核心素養的代碼是 AI 寫的，請對照課綱核對</span>
            <span class="status" id="lpMeta">🟡 AI 草稿，請核對後再交出；預覽區可以直接點字修改。</span>
          </div>
          <div class="preview-host" id="lpPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 📘 教案（108 課綱格式）＋公開授課觀議課紀錄（G4）
    // ============================================================
    const LP_LABELS = { lesson: '🤖 產生教案', observe: '🤖 擴寫觀議課紀錄' };
    function lpFileName() { return $('lpMode').value === 'observe' ? '觀議課紀錄' : '教案'; }
    function lpSyncMode() {
      const observe = $('lpMode').value === 'observe';
      $('lpLessonFields').hidden = observe;
      $('lpObserveFields').hidden = !observe;
      $('lpCodeHint').style.display = observe ? 'none' : '';  // .es-confirm 有 display，不能只靠 hidden
      $('lpGoButton').textContent = $('lpGoButton').dataset.label = LP_LABELS[observe ? 'observe' : 'lesson'];
      $('lpHint').textContent = observe
        ? '把觀課筆記擴寫成觀課紀錄表（觀察面向、教學者的教學行為、學生的學習反應、回饋），再整理議課紀錄：優點 3 項、建議 2 項，教學者回應留白給教學者自己寫。'
        : '教案含：單元目標、學習表現、學習內容、核心素養、每節教學活動流程表（時間、教師活動、學生活動、評量、資源）、差異化教學、評量方式。';
    }
    $('lpMode').addEventListener('change', lpSyncMode);
    lpSyncMode();
    attachZone('lpImages', { multiple: true });
    docBindConfirm('lp');
    function lpCodeTable(list) {
      const rows = docArr(list).map(r => typeof r === 'object' ? [r.code || '', r.text || r.content || ''] : ['', r]);
      return docTable([{ label: '代碼', width: '20%' }, { label: '內容' }], rows, 1) + '<div class="doc-note doc-verify">（代碼請對照課綱核對）</div>';
    }
    function lpActivityTables(lessons) {
      const list = docArr(lessons);
      if (!list.length) return docTable([{ label: '時間', width: '10%' }, { label: '教師活動' }, { label: '學生活動' }, { label: '評量', width: '16%' }, { label: '資源', width: '14%' }], [], 4, 'doc-activity-table');
      return list.map((lesson, i) => `<div class="doc-sub">第${docCn(i)}節${lesson.title ? '：' + docText(lesson.title) : ''}</div>`
        + docTable([{ label: '時間', width: '10%' }, { label: '教師活動' }, { label: '學生活動' }, { label: '評量', width: '16%' }, { label: '資源', width: '14%' }],
          docArr(lesson.activities).map(a => [a.time || '', a.teacher || '', a.student || '', a.assess || '', a.resource || '']), 2, 'doc-activity-table')).join('');
    }
    $('lpGoButton').addEventListener('click', async () => {
      const observe = $('lpMode').value === 'observe';
      const grade = $('lpGrade').value, subject = $('lpSubject').value, unit = $('lpUnit').value.trim();
      const school = docSchool('lpSchool');
      if (observe) {
        const bullets = $('lpBullets').value.split('\n').map(t => t.replace(/^[\s\-•・*‧●○◦]+/, '').trim()).filter(Boolean);
        if (bullets.length < 2) return showToast('請至少寫兩條觀課筆記（一行一條）。', true);
        const prompt = [
          '你是臺灣國小的資深教師，要把同事的公開授課觀課筆記整理成正式的「觀課紀錄表」與「議課紀錄」。',
          DOC_AI_RULES,
          `授課年級：${grade}年級；領域：${subject}；單元：${unit || '（未提供）'}`,
          `觀課筆記（共 ${bullets.length} 條）：`, ...bullets.map((t, i) => `${i + 1}. ${t}`),
          `observations：每一條筆記擴寫成一列（共 ${bullets.length} 列，順序不變）：aspect 觀察面向（例：課程設計與教學、學生學習與反應、班級經營與學習氛圍、評量與回饋）、teacher 教學者的教學行為（具體、客觀描述事實，1–2 句）、student 學生的學習反應（描述看到的事實，用「多數學生」「部分學生」「某組學生」，不寫姓名）、note 觀察者回饋（一句，正向具體）。不要加入筆記裡沒有的事實。`,
          'strengths 議課的優點恰好 3 項；suggestions 具體可行的建議恰好 2 項。教學者回應不要寫，留給教學者。',
          '回傳格式：{"observations":[{"aspect":"","teacher":"","student":"","note":""}],"strengths":["","",""],"suggestions":["",""]}'
        ].join('\n');
        const data = await docAi($('lpGoButton'), $('lpStatus'), prompt);
        if (!data) return;
        const rows = docArr(data.observations).map(o => [o.aspect || '', o.teacher || '', o.student || '', o.note || '']);
        const html = docHead('公開授課觀課與議課紀錄', school, [
            `教學者：${escapeHtml($('lpTeacher').value.trim() || '＿＿＿＿')}`, `觀課者：${escapeHtml($('lpObserver').value.trim() || '＿＿＿＿')}`,
            `日期：${escapeHtml($('lpObsDate').value.trim() || '＿＿＿＿')}`, `${escapeHtml(grade)}年級　${escapeHtml(subject)}　單元：${escapeHtml(unit || '＿＿＿＿')}`])
          + docSection(0, '觀課紀錄', docTable([{ label: '觀察面向', width: '16%' }, { label: '教學者的教學行為' }, { label: '學生的學習反應' }, { label: '觀察者回饋', width: '22%' }], rows, bullets.length, 'doc-observe-table'))
          + docSection(1, '議課紀錄',
            `<div class="doc-sub">一、優點</div>${docItems(docArr(data.strengths).slice(0, 3), 'paren')}`
            + `<div class="doc-sub">二、建議</div>${docItems(docArr(data.suggestions).slice(0, 2), 'paren')}`
            + '<div class="doc-sub">三、教學者回應</div><div class="doc-blank-line"></div><div class="doc-blank-line"></div><div class="doc-blank-line"></div>')
          + '<div class="ws-meta" style="margin-top:26px"><span>教學者簽名：＿＿＿＿＿＿＿＿</span><span>觀課者簽名：＿＿＿＿＿＿＿＿</span></div>';
        docRender('lp', html);
        $('lpMeta').textContent = `🟡 AI 草稿（${bullets.length} 條筆記擴寫），請核對後再勾「老師已核對」。`;
        return showToast('👀 觀議課紀錄草稿完成，請過目。');
      }
      if (!unit) return showToast('請先填單元名稱。', true);
      const periods = Math.max(1, Math.min(8, parseInt($('lpPeriods').value, 10) || 1));
      const files = zoneFiles('lpImages');
      const fields = $('lpFormat').value.split('\n').map(t => t.trim()).filter(Boolean).slice(0, 30);
      const prompt = [
        `你是臺灣國小${grade}年級${subject}領域的資深教師，要依 108 課綱（十二年國民基本教育課程綱要）格式寫一份「${unit}」教案，共 ${periods} 節、每節 40 分鐘。`,
        DOC_AI_RULES,
        $('lpIdea').value.trim() ? `老師的教學重點：${$('lpIdea').value.trim()}` : '',
        files.length ? `附件是課本頁面（共 ${files.length} 份），教學內容以附件為準。` : '',
        '各欄要求：goals 單元目標 2–4 條；performances 學習表現、contents 學習內容、competencies 核心素養，各 1–3 筆，code 寫課綱代碼（例：數-E-A2、n-III-6、N-5-4），不確定的代碼寧可留空字串，text 寫內容；lessons 每節一筆，title 該節主題，activities 依「引起動機、發展活動、綜合活動」排 3–6 列，每列 time（例：5 分）、teacher 教師活動、student 學生活動、assess 評量方式、resource 教學資源，每節時間加總 40 分；differentiation 差異化教學 2–3 條（針對學習較快與需要協助的學生，不寫姓名）；assessment 評量方式 2–4 條。',
        fields.length ? `老師學校的教案有這些欄位，請在 customFields 依序對每個欄位寫內容（name 照抄欄位名稱）：${fields.join('、')}。教學活動流程仍放在 lessons。` : 'customFields 回傳空陣列 []。',
        '回傳格式：{"goals":[""],"performances":[{"code":"","text":""}],"contents":[{"code":"","text":""}],"competencies":[{"code":"","text":""}],"lessons":[{"title":"","activities":[{"time":"","teacher":"","student":"","assess":"","resource":""}]}],"differentiation":[""],"assessment":[""],"customFields":[{"name":"","content":""}]}'
      ].filter(Boolean).join('\n');
      const data = await docAi($('lpGoButton'), $('lpStatus'), prompt, async () => filesToParts(files, 8));
      if (!data) return;
      const custom = docArr(data.customFields).filter(f => f && (f.name || f.content));
      const meta = [`年級：${escapeHtml(grade)}年級`, `領域：${escapeHtml(subject)}`, `單元：${escapeHtml(unit)}`, `節數：${periods} 節（${periods * 40} 分鐘）`, '設計者：＿＿＿＿'];
      let html = docHead(`${subject}領域教學活動設計`, school, meta);
      if (fields.length) {
        html += docSection(0, '教案基本資料（依學校格式）', docTable([{ label: '欄位', width: '24%' }, { label: '內容' }], (custom.length ? custom : fields.map(name => ({ name }))).map(f => [f.name || '', f.content || '']), 0, 'doc-custom-table'))
          + docSection(1, '學習表現與學習內容', lpCodeTable([...docArr(data.performances), ...docArr(data.contents)]))
          + docSection(2, '教學活動', lpActivityTables(data.lessons));
      } else {
        html += docSection(0, '單元目標', docItems(data.goals))
          + docSection(1, '學習表現', lpCodeTable(data.performances))
          + docSection(2, '學習內容', lpCodeTable(data.contents))
          + docSection(3, '核心素養', lpCodeTable(data.competencies))
          + docSection(4, '教學活動', lpActivityTables(data.lessons))
          + docSection(5, '差異化教學', docItems(data.differentiation))
          + docSection(6, '評量方式', docItems(data.assessment));
      }
      docRender('lp', html);
      $('lpMeta').textContent = `🟡 AI 草稿（${periods} 節${fields.length ? '，已套學校格式' : ''}），代碼請對照課綱核對後再勾「老師已核對」。`;
      showToast('📘 教案草稿完成，請過目。');
    });
''')


# =====================================================================
# G5：📅 教學進度表（不用 AI 也能用）
# =====================================================================
def g5():
    rep('''    <button class="tab-button" type="button" data-page="lesson">📘 教案與觀議課</button>''',
        '''    <button class="tab-button" type="button" data-page="lesson">📘 教案與觀議課</button>
    <button class="tab-button" type="button" data-page="schedule">📅 教學進度表</button>''')

    add_css('''    .sc-weeks { max-height:300px; overflow:auto; border:1.5px solid var(--line); border-radius:10px; padding:4px 8px; background:#fbfcfb; }
    .sc-week { display:grid; grid-template-columns:auto 1fr; gap:6px; align-items:center; font-size:13px; padding:3px 0; border-bottom:1px solid #eef2ef; }
    .sc-week label { display:inline-flex; gap:4px; align-items:center; font-weight:700; white-space:nowrap; cursor:pointer; }
    .sc-week .input { padding:3px 8px; font-size:12.5px; }
    .sc-week.off label { color:var(--danger); }
    .sc-chip { display:inline-block; border:1.5px solid #8a9b93; border-radius:8px; padding:0 8px; margin:2px 4px 2px 0; background:#f6faf8; cursor:grab; font-size:13.5px; }
    .sc-chip small { color:#666; font-size:11.5px; }
    .sc-units.sc-over { background:#fff3d6; }
    .sc-off-row td { background:#f1f1f1; color:#777; }
    .sc-note:focus, .sc-title:focus { outline:2px dashed #e0a21a; outline-offset:1px; }
    @media print { .sc-chip { border:0; background:none; padding:0; } }
''')

    add_html('''
    <!-- 🗂 行政文書：📅 教學進度表（G5，不用 AI 也能用） -->
    <section class="page" id="page-schedule">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="scSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>年級／科目</label>
            <div style="display:flex;gap:6px"><input class="input" id="scGrade" placeholder="例：五年級"><input class="input" id="scSubject" placeholder="例：數學"></div></div>
          <div class="field"><label>學期起訖</label>
            <div style="display:flex;gap:6px;align-items:center"><input class="input" type="date" id="scStart"><span>到</span><input class="input" type="date" id="scEnd"></div></div>
          <div class="field"><label>每週節數</label>
            <input class="input" type="number" id="scPerWeek" min="1" max="20" value="4"></div>
          <div class="field"><label>週次（勾＝放假／停課，不排進度；右邊可寫評量或備註）</label>
            <div class="sc-weeks" id="scWeekList"></div></div>
          <div class="field"><label>課本目錄：單元清單（一行一個；要指定節數就寫「單元名｜節數」）</label>
            <textarea class="textarea" id="scToc" style="min-height:140px" placeholder="例：&#10;一、分數的加減｜10&#10;二、小數的乘法&#10;三、長方體與正方體"></textarea></div>
          <div class="field"><label>或拍目錄照片，讓 AI 抓單元（選用）</label>
            <input class="input" type="file" id="scTocImage" accept="image/*">
            <button class="mini" type="button" id="scTocAiButton" style="margin-top:6px">📷 AI 從目錄照片抓單元</button></div>
          <button class="go-button" type="button" id="scGoButton">📅 產生進度表</button>
          <div class="status" id="scStatus"></div>
          <div class="hint">不用 AI 也能用：貼上單元清單就會<strong>自動平均分配到有效週次</strong>（沒寫節數的單元平均分；有寫節數就照節數排）。產生後可以<strong>直接拖拉單元</strong>到別的週，備註欄可以點字修改；匯出 Excel 給教務處。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="scCheckedLabel" style="display:none"><input type="checkbox" id="scChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('scPreview','教學進度表','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('scPreview','教學進度表',false)">⬇ PDF</button>
            <button class="mini" type="button" onclick="downloadPreview('scPreview','教學進度表','xls')">⬇ Excel</button>
            <span class="status" id="scMeta">填好學期與單元清單，按「產生進度表」。</span>
          </div>
          <div class="preview-host" id="scPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 📅 教學進度表（G5）：週次 × 單元自動分配，可拖調、可匯出 Excel
    // ============================================================
    const SC = { weeks: [], perWeek: 4, aiUsed: false, off: new Set(), notes: {} };
    const scIso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const scParse = v => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || ''); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; };
    const scMd = d => `${d.getMonth() + 1}/${d.getDate()}`;
    (function scDefaultTerm() {
      const now = new Date(), y = now.getFullYear(), m = now.getMonth() + 1;
      const [a, b] = m >= 8 ? [`${y}-08-30`, `${y + 1}-01-20`] : m === 1 ? [`${y - 1}-08-30`, `${y}-01-20`] : [`${y}-02-11`, `${y}-06-30`];
      $('scStart').value = a; $('scEnd').value = b;
    })();
    // 依學期起訖切成週（週一到週五），保留老師勾過的放假週與備註
    function scBuildWeeks() {
      const start = scParse($('scStart').value), end = scParse($('scEnd').value);
      const weeks = [];
      if (start && end && end >= start) {
        const monday = new Date(start); monday.setDate(monday.getDate() - (monday.getDay() + 6) % 7);
        for (let i = 0; monday <= end && i < 30; i += 1) {
          const friday = new Date(monday); friday.setDate(friday.getDate() + 4);
          const from = monday < start ? new Date(start) : new Date(monday);
          const to = friday > end ? new Date(end) : friday;
          const key = scIso(monday);
          weeks.push({ no: i + 1, key, from, to, off: SC.off.has(key), note: SC.notes[key] || '', items: [] });
          monday.setDate(monday.getDate() + 7);
        }
      }
      SC.weeks = weeks;
      $('scWeekList').innerHTML = weeks.length ? weeks.map(w => `<div class="sc-week${w.off ? ' off' : ''}" data-key="${w.key}">
          <label><input type="checkbox" class="scOff" data-key="${w.key}"${w.off ? ' checked' : ''}> 第${w.no}週 ${scMd(w.from)}–${scMd(w.to)}</label>
          <input class="input scWeekNote" data-key="${w.key}" value="${escapeHtml(w.note)}" placeholder="評量／備註"></div>`).join('')
        : '<div class="hint">請先填學期起訖日期。</div>';
    }
    $('scWeekList').addEventListener('change', e => {
      const box = e.target.closest('.scOff');
      if (!box) return;
      if (box.checked) SC.off.add(box.dataset.key); else SC.off.delete(box.dataset.key);
      box.closest('.sc-week').classList.toggle('off', box.checked);
    });
    $('scWeekList').addEventListener('input', e => {
      const input = e.target.closest('.scWeekNote');
      if (input) SC.notes[input.dataset.key] = input.value;
    });
    ['scStart', 'scEnd'].forEach(id => $(id).addEventListener('change', scBuildWeeks));
    scBuildWeeks();
    function scParseUnits() {
      return $('scToc').value.split('\n').map(line => line.trim()).filter(Boolean).map(line => {
        const m = /^(.*?)\s*[｜|，,\t]\s*(\d+)\s*節?$/.exec(line);
        return m && m[1] ? { name: m[1].trim(), n: parseInt(m[2], 10) } : { name: line, n: 0 };
      });
    }
    // 分配：沒寫節數→以「週」為單位平均分（單元少就一單元多週，單元多就一週多單元）；有寫節數→照節數依序填滿每週
    function scAllocate(units, perWeek) {
      SC.weeks.forEach(w => { w.items = []; w.over = false; });
      const valid = SC.weeks.filter(w => !w.off);
      if (!valid.length || !units.length) return { overflow: 0 };
      const W = valid.length, U = units.length;
      if (!units.some(u => u.n)) {
        if (U <= W) {
          let wi = 0;
          units.forEach((u, i) => {
            const span = Math.floor(W / U) + (i < W % U ? 1 : 0);
            for (let k = 0; k < span; k += 1) valid[wi++].items.push({ name: u.name, n: perWeek });
          });
        } else {
          let ui = 0;
          valid.forEach((w, j) => {
            const count = Math.floor(U / W) + (j < U % W ? 1 : 0);
            for (let k = 0; k < count; k += 1) w.items.push({ name: units[ui++].name, n: Math.floor(perWeek / count) + (k < perWeek % count ? 1 : 0) });
          });
        }
        return { overflow: 0 };
      }
      // 有指定節數：沒寫的單元平分剩下的節數（至少 1 節）
      const total = W * perWeek;
      const fixed = units.reduce((sum, u) => sum + (u.n || 0), 0);
      const missing = units.filter(u => !u.n).length;
      const share = missing ? Math.max(1, Math.floor(Math.max(0, total - fixed) / missing)) : 0;
      let wi = 0, cap = perWeek, overflow = 0;
      units.forEach(u => {
        let left = u.n || share;
        while (left > 0) {
          if (wi >= W) { const last = valid[W - 1]; last.items.push({ name: u.name, n: left }); last.over = true; overflow += left; break; }
          const take = Math.min(left, cap);
          const week = valid[wi];
          const prev = week.items[week.items.length - 1];
          if (prev && prev.name === u.name) prev.n += take; else week.items.push({ name: u.name, n: take });
          left -= take; cap -= take;
          if (cap === 0) { wi += 1; cap = perWeek; }
        }
      });
      return { overflow };
    }
    function scRender() {
      const title = [$('scGrade').value.trim(), $('scSubject').value.trim()].filter(Boolean).join(' ');
      const rows = SC.weeks.map((w, i) => {
        const units = w.off ? '（放假／停課）' : (w.items.length
          ? w.items.map((it, k) => `<span class="sc-chip" draggable="true" contenteditable="false" data-w="${i}" data-k="${k}">${escapeHtml(it.name)}<small>（${it.n} 節）</small></span>`).join('')
          : '複習／彈性');
        const periods = w.off ? 0 : (w.items.length ? w.items.reduce((s, it) => s + it.n, 0) : SC.perWeek);
        return `<tr class="${w.off ? 'sc-off-row' : ''}"><td style="text-align:center">${w.no}</td><td>${scMd(w.from)}–${scMd(w.to)}</td>
          <td class="sc-units${w.over ? ' sc-over' : ''}" data-w="${i}">${units}</td><td style="text-align:center">${periods}</td>
          <td class="sc-note" contenteditable="true" data-w="${i}">${escapeHtml(w.note)}</td></tr>`;
      }).join('');
      $('scPreview').innerHTML = `<div class="sheet doc-sheet">
        <div class="ws-head"><div class="ws-school">${escapeHtml(docSchool('scSchool') || '＿＿＿＿＿＿國民小學')}</div>
          <div class="sc-title ws-title" contenteditable="true">${escapeHtml(title ? title + ' ' : '')}教學進度表</div></div>
        <div class="ws-meta"><span>學期：${escapeHtml($('scStart').value)} 至 ${escapeHtml($('scEnd').value)}</span><span>每週 ${SC.perWeek} 節</span><span>有效週次 ${SC.weeks.filter(w => !w.off).length} 週</span></div>
        <table class="doc-table sc-table"><colgroup><col style="width:8%"><col style="width:15%"><col><col style="width:8%"><col style="width:22%"></colgroup>
          <tr><th>週次</th><th>日期區間</th><th>單元</th><th>節數</th><th>評量／備註</th></tr>${rows}</table>
        <div class="ws-meta" style="margin-top:20px"><span>任課教師：＿＿＿＿＿＿</span><span>教務處：＿＿＿＿＿＿</span></div>
        <div class="doc-ai-sign" contenteditable="false">AI 協助草擬，內容已由老師核對</div></div>`;
      docApplyConfirm('sc');
    }
    $('scGoButton').addEventListener('click', () => {
      const units = scParseUnits();
      if (!units.length) return showToast('請先輸入單元清單（一行一個），或用目錄照片讓 AI 抓。', true);
      scBuildWeeks();
      if (!SC.weeks.length) return showToast('請先填正確的學期起訖日期。', true);
      SC.perWeek = Math.max(1, Math.min(20, parseInt($('scPerWeek').value, 10) || 1));
      const { overflow } = scAllocate(units, SC.perWeek);
      if (!SC.weeks.some(w => !w.off)) return showToast('每一週都勾了放假，沒有可以排進度的週次。', true);
      scRender();
      const W = SC.weeks.filter(w => !w.off).length;
      $('scMeta').textContent = `${units.length} 個單元 → ${W} 個有效週次（每週 ${SC.perWeek} 節）。可直接拖拉單元換週。`;
      if (overflow) showToast(`單元節數比可用節數多 ${overflow} 節，已先放在最後一週（黃底），請調整。`, true);
      else showToast('📅 進度表完成，可拖拉調整後匯出 Excel。');
    });
    // 拖拉單元到別週
    $('scPreview').addEventListener('dragstart', e => {
      const chip = e.target.closest('.sc-chip');
      if (!chip) return;
      e.dataTransfer.setData('text/plain', `${chip.dataset.w},${chip.dataset.k}`);
      e.dataTransfer.effectAllowed = 'move';
    });
    $('scPreview').addEventListener('dragover', e => { if (e.target.closest('.sc-units')) e.preventDefault(); });
    $('scPreview').addEventListener('drop', e => {
      const cell = e.target.closest('.sc-units');
      if (!cell) return;
      e.preventDefault();
      const [w, k] = String(e.dataTransfer.getData('text/plain')).split(',').map(Number);
      const to = Number(cell.dataset.w);
      const from = SC.weeks[w];
      if (!from || !from.items[k] || to === w) return;
      if (SC.weeks[to].off) return showToast('這週已勾放假，不能排進度；要排請先取消勾選再重新產生。', true);
      const [item] = from.items.splice(k, 1);
      SC.weeks[to].items.push(item);
      from.over = false;
      scRender();
    });
    // 預覽區改備註也記回去（重新拖拉時不會消失）
    $('scPreview').addEventListener('input', e => {
      const note = e.target.closest('.sc-note');
      if (!note) return;
      const w = SC.weeks[Number(note.dataset.w)];
      if (w) { w.note = note.textContent; SC.notes[w.key] = w.note; }
      const side = $('scWeekList').querySelector(`.scWeekNote[data-key="${w && w.key}"]`);
      if (side) side.value = w.note;
    });
    docBindConfirm('sc');
    attachZone('scTocImage');
    $('scTocAiButton').dataset.label = $('scTocAiButton').textContent;
    $('scTocAiButton').addEventListener('click', async () => {
      const file = zoneFirst('scTocImage');
      if (!file) return showToast('請先選目錄照片；沒有照片也可以直接在上面打單元清單。', true);
      const prompt = [
        '附圖是臺灣國小課本的目錄頁。請抓出每一個「單元」（大單元或課次，依目錄的層級，不要抓頁碼）。',
        '只回傳 JSON，不要其他文字。periods 只有目錄上有印節數或建議節數時才填數字，否則填 null，不要自己估。',
        '格式：{"units":[{"name":"一、分數的加減","periods":null}]}'
      ].join('\n');
      const data = await docAi($('scTocAiButton'), $('scStatus'), prompt, async () => filesToParts([file], 1));
      if (!data) return;
      const units = docArr(data.units).map(u => typeof u === 'object' ? u : { name: u }).filter(u => u.name);
      if (!units.length) return showToast('AI 沒有從照片抓到單元，請換一張清楚的照片或手動輸入。', true);
      $('scToc').value = units.map(u => `${String(u.name).trim()}${u.periods ? '｜' + parseInt(u.periods, 10) : ''}`).join('\n');
      SC.aiUsed = true;
      $('scCheckedLabel').style.display = '';
      showToast(`AI 抓到 ${units.length} 個單元，請核對後按「產生進度表」。`);
    });
''')


# =====================================================================
# G6：🧳 代課包（不用 AI；不設任何個別學生欄位）
# =====================================================================
def g6():
    rep('''    <button class="tab-button" type="button" data-page="schedule">📅 教學進度表</button>''',
        '''    <button class="tab-button" type="button" data-page="schedule">📅 教學進度表</button>
    <button class="tab-button" type="button" data-page="substitute">🧳 代課包</button>''')

    add_css('''    .sb-row { display:grid; grid-template-columns:70px 1fr 24px; gap:4px; margin-bottom:6px; padding-bottom:6px; border-bottom:1px dashed var(--line); }
    .sb-row.with-class { grid-template-columns:70px 84px 1fr 24px; }
    .sb-row .input { padding:4px 7px; font-size:13px; }
    .sb-row .sb-wide { grid-column:1 / -2; }
    .sb-row .mini { padding:0 4px; }
    .sb-seat .st-stage { font-size:13px; padding:3px; margin-bottom:8px; letter-spacing:.3em; }
    .sb-seat .st-grid, .sb-seat .st-islands { gap:6px; }
    .sb-seat .st-desk { min-height:34px; font-size:15px; border-width:1.5px; border-radius:6px; cursor:default; }
    .sb-seat .st-island .st-desk { min-width:56px; min-height:30px; font-size:14px; }
''')

    add_html('''
    <!-- 🗂 行政文書：🧳 代課包（G6，不用 AI；依個資保護不設個別學生欄位） -->
    <section class="page" id="page-substitute">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>版本</label>
            <select class="select" id="sbMode"><option value="homeroom">導師版（一個班、全天課表）</option><option value="subject">科任版（可列多個班）</option></select></div>
          <div class="field"><label>學校名稱</label>
            <input class="input docSchool" id="sbSchool" placeholder="例：○○市○○國民小學"></div>
          <div class="field"><label>代課日期／原任教師</label>
            <div style="display:flex;gap:6px"><input class="input" id="sbDate" placeholder="例：11 月 20 日（五）"><input class="input" id="sbTeacher" placeholder="原任教師"></div></div>
          <div class="field" id="sbClassField"><label>班級</label>
            <input class="input" id="sbClass" placeholder="例：五年一班"></div>
          <div class="field"><label>節次與進度（每節：科目、進度、作業與批改規則）</label>
            <div id="sbRows"></div>
            <button class="mini" type="button" id="sbAddRow">＋ 加一節</button></div>
          <div class="field"><label>班級常規三條</label>
            <input class="input" id="sbRule1" value="上課鐘響回座位，先把課本和鉛筆盒放桌上。" style="margin-bottom:4px">
            <input class="input" id="sbRule2" value="要發言先舉手，等老師點到再說。" style="margin-bottom:4px">
            <input class="input" id="sbRule3" value="下課前整理座位周圍，椅子靠好再離開。"></div>
          <div class="field"><label><input type="checkbox" id="sbSeat" checked> 附上座位表（讀「🪑 座位表」分頁目前排好的座位；沒排就印空白格）</label></div>
          <div class="field"><label>聯絡窗口（職稱＋分機）</label>
            <input class="input" id="sbContact1" placeholder="學年主任／隔壁班導師：分機" style="margin-bottom:4px">
            <input class="input" id="sbContact2" placeholder="教務處（代課登記）：分機" style="margin-bottom:4px">
            <input class="input" id="sbContact3" placeholder="學務處／健康中心（緊急）：分機"></div>
          <div class="field"><label>其他交代（全班性的事，例：午餐打菜、放學路隊）</label>
            <textarea class="textarea" id="sbOther" placeholder="例：午餐由值日生打菜；放學路隊在川堂集合。"></textarea></div>
          <button class="go-button" type="button" id="sbGoButton">🧳 產生代課包</button>
          <div class="status" id="sbStatus"></div>
          <div class="hint">完全不用 AI，直接排成 A4 交接單，含代課老師當日簽認欄。依個資保護，本表<strong>刻意不設個別學生的欄位</strong>；需要交代的個別狀況，請口頭說明或請學務處轉知。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('sbPreview','代課交接單','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('sbPreview','代課交接單',false)">⬇ PDF</button>
            <span class="status" id="sbMeta">填好後按「產生代課包」；預覽區可以直接點字修改。</span>
          </div>
          <div class="preview-host" id="sbPreview"></div>
        </div>
      </div>
''')

    add_js(r'''
    // ============================================================
    // 🧳 代課包（G6）：導師版／科任版；純本機、不用 AI、不設個別學生欄位
    // ============================================================
    const SB_PERIODS = ['第一節', '第二節', '第三節', '第四節', '第五節', '第六節', '第七節', '第八節'];
    function sbRowHtml(withClass, period) {
      return `<div class="sb-row${withClass ? ' with-class' : ''}">
        <input class="input sb-period" value="${escapeHtml(period || '')}" placeholder="節次">
        ${withClass ? '<input class="input sb-class" placeholder="班級">' : ''}
        <input class="input sb-subject" placeholder="科目">
        <button class="mini sb-del" type="button" title="刪除這一節">✕</button>
        <input class="input sb-progress sb-wide" placeholder="進度（例：課本 p.42–45，第 3 課第二段）">
        <input class="input sb-homework sb-wide" placeholder="作業與批改規則（例：習作 p.20，寫完收齊放講桌，不用批改）"></div>`;
    }
    function sbResetRows() {
      const subject = $('sbMode').value === 'subject';
      $('sbClassField').hidden = subject;
      $('sbRows').innerHTML = (subject ? SB_PERIODS.slice(0, 6) : SB_PERIODS.slice(0, 7)).map(p => sbRowHtml(subject, p)).join('');
      $('sbSeat').checked = !subject;
    }
    $('sbMode').addEventListener('change', sbResetRows);
    sbResetRows();
    $('sbAddRow').addEventListener('click', () => {
      const rows = $('sbRows').querySelectorAll('.sb-row').length;
      if (rows >= 12) return showToast('最多 12 列。', true);
      $('sbRows').insertAdjacentHTML('beforeend', sbRowHtml($('sbMode').value === 'subject', SB_PERIODS[rows] || ''));
    });
    $('sbRows').addEventListener('click', e => { const del = e.target.closest('.sb-del'); if (del) del.closest('.sb-row').remove(); });
    // 座位表：複製「🪑 座位表」分頁目前的排法（只在這台電腦的畫面之間複製，不存、不送出）；沒有就印 6×5 空白格
    function sbSeatHtml() {
      const src = $('stPreview') && $('stPreview').querySelector('.sheet');
      if (src && src.querySelector('.st-desk')) {
        const box = document.createElement('div');
        [...src.children].filter(el => !el.classList.contains('ws-head') && el.tagName !== 'P').forEach(el => box.appendChild(el.cloneNode(true)));
        box.querySelectorAll('[draggable]').forEach(el => el.removeAttribute('draggable'));
        box.querySelectorAll('.picked').forEach(el => el.classList.remove('picked'));
        return `<div class="sb-seat">${box.innerHTML}</div>`;
      }
      const desks = Array.from({ length: 30 }, () => '<div class="st-desk">&nbsp;</div>').join('');
      return `<div class="sb-seat"><div class="st-stage">講　台</div><div class="st-grid" style="grid-template-columns:repeat(6,1fr)">${desks}</div>
        <div class="doc-note">（座位表分頁還沒排座位，請手寫座號）</div></div>`;
    }
    $('sbGoButton').dataset.label = $('sbGoButton').textContent;
    $('sbGoButton').addEventListener('click', () => {
      const subject = $('sbMode').value === 'subject';
      const rows = [...$('sbRows').querySelectorAll('.sb-row')].map(row => ({
        period: row.querySelector('.sb-period').value.trim(), klass: row.querySelector('.sb-class') ? row.querySelector('.sb-class').value.trim() : '',
        subject: row.querySelector('.sb-subject').value.trim(), progress: row.querySelector('.sb-progress').value.trim(), homework: row.querySelector('.sb-homework').value.trim()
      })).filter(r => r.period || r.klass || r.subject || r.progress || r.homework);
      const headers = subject
        ? [{ label: '節次', width: '10%' }, { label: '班級', width: '12%' }, { label: '科目', width: '11%' }, { label: '進度' }, { label: '作業與批改規則', width: '30%' }]
        : [{ label: '節次', width: '10%' }, { label: '科目', width: '12%' }, { label: '進度' }, { label: '作業與批改規則', width: '34%' }];
      const tableRows = rows.map(r => subject ? [r.period, r.klass, r.subject, r.progress, r.homework] : [r.period, r.subject, r.progress, r.homework]);
      const rules = ['sbRule1', 'sbRule2', 'sbRule3'].map(id => $(id).value.trim()).filter(Boolean);
      const contacts = [['學年主任／隔壁班', 'sbContact1'], ['教務處（代課登記）', 'sbContact2'], ['學務處／健康中心（緊急）', 'sbContact3']].map(([label, id]) => [label, $(id).value.trim()]);
      const other = $('sbOther').value.trim();
      const meta = [`代課日期：${escapeHtml($('sbDate').value.trim() || '＿＿＿＿')}`, `原任教師：${escapeHtml($('sbTeacher').value.trim() || '＿＿＿＿')}`];
      if (!subject) meta.push(`班級：${escapeHtml($('sbClass').value.trim() || '＿＿＿＿')}`);
      let no = 0;
      const section = (title, body) => docSection(no++, title, body);
      const html = docHead(`代課交接單（${subject ? '科任版' : '導師版'}）`, docSchool('sbSchool'), meta)
        + section('課務與進度', docTable(headers, tableRows, subject ? 6 : 7, 'doc-sub-table'))
        + section('班級常規', docItems(rules))
        + ($('sbSeat').checked ? section('座位表', sbSeatHtml()) : '')
        + section('聯絡窗口', docTable([{ label: '窗口', width: '34%' }, { label: '聯絡方式（職稱、分機）' }], contacts, 0))
        + (other ? section('其他交代', `<div class="doc-li"><span>${docText(other)}</span></div>`) : '')
        + section('代課教師當日簽認',
          docTable([{ label: '代課教師簽名', width: '34%' }, { label: '日期', width: '22%' }, { label: '交接確認' }], [['', '', '□ 已了解上列課務、作業與常規']], 0, 'doc-sign-table')
          + '<div class="doc-sub">今日上課情形回報（全班性的事項）：</div><div class="doc-blank-line"></div><div class="doc-blank-line"></div><div class="doc-blank-line"></div>');
      docRender('sb', html, false);
      $('sbMeta').textContent = `已排好 ${subject ? '科任版' : '導師版'}（${rows.length} 節）；預覽區可直接改字，再列印或下載。`;
      showToast('🧳 代課包完成。');
    });
''')


STEPS = [
    ('G1 成果報告', 'id="page-report"', g1),
    ('G2 計畫書', 'id="page-plan"', g2),
    ('G3 會議紀錄', 'id="page-minutes"', g3),
    ('G4 教案與觀議課', 'id="page-lesson"', g4),
    ('G5 教學進度表', 'id="page-schedule"', lambda: g5()),
    ('G6 代課包', 'id="page-substitute"', lambda: g6()),
]

for label, marker, fn in STEPS:
    if marker in s:
        print('略過（已套用）：', label)
        continue
    fn()
    print('已套用：', label)

path.write_text(s, encoding='utf-8')
