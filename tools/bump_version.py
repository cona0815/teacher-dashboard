"""改了程式就跑一次：把版本號（日期＋時間）同步寫進每個地方，老師一看就分得出新舊。

python tools/bump_version.py            # 用現在時間
python tools/bump_version.py "2026-11-11 10:50"

會更新：
- LineBot.gs 第 2 行標題「版本 …」與 BOT_VERSION（試算表「ℹ️ 程式版本」、LINE 傳「版本」看到的）
- assets/version.js 的 TD_VERSION（每個網頁左下角「版本 …」、安裝教學比對用）
"""
import datetime, io, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
v = sys.argv[1] if len(sys.argv) > 1 else datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
assert re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', v), v

def sub(path, pattern, repl):
    p = ROOT / path
    s = io.open(p, encoding='utf-8', newline='').read()
    s2, n = re.subn(pattern, repl, s, count=1, flags=re.M)
    assert n == 1, (path, pattern)
    io.open(p, 'w', encoding='utf-8', newline='').write(s2)

sub('LineBot.gs', r"^var BOT_VERSION = '[^']*';", f"var BOT_VERSION = '{v}';")
sub('LineBot.gs', r"^ \* LINE 小幫手（選用雲端模組）.*$", f" * LINE 小幫手（選用雲端模組）　版本 {v}")
sub('assets/version.js', r"TD_VERSION = '[^']*'", f"TD_VERSION = '{v}'")
# 共用的 JS 加版本號，瀏覽器才不會拿舊的快取
tag = v.replace(' ', '-').replace(':', '')
for page in ('Morning.html', 'Index.html'):
    sub(page, r'assets/attendance-term\.js(\?v=[^"]*)?"', f'assets/attendance-term.js?v={tag}"')
print('版本已更新為', v)
