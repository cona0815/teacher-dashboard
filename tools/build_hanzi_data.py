"""產生 assets/studio/hanzi-data.js：生詞本用的注音、部首、筆畫字表
資料來源：數位發展部「全字庫」開放資料（https://data.cns11643.gov.tw/opendata/），政府資料開放授權條款－第1版
  - Properties.zip：CNS_phonetic.txt（注音，一字多音各一列）、CNS_stroke.txt（總筆畫）、CNS_radical.txt（部首代碼）、CNS_radical_word.txt（部首字）
  - MapingTables.zip：Unicode/CNS2UNICODE_Unicode BMP.txt（CNS 字碼 → Unicode）
只收 CNS 第 1、2 字面（常用字、次常用字，約 13,000 字，涵蓋國小用字）
用法：python tools/build_hanzi_data.py <解壓縮後的資料夾> [資料版本日期]
"""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
version = sys.argv[2] if len(sys.argv) > 2 else ''
root = Path(__file__).resolve().parents[1]


def rows(name):
    for line in (src / name).read_text(encoding='utf-8').splitlines():
        parts = line.rstrip('\r').split('\t')
        if len(parts) >= 2 and parts[0].strip():
            yield parts[0].strip(), parts[1].strip()


uni = {}
for cns, code in rows('Unicode/CNS2UNICODE_Unicode BMP.txt'):
    plane = cns.split('-')[0]
    if plane in ('1', '2'):
        ch = chr(int(code, 16))
        if '㐀' <= ch <= '鿿' or '豈' <= ch <= '﫿':
            uni[cns] = ch

readings, strokes, radicals = {}, {}, {}
for cns, zy in rows('CNS_phonetic.txt'):
    if cns in uni:
        readings.setdefault(cns, [])
        if zy not in readings[cns]:
            readings[cns].append(zy)
for cns, n in rows('CNS_stroke.txt'):
    if cns in uni:
        strokes[cns] = int(n)
for cns, n in rows('CNS_radical.txt'):
    if cns in uni:
        radicals[cns] = int(n)

radical_names = {}
for no, word in rows('CNS_radical_word.txt'):
    if no.isdigit():
        radical_names[int(no)] = word.split('（')[0].strip()
assert len(radical_names) == 214, len(radical_names)

table = {}
for cns, ch in uni.items():
    if cns not in readings or cns not in strokes or cns not in radicals:
        continue
    if ch in table:
        continue
    table[ch] = [strokes[cns], radicals[cns], ' '.join(readings[cns])]

# 抽查：國小常見字一定要有，而且數值正確
checks = {'一': (1, '一'), '晨': (11, '日'), '學': (16, '子'), '樂': (15, '木'), '龜': (16, '龜'), '媽': (13, '女')}
for ch, (n, rad) in checks.items():
    assert ch in table, ch
    assert table[ch][0] == n, (ch, table[ch])
    assert radical_names[table[ch][1]] == rad, (ch, radical_names[table[ch][1]])
assert 'ㄌㄜˋ' in table['樂'][2] and 'ㄩㄝˋ' in table['樂'][2], table['樂']

out = root / 'assets' / 'studio' / 'hanzi-data.js'
body = json.dumps(table, ensure_ascii=False, separators=(',', ':'))
rad = json.dumps([''] + [radical_names[i] for i in range(1, 215)], ensure_ascii=False, separators=(',', ':'))
out.write_text(
    '/* 生詞本字表（自動產生，請勿手改；重產：python tools/build_hanzi_data.py）\n'
    f'   資料來源：數位發展部 全字庫開放資料 屬性資料集（{version or "最新版"}），政府資料開放授權條款－第1版\n'
    '   格式：字: [總筆畫, 部首編號, "讀音1 讀音2 …"]；HANZI_RADICALS[部首編號] = 部首字 */\n'
    f'window.HANZI_SOURCE = {json.dumps("數位發展部 全字庫開放資料（" + (version or "最新版") + "）", ensure_ascii=False)};\n'
    f'window.HANZI_RADICALS = {rad};\n'
    f'window.HANZI_DATA = {body};\n', encoding='utf-8')
print(len(table), 'chars,', out.stat().st_size // 1024, 'KB')
