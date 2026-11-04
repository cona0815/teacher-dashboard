"""作業項目可在設定自己選（老師 2026-11-04「預設出現常用的，自己勾選哪些要增加」）
- 設定頁新增「作業項目」：每科一列，點亮＝出現在作業繳交的選單，跟科目管理同一種操作
- 預設只亮常用的；內建沒有的可以按「＋ 新增」，自己加的可以刪；「恢復常用」回到預設
- 原本的欄位改成「每一科都要出現的項目」
python tools/add_homework_picker.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'homeworkPicks' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 預設亮哪些 ----------
rep("""    const HOMEWORK_NO_COMMON = ['聯絡簿', '通知單'];""", """    // 預設只亮常用的，其他到設定頁點亮
    const HOMEWORK_COMMON_GROUP = '通用';
    const HOMEWORK_DEFAULT_ON = {
      '國語': ['習作（國習）', '作業簿（國作）', '生字簿（甲本）', '語詞簿（乙本）', '圈詞', '造句', '朗讀課文', '閱讀心得', '作文', '日記'],
      '數學': ['習作（數習）', '課本（數課）', '練習本（數練）', '計算練習', '應用題'],
      '英語': ['習作', '作業本', '單字抄寫', '背單字', '課文朗讀'],
      '自然': ['習作', '觀察紀錄', '實驗紀錄', '查資料'],
      '社會': ['習作', '重點整理', '查資料'],
      '生活': ['習作', '觀察紀錄', '美勞作品'],
      '健康與體育': ['健康習作', '運動紀錄'],
      '音樂': ['直笛練習', '歌曲練習'],
      '視覺藝術': ['美勞作品', '帶美術用具'],
      '綜合': ['家事紀錄', '活動省思單'],
      '本土語': ['課文朗讀', '語詞練習'],
      '聯絡簿': ['聯絡簿抄寫', '家長簽名'],
      '通知單': ['回條', '家長同意書'],
      [HOMEWORK_COMMON_GROUP]: ['學習單', '考卷', '作業訂正', '考卷訂正', '其他']
    };
    const HOMEWORK_NO_COMMON = ['聯絡簿', '通知單'];""")

# ---------- 設定值 ----------
rep("""subjects: [], assignmentTypes: [],""", """subjects: [], assignmentTypes: [], homeworkPicks: {}, homeworkExtra: {},""")
rep("""          if (Array.isArray(saved.assignmentTypes)) s.assignmentTypes = saved.assignmentTypes.map(String).filter(name => !HOMEWORK_OLD_DEFAULTS.includes(name));""",
    """          if (Array.isArray(saved.assignmentTypes)) s.assignmentTypes = saved.assignmentTypes.map(String).filter(name => !HOMEWORK_OLD_DEFAULTS.includes(name));
          // homeworkPicks：這一科點亮了哪些（沒動過的科目不存，用預設）；homeworkExtra：老師自己加的項目
          const nameLists = value => Object.fromEntries(Object.entries(value && typeof value === 'object' ? value : {})
            .filter(([, list]) => Array.isArray(list)).map(([key, list]) => [key, list.map(String)]));
          s.homeworkPicks = nameLists(saved.homeworkPicks);
          s.homeworkExtra = nameLists(saved.homeworkExtra);""")

# ---------- 設定頁 ----------
rep("""<label>自己加的作業項目（以、分隔，可留空）</label><input id="setupAssignmentTypes" placeholder="例：小日記、晨讀單">
            <div class="status-text" style="margin-top:4px">各科項目已經內建（國語的甲乙本、圈詞，數學的數習、數練⋯），選了科目就會出現；內建沒有的才加在這裡，會排在選單最上面。</div></div>""",
    """<label>每一科都要出現的作業（以、分隔，可留空）</label><input id="setupAssignmentTypes" placeholder="例：小日記、晨讀單">
            <div class="status-text" style="margin-top:4px">只放每一科都用得到的。各科各自的項目，在下面的「作業項目」選。</div></div>""")
rep("""              <button class="ghost-button" type="button" id="addSubjectButton">＋ 新增科目</button>
            </div>
          </div>""", """              <button class="ghost-button" type="button" id="addSubjectButton">＋ 新增科目</button>
            </div>
          </div>
          <div class="field" style="grid-column:1/-1">
            <label>作業項目（點亮＝出現在作業繳交的選單；預設只亮常用的，要用的再點亮）</label>
            <div id="homeworkManager"></div>
            <button class="ghost-button" type="button" id="homeworkResetButton" style="margin-top:8px">↺ 恢復常用</button>
          </div>""")
rep("""    .subject-toggle.on { background: var(--primary); border-color: var(--primary); color: #fff; }""",
    """    .subject-toggle.on { background: var(--primary); border-color: var(--primary); color: #fff; }
    .hw-row { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid var(--line); }
    .hw-row-name { flex: 0 0 88px; font-weight: 900; padding-top: 6px; }
    .hw-row .subject-manager { margin-top: 0; flex: 1; gap: 6px; }
    .hw-row .subject-toggle { font-size: 14px; padding: 4px 11px; user-select: none; }
    .hw-row .hw-add { border-style: dashed; color: var(--muted); }
    .hw-row .hw-del { margin-left: 2px; font-weight: 900; opacity: .75; }""")

