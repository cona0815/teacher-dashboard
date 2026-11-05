"""2026-11-05 老師研習要用：把系統分成五級，金鑰與網址依「先用到先命名」改代號，教學照五級重排。
一次性腳本（跑過一次就不再用）。程式內部的設定欄位與指令碼屬性名稱一律不動，已在用的老師資料不受影響。
舊 → 新：🌐→🌐A  🔑D→🔑B  🔑C→🔑C  🔑E→🔑D  🔑A→🔑E  🔑B→🔑F  userId→👤G
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = {'A': 'E', 'B': 'F', 'C': 'C', 'D': 'B', 'E': 'D'}
LEVEL = {'1': '2', '2': '3', '3': '4'}
COLOR = {'1': '🔵', '2': '🟡', '3': '🟠'}
ANCHOR = {'tier1': 'level2', 'tier2': 'level3', 'tier3': 'level4', 'part1': 'level2', 'part2': 'level2', 'part3': 'level1', 'pet': 'level5'}


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


def write(name, text):
    (ROOT / name).write_text(text, encoding='utf-8', newline='\n')


def rep(text, old, new, count=1):
    assert text.count(old) >= 1 and (count == 0 or text.count(old) == count), (old[:70], text.count(old))
    return text.replace(old, new)


def map_keys(text):
    return re.sub(r'🔑([A-E])', lambda m: '🔑' + KEY[m.group(1)], text)


def map_globe(text):
    text = text.replace('help-emoji">🌐<', 'help-emoji">@@GLOBE@@<').replace("'🌐 網頁'", "'@@GLOBE@@ 網頁'")
    text = re.sub(r'🌐(?!A)', '🌐A', text)
    return text.replace('@@GLOBE@@', '🌐')


def map_levels(text):
    # 後面接中文時不留空白（「難度 1 完全不用」→「第 2 級完全不用」）
    return re.sub(r'(🟢 |🟡 |🔴 )?難度 ?([123])(?: (?=[一-鿿（]))?',
                  lambda m: (COLOR[m.group(2)] + ' ' if m.group(1) else '') + f'第 {LEVEL[m.group(2)]} 級', text)


def map_install_links(text):
    return re.sub(r'Install\.html#(tier[123]|part3|pet)\b', lambda m: 'Install.html#' + ANCHOR[m.group(1)], text)


# ---------- 只改代號的檔案 ----------
for name in ['SECURITY.md', 'LINE_BOT_SPEC.md', 'desktop_pet_cloud.py', 'desktop_pet_secretary.py', 'desktop_pet_voice.py', 'Studio.html']:
    t = map_keys(read(name))
    if name != 'Studio.html':
        t = map_globe(t)
    write(name, t)

t = map_keys(read('README.md'))
t = rep(t, '## 設計參考聲明', '''## 五級使用路線（教學與命名都照這個順序）

| 級 | 用到什麼 | 要填的代號 |
| --- | --- | --- |
| 第 1 級 | 只有晨間大屏，資料只存這台電腦（不含機敏資料） | 不用填 |
| 第 2 級 | 大屏＋教師工作台，用 GAS 連結 | 🌐A 網址、🔑B 大屏金鑰、🔑C 工作台金鑰 |
| 第 3 級 | 再加 AI 金鑰 | 🔑D Gemini |
| 第 4 級 | 再加 LINE | 🔑E LINE Token、🔑F Webhook 參數、👤G userId |
| 第 5 級 | 再加桌寵小綿助 | 沿用 🌐A、🔑C、🔑D |

新增要老師填的金鑰或網址時，代號接著往後排，不要插隊。

## 設計參考聲明''')
write('README.md', t)

# ---------- 工作台 ----------
t = map_globe(map_keys(read('Index.html')))
t = map_install_links(t)
t = rep(t, '<label for="apiKey">🔑D API 金鑰＝教學裡的「AI 金鑰」　<a href="Install.html#level2"', '<label for="apiKey">🔑D API 金鑰＝教學裡的「AI 金鑰」　<a href="Install.html#level3"')
t = map_levels(t)
write('Index.html', t)

# ---------- 雲端大腦 ----------
t = map_globe(map_keys(read('LineBot.gs')))
t = map_levels(t)
t = rep(t, "var BOT_VERSION = '2026-11-04 23:30';", "var BOT_VERSION = '2026-11-05 10:00';")
start = t.index("    '【第 2 級：雲端大腦】現在就要用這兩把")
end = t.index("  ].join('\\n');", start)
t = t[:start] + """    '【第 2 級：連上大屏和工作台】現在就要用這兩把，抄到記事本：',
    '🔑B 教室大屏金鑰 → 晨間大屏「⚙ 設定」（教室電腦只放這把）',
    '  ' + properties.getProperty('CLASSROOM_TOKEN'),
    '🔑C 工作台同步金鑰 → 工作台「⚙ 設定 → ① 雲端／LINE 小幫手」、小綿助雲端連線',
    '  ' + properties.getProperty('LINE_SYNC_TOKEN'),
    '下一步：擴充功能 → Apps Script → 部署 → 新增部署（網頁應用程式／執行身分：我／存取權：任何人），拿到 🌐A /exec 網址。',
    '',
    '【第 3 級：AI】（選填）要讓 LINE 聽語音、看照片，用選單「④ 填入 Gemini 金鑰」貼 🔑D。',
    '',
    '【第 4 級：LINE 小幫手】做 LINE 時才用，現在先不用管：',
    '🔑F Webhook 驗證參數 → 接在 🌐A 後面：🌐A?hook=🔑F（部署後「📋 安裝總表」的 🔗 列會自動拼好）',
    '  ' + properties.getProperty('LINE_WEBHOOK_TOKEN'),
    'LINE Token（🔑E）用選單「② 填入 LINE Token」，鎖門（👤G）用選單「③ 填入我的 LINE userId」，排程用選單「⑤」。'
