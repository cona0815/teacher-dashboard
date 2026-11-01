"""工作台新增介面配色「可愛動森風」（設定 → 介面配色），跟晨間大屏的動森風同一套：
奶油底、木頭邊、草綠／天空藍、圓潤玩具感按鈕、粉圓字型（assets/fonts，只有選這套才載入）
python tools/add_index_cozy_theme.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Index.html'
s = path.read_text(encoding='utf-8')
assert 'data-theme="cozy"' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""    const INTERFACE_THEMES = ['forest', 'apricot', 'lavender', 'tech', 'minimal'];""",
    """    const INTERFACE_THEMES = ['forest', 'apricot', 'lavender', 'tech', 'minimal', 'cozy'];""")
rep("""<strong>極簡霧灰</strong><small>低彩度・專注閱讀</small></button>""",
    """<strong>極簡霧灰</strong><small>低彩度・專注閱讀</small></button>
              <button class="theme-choice" type="button" data-theme-choice="cozy" aria-pressed="false"><span class="theme-swatches" aria-hidden="true"><span></span><span></span><span></span></span><strong>可愛動森風</strong><small>奶油草綠・圓潤玩具感</small></button>""")
rep("""    .theme-picker { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 9px; }""",
    """    .theme-picker { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }""")
rep("""    @media (max-width: 900px) { .theme-picker { grid-template-columns: repeat(3, minmax(0, 1fr)); } }""",
    """    .theme-choice[data-theme-choice="cozy"] .theme-swatches span:nth-child(1) { background: #6cbf5b; }
    .theme-choice[data-theme-choice="cozy"] .theme-swatches span:nth-child(2) { background: #5ab4e5; }
    .theme-choice[data-theme-choice="cozy"] .theme-swatches span:nth-child(3) { background: #fbf5e6; border: 1px solid #e2c999; }
    @media (max-width: 900px) { .theme-picker { grid-template-columns: repeat(3, minmax(0, 1fr)); } }""")

COZY = """
    /* 可愛動森風：跟晨間大屏的動森風同一套（奶油底、木頭邊、圓潤玩具感按鈕、粉圓字型） */
    :root[data-theme="cozy"] {
      --bg: #fbf5e6;
      --surface: #fffaf0;
      --ink: #5b4636;
      --muted: #8f7b63;
      --line: #ecdcbc;
      --primary: #4f9e45;
      --primary-strong: #3c7f35;
      --primary-soft: #eaf5dc;
      --accent: #3f9bd0;
      --accent-soft: #e3f2fb;
      --gold: #b48a4c;
      --gold-soft: #f6ecd6;
      --danger: #c8574a;
      --warning: #93651c;
      --success: #4f9e45;
      --radius: 22px;
      --shadow: 0 4px 0 rgba(201,166,107,.45), 0 12px 22px -14px rgba(91,70,54,.35);
      --cozy-wood: #e2c999; --cozy-leaf: #6cbf5b; --cozy-leaf-deep: #4f9e45; --cozy-sky: #5ab4e5; --cozy-sky-deep: #3f9bd0; --cozy-paper: #fffdf6;
    }
"""
rep("""    * { box-sizing: border-box; }
    html, body { margin: 0;""", COZY.lstrip('\n') + """
    * { box-sizing: border-box; }
    html, body { margin: 0;""")

COZY_PARTS = """
    @font-face { font-family: 'Huninn'; font-display: swap;
      src: local('Huninn'), local('Huninn Regular'), url('assets/fonts/Huninn-Regular.ttf') format('truetype'); }
    :root[data-theme="cozy"] body {
      background-image: radial-gradient(circle at 14px 14px, rgba(108,191,91,.13) 3px, transparent 4px), radial-gradient(circle at 42px 42px, rgba(90,180,229,.10) 3px, transparent 4px);
      background-size: 56px 56px;
    }
    :root[data-theme="cozy"] body, :root[data-theme="cozy"] button, :root[data-theme="cozy"] input,
    :root[data-theme="cozy"] select, :root[data-theme="cozy"] textarea { font-family: 'Huninn', 'Microsoft JhengHei', 'Noto Sans TC', sans-serif; }
    :root[data-theme="cozy"] .topbar { background: linear-gradient(135deg, var(--cozy-leaf), var(--cozy-leaf-deep)); border-radius: 26px; box-shadow: 0 5px 0 #3c7f35, 0 14px 24px -14px rgba(60,127,53,.55); }
    :root[data-theme="cozy"] .panel { border: 3px solid var(--cozy-wood); border-radius: 26px; }
    :root[data-theme="cozy"] .summary-card { border: 2px solid var(--cozy-wood); border-radius: 20px; box-shadow: 0 4px 0 var(--cozy-wood); }
    :root[data-theme="cozy"] .button { border-radius: 999px; box-shadow: 0 4px 0 rgba(91,70,54,.22); }
    :root[data-theme="cozy"] .button:active, :root[data-theme="cozy"] .mini-button:active, :root[data-theme="cozy"] .secondary-button:active,
    :root[data-theme="cozy"] .toolbox-button:active { transform: translateY(3px); box-shadow: 0 1px 0 rgba(91,70,54,.22); }
    :root[data-theme="cozy"] .button-dark { background: var(--cozy-leaf); box-shadow: 0 4px 0 var(--cozy-leaf-deep); text-shadow: 0 1px 0 rgba(47,107,44,.4); }
    :root[data-theme="cozy"] .button-light { background: var(--primary-soft); border-color: #cfe5b5; box-shadow: 0 4px 0 #cfe5b5; }
    :root[data-theme="cozy"] .button-ghost { background: var(--cozy-paper); border: 2px solid var(--cozy-wood); box-shadow: 0 4px 0 var(--cozy-wood); }
    :root[data-theme="cozy"] .mini-button, :root[data-theme="cozy"] .secondary-button, :root[data-theme="cozy"] .toolbox-button {
      border: 2px solid var(--cozy-wood); border-radius: 999px; background: var(--cozy-paper); box-shadow: 0 3px 0 var(--cozy-wood); }
    :root[data-theme="cozy"] .toolbox-button.active { border-color: var(--cozy-sky-deep); background: var(--cozy-sky); color: #fff; box-shadow: 0 3px 0 var(--cozy-sky-deep); }
    :root[data-theme="cozy"] .settings-tab { border: 2px solid var(--cozy-wood); border-radius: 999px; background: var(--cozy-paper); }
    :root[data-theme="cozy"] .settings-tab.active { border-color: var(--cozy-leaf-deep); background: var(--cozy-leaf); color: #fff; }
    :root[data-theme="cozy"] .role-person { border-color: var(--cozy-wood); background: var(--cozy-paper); box-shadow: 0 3px 0 var(--cozy-wood); }
    :root[data-theme="cozy"] .input, :root[data-theme="cozy"] .select, :root[data-theme="cozy"] .textarea { border-color: var(--cozy-wood); border-radius: 16px; background: var(--cozy-paper); }
"""
rep("""    :root[data-theme="minimal"] .topbar::after { display: none; }
""", """    :root[data-theme="minimal"] .topbar::after { display: none; }
""" + COZY_PARTS.lstrip('\n'))

path.write_text(s, encoding='utf-8')
print('ok')
