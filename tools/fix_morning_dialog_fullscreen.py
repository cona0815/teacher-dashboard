"""大屏：按「設定」「全螢幕播放」沒反應（老師 2026-11-04 回報）
原因：有些瀏覽器環境不支援 window.prompt／confirm（prompt 直接丟錯、confirm 回 false），
      requestFullscreen 也可能被擋（報錯、或永遠沒有回應；iPhone 根本沒有這個 API）。
- 輸入與確認改成頁面內的視窗 askDialog()（設定密碼、倒數分鐘、檢核板名稱、四個確認）
- 全螢幕改走 fsEnter()／fsToggle()：真全螢幕 0.7 秒內沒成功，就改成鋪滿整個分頁（.fake-fs），Esc 或「離開全螢幕」鈕可退出
- CSS 的 :fullscreen 規則同時套用 .fake-fs，版面和真全螢幕一樣
python tools/fix_morning_dialog_fullscreen.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'askDialog' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- CSS ----------
assert s.count(':fullscreen') > 20, s.count(':fullscreen')
s = s.replace(':fullscreen', ':is(:fullscreen, .fake-fs)')
rep("""    /* ===== 倒數大時鐘（右上角按 5分／10分／開始 跳出） ===== */""", """    /* ===== 頁面內的輸入／確認視窗（取代瀏覽器的 prompt、confirm） ===== */
    .ask-pop { position: fixed; inset: 0; z-index: 100000; display: flex; align-items: center; justify-content: center; background: rgba(20, 36, 32, .45); }
    .ask-card { width: min(460px, 90vw); display: flex; flex-direction: column; gap: 14px; padding: 24px; border-radius: 20px; background: var(--surface); color: var(--ink); border: 3px solid var(--line); box-shadow: 0 24px 48px -16px rgba(0,0,0,.45); font-size: 18px; }
    .ask-msg { font-weight: 800; line-height: 1.5; white-space: pre-line; }
    .ask-input { width: 100%; box-sizing: border-box; border: 2px solid var(--line); border-radius: 10px; padding: 10px 12px; font-size: 20px; font-family: inherit; }
    .ask-actions { display: flex; justify-content: flex-end; gap: 10px; }
    html[data-board-style="cozy"] .ask-card { border-color: var(--cozy-wood); border-radius: 28px; box-shadow: 0 6px 0 var(--cozy-wood), 0 24px 48px -16px rgba(91,70,54,.45); }
    /* ===== 全螢幕備援：瀏覽器不給真全螢幕時，鋪滿整個分頁 ===== */
    .fake-fs { position: fixed !important; inset: 0; z-index: 9000; margin: 0 !important; width: auto !important; max-width: none !important; border-radius: 0 !important; overflow: auto; background-color: var(--bg); transition: none !important; }
    html.fake-fs-on body { overflow: hidden; }
    html.fake-fs-on header, html.fake-fs-on .submit-bar { visibility: hidden; }
    html.fake-fs-on .tool-panel { animation: none; }
    .fake-fs-exit { position: fixed; top: 14px; right: 18px; z-index: 9100; border: 2px solid var(--line); border-radius: 12px; background: var(--surface); color: var(--ink); padding: 8px 16px; font-size: 16px; font-weight: 900; font-family: inherit; cursor: pointer; }
    /* ===== 倒數大時鐘（右上角按 5分／10分／開始 跳出） ===== */""")

# ---------- 共用：放在時鐘、倒數前面，第二段 script 也用得到 ----------
rep("""    // ---------- 時鐘、倒數與自動化 ----------""", """    // ---------- 頁面內的輸入／確認視窗 ----------
    // 有些環境不支援 window.prompt／confirm（按了沒反應），一律用這個。回傳：輸入框的文字或 true；取消是 null
    let askClose = null;
    function askDialog({ message, input = false, value = '', password = false, numeric = false }) {
      if (askClose) askClose(null);
      return new Promise(resolve => {
        const box = document.createElement('div');
        box.className = 'ask-pop';
        box.innerHTML = `<form class="ask-card"><div class="ask-msg"></div>${input ? '<input class="ask-input">' : ''}<div class="ask-actions"><button class="ghost-button ask-cancel" type="button">取消</button><button class="primary-button" type="submit">確定</button></div></form>`;
        box.querySelector('.ask-msg').textContent = message;
        const field = box.querySelector('.ask-input');
        if (field) {
          field.type = password ? 'password' : 'text';
          field.value = value;
          field.autocomplete = 'off';
          if (numeric) field.inputMode = 'decimal';
        }
        const done = result => { askClose = null; box.remove(); resolve(result); };
        askClose = done;
        box.querySelector('form').addEventListener('submit', event => { event.preventDefault(); done(field ? field.value : true); });
        box.querySelector('.ask-cancel').addEventListener('click', () => done(null));
        box.addEventListener('mousedown', event => { if (event.target === box) done(null); });
        box.addEventListener('keydown', event => { event.stopPropagation(); if (event.key === 'Escape') done(null); });
        (fsCurrent() || document.body).appendChild(box);
        (field || box.querySelector('[type="submit"]')).focus();
        if (field) field.select();
      });
    }
    // ---------- 全螢幕：瀏覽器不給（報錯、沒回應或沒有這個功能）就鋪滿整個分頁 ----------
    let fakeFsEl = null;
    function fsCurrent() { return document.fullscreenElement || fakeFsEl; }
    function fsSetFake(el) {
      if (fakeFsEl) {
        fakeFsEl.classList.remove('fake-fs');
        const old = fakeFsEl.querySelector(':scope > .fake-fs-exit');
        if (old) old.remove();
      }
      fakeFsEl = el;
      document.documentElement.classList.toggle('fake-fs-on', !!el);
      if (el) {
        el.classList.add('fake-fs');
        const exit = document.createElement('button');
        exit.type = 'button';
        exit.className = 'fake-fs-exit';
        exit.textContent = '✕ 離開全螢幕';
        exit.addEventListener('click', () => fsSetFake(null));
        el.appendChild(exit);
      }
      document.dispatchEvent(new Event('fullscreenchange'));
    }
    function fsEnter(el) {
      if (!el) return;
      if (!el.requestFullscreen) return fsSetFake(el);
      let answered = false;
      el.requestFullscreen().then(() => { answered = true; }).catch(() => { answered = true; fsSetFake(el); });
      setTimeout(() => { if (!answered && !document.fullscreenElement) fsSetFake(el); }, 700);
    }
    function fsToggle(el) {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (fakeFsEl) fsSetFake(null);
      else fsEnter(el);
    }
    // 真全螢幕晚一點才成功時，收掉備援
    document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement && fakeFsEl) fsSetFake(null); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && fakeFsEl) fsSetFake(null); });

    // ---------- 時鐘、倒數與自動化 ----------""")

