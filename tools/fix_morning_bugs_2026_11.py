"""晨間大屏 bug 修正（2026-11-01 全面掃描）：
#1 整夜不關頁 → 隔天自動重新載入當日狀態
#3 08:05 後才第一次開頁 → 不補做「未填轉未到」與自動推播（避免老師還沒點名，LINE 就收到全班未到）
#4 同一次檢查兩段推播都到期 → 只送一次完整版（點名＋作業），不會被「送出中」吃掉
#5 人數調小後，超出座號的缺席紀錄不再送出
#10 定評小幫手：切進來就自動從點名帶入（並用跟抽籤一樣的缺席規則）
#11 離開班級工具頁就停止安靜偵測（不再背景收音、蓋到其他頁）
#12 檢核板：今日缺席的座號標「缺」，不算在未完成裡
python tools/fix_morning_bugs_2026_11.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'BOOT_HHMM' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# #1 跨日：每分鐘比對日期，日期變了就重新載入（整夜開著的大屏隔天早上自動換新的一天）
rep('''    window.setInterval(automationTick, 15000);
    automationTick();''', '''    window.setInterval(automationTick, 15000);
    automationTick();
    const BOOT_DAY = todayKey();
    window.setInterval(() => { if (todayKey() !== BOOT_DAY && !document.fullscreenElement) location.reload(); }, 60000);''')

# #3 晚開頁不補做；#4 兩段推播同時到期只送一次完整版
rep('''      let changed = false;
      if (!state.flags.autoAbsentDone && now >= state.settings.autoAbsentTime) {''', '''      let changed = false;
      // 08:05（自動缺席時間）之後才第一次打開大屏：不補做「未填轉未到」與自動推播——
      // 老師可能還沒點名，補做會讓 LINE 收到「全班未到」（2026-11-01 掃描發現）。點完名請按「送出」。
      if (!state.flags.autoAbsentDone && BOOT_HHMM >= state.settings.autoAbsentTime) {
        state.flags.autoAbsentDone = true;
        if (BOOT_HHMM >= state.settings.autoNotifyTime) state.flags.autoNotifyDone = true;
        if (BOOT_HHMM >= state.settings.autoHomeworkNotifyTime) state.flags.autoHomeworkNotifyDone = true;
        saveTodayState();
        showToast(`大屏在 ${state.settings.autoAbsentTime} 之後才打開，今天不自動轉「未到」；點完名請按「送出」。`);
      }
      if (!state.flags.autoAbsentDone && now >= state.settings.autoAbsentTime) {''')
rep('''      if (!state.flags.autoNotifyDone && now >= state.settings.autoNotifyTime) {
        state.flags.autoNotifyDone = true;
        changed = true;
        submitReport({ auto: true, push: 'attendance' });
      }''', '''      if (!state.flags.autoNotifyDone && now >= state.settings.autoNotifyTime && !state.flags.autoHomeworkNotifyDone && now >= state.settings.autoHomeworkNotifyTime) {
        // 兩段都到期（例如中間電腦睡著）：只送一次完整版，避免第二次因「送出中」被略過
        state.flags.autoNotifyDone = true;
        state.flags.autoHomeworkNotifyDone = true;
        changed = true;
        submitReport({ auto: true, push: 'full' });
      }
      if (!state.flags.autoNotifyDone && now >= state.settings.autoNotifyTime) {
        state.flags.autoNotifyDone = true;
        changed = true;
        submitReport({ auto: true, push: 'attendance' });
      }''')
rep('''    function automationTick() {''', '''    const BOOT_HHMM = nowHhmm();   // 這次打開大屏的時間（判斷是不是晨間時段之後才開）
    function automationTick() {''')

# #5 只送現在班級裡的座號
rep('''      const attendance = Object.entries(state.attendance)
        .filter(([seat]) => !state.settings.emptySeats.includes(Number(seat)))''', '''      const seatsNow = new Set(activeSeats());
      const attendance = Object.entries(state.attendance)
        .filter(([seat]) => seatsNow.has(Number(seat)))''')

# #10 定評：用跟抽籤一樣的缺席規則，切到這個工具就自動帶入
rep('''      activeSeats().forEach(seat => {
        const status = state.attendance[seat] || '';
        if (['病假', '事假', '未到'].includes(status)) absent.push({ seat, status });
      });''', '''      const absentSet = absentSeatSet();   // 跟抽籤、分組同一套：沒點名時自動「未到」不算缺席
      activeSeats().forEach(seat => {
        if (absentSet.has(seat)) absent.push({ seat, status: state.attendance[seat] || '' });
      });''')
rep('''    $('examSyncButton').addEventListener('click', syncExam);
    syncExam();''', '''    $('examSyncButton').addEventListener('click', syncExam);
    syncExam();
    document.querySelector('#toolTabs [data-tool="exam"]').addEventListener('click', syncExam);
    document.querySelector('.tab-button[data-page="tools"]').addEventListener('click', () => setTimeout(syncExam, 0));''')

# #11 離開班級工具頁就停止安靜偵測
rep('''    if (tab.dataset.tool !== 'quiet') stopQuiet();
  }));''', '''    if (tab.dataset.tool !== 'quiet') stopQuiet();
  }));
  document.querySelectorAll('.tab-button').forEach(btn => btn.addEventListener('click', () => { if (btn.dataset.page !== 'tools') stopQuiet(); }));''')

# #12 檢核板：缺席座號標「缺」，不算未完成
rep('''      const seats = activeSeats();
      const doneCount = seats.filter(seat => board.done[seat]).length;
      let missIndex = 0;
      const cells = seats.map(seat => {
        const done = !!board.done[seat];
        const miss = board.showMiss && !done;''', '''      const absentSet = absentSeatSet();
      const seats = activeSeats().filter(seat => !absentSet.has(seat));   // 今日缺席不算在這張檢核板
      const doneCount = seats.filter(seat => board.done[seat]).length;
      let missIndex = 0;
      const cells = activeSeats().map(seat => {
        if (absentSet.has(seat)) return `<button class="check-seat absent" type="button" disabled title="今日缺席">${seat}<small>缺</small></button>`;
        const done = !!board.done[seat];
        const miss = board.showMiss && !done;''')
rep('''          <button class="check-missing-btn" type="button" data-check-miss="${index}">${board.showMiss ? '關閉反查' : `未點 ${activeSeats().length - doneCount} 人`}</button>''', '''          <button class="check-missing-btn" type="button" data-check-miss="${index}">${board.showMiss ? '關閉反查' : `未點 ${seats.length - doneCount} 人`}</button>''')
rep('''        .check-seat.done { background: var(--resub, #2273c9); border-color: var(--resub, #2273c9); color: #fff; }''', '''        .check-seat.done { background: var(--resub, #2273c9); border-color: var(--resub, #2273c9); color: #fff; }
        .check-seat.absent { background: #f1f1ef; color: #b5b5ad; border-style: dashed; cursor: default; }
        .check-seat.absent small { display: block; font-size: 10px; font-weight: 700; }''')

path.write_text(s, encoding='utf-8')
print('ok')
