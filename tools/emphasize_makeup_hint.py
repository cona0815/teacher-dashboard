"""作業補交頁：「今天的缺交請到作業繳交直接改」強調（老師 2026-11-04），做成醒目的提示，點了直接跳到作業繳交
python tools/emphasize_makeup_hint.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'hint-callout' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""    .page-hint .sep { color: var(--line); margin: 0 8px; font-weight: 900; }""", """    .page-hint .sep { color: var(--line); margin: 0 8px; font-weight: 900; }
    .hint-callout { display: inline-block; margin: 4px 0 2px; padding: 5px 14px; border: 2px solid #d98a00; border-radius: 999px; background: #fff3d1; color: #7a4a00; font: inherit; font-size: 17px; font-weight: 900; cursor: pointer; }
    .hint-callout:hover { background: #ffe7a8; }""")
rep("""點完就從清單消失。<span class="sep">｜</span>今天的缺交請到「作業繳交」直接改。""",
    """點完就從清單消失。<br><button class="hint-callout" type="button" id="makeupGoHomework">⚠️ 今天的缺交請到「作業繳交」直接改 →</button>""")
rep("""    $('addBoardButton').addEventListener('click', addBoard);""", """    $('addBoardButton').addEventListener('click', addBoard);
    $('makeupGoHomework').addEventListener('click', () => document.querySelector('.tab-button[data-page="homework"]').click());""")
path.write_text(s, encoding='utf-8')
print('ok')