# ---------- 全螢幕按鈕 ----------
rep("""    if (document.fullscreenElement) document.exitFullscreen();
    else if (panel && panel.requestFullscreen) panel.requestFullscreen().catch(() => showToast('這個瀏覽器不支援全螢幕。', true));""", """    fsToggle(panel);""")
rep("""      if (document.fullscreenElement) document.exitFullscreen();
      else if (examBoard.requestFullscreen) examBoard.requestFullscreen().catch(() => showToast('這個瀏覽器不支援全螢幕。', true));""", """      fsToggle(examBoard);""")
rep("""      if (document.fullscreenElement) document.exitFullscreen();
      else if (board.requestFullscreen) board.requestFullscreen().catch(() => showToast('這個瀏覽器不支援全螢幕。', true));""", """      fsToggle(board);""")
rep("""      if (document.fullscreenElement) document.exitFullscreen();
      else if (promptBoard.requestFullscreen) promptBoard.requestFullscreen().catch(() => showToast('這個瀏覽器不支援全螢幕。', true));""", """      fsToggle(promptBoard);""")
helper_marker = 'function fsCurrent() { return document.fullscreenElement || fakeFsEl; }'
head, tail = s.split('// ---------- 頁面內的輸入／確認視窗 ----------', 1)
helper, rest = tail.split('// ---------- 時鐘、倒數與自動化 ----------', 1)
s = (head.replace('document.fullscreenElement', 'fsCurrent()') + '// ---------- 頁面內的輸入／確認視窗 ----------' + helper
     + '// ---------- 時鐘、倒數與自動化 ----------' + rest.replace('document.fullscreenElement', 'fsCurrent()'))