""" + t[end:]
t = rep(t, "'① 初始化（第 2 級：建資料表＋產生金鑰）'", "'① 初始化（第 2 級：建資料表＋產生金鑰）'")
t = rep(t, "'③ 填入我的 LINE userId（鎖門，第 4 級）'", "'③ 填入我的 LINE userId（👤G，鎖門，第 4 級）'")
t = rep(t, "'④ 填入 Gemini 金鑰（🔑D，選填）'", "'④ 填入 Gemini 金鑰（🔑D，第 3 級）'")
t = rep(t, "['👤', '（第 4 級）我的 LINE userId'", "['👤G', '（第 4 級）我的 LINE userId'")
# 安裝總表依代號順序列
rows_start = t.index("    ['代號', '這是什麼'")
rows_end = t.index("  ];", rows_start)
rows = t[rows_start:rows_end].rstrip('\n').split('\n')
order = ["'代號'", "'🌐A'", "'🔑B'", "'🔑C'", "'🔑D'", "'🔑E'", "'🔑F'", "'🔗'", "'👤G'", "'ℹ️'"]
picked = [next(r for r in rows if r.strip().startswith('[' + code)) for code in order]
assert len(picked) == len(rows)
picked = [r.rstrip(',') for r in picked]
t = t[:rows_start] + ',\n'.join(picked) + '\n' + t[rows_end:]
start = t.index("    '【第 2 級】🔑C 工作台同步金鑰")
end = t.index("  ].join('\\n'));", start)
t = t[:start] + """    '【第 2 級】🔑B 教室大屏金鑰（晨間大屏「⚙ 設定」）：',
    '  ' + properties.getProperty('CLASSROOM_TOKEN'),
    '',
    '【第 2 級】🔑C 工作台同步金鑰（工作台「① 雲端／LINE 小幫手」、小綿助雲端連線）：',
    '  ' + properties.getProperty('LINE_SYNC_TOKEN'),
    '',
    '【第 4 級】🔑F Webhook 驗證參數（接在 🌐A 後面：?hook=🔑F）：',
    '  ' + properties.getProperty('LINE_WEBHOOK_TOKEN')
""" + t[end:]
write('LineBot.gs', t)

# ---------- 大屏 ----------
t = map_globe(map_keys(read('Morning.html')))
t = map_install_links(t)
lines = t.split('\n')


def take_line(marker):
    i = next(n for n, line in enumerate(lines) if marker in line and 'class="field"' in line)
    return lines.pop(i)


notify1 = take_line('id="setupAutoNotifyTime"')
notify2 = take_line('id="setupAutoHomeworkNotifyTime"')
gas = take_line('id="setupGasUrl"')
room = take_line('id="setupClassroomToken"')
teacher = take_line('id="setupTeacherToken"')
t = '\n'.join(lines)
t = rep(t, """        <button class="primary-button" type="button" id="saveSetupButton\"""", f"""        <details class="level-box" id="setupLevel2">
          <summary>🔵 第 2 級：連上工作台（要在家寫聯絡本、看補交與統計才填）</summary>
          <div class="form-grid">
{gas}
{room}
{teacher}
          </div>
          <p class="note">
            ・「💾 存到雲端」只把資料存進試算表，<strong>不會</strong>推播 LINE；每 5 分鐘與離開頁面時也會自動存一次。<br>
            ・教室金鑰權限受限：只能回報當天、讀取近期缺交、把缺交標成補交；歷史統計需要老師金鑰，別把老師金鑰存在教室電腦。
          </p>
        </details>
        <details class="level-box" id="setupLevel4">
          <summary>🟠 第 4 級：LINE 推播時間（接上 LINE 才有作用）</summary>
          <div class="form-grid">
{notify1}
{notify2}
          </div>
          <p class="note">
            ・LINE 只在兩個時間推播：① 點名推播（出缺，並附上工作台的今日課程、任務、記事與逾期提醒）② 作業推播（點名＋各科繳交）。教室電腦需開著本頁。<br>
            ・可在 Apps Script 另設 sendRollcallReminder 每日觸發器作雲端備援：當天沒回報時 LINE 提醒老師。
          </p>
        </details>
        <button class="primary-button" type="button" id="saveSetupButton\"""")
start = t.index('          ・第一次設定？<a href="Install.html"')
end = t.index('        </p>', start)
t = t[:start] + """          ・第一次設定？<a href="Install.html" target="_blank" rel="noopener"><strong>📖 開啟新手教學</strong></a>（從第 1 級開始，含開機自動開大屏）。<br>
          ・沒有填下面第 2 級的網址和金鑰，就是第 1 級：資料只存在這台電腦，不會上傳。<br>
          ・設定保存在這台電腦的瀏覽器；只使用座號，不輸入學生姓名，聯絡本也請不要寫學生姓名或個資。<br>
          ・點名預設全部未填。遲到界線後點「到校」，大屏顯示「到」，但資料記為遲到。<br>
          ・自動缺席時間一到，仍未填的座號自動轉「未到」。<br>
          ・完整的使用情境教學與資安說明請看 <a href="About.html" target="_blank" rel="noopener">📚 系統說明與資安</a>。
""" + t[end:]
t = rep(t, """    /* ===== 聯絡本日曆 ===== */""", """    /* ===== 第 1 級（只有大屏、沒接雲端）：收起一定要雲端才能用的東西 ===== */
    body.local-only .tab-button[data-page="makeup"], body.local-only .tab-button[data-page="query"],
    body.local-only #submitButton, body.local-only #contactRefreshButton { display: none !important; }
    .level-box { margin-top: 14px; max-width: 1000px; border: 2px solid var(--line); border-radius: 12px; padding: 12px 16px; background: var(--surface); }
    .level-box summary { cursor: pointer; font-size: 17px; font-weight: 800; color: var(--primary-strong); }
    .level-box[open] summary { margin-bottom: 12px; }
    .level-box .note { margin-top: 12px; }
    /* ===== 聯絡本日曆 ===== */""")
t = rep(t, """    function classKeySuffix(cls = currentClass()) {""", """    // 第 2 級的網址和大屏金鑰都填了才算接上雲端；沒填就是第 1 級，資料只存這台電腦
    const hasCloud = () => !!(state.settings.gasUrl && state.settings.classroomToken);
    function classKeySuffix(cls = currentClass()) {""")
t = rep(t, """: '<span class="chalk-empty">今天還沒有聯絡本內容。<br>老師可在教師工作台預先輸入，或按「✏️ 編輯」直接在這裡寫。</span>';""",
        """: `<span class="chalk-empty">今天還沒有聯絡本內容。<br>${hasCloud() ? '老師可在教師工作台預先輸入，或按「✏️ 編輯」直接在這裡寫。' : '按「✏️ 編輯」直接在這裡寫。'}</span>`;""")
t = rep(t, """: state.contact.source === 'line' ? '（LINE 輸入""", """: state.contact.source === 'local' ? '（存在這台電腦）' : state.contact.source === 'line' ? '（LINE 輸入""")
t = rep(t, """    async function loadContactBook({ silent = true } = {}) {
      if (!state.settings.className || !state.settings.classroomToken || !state.settings.gasUrl) { renderContactBook(); return; }""",
        """    // 第 1 級的聯絡本存在這台電腦，一天一筆
    const CONTACT_LOCAL_PREFIX = 'morningContactLocal:';
    function contactLocalGet(date) {
      try { return JSON.parse(localStorage.getItem(CONTACT_LOCAL_PREFIX + date + classKeySuffix()) || 'null'); } catch (error) { return null; }
    }
    async function loadContactBook({ silent = true } = {}) {
      if (!hasCloud()) {
        const saved = contactLocalGet(todayKey());
        state.contact.text = saved ? String(saved.text || '') : '';
        state.contact.updatedAt = saved ? String(saved.updatedAt || '') : '';
        state.contact.source = saved ? 'local' : '';
        renderContactBook();
        return;
      }
      if (!state.settings.className || !state.settings.classroomToken || !state.settings.gasUrl) { renderContactBook(); return; }""")
