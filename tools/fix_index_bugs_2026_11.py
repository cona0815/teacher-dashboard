"""工作台 bug 修正（2026-11-01 全面掃描）：
#2 本機模式新任務 ID 用「現有最大編號＋1」（備份還原後不再撞號、改到別的任務）
#8 聯絡本切日期讀取失敗：清空編輯區並鎖住儲存（不會把前一天的內容存到新日期）
#9 「複製最近一筆」只取比目前日期早的那一筆（不會抓到未來預排或自己）
#15 新增、編輯、封存任務後保留篩選條件
python tools/fix_index_bugs_2026_11.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Index.html'
s = path.read_text(encoding='utf-8')
assert 'nextPreviewTaskId' not in s, '已套用過'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''            savedTask = { ...payload, taskId: `T-${String(previewTasks.length + 1).padStart(3, '0')}` };''', '''            savedTask = { ...payload, taskId: nextPreviewTaskId(previewTasks) };''')
rep('''      const api = {
        getBootstrapData: () => ({''', '''      // 新編號＝現有最大編號＋1（備份還原時已封存的不在清單裡，用「筆數＋1」會撞號）
      const nextPreviewTaskId = tasks => {
        const max = tasks.reduce((m, t) => Math.max(m, Number(String(t.taskId || '').replace(/^T-/, '')) || 0), 0);
        return `T-${String(max + 1).padStart(3, '0')}`;
      };
      const api = {
        getBootstrapData: () => ({''')
# 函式本體放在 previewResult 外層可呼叫的位置：直接定義成全域函式


# #8
rep('''      } catch (error) {
        renderContactVisual();
        $('contactBookMeta').textContent = `讀取失敗：${error.message}`;
      }
    }''', '''        $('contactBookSaveButton').disabled = false;
      } catch (error) {
        // 讀不到這一天：清空並鎖住儲存，避免把前一天的內容存到這一天
        $('contactBookInput').value = '';
        renderContactVisual();
        $('contactBookSaveButton').disabled = true;
        $('contactBookMeta').textContent = `讀取失敗：${error.message}（為了避免蓋掉資料，暫時不能儲存；請重新整理或換日期再試）`;
      }
    }''')
rep('''      $('contactBookMeta').textContent = '讀取中……';
      try {
        const result = await callLineBridge('contactbook_get', { date });''', '''      $('contactBookMeta').textContent = '讀取中……';
      $('contactBookSaveButton').disabled = true;
      try {
        const result = await callLineBridge('contactbook_get', { date });''')

# #9
rep('''      const target = contactBookHistory.find(entry => !entry.empty);''', '''      const current = $('contactBookDate').value;
      // 清單是新到舊、含未來預排：只取比目前編輯日期早的最近一筆
      const target = contactBookHistory.filter(entry => !entry.empty && entry.date < current).sort((a, b) => (a.date < b.date ? 1 : -1))[0];''')

# #15
rep('''        state.tasks = result.tasks || [];
        state.filteredTasks = [...state.tasks];
        renderSummary(result.summary || {});
        renderTasks();
        closeTaskModal();''', '''        state.tasks = result.tasks || [];
        renderSummary(result.summary || {});
        applyFilters();   // 保留目前的篩選條件
        closeTaskModal();''')
rep('''        state.tasks = result.tasks || [];
        state.filteredTasks = [...state.tasks];
        renderSummary(result.summary || {});
        renderTasks();
        if ($('taskModal').classList.contains('open')) closeTaskModal();''', '''        state.tasks = result.tasks || [];
        renderSummary(result.summary || {});
        applyFilters();   // 保留目前的篩選條件
        if ($('taskModal').classList.contains('open')) closeTaskModal();''')
rep('''          state.tasks = result.tasks || [];
          state.filteredTasks = [...state.tasks];
          renderSummary(result.summary || {});
          renderTasks();
          appendDeskpetDiary(''', '''          state.tasks = result.tasks || [];
          renderSummary(result.summary || {});
          applyFilters();   // 保留目前的篩選條件
          appendDeskpetDiary(''')

path.write_text(s, encoding='utf-8')
print('ok')
