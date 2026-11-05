"""2026-11-05 老師：第 1 級的聯絡本在這台電腦留 180 天，超過自動清掉。點名與作業維持 30 天。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rep(text, old, new):
    assert text.count(old) == 1, (old[:70], text.count(old))
    return text.replace(old, new)


p = ROOT / 'Morning.html'
t = p.read_text(encoding='utf-8')
t = rep(t, "    const LOCAL_KEEP_DAYS = 30;   // 點名與作業在這台電腦留 30 天，第 1 級的補交靠它\n",
        "    const LOCAL_KEEP_DAYS = 30;   // 點名與作業在這台電腦留 30 天，第 1 級的補交靠它\n"
        "    const CONTACT_LOCAL_PREFIX = 'morningContactLocal:';   // 第 1 級的聯絡本，一天一筆\n"
        "    const CONTACT_KEEP_DAYS = 180;\n")
t = rep(t, """    // 第 1 級的聯絡本存在這台電腦，一天一筆
    const CONTACT_LOCAL_PREFIX = 'morningContactLocal:';
""", '')
t = rep(t, """key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -LOCAL_KEEP_DAYS)) localStorage.removeItem(key);
""", """key.slice(STATE_PREFIX.length) < shiftDate(todayKey(), -LOCAL_KEEP_DAYS)) localStorage.removeItem(key);
        if (key && key.startsWith(CONTACT_LOCAL_PREFIX) && key.slice(CONTACT_LOCAL_PREFIX.length) < shiftDate(todayKey(), -CONTACT_KEEP_DAYS)) localStorage.removeItem(key);
""")
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'tests/profile_config.test.js'
t = p.read_text(encoding='utf-8')
t = rep(t, '''assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -LOCAL_KEEP_DAYS\\)/, "清舊資料要照 30 天");
''', '''assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -LOCAL_KEEP_DAYS\\)/, "清舊資料要照 30 天");
assert.match(morningLevelSource, /CONTACT_KEEP_DAYS = 180/, "第 1 級聯絡本應留 180 天");
assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -CONTACT_KEEP_DAYS\\)/, "清舊聯絡本要照 180 天");
''')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'Install.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '點名與作業的紀錄在這台電腦留 <strong>30 天</strong>，超過會自動清掉。', '點名與作業的紀錄在這台電腦留 <strong>30 天</strong>，聯絡本留 <strong>180 天</strong>，超過會自動清掉。')
t = rep(t, '補交改看雲端，這台電腦以前的紀錄不會搬上去。', '補交和聯絡本改看雲端，這台電腦以前的紀錄不會搬上去。')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'About.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '不含機敏資料；點名與作業留 30 天</td>', '不含機敏資料；點名與作業留 30 天，聯絡本留 180 天</td>')
p.write_text(t, encoding='utf-8', newline='\n')
print('done')