t = rep(t, """      const text = $('contactTextarea').value.trim().slice(0, 5000);
      try {
        await callGas({ action: 'contactbook_save',""", """      const text = $('contactTextarea').value.trim().slice(0, 5000);
      if (!hasCloud()) {
        const updatedAt = new Date().toISOString();
        try {
          localStorage.setItem(CONTACT_LOCAL_PREFIX + todayKey() + classKeySuffix(), JSON.stringify({ text, updatedAt }));
        } catch (error) {
          showToast('這台電腦存不下了，聯絡本沒有存到。', true);
          return;
        }
        state.contact.text = text;
        state.contact.updatedAt = updatedAt;
        state.contact.source = 'local';
        state.contact.editing = false;
        renderContactBook();
        showToast('聯絡本已存在這台電腦。');
        return;
      }
      try {
        await callGas({ action: 'contactbook_save',""")
t = rep(t, """const CCAL_SOURCE = { teacher: '工作台輸入', classroom: '教室輸入', line: 'LINE 輸入' };""", """const CCAL_SOURCE = { teacher: '工作台輸入', classroom: '教室輸入', line: 'LINE 輸入', local: '存在這台電腦' };""")
t = rep(t, """      if (!state.settings.gasUrl || !state.settings.classroomToken) throw new Error('要先在「設定」填雲端網址和教室大屏金鑰，才看得到以前的聯絡本。');
""", """      if (!hasCloud()) {
        const [y, m] = month.split('-').map(Number);
        const entries = [];
        for (let d = 1; d <= new Date(y, m, 0).getDate(); d += 1) {
          const date = `${month}-${String(d).padStart(2, '0')}`;
          const saved = contactLocalGet(date);
          if (saved && String(saved.text || '').trim()) entries.push({ date, text: String(saved.text), updatedAt: String(saved.updatedAt || ''), source: 'local' });
        }
        return entries;
      }
""")
t = rep(t, """        $('autoStatus').textContent = `自動化：已過晨間時段（${state.settings.autoAbsentTime} 未填轉未到、""", """        $('autoStatus').textContent = !hasCloud() ? `自動化：已過晨間時段（${state.settings.autoAbsentTime} 未填轉未到只在中午前執行）。` : `自動化：已過晨間時段（${state.settings.autoAbsentTime} 未填轉未到、""")
t = rep(t, """      $('autoStatus').textContent = `自動化：${state.settings.lateTime} 後點到校記遲到（大屏不顯示）｜""", """      $('autoStatus').textContent = !hasCloud() ? `自動化：${state.settings.lateTime} 後點到校記遲到（大屏不顯示）｜${state.settings.autoAbsentTime} 未填轉未到${state.flags.autoAbsentDone ? '（已執行）' : ''}` : `自動化：${state.settings.lateTime} 後點到校記遲到（大屏不顯示）｜""")
t = rep(t, "'⚠ 這台電腦還沒填「設定 → 班級名稱＋教室金鑰」，所以只看得到今天這台自己登記的訂正。填好後會自動統計", "'這台電腦還沒接上雲端（第 2 級：班級名稱＋🌐A＋🔑B），所以只看得到今天這台自己登記的訂正。接好後會自動統計")
t = rep(t, """    function applySettingsToUi() {
      const s = state.settings;
""", """    // 切換第 1 級／第 2 級：沒接雲端就收起要雲端的分頁與按鈕，接上後全部回來
    const SUBMIT_STATUS_DEFAULT = '尚未存到雲端（每 5 分鐘與離開頁面時會自動存；LINE 只在設定的推播時間通知）。';
    let levelLocal = null;
    function applyLevelUi() {
      const local = !hasCloud();
      if (local === levelLocal) return;
      const changed = levelLocal !== null;
      levelLocal = local;
      document.body.classList.toggle('local-only', local);
      $('setupLevel2').open = !local;
      if (local) {
        $('submitStatus').innerHTML = '📁 資料只存在這台電腦，不會上傳。想在家寫聯絡本、看補交與統計：<a href="Install.html#level2" target="_blank" rel="noopener">看第 2 級教學</a>';
        const active = document.querySelector('.tab-button.active');
        if (active && ['makeup', 'query'].includes(active.dataset.page)) document.querySelector('.tab-button[data-page="rollcall"]').click();
      } else {
        $('submitStatus').textContent = SUBMIT_STATUS_DEFAULT;
      }
      if (changed) { state.makeup.loaded = false; state.correct.loaded = false; loadContactBook(); }
    }
    function applySettingsToUi() {
      const s = state.settings;
      applyLevelUi();
""")
write('Morning.html', t)

# ---------- 安裝教學 ----------
t = map_globe(map_keys(read('Install.html')))
for old, new in [('🟢 1</td>', '🔵 2</td>'), ('🟡 2</td>', '🟡 3</td>'), ('🔴 3</td>', '🟠 4</td>')]:
    t = t.replace(old, new)
t = rep(t, '<tr><th>症狀</th><th>難度</th><th>解法</th></tr>', '<tr><th>症狀</th><th>哪一級</th><th>解法</th></tr>')
t = rep(t, '照難度 1 第 1 關第 3 步的方式', '照第 2 級第 2 關第 3 步的方式')
t = map_levels(t)


def section(text, sid):
    start = text.index(f'<section id="{sid}"')
    end = text.index('</section>', start) + len('</section>')
    return start, end, text[start:end]


def figures(html):
    return re.findall(r'<figure class="diagram.*?</figure>', html, re.S)


_, _, part1 = section(t, 'part1')
_, _, tier1 = section(t, 'tier1')
_, _, tier2 = section(t, 'tier2')
_, _, tier3 = section(t, 'tier3')
_, _, part3 = section(t, 'part3')
_, _, pet = section(t, 'pet')

# 第 1 級的操作圖：由原本的大屏設定圖改掉雲端欄位
fig_cloud = figures(part3)[0]
fig_local = fig_cloud.replace('ar-pc', 'ar-pl').replace('aria-label="晨間大屏設定操作畫面"', 'aria-label="第 1 級：晨間大屏設定操作畫面"')
a = fig_local.index('<text class="d-small" x="414" y="76"')
b = fig_local.index('<rect class="d-btn-p" x="494"')
fig_local = fig_local[:a] + '<text class="d-small" x="414" y="84" text-anchor="start">最大座號</text><rect class="d-field" x="470" y="71" width="94" height="20" rx="4"/><text class="d-text" x="476" y="85" text-anchor="start">30</text><text class="d-small" x="414" y="118" text-anchor="start">要收的科目</text><rect class="d-field" x="470" y="105" width="94" height="20" rx="4"/><text class="d-text" x="476" y="119" text-anchor="start">國語、數學</text>' + fig_local[b:]
fig_local = rep(fig_local, '③ 填班級、🌐A、🔑B', '③ 填班級、座號、科目')
a = fig_local.index('<rect class="d-btn-p" x="612"')
b = fig_local.index('<path class="d-cursor" d="M686,146')
fig_local = fig_local[:a] + '<text class="d-small" x="612" y="150" text-anchor="start">自動存在這台電腦</text>' + fig_local[b:]
fig_local = rep(fig_local, '<text class="d-small" x="712" y="149" text-anchor="start">點座號</text>', '')
fig_local = rep(fig_local, '④ 點名 → 💾 存到雲端', '④ 點座號就存好')
fig_local = rep(fig_local, '<text class="d-small" x="687" y="218" text-anchor="middle">驗收</text>', '<text class="d-small" x="687" y="218" text-anchor="middle">不用按存檔</text>')


