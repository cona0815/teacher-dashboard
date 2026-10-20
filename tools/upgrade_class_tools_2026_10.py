"""2026-10 班級工具大升級：動畫與 UI。

執行一次：python tools/upgrade_class_tools_2026_10.py
- 只加版面、動畫、音效與小綿羊吉祥物，不改資料格式（config.scores、day.drawn、day.boards 照舊）。
- 小綿羊動畫由 assets/pet/frames 壓成 160px 動態 WebP 後內嵌，維持大屏單檔可攜。
"""
import base64
import io
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from desktop_pet_preview import DesktopPetPreview as P  # noqa: E402

path = REPO / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert '2026-10 班級工具大升級' not in s, '已經升級過了'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ---------------------------------------------------------------- 小綿羊動畫
def sheep_webp(state):
    frames = [Image.open(p).convert('RGBA').resize((160, 160), Image.LANCZOS)
              for p in sorted((REPO / 'assets' / 'pet' / 'frames' / f'pet_{state}').glob('*.png'))]
    buf = io.BytesIO()
    frames[0].save(buf, 'WEBP', save_all=True, append_images=frames[1:], duration=P.FRAME_DELAYS[state],
                   loop=0, quality=55, alpha_quality=60, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


SHEEP_STATES = ['idle', 'sign', 'think', 'success', 'focus', 'stretch', 'sleep', 'warning']
sheep_js = '  const SHEEP = {\n' + ',\n'.join(f"    {st}: '{sheep_webp(st)}'" for st in SHEEP_STATES) + '\n  };\n'

# ---------------------------------------------------------------- CSS
CSS = r'''
        /* ===== 2026-10 班級工具大升級：動畫與 UI ===== */
        /* 有 hidden 屬性就一定藏起來（舊樣式的 display:flex 會蓋掉 hidden，造成編輯框與名稱列常駐） */
        .tool-opts[hidden], .tomato-edit[hidden], .tomato-time[hidden], .tool-panel[hidden] { display: none !important; }
        #toolTabs { gap: 10px; }
        #toolTabs .status-text { flex-basis: 100%; margin-top: 2px; }
        .tool-tab[data-tool="lottery"] { --tc: #d9573f; --tc-soft: #fdece8; }
        .tool-tab[data-tool="check"] { --tc: #2273c9; --tc-soft: #e6f0fb; }
        .tool-tab[data-tool="score"] { --tc: #b07d12; --tc-soft: #fbf1da; }
        .tool-tab[data-tool="group"] { --tc: #7b4fb8; --tc-soft: #f1eafa; }
        .tool-tab[data-tool="quiet"] { --tc: #1d9e5f; --tc-soft: #e3f6ec; }
        .tool-tab[data-tool="exam"] { --tc: #2457e6; --tc-soft: #e7edfc; }
        .tool-tab[data-tool="tomato"] { --tc: #e0523f; --tc-soft: #fdebe6; }
        .tool-tab[data-tool="prompt"] { --tc: #1f514a; --tc-soft: #e8f2ee; }
        .tool-tab { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; min-width: 108px; padding: 10px 14px 9px; border: 2px solid transparent; border-radius: 18px; background: var(--tc-soft); color: var(--tc); font-size: 15.5px; line-height: 1.2; box-shadow: 0 2px 0 rgba(0,0,0,.05); transition: transform .18s cubic-bezier(.3,1.6,.5,1), box-shadow .18s, background .18s, color .18s; }
        .tool-tab .tt-ico { font-size: 30px; line-height: 1; transition: transform .25s cubic-bezier(.3,1.6,.5,1); }
        .tool-tab:hover { transform: translateY(-2px); }
        .tool-tab:hover .tt-ico { transform: scale(1.12) rotate(-6deg); }
        .tool-tab.active { background: var(--tc); color: #fff; border-color: var(--tc); transform: translateY(-3px); box-shadow: 0 10px 20px -8px var(--tc); }
        .tool-tab.active .tt-ico { animation: ttBounce .6s cubic-bezier(.3,1.6,.5,1); }
        @keyframes ttBounce { 0% { transform: scale(.6); } 60% { transform: scale(1.22); } 100% { transform: scale(1); } }
        .tool-panel:not([hidden]) { animation: panelIn .35s ease both; }
        @keyframes panelIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
        .tool-panel:fullscreen { background: var(--bg); padding: 3vh 3vw; overflow: auto; }
        .mascot { width: 150px; height: 150px; object-fit: contain; pointer-events: none; filter: drop-shadow(0 8px 10px rgba(30,50,40,.18)); }
        .mascot.pop { animation: mascotPop .6s cubic-bezier(.3,1.6,.5,1); }
        @keyframes mascotPop { 0% { transform: scale(.5) translateY(24px); opacity: 0; } 100% { transform: none; opacity: 1; } }
        .fx-canvas { position: fixed; inset: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 95; }
        @keyframes chipIn { 0% { transform: scale(.3); opacity: 0; } 70% { transform: scale(1.12); } 100% { transform: none; opacity: 1; } }

        /* 🎡 抽籤：舞台、跑馬燈、放射光芒、號碼牌 */
        .lottery-stage { background: radial-gradient(120% 90% at 50% 35%, #fffaf0 0%, #ffe9dc 55%, #f9d3c3 100%); border: 0; box-shadow: inset 0 0 0 3px rgba(217,87,63,.18), 0 14px 30px -18px rgba(120,40,20,.45); min-height: 390px; gap: 34px; padding: 26px 18px; }
        .lot-wheel-wrap { width: 340px; height: 340px; }
        .lot-bulbs { position: absolute; inset: 0; pointer-events: none; z-index: 1; }
        .lot-bulbs i { position: absolute; left: 50%; top: 50%; width: 13px; height: 13px; margin: -6.5px; border-radius: 50%; transform: rotate(var(--a)) translateY(calc(-1 * var(--r, 180px))); background: #ffe38a; animation: bulbChase 1.2s steps(1) infinite; animation-delay: calc(var(--k) * -.4s); }
        @keyframes bulbChase { 0% { background: #fff3b0; box-shadow: 0 0 10px 3px rgba(255,214,90,.9); } 33% { background: #f6c445; box-shadow: 0 0 5px 1px rgba(255,190,60,.6); } 66% { background: #c99a45; box-shadow: none; } }
        .lottery-stage.spinning .lot-bulbs i { animation-duration: .27s; }
        .lot-result-wrap { position: relative; min-width: 250px; min-height: 220px; display: flex; align-items: center; justify-content: center; }
        .lot-rays { position: absolute; left: 50%; top: 50%; width: 420px; height: 420px; margin: -210px; border-radius: 50%; background: repeating-conic-gradient(from 0deg, rgba(255,190,70,.42) 0 9deg, rgba(255,190,70,0) 9deg 18deg); -webkit-mask: radial-gradient(circle, #000 22%, transparent 68%); mask: radial-gradient(circle, #000 22%, transparent 68%); opacity: 0; transform: scale(.4); transition: opacity .4s, transform .7s cubic-bezier(.3,1.5,.5,1); pointer-events: none; }
        .lottery-stage.revealed .lot-rays { opacity: 1; transform: scale(1); animation: raySpin 10s linear infinite; }
        @keyframes raySpin { from { transform: scale(1) rotate(0); } to { transform: scale(1) rotate(360deg); } }
        .lot-result { position: relative; z-index: 2; font-size: 118px; color: #c2410c; text-shadow: 0 4px 0 #fff, 0 12px 24px rgba(194,65,12,.25); }
        .lottery-stage.spinning .lot-result { animation: suspense .5s ease-in-out infinite; }
        @keyframes suspense { 50% { transform: scale(1.12); opacity: .6; } }
        .lot-mascot { position: absolute; right: 14px; bottom: 4px; z-index: 3; }
        .lot-drawn { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
        .lot-chip { display: inline-flex; align-items: center; gap: 6px; background: #fff; border: 2px solid #f3c9b8; border-radius: 999px; padding: 3px 13px 3px 4px; font-weight: 900; color: #7a2e1c; font-size: 16px; }
        .lot-chip i { font-style: normal; width: 24px; height: 24px; border-radius: 50%; background: #d9573f; color: #fff; display: grid; place-items: center; font-size: 12px; }
        .lot-chip.new { animation: chipIn .5s cubic-bezier(.3,1.6,.5,1) both; border-color: #d9573f; }
        .tool-panel:fullscreen .lottery-stage { min-height: 80vh; }
        .tool-panel:fullscreen #lotWheel { width: auto !important; height: auto !important; }
        .tool-panel:fullscreen .lot-wheel-wrap { width: min(66vh, 56vw); height: min(66vh, 56vw); }
        .tool-panel:fullscreen .lot-result { font-size: clamp(130px, 20vh, 240px); }
        .tool-panel:fullscreen .lot-mascot { width: 220px; height: 220px; }

        /* ✅ 檢核板：進度環、打勾彈跳、完成慶祝、反查閃爍 */
        .check-wall { gap: 16px; }
        .check-card { border: 0; border-radius: 20px; background: #fff; box-shadow: 0 10px 24px -16px rgba(34,115,201,.5), inset 0 0 0 2px #e3ecf7; padding: 14px; transition: box-shadow .3s; }
        .check-card.complete { box-shadow: 0 14px 30px -14px rgba(29,158,95,.55), inset 0 0 0 3px #1d9e5f; }
        .check-head { gap: 10px; }
        .check-ring { position: relative; flex: 0 0 54px; height: 54px; }
        .check-ring svg { width: 54px; height: 54px; transform: rotate(-90deg); display: block; }
        .check-ring circle { fill: none; stroke-width: 6; }
        .check-ring .bg { stroke: #e6eef8; }
        .check-ring .fg { stroke: #2273c9; stroke-linecap: round; transition: stroke-dashoffset .55s cubic-bezier(.3,1.2,.5,1), stroke .3s; }
        .check-card.complete .check-ring .fg { stroke: #1d9e5f; }
        .check-ring b { position: absolute; inset: 0; display: grid; place-items: center; font-size: 13px; font-weight: 900; color: #2273c9; }
        .check-card.complete .check-ring b { color: #1d9e5f; }
        .check-seat { position: relative; border-radius: 12px; transition: transform .12s, background .2s, border-color .2s; }
        .check-seat:active { transform: scale(.9); }
        .check-seat.done::after { content: "✓"; position: absolute; right: 4px; top: 0; font-size: 11px; opacity: .9; }
        .check-seat.pop { animation: seatPop .45s cubic-bezier(.3,1.8,.5,1); }
        @keyframes seatPop { 0% { transform: scale(.7); } 60% { transform: scale(1.2); } 100% { transform: scale(1); } }
        .check-seat.miss { animation: missPulse 1.3s ease-in-out infinite both; animation-delay: calc(var(--i, 0) * 70ms); }
        @keyframes missPulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(207,68,51,0); transform: scale(1); } 50% { box-shadow: 0 0 0 6px rgba(207,68,51,.25); transform: scale(1.06); } }
        .check-complete { font-weight: 900; color: #1d9e5f; animation: chipIn .5s cubic-bezier(.3,1.6,.5,1) both; }
        .tool-panel:fullscreen .check-seat { font-size: 24px; padding: 14px 2px; }

        /* 🏆 計分板：隊伍色、名次、皇冠、長條、飄字 */
        .score-wall { gap: 22px; padding-top: 24px; }
        .score-card { position: relative; border: 0; border-radius: 22px; background: linear-gradient(180deg, var(--team-soft), #fff 72%); box-shadow: 0 12px 26px -18px var(--team), inset 0 0 0 2px var(--team-line); padding: 20px 12px 16px; transition: box-shadow .3s, transform .3s; }
        .score-card.leader { box-shadow: 0 18px 36px -16px var(--team), inset 0 0 0 3px var(--team); transform: translateY(-4px); }
        .score-crown { position: absolute; top: -28px; left: 50%; font-size: 38px; opacity: 0; transform: translateX(-50%); transition: opacity .35s; pointer-events: none; }
        .score-card.leader .score-crown { opacity: 1; animation: crownBob 2.2s ease-in-out infinite; }
        @keyframes crownBob { 0%, 100% { transform: translate(-50%, 0) rotate(-7deg); } 50% { transform: translate(-50%, -7px) rotate(7deg); } }
        .score-rank { position: absolute; top: 10px; left: 12px; font-size: 26px; line-height: 1; }
        .score-name { color: var(--team); }
        .score-value { color: var(--team); font-size: 86px; text-shadow: 0 4px 0 rgba(255,255,255,.95); }
        .score-bar { height: 12px; border-radius: 999px; background: rgba(0,0,0,.06); overflow: hidden; margin: 2px 10px 12px; }
        .score-bar i { display: block; height: 100%; width: 0; background: var(--team); border-radius: 999px; transition: width .7s cubic-bezier(.3,1.3,.5,1); }
        .score-buttons button { width: auto; min-width: 58px; padding: 0 14px; height: 52px; border-radius: 14px; box-shadow: 0 4px 0 rgba(0,0,0,.16); transition: transform .08s, box-shadow .08s; }
        .score-buttons button:active { transform: translateY(3px); box-shadow: 0 1px 0 rgba(0,0,0,.16); }
        .score-plus { background: var(--team); }
        .score-plus5 { background: var(--team); filter: brightness(.86); font-size: 20px !important; }
        .score-minus { background: #9aa7a2; }
        .score-float { position: absolute; left: 50%; top: 34%; font-size: 36px; font-weight: 900; color: var(--team); pointer-events: none; text-shadow: 0 2px 0 #fff; animation: floatUp .95s ease-out forwards; }
        @keyframes floatUp { from { transform: translate(-50%, 0) scale(.8); opacity: 1; } to { transform: translate(-50%, -78px) scale(1.35); opacity: 0; } }
        .tool-panel:fullscreen .score-value { font-size: clamp(96px, 15vh, 190px); }

        /* 👥 分組：洗牌池、飛入、組別色 */
        .group-pool { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; padding: 18px; border-radius: 20px; background: radial-gradient(circle, #f6f0fd, #e9defa); margin-top: 12px; }
        .group-pool span { background: #fff; color: #7b4fb8; border-radius: 10px; padding: 6px 12px; font-size: 18px; font-weight: 900; box-shadow: inset 0 0 0 2px #dccbf3; animation: jiggle .22s ease-in-out infinite alternate; animation-delay: calc(var(--i) * -37ms); }
        @keyframes jiggle { from { transform: translate(-2px, 1px) rotate(-7deg); } to { transform: translate(2px, -1px) rotate(7deg); } }
        .group-card { border: 0; border-radius: 20px; background: linear-gradient(180deg, var(--g-soft), #fff 80%); box-shadow: inset 0 0 0 2px var(--g-line), 0 12px 24px -18px var(--g); }
        .group-card h4 { color: var(--g); }
        .group-card .members span { background: #fff; color: var(--g); box-shadow: inset 0 0 0 2px var(--g-line); }
        .tool-panel:fullscreen .group-card .members span { font-size: 26px; padding: 8px 16px; }

        /* 🔇 安靜：半圓儀表、波紋、星星飛入 */
        .quiet-meter { display: none; }
        .quiet-top { display: flex; align-items: flex-end; justify-content: center; gap: 18px; flex-wrap: wrap; margin: 8px 0 4px; }
        .quiet-gauge { position: relative; width: 300px; }
        .quiet-gauge svg { width: 100%; display: block; overflow: visible; }
        .quiet-level { position: absolute; left: 0; right: 0; bottom: 2px; text-align: center; font-size: 30px; font-weight: 900; color: var(--ink); font-variant-numeric: tabular-nums; }
        #quietNeedle { transition: transform .12s linear; }
        .quiet-stage { position: relative; }
        .quiet-rings { position: absolute; left: 50%; top: 115px; width: 0; height: 0; pointer-events: none; --lv: 0; }
        .quiet-rings i { position: absolute; left: -110px; top: -110px; width: 220px; height: 220px; border-radius: 50%; border: 6px solid #1d9e5f; opacity: 0; animation: ringOut 2.4s ease-out infinite; }
        .quiet-rings i:nth-child(2) { animation-delay: .8s; } .quiet-rings i:nth-child(3) { animation-delay: 1.6s; }
        .quiet-rings[data-mood="warn"] i { border-color: #f2b53c; }
        .quiet-rings[data-mood="loud"] i { border-color: #cf4433; animation-duration: .9s; }
        .quiet-rings[data-mood="off"] i { display: none; }
        @keyframes ringOut { from { transform: scale(calc(.45 + var(--lv) * .5)); opacity: .55; } to { transform: scale(calc(.9 + var(--lv) * 1.8)); opacity: 0; } }
        .quiet-img { position: relative; z-index: 1; }
        .quiet-star-fly { position: fixed; z-index: 96; font-size: 46px; pointer-events: none; }

        /* 📝 定評 */
        .exam-board { background: radial-gradient(120% 90% at 50% 0%, #eef2ff, #fff 62%); border-radius: 26px; padding: 22px 12px 16px; box-shadow: inset 0 0 0 2px #e1e7fb; }
        .exam-badge { display: inline-flex; align-items: center; gap: 8px; background: #2457e6; color: #fff; font-weight: 900; border-radius: 999px; padding: 6px 20px; font-size: 18px; letter-spacing: .12em; animation: examPulse 2.4s ease-in-out infinite; }
        @keyframes examPulse { 50% { box-shadow: 0 0 0 10px rgba(36,87,230,.12); } }
        .exam-sec { width: min(520px, 80%); height: 8px; margin: 4px auto 6px; background: #e1e7fb; border-radius: 999px; overflow: hidden; }
        .exam-sec i { display: block; height: 100%; width: 0; background: linear-gradient(90deg, #2457e6, #a832e0); border-radius: 999px; transition: width 1s linear; }
        .exam-card { border: 0; border-radius: 20px; box-shadow: 0 10px 24px -18px rgba(36,87,230,.6), inset 0 0 0 2px #e1e7fb; }

        /* 🍅 番茄鐘：進度環、模式色、吉祥物 */
        .tomato-face-wrap { position: relative; width: fit-content; margin: 0 auto 16px; }
        .tomato-face { position: relative; margin: 0; border-width: 0 !important; background: radial-gradient(circle at 50% 38%, #fff, #fff7f3 70%, #fdeee8); --mc: #e0523f; }
        .tomato-face[data-mode="short"] { --mc: #1d9e5f; } .tomato-face[data-mode="long"] { --mc: #2273c9; } .tomato-face[data-mode="custom"] { --mc: #7b4fb8; }
        .tomato-ring { position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg); pointer-events: none; }
        .tomato-ring circle { fill: none; stroke-width: 6.5; }
        .tomato-ring .bg { stroke: #f1e7e3; }
        .tomato-ring .fg { stroke: var(--mc); stroke-linecap: round; transition: stroke-dashoffset 1s linear, stroke .4s; }
        .tomato-time, .tomato-edit { position: relative; z-index: 1; }
        .tomato-face.running .tomato-time { color: var(--mc); }
        .tomato-mascot { position: absolute; right: -118px; bottom: -6px; }
        @media (max-width: 700px) { .tomato-mascot { display: none; } }
        .tool-panel:fullscreen .tomato-mascot, .tomato-board:fullscreen .tomato-mascot { width: 220px; height: 220px; right: -200px; }

        /* 📣 大屏提示：圖磚、分類色、換句轉場 */
        .prompt-tiles { display: grid; gap: 10px; margin: 4px 0 14px; }
        .prompt-group-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .prompt-group-row > b { min-width: 108px; font-size: 14px; color: var(--muted); }
        .prompt-tile { border: 0; border-radius: 14px; padding: 8px 14px; font-weight: 900; font-size: 15px; cursor: pointer; background: var(--pg-soft); color: var(--pg); box-shadow: inset 0 0 0 2px var(--pg-line); font-family: inherit; transition: transform .15s cubic-bezier(.3,1.6,.5,1), background .2s, color .2s; }
        .prompt-tile:hover { transform: translateY(-2px); }
        .prompt-tile.active { background: var(--pg); color: #fff; box-shadow: 0 8px 16px -8px var(--pg); }
        .prompt-board { border-radius: 26px; padding: 20px 12px 12px; background: var(--pb, linear-gradient(160deg, #eaf6f0, #fff)); box-shadow: inset 0 0 0 2px rgba(0,0,0,.04); transition: background .6s; }
        .prompt-message.swap { animation: promptSwap .65s cubic-bezier(.3,1.4,.5,1); }
        @keyframes promptSwap { from { opacity: 0; transform: translateY(28px) scale(.95); } to { opacity: 1; transform: none; } }
        .prompt-img.swap { animation: promptImgIn .75s cubic-bezier(.3,1.6,.5,1), quietFloat 3.4s ease-in-out .75s infinite; }
        @keyframes promptImgIn { from { opacity: 0; transform: scale(.4) rotate(-10deg); } to { opacity: 1; transform: none; } }
        @media (prefers-reduced-motion: reduce) {
          .tool-tab, .tool-tab .tt-ico, .tool-panel, .mascot, .lot-bulbs i, .lot-rays, .lot-chip, .check-seat, .score-crown, .score-float, .group-pool span, .quiet-rings i, .exam-badge, .prompt-message, .prompt-img { animation: none !important; transition: none !important; }
        }
'''
rep('        .prompt-board:fullscreen .prompt-img { max-height: 38vh; }\n      </style>',
    '        .prompt-board:fullscreen .prompt-img { max-height: 38vh; }\n' + CSS + '      </style>')

# ---------------------------------------------------------------- HTML：工具分頁磚
for tool, ico, label in [('lottery', '🎡', '抽籤機'), ('check', '✅', '檢核板'), ('score', '🏆', '計分板'), ('group', '👥', '隨機分組'),
                         ('quiet', '🔇', '安靜偵測'), ('exam', '📝', '定評小幫手'), ('tomato', '🍅', '番茄鐘'), ('prompt', '📣', '大屏提示')]:
    active = ' active' if tool == 'lottery' else ''
    rep(f'<button class="tool-tab{active}" type="button" data-tool="{tool}">{ico} {label}</button>',
        f'<button class="tool-tab{active}" type="button" data-tool="{tool}"><span class="tt-ico">{ico}</span><span>{label}</span></button>')

FS = lambda tool: f'<button class="ghost-button" type="button" data-fs-panel="{tool}">⛶ 投影模式</button>'

# 抽籤
rep('<input class="inline-select" id="lotCustomList" placeholder="以、分隔，例：第1組、第2組、第3組" style="max-width:280px" hidden>\n          </div>',
    '<input class="inline-select" id="lotCustomList" placeholder="以、分隔，例：第1組、第2組、第3組" style="max-width:280px" hidden>\n            ' + FS('lottery') + '\n          </div>')
rep('<div class="lot-anim" id="lotWheel" style="width:300px;height:300px">', '<div class="lot-anim" id="lotWheel" style="width:340px;height:340px">')
rep('<div class="lot-wheel-pointer" id="lotPointer"></div>', '<div class="lot-bulbs" id="lotBulbs"></div>\n                <div class="lot-wheel-pointer" id="lotPointer"></div>')
rep('<div class="lot-result" id="lotResult">？</div>\n            <canvas class="lot-confetti" id="lotConfetti"></canvas>',
    '<div class="lot-result-wrap"><div class="lot-rays" id="lotRays"></div><div class="lot-result" id="lotResult">？</div></div>\n'
    '            <img class="mascot lot-mascot" id="lotMascot" alt="">\n'
    '            <canvas class="lot-confetti" id="lotConfetti"></canvas>')
# 檢核、計分、分組
rep('<span class="status-text">點座號＝已點（藍）；按「未點」把沒點的亮紅反查；隔天自動歸零、不留紀錄。</span>',
    FS('check') + '\n            <span class="status-text">點座號＝已點（藍）；按「未點」把沒點的亮紅反查；隔天自動歸零、不留紀錄。</span>')
rep('<label><input type="checkbox" id="scoreSound" checked>音效</label>', '<label><input type="checkbox" id="scoreSound" checked>音效</label>\n            ' + FS('score'))
rep('<label><input type="checkbox" id="groupExcludeAbsent" checked>排除今日缺席</label>', '<label><input type="checkbox" id="groupExcludeAbsent" checked>排除今日缺席</label>\n            ' + FS('group'))
# 安靜偵測
rep('<span class="status-text">需要允許使用麥克風；聲音只在這台電腦即時分析，不錄音、不上傳。</span>\n          </div>',
    FS('quiet') + '\n            <span class="status-text">需要允許使用麥克風；聲音只在這台電腦即時分析，不錄音、不上傳。</span>\n          </div>\n'
    '          <div class="quiet-top">\n'
    '            <img class="mascot" id="quietMascot" alt="">\n'
    '            <div class="quiet-gauge"><svg viewBox="0 0 220 132" role="img" aria-label="音量儀表">\n'
    '              <defs><linearGradient id="quietGrad" x1="0" x2="1"><stop offset="0" stop-color="#1d9e5f"/><stop offset=".6" stop-color="#f2b53c"/><stop offset="1" stop-color="#cf4433"/></linearGradient></defs>\n'
    '              <path d="M20 115 A90 90 0 0 1 200 115" fill="none" stroke="#e8efeb" stroke-width="22" stroke-linecap="round"/>\n'
    '              <path id="quietArc" d="M20 115 A90 90 0 0 1 200 115" fill="none" stroke="url(#quietGrad)" stroke-width="22" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>\n'
    '              <line id="quietTh" x1="110" y1="115" x2="110" y2="10" stroke="#cf4433" stroke-width="3" stroke-dasharray="5 4"/>\n'
    '              <g id="quietNeedle"><line x1="110" y1="115" x2="110" y2="34" stroke="#1c302d" stroke-width="5" stroke-linecap="round"/><circle cx="110" cy="115" r="10" fill="#1c302d"/></g>\n'
    '            </svg><div class="quiet-level" id="quietLevel">0</div></div>\n'
    '          </div>')
rep('<div class="quiet-stage" id="quietStage">\n            <img class="quiet-img"', '<div class="quiet-stage" id="quietStage">\n            <div class="quiet-rings" id="quietRings" data-mood="off"><i></i><i></i><i></i></div>\n            <img class="quiet-img"')
# 定評
rep('<div class="exam-board">\n            <div class="exam-clock" id="examClock">--:--:--</div>',
    '<div class="exam-board">\n            <span class="exam-badge">📝 考試中・請保持安靜</span>\n            <div class="exam-clock" id="examClock">--:--:--</div>\n            <div class="exam-sec"><i id="examSec"></i></div>')
# 番茄鐘
rep('''              <div class="tomato-face" id="tomatoFace">
                <div class="tomato-time" id="tomatoTime">25:00</div>''', '''              <div class="tomato-face-wrap">
              <div class="tomato-face" id="tomatoFace" data-mode="focus">
                <svg class="tomato-ring" viewBox="0 0 100 100" aria-hidden="true"><circle class="bg" cx="50" cy="50" r="45"/><circle class="fg" id="tomatoRing" cx="50" cy="50" r="45" pathLength="100" stroke-dasharray="100" stroke-dashoffset="0"/></svg>
                <div class="tomato-time" id="tomatoTime">25:00</div>''')
rep('''                  <button class="ghost-button" type="button" id="tomatoConfirmButton">確認</button>
                </div>
              </div>''', '''                  <button class="ghost-button" type="button" id="tomatoConfirmButton">確認</button>
                </div>
              </div>
              <img class="mascot tomato-mascot" id="tomatoMascot" alt="">
              </div>''')
# 大屏提示圖磚
rep('''            <button class="ghost-button" type="button" id="promptFullscreenButton">⛶ 全螢幕播放</button>
          </div>''', '''            <button class="ghost-button" type="button" id="promptFullscreenButton">⛶ 全螢幕播放</button>
          </div>
          <div class="prompt-tiles" id="promptTiles"></div>''')

# ---------------------------------------------------------------- JS：共用（吉祥物、慶祝、投影模式、音效）
rep("  function fanfare() { beep(523, .18); setTimeout(() => beep(659, .18), 140); setTimeout(() => beep(784, .34), 280); }",
    '''  // 2026-10 班級工具大升級：更完整的勝利音效（三和弦琶音＋亮音）
  function fanfare() {
    [[523, 0, .16], [659, .12, .16], [784, .24, .16], [1047, .38, .5]].forEach(([freq, delay, dur]) => setTimeout(() => beep(freq, dur, 'triangle', .18), delay * 1000));
    setTimeout(() => { beep(1319, .3, 'sine', .06); beep(1568, .4, 'sine', .05); }, 620);
  }

  // ---------- 小綿羊吉祥物（內嵌動態 WebP，維持單檔可攜） ----------
''' + sheep_js + '''  function setMascot(img, state, pop) {
    if (!img) return;
    if (img.dataset.state === state) return;
    img.src = SHEEP[state] || SHEEP.idle;
    img.dataset.state = state;
    if (pop) { img.classList.remove('pop'); void img.offsetWidth; img.classList.add('pop'); }
  }
  const TEAM_COLORS = [['#e0523f', '#fdebe6', '#f6c9bd'], ['#2273c9', '#e6f0fb', '#c3d8f1'], ['#1d9e5f', '#e3f6ec', '#b8e2cb'],
    ['#c08a12', '#fbf1da', '#efd9a6'], ['#7b4fb8', '#f1eafa', '#dccbf3'], ['#d4589a', '#fbe8f2', '#f2c2dc']];

  // ---------- 全畫面慶祝彩帶（任何工具都能用；投影模式時畫在投影的元素裡） ----------
  let fxParts = [], fxRaf = 0, fxCanvas = null;
  function screenConfetti(target, count) {
    if (REDUCED_MOTION_ALL) return;
    const host = document.fullscreenElement || document.body;
    if (!fxCanvas || fxCanvas.parentNode !== host) {
      if (fxCanvas) fxCanvas.remove();
      fxCanvas = document.createElement('canvas'); fxCanvas.className = 'fx-canvas'; host.appendChild(fxCanvas);
    }
    fxCanvas.width = window.innerWidth; fxCanvas.height = window.innerHeight;
    const rect = target ? target.getBoundingClientRect() : { left: window.innerWidth / 2, top: window.innerHeight / 3, width: 0, height: 0 };
    const x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
    const colors = ['#e57368', '#f2b53c', '#79c281', '#5f9fe0', '#b784d9', '#ffd166'];
    for (let i = 0; i < (count || 120); i += 1) {
      const angle = Math.random() * Math.PI * 2, speed = 3 + Math.random() * 8;
      fxParts.push({ x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed - 4, life: 70 + Math.random() * 40,
        color: colors[i % colors.length], w: 6 + Math.random() * 6, r: Math.random() * Math.PI, vr: (Math.random() - .5) * .4 });
    }
    if (!fxRaf) fxTick();
  }
  function fxTick() {
    const ctx = fxCanvas.getContext('2d');
    ctx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);
    fxParts = fxParts.filter(p => p.life > 0 && p.y < fxCanvas.height + 40);
    fxParts.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.vy += .25; p.vx *= .99; p.r += p.vr; p.life -= 1;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.globalAlpha = Math.min(1, p.life / 28);
      ctx.fillStyle = p.color; ctx.fillRect(-p.w / 2, -p.w / 2, p.w, p.w * .6); ctx.restore();
    });
    fxRaf = fxParts.length ? requestAnimationFrame(fxTick) : 0;
  }
  const REDUCED_MOTION_ALL = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;''')

# 投影模式按鈕＋分頁切換時讓羊打招呼
rep('''    if (tab.dataset.tool !== 'quiet') stopQuiet();
  }));''', '''    if (tab.dataset.tool !== 'quiet') stopQuiet();
  }));
  // 投影模式：把整個工具面板放到全螢幕（抽籤、檢核、計分、分組、安靜）
  document.querySelectorAll('[data-fs-panel]').forEach(btn => btn.addEventListener('click', () => {
    const panel = document.querySelector(`[data-tool-panel="${btn.dataset.fsPanel}"]`);
    if (document.fullscreenElement) document.exitFullscreen();
    else if (panel && panel.requestFullscreen) panel.requestFullscreen().catch(() => showToast('這個瀏覽器不支援全螢幕。', true));
  }));
  document.addEventListener('fullscreenchange', () => {
    document.querySelectorAll('[data-fs-panel]').forEach(btn => {
      const on = document.fullscreenElement && document.fullscreenElement.dataset && document.fullscreenElement.dataset.toolPanel === btn.dataset.fsPanel;
      btn.textContent = on ? '⛶ 離開投影' : '⛶ 投影模式';
    });
    if (typeof layoutBulbs === 'function') { layoutBulbs(); drawWheel(wheelRotation); }
  });''')

# ---------------------------------------------------------------- JS：抽籤
rep('''  function updateLotStatus() {
    const remaining = remainingPool();
    $('lotStatus').textContent = `剩 ${remaining.length} 個可抽`;
    $('lotDrawnList').innerHTML = day.drawn.length
      ? '已抽出：' + day.drawn.map(v => `<b>${escapeHtml(v)}</b>`).join('、')
      : '還沒抽過，按「🎯 抽！」開始。';
    drawWheel(wheelRotation);''', '''  function renderDrawnChips(animateNewest) {
    $('lotDrawnList').innerHTML = day.drawn.length
      ? '<span>已抽出：</span>' + day.drawn.map((v, i) => `<span class="lot-chip${animateNewest && i === day.drawn.length - 1 ? ' new' : ''}"><i>${i + 1}</i>${escapeHtml(v)}${/^\\d+$/.test(v) ? '號' : ''}</span>`).join('')
      : '還沒抽過，按「🎯 抽！」開始。';
  }
  function updateLotStatus() {
    const remaining = remainingPool();
    $('lotStatus').textContent = `剩 ${remaining.length} 個可抽`;
    renderDrawnChips(false);
    drawWheel(wheelRotation);''')
rep('''    if (lotteryMode === 'wheel') $('lotWheelHub').textContent = isNumber ? picked : '🎉';
    if ($('lotSound').checked) fanfare();
    burstConfetti();
    day.drawn.push(picked);
    saveDay();
    const remaining = remainingPool();
    $('lotStatus').textContent = `剩 ${remaining.length} 個可抽`;
    $('lotDrawnList').innerHTML = '已抽出：' + day.drawn.map(v => `<b>${escapeHtml(v)}</b>`).join('、');''', '''    if (lotteryMode === 'wheel') $('lotWheelHub').textContent = isNumber ? picked : '🎉';
    if ($('lotSound').checked) fanfare();
    burstConfetti();
    lotStage.classList.remove('spinning');
    lotStage.classList.add('revealed');
    setMascot($('lotMascot'), 'sign', true);
    day.drawn.push(picked);
    saveDay();
    const remaining = remainingPool();
    $('lotStatus').textContent = `剩 ${remaining.length} 個可抽`;
    renderDrawnChips(true);''')
rep('''    lotteryBusy = true;
    const result = $('lotResult');
    result.classList.remove('reveal');
    result.innerHTML = '…';''', '''    lotteryBusy = true;
    const result = $('lotResult');
    result.classList.remove('reveal');
    result.innerHTML = '…';
    lotStage.classList.remove('revealed');
    lotStage.classList.add('spinning');
    setMascot($('lotMascot'), 'think', true);''')
rep('''    $('lotWheelHub').textContent = '🎯';
    $('lotGacha').classList.remove('dropped', 'opened');
    updateLotStatus();''', '''    $('lotWheelHub').textContent = '🎯';
    $('lotGacha').classList.remove('dropped', 'opened');
    lotStage.classList.remove('revealed', 'spinning');
    setMascot($('lotMascot'), 'idle', true);
    updateLotStatus();''')
rep('''  // ---- 轉盤：把剩餘座號真的畫在盤面上，指針落點＝抽中的人 ----''', '''  // ---- 跑馬燈燈泡：繞轉盤一圈，轉動時加速 ----
  const lotStage = $('lotteryStage');
  $('lotBulbs').innerHTML = Array.from({ length: 28 }, (_, k) => `<i style="--a:${k * 360 / 28}deg;--k:${k % 3}"></i>`).join('');
  function layoutBulbs() {
    const wrap = document.querySelector('.lot-wheel-wrap');
    if (wrap && wrap.clientWidth) $('lotBulbs').style.setProperty('--r', (wrap.clientWidth / 2 + 10) + 'px');
  }
  window.addEventListener('resize', layoutBulbs);
  setMascot($('lotMascot'), 'idle');

  // ---- 轉盤：把剩餘座號真的畫在盤面上，指針落點＝抽中的人 ----''')

# ---------------------------------------------------------------- JS：檢核板
rep('''  function renderCheckWall() {
    const wall = $('checkWall');
    if (!wall) return;
    wall.innerHTML = day.boards.map((board, index) => {
      const seats = activeSeats();
      const doneCount = seats.filter(seat => board.done[seat]).length;
      const cells = seats.map(seat => {
        const done = !!board.done[seat];
        const miss = board.showMiss && !done;
        return `<button class="check-seat${done ? ' done' : ''}${miss ? ' miss' : ''}" type="button" data-check-board="${index}" data-check-seat="${seat}">${seat}</button>`;
      }).join('');
      return `<div class="check-card">
        <div class="check-head">
          <select data-check-name="${index}">${checkNameOptions(board.name)}</select>''', '''  let checkPopKey = '';
  function renderCheckWall() {
    const wall = $('checkWall');
    if (!wall) return;
    wall.innerHTML = day.boards.map((board, index) => {
      const seats = activeSeats();
      const doneCount = seats.filter(seat => board.done[seat]).length;
      let missIndex = 0;
      const cells = seats.map(seat => {
        const done = !!board.done[seat];
        const miss = board.showMiss && !done;
        const pop = checkPopKey === `${index}-${seat}` ? ' pop' : '';
        return `<button class="check-seat${done ? ' done' : ''}${miss ? ' miss' : ''}${pop}" type="button" data-check-board="${index}" data-check-seat="${seat}"${miss ? ` style="--i:${missIndex++}"` : ''}>${seat}</button>`;
      }).join('');
      const complete = seats.length > 0 && doneCount === seats.length;
      const ratio = seats.length ? doneCount / seats.length : 0;
      return `<div class="check-card${complete ? ' complete' : ''}" data-check-card="${index}">
        <div class="check-head">
          <div class="check-ring" title="已點 ${doneCount}／${seats.length}"><svg viewBox="0 0 54 54"><circle class="bg" cx="27" cy="27" r="22"/><circle class="fg" cx="27" cy="27" r="22" stroke-dasharray="138.2" stroke-dashoffset="${(138.2 * (1 - ratio)).toFixed(1)}"/></svg><b>${Math.round(ratio * 100)}%</b></div>
          <select data-check-name="${index}">${checkNameOptions(board.name)}</select>''')
rep('''          <span class="status-text">已點 ${doneCount}／${seats.length}</span>''',
    '''          ${complete ? '<span class="check-complete">🎉 全部完成！</span>' : `<span class="status-text">已點 ${doneCount}／${seats.length}</span>`}''')
rep('''      const board = day.boards[Number(seatBtn.dataset.checkBoard)];
      const seat = seatBtn.dataset.checkSeat;
      if (board.done[seat]) delete board.done[seat]; else board.done[seat] = true;
      saveDay(); renderCheckWall(); return;''', '''      const boardIndex = Number(seatBtn.dataset.checkBoard);
      const board = day.boards[boardIndex];
      const seat = seatBtn.dataset.checkSeat;
      const seats = activeSeats();
      const wasComplete = seats.every(item => board.done[item]);
      if (board.done[seat]) delete board.done[seat]; else board.done[seat] = true;
      checkPopKey = `${boardIndex}-${seat}`;
      saveDay(); renderCheckWall(); checkPopKey = '';
      if (!wasComplete && seats.every(item => board.done[item])) {
        screenConfetti(document.querySelector(`[data-check-card="${boardIndex}"]`), 100);
        fanfare();
      } else if (board.done[seat]) beep(880, .06, 'sine', .05);
      return;''')

# ---------------------------------------------------------------- JS：計分板
rep('''    wall.innerHTML = Array.from({ length: teamCount() }, (_, i) => {
      const name = config.teamNames[i] || `第 ${i + 1} 組`;
      return `<div class="score-card">
        <span class="score-name" contenteditable="true" data-score-name="${i}" spellcheck="false">${escapeHtml(name)}</span>
        <div class="score-value" id="scoreValue${i}">${config.scores[i] || 0}</div>
        <div class="score-buttons">
          <button class="score-plus" type="button" data-score-delta="1" data-score-team="${i}">＋</button>
          <button class="score-minus" type="button" data-score-delta="-1" data-score-team="${i}">−</button>
        </div>
      </div>`;
    }).join('');
  }''', '''    wall.innerHTML = Array.from({ length: teamCount() }, (_, i) => {
      const name = config.teamNames[i] || `第 ${i + 1} 組`;
      const [team, soft, line] = TEAM_COLORS[i % TEAM_COLORS.length];
      return `<div class="score-card" id="scoreCard${i}" style="--team:${team};--team-soft:${soft};--team-line:${line}">
        <span class="score-crown">👑</span><span class="score-rank" id="scoreRank${i}"></span>
        <span class="score-name" contenteditable="true" data-score-name="${i}" spellcheck="false">${escapeHtml(name)}</span>
        <div class="score-value" id="scoreValue${i}">${config.scores[i] || 0}</div>
        <div class="score-bar"><i id="scoreBar${i}"></i></div>
        <div class="score-buttons">
          <button class="score-plus" type="button" data-score-delta="1" data-score-team="${i}">＋1</button>
          <button class="score-plus5" type="button" data-score-delta="5" data-score-team="${i}">＋5</button>
          <button class="score-minus" type="button" data-score-delta="-1" data-score-team="${i}">−</button>
        </div>
      </div>`;
    }).join('');
    decorateScores();
  }
  // 名次獎牌、領先皇冠、長條比例（同分同名次）
  function decorateScores() {
    const n = teamCount();
    const values = Array.from({ length: n }, (_, i) => config.scores[i] || 0);
    const max = Math.max(0, ...values);
    const ranked = [...new Set(values)].sort((a, b) => b - a);
    values.forEach((value, i) => {
      const card = $(`scoreCard${i}`);
      if (!card) return;
      const rank = ranked.indexOf(value);
      card.classList.toggle('leader', max > 0 && value === max);
      $(`scoreRank${i}`).textContent = max > 0 ? (['🥇', '🥈', '🥉'][rank] || '') : '';
      $(`scoreBar${i}`).style.width = max > 0 ? `${Math.round(value / max * 100)}%` : '0%';
    });
  }
  function animateCount(el, from, to) {
    if (REDUCED_MOTION_ALL || from === to) { el.textContent = to; return; }
    const start = performance.now(), dur = 420;
    const step = now => {
      const t = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(from + (to - from) * e);
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }''')
rep('''    ensureScores();
    config.scores[i] = Math.max(0, (config.scores[i] || 0) + delta);
    saveConfig();
    const value = $(`scoreValue${i}`);
    value.textContent = config.scores[i];
    value.classList.remove('bump'); void value.offsetWidth; value.classList.add('bump');
    if ($('scoreSound').checked) beep(delta > 0 ? 740 : 262, .2, delta > 0 ? 'sine' : 'square');''', '''    ensureScores();
    const before = config.scores[i] || 0;
    config.scores[i] = Math.max(0, before + delta);
    saveConfig();
    const value = $(`scoreValue${i}`);
    animateCount(value, before, config.scores[i]);
    value.classList.remove('bump'); void value.offsetWidth; value.classList.add('bump');
    if (config.scores[i] !== before) {
      const float = document.createElement('span');
      float.className = 'score-float';
      float.textContent = (delta > 0 ? '+' : '') + (config.scores[i] - before);
      $(`scoreCard${i}`).appendChild(float);
      setTimeout(() => float.remove(), 1000);
    }
    const wasLeader = $(`scoreCard${i}`).classList.contains('leader');
    decorateScores();
    if (!wasLeader && $(`scoreCard${i}`).classList.contains('leader') && delta > 0 && $('scoreSound').checked) fanfare();
    else if ($('scoreSound').checked) beep(delta > 0 ? (delta >= 5 ? 988 : 740) : 262, .2, delta > 0 ? 'sine' : 'square');''')

# ---------------------------------------------------------------- JS：分組
rep('''    $('groupWall').innerHTML = groups.map((members, i) =>
      `<div class="group-card" style="animation-delay:${i * 0.13}s">
        <h4>第 ${i + 1} 組（${members.length} 人）</h4>
        <div class="members">${members.map(m => `<span>${escapeHtml(m)}</span>`).join('')}</div>
      </div>`).join('');
    if ($('lotSound').checked) fanfare();
  });''', '''    const wall = $('groupWall');
    const renderGroups = () => {
      let order = 0;
      wall.innerHTML = groups.map((members, i) => {
        const [g, soft, line] = TEAM_COLORS[i % TEAM_COLORS.length];
        return `<div class="group-card" style="animation-delay:${i * 0.06}s;--g:${g};--g-soft:${soft};--g-line:${line}">
          <h4>第 ${i + 1} 組（${members.length} 人）</h4>
          <div class="members">${members.map(m => `<span data-fly="${order++}">${escapeHtml(m)}</span>`).join('')}</div>
        </div>`;
      }).join('');
      if (REDUCED_MOTION_ALL || !wall.animate) { if ($('lotSound').checked) fanfare(); return; }
      // 號碼一顆顆從畫面上方中央飛進各組
      const wallRect = wall.getBoundingClientRect();
      const ox = wallRect.left + wallRect.width / 2, oy = wallRect.top - 30;
      const chips = [...wall.querySelectorAll('[data-fly]')];
      chips.forEach(chip => {
        const r = chip.getBoundingClientRect();
        const k = Number(chip.dataset.fly);
        chip.animate([
          { transform: `translate(${ox - (r.left + r.width / 2)}px, ${oy - (r.top + r.height / 2)}px) scale(.4) rotate(-20deg)`, opacity: 0 },
          { transform: 'none', opacity: 1 }
        ], { duration: 520, delay: 250 + k * 55, easing: 'cubic-bezier(.2,.9,.3,1.25)', fill: 'backwards' });
        if ($('lotSound').checked && k % 2 === 0) setTimeout(() => beep(520 + (k % 8) * 60, .05, 'sine', .05), 250 + k * 55 + 400);
      });
      setTimeout(() => { if ($('lotSound').checked) fanfare(); }, 250 + chips.length * 55 + 450);
    };
    if (REDUCED_MOTION_ALL) { renderGroups(); return; }
    // 先洗牌：全部號碼在池子裡抖動一下
    wall.innerHTML = `<div class="group-pool" style="grid-column:1/-1">${shuffled.map((m, i) => `<span style="--i:${i}">${escapeHtml(m)}</span>`).join('')}</div>`;
    if ($('lotSound').checked) { let c = 0; const t = setInterval(() => { beep(300 + Math.random() * 200, .04, 'square', .04); if (++c > 7) clearInterval(t); }, 90); }
    setTimeout(renderGroups, 800);
  });''')

# ---------------------------------------------------------------- JS：安靜偵測
rep('''  $('quietThreshold').addEventListener('input', () => {
    config.quietThreshold = Number($('quietThreshold').value); saveConfig();
    $('quietThresholdValue').textContent = $('quietThreshold').value;
    $('quietLine').style.left = $('quietThreshold').value + '%';
  });''', '''  $('quietThreshold').addEventListener('input', () => {
    config.quietThreshold = Number($('quietThreshold').value); saveConfig();
    $('quietThresholdValue').textContent = $('quietThreshold').value;
    $('quietLine').style.left = $('quietThreshold').value + '%';
    placeQuietThreshold();
  });
  // 半圓儀表：0～100 對應 -90°～90°；警戒線跟著拉桿
  let quietSmooth = 0;
  function placeQuietThreshold() { $('quietTh').setAttribute('transform', `rotate(${-90 + Number($('quietThreshold').value) * 1.8} 110 115)`); }
  function updateQuietFx(level, threshold) {
    quietSmooth = quietSmooth * .75 + level * .25;
    const v = Math.round(quietSmooth);
    $('quietArc').setAttribute('stroke-dashoffset', String(100 - v));
    $('quietNeedle').setAttribute('transform', `rotate(${-90 + v * 1.8} 110 115)`);
    $('quietLevel').textContent = v;
    const rings = $('quietRings');
    rings.style.setProperty('--lv', (v / 100).toFixed(2));
    const mood = level < threshold - 12 ? 'calm' : level < threshold ? 'warn' : 'loud';
    rings.dataset.mood = mood;
    setMascot($('quietMascot'), mood === 'calm' ? 'sleep' : mood === 'warn' ? 'idle' : 'warning');
  }
  function resetQuietFx() {
    quietSmooth = 0;
    $('quietArc').setAttribute('stroke-dashoffset', '100');
    $('quietNeedle').setAttribute('transform', 'rotate(-90 110 115)');
    $('quietLevel').textContent = '0';
    $('quietRings').dataset.mood = 'off';
    setMascot($('quietMascot'), 'idle');
  }
  // 集到星星時，星星從角色飛進星星盤
  function flyStar() {
    if (REDUCED_MOTION_ALL || !document.body.animate) return;
    const from = $('quietImg').getBoundingClientRect(), to = $('quietStars').getBoundingClientRect();
    const star = document.createElement('span');
    star.className = 'quiet-star-fly'; star.textContent = '⭐';
    (document.fullscreenElement || document.body).appendChild(star);
    const sx = from.left + from.width / 2 - 23, sy = from.top + from.height / 3;
    const ex = to.left + to.width / 2 - 23, ey = to.top;
    star.style.left = '0px'; star.style.top = '0px';
    star.animate([
      { transform: `translate(${sx}px, ${sy}px) scale(.3)`, opacity: 0 },
      { transform: `translate(${(sx + ex) / 2}px, ${Math.min(sy, ey) - 120}px) scale(1.6)`, opacity: 1, offset: .5 },
      { transform: `translate(${ex}px, ${ey}px) scale(1)`, opacity: 1 }
    ], { duration: 950, easing: 'cubic-bezier(.3,.7,.4,1)' }).onfinish = () => star.remove();
  }
  placeQuietThreshold();
  resetQuietFx();''')
rep('''      $('quietBar').style.width = level + '%';
      const threshold = Number($('quietThreshold').value);''', '''      $('quietBar').style.width = level + '%';
      const threshold = Number($('quietThreshold').value);
      updateQuietFx(level, threshold);''')
rep('''          $('quietStars').textContent = '⭐'.repeat(stars);
          if (stars > 0) beep(880, .18, 'sine', .08);''', '''          $('quietStars').textContent = '⭐'.repeat(stars);
          if (stars > 0) { beep(880, .18, 'sine', .08); flyStar(); }''')
rep('''    quietCalmSince = 0; quietStarCount = 0;
    overSince = 0;
  }''', '''    quietCalmSince = 0; quietStarCount = 0;
    overSince = 0;
    if ($('quietArc')) resetQuietFx();
  }''')

# ---------------------------------------------------------------- JS：定評秒數條
rep('''      $('examClock').textContent = now.toLocaleTimeString('zh-TW', { hour12: false });''', '''      $('examClock').textContent = now.toLocaleTimeString('zh-TW', { hour12: false });
      const secBar = $('examSec');
      secBar.style.transition = now.getSeconds() === 0 ? 'none' : '';
      secBar.style.width = `${Math.round(now.getSeconds() / 59 * 100)}%`;''')

# ---------------------------------------------------------------- JS：番茄鐘進度環＋吉祥物＋完成彩帶
rep('''      face.classList.toggle('running', running);
      startBtn.textContent = running ? '⏸ 暫停' : '▶ 開始';
    }''', '''      face.classList.toggle('running', running);
      startBtn.textContent = running ? '⏸ 暫停' : '▶ 開始';
      face.dataset.mode = mode;
      const total = MODES[mode] || remain || 1;
      $('tomatoRing').setAttribute('stroke-dashoffset', String((100 * (1 - Math.min(1, remain / total))).toFixed(2)));
      if (!face.classList.contains('finished')) setMascot($('tomatoMascot'), running ? (mode === 'focus' || mode === 'custom' ? 'focus' : 'stretch') : 'idle');
    }''')
rep('''        face.classList.add('finished');
        chime();''', '''        face.classList.add('finished');
        setMascot($('tomatoMascot'), 'success', true);
        screenConfetti(face, 140);
        chime();''')

# ---------------------------------------------------------------- JS：大屏提示圖磚＋換句轉場
rep('''    function applyPrompt() {
      const custom = $('promptCustomText').value.trim();
      const preset = PROMPTS[Number(select.value)] || PROMPTS[0];
      $('promptMessage').textContent = custom || preset.text;
      $('promptImg').src = 'assets/irasutoya/' + preset.img;
    }
    select.addEventListener('change', () => { $('promptCustomText').value = ''; applyPrompt(); });''', '''    // 分類色：上課秩序綠、作業藍、生活橘、集合紫
    const PROMPT_THEMES = [['#1f7a52', '#e3f3ea', '#bfe3cf', 'linear-gradient(160deg,#e6f6ec,#fff 70%)'],
      ['#2457e6', '#e7edfc', '#c7d4f7', 'linear-gradient(160deg,#e9eefc,#fff 70%)'],
      ['#d0631a', '#fdeee2', '#f6cfb0', 'linear-gradient(160deg,#fff0e4,#fff 70%)'],
      ['#7b4fb8', '#f1eafa', '#dccbf3', 'linear-gradient(160deg,#f3ecfb,#fff 70%)']];
    const promptGroupOf = [];
    PROMPT_GROUPS.forEach((group, g) => group.items.forEach(() => promptGroupOf.push(g)));
    let tileIndex = 0;
    $('promptTiles').innerHTML = PROMPT_GROUPS.map((group, g) => {
      const [c, soft, line] = PROMPT_THEMES[g % PROMPT_THEMES.length];
      return `<div class="prompt-group-row" style="--pg:${c};--pg-soft:${soft};--pg-line:${line}"><b>${group.label}</b>${group.items.map(item =>
        `<button class="prompt-tile" type="button" data-prompt-tile="${tileIndex++}">${escapeHtml(item.text)}</button>`).join('')}</div>`;
    }).join('');
    function swapAnim(el) { el.classList.remove('swap'); void el.offsetWidth; el.classList.add('swap'); }
    function applyPrompt(animate) {
      const custom = $('promptCustomText').value.trim();
      const index = Number(select.value) || 0;
      const preset = PROMPTS[index] || PROMPTS[0];
      $('promptMessage').textContent = custom || preset.text;
      $('promptImg').src = 'assets/irasutoya/' + preset.img;
      $('promptBoard').style.setProperty('--pb', PROMPT_THEMES[promptGroupOf[index] % PROMPT_THEMES.length][3]);
      document.querySelectorAll('[data-prompt-tile]').forEach(tile => tile.classList.toggle('active', !custom && Number(tile.dataset.promptTile) === index));
      if (animate) { swapAnim($('promptMessage')); swapAnim($('promptImg')); }
    }
    $('promptTiles').addEventListener('click', event => {
      const tile = event.target.closest('[data-prompt-tile]');
      if (!tile) return;
      select.value = tile.dataset.promptTile;
      $('promptCustomText').value = '';
      applyPrompt(true);
      beep(660, .08, 'sine', .06);
    });
    select.addEventListener('change', () => { $('promptCustomText').value = ''; applyPrompt(true); });''')
rep('''          $('promptMessage').textContent = prompt.text;
          $('promptImg').src = 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(prompt.img || '')) ? prompt.img : 'class_focus.png');''', '''          $('promptMessage').textContent = prompt.text;
          $('promptImg').src = 'assets/irasutoya/' + (/^[a-z_]+\\.png$/.test(String(prompt.img || '')) ? prompt.img : 'class_focus.png');
          document.querySelectorAll('[data-prompt-tile]').forEach(tile => tile.classList.toggle('active', tile.textContent === prompt.text));
          swapAnim($('promptMessage')); swapAnim($('promptImg'));''')

# 自己打字時不要每個字都播換句動畫
rep("    $('promptCustomText').addEventListener('input', applyPrompt);", "    $('promptCustomText').addEventListener('input', () => applyPrompt(false));")

# 初始渲染：轉盤燈泡位置
rep('''  // 初始渲染
  updateLotStatus();''', '''  // 初始渲染
  layoutBulbs();
  setMascot($('tomatoMascot'), 'idle');
  updateLotStatus();''')

path.write_text(s, encoding='utf-8')
print('ok', len(s))
