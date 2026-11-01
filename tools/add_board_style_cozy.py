"""大屏風格：標準／可愛動森風（設定 → 大屏風格），介面與提示插圖一起換
- 取代上一版只換插圖的「大屏提示插圖風格」（promptArt → boardStyle：standard／cozy）
- 動森風介面：奶油底、木頭邊、圓潤玩具感按鈕、粉圓字型（assets/fonts，只有選動森風才載入）
- 動森風圖示（ART-01 cozy）交件驗收後，把 id 加進 COZY_ICON_READY；沒列的維持原圖示
python tools/add_board_style_cozy.py
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'boardStyle' not in s, '已套用過'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 設定值 ----------
rep("""    const PROMPT_ART_STYLE_KEYS = ['storybook', 'cozy'];   // 大屏提示插圖：溫暖繪本／可愛動森風""",
    """    const BOARD_STYLES = ['standard', 'cozy'];   // 大屏風格：標準（提示插圖＝溫暖繪本）／可愛動森風（介面＋插圖）""")
rep("""contactFont: 'default', promptArt: 'storybook', correctColor""",
    """contactFont: 'default', boardStyle: 'standard', correctColor""")
rep("""          s.promptArt = PROMPT_ART_STYLE_KEYS.includes(saved.promptArt) ? saved.promptArt : 'storybook';""",
    """          s.boardStyle = BOARD_STYLES.includes(saved.boardStyle) ? saved.boardStyle : 'standard';""")
rep("""          <div class="field"><label>大屏提示插圖風格</label><select id="setupPromptArt">
            <option value="storybook">溫暖繪本（手繪水彩感）</option>
            <option value="cozy">可愛動森風（圓潤小島玩具感）</option>
          </select><div class="status-text" style="margin-top:4px">兩套都是原創插圖，存好馬上換。可愛動森風還在畫，沒畫好的句子先用溫暖繪本。</div></div>""",
    """          <div class="field"><label>大屏風格</label><select id="setupBoardStyle">
            <option value="standard">標準（現在的樣子，提示插圖用溫暖繪本）</option>
            <option value="cozy">可愛動森風（介面與提示插圖一起換）</option>
          </select><div class="status-text" style="margin-top:4px">存好馬上換，都是原創美術。動森風的圖示與插圖還在畫，沒畫好的先用標準版的圖。</div></div>""")
rep("""      $('setupPromptArt').value = s.promptArt;
      document.dispatchEvent(new Event('promptartchange'));""",
    """      $('setupBoardStyle').value = s.boardStyle;
      applyBoardStyle();""")
rep("""      s.promptArt = PROMPT_ART_STYLE_KEYS.includes($('setupPromptArt').value) ? $('setupPromptArt').value : 'storybook';""",
    """      s.boardStyle = BOARD_STYLES.includes($('setupBoardStyle').value) ? $('setupBoardStyle').value : 'standard';""")

# ---------- 套用風格：介面、圖示，再通知提示插圖換圖 ----------
rep("""    function saveSettings() {""",
    """    // 動森風圖示（ART-01 cozy）：驗收後把 id 加進來就會換成 assets/art/cozy/icon/<id>.webp；沒列的維持原圖示
    const COZY_ICON_READY = new Set([]);
    const TAB_ICON_IDS = { rollcall: 'tab_rollcall', homework: 'tab_homework', makeup: 'tab_makeup', correct: 'tab_correct', query: 'tab_query', tools: 'tab_tools', setup: 'tab_setup' };
    function applyBoardStyle() {
      const cozy = state.settings.boardStyle === 'cozy';
      document.documentElement.dataset.boardStyle = state.settings.boardStyle;
      const iconSrc = id => cozy && COZY_ICON_READY.has(id) ? 'assets/art/cozy/icon/' + id + '.webp' : '';
      document.querySelectorAll('.tab-button[data-page] .tab-icon, img[data-icon]').forEach(img => {
        if (!img.dataset.origSrc) img.dataset.origSrc = img.getAttribute('src');
        const id = img.dataset.icon || TAB_ICON_IDS[img.closest('.tab-button').dataset.page];
        img.src = iconSrc(id) || img.dataset.origSrc;
      });
      document.querySelectorAll('.tool-tab[data-tool] .tt-ico').forEach(span => {
        if (span.dataset.origText === undefined) span.dataset.origText = span.textContent;
        const src = iconSrc('tool_' + span.closest('.tool-tab').dataset.tool);
        if (src) span.innerHTML = `<img class="tt-img" src="${src}" alt="">`;
        else span.textContent = span.dataset.origText;
      });
      document.dispatchEvent(new Event('boardstylechange'));
    }
    function saveSettings() {""")
