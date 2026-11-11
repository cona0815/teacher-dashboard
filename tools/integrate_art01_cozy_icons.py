"""ART-01 R4（Codex 交件、Claude 2026-11-02 驗收）：可愛溫暖風介面圖示 35 張＋安靜偵測 4 張整合
- 轉 WebP：圖示 256×256 → assets/art/cozy/icon/，安靜偵測 800×800 → assets/art/cozy/quiet/
- 大屏：COZY_ICON_READY 填入 16 個 id；安靜偵測在可愛溫暖風改用原創學生插圖與對應文字
- 工作台：圖示加 data-cozy-icon，選「可愛溫暖風」配色時換圖，換回其他配色恢復原圖
python tools/integrate_art01_cozy_icons.py <交件_R4 資料夾> [--convert-only 只重新轉檔]
"""
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1])

MORNING_IDS = ['tab_rollcall', 'tab_homework', 'tab_makeup', 'tab_correct', 'tab_query', 'tab_tools', 'tab_setup', 'contact_book',
               'tool_lottery', 'tool_check', 'tool_score', 'tool_group', 'tool_quiet', 'tool_exam', 'tool_tomato', 'tool_prompt']
INDEX_IDS = ['sum_todo', 'sum_weekly', 'sum_waiting', 'sum_duetoday', 'sum_overdue', 'sum_done', 'sum_urgent',
             'panel_toolbox', 'panel_progress', 'panel_ai', 'panel_line_inbox', 'panel_message_hub', 'panel_filter', 'panel_tasks',
             'role_grade_lead', 'role_admin', 'role_homeroom', 'role_subject', 'role_teacher']
QUIET_IDS = ['quiet_super', 'quiet_good', 'quiet_warn', 'quiet_loud']

# ---------- 轉檔 ----------
for ids, folder, size in [(MORNING_IDS + INDEX_IDS, 'icon', 256), (QUIET_IDS, 'quiet', 800)]:
    out = root / 'assets' / 'art' / 'cozy' / folder
    out.mkdir(parents=True, exist_ok=True)
    for i in ids:
        im = Image.open(src / f'{i}.png').convert('RGBA')
        if folder == 'icon':
            # 原圖四周留 15～25% 透明邊，縮到 22px 會太小：裁成貼齊物件的正方形（留 4% 邊）
            l, t, r, b = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
            side = int(max(r - l, b - t) * 1.08)
            cx, cy = (l + r) // 2, (t + b) // 2
            canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
            canvas.paste(im.crop((cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)), (0, 0))
            im = canvas
        im = im.resize((size, size), Image.LANCZOS)
        im.save(out / f'{i}.webp', 'WEBP', quality=88, alpha_quality=92, method=6)


def patch(name, pairs):
    path = root / name
    s = path.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, s.count(old), old[:90])
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')
    return s


if '--convert-only' in sys.argv:
    sys.exit(print('converted') or 0)

# ---------- 大屏 ----------
patch('Morning.html', [
    ("""    const COZY_ICON_READY = new Set([]);""",
     """    const COZY_ICON_READY = new Set([""" + ', '.join(f"'{i}'" for i in MORNING_IDS) + """]);"""),
    ("""      const setCharacter = (src, cls) => {
        if (!img.src.endsWith(src)) img.src = 'assets/irasutoya/' + src;
        img.className = 'quiet-img ' + cls;
      };
      if (level < threshold - 25) { setCharacter('quiet_usagi.png', 'is-calm'); face.textContent = '😊 超安靜！兔兔為你們驕傲'; }
      else if (level < threshold - 12) { setCharacter('quiet_cat.png', 'is-calm'); face.textContent = '🐱 噓——保持這個音量'; }
      else if (level < threshold) { setCharacter('quiet_kuma.png', 'is-warn'); face.textContent = '🐻 有點聲音囉，小心！'; }
      else { setCharacter('too_noisy.png', 'is-loud'); face.textContent = '😫 太吵了！教室要翻掉啦！'; }""",
     """      // 可愛溫暖風改用原創學生插圖（assets/art/cozy/quiet/）；標準維持いらすとや動物
      const cozy = state.settings.boardStyle === 'cozy';
      const setCharacter = (src, cozyId, cls) => {
        const want = cozy ? 'assets/art/cozy/quiet/' + cozyId + '.webp' : 'assets/irasutoya/' + src;
        if (img.getAttribute('src') !== want) img.src = want;
        img.className = 'quiet-img ' + cls;
      };
      if (level < threshold - 25) { setCharacter('quiet_usagi.png', 'quiet_super', 'is-calm'); face.textContent = cozy ? '😊 超安靜！大家好棒' : '😊 超安靜！兔兔為你們驕傲'; }
      else if (level < threshold - 12) { setCharacter('quiet_cat.png', 'quiet_good', 'is-calm'); face.textContent = cozy ? '🤫 噓——保持這個音量' : '🐱 噓——保持這個音量'; }
      else if (level < threshold) { setCharacter('quiet_kuma.png', 'quiet_warn', 'is-warn'); face.textContent = cozy ? '😟 有點聲音囉，小心！' : '🐻 有點聲音囉，小心！'; }
      else { setCharacter('too_noisy.png', 'quiet_loud', 'is-loud'); face.textContent = '😫 太吵了！教室要翻掉啦！'; }"""),
    ("""          <div class="status-text" style="text-align:center;display:block">安靜就換可愛動物站崗、""",
     """          <div class="status-text" id="quietCredit" style="text-align:center;display:block">安靜就換可愛動物站崗、"""),
    ("""  $('quietStartButton').addEventListener('click', () => { quietStream ? stopQuiet() : startQuiet(); });""",
     """  $('quietStartButton').addEventListener('click', () => { quietStream ? stopQuiet() : startQuiet(); });
  // 可愛溫暖風的安靜偵測是原創插圖，說明與出處跟著換
  const quietCreditHtml = $('quietCredit').innerHTML;
  function updateQuietCredit() {
    $('quietCredit').innerHTML = state.settings.boardStyle === 'cozy'
      ? '安靜就換同學比「噓」、太吵會換成摀耳朵的同學；連續安靜 30 秒集一顆 ⭐。插圖：本系統原創'
      : quietCreditHtml;
  }
  updateQuietCredit();
  document.addEventListener('boardstylechange', updateQuietCredit);"""),
])

