"""大屏作業項目整合（老師 2026-11-04「整合一下」，截圖是「我的常用」和各科項目重複）
- 舊的五個預設（習作、試卷、作業本、學習單、其他）不再單獨列，只有老師自己加的才排在最上面
- 學習單、考卷不再每科各一個（版面標題本來就有科目），統一放「通用」；「其他」放通用最後
- 聯絡簿、通知單不是作業，不列通用項目
python tools/merge_homework_items.py
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'HOMEWORK_OLD_DEFAULTS' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# 各科的學習單、考卷拿掉
start = s.index('const HOMEWORK_ITEMS = {')
end = s.index('const HOMEWORK_COMMON = ')
block = re.sub(r"'[^',]*(?:學習單|考卷)', ?", '', s[start:end])
block = re.sub(r", '[^',]*(?:學習單|考卷)'\]", ']', block)
assert '學習單' not in block.replace('樂理學習單', '') and '考卷' not in block, block
block = block.replace("'樂理學習單', ", "'樂理練習', ")
s = s[:start] + block + s[end:]

rep("""    const HOMEWORK_COMMON = ['作業訂正', '考卷訂正', '考卷家長簽名', '小考訂正', '學習單', '預習', '複習', '閱讀紀錄', '親子共讀', '線上學習作業', '小組作業', '假期作業', '補寫作業'];""",
    """    const HOMEWORK_COMMON = ['學習單', '考卷', '作業訂正', '考卷訂正', '考卷家長簽名', '小考訂正', '預習', '複習', '閱讀紀錄', '親子共讀', '線上學習作業', '小組作業', '假期作業', '補寫作業', '其他'];
    const HOMEWORK_NO_COMMON = ['聯絡簿', '通知單'];   // 這兩個不是作業，不列通用項目
    const HOMEWORK_OLD_DEFAULTS = ['習作', '試卷', '作業本', '學習單', '其他'];   // 舊版的預設清單，已併進各科與通用""")
rep("""subjects: [], assignmentTypes: ['習作', '試卷', '作業本', '學習單', '其他'],""", """subjects: [], assignmentTypes: [],""")
rep("""          if (Array.isArray(saved.assignmentTypes) && saved.assignmentTypes.length) s.assignmentTypes = saved.assignmentTypes.map(String);""",
    """          if (Array.isArray(saved.assignmentTypes)) s.assignmentTypes = saved.assignmentTypes.map(String).filter(name => !HOMEWORK_OLD_DEFAULTS.includes(name));""")
rep("""      s.assignmentTypes = types.length ? types : ['習作', '試卷', '作業本', '學習單', '其他'];""", """      s.assignmentTypes = types.filter(name => !HOMEWORK_OLD_DEFAULTS.includes(name));""")
rep("""    // 第二個選單跟著科目換：我的常用 → 這一科 → 各科通用（重複的只留最前面）""", """    // 第二個選單跟著科目換：老師自己加的 → 這一科 → 通用（重複的只留最前面）""")
rep("""        group('我的常用', state.settings.assignmentTypes),
        group(subject || '這一科', HOMEWORK_ITEMS[subject] || []),
        group('各科通用', HOMEWORK_COMMON),""", """        group('我加的', state.settings.assignmentTypes),
        group(subject || '這一科', HOMEWORK_ITEMS[subject] || []),
        group('通用', HOMEWORK_NO_COMMON.includes(subject) ? [] : HOMEWORK_COMMON),""")
rep("""<label>我的常用作業（以、分隔，排在選單最上面）</label><input id="setupAssignmentTypes" placeholder="習作、試卷、作業本、學習單、其他">
            <div class="status-text" style="margin-top:4px">各科的詳細項目已經內建（國語的甲乙本、圈詞、數學的數習、數練⋯），選了科目就會出現；這裡只放你最常用的。</div></div>""",
    """<label>自己加的作業項目（以、分隔，可留空）</label><input id="setupAssignmentTypes" placeholder="例：小日記、晨讀單">
            <div class="status-text" style="margin-top:4px">各科項目已經內建（國語的甲乙本、圈詞，數學的數習、數練⋯），選了科目就會出現；內建沒有的才加在這裡，會排在選單最上面。</div></div>""")

path.write_text(s, encoding='utf-8')
print('ok')