rep("""display:inline-flex;align-items:center;gap:6px"><img class="tab-icon" src=""",
    """display:inline-flex;align-items:center;gap:6px"><img class="tab-icon" data-icon="contact_book" src=""")

# ---------- 提示插圖跟著大屏風格 ----------
rep("""    // 原創插圖兩套，設定頁「大屏提示插圖風格」切換。""",
    """    // 原創插圖兩套，跟著設定頁「大屏風格」切換（標準＝溫暖繪本）。""")
rep("""      const chosen = PROMPT_ART_STYLES[state.settings.promptArt] || PROMPT_ART_STYLES.storybook;""",
    """      const chosen = state.settings.boardStyle === 'cozy' ? PROMPT_ART_STYLES.cozy : PROMPT_ART_STYLES.storybook;""")
rep("""    // 設定頁換插圖風格：提示分頁與正在顯示的跳出畫面馬上換圖
    document.addEventListener('promptartchange', () => {""",
    """    // 設定頁換大屏風格：提示分頁與正在顯示的跳出畫面馬上換圖
    document.addEventListener('boardstylechange', () => {""")

# ---------- 動森風介面 CSS（放在第一個 style 的最後） ----------
COZY_CSS = """
    /* ===== 大屏風格：可愛動森風（設定 → 大屏風格）。只換外觀，功能顏色（到校綠、病假橘…）保留原意 ===== */
    html[data-board-style="cozy"] {
      --bg: #fbf5e6; --surface: #fffaf0; --ink: #5b4636; --muted: #8f7b63; --line: #ecdcbc;
      --primary: #4f9e45; --primary-strong: #3c7f35;
      --ok: #4fae5b; --ok-soft: #eaf5dc;
      --blank: #c4b394;
      --cozy-wood: #e2c999; --cozy-wood-deep: #c9a66b; --cozy-leaf: #6cbf5b; --cozy-leaf-deep: #4f9e45;
      --cozy-sky: #5ab4e5; --cozy-sky-deep: #3f9bd0; --cozy-paper: #fffdf6;
    }
    html[data-board-style="cozy"] body {
      background-color: var(--bg);
      background-image: radial-gradient(circle at 14px 14px, rgba(108,191,91,.13) 3px, transparent 4px),
        radial-gradient(circle at 42px 42px, rgba(90,180,229,.10) 3px, transparent 4px);
      background-size: 56px 56px;
    }
    html[data-board-style="cozy"] body, html[data-board-style="cozy"] button,
    html[data-board-style="cozy"] select, html[data-board-style="cozy"] input { font-family: 'Huninn', 'Microsoft JhengHei', 'Noto Sans TC', sans-serif; }
    html[data-board-style="cozy"] header { background: var(--surface); border-bottom: 0; box-shadow: 0 4px 0 var(--cozy-wood), 0 10px 18px -12px rgba(91,70,54,.4); }
    html[data-board-style="cozy"] .brand, html[data-board-style="cozy"] .clock { color: #6b4f37; }
    html[data-board-style="cozy"] .countdown-box { background: #eef7e2; border: 3px solid #cfe5b5; border-radius: 999px; }
    html[data-board-style="cozy"] .tabs { gap: 10px; padding-top: 12px; }
    html[data-board-style="cozy"] .tab-button { border: 3px solid var(--cozy-wood); border-bottom: 0; border-radius: 22px 22px 0 0; background: var(--cozy-paper); color: #7a5c3e; box-shadow: inset 0 -4px 0 rgba(201,166,107,.22); }
    html[data-board-style="cozy"] .tab-button.active { background: var(--cozy-leaf); border-color: var(--cozy-leaf-deep); color: #fff; text-shadow: 0 1px 0 rgba(47,107,44,.45); box-shadow: inset 0 -5px 0 var(--cozy-leaf-deep); }
    html[data-board-style="cozy"] .tab-icon { border-radius: 50%; background: #fff; box-shadow: 0 0 0 2px #fff; }
    html[data-board-style="cozy"] .panel { border: 3px solid var(--cozy-wood); border-radius: 0 28px 28px 28px; box-shadow: 0 5px 0 var(--cozy-wood), 0 16px 26px -16px rgba(91,70,54,.4); }
    html[data-board-style="cozy"] .ghost-button, html[data-board-style="cozy"] .mode-button, html[data-board-style="cozy"] .class-pill {
      border: 3px solid var(--cozy-wood); border-radius: 999px; background: var(--cozy-paper); color: #6b4f37; box-shadow: 0 4px 0 var(--cozy-wood); }
    html[data-board-style="cozy"] .mode-button.active, html[data-board-style="cozy"] .class-pill.active {
      background: var(--cozy-sky); border-color: var(--cozy-sky-deep); color: #fff; box-shadow: 0 4px 0 var(--cozy-sky-deep); }
    html[data-board-style="cozy"] .primary-button { border-radius: 999px; background: var(--cozy-leaf); color: #fff; text-shadow: 0 1px 0 rgba(47,107,44,.45); box-shadow: 0 5px 0 var(--cozy-leaf-deep); }
    html[data-board-style="cozy"] .tool-tab { border-width: 3px; border-radius: 24px; box-shadow: 0 5px 0 var(--cozy-wood); }   /* 底色沿用各工具的分類色 */
    html[data-board-style="cozy"] .tool-tab.active { box-shadow: 0 5px 0 rgba(91,70,54,.28), 0 12px 20px -10px var(--tc); }
    html[data-board-style="cozy"] .tt-img { width: 34px; height: 34px; display: block; }
    html[data-board-style="cozy"] .ghost-button:active, html[data-board-style="cozy"] .mode-button:active,
    html[data-board-style="cozy"] .primary-button:active, html[data-board-style="cozy"] .tool-tab:active { transform: translateY(3px); box-shadow: 0 1px 0 var(--cozy-wood); }
    html[data-board-style="cozy"] .seat { border-radius: 22px; box-shadow: inset 0 -6px 0 rgba(0,0,0,.12), 0 3px 0 rgba(91,70,54,.16); }
    html[data-board-style="cozy"] .hw-seat, html[data-board-style="cozy"] .check-seat { border-radius: 14px; box-shadow: inset 0 -4px 0 rgba(0,0,0,.12); }
    html[data-board-style="cozy"] .board-card { background: var(--cozy-paper); border: 3px solid var(--line); border-radius: 22px; }
    html[data-board-style="cozy"] .field input, html[data-board-style="cozy"] .field select, html[data-board-style="cozy"] .inline-select {
      border: 3px solid var(--cozy-wood); border-radius: 16px; background: var(--cozy-paper); color: var(--ink); }
    html[data-board-style="cozy"] .submit-bar { background: var(--surface); border-top: 0; box-shadow: 0 -4px 0 var(--cozy-wood), 0 -10px 18px -12px rgba(91,70,54,.35); }
  </style>"""
first_close = s.index('  </style>')
s = s[:first_close] + COZY_CSS.lstrip('\n') + s[first_close + len('  </style>'):]

assert not re.search(r'promptArt(?!File)', s) and 'PROMPT_ART_STYLE_KEYS' not in s and 'promptartchange' not in s
path.write_text(s, encoding='utf-8')
print('ok')