def between(html, start_mark, end_mark):
    a = html.index(start_mark)
    return html[a:html.index(end_mark, a)]


step_kiosk = between(part3, '<div class="step"><div class="step-no">3</div>', '<div class="step"><div class="step-no">4</div>')
step_tablet = between(part3, '<div class="step"><div class="step-no">4</div>', '<div class="step"><div class="step-no">5</div>')
copy_morning = between(part3, '<div class="copyrow"><code id="urlMorning">', '</div></div>\n      <div class="step"><div class="step-no">2</div>')

level1 = f'''<section id="level1" class="tier1">
      <span id="part3"></span>
      <div class="sec-head"><div class="sec-icon">🟢</div><div class="sec-titles"><div class="tier-head"><h2><span class="sec-num">2.</span>第 1 級：只用晨間大屏</h2><span class="pill">約 5 分鐘</span><span class="pill">不用金鑰</span></div></div></div>
      <p class="lead">沒用過 AI、沒碰過雲端也沒關係。打開網址、填幾個欄位，教室電腦就能點名、收作業、寫黑板。<strong>資料只存在這台電腦</strong>，不會上傳到任何地方。</p>
      <div class="gets"><span>不用申請任何東西</span></div>
      {fig_local}
      <div class="step"><div class="step-no">1</div><div class="step-body">
        <strong class="t">教室電腦（接投影機或觸控大屏）開啟大屏網址</strong>
        {copy_morning}
      </div></div>
      <div class="step"><div class="step-no">2</div><div class="step-body">
        <strong class="t">點最上排<strong>最右邊的分頁「設定」</strong>→ 輸入密碼（預設 <code>1234</code>）→ 填好 → 最下面「儲存設定」</strong>
        <table>
          <tr><th>欄位</th><th>填什麼</th></tr>
          <tr><td>班級名稱</td><td>例：601</td></tr>
          <tr><td>班級最大座號／空號</td><td>照實填；轉走的座號填進「空號」就不會出現</td></tr>
          <tr><td>科目管理／作業項目</td><td>點亮要收作業的科目與項目；不夠的自己新增</td></tr>
          <tr><td>兩個時間</td><td>預設 08:00 遲到界線／08:05 未填轉未到，都可以自訂</td></tr>
          <tr><td>設定頁密碼</td><td>建議改掉預設的 1234，免得學生進設定亂改</td></tr>
          <tr><td>聯絡本字體</td><td>一般：標準／粉圓／芫荽；注音：注音芫荽／注音粉圓（低年級選注音體，第一次切換要等字型下載）</td></tr>
        </table>
        <span class="lead">設定頁下面「第 2 級」「第 4 級」那兩塊先不用打開。</span>
      </div></div>
      {step_kiosk}
      <div class="step"><div class="step-no">4</div><div class="step-body">
        <strong class="t">（內建）🧰 班級工具——不用任何設定</strong>
        <p>抽籤機、檢核板、計分板、隨機分組、安靜偵測、定評小幫手、番茄鐘、大屏提示、螢幕公告；全部只存教室電腦。使用情境見<a href="About.html" target="_blank" rel="noopener">系統說明</a>。</p>
      </div></div>
      <div class="warn">🔒 <strong>第 1 級的資料範圍：</strong>只存在這台電腦的這個瀏覽器。大屏只用<strong>座號</strong>，不輸入學生姓名；聯絡本也請不要寫學生姓名或個資。換電腦或清除瀏覽器資料，內容就不見了。</div>
      <div class="box"><strong>第 1 級看不到的：</strong>「作業補交」「查詢統計」兩個分頁要看前幾天的資料，接上第 2 級才會出現。</div>
      <div class="ok">✅ <strong>第 1 級完成！</strong>測一下：點幾個座號 → 到「作業繳交」新增一科 → 黑板按「✏️ 編輯」寫一句並儲存 → 按 F5 重新整理，內容都還在就對了。</div>
    </section>'''

# 第 2 級：工作台＋複製試算表＋部署＋接大屏＋接工作台
wb_fig = figures(part1)[0]
wb_steps = part1[part1.index('<div class="step"><div class="step-no">1</div>'):part1.index('<div class="ok">')]
wb_steps = rep(wb_steps, '（做了第 2 級還能雲端備份）', '（做完這一級還能雲端備份）')
copy_part = between(tier1, '<h3>第 1 關：一鍵複製試算表副本</h3>', '<h3>第 2 關：部署')
deploy_part = between(tier1, '<h3>第 2 關：部署', '<h3>第 3 關：把工作台接上')
join_part = between(tier1, '<h3>第 3 關：把工作台接上', '<div class="ok">')
option_box = between(tier1, '<div class="box"><strong>選配：記事同步 Google Tasks', '</section>')
copy_part = rep(copy_part, '<h3>第 1 關：一鍵複製試算表副本</h3>', '<h3>第 2 關：一鍵複製試算表副本</h3>')
copy_part = rep(copy_part, '<strong>第 2 級只要把【第 2 級】那段的兩把</strong>貼進你的金鑰記錄表：<br>・<strong>🔑C</strong> 工作台同步金鑰（之後貼工作台、小綿助）<br>・<strong>🔑B</strong> 教室大屏金鑰（之後貼教室大屏）',
                '<strong>現在只要把【第 2 級】那段的兩把</strong>貼進你的金鑰記錄表：<br>・<strong>🔑B</strong> 教室大屏金鑰（第 4 關貼大屏）<br>・<strong>🔑C</strong> 工作台同步金鑰（第 5 關貼工作台）')