# ---------- 程式 ----------
rep("""    function renderSubjectManager() {
      $('subjectManager').innerHTML = state.settings.subjects.map((item, index) =>
        `<span class="subject-toggle${item.enabled ? ' on' : ''}" data-subject-index="${index}">${escapeHtml(item.name)}${item.enabled ? ' ✓' : ''}</span>`).join('');
    }""", """    function renderSubjectManager() {
      $('subjectManager').innerHTML = state.settings.subjects.map((item, index) =>
        `<span class="subject-toggle${item.enabled ? ' on' : ''}" data-subject-index="${index}">${escapeHtml(item.name)}${item.enabled ? ' ✓' : ''}</span>`).join('');
      renderHomeworkManager();
    }
    // 作業項目：一科一列，點亮＝出現在作業繳交的選單
    const homeworkExtra = group => state.settings.homeworkExtra[group] || [];
    const homeworkAll = group => [...new Set([...(group === HOMEWORK_COMMON_GROUP ? HOMEWORK_COMMON : HOMEWORK_ITEMS[group] || []), ...homeworkExtra(group)])];
    function homeworkOn(group) {
      const picks = state.settings.homeworkPicks[group];
      const on = picks || [...(HOMEWORK_DEFAULT_ON[group] || []), ...homeworkExtra(group)];
      return homeworkAll(group).filter(name => on.includes(name));
    }
    function renderHomeworkManager() {
      const groups = [...enabledSubjects(), HOMEWORK_COMMON_GROUP];
      $('homeworkManager').innerHTML = groups.map(group => {
        const on = homeworkOn(group), extra = homeworkExtra(group);
        const chips = homeworkAll(group).map(name => {
          const lit = on.includes(name);
          return `<span class="subject-toggle${lit ? ' on' : ''}" data-hw-group="${escapeHtml(group)}" data-hw-name="${escapeHtml(name)}">${escapeHtml(name)}${lit ? ' ✓' : ''}${extra.includes(name) ? '<span class="hw-del" data-hw-del title="刪除這個項目"> ✕</span>' : ''}</span>`;
        }).join('');
        return `<div class="hw-row"><div class="hw-row-name">${escapeHtml(group)}</div><div class="subject-manager">${chips}<span class="subject-toggle hw-add" data-hw-add="${escapeHtml(group)}">＋ 新增</span></div></div>`;
      }).join('');
    }
    function homeworkChanged() {
      saveSettings();
      renderHomeworkManager();
      renderAssignmentOptions();
    }""")
rep("""        group(subject || '這一科', HOMEWORK_ITEMS[subject] || []),
        group('通用', HOMEWORK_NO_COMMON.includes(subject) ? [] : HOMEWORK_COMMON),""", """        group(subject || '這一科', subject ? homeworkOn(subject) : []),
        group(HOMEWORK_COMMON_GROUP, HOMEWORK_NO_COMMON.includes(subject) ? [] : homeworkOn(HOMEWORK_COMMON_GROUP)),""")
rep("""        group('我加的', state.settings.assignmentTypes),""", """        group('每科都有', state.settings.assignmentTypes),""")
rep("""    $('addSubjectButton').addEventListener('click', () => {""", """    $('homeworkManager').addEventListener('click', async event => {
      const s = state.settings;
      const addButton = event.target.closest('[data-hw-add]');
      if (addButton) {
        const group = addButton.dataset.hwAdd;
        const typed = await askDialog({ message: `「${group}」要新增什麼作業項目？`, input: true });
        const name = String(typed || '').trim().slice(0, 10);
        if (!name) return;
        if (homeworkAll(group).includes(name)) {
          if (!homeworkOn(group).includes(name)) s.homeworkPicks[group] = [...homeworkOn(group), name];
        } else {
          const on = homeworkOn(group);
          s.homeworkExtra[group] = [...homeworkExtra(group), name];
          s.homeworkPicks[group] = [...on, name];
        }
        homeworkChanged();
        return;
      }
      const chip = event.target.closest('[data-hw-name]');
      if (!chip) return;
      const group = chip.dataset.hwGroup, name = chip.dataset.hwName;
      if (event.target.closest('[data-hw-del]')) {
        const on = homeworkOn(group);
        s.homeworkExtra[group] = homeworkExtra(group).filter(item => item !== name);
        s.homeworkPicks[group] = on.filter(item => item !== name);
      } else {
        const on = homeworkOn(group);
        s.homeworkPicks[group] = on.includes(name) ? on.filter(item => item !== name) : [...on, name];
      }
      homeworkChanged();
    });
    $('homeworkResetButton').addEventListener('click', async () => {
      if (!(await askDialog({ message: '把各科的作業項目恢復成預設的常用項目？\\n自己新增的項目會保留。' }))) return;
      state.settings.homeworkPicks = {};
      homeworkChanged();
    });
    $('addSubjectButton').addEventListener('click', () => {""")

path.write_text(s, encoding='utf-8')
print('ok')
