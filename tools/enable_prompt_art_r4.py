"""大屏提示插圖換成原創「溫暖繪本」33 張（ART-02 R4 驗收通過）：
- PROMPT_ART_READY 列入 32 句的 id，全部改用 assets/art/cozy/prompt/<id>.webp
- 自訂句（不在內建清單）改用 custom_default.webp；不再顯示 いらすとや 出處
python tools/enable_prompt_art_r4.py
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'const PROMPT_ART_READY = new Set([]);' in s, '已套用過'

ids = sorted(p.stem for p in (root / 'assets/art/cozy/prompt').glob('*.webp'))
assert len(ids) == 33 and 'custom_default' in ids, ids
preset_ids = re.findall(r"\{ id: '([a-z_]+)', text: '[^']+', img: '[^']+' \}", s)
assert set(preset_ids) == set(ids) - {'custom_default'}, (set(ids) ^ set(preset_ids))


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''    // 新插圖（動森風）交件驗收後，把 id 加進來就會改用新圖；沒列的繼續用舊圖
    const PROMPT_ART_READY = new Set([]);''',
    '''    // 原創插圖「溫暖繪本」（ART-02 R4 驗收通過）；列在這裡的 id 用新圖，沒列的繼續用舊圖
    const PROMPT_ART_READY = new Set([
''' + ''.join(f"      '{i}',\n" for i in ids) + '''    ]);''')
rep('''      return 'assets/irasutoya/' + ((item && item.img) || 'class_focus.png');
    }''',
    '''      return 'assets/irasutoya/' + ((item && item.img) || 'class_focus.png');
    }
    // 自訂句（不在內建清單）的預設插圖
    function promptCustomImgSrc(legacyImg) {
      if (PROMPT_ART_READY.has('custom_default')) return PROMPT_ART_DIR + 'custom_default.webp';
      return 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(legacyImg || '')) ? legacyImg : 'class_focus.png');
    }''')
rep('''          $('promptImg').src = known ? promptImgSrc(known) : 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(prompt.img || '')) ? prompt.img : 'class_focus.png');''',
    '''          $('promptImg').src = known ? promptImgSrc(known) : promptCustomImgSrc(prompt.img);''')
rep('''      img.hidden = !item;
      if (item) img.src = promptImgSrc(item);''',
    '''      // 自訂句（例：LINE 傳來的提示）用自訂預設插圖；舊圖時期維持不顯示
      img.hidden = !item && !PROMPT_ART_READY.has('custom_default');
      if (!img.hidden) img.src = item ? promptImgSrc(item) : promptCustomImgSrc();''')

path.write_text(s, encoding='utf-8')
print('ok', len(ids))