deploy_part = rep(deploy_part, '<h3>第 2 關：部署（把大腦開機，拿到 🌐A）</h3>', '<h3>第 3 關：部署（把大腦開機，拿到 🌐A）</h3>')
join_part = rep(join_part, '<h3>第 3 關：把工作台接上（🌐A＋🔑C）</h3>', '<h3>第 5 關：把工作台接上（🌐A＋🔑C）</h3>')
step_tablet = step_tablet.replace('<div class="step-no">4</div>', '<div class="step-no">2</div>').replace('照第 2 步填一次', '照第 1 步填一次')
level2 = f'''<section id="level2" class="tierb">
      <span id="tier1"></span><span id="part2"></span><span id="part1"></span>
      <div class="sec-head"><div class="sec-icon">🔵</div><div class="sec-titles"><div class="tier-head"><h2><span class="sec-num">3.</span>第 2 級：大屏＋教師工作台（用 GAS 連結）</h2><span class="pill">約 20 分鐘</span><span class="pill">不碰程式碼</span></div></div></div>
      <p class="lead">在你自己的 Google 帳號複製一份程式，當作「雲端大腦」，把大屏和工作台接起來。接好後可以在家寫聯絡本、隔天黑板自動出現，還多了作業補交與查詢統計。<strong>先在瀏覽器登入 Google</strong>（右上角看得到你的頭像），建議用<strong>個人 Gmail</strong>（學校帳號可能被管理員擋）。</p>
      <div class="gets"><span>會拿到：🌐A 🔑B 🔑C</span><span>（🔑F 會一起產生，第 4 級才用）</span></div>

      <h3>第 1 關：打開工作台（1 分鐘）</h3>
      {wb_fig}
      {wb_steps}
      {copy_part}
      {deploy_part}
      <h3>第 4 關：把大屏接上（🌐A＋🔑B）</h3>
      {fig_cloud}
      <div class="step"><div class="step-no">1</div><div class="step-body">教室電腦的大屏 →「設定」→ 打開「<strong>🔵 第 2 級：連上工作台</strong>」→「<strong>🌐A</strong>」欄貼 🌐A、「<strong>🔑B</strong>」欄貼 🔑B → 按「<strong>儲存設定</strong>」。<br><span class="lead">⚠ 教室電腦只填這兩個，別填 🔑C——🔑B 只能回報當天，被學生玩到也拿不到你的資料。</span><br><span class="lead">✔ 檢查：上排多出「作業補交」「查詢統計」，左下出現「💾 存到雲端」，按下去看到「已存到雲端」。</span></div></div>
      {step_tablet}
      {join_part}
      <div class="ok">✅ <strong>第 2 級完成！</strong>工作台多出「聯絡本」按鈕；任務可一鍵加 Google 日曆、記事可同步 Google Tasks、檔案可歸檔到雲端硬碟、設定裡的「備份與還原」可雲端備份。工作台日曆也會出現今日出缺摘要。</div>
      {option_box.strip()}
    </section>'''

tier2_new = tier2.replace('<section id="tier2" class="tier2">', '<section id="level3" class="tier2">\n      <span id="tier2"></span>')
tier2_new = rep(tier2_new, '<span class="sec-num">4.</span>第 3 級：AI 金鑰 🔑D（Gemini）', '<span class="sec-num">4.</span>第 3 級：再加 AI 金鑰 🔑D（Gemini）')
tier2_new = rep(tier2_new, '<span class="pill">不需要第 2 級</span>', '<span class="pill">申請一串字</span>')
tier2_new = rep(tier2_new, '（做了第 4 級才需要）', '（做到第 4 級才需要）')

tier3_new = tier3.replace('<section id="tier3" class="tier3">', '<section id="level4" class="tier3">\n      <span id="tier3"></span>')
tier3_new = rep(tier3_new, '第 4 級：LINE 小幫手</h2>', '第 4 級：再加 LINE 小幫手</h2>')
tier3_new = rep(tier3_new, '<span>會拿到：🔑E</span><span>會用到：第 2 級的 🌐A 與 🔑F</span>', '<span>會拿到：🔑E 🔑F 👤G</span><span>會用到：第 2 級的 🌐A</span>')
tier3_new = rep(tier3_new, '接上第 2 級的雲端大腦。', '接上第 2 級的雲端大腦。')

pet_new = pet.replace('<section id="pet">', '<section id="level5" class="tierp">\n      <span id="pet"></span>')
pet_new = rep(pet_new, '<div class="sec-icon">🐑</div>', '<div class="sec-icon">🟣</div>')
pet_new = rep(pet_new, '<span class="sec-num">7.</span>桌面小綿助（選用，Windows）', '<span class="sec-num">6.</span>第 5 級：再加桌寵小綿助（Windows）')
pet_new = rep(pet_new, '做了第 2 級可以直連你的資料，做了第 3 級可以按住說話就出字。', '接上第 2 級可以直連你的資料（用 🌐A＋🔑C），有第 3 級的 🔑D 可以按住說話就出字。')

route = '''<figure class="diagram"><svg viewBox="0 0 780 462" role="img" aria-label="五級路線圖（點方框可跳到該級教學）：第 1 級只用大屏，第 2 級加工作台與雲端，第 3 級加 AI，第 4 級加 LINE，第 5 級加桌寵">
<defs><marker id="ar-road" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#1f514a"/></marker></defs>
''' + ''.join(
    f'''<a href="#level{i + 1}"><rect class="{cls}" x="10" y="{10 + i * 92}" width="344" height="76" rx="12"/>
<text class="d-title" x="24" y="{34 + i * 92}" text-anchor="start">{title}</text>
<text class="d-small" x="24" y="{54 + i * 92}" text-anchor="start">{cost}</text>
<text class="d-small" x="24" y="{74 + i * 92}" text-anchor="start">{keys}</text>
<text class="d-small" x="344" y="{74 + i * 92}" text-anchor="end">看教學 →</text></a>
<rect class="d-box" x="412" y="{14 + i * 92}" width="358" height="68" rx="10"/>
<text class="d-text" x="426" y="{43 + i * 92}" text-anchor="start">{gain1}</text>
<text class="d-text" x="426" y="{65 + i * 92}" text-anchor="start">{gain2}</text>
<path class="d-line" d="M356,{48 + i * 92} L406,{48 + i * 92}" marker-end="url(#ar-road)"/>
''' + (f'<path class="d-line" d="M182,{88 + i * 92} L182,{100 + i * 92}" marker-end="url(#ar-road)"/>\n' if i < 4 else '')
    for i, (cls, title, cost, keys, gain1, gain2) in enumerate([
        ('d-t1', '🟢 第 1 級｜只用晨間大屏', '約 5 分・打開網址就能用', '不用金鑰', '點名、收作業、訂正、黑板聯絡本、班級工具', '資料只存這台電腦（不含機敏資料）'),
        ('d-tb', '🔵 第 2 級｜大屏＋教師工作台', '約 20 分・用 GAS 連結，按按鈕複製', '拿到 🌐A 🔑B 🔑C', '在家寫聯絡本、作業補交、查詢統計、雲端備份', '任務與教學進度、Google 日曆／Tasks'),
        ('d-t2', '🟡 第 3 級｜再加 AI 金鑰', '約 3 分・申請一串字', '拿到 🔑D', 'AI 行政助理、訊息整合站', '教材小工場的 AI 工具'),
        ('d-t3', '🟠 第 4 級｜再加 LINE', '約 30 分・要照 LINE 後台一步步做', '拿到 🔑E 🔑F 👤G', 'LINE 傳訊息建任務、晨間推播', '家長訊息草稿、遙控大屏提示'),
        ('d-tp', '🟣 第 5 級｜再加桌寵小綿助', '約 3 分・下載解壓（Windows）', '沿用 🌐A 🔑C 🔑D', '桌面陪伴與健康提醒', '直連資料、按住說話就出字'),
    ])
) + '''</svg><figcaption>由上往下，一級一級加。停在哪一級都可以；上一級的資料和設定不會不見。</figcaption></figure>'''