# ---------- 工作台 ----------
INDEX_TAGS = [
    ('<img class="summary-icon" src="assets/ipas/abacus-todo.webp"', 'sum_todo'),
    ('<img class="summary-icon" src="assets/ipas/star-weekly.webp"', 'sum_weekly'),
    ('<img class="summary-icon" src="assets/ipas/hourglass-waiting.webp"', 'sum_waiting'),
    ('<img class="summary-icon" src="assets/ipas/clock-duetoday.webp"', 'sum_duetoday'),
    ('<img class="summary-icon" src="assets/ipas/bell-overdue.webp"', 'sum_overdue'),
    ('<img class="summary-icon" src="assets/ipas/rocket-done.webp"', 'sum_done'),
    ('data-role="gradeLead" aria-pressed="true"><img src=', 'role_grade_lead'),
    ('data-role="admin" aria-pressed="false"><img src=', 'role_admin'),
    ('data-role="homeroom" aria-pressed="true"><img src=', 'role_homeroom'),
    ('data-role="subject" aria-pressed="false"><img src=', 'role_subject'),
    ('data-role="teacher" aria-pressed="true"><img src=', 'role_teacher'),
    ("""          <img src="assets/ipas/owl-toolbox.webp" alt="">""", 'panel_toolbox'),
    ("""          <img src="assets/ipas/compass-progress.webp" alt="">""", 'panel_progress'),
    ("""          <img src="assets/ipas/robot-ai.webp" alt="AI 行政助理">""", 'panel_ai'),
    ("""          <img src="assets/ipas/book-contact.webp" alt="">""", 'contact_book'),
    ("""<img class="title-icon" src="assets/ipas/owl-filter.webp" alt="">""", 'panel_filter'),
    ("""<img class="title-icon" src="assets/ipas/pencil-tasks.webp" alt="">""", 'panel_tasks'),
]
pairs = [(old, old.replace('<img ', f'<img data-cozy-icon="{cid}" ', 1)) for old, cid in INDEX_TAGS]
# LINE 收件匣與訊息整合站共用同一張郵箱圖，靠後面的標題分辨
pairs += [
    ("""          <img src="assets/ipas/mailbox-line.webp" alt="">
          <div>
            <h2 id="lineInbox""", """          <img data-cozy-icon="panel_line_inbox" src="assets/ipas/mailbox-line.webp" alt="">
          <div>
            <h2 id="lineInbox"""),
    ("""          <img src="assets/ipas/mailbox-line.webp" alt="">
          <div>
            <h2 id="messageHubTitle">""", """          <img data-cozy-icon="panel_message_hub" src="assets/ipas/mailbox-line.webp" alt="">
          <div>
            <h2 id="messageHubTitle">"""),
    ("""      document.querySelectorAll('[data-theme-choice]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.themeChoice === safeTheme));
      });
    }""", """      document.querySelectorAll('[data-theme-choice]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.themeChoice === safeTheme));
      });
      // 可愛溫暖風換成原創圖示（assets/art/cozy/icon/），其他配色用原圖
      document.querySelectorAll('img[data-cozy-icon]').forEach(img => {
        if (!img.dataset.origSrc) img.dataset.origSrc = img.getAttribute('src');
        const want = safeTheme === 'cozy' ? 'assets/art/cozy/icon/' + img.dataset.cozyIcon + '.webp' : img.dataset.origSrc;
        if (img.getAttribute('src') !== want) img.src = want;
      });
    }"""),
    ("""    :root[data-theme="cozy"] .input, :root[data-theme="cozy"] .select, :root[data-theme="cozy"] .textarea {""",
     """    /* 可愛溫暖風圖示本身就有白貼紙邊與顏色：不再套灰階與底色；身分沒選的維持淡灰 */
    :root[data-theme="cozy"] .summary-icon { width: 40px; height: 40px; padding: 0; background: transparent; filter: none; opacity: 1; }
    :root[data-theme="cozy"] .title-icon { padding: 2px; background: var(--cozy-paper); border-color: var(--cozy-wood); }
    :root[data-theme="cozy"] .role-person img { width: 32px; height: 32px; padding: 0; background: transparent; filter: grayscale(.85); opacity: .7; }
    :root[data-theme="cozy"] .role-person[aria-pressed="true"] img { filter: none; opacity: 1; }
    :root[data-theme="cozy"] .input, :root[data-theme="cozy"] .select, :root[data-theme="cozy"] .textarea {"""),
]
patch('Index.html', pairs)
print('ok')
