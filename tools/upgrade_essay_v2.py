"""作文批改升級（升級規劃第一批 1–3）：
1. 年段規準表（原創描述；架構參酌會考四向度六級分）；一二年級改「看圖寫話四指標」三星制
2. 批改單可直接修改、勾「老師已確認」才能列印；本機批改紀錄；家長版說明（先預覽再複製）
3. 同題目 ≥3 篇 → 全班共通問題統計＋回饋課一頁講義（本機計算，不呼叫 AI、沒有姓名）

python tools/upgrade_essay_v2.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'ES_RUBRICS' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ------------------------------------------------------------------ CSS
rep('''    .ws-section { margin:14px 0 6px; font-size:16px; font-weight:900; }''', '''    .ws-section { margin:14px 0 6px; font-size:16px; font-weight:900; }
    /* ✍️ 作文批改 v2 */
    .mini[disabled] { opacity:.45; cursor:not-allowed; }
    .es-confirm { display:inline-flex; align-items:center; gap:6px; font-weight:900; font-size:13.5px; color:#a33; background:#fff3f0; border:1.5px solid #f0c2b8; border-radius:9px; padding:5px 10px; cursor:pointer; }
    .es-confirm.ok { color:#1d6e3f; background:#eaf6ee; border-color:#bfe0c9; }
    #esPreview [contenteditable="true"]:focus { outline:2px dashed #e0a21a; outline-offset:2px; }
    .es-records { margin-top:14px; border-top:1.5px dashed var(--line); padding-top:10px; }
    .es-records h4 { margin:0 0 6px; font-size:14.5px; }
    .es-rec { display:grid; grid-template-columns:1fr auto; gap:6px; align-items:center; font-size:13px; padding:5px 0; border-bottom:1px solid #eef2ef; }
    .es-rec b { font-weight:900; }
    .es-rec .mini { padding:3px 9px; font-size:12px; }
    .es-parent { width:100%; min-height:150px; font-size:14px; line-height:1.7; border-radius:10px; border:1.5px solid var(--line); padding:8px 10px; font-family:inherit; }''')

# ------------------------------------------------------------------ HTML：左欄加座號、保存原文、紀錄區
rep('''          <div class="field"><label>作文題目</label>
            <input class="input" id="esTopic" placeholder="例：我的家人／難忘的校外教學"></div>''', '''          <div class="field"><label>作文題目</label>
            <input class="input" id="esTopic" placeholder="例：我的家人／難忘的校外教學"></div>
          <div class="field"><label>座號（選填，只存在這台電腦；做全班統計用，不要填姓名）</label>
            <input class="input" id="esSeat" inputmode="numeric" placeholder="例：12"></div>''')
rep('''              <option value="六級分" selected>六級分（國中會考寫作評分規準，依年級調整期待）</option>''', '''              <option value="六級分" selected>六級分（四向度，依年段規準表）</option>''')
rep('''          <div class="warn">AI 批改是<strong>老師的助手草稿</strong>——分數與評語請老師確認調整後再回饋給學生；照片請避免拍到姓名（可先用遮蔽工具處理）。</div>
        </div>''', '''          <div class="warn">AI 批改是<strong>老師的助手草稿</strong>——分數與評語請老師確認調整後再回饋給學生；照片請避免拍到姓名（可先用遮蔽工具處理）。</div>
          <div class="es-records">
            <h4>📚 批改紀錄（只存在這台電腦）</h4>
            <label style="font-size:13px;font-weight:700"><input type="checkbox" id="esKeepText"> 同時保存作文原文（預設不保存）</label>
            <div id="esRecordList" style="margin-top:6px"></div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
              <button class="mini" type="button" id="esStatsButton">📊 同題目全班統計＋回饋課講義</button>
              <button class="mini" type="button" id="esRubricButton">📐 看規準表</button>
            </div>
          </div>
        </div>''')
rep('''            <button class="mini" type="button" onclick="window.print()">🖨 列印批改單</button>
            <button class="mini" type="button" onclick="downloadPreview('esPreview','作文批改單','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('esPreview','作文批改單',false)">⬇ PDF</button>
            <span class="status" id="esMeta">批改後會產生一張可列印的批改單，可以夾回作文本。</span>''', '''            <label class="es-confirm" id="esConfirmLabel" hidden><input type="checkbox" id="esConfirm"> 老師已確認內容</label>
            <button class="mini es-out" type="button" onclick="window.print()">🖨 列印批改單</button>
            <button class="mini es-out" type="button" onclick="downloadPreview('esPreview','作文批改單','doc')">⬇ Word</button>
            <button class="mini es-out" type="button" onclick="downloadPdfFromHost('esPreview','作文批改單',false)">⬇ PDF</button>
            <button class="mini" type="button" id="esParentButton" hidden>👪 家長版說明</button>
            <span class="status" id="esMeta">批改後會產生一張可列印的批改單，可以夾回作文本。</span>''')

# ------------------------------------------------------------------ JS：規準表
RUBRIC = r'''
    // 年段規準表（2026-11-01 升級）：架構參酌國中教育會考寫作測驗「四向度・六級分」；
    // 各級描述由本系統依國小年段自行撰寫，不是會考原文。一二年級改用「看圖寫話四指標」三星制。
    const ES_RUBRIC_NOTE = '評分架構參酌國中教育會考寫作測驗的四向度與六級分；各級描述為本系統依國小年段自行撰寫，非會考原文。';
    const ES_RUBRICS = {
      mid: { label: '中年級（三、四年級）', unit: '級', levels: [6, 5, 4, 3, 2, 1], dims: [
        { name: '立意取材', d: ['切題，寫出具體的經過和自己的感受', '切題，經過寫得具體', '大致切題，經過寫得簡單', '有點離題，或缺少細節', '大部分離題，內容很少', '幾乎沒有寫到題目要求'] },
        { name: '結構組織', d: ['能分段寫出開頭、經過、結尾，順序清楚', '有分段，順序清楚', '有分段，但某一段太短或太長', '分段不清楚，或順序有點亂', '只有一段，或前後跳來跳去', '看不出段落'] },
        { name: '遣詞造句', d: ['用詞具體，句子通順，會用簡單修辭（如譬喻）', '句子通順，用詞恰當', '句子大多通順，用詞平實', '有幾句不通順或用詞不當', '很多句子不通順', '大多數句子讀不懂'] },
        { name: '錯別字・格式・標點', d: ['幾乎沒有錯字，會正確使用逗號、句號、引號', '少數錯字或標點小錯', '有一些錯字或標點錯誤，但不影響閱讀', '錯字、注音代替或標點錯誤偏多', '錯誤很多，影響閱讀', '錯誤多到難以閱讀'] }] },
      high: { label: '高年級（五、六年級）', unit: '級', levels: [6, 5, 4, 3, 2, 1], dims: [
        { name: '立意取材', d: ['切題，選材有代表性，主旨鮮明，有自己的想法', '切題，選材適切，主旨清楚', '大致切題，選材平常，看得出主旨', '有些偏題或事例空泛，主旨不夠明確', '大部分離題或內容很少', '幾乎沒有寫到題目要求'] },
        { name: '結構組織', d: ['分段恰當，開頭結尾呼應，段落銜接自然', '段落完整，順序清楚', '有開頭、中間、結尾，但一兩處銜接生硬', '分段不太恰當，或順序有些混亂', '段落不完整，或前後跳躍', '看不出段落結構'] },
        { name: '遣詞造句', d: ['用詞精準生動，句型有變化，修辭運用得當', '用詞恰當，句子通順，偶有修辭', '句子大致通順，用詞平實', '有幾處句子不通或用詞不當', '句子常常不通順，影響理解', '大多數句子無法讀懂'] },
        { name: '錯別字・格式・標點', d: ['幾乎沒有錯別字，標點正確，格式完整', '偶有錯別字或標點小錯', '有一些錯別字或標點錯誤，但不影響閱讀', '錯別字或標點錯誤偏多', '錯誤很多，影響閱讀', '錯誤多到難以閱讀'] }] },
      low: { label: '低年級（一、二年級）看圖寫話', unit: '星', levels: [3, 2, 1], dims: [
        { name: '句子完整', d: ['每一句都說清楚「誰、做什麼」', '大部分句子完整', '很多句子只寫一半'] },
        { name: '標點符號', d: ['會用逗號、句號，問句會用問號', '偶爾忘記標點', '很少用標點'] },
        { name: '用詞', d: ['會用學過的語詞，字大多寫對', '有一些錯字或用注音代替', '錯字或注音很多'] },
        { name: '內容', d: ['寫出圖片或題目的重點，還加上自己的想法', '寫出圖片或題目的重點', '內容很少，或沒寫到重點'] }] }
    };
    function esBand(grade) { return ['一', '二'].includes(grade) ? 'low' : ['三', '四'].includes(grade) ? 'mid' : 'high'; }
    function esRubricPrompt(band) {
      const r = ES_RUBRICS[band];
      return r.dims.map(dim => `【${dim.name}】` + r.levels.map((lv, i) => `${lv}${r.unit}：${dim.d[i]}`).join('；')).join('\n');
    }
    function esRubricTableHtml(band) {
      const r = ES_RUBRICS[band];
      const th = 'border:1px solid #999;padding:4px;background:#f3f3f3';
      const td = 'border:1px solid #999;padding:4px;vertical-align:top';
      return `<div class="ws-section">📏 評分規準（${r.label}）</div>
        <table style="width:100%;border-collapse:collapse;font-size:11.5px">
          <tr><th style="${th};width:88px">向度</th>${r.levels.map(lv => `<th style="${th}">${band === 'low' ? '⭐'.repeat(lv) : lv + ' 級'}</th>`).join('')}</tr>
          ${r.dims.map(dim => `<tr><td style="${td};font-weight:800">${dim.name}</td>${dim.d.map(t => `<td style="${td}">${t}</td>`).join('')}</tr>`).join('')}
        </table>
        <p style="font-size:10.5px;color:#666;margin:4px 0 0">${ES_RUBRIC_NOTE}</p>`;
    }
    // 一二年級選「六級分」時，選單文字換成看圖寫話四指標
    function esSyncScoringLabel() {
      const opt = $('esScoring').querySelector('option[value="六級分"]');
      opt.textContent = esBand($('esGrade').value) === 'low' ? '看圖寫話四指標（一二年級，三星制）' : '六級分（四向度，依年段規準表）';
    }
    $('esGrade').addEventListener('change', esSyncScoringLabel);
    esSyncScoringLabel();
'''
rep('''    $('esGoButton').dataset.label = $('esGoButton').textContent;''', RUBRIC + '''    $('esGoButton').dataset.label = $('esGoButton').textContent;''')

# prompt：送完整規準；一二年級改四指標三星；多要 homeTip
rep('''        scoring === '六級分'
          ? ['採「國中教育會考寫作測驗評分規準」的六級分制與四向度，但期待值依國小年級調整（同年級中表現）：',
             '四向度＝①立意取材（能否切題、選材是否凸顯主旨）②結構組織（段落完整、前後連貫）③遣詞造句（用詞準確、句型變化、文句流暢）④錯別字、格式與標點符號。',
             '六級分意義：6=十分優秀、5=精采、4=符合基本要求、3=尚可但不太充分、2=不夠好、1=嚴重問題。',
             'grade 欄填「N級分」，並回傳 "dimensions":[{"name":"立意取材","level":1到6,"note":"一句話評語"}×4個向度]。'].join('\\n')''', '''        scoring === '六級分' && esBand($('esGrade').value) === 'low'
          ? ['一二年級用「看圖寫話四指標」三星制，不要用級分。依下面的規準逐項給 1～3 星：',
             esRubricPrompt('low'),
             'grade 欄填整體星等，例如「⭐⭐」；回傳 "dimensions":[{"name":"句子完整","level":1到3,"note":"一句話評語"}，四個指標都要（句子完整、標點符號、用詞、內容）]。'].join('\\n')
          : scoring === '六級分'
          ? ['用四向度六級分評分，期待值以同年段學生為準。各級描述如下（請照這份規準判斷，不要用你記得的其他版本）：',
             esRubricPrompt(esBand($('esGrade').value)),
             'grade 欄填整體「N級分」；回傳 "dimensions":[{"name":"立意取材","level":1到6,"note":"一句話評語"}，四個向度都要（立意取材、結構組織、遣詞造句、錯別字・格式・標點）]。'].join('\\n')''')
rep('''        '5. 評語 comment 固定三條、以正向為原則：praise 兩條（具體引用孩子寫得好的地方，不要空泛）、improve 一條（最值得下次努力的一個方向，語氣溫暖）。',''', '''        '5. 評語 comment 固定三條、以正向為原則：praise 兩條（具體引用孩子寫得好的地方，不要空泛）、improve 一條（最值得下次努力的一個方向，語氣溫暖）。',
        '6. homeTip：給家長的一件「在家就能做」的小練習（一句話，具體、不用買東西，例：吃晚餐時請孩子說說今天最開心的一件事，練習把經過說完整）。',''')
rep('''"structure":"整篇結構與內容的一段建議","comment":{"praise":["",""],"improve":""}}\'''', '''"structure":"整篇結構與內容的一段建議","comment":{"praise":["",""],"improve":""},"homeTip":""}\'''')

# 結果：向度表依年段顯示、印規準表、可編輯、確認後才能列印、存紀錄
rep('''        const dimensionRows = (data.dimensions || []).map(d => `<tr>
          <td style="border:1px solid #999;padding:5px;font-weight:700">${escapeHtml(d.name || '')}</td>
          <td style="border:1px solid #999;padding:5px;text-align:center;font-weight:900;color:#a33">${escapeHtml(String(d.level || ''))} 級</td>''', '''        const band = scoring === '六級分' ? esBand($('esGrade').value) : '';
        const dimensionRows = (data.dimensions || []).map(d => `<tr>
          <td style="border:1px solid #999;padding:5px;font-weight:700">${escapeHtml(d.name || '')}</td>
          <td style="border:1px solid #999;padding:5px;text-align:center;font-weight:900;color:#a33">${band === 'low' ? '⭐'.repeat(Math.max(1, Math.min(3, parseInt(d.level, 10) || 1))) : escapeHtml(String(d.level || '')) + ' 級'}</td>''')
rep('''        const dimensionTable = dimensionRows ? `<div class="ws-section">📐 四向度評分（會考寫作規準・依年級調整）</div>
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:120px">向度</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:70px">級分</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">說明</th></tr>''', '''        const dimensionTable = dimensionRows ? `<div class="ws-section">📐 ${band === 'low' ? '看圖寫話四指標' : '四向度評分（' + (ES_RUBRICS[band] || ES_RUBRICS.high).label + '規準）'}</div>
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:120px">${band === 'low' ? '指標' : '向度'}</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:70px">${band === 'low' ? '星等' : '級分'}</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">說明</th></tr>''')
rep('''          <div class="ws-meta"><span>題目：${escapeHtml($('esTopic').value.trim() || '＿＿＿＿＿')}</span><span>班級：＿＿＿</span><span>座號：＿＿＿</span><span>約 ${escapeHtml(String(data.wordCount || '—'))} 字</span></div>''', '''          <div class="ws-meta"><span>題目：${escapeHtml($('esTopic').value.trim() || '＿＿＿＿＿')}</span><span>班級：＿＿＿</span><span>座號：${escapeHtml($('esSeat').value.trim() || '＿＿＿')}</span><span>約 ${escapeHtml(String(data.wordCount || '—'))} 字</span></div>''')
rep('''          <p style="text-align:right;font-size:14px;margin-top:14px">老師簽名：＿＿＿＿＿＿＿＿</p>
        </div>`;
        $('esMeta').textContent = '請老師確認內容後列印，可夾回學生作文本。';
        showToast('✍️ 批改完成，請老師過目！');''', '''          ${band ? esRubricTableHtml(band) : ''}
          <p style="text-align:right;font-size:14px;margin-top:14px">老師簽名：＿＿＿＿＿＿＿＿</p>
        </div>`;
        esOnResult(data, band);
        showToast('✍️ 批改完成，請老師過目！');''')

# 確認／編輯／紀錄／家長版／統計
TAIL = r'''
    // ---- 批改單 v2：老師可直接改字；勾「老師已確認」才開放列印、才存進紀錄 ----
    const ES_REC_KEY = 'studio_essay_records_v1';
    let esCurrent = null;
    function esRecords() { try { const a = JSON.parse(localStorage.getItem(ES_REC_KEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
    function esSaveRecords(list) { try { localStorage.setItem(ES_REC_KEY, JSON.stringify(list.slice(-300))); } catch (e) { showToast('批改紀錄存不下（這台電腦空間不足）。', true); } }
    function esSetConfirmed(on) {
      $('esConfirm').checked = on;
      $('esConfirmLabel').classList.toggle('ok', on);
      document.querySelectorAll('.es-out').forEach(b => { b.disabled = !on; b.title = on ? '' : '請先勾「老師已確認內容」'; });
    }
    function esOnResult(data, band) {
      const sheet = $('esPreview').querySelector('.sheet');
      sheet.setAttribute('contenteditable', 'true');
      sheet.setAttribute('spellcheck', 'false');
      esCurrent = { id: 'e' + Date.now().toString(36), ts: Date.now(), date: new Date().toLocaleDateString('zh-TW'), grade: $('esGrade').value, band,
        topic: $('esTopic').value.trim(), seat: $('esSeat').value.trim(), scoring: $('esScoring').value, result: String(data.grade || ''),
        dims: (data.dimensions || []).map(d => ({ name: String(d.name || ''), level: parseInt(d.level, 10) || 0 })),
        counts: Object.fromEntries(Object.keys(ES_CATEGORY_COLORS).map(k => [k, (data.corrections || []).filter(c => c.category === k).length])),
        wrong: (data.corrections || []).filter(c => c.category === '錯字' && c.original).slice(0, 30).map(c => [String(c.original).slice(0, 8), String(c.corrected || '').slice(0, 8)]),
        improve: String((data.comment || {}).improve || ''), praise: ((data.comment || {}).praise || []).slice(0, 2).map(String), homeTip: String(data.homeTip || ''),
        data: $('esKeepText').checked ? data : Object.assign({}, data, { paragraphs: [] }) };
      $('esConfirmLabel').hidden = false;
      $('esParentButton').hidden = false;
      esSetConfirmed(false);
      $('esMeta').textContent = '可以直接點批改單改字（分數、評語都能改），改好勾「老師已確認內容」才能列印，也會存進批改紀錄。';
    }
    $('esConfirm').addEventListener('change', () => {
      const on = $('esConfirm').checked;
      esSetConfirmed(on);
      if (!on || !esCurrent) return;
      // 老師改過的整體分數（右上角印章）寫回紀錄
      const badge = $('esPreview').querySelector('.sheet > div[style*="rotate(8deg)"]');
      if (badge) esCurrent.result = badge.textContent.trim() || esCurrent.result;
      const list = esRecords().filter(r => r.id !== esCurrent.id);
      list.push(esCurrent);
      esSaveRecords(list);
      esRenderRecords();
      showToast('已確認，存進批改紀錄。');
    });
    function esRenderRecords() {
      const list = esRecords().slice().reverse();
      $('esRecordList').innerHTML = list.length ? list.slice(0, 12).map(r => `<div class="es-rec">
          <span><b>${escapeHtml(r.seat ? r.seat + '號' : '—')}</b>・${escapeHtml(r.topic || '（沒填題目）')}・${escapeHtml(r.result || '')}<br><span style="color:#888">${escapeHtml(r.date)}・${escapeHtml(r.grade)}年級</span></span>
          <span><button class="mini" type="button" data-es-open="${r.id}">開啟</button> <button class="mini" type="button" data-es-del="${r.id}">刪除</button></span>
        </div>`).join('') + (list.length > 12 ? `<div style="font-size:12px;color:#888;margin-top:4px">只列最近 12 筆，共 ${list.length} 筆（統計會用全部）</div>` : '')
        : '<div style="font-size:12.5px;color:#888">還沒有紀錄。批改完勾「老師已確認內容」就會存進來。</div>';
    }
    $('esRecordList').addEventListener('click', event => {
      const del = event.target.closest('[data-es-del]');
      const open = event.target.closest('[data-es-open]');
      if (del) {
        if (!window.confirm('刪除這筆批改紀錄？')) return;
        esSaveRecords(esRecords().filter(r => r.id !== del.dataset.esDel)); esRenderRecords();
      } else if (open) {
        const r = esRecords().find(x => x.id === open.dataset.esOpen);
        if (!r) return;
        $('esPreview').innerHTML = `<div class="sheet"><div class="ws-head"><div class="ws-title">作文批改紀錄</div></div>
          <div class="ws-meta"><span>題目：${escapeHtml(r.topic || '—')}</span><span>座號：${escapeHtml(r.seat || '—')}</span><span>${escapeHtml(r.date)}</span><span>結果：${escapeHtml(r.result)}</span></div>
          ${r.dims.length ? `<div class="ws-section">📐 ${r.band === 'low' ? '四指標' : '四向度'}</div><ul style="font-size:15px;margin-left:2em">${r.dims.map(d => `<li>${escapeHtml(d.name)}：${r.band === 'low' ? '⭐'.repeat(Math.max(1, d.level)) : d.level + ' 級'}</li>`).join('')}</ul>` : ''}
          ${r.data && (r.data.paragraphs || []).length ? essayMarkupHtml(r.data) : `<div class="ws-section">✏️ 修改類別</div><p style="font-size:15px">${Object.entries(r.counts).map(([k, v]) => `${k} ${v}`).join('、')}（沒有保存原文）</p>`}
          <div class="ws-section">💬 老師的話</div><div style="font-size:15px">${r.praise.map(t => `⭐ ${escapeHtml(t)}`).join('<br>')}${r.improve ? `<br>🌱 ${escapeHtml(r.improve)}` : ''}</div>
          ${r.band ? esRubricTableHtml(r.band) : ''}</div>`;
        esCurrent = r;
        $('esConfirmLabel').hidden = false; $('esParentButton').hidden = false; esSetConfirmed(true);
      }
    });
    esRenderRecords();
    document.querySelectorAll('.es-out').forEach(b => { b.disabled = true; b.title = '先批改一篇作文'; });

    // 家長版說明：本機用批改結果組一段白話，先在框裡預覽、可改，再複製（不呼叫 AI、不含姓名）
    const ES_LEVEL_MEANING = { 6: '非常優秀', 5: '表現精采', 4: '達到年段的基本要求', 3: '大致可以，但還不夠充分', 2: '還需要多練習', 1: '需要老師和家長一起陪伴練習' };
    function esParentText(r) {
      const n = parseInt(String(r.result).replace(/[^0-9]/g, ''), 10);
      const stars = (String(r.result).match(/⭐/g) || []).length;
      const meaning = r.band === 'low' ? (stars >= 3 ? '每一項都做得很好' : stars === 2 ? '大部分都做到了' : '還在學習中') : (ES_LEVEL_MEANING[n] || '');
      return [`【${r.topic || '作文'}】回饋`,
        `這次的表現：${r.result}${meaning ? `（${meaning}）` : ''}。`,
        r.praise.length ? `做得好的地方：${r.praise.join('；')}` : '',
        r.improve ? `下一步可以加油的地方：${r.improve}` : '',
        r.homeTip ? `在家可以一起做的小練習：${r.homeTip}` : '',
        '（AI 協助草擬，老師已確認）'].filter(Boolean).join('\n');
    }
    $('esParentButton').addEventListener('click', () => {
      if (!esCurrent) return;
      const host = document.createElement('div');
      host.className = 'sheet';
      host.style.minHeight = '0';
      host.innerHTML = `<div class="ws-section">👪 家長版說明（先看一遍、可以直接改，確認沒有孩子姓名再複製）</div>
        <textarea class="es-parent" id="esParentText">${escapeHtml(esParentText(esCurrent))}</textarea>
        <div style="display:flex;gap:8px;margin-top:8px"><button class="mini" type="button" id="esParentCopy">📋 複製</button><button class="mini" type="button" id="esParentBack">↩ 回批改單</button></div>`;
      const keep = $('esPreview').innerHTML;
      $('esPreview').innerHTML = '';
      $('esPreview').appendChild(host);
      $('esParentCopy').onclick = async () => {
        const text = $('esParentText').value;
        if (/[一-鿿]{2,3}(同學|小朋友)/.test(text) && !window.confirm('內容好像有姓名稱呼，確定要複製？')) return;
        try { await navigator.clipboard.writeText(text); showToast('已複製，可以貼到 LINE 或聯絡本。'); } catch (e) { $('esParentText').select(); document.execCommand('copy'); showToast('已複製。'); }
      };
      $('esParentBack').onclick = () => { $('esPreview').innerHTML = keep; const sheet = $('esPreview').querySelector('.sheet'); if (sheet && esCurrent && !esCurrent.data) sheet.removeAttribute('contenteditable'); };
    });

    $('esRubricButton').addEventListener('click', () => {
      $('esPreview').innerHTML = `<div class="sheet">${['low', 'mid', 'high'].map(esRubricTableHtml).join('<div style="height:18px"></div>')}</div>`;
      $('esConfirmLabel').hidden = true; $('esParentButton').hidden = true;
      document.querySelectorAll('.es-out').forEach(b => { b.disabled = false; b.title = ''; });
    });

    // 全班共通問題統計（同題目 ≥3 篇）：本機計算，沒有姓名，可印成回饋課一頁講義
    const ES_TEACH_TIPS = {
      '錯字': '挑出全班最常錯的字，用「部件拆解＋造詞」帶一次，下次作文前先複習這張字表。',
      '標點': '用一段沒有標點的短文，全班一起加上逗號、句號、引號，再對照原文。',
      '用字': '把用錯的字放在句子裡比較（例：再／在、的／得），讓孩子說出差別。',
      '語詞': '收集「更精準的說法」：把「很好玩」換成具體的感受或動作，建立班級語詞牆。',
      '語句': '示範把一個太長或不通的句子拆成兩句，再請孩子改自己作文裡的一句。'
    };
    $('esStatsButton').addEventListener('click', () => {
      const topic = $('esTopic').value.trim();
      const all = esRecords();
      const topics = [...new Set(all.map(r => r.topic).filter(Boolean))];
      const use = topic || topics[topics.length - 1] || '';
      const recs = all.filter(r => r.topic === use);
      if (recs.length < 3) return showToast(use ? `「${use}」只有 ${recs.length} 篇紀錄，至少 3 篇才做全班統計。` : '還沒有批改紀錄。', true);
      const cats = Object.keys(ES_CATEGORY_COLORS).map(k => [k, recs.reduce((s, r) => s + (r.counts[k] || 0), 0)]).sort((a, b) => b[1] - a[1]);
      const totalMarks = cats.reduce((s, [, v]) => s + v, 0) || 1;
      const dimNames = [...new Set(recs.flatMap(r => r.dims.map(d => d.name)))];
      const dimAvg = dimNames.map(n => { const v = recs.flatMap(r => r.dims.filter(d => d.name === n && d.level).map(d => d.level)); return [n, v.length ? (v.reduce((a, b) => a + b, 0) / v.length) : 0]; });
      const wrongMap = new Map();
      recs.forEach(r => (r.wrong || []).forEach(([o, c]) => { const k = o + '→' + c; wrongMap.set(k, (wrongMap.get(k) || 0) + 1); }));
      const wrongTop = [...wrongMap.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
      const weakDim = dimAvg.slice().sort((a, b) => a[1] - b[1])[0];
      const tips = cats.filter(([, v]) => v).slice(0, 2).map(([k]) => ES_TEACH_TIPS[k]);
      if (weakDim) tips.push(`全班「${weakDim[0]}」平均最低（${weakDim[1].toFixed(1)}），下一次作文前先用一節課示範這個向度的好例子與待改例子。`);
      const bar = (v, max, color) => `<span style="display:inline-block;height:12px;width:${Math.round(v / max * 220)}px;background:${color};border-radius:6px;vertical-align:-1px"></span>`;
      const maxCat = Math.max(1, ...cats.map(([, v]) => v));
      const lowBand = recs.every(r => r.band === 'low');
      $('esPreview').innerHTML = `<div class="sheet">
        <div class="ws-head"><div class="ws-title">全班作文回饋課：${escapeHtml(use)}</div></div>
        <div class="ws-meta"><span>共 ${recs.length} 篇</span><span>${escapeHtml(recs[0].grade)}年級</span><span>${new Date().toLocaleDateString('zh-TW')}</span></div>
        <div class="ws-section">✏️ 大家最常要修改的地方（共 ${totalMarks} 處）</div>
        <table style="width:100%;font-size:14.5px">${cats.map(([k, v]) => `<tr><td style="width:60px;font-weight:800;color:${ES_CATEGORY_COLORS[k]}">${k}</td><td>${bar(v, maxCat, ES_CATEGORY_COLORS[k])} ${v} 處（${Math.round(v / totalMarks * 100)}%）</td></tr>`).join('')}</table>
        ${dimAvg.length ? `<div class="ws-section">📐 ${lowBand ? '四指標平均星等' : '四向度平均級分'}</div>
        <table style="width:100%;font-size:14.5px">${dimAvg.map(([n, v]) => `<tr><td style="width:150px;font-weight:800">${escapeHtml(n)}</td><td>${bar(v, lowBand ? 3 : 6, '#3f8f6b')} ${v.toFixed(1)}</td></tr>`).join('')}</table>` : ''}
        ${wrongTop.length ? `<div class="ws-section">🔤 全班常見錯字（前 ${wrongTop.length} 個）</div>
        <table style="width:100%;border-collapse:collapse;font-size:15px"><tr><th style="border:1px solid #999;padding:4px;background:#f3f3f3">寫成</th><th style="border:1px solid #999;padding:4px;background:#f3f3f3">正確</th><th style="border:1px solid #999;padding:4px;background:#f3f3f3">幾篇出現</th></tr>
        ${wrongTop.map(([k, n]) => { const [o, c] = k.split('→'); return `<tr><td style="border:1px solid #999;padding:4px;color:#d32f2f;text-decoration:line-through">${escapeHtml(o)}</td><td style="border:1px solid #999;padding:4px;font-weight:900">${escapeHtml(c)}</td><td style="border:1px solid #999;padding:4px;text-align:center">${n}</td></tr>`; }).join('')}</table>` : ''}
        <div class="ws-section">🧑‍🏫 回饋課可以這樣上</div>
        <ol style="font-size:15px;margin-left:2em">${tips.map(t => `<li style="margin:4px 0">${escapeHtml(t)}</li>`).join('')}</ol>
        <p style="font-size:11px;color:#888">統計只用這台電腦的批改紀錄（座號、級分、錯誤類別），不含學生姓名。</p></div>`;
      $('esConfirmLabel').hidden = true; $('esParentButton').hidden = true;
      document.querySelectorAll('.es-out').forEach(b => { b.disabled = false; b.title = ''; });
    });
'''
rep('''    // ============================================================
    // 📋 Google 表單產生器（經老師自己的 GAS 建立）''', TAIL + '''
    // ============================================================
    // 📋 Google 表單產生器（經老師自己的 GAS 建立）''')

path.write_text(s, encoding='utf-8')
print('ok', len(s))
