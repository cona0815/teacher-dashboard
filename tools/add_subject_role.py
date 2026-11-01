"""工作台身分升級（升級規劃第一批第 5 項之二）：
- 新增「科任」身分
- 工具箱依身分顯示：data-role-only 可寫多個身分（空白分隔）；聯絡本只給導師、教學進度給教師與科任
- 身分隱藏用 class（role-hidden），不跟「LINE 才顯示」的 hidden 互相蓋掉；舊的 grade6SelectedRoles 照樣讀得到
python tools/add_subject_role.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Index.html'
s = path.read_text(encoding='utf-8')
assert "subject: '科任'" not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''    const ROLE_LABELS = { gradeLead: '學年主任', admin: '行政', homeroom: '導師', teacher: '教師' };''',
    '''    const ROLE_LABELS = { gradeLead: '學年主任', admin: '行政', homeroom: '導師', subject: '科任', teacher: '教師' };''')
rep('''      <button class="role-person" type="button" data-role="teacher" aria-pressed="true"><img src="assets/koboyo/academic-year-planner.svg" alt=""><span>教師</span><span class="role-check">✓</span></button>''',
    '''      <button class="role-person" type="button" data-role="subject" aria-pressed="false"><img src="assets/koboyo/academic-year-planner.svg" alt=""><span>科任</span><span class="role-check">✓</span></button>
      <button class="role-person" type="button" data-role="teacher" aria-pressed="true"><img src="assets/koboyo/academic-year-planner.svg" alt=""><span>教師</span><span class="role-check">✓</span></button>''')
rep('''            <button class="toolbox-button" type="button" data-toolbox-target="contactBookSection" data-line-only aria-expanded="false" hidden>聯絡本</button>''',
    '''            <button class="toolbox-button" type="button" data-toolbox-target="contactBookSection" data-line-only data-role-only="homeroom" aria-expanded="false" hidden>聯絡本</button>''')
rep('''data-toolbox-target="teachingProgressPanel" data-role-only="teacher" aria-expanded="false">教學進度</button>''',
    '''data-toolbox-target="teachingProgressPanel" data-role-only="teacher subject" aria-expanded="false">教學進度</button>''')
rep('''      const hasTeacherRole = roleWorkspaceState.selectedRoles.has('teacher');
      $('teachingProgressPanel').hidden = !hasTeacherRole;
      const teachingToolButton = document.querySelector('[data-toolbox-target="teachingProgressPanel"]');
      if (teachingToolButton) teachingToolButton.hidden = !hasTeacherRole;
      if (!hasTeacherRole && teachingToolButton?.classList.contains('active')) setTeacherToolbox('');''',
    '''      const roles = roleWorkspaceState.selectedRoles;
      const hasTeacherRole = roles.has('teacher') || roles.has('subject');   // 教學進度：教師、科任都用得到
      $('teachingProgressPanel').hidden = !hasTeacherRole;
      // 工具箱依身分顯示（data-role-only 可寫多個身分）；用 class 隱藏，不跟「LINE 才顯示」的 hidden 互相蓋掉
      document.querySelectorAll('[data-role-only]').forEach(el => {
        const allowed = el.dataset.roleOnly.split(/\\s+/).some(role => roles.has(role));
        el.classList.toggle('role-hidden', !allowed);
        if (!allowed && el.classList.contains('active')) setTeacherToolbox('');
      });
      $('teachingProgressTitle').textContent = roles.has('subject') && !roles.has('teacher') ? '科任｜各班教學與評量進度' : '教師｜教學與評量進度';''')
rep('''      if (targetId === 'teachingProgressPanel' && !roleWorkspaceState.selectedRoles.has('teacher')) {
        return showToast('請先勾選「教師」身分。', true);''',
    '''      if (targetId === 'teachingProgressPanel' && !roleWorkspaceState.selectedRoles.has('teacher') && !roleWorkspaceState.selectedRoles.has('subject')) {
        return showToast('請先勾選「教師」或「科任」身分。', true);''')
rep('''  <style>''', '''  <style>
    .role-hidden { display: none !important; }''')

path.write_text(s, encoding='utf-8')
print('ok')
