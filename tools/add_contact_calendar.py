"""大屏聯絡本日曆（老師 2026-11-04「可以查看聯絡本，用日曆方式檢視，點了有詳細的資料」）
- 點「今日聯絡本」打開月曆：有寫的日子會亮、顯示開頭幾個字；點某一天看全文、更新時間與來源，可複製
- 唯讀，不能改過去的內容；今天的編輯仍在黑板上
- LineBot.gs 新增 contactbook_month：大屏金鑰只讀得到今天以前（老師預先寫好的未來內容教室端看不到），老師金鑰全部看得到
python tools/add_contact_calendar.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def patch(name, pairs):
    path = root / name
    s = path.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, s.count(old), old[:80])
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')


# ---------- 雲端 ----------
patch('LineBot.gs', [
    ("""  // 教室金鑰權限受限：只能回報與讀取「當日」的點名與作業；歷史查詢需要老師金鑰。""", """  // 教室金鑰權限受限：只能回報與讀取「當日」的點名與作業；歷史查詢需要老師金鑰。聯絡本例外：可以看今天以前（contactbook_month，唯讀），看不到未來。"""),
    ("""'contactbook_get', 'contactbook_save', 'prompt_get']""", """'contactbook_get', 'contactbook_save', 'contactbook_month', 'prompt_get']"""),
    ("""    if (action === 'contactbook_list') {""", """    if (action === 'contactbook_month') return lineBotJson_(monthContactBook_(body, isTeacher));
    if (action === 'contactbook_list') {"""),
    ("""/** 老師金鑰限定：聯絡本歷史清單（近 limit 筆，新到舊，含內容預覽）。 */""", """/** 聯絡本月曆：某個月有內容的每一天（全文）。大屏金鑰只看得到今天以前，老師預先寫好的未來內容只有老師金鑰看得到。 */
function monthContactBook_(body, isTeacher) {
  var month = String(body.month || '');
  if (!/^\\d{4}-\\d{2}$/.test(month)) throw new Error('月份格式不正確');
  var today = lineBotToday_();
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.contactbook.getLastRow();
  if (lastRow <= 1) return { ok: true, month: month, entries: [] };
  var values = sheets.contactbook.getRange(2, 1, lastRow - 1, 5).getValues();
  var entries = values.map(function (row) {
    return {
      date: row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]),
      text: String(row[2] || '').slice(0, 5000),
      updatedAt: row[3] instanceof Date ? row[3].toISOString() : String(row[3] || ''),
      source: String(row[4] || '')
    };
  }).filter(function (entry) {
    return entry.date.indexOf(month + '-') === 0 && entry.text.trim() && (isTeacher || entry.date <= today);
  }).sort(function (a, b) { return a.date.localeCompare(b.date); });
  return { ok: true, month: month, entries: entries };
}

/** 老師金鑰限定：聯絡本歷史清單（近 limit 筆，新到舊，含內容預覽）。 */"""),
    ("""var BOT_VERSION = '2026-11-01 14:30';""", """var BOT_VERSION = '2026-11-04 23:30';"""),
])

