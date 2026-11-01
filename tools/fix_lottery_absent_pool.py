"""修正：抽籤／分組「排除今日缺席」把自動轉「未到」的整班都排掉（老師沒點名或只點請假時，08:05 後只剩少數號碼可抽）。

規則改成：病假、事假一律排除；「未到」只有在今天真的有點名（至少一位標「到／遲到」）時才排除。
抽籤狀態列直接寫出座號範圍、空號、排除了誰，老師一眼看得出設定對不對。

python tools/fix_lottery_absent_pool.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'rollcallTaken' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''  function absentSeatSet() {
    const absent = new Set();
    activeSeats().forEach(seat => {
      if (['病假', '事假', '未到'].includes(state.attendance[seat] || '')) absent.add(seat);
    });
    return absent;
  }''', '''  // 今天有沒有真的點名：至少一位標了「到／遲到」。
  // 自動缺席時間（預設 08:05）一到，未填座號會自動轉「未到」；老師沒點名或只點請假的人時，
  // 全班都會變「未到」——這時不能把「未到」當缺席，否則抽籤、分組只剩少數號碼（2026-11-01 老師回報）。
  function rollcallTaken() {
    return activeSeats().some(seat => ['到', '遲到'].includes(state.attendance[seat] || ''));
  }
  function absentSeatSet() {
    const absent = new Set();
    const countMissing = rollcallTaken();
    activeSeats().forEach(seat => {
      const status = state.attendance[seat] || '';
      if (status === '病假' || status === '事假' || (status === '未到' && countMissing)) absent.add(seat);
    });
    return absent;
  }
  // 給狀態列看的座號池說明：「座號 1～30（空號 4、13）・排除請假／未到：5、9」
  function seatPoolNote(excludeAbsent) {
    const s = state.settings;
    const empties = s.emptySeats.filter(n => n <= s.seatCount);
    let note = `座號 1～${s.seatCount}` + (empties.length ? `（空號 ${empties.join('、')}）` : '');
    if (excludeAbsent) {
      const absent = [...absentSeatSet()].sort((a, b) => a - b);
      if (absent.length) note += `・排除今日缺席 ${absent.length} 人：${absent.join('、')}`;
      else if (!rollcallTaken() && activeSeats().some(seat => state.attendance[seat] === '未到')) note += '・今天還沒點名，只排除請假';
    }
    return note;
  }''')

rep('''  function updateLotStatus() {
    const remaining = remainingPool();
    $('lotStatus').textContent = `剩 ${remaining.length} 個可抽`;''', '''  function updateLotStatus() {
    const remaining = remainingPool();
    $('lotStatus').textContent = $('lotCustom').checked
      ? `剩 ${remaining.length} 個可抽（自訂名單）`
      : `剩 ${remaining.length} 個可抽｜${seatPoolNote($('lotExcludeAbsent').checked)}（到「設定」改座號與空號）`;''')

# 進到班級工具分頁就重算一次（點名、設定可能剛改過）
rep('''  // ---- 跑馬燈燈泡：繞轉盤一圈，轉動時加速 ----''', '''  document.querySelector('.tab-button[data-page="tools"]').addEventListener('click', () => setTimeout(updateLotStatus, 0));
  // ---- 跑馬燈燈泡：繞轉盤一圈，轉動時加速 ----''')

path.write_text(s, encoding='utf-8')
print('ok')
