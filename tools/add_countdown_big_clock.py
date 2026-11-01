"""大屏右上角倒數：按「5分／10分／開始」後畫面中間跳出大時鐘（老師 2026-11-02）
- 5分／10分 直接開始倒數（原本只設定時間、要再按開始）
- 大時鐘：進度圈、−1分／暫停／＋1分／縮小／結束；最後 10 秒變紅；時間到顯示「時間到」20 秒後自動收起
- 縮小（Esc、點背景）後在右上角繼續倒數，點右上角的時間再打開
- 工具在全螢幕時，大時鐘放進全螢幕畫面裡才看得到
python tools/add_countdown_big_clock.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'cdPop' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- CSS（放在第一個 style 的動森風規則前面） ----------
rep("""    /* ===== 大屏風格：可愛動森風""", """    /* ===== 倒數大時鐘（右上角按 5分／10分／開始 跳出） ===== */
    .countdown-display { cursor: pointer; }
    .cd-pop { position: fixed; inset: 0; z-index: 99990; display: flex; align-items: center; justify-content: center; background: rgba(20, 36, 32, .42); }
    .cd-pop[hidden] { display: none !important; }
    .cd-card { position: relative; display: flex; flex-direction: column; align-items: center; gap: 2.4vh; padding: 4vh 5vw 3.4vh; border-radius: 36px; background: var(--surface); border: 3px solid var(--line); box-shadow: 0 30px 60px -20px rgba(0,0,0,.45); }
    .cd-ring { position: relative; width: min(60vh, 70vw); height: min(60vh, 70vw); }
    .cd-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
    .cd-track { fill: none; stroke: var(--line); stroke-width: 9; }
    .cd-arc { fill: none; stroke: var(--primary); stroke-width: 9; stroke-linecap: round; stroke-dasharray: 100; transition: stroke-dashoffset 1s linear, stroke .3s; }
    .cd-time { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: min(17vh, 19vw); font-weight: 900; font-variant-numeric: tabular-nums; color: var(--ink); letter-spacing: .02em; }
    .cd-pop.warning .cd-arc { stroke: var(--missing); }
    .cd-pop.warning .cd-time { color: var(--missing); animation: cdPulse 1s ease-in-out infinite; }
    .cd-pop.paused .cd-time { opacity: .55; }
    .cd-pop.done .cd-time { font-size: min(9vh, 9vw); white-space: nowrap; color: var(--missing); animation: cdPulse .8s ease-in-out infinite; }
    .cd-pop.done .cd-arc { stroke: var(--missing); stroke-dashoffset: 0 !important; }
    @keyframes cdPulse { 50% { transform: scale(1.06); } }
    .cd-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }
    .cd-actions button { font-size: 20px; padding: 12px 24px; }
    @media (prefers-reduced-motion: reduce) { .cd-pop .cd-time { animation: none !important; } }
    html[data-board-style="cozy"] .cd-card { border: 4px solid var(--cozy-wood); border-radius: 44px; box-shadow: 0 8px 0 var(--cozy-wood), 0 30px 60px -20px rgba(91,70,54,.45); }
    html[data-board-style="cozy"] .cd-pop { background: rgba(91, 70, 54, .38); }

    /* ===== 大屏風格：可愛動森風""")

# ---------- HTML ----------
rep("""      <button class="ghost-button" type="button" id="countdownReset">歸零</button>
    </div>
  </header>""", """      <button class="ghost-button" type="button" id="countdownReset">歸零</button>
    </div>
  </header>
  <div class="cd-pop" id="cdPop" role="dialog" aria-label="倒數計時" hidden>
    <div class="cd-card">
      <div class="cd-ring">
        <svg viewBox="0 0 120 120" aria-hidden="true"><circle class="cd-track" cx="60" cy="60" r="52"/><circle class="cd-arc" id="cdArc" cx="60" cy="60" r="52" pathLength="100"/></svg>
        <div class="cd-time" id="cdTime">00:00</div>
      </div>
      <div class="cd-actions">
        <button class="ghost-button" type="button" id="cdMinus">−1分</button>
        <button class="primary-button" type="button" id="cdToggle">暫停</button>
        <button class="ghost-button" type="button" id="cdPlus">＋1分</button>
        <button class="ghost-button" type="button" id="cdMinimize">縮小（Esc）</button>
        <button class="ghost-button" type="button" id="cdStop">結束</button>
      </div>
    </div>
  </div>""")

# ---------- 狀態 ----------
rep("""      countdown: { remaining: 0, running: false },""",
    """      countdown: { remaining: 0, running: false, total: 0 },   // total：這一輪的總秒數（大時鐘進度圈用）""")

# ---------- 顯示 ----------
rep("""      $('countdownToggle').textContent = state.countdown.running ? '暫停' : '開始';
    }
    function countdownTick() {
      if (!state.countdown.running) return;
      state.countdown.remaining -= 1;
      if (state.countdown.remaining <= 0) {
        state.countdown.remaining = 0;
        state.countdown.running = false;
        beep();
        showToast('⏰ 時間到！');
      }
      renderCountdown();
    }""", """      $('countdownToggle').textContent = state.countdown.running ? '暫停' : '開始';
      // 大時鐘
      const pop = $('cdPop');
      if (!pop.classList.contains('done')) $('cdTime').textContent = $('countdownDisplay').textContent;
      const total = Math.max(state.countdown.total, remaining, 1);
      $('cdArc').style.strokeDashoffset = String(100 - remaining / total * 100);
      pop.classList.toggle('warning', state.countdown.running && remaining <= 10);
      pop.classList.toggle('paused', !state.countdown.running && remaining > 0);
      $('cdToggle').textContent = state.countdown.running ? '⏸ 暫停' : '▶ 繼續';
      $('cdToggle').hidden = $('cdMinus').hidden = pop.classList.contains('done');
    }
    let cdAutoClose = 0;
    function openCountdownPop() {
      const pop = $('cdPop');
      clearTimeout(cdAutoClose);
      // 工具在全螢幕時，要放進全螢幕的元素裡才看得到
      const host = document.fullscreenElement || document.body;
      if (pop.parentNode !== host) host.appendChild(pop);
      pop.hidden = false;
      renderCountdown();
    }
    function closeCountdownPop() {
      clearTimeout(cdAutoClose);
      const pop = $('cdPop');
      pop.hidden = true;
      pop.classList.remove('done');
      renderCountdown();
    }
    function startCountdown(seconds) {
      state.countdown.remaining = seconds;
      state.countdown.total = seconds;
      state.countdown.running = true;
      $('cdPop').classList.remove('done');
      openCountdownPop();
    }
    function countdownTick() {
      if (!state.countdown.running) return;
      state.countdown.remaining -= 1;
      if (state.countdown.remaining <= 0) {
        state.countdown.remaining = 0;
        state.countdown.running = false;
        beep();
        showToast('⏰ 時間到！');
        // 時間到：大時鐘跳出來顯示，20 秒後自動收起
        openCountdownPop();
        $('cdPop').classList.add('done');
        $('cdTime').textContent = '⏰ 時間到！';
        cdAutoClose = setTimeout(closeCountdownPop, 20000);
      }
      renderCountdown();
    }""")

# ---------- 按鈕 ----------
rep("""    document.querySelectorAll('[data-countdown]').forEach(button => button.addEventListener('click', () => {
      state.countdown.remaining = Number(button.dataset.countdown);
      state.countdown.running = false;
      renderCountdown();
    }));
    $('countdownToggle').addEventListener('click', () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        const minutes = Number(window.prompt('倒數幾分鐘？', '10'));
        if (!minutes || minutes <= 0) return;
        state.countdown.remaining = Math.round(minutes * 60);
      }
      state.countdown.running = !state.countdown.running;
      renderCountdown();
    });
    $('countdownReset').addEventListener('click', () => { state.countdown.remaining = 0; state.countdown.running = false; renderCountdown(); });""",
    """    // 5分／10分：直接開始倒數並跳出大時鐘
    document.querySelectorAll('[data-countdown]').forEach(button => button.addEventListener('click', () => startCountdown(Number(button.dataset.countdown))));
    $('countdownToggle').addEventListener('click', () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        const minutes = Number(window.prompt('倒數幾分鐘？', '10'));
        if (!minutes || minutes <= 0) return;
        startCountdown(Math.round(minutes * 60));
        return;
      }
      state.countdown.running = !state.countdown.running;
      if (state.countdown.running) openCountdownPop();
      renderCountdown();
    });
    $('countdownReset').addEventListener('click', () => { state.countdown.remaining = 0; state.countdown.running = false; closeCountdownPop(); });
    // 大時鐘：點右上角的時間再打開；縮小（Esc、點背景）後在右上角繼續倒數
    $('countdownDisplay').addEventListener('click', () => { if (state.countdown.remaining > 0) openCountdownPop(); });
    $('cdToggle').addEventListener('click', () => { if (state.countdown.remaining > 0) { state.countdown.running = !state.countdown.running; renderCountdown(); } });
    $('cdPlus').addEventListener('click', () => {
      if ($('cdPop').classList.contains('done')) { startCountdown(60); return; }
      state.countdown.remaining += 60; state.countdown.total = Math.max(state.countdown.total, state.countdown.remaining); renderCountdown();
    });
    $('cdMinus').addEventListener('click', () => {
      if ($('cdPop').classList.contains('done')) return;
      state.countdown.remaining = Math.max(1, state.countdown.remaining - 60); renderCountdown();
    });
    $('cdMinimize').addEventListener('click', closeCountdownPop);
    $('cdStop').addEventListener('click', () => { state.countdown.remaining = 0; state.countdown.running = false; closeCountdownPop(); });
    $('cdPop').addEventListener('click', event => { if (event.target === $('cdPop')) closeCountdownPop(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && !$('cdPop').hidden) closeCountdownPop(); });
    // 進出全螢幕時把打開中的大時鐘搬到看得到的地方
    document.addEventListener('fullscreenchange', () => { if (!$('cdPop').hidden) openCountdownPop(); });""")

path.write_text(s, encoding='utf-8')
print('ok')