part0_new = f'''<section id="part0">
      <div class="sec-head"><div class="sec-icon">🧭</div><div class="sec-titles"><h2><span class="sec-num">1.</span>開始前：你想用到哪一級？</h2></div></div>
      <p class="lead">系統分成五級，<strong>從第 1 級開始，用得順手再往下加</strong>。沒有 AI 經驗的老師，只用第 1 級就很夠用。</p>
      {route}

      <h3>我想要……要做到哪一級？</h3>
      <table>
        <tr><th>我想要</th><th>做到</th></tr>
        <tr><td>教室大屏點名、收作業、訂正、黑板聯絡本、班級工具</td><td><a href="#level1">🟢 第 1 級</a></td></tr>
        <tr><td>在家寫聯絡本隔天黑板出現、作業補交、查詢統計、任務清單、教學進度、Google 日曆與 Tasks</td><td><a href="#level2">🔵 第 2 級</a></td></tr>
        <tr><td>AI 幫我拆公文、整合 LINE 群組訊息、做學習單、改作文、生海報、建 Google 表單</td><td><a href="#level3">🟡 第 3 級</a></td></tr>
        <tr><td>在 LINE 傳一句話就建任務、每天早上收到點名回報</td><td><a href="#level4">🟠 第 4 級</a></td></tr>
        <tr><td>桌面小綿助陪伴與健康提醒、按住說話就出字</td><td><a href="#level5">🟣 第 5 級</a></td></tr>
      </table>

      <h3>📝 做到第 2 級再準備：一份「金鑰記錄表」</h3>
      <p class="lead">第 1 級完全用不到。從第 2 級開始會拿到幾串網址和「金鑰」（一長串亂碼），<strong>代號照用到的先後排成 A、B、C……</strong>。按下面的「複製」→ 開 Windows 的<strong>記事本</strong>（開始功能表搜尋「記事本」）→ 貼上 → 存到桌面，取名 <code>我的教師工作台金鑰.txt</code>。之後拿到哪一串，就貼在對應那一行後面。每個要貼的欄位上都印著同樣的代號，<strong>照代號貼就對了</strong>。</p>
      <pre class="notes" id="keyNotes">🌐A 機器人網址（第 2 級）：
🔑B 教室大屏金鑰（第 2 級）：
🔑C 工作台同步金鑰（第 2 級）：
🔑D Gemini 金鑰（第 3 級）：
🔑E LINE Token（第 4 級）：
🔑F Webhook 驗證參數（第 4 級）：
👤G LINE userId（第 4 級，U 開頭）：</pre>
      <div class="dl-row"><button class="copy-btn" data-copy="#keyNotes">複製記錄表</button><span class="lead">⚠ 這份檔案不要傳給別人、不要放群組；教室電腦只需要 🌐A 和 🔑B。</span></div>

      <h3>🗝 代號對照表</h3>
      <table>
        <tr><th>代號</th><th>第幾級</th><th>這是什麼</th><th>哪裡拿到</th><th>貼到哪裡</th></tr>
        <tr><td><strong>🌐A</strong></td><td>🔵 第 2 級</td><td>機器人網址（/exec 結尾）</td><td>第 2 級第 3 關，部署後產生</td><td>大屏設定、工作台「① 雲端／LINE 小幫手」、小綿助雲端連線；（第 4 級）Webhook</td></tr>
        <tr><td><strong>🔑B</strong></td><td>🔵 第 2 級</td><td>教室大屏金鑰（教室專用，只能報當天）</td><td rowspan="2">第 2 級第 2 關「① 初始化」彈窗<br><span class="lead">隨時可用選單「🔑 顯示我的金鑰」再看</span></td><td>晨間大屏「設定」的 🔑B 欄（教室電腦只放這把）</td></tr>
        <tr><td><strong>🔑C</strong></td><td>🔵 第 2 級</td><td>工作台同步金鑰（老師專用，可查歷史）</td><td>工作台「① 雲端／LINE 小幫手」、小綿助雲端連線、大屏「查詢統計」</td></tr>
        <tr><td><strong>🔑D</strong></td><td>🟡 第 3 級</td><td>AI 金鑰（Gemini）</td><td><a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener">Google AI Studio</a> 免費申請</td><td>工作台「② AI 設定」、小綿助「🎙 語音輸入」；（第 4 級）試算表選單「④ 填入 Gemini 金鑰」</td></tr>
        <tr><td><strong>🔑E</strong></td><td>🟠 第 4 級</td><td>LINE Channel access token</td><td>LINE Developers 按 Issue 發行</td><td>試算表選單「② 填入 LINE Token（🔑E）」</td></tr>
        <tr><td><strong>🔑F</strong></td><td>🟠 第 4 級</td><td>Webhook 驗證參數</td><td>第 2 級初始化時已一起產生（先不用）</td><td>接在 🌐A 後面：<code>🌐A?hook=🔑F</code>，貼到 LINE 的 Webhook URL</td></tr>
        <tr><td><strong>👤G</strong></td><td>🟠 第 4 級</td><td>LINE userId（U 開頭，用來鎖門）</td><td>對機器人傳「我的ID」</td><td>試算表選單「③ 填入我的 LINE userId」</td></tr>
      </table>
      <div class="warn">💰 <strong>費用：全部免費。</strong>Google 免費額度＋ Gemini 免費額度＋ LINE 官方帳號免費方案就夠用。LINE 唯一的量限制是「主動推播」每月 200 則（晨間回報一天 2 則，一個月約 44 則）。</div>
    </section>'''

a = t.index('<section id="part0">')
b = t.index('<section id="part4">')
t = t[:a] + part0_new + '\n\n    ' + level1 + '\n\n    ' + level2 + '\n\n    ' + tier2_new + '\n\n    ' + tier3_new + '\n\n    ' + pet_new + '\n\n    ' + t[b:]

