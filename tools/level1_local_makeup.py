"""2026-11-05 老師：第 1 級也要能補交前幾天的作業，紀錄在這台電腦留 30 天。
補交與訂正統計改成沒接雲端時從本機讀，資料格式和雲端的 classroom_missing 一樣，畫面不用改。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rep(text, old, new):
    assert text.count(old) == 1, (old[:70], text.count(old))
    return text.replace(old, new)


# ---------- 大屏 ----------
p = ROOT / 'Morning.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '''    body.local-only .tab-button[data-page="makeup"], body.local-only .tab-button[data-page="query"],
    body.local-only #submitButton''', '''    body.local-only .tab-button[data-page="query"],
    body.local-only #submitButton''')
t = rep(t, '（要在家寫聯絡本、看補交與統計才填）', '（要在家寫聯絡本、看查詢統計才填）')
t = rep(t, '想在家寫聯絡本、看補交與統計：<a href', '想在家寫聯絡本、看查詢統計：<a href')
t = rep(t, "if (active && ['makeup', 'query'].includes(active.dataset.page)) document", "if (active && active.dataset.page === 'query') document")
t = rep(t, "key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -7)) localStorage.removeItem(key);", "key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -LOCAL_KEEP_DAYS)) localStorage.removeItem(key);")
t = rep(t, "    const STATE_PREFIX = 'morningBoardState:';\n", "    const STATE_PREFIX = 'morningBoardState:';\n    const LOCAL_KEEP_DAYS = 30;   // 點名與作業在這台電腦留 30 天，第 1 級的補交靠它\n")
t = rep(t, """    // ---------- 作業補交 ----------
    async function loadMakeup() {
""", """    // ---------- 第 1 級：前幾天的作業從這台電腦讀 ----------
    const localDays = () => Math.min(state.settings.lookbackDays, LOCAL_KEEP_DAYS);
    function localDayKey(date) { return STATE_PREFIX + date + classKeySuffix(); }
    function localDayBoards(date) {
      try {
        const saved = JSON.parse(localStorage.getItem(localDayKey(date)) || 'null');
        return saved && Array.isArray(saved.boards) ? saved.boards : [];
      } catch (error) { return []; }
    }
    /** 回傳格式和雲端的 classroom_missing 一樣。今天的在「作業繳交」直接改，所以只列前幾天。 */
    function localMissingReport() {
      const to = todayKey(), from = shiftDate(to, -(localDays() - 1));
      const pending = [], corrections = [];
      for (let date = from; date < to; date = shiftDate(date, 1)) {
        localDayBoards(date).forEach(board => {
          if (!board || !board.subject || !board.seats) return;
          activeSeats().forEach(seat => {
            const row = { date, subject: board.subject, assignment: board.assignment || '', seat };
            const mark = board.seats[seat];
            if (!mark) pending.push({ ...row, status: '缺交' });
            else if (mark === 'correcting') { pending.push({ ...row, status: '待訂正' }); corrections.push({ ...row, status: '待訂正' }); }
            else if (mark === 'corrected') corrections.push({ ...row, status: '已訂正' });
          });
        });
      }
      return { from, to, pending, corrections };
    }
    /** 把前幾天的一筆改成補交或訂正完成，回傳改了幾筆。 */
    function localMarkDone({ date, subject, assignment, seat }) {
      const key = localDayKey(date);
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem(key) || 'null'); } catch (error) {}
      const boards = saved && Array.isArray(saved.boards) ? saved.boards : [];
      const board = boards.find(item => item.subject === subject && (item.assignment || '') === (assignment || '')
        && item.seats && (!item.seats[seat] || item.seats[seat] === 'correcting'));
      if (!board) return 0;
      board.seats[seat] = board.seats[seat] === 'correcting' ? 'corrected' : 'resub';
      localStorage.setItem(key, JSON.stringify(saved));
      return 1;
    }

    // ---------- 作業補交 ----------
    async function loadMakeup() {
      if (!hasCloud()) {
        const report = localMissingReport();
        state.makeup.items = report.pending;
        state.makeup.loaded = true;
        const correctingCount = report.pending.filter(item => item.status === '待訂正').length;
        $('makeupStatus').textContent = `這台電腦近 ${localDays()} 天：缺交 ${report.pending.length - correctingCount} 筆`
          + (correctingCount ? `、待訂正 ${correctingCount} 筆` : '') + '。學生補交或訂正完成後點號碼。';
        renderMakeup();
        return;
      }
""")
t = rep(t, """    async function loadCorrectStats() {
""", """    async function loadCorrectStats() {
      if (!hasCloud()) {
        const all = localMissingReport().corrections;
        state.correct.items = all.filter(item => item.status === '待訂正');
        state.correct.doneCount = all.length - state.correct.items.length;
        state.correct.loaded = true;
        $('correctStatus').textContent = `這台電腦近 ${localDays()} 天：待訂正 ${state.correct.items.length} 筆`
          + (state.correct.doneCount ? `（另有 ${state.correct.doneCount} 筆已完成，不列出）` : '');
        renderCorrectStats();
        return;
      }
""")
t = rep(t, """      if (!state.settings.className || !state.settings.classroomToken) {
        return showToast('要處理前幾天的訂正，請先在「設定」填入班級名稱與教室金鑰。', true);
      }
      try {
        const result = await callGas({
          action: 'homework_resubmit', token: state.settings.classroomToken, className: currentClass(),
          date, subject, assignment, seat
        });
        if (!result.updated) showToast('雲端找不到這一筆（可能已處理過），已從清單移除。');""", """      if (hasCloud() && !state.settings.className) {
        return showToast('要處理前幾天的訂正，請先在「設定」填入班級名稱。', true);
      }
      try {
        const result = !hasCloud() ? { updated: localMarkDone({ date, subject, assignment, seat }) } : await callGas({
          action: 'homework_resubmit', token: state.settings.classroomToken, className: currentClass(),
          date, subject, assignment, seat
        });
        if (!result.updated) showToast('找不到這一筆（可能已處理過），已從清單移除。');""")
t = rep(t, """        const result = await callGas({ action: 'homework_resubmit', token: state.settings.classroomToken, className: currentClass(), date: item.date,""", """        const result = !hasCloud() ? { updated: localMarkDone(item) } : await callGas({ action: 'homework_resubmit', token: state.settings.classroomToken, className: currentClass(), date: item.date,""")
t = rep(t, "if (!result.updated) showToast('雲端找不到這筆紀錄（可能已處理過），已從清單移除。');", "if (!result.updated) showToast('找不到這筆紀錄（可能已處理過），已從清單移除。');")
p.write_text(t, encoding='utf-8', newline='\n')

# ---------- 測試 ----------
p = ROOT / 'tests/profile_config.test.js'
t = p.read_text(encoding='utf-8')
t = rep(t, '''assert.match(morningLevelSource, /body\\.local-only \\.tab-button\\[data-page="makeup"\\]/, "第 1 級應收起作業補交");
''', '''assert.match(morningLevelSource, /body\\.local-only \\.tab-button\\[data-page="query"\\]/, "第 1 級應收起查詢統計");
assert.doesNotMatch(morningLevelSource, /body\\.local-only \\.tab-button\\[data-page="makeup"\\]/, "第 1 級也要能補交");
assert.match(morningLevelSource, /LOCAL_KEEP_DAYS = 30/, "點名與作業應在本機留 30 天");
assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -LOCAL_KEEP_DAYS\\)/, "清舊資料要照 30 天");
''')
p.write_text(t, encoding='utf-8', newline='\n')

# ---------- 教學 ----------
p = ROOT / 'Install.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '點名、收作業、訂正、黑板聯絡本、班級工具</text>', '點名、收作業、補交、訂正、黑板聯絡本、班級工具</text>')
t = rep(t, '在家寫聯絡本、作業補交、查詢統計、雲端備份</text>', '在家寫聯絡本、查詢統計、跨電腦同步、雲端備份</text>')
t = rep(t, '<tr><td>教室大屏點名、收作業、訂正、黑板聯絡本、班級工具</td>', '<tr><td>教室大屏點名、收作業、補交、訂正、黑板聯絡本、班級工具</td>')
t = rep(t, '<tr><td>在家寫聯絡本隔天黑板出現、作業補交、查詢統計、任務清單', '<tr><td>在家寫聯絡本隔天黑板出現、查詢統計、平板和大屏同步、任務清單')
t = rep(t, '<div class="box"><strong>第 1 級看不到的：</strong>「作業補交」「查詢統計」兩個分頁要看前幾天的資料，接上第 2 級才會出現。</div>',
        '<div class="box"><strong>前幾天沒交的作業：</strong>到「作業補交」分頁，學生補來了就點掉號碼。點名與作業的紀錄在這台電腦留 <strong>30 天</strong>，超過會自動清掉。<br><strong>第 1 級看不到的：</strong>「查詢統計」要接上第 2 級才會出現。之後接上第 2 級時，補交改看雲端，這台電腦以前的紀錄不會搬上去。</div>')
t = rep(t, '接好後可以在家寫聯絡本、隔天黑板自動出現，還多了作業補交與查詢統計。', '接好後可以在家寫聯絡本、隔天黑板自動出現，平板和大屏同步，還多了查詢統計。')
t = rep(t, '✔ 檢查：上排多出「作業補交」「查詢統計」，左下出現', '✔ 檢查：上排多出「查詢統計」，左下出現')
t = rep(t, '<tr><td>下課<br><span class="lead">第 2 級</span></td>', '<tr><td>下課</td>')
t = rep(t, '統計要看得到前幾天，必須做到第 2 級（「設定」填入「班級名稱」、🌐A 與 🔑B）', '統計，第 1 級只看這台電腦近 30 天；做到第 2 級（「設定」填入「班級名稱」、🌐A 與 🔑B）才看雲端')
t = rep(t, '<tr><td>大屏看不到「作業補交」「查詢統計」「存到雲端」</td>', '<tr><td>大屏看不到「查詢統計」「存到雲端」</td>')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'About.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '<td>點名、收作業、訂正、黑板聯絡本、班級工具。資料只存這台電腦，不含機敏資料</td>', '<td>點名、收作業、補交、訂正、黑板聯絡本、班級工具。資料只存這台電腦，不含機敏資料；點名與作業留 30 天</td>')
t = rep(t, '<td>在家寫聯絡本、作業補交、查詢統計、任務', '<td>在家寫聯絡本、查詢統計、平板和大屏同步、任務')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'Intro.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '<p>點名、收作業、訂正、黑板聯絡本、班級工具。打開網址、填班級和座號就開始。', '<p>點名、收作業、補交、訂正、黑板聯絡本、班級工具。打開網址、填班級和座號就開始。')
t = rep(t, '在家寫聯絡本、作業補交、查詢統計、任務與教學進度', '在家寫聯絡本、查詢統計、平板和大屏同步、任務與教學進度')
p.write_text(t, encoding='utf-8', newline='\n')
print('done')
