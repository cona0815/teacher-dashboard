"""大屏倒數多一個「自訂」（老師 2026-11-04）：可打分鐘（8、1.5）或分:秒（2:30），1 秒到 3 小時；「開始」在沒有時間時也走同一個視窗
python tools/add_countdown_custom.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'countdownCustom' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""      <button class="ghost-button" type="button" data-countdown="600">10分</button>""",
    """      <button class="ghost-button" type="button" data-countdown="600">10分</button>
      <button class="ghost-button" type="button" id="countdownCustom">自訂</button>""")
rep("""    $('countdownToggle').addEventListener('click', async () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        const minutes = Number(await askDialog({ message: '倒數幾分鐘？', input: true, value: '10', numeric: true }));
        if (!minutes || minutes <= 0) return;
        startCountdown(Math.round(minutes * 60));
        return;
      }""", """    // 自訂時間：打分鐘（8、1.5）或分:秒（2:30）；打不懂就再問一次
    function parseCountdownSeconds(text) {
      const value = String(text || '').trim().replace(/：/g, ':');
      const clock = /^(\\d{1,3}):([0-5]?\\d)$/.exec(value);
      const seconds = clock ? Number(clock[1]) * 60 + Number(clock[2]) : /^\\d+(\\.\\d+)?$/.test(value) ? Math.round(Number(value) * 60) : 0;
      return seconds >= 1 && seconds <= 3 * 60 * 60 ? seconds : 0;
    }
    async function askCountdownTime() {
      let message = '倒數多久？\\n打分鐘（例如 8、1.5），或分:秒（例如 2:30）';
      for (;;) {
        const typed = await askDialog({ message, input: true, value: '10' });
        if (typed === null) return;
        const seconds = parseCountdownSeconds(typed);
        if (seconds) return startCountdown(seconds);
        message = '看不懂這個時間，請再打一次：\\n分鐘（例如 8、1.5）或分:秒（例如 2:30），最長 3 小時';
      }
    }
    $('countdownCustom').addEventListener('click', askCountdownTime);
    $('countdownToggle').addEventListener('click', async () => {
      if (!state.countdown.remaining && !state.countdown.running) {
        await askCountdownTime();
        return;
      }""")

path.write_text(s, encoding='utf-8')
print('ok')