# 頁首、目錄
a = t.index('<a class="nl" href="#part0">')
b = t.index('</div></div>', a)
t = t[:a] + '''<a class="nl" href="#part0">🧭 開始前</a>
    <a class="nl" href="#level1">🟢 1 大屏</a>
    <a class="nl" href="#level2">🔵 2 工作台</a>
    <a class="nl" href="#level3">🟡 3 AI</a>
    <a class="nl" href="#level4">🟠 4 LINE</a>
    <a class="nl" href="#level5">🟣 5 桌寵</a>
    <a class="nl" href="#part5">🛟 疑難排解</a>
    <a class="nl" href="#partv2">🆕 舊版升級</a>
    <a class="cta" href="Morning.html">打開晨間大屏 →</a>
  ''' + t[b:]
t = rep(t, '<span class="badge">🔵 第 2 級 → 🟡 第 3 級 → 🟠 第 4 級・每一步都附操作畫面</span>', '<span class="badge">🟢 大屏 → 🔵 工作台 → 🟡 AI → 🟠 LINE → 🟣 桌寵・每一步都附操作畫面</span>')
t = rep(t, '<h1>📖 安裝教學（第 2 版）<br>', '<h1>📖 安裝教學（五級版）<br>')
t = rep(t, '<span>安裝教學（第 2 版）<small>', '<span>安裝教學（五級版）<small>')
a = t.index('<p class="intro">')
b = t.index('</p>', a)
t = t[:a] + '<p class="intro">從<strong>只用大屏</strong>開始，不用金鑰；用得順手再一級一級往下加。每一步都附操作畫面，<strong>照紅框點</strong>就對了。' + t[b:]
a = t.index('<nav class="toc">')
b = t.index('</nav>', a)
t = t[:a] + '''<nav class="toc"><div class="wrap">
    <a href="#part0">開始前</a>
    <a href="#level1">🟢 第 1 級 大屏</a>
    <a href="#level2">🔵 第 2 級 工作台</a>
    <a href="#level3">🟡 第 3 級 AI</a>
    <a href="#level4">🟠 第 4 級 LINE</a>
    <a href="#level5">🟣 第 5 級 桌寵</a>
    <a href="#part4">每天怎麼用</a>
    <a href="#part5">疑難排解</a>
    <a href="#part6">備份與安全</a>
    <a href="#partv2" style="font-weight:900">🆕 舊版升級</a>
    <a href="About.html">📚 說明與資安</a>
    <a href="#part7">版權</a>
  </div>''' + t[b:]
t = re.sub(r'href="#tier1"', 'href="#level2"', t)
t = re.sub(r'href="#tier2"', 'href="#level3"', t)
t = re.sub(r'href="#tier3"', 'href="#level4"', t)
t = re.sub(r'href="#part3"', 'href="#level1"', t)
t = re.sub(r'href="#part1"', 'href="#level2"', t)
t = re.sub(r'href="#pet"', 'href="#level5"', t)

# 樣式：第 2 級藍、第 5 級紫
t = rep(t, 'section.tier1 { border-color:#9fd4b8; } section.tier2', 'section.tierb { border-color:#9dbfe6; } section.tierp { border-color:#c4b0e6; } section.tier1 { border-color:#9fd4b8; } section.tier2')
t = rep(t, '.d-t1 { fill:#eef8f2;', '.d-tb { fill:#eef4fc; stroke:#4f86c6; stroke-width:2; } .d-tp { fill:#f4effb; stroke:#8a6cc4; stroke-width:2; } .d-t1 { fill:#eef8f2;')
t = rep(t, 'section.tier1, section.tier2, section.tier3 { border:0; }', 'section.tier1, section.tier2, section.tier3, section.tierb, section.tierp { border:0; }')
t = rep(t, 'section.tier1 { border-top:5px solid #5fa87f; }', 'section.tierb { border-top:5px solid #4f86c6; } section.tierp { border-top:5px solid #8a6cc4; } section.tier1 { border-top:5px solid #5fa87f; }')
t = rep(t, 'section.tier1 .sec-icon { background:#eef8f2; }', 'section.tierb .sec-icon { background:#eef4fc; } section.tierp .sec-icon { background:#f4effb; } section.tier1 .sec-icon { background:#eef8f2; }')
t = rep(t, 'section.tier1 .sec-num { color:#2f8a5b; }', 'section.tierb .sec-num { color:#2f65a5; } section.tierp .sec-num { color:#6b4fa8; } section.tier1 .sec-num { color:#2f8a5b; }')

# 每天怎麼用
t = rep(t, '<div class="sec-icon">🅳</div>', '<div class="sec-icon">📅</div>')
t = rep(t, 'Part D：每天怎麼用（日常流程）', '每天怎麼用（日常流程）')
t = rep(t, '<tr><td>前一晚</td><td>工作台「聯絡本」', '<tr><td>前一晚<br><span class="lead">第 2 級</span></td><td>工作台「聯絡本」')
t = rep(t, '<tr><td>08:08</td>', '<tr><td>08:08<br><span class="lead">第 4 級</span></td>')
t = rep(t, '<tr><td>08:40</td>', '<tr><td>08:40<br><span class="lead">第 4 級</span></td>')
t = rep(t, '<tr><td>白天隨時</td>', '<tr><td>白天隨時<br><span class="lead">第 4 級</span></td>')
t = rep(t, '<tr><td>下課</td>', '<tr><td>下課<br><span class="lead">第 2 級</span></td>')
t = rep(t, '<tr><td>週五下午</td>', '<tr><td>週五下午<br><span class="lead">第 4 級</span></td>')
t = rep(t, '<tr><td>期末</td>', '<tr><td>期末<br><span class="lead">第 2 級</span></td>')
t = rep(t, '「作業訂正」與「作業補交」的統計要看得到前幾天，必須先在「設定」填入「班級名稱」與 🔑B 教室金鑰', '「作業訂正」與「作業補交」的統計要看得到前幾天，必須做到第 2 級（「設定」填入「班級名稱」、🌐A 與 🔑B）')
t = rep(t, '<tr><td>大屏進設定說密碼錯</td>', '<tr><td>大屏看不到「作業補交」「查詢統計」「存到雲端」</td><td>🟢 1</td><td>第 1 級本來就沒有；要用就做第 2 級，把 🌐A＋🔑B 填進大屏設定</td></tr>\n        <tr><td>大屏進設定說密碼錯</td>')
t = t.replace('金鑰的家</strong>：你的金鑰記錄表；🔑F🔑C🔑B 也能', '金鑰的家</strong>：你的金鑰記錄表；🔑B🔑C🔑F 也能')

