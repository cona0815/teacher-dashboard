"""教材小工場與 LINE 小幫手 bug 修正（2026-11-01 全面掃描）：
Studio #13 圖像簡報「產生逐頁大綱」按完後按鈕文字變空白
Studio #14 座位表：空號支援全形逗號與頓號；人數上限 60（同大屏）；預設人數沿用大屏設定；切換排法保留目前的座位順序
GAS    #7 寫入點名／作業時，班級、科目、作業名稱欄設成純文字（「0601」「6-1」「1-2」不會被試算表轉成數字或日期而比對不到）
python tools/fix_studio_gas_bugs_2026_11.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(name, pairs):
    p = ROOT / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:80])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


patch('Studio.html', [
    ("""    ['wsGoButton', 'ntGoButton', 'mmGoButton', 'cmGoButton', 'poGoButton'].forEach(id => { $(id).dataset.label = $(id).textContent; });""",
     """    ['wsGoButton', 'ntGoButton', 'mmGoButton', 'cmGoButton', 'poGoButton', 'dkOutlineButton'].forEach(id => { $(id).dataset.label = $(id).textContent; });"""),
    ("""      const count = Math.max(2, Math.min(50, parseInt($('stCount').value, 10) || 28));
      const skip = new Set($('stSkip').value.split(/[、,\\s]+/).map(v => parseInt(v, 10)).filter(Boolean));""",
     """      const count = Math.max(2, Math.min(60, parseInt($('stCount').value, 10) || 28));
      const skip = new Set($('stSkip').value.split(/[、,，;；\\s]+/).map(v => parseInt(v, 10)).filter(Boolean));"""),
    ("""            <input class="input" id="stCount" type="number" min="2" max="50" value="28"></div>""",
     """            <input class="input" id="stCount" type="number" min="2" max="60" value="28"></div>"""),
    ("""    function stBuild(shuffle) {
      const pool = stPool();""",
     """    function stBuild(shuffle, keepOrder) {
      const pool = keepOrder || stPool();"""),
    ("""      if (!shuffle && $('stDirection').value === 'col' && layout !== 'island4' && layout !== 'island6') {""",
     """      if (!shuffle && !keepOrder && $('stDirection').value === 'col' && layout !== 'island4' && layout !== 'island6') {"""),
    ("""      if (stSeats.length) stBuild(false);
    });""",
     """      // 換排法：保留目前的座位順序（隨機重排或拖拉過的結果不會消失）
      if (stSeats.length) stBuild(false, stSeats.filter(seat => seat != null));
    });
    // 預設人數沿用晨間大屏的設定（同一台電腦）
    try {
      const board = JSON.parse(localStorage.getItem('morningBoardSettings') || 'null');
      if (board && Number(board.seatCount)) {
        $('stCount').value = Math.min(60, Math.max(2, Number(board.seatCount)));
        if (Array.isArray(board.emptySeats) && board.emptySeats.length && !$('stSkip').value) $('stSkip').value = board.emptySeats.join('、');
      }
    } catch (e) {}"""),
])

patch('LineBot.gs', [
    ("""    if (rollcallRows.length) {
      sheets.rollcall.getRange(sheets.rollcall.getLastRow() + 1, 1, rollcallRows.length, 4).setValues(rollcallRows);
    }""",
     """    if (rollcallRows.length) {
      var rollcallRange = sheets.rollcall.getRange(sheets.rollcall.getLastRow() + 1, 1, rollcallRows.length, 4);
      rollcallRange.offset(0, 1, rollcallRows.length, 1).setNumberFormat('@');   // 班級欄存成文字：「0601」「6-1」不會被轉成數字或日期而比對不到
      rollcallRange.setValues(rollcallRows);
    }"""),
    ("""    if (homeworkRows.length) {
      sheets.homework.getRange(sheets.homework.getLastRow() + 1, 1, homeworkRows.length, 6).setValues(homeworkRows);
    }""",
     """    if (homeworkRows.length) {
      var homeworkRange = sheets.homework.getRange(sheets.homework.getLastRow() + 1, 1, homeworkRows.length, 6);
      homeworkRange.offset(0, 1, homeworkRows.length, 3).setNumberFormat('@');   // 班級、科目、作業名稱存成文字（「1-2」不會變日期）
      homeworkRange.setValues(homeworkRows);
    }"""),
    ("var BOT_VERSION = '2026-10-31 22:40';", "var BOT_VERSION = '2026-11-01 14:30';"),
])
print('ok')
