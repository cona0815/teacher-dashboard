"""大屏作業項目內建到各科（老師 2026-11-04「作業項目，幫我去網路，把項目愈詳細愈好」）
參考公開的國小班級聯絡簿與班級經營計畫（國習、國作、甲乙本、圈詞、數課、數習、數練、訂正、日記、閱讀……）再依教學現場補齊。
- 選了科目，第二個選單只出現「我的常用」「這一科」「各科通用」，不會一長串
- 設定頁的清單變成「我的常用」，排在最上面；舊的設定不受影響，上限放寬到 30 個
python tools/add_homework_items.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'HOMEWORK_ITEMS' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""    const DEFAULT_ENABLED = ['國語', '數學', '英語', '自然', '社會', '聯絡簿', '通知單'];""",
    """    const DEFAULT_ENABLED = ['國語', '數學', '英語', '自然', '社會', '聯絡簿', '通知單'];
    // 各科內建的作業項目（版面名稱上限 20 字，要留給補充的頁數，所以每項都短）
    const HOMEWORK_ITEMS = {
      '國語': ['習作（國習）', '作業簿（國作）', '生字簿（甲本）', '語詞簿（乙本）', '生字練習', '圈詞', '語詞解釋', '造句', '照樣造句', '成語', '四字語詞', '修辭練習', '查字典', '注音練習', '聽寫', '朗讀課文', '背誦', '預習單', '課文大意', '閱讀測驗', '閱讀心得', '看圖寫話', '短文寫作', '作文', '作文草稿', '日記', '週記', '國語考卷'],
      '數學': ['習作（數習）', '課本（數課）', '練習本（數練）', '計算練習', '直式計算', '九九乘法', '心算練習', '應用題', '重點整理', '數學學習單', '數學考卷'],
      '英語': ['習作', '作業本', '字母書寫', '單字抄寫', '背單字', '自然發音', '句型練習', '對話練習', '課文朗讀', '跟讀音檔', '聽力練習', '口說錄音', '英語學習單', '單字小考', '英語考卷'],
      '自然': ['習作', '自然學習單', '實驗紀錄', '觀察紀錄', '種植紀錄', '天氣紀錄', '查資料', '重點整理', '帶實驗材料', '自然考卷'],
      '社會': ['習作', '社會學習單', '重點整理', '查資料', '地圖練習', '訪問家人', '社區踏查', '時事剪報', '小組報告', '社會考卷'],
      '生活': ['習作', '生活學習單', '觀察紀錄', '種植紀錄', '家事紀錄', '美勞作品', '唱遊練習', '帶材料'],
      '健康與體育': ['健康習作', '健康學習單', '運動紀錄', '跳繩練習', '潔牙紀錄', '視力保健紀錄', '飲食紀錄', '健康檢查單'],
      '音樂': ['直笛練習', '歌曲練習', '節奏練習', '樂理學習單', '音樂欣賞單', '帶直笛'],
      '視覺藝術': ['美勞作品', '素描練習', '藝術學習單', '帶美術用具', '帶材料'],
      '綜合': ['綜合學習單', '家事紀錄', '服務學習紀錄', '活動省思單', '小組報告', '活動企劃'],
      '本土語': ['課文朗讀', '語詞練習', '本土語學習單', '錄音作業', '認證練習'],
      '聯絡簿': ['聯絡簿抄寫', '家長簽名', '聯絡簿訂正'],
      '通知單': ['回條', '家長同意書', '調查表', '報名表', '繳費單', '健康資料表']
    };
    const HOMEWORK_COMMON = ['作業訂正', '考卷訂正', '考卷家長簽名', '小考訂正', '學習單', '預習', '複習', '閱讀紀錄', '親子共讀', '線上學習作業', '小組作業', '假期作業', '補寫作業'];""")

rep("""      $('boardAssignmentSelect').innerHTML = [
        ...state.settings.assignmentTypes.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`),
        '<option value="__custom__">✏️ 自行輸入…</option>'
      ].join('');
    }""", """      renderAssignmentOptions();
    }
    // 第二個選單跟著科目換：我的常用 → 這一科 → 各科通用（重複的只留最前面）
    function renderAssignmentOptions() {
      const select = $('boardAssignmentSelect');
      const before = select.value;
      const subject = $('boardSubjectSelect').value;
      const seen = new Set();
      const group = (label, items) => {
        const list = items.filter(name => !seen.has(name) && seen.add(name));
        return list.length ? `<optgroup label="${escapeHtml(label)}">${list.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('')}</optgroup>` : '';
      };
      select.innerHTML = [
        group('我的常用', state.settings.assignmentTypes),
        group(subject || '這一科', HOMEWORK_ITEMS[subject] || []),
        group('各科通用', HOMEWORK_COMMON),
        '<option value="__custom__">✏️ 自行輸入…</option>'
      ].join('');
      if (before && [...select.options].some(option => option.value === before)) select.value = before;
    }""")
rep("""    $('addBoardButton').addEventListener('click', addBoard);""", """    $('addBoardButton').addEventListener('click', addBoard);
    $('boardSubjectSelect').addEventListener('change', renderAssignmentOptions);""")
rep("""<label>作業名稱選單（以、分隔，可自訂）</label><input id="setupAssignmentTypes" placeholder="習作、試卷、作業本、學習單、其他"></div>""",
    """<label>我的常用作業（以、分隔，排在選單最上面）</label><input id="setupAssignmentTypes" placeholder="習作、試卷、作業本、學習單、其他">
            <div class="status-text" style="margin-top:4px">各科的詳細項目已經內建（國語的甲乙本、圈詞、數學的數習、數練⋯），選了科目就會出現；這裡只放你最常用的。</div></div>""")
rep("""map(value => value.trim()).filter(Boolean).slice(0, 12);""", """map(value => value.trim()).filter(Boolean).slice(0, 30);""")

path.write_text(s, encoding='utf-8')
print('ok')