# 舊版升級：舊代號對照
t = rep(t, '<h3>第 2 版多了什麼？</h3>', '''<h3>🔤 金鑰代號換了（金鑰本身沒變，不用重貼）</h3>
      <p class="lead">為了配合五級，代號改成照用到的先後排。你記事本裡那幾串字完全不用動，只是名字不一樣；舊代號只出現在舊的教學和舊的記錄表。</p>
      <table>
        <tr><th>這是什麼</th><th>舊代號</th><th>新代號</th></tr>
        <tr><td>機器人網址</td><td>🌐</td><td><strong>🌐A</strong></td></tr>
        <tr><td>教室大屏金鑰</td><td>舊 D</td><td><strong>🔑B</strong></td></tr>
        <tr><td>工作台同步金鑰</td><td>舊 C</td><td><strong>🔑C</strong>（沒變）</td></tr>
        <tr><td>Gemini 金鑰</td><td>舊 E</td><td><strong>🔑D</strong></td></tr>
        <tr><td>LINE Token</td><td>舊 A</td><td><strong>🔑E</strong></td></tr>
        <tr><td>Webhook 驗證參數</td><td>舊 B</td><td><strong>🔑F</strong></td></tr>
        <tr><td>LINE userId</td><td>（沒有代號）</td><td><strong>👤G</strong></td></tr>
      </table>
      <h3>第 2 版多了什麼？</h3>''')

# 章節重新編號
num = iter(range(1, 40))
t = re.sub(r'<span class="sec-num">\d+\.</span>', lambda m: f'<span class="sec-num">{next(num)}.</span>', t)
write('Install.html', t)

# ---------- 說明與資安 ----------
t = map_globe(map_keys(read('About.html')))
t = map_install_links(t)
a = t.index('<h2>🧭 系統是什麼')
b = t.index('</table>', a)
t = t[:a] + '''<h2>🧭 系統是什麼：從大屏開始的五級路線</h2>
      <table>
        <tr><th>第幾級</th><th>裝什麼</th><th>做什麼</th></tr>
        <tr><td>🟢 第 1 級 只用晨間大屏</td><td>不用裝，開網址填幾個欄位，約 5 分鐘（<a href="Install.html#level1">教學</a>）</td><td>點名、收作業、訂正、黑板聯絡本、班級工具。資料只存這台電腦，不含機敏資料</td></tr>
        <tr><td>🔵 第 2 級 大屏＋教師工作台（GAS）</td><td>按按鈕複製一份程式，約 20 分鐘，拿到 🌐A 🔑B 🔑C（<a href="Install.html#level2">教學</a>）</td><td>在家寫聯絡本、作業補交、查詢統計、任務、日曆、教學進度、雲端備份、Google 日曆／Tasks／雲端硬碟</td></tr>
        <tr><td>🟡 第 3 級 再加 AI 金鑰（Gemini）</td><td>申請一把 🔑D，約 3 分鐘（<a href="Install.html#level3">教學</a>）</td><td>AI 行政助理、訊息整合站、教材小工場 AI 工具</td></tr>
        <tr><td>🟠 第 4 級 再加 LINE 小幫手</td><td>LINE 後台設定，約 30 分鐘，拿到 🔑E 🔑F 👤G（<a href="Install.html#level4">教學</a>）</td><td>LINE 傳文字／語音／照片建任務、寫聯絡本、推播簡報、家長訊息草稿、代課包、檔案歸檔</td></tr>
        <tr><td>🟣 第 5 級 再加桌寵小綿助</td><td>Windows 免安裝可攜版（<a href="Install.html#level5">教學</a>）</td><td>桌面陪伴、健康提醒、按住說話就出字、直連雲端大腦拿快照、分心提醒、專注模式、遙控大屏提示</td></tr>
      ''' + t[b:]
a = t.index('<tr><th>金鑰</th><th>放在哪</th>')
b = t.index('</table>', a)
block = t[a:b]
key_rows = re.findall(r'<tr><td>.*?</tr>', block, re.S)
assert len(key_rows) == 6, len(key_rows)
key_rows.sort(key=lambda row: re.search(r'🔑([A-F])', row).group(1))
t = t[:a] + '<tr><th>金鑰</th><th>放在哪</th><th>權限範圍</th><th>外洩了怎麼辦</th></tr>\n        ' + '\n        '.join(key_rows) + '\n      ' + t[b:]
t = map_levels(t)
write('About.html', t)

# ---------- 一頁式介紹 ----------
t = map_keys(read('Intro.html'))
a = t.index('<h2>先免設定，再照難度往下裝</h2>')
b = t.index('</section>', a)
t = t[:a] + '''<h2>從大屏開始，一級一級往下加</h2>
        <p>不必一次全裝。只用第 1 級就很好用，不用金鑰，資料也只存在教室電腦。</p>
      </div>

      <div class="layers">
        <div class="layer">
          <span class="step">🟢 第 1 級</span>
          <h3>只用晨間大屏</h3>
          <span class="cost">0 安裝・約 5 分鐘・不用金鑰</span>
          <p>點名、收作業、訂正、黑板聯絡本、班級工具。打開網址、填班級和座號就開始。資料只存這台電腦，不含機敏資料。</p>
          <a class="go" href="https://t-borad2026.netlify.app/Install.html#level1" target="_blank" rel="noopener">看第 1 級教學 →</a>
        </div>

        <div class="layer">
          <span class="step">🔵 第 2 級</span>
          <h3>大屏＋教師工作台</h3>
          <span class="cost">約 20 分鐘・按按鈕複製，不貼程式碼</span>
          <p>複製一份程式到自己的 Google，把大屏和工作台接起來：在家寫聯絡本、作業補交、查詢統計、任務與教學進度、雲端備份、Google 日曆。</p>
          <a class="go" href="https://t-borad2026.netlify.app/Install.html#level2" target="_blank" rel="noopener">看第 2 級教學 →</a>
        </div>

        <div class="layer">
          <span class="step">🟡 第 3 級</span>
          <h3>再加 AI 金鑰（Gemini）</h3>
          <span class="cost">約 3 分鐘・申請一串字</span>
          <p>一把免費的 🔑D 就打開 AI 行政助理、訊息整合站、教材小工場全部 AI 工具。</p>
          <a class="go" href="https://t-borad2026.netlify.app/Install.html#level3" target="_blank" rel="noopener">看第 3 級教學 →</a>
        </div>

        <div class="layer">
          <span class="step">🟠 第 4 級</span>
          <h3>再加 LINE 小幫手</h3>
          <span class="cost">約 30 分鐘・接上第 2 級的雲端大腦</span>
          <p>申請自己的 LINE 機器人：LINE 傳文字／語音／照片建任務、晨間回報推播、家長訊息草稿。教學附代號對照表，照代號貼不會錯。</p>
          <a class="go" href="https://t-borad2026.netlify.app/Install.html#level4" target="_blank" rel="noopener">看第 4 級教學 →</a>
        </div>

        <div class="layer">
          <span class="step">🟣 第 5 級</span>
          <h3>再加桌寵小綿助</h3>
          <span class="cost">約 3 分鐘・Windows 下載解壓</span>
          <p>桌面陪伴與健康提醒；接上雲端可以直連資料，有 AI 金鑰可以按住說話就出字。</p>
          <a class="go" href="https://t-borad2026.netlify.app/Install.html#level5" target="_blank" rel="noopener">看第 5 級教學 →</a>
        </div>
      </div>
    </div>
  ''' + t[b:]
write('Intro.html', t)

print('done')
