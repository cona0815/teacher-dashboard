"""大屏提示插圖兩套風格可切換（設定頁「大屏提示插圖風格」）：
- 溫暖繪本（ART-02 R4，33 張）搬到 assets/art/storybook/prompt/
- 可愛動森風放 assets/art/cozy/prompt/（ART-03 製作中；交件驗收後把 id 加進 cozy.ready）
- 選的風格還沒畫好的句子先用溫暖繪本，再沒有才用舊圖
先 git mv assets/art/cozy/prompt assets/art/storybook/prompt，再執行：
python tools/add_prompt_art_styles.py
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'PROMPT_ART_STYLES' not in s, '已套用過'
assert (root / 'assets/art/storybook/prompt/custom_default.webp').exists(), '先 git mv 溫暖繪本資料夾'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# 設定值
rep("""    const CONTACT_FONTS = ['default', 'huninn', 'iansui', 'bpmf', 'bpmfhuninn'];""",
    """    const CONTACT_FONTS = ['default', 'huninn', 'iansui', 'bpmf', 'bpmfhuninn'];
    const PROMPT_ART_STYLE_KEYS = ['storybook', 'cozy'];   // 大屏提示插圖：溫暖繪本／可愛動森風""")
rep("""boardTitle: '晨間大屏', contactFont: 'default', correctColor: 'brown',""",
    """boardTitle: '晨間大屏', contactFont: 'default', promptArt: 'storybook', correctColor: 'brown',""")
rep("""          s.contactFont = CONTACT_FONTS.includes(saved.contactFont) ? saved.contactFont : 'default';
""",
    """          s.contactFont = CONTACT_FONTS.includes(saved.contactFont) ? saved.contactFont : 'default';
          s.promptArt = PROMPT_ART_STYLE_KEYS.includes(saved.promptArt) ? saved.promptArt : 'storybook';
""")

# 設定頁欄位（放在「待訂正」顏色前面）
rep("""          <div class="field"><label>「待訂正」的顏色</label><select id="setupCorrectColor">""",
    """          <div class="field"><label>大屏提示插圖風格</label><select id="setupPromptArt">
            <option value="storybook">溫暖繪本（手繪水彩感）</option>
            <option value="cozy">可愛動森風（圓潤小島玩具感）</option>
          </select><div class="status-text" style="margin-top:4px">兩套都是原創插圖，存好馬上換。可愛動森風還在畫，沒畫好的句子先用溫暖繪本。</div></div>
          <div class="field"><label>「待訂正」的顏色</label><select id="setupCorrectColor">""")
rep("""      $('setupContactFont').value = s.contactFont;
""",
    """      $('setupContactFont').value = s.contactFont;
      $('setupPromptArt').value = s.promptArt;
      document.dispatchEvent(new Event('promptartchange'));
""")
rep("""      s.contactFont = CONTACT_FONTS.includes($('setupContactFont').value) ? $('setupContactFont').value : 'default';
""",
    """      s.contactFont = CONTACT_FONTS.includes($('setupContactFont').value) ? $('setupContactFont').value : 'default';
      s.promptArt = PROMPT_ART_STYLE_KEYS.includes($('setupPromptArt').value) ? $('setupPromptArt').value : 'storybook';
""")

# 提示插圖：兩套風格
m = re.search(r"    // 原創插圖「溫暖繪本」（ART-02 R4 驗收通過）；列在這裡的 id 用新圖，沒列的繼續用舊圖\n    const PROMPT_ART_READY = new Set\(\[\n((?:      '[a-z_]+',\n)+)    \]\);\n    const PROMPT_ART_DIR = 'assets/art/cozy/prompt/';\n", s)
assert m, '找不到 PROMPT_ART_READY'
ids = re.findall(r"'([a-z_]+)'", m.group(1))
assert len(ids) == 33
s = s[:m.start()] + """    // 原創插圖兩套，設定頁「大屏提示插圖風格」切換。ready 列出已驗收的 id；
    // 選的風格沒有這張就用溫暖繪本，再沒有才用舊圖
    const PROMPT_ART_STYLES = {
      storybook: { dir: 'assets/art/storybook/prompt/', ready: new Set([   // 溫暖繪本（ART-02 R4）
""" + m.group(1).replace("      '", "        '") + """      ]) },
      cozy: { dir: 'assets/art/cozy/prompt/', ready: new Set([]) }   // 可愛動森風（ART-03 製作中）
    };
    function promptArtFile(id) {
      const chosen = PROMPT_ART_STYLES[state.settings.promptArt] || PROMPT_ART_STYLES.storybook;
      const style = [chosen, PROMPT_ART_STYLES.storybook].find(item => item.ready.has(id));
      return style ? style.dir + id + '.webp' : '';
    }
""" + s[m.end():]
rep("""      if (item && PROMPT_ART_READY.has(item.id)) return PROMPT_ART_DIR + item.id + '.webp';
      return 'assets/irasutoya/' + ((item && item.img) || 'class_focus.png');""",
    """      return (item && promptArtFile(item.id)) || 'assets/irasutoya/' + ((item && item.img) || 'class_focus.png');""")
rep("""      if (PROMPT_ART_READY.has('custom_default')) return PROMPT_ART_DIR + 'custom_default.webp';
      return 'assets/irasutoya/' +""",
    """      return promptArtFile('custom_default') || 'assets/irasutoya/' +""")
rep("""      const usingLegacy = PROMPTS.some(item => !PROMPT_ART_READY.has(item.id));""",
    """      const usingLegacy = PROMPTS.some(item => !promptArtFile(item.id));""")
rep("""      img.hidden = !item && !PROMPT_ART_READY.has('custom_default');""",
    """      img.hidden = !item && !promptArtFile('custom_default');""")
rep("""    pop.querySelector('.pp-close').addEventListener('click', closePop);""",
    """    pop.querySelector('.pp-close').addEventListener('click', closePop);
    // 設定頁換插圖風格：提示分頁與正在顯示的跳出畫面馬上換圖
    document.addEventListener('promptartchange', () => {
      applyPrompt(false);
      updatePromptCredit();
      const popImg = pop.querySelector('.pp-img');
      if (!pop.hidden && popImg.src) popImg.src = popImg.getAttribute('src').replace(/assets\\/art\\/(storybook|cozy)\\/prompt\\/([a-z_]+)\\.webp$/, (all, from, id) => promptArtFile(id) || all);
    });""")
rep("""    // id＝新插圖檔名（assets/art/cozy/prompt/<id>.webp）；""",
    """    // id＝新插圖檔名（assets/art/<storybook|cozy>/prompt/<id>.webp）；""")
assert 'PROMPT_ART_READY' not in s and 'PROMPT_ART_DIR' not in s

path.write_text(s, encoding='utf-8')
print('ok', len(ids))
