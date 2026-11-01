"""晨間大屏 G10 多班模式（2026-11 升級規格書・組 C）：
- 設定頁新增「我教的班級」（頓號／逗號分隔；留空＝只有「班級名稱」一班，行為與舊版相同）→ settings.classes
- 兩班以上時，左上角班級名稱旁出現班級切換鈕；目前班存在 localStorage morningCurrentClass
- 每班一份：計分板（分數、隊名、組數）、檢核板、抽籤已抽名單、分組結果、作業繳交版面
  存法：既有 key 後面加「:班級」；第一個班沿用舊 key（舊資料零遷移）
- 點名、旗標、聯絡本、定時提示仍屬第一個班；自動推播（點名／點名＋作業）只送第一個班
- 存到雲端（rollcall_submit）、補交與訂正（classroom_missing／homework_resubmit）用目前的班
python tools/upgrade_morning_multiclass_2026_11.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
raw = path.read_bytes().decode('utf-8')
crlf = '\r\n' in raw
s = raw.replace('\r\n', '\n')
assert 'morningCurrentClass' not in s, '已套用過'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ---------- 樣式 ----------
rep('''    .brand { font-size: 20px; font-weight: 900; color: var(--primary-strong); }
''', '''    .brand { font-size: 20px; font-weight: 900; color: var(--primary-strong); }
    /* G10 多班模式：班級切換鈕（只有設定兩班以上才出現） */
    .class-switch { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    .class-switch[hidden] { display: none; }
    .class-pill { border: 2px solid var(--line); background: var(--surface); color: var(--primary-strong); border-radius: 999px; padding: 3px 14px; font-size: 16px; font-weight: 900; cursor: pointer; font-family: inherit; }
    .class-pill.active { background: var(--primary); border-color: var(--primary); color: #fff; }
    .class-switch-note { font-size: 13px; font-weight: 700; color: var(--muted); }
''')

# ---------- 頂部切換鈕 ----------
rep('''    <div class="brand" id="classNameLabel">晨間大屏</div>
''', '''    <div class="brand" id="classNameLabel">晨間大屏</div>
    <div class="class-switch" id="classSwitch" hidden></div>
''')

# ---------- 設定頁欄位 ----------
rep('''          <div class="field"><label>班級名稱（例：601）</label><input id="setupClassName" maxlength="20" placeholder="601"></div>
''', '''          <div class="field"><label>班級名稱（例：601）</label><input id="setupClassName" maxlength="20" placeholder="601"></div>
          <div class="field"><label>我教的班級（科任多班用，例：601、602、603）</label><input id="setupClasses" maxlength="160" placeholder="留空＝只有上面這一班">
            <div class="status-text" style="margin-top:4px">用頓號或逗號分隔。第一個班＝上面的「班級名稱」，點名、聯絡本、自動推播都只屬於它。設兩班以上時，左上角會出現班級切換鈕；計分板、檢核板、抽籤已抽名單、分組結果與作業繳交版面每班各一份，切班不互蓋。座號範圍與空號各班共用下方的設定。</div></div>
''')

# ---------- 設定預設值與 dirty 旗標 ----------
rep('''        className: '', boardTitle: '晨間大屏', contactFont: 'default',''',
    '''        className: '', classes: [], boardTitle: '晨間大屏', contactFont: 'default',''')
rep('''      dirty: false,          // 有未存到雲端的異動；每 5 分鐘與離開頁面時自動存檔
''', '''      dirty: false,          // 有未存到雲端的異動；每 5 分鐘與離開頁面時自動存檔
      dirtyFirst: false,     // 多班模式：在別班畫面改到第一個班的點名，也要存回第一個班
''')

# ---------- 多班 helper（放在設定載入之前） ----------
rep('''    // ---------- 設定（含 v1 → v2 遷移） ----------
    function loadSettings() {''', r'''    // ---------- 多班模式（G10）：第一個班＝className、沿用舊 key；其他班的 key 後面加「:班級」 ----------
    const CURRENT_CLASS_KEY = 'morningCurrentClass';
    /** 把「601、602」整理成不重複的班級陣列，第一個固定是 className；不到兩班就回傳 []（單班＝舊行為）。 */
    function normalizeClassList(className, list) {
      const items = (Array.isArray(list) ? list : String(list || '').split(/[、,，;；\s]+/))
        .map(value => String(value || '').trim().slice(0, 20)).filter(Boolean);
      const out = [];
      [String(className || '').trim(), ...items].forEach(name => { if (name && !out.includes(name)) out.push(name); });
      return out.length >= 2 ? out.slice(0, 12) : [];
    }
    function isMultiClass() { return state.settings.classes.length >= 2; }
    function teachingClasses() { return isMultiClass() ? state.settings.classes : [state.settings.className]; }
    function firstClass() { return teachingClasses()[0]; }
    function currentClass() {
      if (!isMultiClass()) return state.settings.className;
      let saved = '';
      try { saved = localStorage.getItem(CURRENT_CLASS_KEY) || ''; } catch (error) {}
      return state.settings.classes.includes(saved) ? saved : state.settings.classes[0];
    }
    function isFirstClass() { return currentClass() === firstClass(); }
    /** 第一個班（或單班）回傳 ''＝舊 key；其他班回傳「:602」。 */
    function classKeySuffix(cls = currentClass()) {
      return !isMultiClass() || cls === state.settings.classes[0] ? '' : ':' + cls;
    }

    // ---------- 設定（含 v1 → v2 遷移） ----------
    function loadSettings() {''')

rep('''          s.className = String(saved.className || '');
''', '''          s.className = String(saved.className || '');
          s.classes = normalizeClassList(s.className, saved.classes);
          if (!s.className && s.classes.length) s.className = s.classes[0];
''')

# ---------- 當日狀態：作業繳交版面每班一份 ----------
rep('''      } catch (error) {}
      for (let index = localStorage.length - 1; index >= 0; index -= 1) {
        const key = localStorage.key(index);
        if (key && key.startsWith(STATE_PREFIX) && key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -7)) localStorage.removeItem(key);
      }
    }
    function saveTodayState() {
      state.dirty = true;   // 有異動就標記；autoCloudSaveTick 會在 5 分鐘內存到雲端（不推播）
      localStorage.setItem(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: state.boards, flags: state.flags }));
    }''', '''      } catch (error) {}
      // 多班模式且目前不是第一個班：點名與旗標照舊讀第一個班，作業繳交版面改讀本班的「:班級」key
      if (classKeySuffix()) state.boards = loadClassBoards(classKeySuffix());
      for (let index = localStorage.length - 1; index >= 0; index -= 1) {
        const key = localStorage.key(index);
        if (key && key.startsWith(STATE_PREFIX) && key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -7)) localStorage.removeItem(key);
      }
    }
    /** 讀某一班今天的作業繳交版面（suffix ''＝第一個班的舊 key）。 */
    function loadClassBoards(suffix) {
      try {
        const saved = JSON.parse(localStorage.getItem(STATE_PREFIX + todayKey() + suffix) || 'null');
        const boards = saved && Array.isArray(saved.boards) ? saved.boards.filter(board => board && board.subject) : [];
        const seenIds = new Set();
        boards.forEach(board => {
          if (!board.id || seenIds.has(board.id)) board.id = `b${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
          seenIds.add(board.id);
        });
        return boards;
      } catch (error) { return []; }
    }
    function saveTodayState() {
      state.dirty = true;   // 有異動就標記；autoCloudSaveTick 會在 5 分鐘內存到雲端（不推播）
      const suffix = classKeySuffix();
      if (!suffix) {
        localStorage.setItem(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: state.boards, flags: state.flags }));
        return;
      }
      // 別班畫面：點名、旗標仍寫回第一個班的舊 key（保留第一個班的版面），本班版面寫到「:班級」key
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem(STATE_PREFIX + todayKey()) || 'null'); } catch (error) {}
      const firstBoards = saved && Array.isArray(saved.boards) ? saved.boards : [];
      if (JSON.stringify((saved && saved.attendance) || {}) !== JSON.stringify(state.attendance)) state.dirtyFirst = true;
      localStorage.setItem(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: firstBoards, flags: state.flags }));
      localStorage.setItem(STATE_PREFIX + todayKey() + suffix, JSON.stringify({ boards: state.boards }));
    }''')

# ---------- 送出雲端：作業用目前的班；點名只屬第一個班 ----------
rep('''    function buildSubmitPayload(push = 'none') {
      const seatsNow = new Set(activeSeats());
      const attendance = Object.entries(state.attendance)''', '''    function buildSubmitPayload(push = 'none', cls = currentClass()) {
      const seatsNow = new Set(activeSeats());
      // 多班模式：點名只屬於第一個班；作業版面用指定那一班的
      const isFirst = cls === firstClass();
      const boards = cls === currentClass() ? state.boards : loadClassBoards(classKeySuffix(cls));
      const attendance = (isFirst ? Object.entries(state.attendance) : [])''')
rep('''      const homework = state.boards.map(board => {
        const missing = [];
        const resubmitted = [];''', '''      const homework = boards.map(board => {
        const missing = [];
        const resubmitted = [];''')
rep('''date: todayKey(), className: state.settings.className, attendance, homework, push };''',
    '''date: todayKey(), className: cls, attendance, homework, push };''')

rep('''    async function submitReport({ auto = false, push = 'none', silent = false } = {}) {
      if (state.submitting) return;
      if (!state.settings.className) return auto || silent ? undefined : showToast('請先在「設定」填入班級名稱。', true);
      if (!state.settings.classroomToken) return auto || silent ? undefined : showToast('請先在「設定」填入教室大屏金鑰。', true);
      const blanks = activeSeats().filter(seat => !state.attendance[seat]).length;''', '''    async function submitReport({ auto = false, push = 'none', silent = false, cls = '' } = {}) {
      if (state.submitting) return;
      if (!state.settings.className) return auto || silent ? undefined : showToast('請先在「設定」填入班級名稱。', true);
      if (!state.settings.classroomToken) return auto || silent ? undefined : showToast('請先在「設定」填入教室大屏金鑰。', true);
      // 多班模式：推播（點名／點名＋作業）只送第一個班；一般存檔送目前畫面上的班
      const target = cls || (push !== 'none' ? firstClass() : currentClass());
      const classTag = isMultiClass() ? `【${target}】` : '';
      const blanks = target === firstClass() ? activeSeats().filter(seat => !state.attendance[seat]).length : 0;''')
rep('''        const result = await callGas(buildSubmitPayload(push));
        const time = new Date().toLocaleTimeString('zh-TW', { hour12: false });
        state.dirty = false;''', '''        const result = await callGas(buildSubmitPayload(push, target));
        const time = new Date().toLocaleTimeString('zh-TW', { hour12: false });
        if (target === currentClass()) state.dirty = false;
        if (target === firstClass()) state.dirtyFirst = false;''')
rep('''        $('submitStatus').textContent = silent
          ? `已自動存到雲端（${time}）。`
          : `已存到雲端（${time}${auto ? '・自動' : ''}）${pushedNote}。同一天重存會覆蓋更新。`;''', '''        $('submitStatus').textContent = classTag + (silent
          ? `已自動存到雲端（${time}）。`
          : `已存到雲端（${time}${auto ? '・自動' : ''}）${pushedNote}。同一天重存會覆蓋更新。`);''')

rep('''    function autoCloudSaveTick() {
      if (!state.dirty || state.submitting) return;
      if (!state.settings.className || !state.settings.classroomToken || !state.settings.gasUrl) return;
      submitReport({ silent: true, push: 'none' });
    }''', '''    async function autoCloudSaveTick() {
      if ((!state.dirty && !state.dirtyFirst) || state.submitting) return;
      if (!state.settings.className || !state.settings.classroomToken || !state.settings.gasUrl) return;
      if (state.dirty) await submitReport({ silent: true, push: 'none' });
      // 多班模式：在別班畫面改過第一個班的點名，也補存第一個班
      if (state.dirtyFirst && !isFirstClass()) await submitReport({ silent: true, push: 'none', cls: firstClass() });
    }''')
rep('''    function flushCloudSaveOnExit() {
      if (!state.dirty || !state.settings.className || !state.settings.classroomToken) return;
      const gasUrl = state.settings.gasUrl.trim();
      if (!/^https:\\/\\/script\\.google\\.com\\/macros\\//.test(gasUrl)) return;
      try {
        fetch(gasUrl, {
          method: 'POST', keepalive: true, redirect: 'follow', cache: 'no-store',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify(buildSubmitPayload('none'))
        }).catch(() => {});
        state.dirty = false;
      } catch (error) {}
    }''', '''    function flushCloudSaveOnExit() {
      if ((!state.dirty && !state.dirtyFirst) || !state.settings.className || !state.settings.classroomToken) return;
      const gasUrl = state.settings.gasUrl.trim();
      if (!/^https:\\/\\/script\\.google\\.com\\/macros\\//.test(gasUrl)) return;
      const targets = [];
      if (state.dirty) targets.push(currentClass());
      if (state.dirtyFirst && !targets.includes(firstClass())) targets.push(firstClass());
      try {
        targets.forEach(cls => fetch(gasUrl, {
          method: 'POST', keepalive: true, redirect: 'follow', cache: 'no-store',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify(buildSubmitPayload('none', cls))
        }).catch(() => {}));
        state.dirty = false;
        state.dirtyFirst = false;
      } catch (error) {}
    }''')

# 補交、訂正（作業相關）讀寫目前的班
rep("action: 'classroom_missing', token: state.settings.classroomToken, className: state.settings.className",
    "action: 'classroom_missing', token: state.settings.classroomToken, className: currentClass()", count=2)
rep("action: 'homework_resubmit', token: state.settings.classroomToken, className: state.settings.className",
    "action: 'homework_resubmit', token: state.settings.classroomToken, className: currentClass()", count=2)

# ---------- 設定畫面 ----------
rep('''    function applySettingsToUi() {
      const s = state.settings;
      $('classNameLabel').textContent = s.className ? `${s.className}｜${s.boardTitle}` : s.boardTitle;
      document.title = `${s.boardTitle}｜點名與作業繳交`;
      $('setupPin').value = s.setupPin;
      $('setupClassName').value = s.className;''', '''    function renderClassSwitch() {
      const s = state.settings;
      const shown = currentClass();
      $('classNameLabel').textContent = shown ? `${shown}｜${s.boardTitle}` : s.boardTitle;
      const host = $('classSwitch');
      if (!isMultiClass()) { host.hidden = true; host.innerHTML = ''; return; }
      host.hidden = false;
      host.innerHTML = s.classes.map(cls => `<button class="class-pill${cls === shown ? ' active' : ''}" type="button" data-class-pill="${escapeHtml(cls)}" title="切換到 ${escapeHtml(cls)}">${escapeHtml(cls)}</button>`).join('')
        + (shown !== s.classes[0] ? `<span class="class-switch-note">點名、聯絡本仍是 ${escapeHtml(s.classes[0])}</span>` : '');
    }
    /** 切班後重新載入這一班的作業版面，並通知班級工具換資料。 */
    function reloadClassData() {
      state.boards = loadClassBoards(classKeySuffix());
      state.makeup.items = []; state.makeup.loaded = false;
      state.correct.items = []; state.correct.loaded = false; state.correct.doneCount = 0;
      state.correct.sticky = []; state.correct.showSettled = false;
      renderClassSwitch();
      renderBoards();
      renderMakeup();
      renderCorrectStats();
      if ($('page-makeup').classList.contains('active')) loadMakeup();
      if ($('page-correct').classList.contains('active')) loadCorrectStats();
      document.dispatchEvent(new CustomEvent('morning:classchange', { detail: { className: currentClass(), suffix: classKeySuffix() } }));
    }
    function switchClass(cls) {
      if (!isMultiClass() || !state.settings.classes.includes(cls) || cls === currentClass()) return;
      // 抽籤動畫跑到一半不能切（結果會記到另一班）
      if (!document.dispatchEvent(new CustomEvent('morning:beforeclasschange', { cancelable: true }))) {
        showToast('抽籤進行中，抽完再切換班級。', true);
        return;
      }
      flushCloudSaveOnExit();   // 離開前把這班未存的異動送到雲端（不推播）
      try { localStorage.setItem(CURRENT_CLASS_KEY, cls); } catch (error) {}
      reloadClassData();
      showToast(`已切換到 ${cls}。`);
    }
    function applySettingsToUi() {
      const s = state.settings;
      renderClassSwitch();
      document.title = `${s.boardTitle}｜點名與作業繳交`;
      $('setupPin').value = s.setupPin;
      $('setupClassName').value = s.className;
      $('setupClasses').value = s.classes.join('、');''')

rep('''    function saveSetupFromForm() {
      const s = state.settings;
      s.setupPin = $('setupPin').value.trim().slice(0, 12);
      s.className = $('setupClassName').value.trim().slice(0, 20);
''', r'''    function saveSetupFromForm() {
      const s = state.settings;
      const classBefore = currentClass();
      const suffixBefore = classKeySuffix();
      s.setupPin = $('setupPin').value.trim().slice(0, 12);
      s.className = $('setupClassName').value.trim().slice(0, 20);
      const classItems = $('setupClasses').value.split(/[、,，;；\s]+/).map(value => value.trim().slice(0, 20)).filter(Boolean);
      if (!s.className && classItems.length) s.className = classItems[0];
      s.classes = normalizeClassList(s.className, classItems);
''')
rep('''      s.teacherToken = $('setupTeacherToken').value.trim();
      saveSettings();
      applySettingsToUi();
      showToast('設定已儲存。');''', '''      s.teacherToken = $('setupTeacherToken').value.trim();
      saveSettings();
      const classChanged = currentClass() !== classBefore || classKeySuffix() !== suffixBefore;
      applySettingsToUi();
      if (classChanged) reloadClassData();
      showToast('設定已儲存。');''')

# ---------- 事件 ----------
rep('''    $('submitButton').addEventListener('click', () => submitReport());
''', '''    $('submitButton').addEventListener('click', () => submitReport());
    $('classSwitch').addEventListener('click', event => {
      const pill = event.target.closest('[data-class-pill]');
      if (pill) switchClass(pill.dataset.classPill);
    });
''')

# ================= 班級工具（第二段 script） =================
rep('''  function saveConfig() { try { localStorage.setItem(CONFIG_KEY, JSON.stringify(config)); } catch (e) {} }
  function saveDay() { try { localStorage.setItem(DAY_PREFIX + todayKey(), JSON.stringify(day)); } catch (e) {} }
''', '''  function toolsClassSuffix() { return typeof classKeySuffix === 'function' ? classKeySuffix() : ''; }
  /** 把「共用欄位寫舊 key、本班欄位寫 :班級 key」拆開存；第一個班整包照舊存。 */
  function saveSplit(baseKey, obj, fields) {
    const suffix = toolsClassSuffix();
    if (!suffix) { localStorage.setItem(baseKey, JSON.stringify(obj)); return; }
    const stored = loadJson(baseKey, {});
    const shared = Object.assign({}, obj);
    const mine = {};
    fields.forEach(field => {
      mine[field] = obj[field];
      if (field in stored) shared[field] = stored[field]; else delete shared[field];
    });
    localStorage.setItem(baseKey, JSON.stringify(shared));
    localStorage.setItem(baseKey + suffix, JSON.stringify(mine));
  }
  function saveConfig() { try { saveSplit(CONFIG_KEY, config, CLASS_CONFIG_FIELDS); } catch (e) {} }
  function saveDay() { try { saveSplit(DAY_PREFIX + todayKey(), day, CLASS_DAY_FIELDS); } catch (e) {} }
  /** 切班（或開頁時目前不是第一個班）：重新讀這一班的計分板、檢核板、已抽名單、分組結果。 */
  function loadClassSlice() {
    const suffix = toolsClassSuffix();
    const mainDay = loadJson(DAY_PREFIX + todayKey(), {});
    const c = loadJson(CONFIG_KEY + suffix, {});
    const d = suffix ? loadJson(DAY_PREFIX + todayKey() + suffix, {}) : mainDay;
    CLASS_CONFIG_FIELDS.forEach(field => { if (field in c) config[field] = c[field]; else delete config[field]; });
    CLASS_DAY_FIELDS.forEach(field => { if (field in d) day[field] = d[field]; else delete day[field]; });
    config.teamNames = Array.isArray(config.teamNames) ? config.teamNames : [];
    // 第一個班沿用舊版「分數存在當日鍵」的搬移規則
    config.scores = Array.isArray(config.scores) ? config.scores
      : (!suffix && Array.isArray(mainDay.scores) && mainDay.scores.length ? mainDay.scores.slice() : []);
    day.drawn = Array.isArray(day.drawn) ? day.drawn : [];
    day.boards = Array.isArray(day.boards) ? day.boards : [{ name: config.checkNames[0], done: {}, showMiss: false }];
    day.groups = Array.isArray(day.groups) ? day.groups : [];
  }
''')
rep('''  config.scores = Array.isArray(config.scores) ? config.scores : (day.scores.length ? day.scores.slice() : []);
  cleanupOldDays();
''', '''  config.scores = Array.isArray(config.scores) ? config.scores : (day.scores.length ? day.scores.slice() : []);
  cleanupOldDays();
  // G10 多班模式：這些欄位每班一份。第一個班（或單班）沿用舊 key；其他班寫到「key:班級」。
  const CLASS_CONFIG_FIELDS = ['scores', 'teamNames', 'teamCount'];
  const CLASS_DAY_FIELDS = ['drawn', 'boards', 'groups'];
  if (toolsClassSuffix()) loadClassSlice();
''')

# 別班沒有點名資料：抽籤、分組、檢核板不排除第一個班的缺席
rep('''  function rollcallTaken() {
    return activeSeats()''', '''  function rollcallTaken() {
    if (toolsClassSuffix()) return false;   // 多班模式：點名只屬第一個班
    return activeSeats()''')
rep('''  function absentSeatSet() {
    const absent = new Set();
''', '''  function absentSeatSet() {
    const absent = new Set();
    if (toolsClassSuffix()) return absent;   // 多班模式：別班沒有點名資料，不排除任何人
''')
rep('''    let note = `座號 1～${s.seatCount}` + (empties.length ? `（空號 ${empties.join('、')}）` : '');
    if (excludeAbsent) {''', '''    let note = `座號 1～${s.seatCount}` + (empties.length ? `（空號 ${empties.join('、')}）` : '');
    if (excludeAbsent && toolsClassSuffix()) return note + `・${currentClass()} 沒有點名資料，不排除缺席`;
    if (excludeAbsent) {''')

# 分組結果存起來（每班一份），切班時畫回來
rep('''      groups.push(shuffled.slice(cursor, cursor + take));
      cursor += take;
    }
    const wall = $('groupWall');''', '''      groups.push(shuffled.slice(cursor, cursor + take));
      cursor += take;
    }
    day.groups = groups; saveDay();
    const wall = $('groupWall');''')
rep('''  // ================================================================
  // 🔇 安靜偵測
  // ================================================================
''', '''  /** 切班或重新整理時，把這一班上次的分組結果畫回來（不重播動畫）。 */
  function renderSavedGroups() {
    const wall = $('groupWall');
    if (!wall) return;
    wall.innerHTML = (day.groups || []).map((members, i) => {
      const [g, soft, line] = TEAM_COLORS[i % TEAM_COLORS.length];
      return `<div class="group-card" style="--g:${g};--g-soft:${soft};--g-line:${line}">
          <h4>第 ${i + 1} 組（${members.length} 人）</h4>
          <div class="members">${members.map(m => `<span>${escapeHtml(m)}</span>`).join('')}</div>
        </div>`;
    }).join('');
  }

  // ================================================================
  // 🔇 安靜偵測
  // ================================================================
''')

rep('''  updateLotStatus();
  renderCheckWall();
  renderScoreWall();
})();''', '''  updateLotStatus();
  renderCheckWall();
  renderScoreWall();
  // G10 多班模式：只有設定兩班以上才把上次分組畫回來（單班維持舊行為）
  if (typeof isMultiClass === 'function' && isMultiClass()) renderSavedGroups();
  document.addEventListener('morning:beforeclasschange', event => { if (lotteryBusy) event.preventDefault(); });
  document.addEventListener('morning:classchange', () => {
    loadClassSlice();
    $('lotResult').textContent = '？';
    $('lotResult').classList.remove('reveal');
    $('lotWheelHub').textContent = '🎯';
    lotStage.classList.remove('revealed', 'spinning');
    gacha.prize = null; gacha.key = '';
    wheelFx.win = -1; wheelFx.pool = null;
    updateLotStatus();
    renderCheckWall();
    renderScoreWall();
    renderSavedGroups();
  });
})();''')

out = s.replace('\n', '\r\n') if crlf else s
path.write_bytes(out.encode('utf-8'))
print('OK: Morning.html 已加入多班模式')