assert helper_marker in s

# ---------- 設定密碼 ----------
rep("""    function setupUnlockOk() {
      const pin = String(state.settings.setupPin || '');
      if (!pin || setupUnlocked) return true;
      const typed = window.prompt('請輸入設定頁密碼（預設 1234）');
      if (typed === null) return false;
      if (typed.trim() !== pin) {
        showToast('密碼不正確。', true);
        return false;
      }
      setupUnlocked = true;
      return true;
    }""", """    const setupNeedsPin = () => !!String(state.settings.setupPin || '') && !setupUnlocked;
    async function askSetupPin() {
      const typed = await askDialog({ message: '請輸入設定頁密碼（預設 1234）', input: true, password: true });
      if (typed === null) return false;
      if (typed.trim() !== String(state.settings.setupPin || '')) {
        showToast('密碼不正確。', true);
        return false;
      }
      setupUnlocked = true;
      return true;
    }""")
rep("""      if (button.dataset.page === 'setup' && !setupUnlockOk()) return;""",
    """      if (button.dataset.page === 'setup' && setupNeedsPin()) {
        askSetupPin().then(ok => { if (ok) button.click(); });
        return;
      }""")

# ---------- 倒數分鐘 ----------
rep("""    $('countdownToggle').addEventListener('click', () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        const minutes = Number(window.prompt('倒數幾分鐘？', '10'));""", """    $('countdownToggle').addEventListener('click', async () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        const minutes = Number(await askDialog({ message: '倒數幾分鐘？', input: true, value: '10', numeric: true }));""")

# ---------- 確認 ----------
rep("""      if (!auto && !silent && blanks > 0 && !window.confirm(`還有 ${blanks} 個座號未填（不會列入缺席）。確定存到雲端？`)) return;""",
    """      if (!auto && !silent && blanks > 0 && !(await askDialog({ message: `還有 ${blanks} 個座號未填（不會列入缺席）。確定存到雲端？` }))) return;""")
rep("""        if (board && window.confirm(`移除「${boardLabel(board)}」版面？已登記的資料會清除。`)) {
          state.boards = state.boards.filter(item => item.id !== board.id);
          saveTodayState();
          renderBoards();
        }
        return;""", """        if (board) askDialog({ message: `移除「${boardLabel(board)}」版面？已登記的資料會清除。` }).then(ok => {
          if (!ok) return;
          state.boards = state.boards.filter(item => item.id !== board.id);
          saveTodayState();
          renderBoards();
        });
        return;""")
rep("""  $('lotResetButton').addEventListener('click', () => {
    if (lotteryBusy) return;
    if (day.drawn.length && !window.confirm('清空已抽名單、重新開始？')) return;""", """  $('lotResetButton').addEventListener('click', async () => {
    if (lotteryBusy) return;
    if (day.drawn.length && !(await askDialog({ message: '清空已抽名單、重新開始？' }))) return;""")
rep("""  $('checkWall').addEventListener('change', event => {
    const select = event.target.closest('[data-check-name]');""", """  $('checkWall').addEventListener('change', async event => {
    const select = event.target.closest('[data-check-name]');""")
rep("""      const name = window.prompt('檢核板名稱：', board.name);""", """      const name = await askDialog({ message: '檢核板名稱：', input: true, value: board.name });""")
rep("""  $('scoreResetButton').addEventListener('click', () => {
    if (!window.confirm('全部分數歸零？')) return;""", """  $('scoreResetButton').addEventListener('click', async () => {
    if (!(await askDialog({ message: '全部分數歸零？' }))) return;""")

assert 'window.prompt(' not in s and 'window.confirm(' not in s
path.write_text(s, encoding='utf-8')
print('ok')
