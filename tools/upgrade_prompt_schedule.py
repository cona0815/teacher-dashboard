"""大屏提示升級：定時自動跳出（可重複、每節下課）、新增提示句（飯後潔牙等）、全螢幕圖片不變形、新插圖接口。

python tools/upgrade_prompt_schedule.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'promptSchedules' not in s, '已套用過'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ---------------------------------------------------------------- CSS
rep('''        .prompt-board:fullscreen .prompt-img { max-height: 38vh; }
''', '''        .prompt-board:fullscreen .prompt-img { max-height: 38vh; }
        /* 圖片維持原比例：全螢幕時 prompt-board 是直向 flex，預設會把圖拉寬變形 */
        .prompt-img { width: auto; height: auto; align-self: center; object-fit: contain; }
        .prompt-board { padding-bottom: 26px !important; }
        .prompt-board:fullscreen .prompt-img { max-width: 80vw; }
        /* ⏰ 定時自動跳出 */
        .prompt-sched { margin-top: 14px; border-radius: 18px; background: #fff; box-shadow: inset 0 0 0 2px var(--line, #dfe8e3); padding: 12px 16px; }
        .prompt-sched > summary { cursor: pointer; font-weight: 900; font-size: 17px; color: var(--primary-strong); list-style: none; }
        .prompt-sched > summary::-webkit-details-marker { display: none; }
        .prompt-sched > summary small { font-weight: 700; color: var(--muted); margin-left: 8px; font-size: 14px; }
        .ps-breaks { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 10px 0; font-weight: 800; }
        .ps-breaks input { flex: 1 1 320px; font-size: 16px; padding: 7px 10px; border-radius: 10px; border: 2px solid var(--line, #dfe8e3); font-family: inherit; }
        .ps-row { display: grid; grid-template-columns: auto minmax(150px, 1.1fr) auto minmax(200px, 1.6fr) auto auto auto; gap: 10px; align-items: center;
          padding: 10px 0; border-top: 1px dashed var(--line, #dfe8e3); }
        .ps-row.off { opacity: .55; }
        .ps-row select, .ps-row input[type=text], .ps-row input[type=number] { font-size: 15px; padding: 6px 8px; border-radius: 10px; border: 2px solid var(--line, #dfe8e3); font-family: inherit; min-width: 0; }
        .ps-row input[type=number] { width: 62px; }
        .ps-when { display: grid; gap: 4px; }
        .ps-days { display: flex; gap: 3px; }
        .ps-days button { width: 30px; height: 30px; border-radius: 9px; border: 0; font-weight: 900; cursor: pointer; background: #eef2f0; color: #8a9893; font-family: inherit; }
        .ps-days button.on { background: var(--primary, #1f7a52); color: #fff; }
        .ps-what { display: grid; gap: 4px; }
        .ps-del { border: 0; background: none; font-size: 18px; cursor: pointer; color: #b0413e; }
        .ps-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        @media (max-width: 900px) { .ps-row { grid-template-columns: 1fr 1fr; } }
        /* 跳出畫面：蓋在大屏任何分頁之上（全螢幕時放進全螢幕元素裡） */
        .prompt-pop { position: fixed; inset: 0; z-index: 99999; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1vh;
          background: var(--pb, linear-gradient(160deg, #eaf6f0, #fff 70%)); animation: popIn .55s cubic-bezier(.3,1.4,.5,1); padding: 3vh 4vw; text-align: center; }
        .prompt-pop[hidden] { display: none !important; }
        @keyframes popIn { from { opacity: 0; transform: scale(.92); } to { opacity: 1; transform: none; } }
        .prompt-pop .pp-clock { font-size: clamp(70px, 14vh, 200px); font-weight: 900; line-height: 1; font-variant-numeric: tabular-nums;
          background: linear-gradient(90deg, #1d9e5f, #2457e6); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .prompt-pop .pp-msg { font-size: clamp(48px, 10vh, 150px); font-weight: 900; color: var(--pp-ink, #173f3a); line-height: 1.25; letter-spacing: .04em; max-width: 92vw; }
        .prompt-pop .pp-img { max-height: 42vh; max-width: 80vw; width: auto; height: auto; object-fit: contain; animation: quietFloat 3.4s ease-in-out infinite; }
        .prompt-pop .pp-close { position: absolute; top: 18px; right: 22px; border: 0; border-radius: 14px; padding: 10px 18px; font-size: 18px; font-weight: 900;
          background: rgba(255,255,255,.85); color: #173f3a; cursor: pointer; box-shadow: 0 6px 16px -8px rgba(0,0,0,.35); font-family: inherit; }
        .prompt-pop .pp-bar { position: absolute; left: 0; bottom: 0; height: 10px; background: var(--pp-ink, #1f7a52); opacity: .55; transform-origin: left; }
        @media (prefers-reduced-motion: reduce) { .prompt-pop, .prompt-pop .pp-img { animation: none !important; } }
''')

# ---------------------------------------------------------------- HTML
rep('''          <div class="status-text" style="text-align:center;display:block">內建常用班級經營句，也可自訂文字；插圖：<a href="https://www.irasutoya.com/" target="_blank" rel="noopener">いらすとや</a>。純本機、不上傳。</div>
        </div>''', '''          <div class="status-text" style="text-align:center;display:block" id="promptCredit">內建常用班級經營句，也可自訂文字；插圖：<a href="https://www.irasutoya.com/" target="_blank" rel="noopener">いらすとや</a>。純本機、不上傳。</div>
          <details class="prompt-sched" id="promptSched">
            <summary>⏰ 定時自動跳出 <small id="promptSchedSummary"></small></summary>
            <div class="ps-breaks">
              <label for="promptBreakTimes">本校每節下課時間</label>
              <input id="promptBreakTimes" placeholder="例：09:20, 10:10, 11:10, 14:10, 15:00">
            </div>
            <div class="status-text">設定的時間一到，提示會自動蓋滿晨間大屏（任何分頁都會跳出），時間到自己收起；按 Esc 或「關閉」可以提早收。晨間大屏要開在投影的畫面上才看得到。</div>
            <div id="promptSchedList"></div>
            <div class="ps-actions">
              <button class="ghost-button" type="button" id="promptSchedAdd">＋ 新增定時提示</button>
              <button class="ghost-button" type="button" id="promptSchedPreview">▶ 預覽跳出畫面（10 秒）</button>
            </div>
          </details>
        </div>''')

# ---------------------------------------------------------------- JS：提示句加 id、新增內容
OLD_GROUPS_START = '''    const PROMPT_GROUPS = [
      { label: '🪑 上課秩序', items: [
        { text: '上課囉！眼睛看老師', img: 'class_focus.png' },
        { text: '坐姿端正，抬頭挺胸', img: 'class_focus.png' },
        { text: '動作快，三秒內坐好', img: 'class_focus.png' },
        { text: '發言請舉手，輪流說', img: 'raise_hand.png' },
        { text: '安靜！音量零級', img: 'quiet_usagi.png' },
        { text: '輕聲討論，別吵到隔壁組', img: 'quiet_cat.png' }
      ] },
      { label: '📚 作業與學習', items: [
        { text: '收作業囉，交給小組長', img: 'homework.png' },
        { text: '訂正完拿給老師檢查', img: 'homework.png' },
        { text: '寫完的同學自己再檢查一遍', img: 'homework.png' },
        { text: '閱讀時間，安靜看書', img: 'reading.png' },
        { text: '自習時間，完成自己的進度', img: 'reading.png' },
        { text: '不會的先圈起來，等一下問', img: 'raise_hand.png' }
      ] },
      { label: '🍱 生活作息', items: [
        { text: '下課先喝水、上廁所', img: 'drink_water.png' },
        { text: '吃飯不說話，細嚼慢嚥', img: 'quiet_cat.png' },
        { text: '午休時間，趴下休息', img: 'nap.png' },
        { text: '打掃時間，責任區掃乾淨', img: 'cleaning.png' },
        { text: '整理書包，檢查抽屜', img: 'cleaning.png' }
      ] },
      { label: '🚶 集合與移動', items: [
        { text: '排隊囉！快、靜、齊', img: 'line_up.png' },
        { text: '到走廊排隊，不推不擠', img: 'line_up.png' },
        { text: '上下樓梯靠右走、不奔跑', img: 'line_up.png' },
        { text: '專科教室集合，帶課本鉛筆盒', img: 'line_up.png' },
        { text: '準備放學：桌面清空、帶齊物品', img: 'cleaning.png' }
      ] }
    ];'''
NEW_GROUPS = '''    // id＝新插圖檔名（assets/art/cozy/prompt/<id>.webp）；img＝新圖還沒好之前用的舊圖
    const PROMPT_GROUPS = [
      { label: '🪑 上課秩序', items: [
        { id: 'focus_teacher', text: '上課囉！眼睛看老師', img: 'class_focus.png' },
        { id: 'sit_up', text: '坐姿端正，抬頭挺胸', img: 'class_focus.png' },
        { id: 'sit_fast', text: '動作快，三秒內坐好', img: 'class_focus.png' },
        { id: 'raise_hand', text: '發言請舉手，輪流說', img: 'raise_hand.png' },
        { id: 'quiet_zero', text: '安靜！音量零級', img: 'quiet_usagi.png' },
        { id: 'whisper', text: '輕聲討論，別吵到隔壁組', img: 'quiet_cat.png' },
        { id: 'back_to_class', text: '上課鐘響，回教室坐好', img: 'class_focus.png' },
        { id: 'prep_next', text: '準備下一節的課本和用品', img: 'homework.png' }
      ] },
      { label: '📚 作業與學習', items: [
        { id: 'hand_in', text: '收作業囉，交給小組長', img: 'homework.png' },
        { id: 'correction', text: '訂正完拿給老師檢查', img: 'homework.png' },
        { id: 'self_check', text: '寫完的同學自己再檢查一遍', img: 'homework.png' },
        { id: 'reading', text: '閱讀時間，安靜看書', img: 'reading.png' },
        { id: 'self_study', text: '自習時間，完成自己的進度', img: 'reading.png' },
        { id: 'circle_question', text: '不會的先圈起來，等一下問', img: 'raise_hand.png' }
      ] },
      { label: '🍱 生活作息', items: [
        { id: 'drink_toilet', text: '下課先喝水、上廁所', img: 'drink_water.png' },
        { id: 'lunch_prep', text: '午餐準備：洗手、拿餐具、排隊打菜', img: 'line_up.png' },
        { id: 'lunch', text: '吃飯不說話，細嚼慢嚥', img: 'quiet_cat.png' },
        { id: 'lunch_cleanup', text: '吃完收好餐具，擦乾淨桌面', img: 'cleaning.png' },
        { id: 'nap', text: '午休時間，趴下休息', img: 'nap.png' },
        { id: 'cleaning', text: '打掃時間，責任區掃乾淨', img: 'cleaning.png' },
        { id: 'recycle', text: '垃圾分類，做好資源回收', img: 'cleaning.png' },
        { id: 'tidy_bag', text: '整理書包，檢查抽屜', img: 'cleaning.png' }
      ] },
      { label: '🦷 衛生健康', items: [
        { id: 'brush_teeth', text: '飯後潔牙，刷牙三分鐘', img: 'drink_water.png' },
        { id: 'wash_hands', text: '吃飯前，先用肥皂洗手', img: 'drink_water.png' },
        { id: 'cover_cough', text: '咳嗽打噴嚏，記得摀住口鼻', img: 'raise_hand.png' },
        { id: 'rest_eyes', text: '眼睛休息一下，看看遠方', img: 'reading.png' }
      ] },
      { label: '🚶 集合與移動', items: [
        { id: 'line_up', text: '排隊囉！快、靜、齊', img: 'line_up.png' },
        { id: 'hallway', text: '到走廊排隊，不推不擠', img: 'line_up.png' },
        { id: 'stairs', text: '上下樓梯靠右走、不奔跑', img: 'line_up.png' },
        { id: 'special_room', text: '專科教室集合，帶課本鉛筆盒', img: 'line_up.png' },
        { id: 'go_home', text: '準備放學：桌面清空、帶齊物品', img: 'cleaning.png' },
        { id: 'go_home_line', text: '放學路隊，跟著路隊長走', img: 'line_up.png' }
      ] }
    ];
    // 新插圖（動森風）交件驗收後，把 id 加進來就會改用新圖；沒列的繼續用舊圖
    const PROMPT_ART_READY = new Set([]);
    const PROMPT_ART_DIR = 'assets/art/cozy/prompt/';
    function promptImgSrc(item) {
      if (item && PROMPT_ART_READY.has(item.id)) return PROMPT_ART_DIR + item.id + '.webp';
      return 'assets/irasutoya/' + ((item && item.img) || 'class_focus.png');
    }
    function updatePromptCredit() {
      const usingLegacy = PROMPTS.some(item => !PROMPT_ART_READY.has(item.id));
      $('promptCredit').innerHTML = '內建常用班級經營句，也可自訂文字' +
        (usingLegacy ? '；部分插圖：<a href="https://www.irasutoya.com/" target="_blank" rel="noopener">いらすとや</a>' : '') + '。純本機、不上傳。';
    }'''
rep(OLD_GROUPS_START, NEW_GROUPS)
rep('''    // 分類色：上課秩序綠、作業藍、生活橘、集合紫
    const PROMPT_THEMES = [['#1f7a52', '#e3f3ea', '#bfe3cf', 'linear-gradient(160deg,#e6f6ec,#fff 70%)'],
      ['#2457e6', '#e7edfc', '#c7d4f7', 'linear-gradient(160deg,#e9eefc,#fff 70%)'],
      ['#d0631a', '#fdeee2', '#f6cfb0', 'linear-gradient(160deg,#fff0e4,#fff 70%)'],
      ['#7b4fb8', '#f1eafa', '#dccbf3', 'linear-gradient(160deg,#f3ecfb,#fff 70%)']];''', '''    // 分類色：上課秩序綠、作業藍、生活橘、衛生健康青、集合紫
    const PROMPT_THEMES = [['#1f7a52', '#e3f3ea', '#bfe3cf', 'linear-gradient(160deg,#e6f6ec,#fff 70%)'],
      ['#2457e6', '#e7edfc', '#c7d4f7', 'linear-gradient(160deg,#e9eefc,#fff 70%)'],
      ['#d0631a', '#fdeee2', '#f6cfb0', 'linear-gradient(160deg,#fff0e4,#fff 70%)'],
      ['#0f8a8a', '#e0f4f4', '#bde5e5', 'linear-gradient(160deg,#e3f6f6,#fff 70%)'],
      ['#7b4fb8', '#f1eafa', '#dccbf3', 'linear-gradient(160deg,#f3ecfb,#fff 70%)']];''')
rep("      $('promptImg').src = 'assets/irasutoya/' + preset.img;", "      $('promptImg').src = promptImgSrc(preset);")
# LINE 遠端：同一句話就用那句的插圖
rep("""          $('promptImg').src = 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(prompt.img || '')) ? prompt.img : 'class_focus.png');""",
    """          const known = PROMPTS.find(item => item.text === prompt.text);
          $('promptImg').src = known ? promptImgSrc(known) : 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(prompt.img || '')) ? prompt.img : 'class_focus.png');""")

# ---------------------------------------------------------------- JS：定時自動跳出
SCHED = r'''
    updatePromptCredit();

    // ⏰ 定時自動跳出：指定時間（可多個）或「每節下課」，選星期重複；時間到蓋滿整個大屏，幾分鐘後自己收
    const presetById = id => PROMPTS.find(item => item.id === id);
    const DAY_NAMES = ['日', '一', '二', '三', '四', '五', '六'];
    if (typeof config.promptBreakTimes !== 'string') config.promptBreakTimes = '09:20, 10:10, 11:10, 14:10, 15:00';
    if (!Array.isArray(config.promptSchedules)) {
      // 第一次使用給兩個範例（先不啟用，老師勾了才會跳）
      config.promptSchedules = [
        { id: 's1', on: false, mode: 'breaks', times: '', days: [1, 2, 3, 4, 5], preset: 'drink_toilet', text: '', minutes: 3, chime: true },
        { id: 's2', on: false, mode: 'times', times: '12:35', days: [1, 2, 3, 4, 5], preset: 'brush_teeth', text: '', minutes: 5, chime: true }
      ];
      saveConfig();
    }
    $('promptBreakTimes').value = config.promptBreakTimes;
    function parseTimes(textValue) {
      return String(textValue || '').split(/[,，、\s]+/).map(t => t.trim()).filter(Boolean)
        .map(t => { const m = t.match(/^(\d{1,2})[:：](\d{2})$/); return m && +m[1] < 24 && +m[2] < 60 ? String(+m[1]).padStart(2, '0') + ':' + m[2] : null; })
        .filter(Boolean);
    }
    function entryTimes(entry) { return parseTimes(entry.mode === 'breaks' ? config.promptBreakTimes : entry.times); }
    function entryText(entry) { const p = presetById(entry.preset); return entry.text.trim() || (p ? p.text : ''); }
    const presetOptions = PROMPT_GROUPS.map(group => `<optgroup label="${group.label}">${group.items.map(item =>
      `<option value="${item.id}">${escapeHtml(item.text)}</option>`).join('')}</optgroup>`).join('') + '<option value="">（自己打一句）</option>';
    function renderSchedules() {
      const list = config.promptSchedules;
      $('promptSchedList').innerHTML = list.map((entry, i) => `
        <div class="ps-row${entry.on ? '' : ' off'}" data-ps="${i}">
          <label title="啟用"><input type="checkbox" data-ps-field="on" ${entry.on ? 'checked' : ''}> 啟用</label>
          <div class="ps-when">
            <select data-ps-field="mode"><option value="breaks" ${entry.mode === 'breaks' ? 'selected' : ''}>每節下課</option><option value="times" ${entry.mode === 'times' ? 'selected' : ''}>指定時間</option></select>
            <input type="text" data-ps-field="times" value="${escapeHtml(entry.times)}" placeholder="例：12:35, 15:50" ${entry.mode === 'breaks' ? 'hidden' : ''}>
          </div>
          <div class="ps-days">${[1, 2, 3, 4, 5, 6, 0].map(d => `<button type="button" data-ps-day="${d}" class="${entry.days.includes(d) ? 'on' : ''}">${DAY_NAMES[d]}</button>`).join('')}</div>
          <div class="ps-what">
            <select data-ps-field="preset">${presetOptions}</select>
            <input type="text" data-ps-field="text" value="${escapeHtml(entry.text)}" placeholder="或自己打一句（會蓋過上面）" maxlength="40">
          </div>
          <label>顯示 <input type="number" data-ps-field="minutes" min="1" max="30" value="${entry.minutes}"> 分</label>
          <label><input type="checkbox" data-ps-field="chime" ${entry.chime ? 'checked' : ''}> 響鈴</label>
          <button class="ps-del" type="button" data-ps-del="${i}" title="刪除">🗑</button>
        </div>`).join('');
      list.forEach((entry, i) => {
        const sel = $('promptSchedList').querySelector(`[data-ps="${i}"] [data-ps-field="preset"]`);
        if (sel) sel.value = entry.preset || '';
      });
      const active = list.filter(e => e.on && e.days.length && entryTimes(e).length);
      $('promptSchedSummary').textContent = active.length ? `已啟用 ${active.length} 個` : '尚未啟用';
    }
    $('promptSchedList').addEventListener('input', event => {
      const row = event.target.closest('[data-ps]');
      const field = event.target.dataset.psField;
      if (!row || !field) return;
      const entry = config.promptSchedules[Number(row.dataset.ps)];
      if (field === 'on' || field === 'chime') entry[field] = event.target.checked;
      else if (field === 'minutes') entry.minutes = Math.max(1, Math.min(30, Number(event.target.value) || 3));
      else entry[field] = event.target.value;
      saveConfig();
      if (field === 'on' || field === 'mode' || field === 'preset') renderSchedules();
      else $('promptSchedSummary').textContent = config.promptSchedules.some(e => e.on) ? `已啟用 ${config.promptSchedules.filter(e => e.on).length} 個` : '尚未啟用';
    });
    $('promptSchedList').addEventListener('click', event => {
      const dayBtn = event.target.closest('[data-ps-day]');
      const del = event.target.closest('[data-ps-del]');
      if (dayBtn) {
        const entry = config.promptSchedules[Number(dayBtn.closest('[data-ps]').dataset.ps)];
        const d = Number(dayBtn.dataset.psDay);
        entry.days = entry.days.includes(d) ? entry.days.filter(x => x !== d) : entry.days.concat(d);
        saveConfig(); renderSchedules();
      } else if (del) {
        config.promptSchedules.splice(Number(del.dataset.psDel), 1);
        saveConfig(); renderSchedules();
      }
    });
    $('promptBreakTimes').addEventListener('change', () => {
      const times = parseTimes($('promptBreakTimes').value);
      config.promptBreakTimes = times.join(', ');
      $('promptBreakTimes').value = config.promptBreakTimes;
      saveConfig(); renderSchedules();
      showToast(times.length ? `下課時間：${times.length} 個` : '沒有讀到時間，請用 09:20 這種格式。', !times.length);
    });
    $('promptSchedAdd').addEventListener('click', () => {
      config.promptSchedules.push({ id: 's' + Date.now().toString(36), on: true, mode: 'times', times: '', days: [1, 2, 3, 4, 5], preset: 'focus_teacher', text: '', minutes: 3, chime: true });
      saveConfig(); renderSchedules();
      $('promptSched').open = true;
    });
    renderSchedules();

    // 跳出畫面
    const pop = document.createElement('div');
    pop.className = 'prompt-pop';
    pop.hidden = true;
    pop.innerHTML = '<button class="pp-close" type="button">✕ 關閉（Esc）</button><div class="pp-clock"></div><div class="pp-msg"></div><img class="pp-img" alt=""><div class="pp-bar"></div>';
    document.body.appendChild(pop);
    let popTimer = 0, popUntil = 0, popTotal = 0;
    function popHost() { return document.fullscreenElement || document.body; }
    function placePop() { if (!pop.hidden && pop.parentNode !== popHost()) popHost().appendChild(pop); }
    document.addEventListener('fullscreenchange', placePop);
    function closePop() { pop.hidden = true; clearInterval(popTimer); popTimer = 0; }
    function tickPop() {
      const now = Date.now();
      const d = new Date();
      pop.querySelector('.pp-clock').textContent = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      pop.querySelector('.pp-bar').style.width = Math.max(0, (popUntil - now) / popTotal * 100) + '%';
      if (now >= popUntil) closePop();
    }
    function showPop(entryOrItem, seconds, chime) {
      const item = entryOrItem.preset !== undefined ? presetById(entryOrItem.preset) : entryOrItem;
      const text = entryOrItem.preset !== undefined ? entryText(entryOrItem) : entryOrItem.text;
      const index = item ? PROMPTS.indexOf(item) : -1;
      const theme = PROMPT_THEMES[(index >= 0 ? promptGroupOf[index] : 0) % PROMPT_THEMES.length];
      pop.style.setProperty('--pb', theme[3]);
      pop.style.setProperty('--pp-ink', theme[0]);
      pop.querySelector('.pp-msg').textContent = text;
      const img = pop.querySelector('.pp-img');
      img.hidden = !item;
      if (item) img.src = promptImgSrc(item);
      popTotal = seconds * 1000; popUntil = Date.now() + popTotal;
      pop.hidden = false;
      placePop();
      clearInterval(popTimer); popTimer = setInterval(tickPop, 500); tickPop();
      if (chime) { beep(784, .18, 'sine', .12); setTimeout(() => beep(988, .18, 'sine', .12), 220); setTimeout(() => beep(1319, .32, 'sine', .12), 440); }
      // 提示分頁也同步成這一句
      if (item && index >= 0) { select.value = String(index); $('promptCustomText').value = entryOrItem.preset !== undefined ? (entryOrItem.text || '') : ''; applyPrompt(false); }
    }
    pop.querySelector('.pp-close').addEventListener('click', closePop);
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && !pop.hidden) closePop(); });
    $('promptSchedPreview').addEventListener('click', () => {
      const entry = config.promptSchedules.find(e => e.on) || config.promptSchedules[0];
      if (entry) showPop(entry, 10, entry.chime); else showPop(PROMPTS[0], 10, true);
    });
    // 每 10 秒檢查；同一天同一個時間只跳一次（重新整理頁面也不會重跳），在顯示時間內打開大屏仍會補跳
    day.promptFired = day.promptFired && typeof day.promptFired === 'object' ? day.promptFired : {};
    function checkSchedules() {
      const now = new Date();
      const minutesNow = now.getHours() * 60 + now.getMinutes();
      for (const entry of config.promptSchedules) {
        if (!entry.on || !entry.days.includes(now.getDay()) || !entryText(entry)) continue;
        for (const t of entryTimes(entry)) {
          const [h, m] = t.split(':').map(Number);
          const start = h * 60 + m;
          const key = entry.id + '@' + t;
          if (minutesNow >= start && minutesNow < start + entry.minutes && !day.promptFired[key]) {
            day.promptFired[key] = Date.now();
            saveDay();
            const left = (start + entry.minutes) * 60 - (minutesNow * 60 + now.getSeconds());
            showPop(entry, Math.max(20, left), entry.chime);
            return;
          }
        }
      }
    }
    setInterval(checkSchedules, 10000);
    setTimeout(checkSchedules, 1500);
'''
rep('''    $('promptFullscreenButton').addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();''', SCHED + '''    $('promptFullscreenButton').addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();''')

path.write_text(s, encoding='utf-8')
print('ok', len(s))
