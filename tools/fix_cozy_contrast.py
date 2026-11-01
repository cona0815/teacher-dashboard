"""可愛動森風修正（2026-11-02 測試找到）
1. 白字放在草綠／天空藍上對比只有 2.3（投影看不清）→ 按鈕用的綠、藍調深到 4.3 以上，文字綠也調深
2. 動森風的按鈕底色規則蓋掉了「已選取／危險／建議」的樣式：
   工作台：記事篩選「全部」變白底白字、身分選取看不出來、刪除鈕失去紅底、AI 建議鈕失去金框
   大屏：已完成的作業版面失去綠底
python tools/fix_cozy_contrast.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def patch(name, pairs):
    path = root / name
    s = path.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (name, s.count(old), old[:80])
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')


patch('Index.html', [
    ("""      --primary: #4f9e45;
      --primary-strong: #3c7f35;
      --primary-soft: #eaf5dc;
      --accent: #3f9bd0;""",
     """      --primary: #3c7f35;
      --primary-strong: #2f6a2a;
      --primary-soft: #eaf5dc;
      --accent: #2a7fb3;"""),
    ("""      --success: #4f9e45;""", """      --success: #3c7f35;"""),
    # 白字底色：對比 4.3 以上
    ("""--cozy-leaf: #6cbf5b; --cozy-leaf-deep: #4f9e45; --cozy-sky: #5ab4e5; --cozy-sky-deep: #3f9bd0; --cozy-paper: #fffdf6;""",
     """--cozy-leaf: #3f8a37; --cozy-leaf-deep: #2f6a2a; --cozy-sky: #2a7fb3; --cozy-sky-deep: #1f6491; --cozy-paper: #fffdf6;"""),
    ("""    :root[data-theme="cozy"] .input, :root[data-theme="cozy"] .select, :root[data-theme="cozy"] .textarea {""",
     """    /* 上面的通用按鈕規則權重較高，選取／危險／建議狀態要再寫一次，不然會被蓋成一般按鈕 */
    :root[data-theme="cozy"] .note-filter-chip.active { border-color: var(--primary); background: var(--primary); color: #fff; box-shadow: 0 3px 0 var(--primary-strong); }
    :root[data-theme="cozy"] .role-person[aria-pressed="true"] { border-color: var(--primary); background: var(--primary-soft); color: var(--primary-strong); box-shadow: 0 3px 0 #b9d99a; }
    :root[data-theme="cozy"] .mini-button-danger, :root[data-theme="cozy"] .progress-course-picker .course-delete-button { border-color: #e8bcb0; background: #fff8f5; color: var(--danger); box-shadow: 0 3px 0 #e8bcb0; }
    :root[data-theme="cozy"] .mini-button.is-suggested { border-color: #b9852f; box-shadow: 0 0 0 2px #fff3d6 inset, 0 3px 0 #b9852f; font-weight: 900; }
    :root[data-theme="cozy"] .input, :root[data-theme="cozy"] .select, :root[data-theme="cozy"] .textarea {"""),
])

patch('Morning.html', [
    ("""      --primary: #4f9e45; --primary-strong: #3c7f35;
      --ok: #4fae5b; --ok-soft: #eaf5dc;""",
     """      --primary: #3c7f35; --primary-strong: #2f6a2a;
      --ok: #3d8f47; --ok-soft: #eaf5dc;"""),
    ("""--cozy-leaf: #6cbf5b; --cozy-leaf-deep: #4f9e45;
      --cozy-sky: #5ab4e5; --cozy-sky-deep: #3f9bd0;""",
     """--cozy-leaf: #3f8a37; --cozy-leaf-deep: #2f6a2a;
      --cozy-sky: #2a7fb3; --cozy-sky-deep: #1f6491;"""),
    ("""    html[data-board-style="cozy"] .board-card { background: var(--cozy-paper); border: 3px solid var(--line); border-radius: 22px; }""",
     """    html[data-board-style="cozy"] .board-card { background: var(--cozy-paper); border: 3px solid var(--line); border-radius: 22px; }
    html[data-board-style="cozy"] .board-card.board-settled { background: var(--ok-soft); }   /* 已完成的版面保留綠底 */"""),
])
print('ok')