# ---------- 大屏 ----------
patch('Morning.html', [
    ("""    /* ===== 全螢幕備援：瀏覽器不給真全螢幕時，鋪滿整個分頁 ===== */""", """    /* ===== 聯絡本日曆 ===== */
    .contact-title { border: 0; background: none; font: inherit; font-size: 18px; font-weight: 900; color: var(--primary-strong); display: inline-flex; align-items: center; gap: 6px; padding: 3px 8px 3px 2px; border-radius: 10px; cursor: pointer; }
    .contact-title:hover { background: var(--ok-soft); }
    .contact-title small { font-size: 13px; font-weight: 800; color: var(--muted); border: 1.5px solid var(--line); border-radius: 999px; padding: 1px 8px; background: var(--surface); }
    .ccal-pop { position: fixed; inset: 0; z-index: 99980; display: flex; align-items: center; justify-content: center; background: rgba(20, 36, 32, .45); }
    .ccal-pop[hidden] { display: none !important; }
    .ccal-card { width: min(1240px, 95vw); height: min(90vh, 860px); display: flex; flex-direction: column; gap: 10px; padding: 16px 20px; border-radius: 24px; background: var(--surface); border: 3px solid var(--line); box-shadow: 0 30px 60px -20px rgba(0,0,0,.45); }
    .ccal-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .ccal-head h2 { margin: 0 8px 0 0; font-size: 22px; color: var(--primary-strong); }
    .ccal-month { min-width: 150px; text-align: center; font-size: 22px; font-weight: 900; }
    .ccal-close { margin-left: auto; }
    .ccal-note { font-size: 14px; font-weight: 700; color: var(--muted); }
    .ccal-note.bad { color: var(--missing); }
    .ccal-body { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 16px; }
    .ccal-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); grid-template-rows: auto; grid-auto-rows: 1fr; gap: 5px; min-height: 0; }
    .ccal-week { font-size: 14px; font-weight: 900; color: var(--muted); text-align: center; align-self: center; }
    .ccal-day { min-width: 0; min-height: 0; overflow: hidden; display: flex; flex-direction: column; gap: 2px; text-align: left; border: 2px solid var(--line); border-radius: 10px; background: var(--surface); color: var(--ink); padding: 4px 6px; font-family: inherit; cursor: pointer; }
    .ccal-day b { font-size: 16px; font-weight: 900; }
    .ccal-day span { font-size: 12px; font-weight: 700; line-height: 1.25; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .ccal-day.has { background: var(--ok-soft); border-color: var(--ok); }
    .ccal-day.today b { color: var(--primary-strong); text-decoration: underline; text-underline-offset: 3px; }
    .ccal-day.sel { background: var(--primary-strong); border-color: var(--primary-strong); color: #fff; }
    .ccal-day.sel b { color: #fff; }
    .ccal-day:disabled { opacity: .4; cursor: default; }
    .ccal-blank { min-height: 0; }
    .ccal-detail { min-height: 0; display: flex; flex-direction: column; gap: 8px; }
    .ccal-detail-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .ccal-detail-head strong { font-size: 20px; }
    .ccal-detail-head .ghost-button { margin-left: auto; padding: 6px 14px; }
    .ccal-board { flex: 1; min-height: 0; overflow: auto; background: #2e4a3d; color: #f4f1e6; border: 8px solid #8a5f38; border-radius: 12px; padding: 12px 16px; }
    .ccal-board .chalk-content { font-size: 22px !important; }
    .ccal-meta { font-size: 13px; font-weight: 700; color: var(--muted); min-height: 1.3em; }
    @media (max-width: 820px) { .ccal-body { grid-template-columns: 1fr; grid-template-rows: minmax(0, 1.1fr) minmax(0, 1fr); } .ccal-day span { display: none; } }
    html[data-board-style="cozy"] .ccal-card { border-color: var(--cozy-wood); border-radius: 32px; box-shadow: 0 8px 0 var(--cozy-wood), 0 30px 60px -20px rgba(91,70,54,.45); }
    html[data-board-style="cozy"] .ccal-day { border-radius: 14px; }
    /* ===== 全螢幕備援：瀏覽器不給真全螢幕時，鋪滿整個分頁 ===== */"""),
    ("""<strong style="font-size:18px;color:var(--primary-strong);display:inline-flex;align-items:center;gap:6px"><img class="tab-icon" data-icon="contact_book\"""",
     """<button class="contact-title" type="button" id="contactCalButton" title="打開聯絡本日曆"><img class="tab-icon" data-icon="contact_book\""""),
    ("""alt="">今日聯絡本</strong>""", """alt="">今日聯絡本 <small>📅 日曆</small></button>"""),
    ("""  <div class="cd-pop" id="cdPop" role="dialog" aria-label="倒數計時" hidden>""", """  <div class="ccal-pop" id="ccalPop" role="dialog" aria-label="聯絡本日曆" hidden>
    <div class="ccal-card">
      <div class="ccal-head">
        <h2>📅 聯絡本日曆</h2>
        <button class="ghost-button" type="button" id="ccalPrev">‹ 上個月</button>
        <span class="ccal-month" id="ccalMonth"></span>
        <button class="ghost-button" type="button" id="ccalNext">下個月 ›</button>
        <button class="ghost-button" type="button" id="ccalToday">回今天</button>
        <button class="ghost-button ccal-close" type="button" id="ccalClose">✕ 關閉（Esc）</button>
      </div>
      <div class="ccal-note" id="ccalNote"></div>
      <div class="ccal-body">
        <div class="ccal-grid" id="ccalGrid"></div>
        <div class="ccal-detail">
          <div class="ccal-detail-head"><strong id="ccalDate"></strong><button class="ghost-button" type="button" id="ccalCopy">📋 複製這天</button></div>
          <div class="ccal-board" id="ccalBoard"></div>
          <div class="ccal-meta" id="ccalMeta"></div>
        </div>
      </div>
    </div>
  </div>
  <div class="cd-pop" id="cdPop" role="dialog" aria-label="倒數計時" hidden>"""),
    # 複製抽成共用
    ("""      const full = `${header}\\n${text}`;
      let copied = false;
      try {""", """      const full = `${header}\\n${text}`;
      const copied = await copyText(full);
      showToast(copied ? '已複製！可直接貼到家長群組。' : '複製失敗，請手動選取內容複製。', !copied);
    }
    async function copyText(full) {
      let copied = false;
      try {"""),
    ("""        try { copied = document.execCommand('copy'); } catch (error2) { copied = false; }
        helper.remove();
      }
      showToast(copied ? '已複製！可直接貼到家長群組。' : '複製失敗，請手動選取內容複製。', !copied);
    }
""", """        try { copied = document.execCommand('copy'); } catch (error2) { copied = false; }
        helper.remove();
      }
      return copied;
    }

    // ---------- 聯絡本日曆：點「今日聯絡本」打開，點某一天看全文（唯讀，今天的編輯在黑板上） ----------
    const ccal = { month: '', sel: '', cache: {}, loading: false, error: '' };
    const ccalPad = n => String(n).padStart(2, '0');
    const ccalWeek = ['日', '一', '二', '三', '四', '五', '六'];
    const CCAL_SOURCE = { teacher: '工作台輸入', classroom: '教室輸入', line: 'LINE 輸入' };
    async function ccalFetch(month) {
      if (!state.settings.gasUrl || !state.settings.classroomToken) throw new Error('要先在「設定」填雲端網址和教室大屏金鑰，才看得到以前的聯絡本。');
      const result = await callGas({ action: 'contactbook_month', token: state.settings.classroomToken, className: state.settings.className, month });
      return result.entries || [];
    }
    // 今天的內容以黑板上最新的為準
    function ccalEntry(date) {
      if (date === todayKey() && state.contact.text.trim()) return { date, text: state.contact.text, updatedAt: state.contact.updatedAt, source: state.contact.source };
      return (ccal.cache[date.slice(0, 7)] || {})[date] || null;
    }
    function ccalRender() {
      const today = todayKey(), thisMonth = today.slice(0, 7);
      const [y, m] = ccal.month.split('-').map(Number);
      $('ccalMonth').textContent = `${y} 年 ${m} 月`;
      $('ccalNext').disabled = ccal.month >= thisMonth;
      $('ccalNote').className = ccal.error ? 'ccal-note bad' : 'ccal-note';
      $('ccalNote').textContent = ccal.loading ? '讀取中…' : ccal.error || '綠色的日子有寫聯絡本，點一下看內容。這裡只能看，不能改。';
      const first = new Date(y, m - 1, 1).getDay(), days = new Date(y, m, 0).getDate();
      const cells = ccalWeek.map(w => `<div class="ccal-week">${w}</div>`);
      for (let i = 0; i < first; i += 1) cells.push('<div class="ccal-blank"></div>');
      for (let d = 1; d <= days; d += 1) {
        const date = `${ccal.month}-${ccalPad(d)}`;
        const entry = ccalEntry(date);
        const cls = [entry ? 'has' : '', date === today ? 'today' : '', date === ccal.sel ? 'sel' : ''].filter(Boolean).join(' ');
        const snippet = entry ? entry.text.trim().split('\\n')[0].slice(0, 16) : '';
        cells.push(`<button class="ccal-day ${cls}" type="button" data-ccal-day="${date}"${date > today ? ' disabled' : ''}><b>${d}</b>${snippet ? `<span>${escapeHtml(snippet)}</span>` : ''}</button>`);
      }
      $('ccalGrid').innerHTML = cells.join('');
      ccalRenderDetail();
    }
    function ccalRenderDetail() {
      const [y, m, d] = ccal.sel.split('-').map(Number);
      const entry = ccalEntry(ccal.sel);
      $('ccalDate').textContent = `${y} 年 ${m} 月 ${d} 日（週${ccalWeek[new Date(y, m - 1, d).getDay()]}）`;
      $('ccalCopy').hidden = !entry;
      // 字體跟黑板一樣（低年級可能選注音字型）
      const font = CONTACT_FONTS.includes(state.settings.contactFont) ? state.settings.contactFont : 'default';
      $('ccalBoard').className = `ccal-board chalk-${font}`;
      $('ccalBoard').innerHTML = entry
        ? `<div class="chalk-content">${escapeHtml(entry.text)}</div>`
        : `<span class="chalk-empty">${ccal.loading ? '讀取中…' : '這一天沒有聯絡本內容。'}</span>`;
      const time = entry && entry.updatedAt ? new Date(entry.updatedAt) : null;
      const validTime = time && !Number.isNaN(time.getTime());
      const source = entry ? CCAL_SOURCE[entry.source] : '';
      $('ccalMeta').textContent = entry && (validTime || source)
        ? [validTime ? `最後更新 ${time.getMonth() + 1}/${time.getDate()} ${ccalPad(time.getHours())}:${ccalPad(time.getMinutes())}` : '', source ? `（${source}）` : ''].join('')
        : '';
    }
    async function ccalLoad(month, force) {
      ccal.month = month;
      ccal.error = '';
      if (ccal.cache[month] && !force) { ccal.loading = false; ccalRender(); return; }
      ccal.loading = true;
      ccalRender();
      try {
        const entries = await ccalFetch(month);
        ccal.cache[month] = Object.fromEntries(entries.map(entry => [entry.date, entry]));
      } catch (error) {
        const message = String((error && error.message) || '');
        if (ccal.month === month) ccal.error = error.name === 'AbortError' ? '雲端太久沒回應，請再試一次。' : /權限不足/.test(message) ? '雲端的 LINE 小幫手要更新成新版（或教室大屏金鑰不對），才看得到以前的聯絡本。' : message || '讀取失敗，請再試一次。';
      }
      if (ccal.month === month) { ccal.loading = false; ccalRender(); }
    }
    function ccalShift(delta) {
      const [y, m] = ccal.month.split('-').map(Number);
      const when = new Date(y, m - 1 + delta, 1);
      const month = `${when.getFullYear()}-${ccalPad(when.getMonth() + 1)}`;
      const today = todayKey();
      const last = new Date(when.getFullYear(), when.getMonth() + 1, 0).getDate();
      ccal.sel = month === today.slice(0, 7) ? today : `${month}-${ccalPad(last)}`;
      ccalLoad(month).then(() => {
        // 以前的月份：選那個月最後一天有寫的
        const dates = Object.keys(ccal.cache[month] || {}).sort();
        if (ccal.month === month && month !== today.slice(0, 7) && dates.length) { ccal.sel = dates[dates.length - 1]; ccalRender(); }
      });
    }
    function ccalOpen() {
      const today = todayKey();
      ccal.sel = today;
      $('ccalPop').hidden = false;
      ccalLoad(today.slice(0, 7), true);
    }
"""),
    ("""    $('contactCopyButton').addEventListener('click', copyContactBookText);""", """    $('contactCopyButton').addEventListener('click', copyContactBookText);
    $('contactCalButton').addEventListener('click', ccalOpen);
    $('ccalClose').addEventListener('click', () => { $('ccalPop').hidden = true; });
    $('ccalPop').addEventListener('click', event => { if (event.target === $('ccalPop')) $('ccalPop').hidden = true; });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && !$('ccalPop').hidden) $('ccalPop').hidden = true; });
    $('ccalPrev').addEventListener('click', () => ccalShift(-1));
    $('ccalNext').addEventListener('click', () => ccalShift(1));
    $('ccalToday').addEventListener('click', () => { ccal.sel = todayKey(); ccalLoad(ccal.sel.slice(0, 7)); });
    $('ccalGrid').addEventListener('click', event => {
      const day = event.target.closest('[data-ccal-day]');
      if (!day || day.disabled) return;
      ccal.sel = day.dataset.ccalDay;
      ccalRender();
    });
    $('ccalCopy').addEventListener('click', async () => {
      const entry = ccalEntry(ccal.sel);
      if (!entry) return;
      const [, m, d] = ccal.sel.split('-').map(Number);
      const weekday = ccalWeek[new Date(ccal.sel + 'T00:00:00').getDay()];
      const copied = await copyText(`【${state.settings.className ? state.settings.className + ' ' : ''}聯絡本】${m}/${d}（週${weekday}）\\n${entry.text.trim()}`);
      showToast(copied ? '已複製這一天的聯絡本。' : '複製失敗，請手動選取內容複製。', !copied);
    });"""),
])
print('ok')
