"""數學出題：加入「應用題（不用 AI）」——生活情境模板，數字隨機、答案由程式算（MathGen.WORDS）
python tools/add_studio_math_words.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'mqWordKinds' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""          <div class="field"><label>計算題（勾題型，右邊填題數）</label>
            <div class="mq-kinds" id="mqKinds"></div></div>""", """          <div class="field"><label>計算題（勾題型，右邊填題數）</label>
            <div class="mq-kinds" id="mqKinds"></div></div>
          <div class="field"><label>應用題（不用 AI：生活情境，答案由程式算）</label>
            <div class="mq-kinds" id="mqWordKinds"></div></div>""")
rep("""          <div class="field" style="margin-top:14px"><label>應用題（選用：AI 出題，系統自動驗算）</label>""",
    """          <div class="field" style="margin-top:14px"><label>更多應用題（選用：AI 依你的單元出題，系統自動驗算）</label>""")

rep("""    const MQ = { seed: Date.now() % 1000000007, picked: new Set(), counts: {}, word: [] };""",
    """    const MQ = { seed: Date.now() % 1000000007, picked: new Set(), counts: {}, word: [], wordPicked: new Set(), wordCounts: {} };""")
rep("""    function mqRenderKinds() {
      const grade = Number($('mqGrade').value), all = $('mqAllGrades').checked;""", """    function mqRenderWordKinds() {
      const grade = Number($('mqGrade').value), all = $('mqAllGrades').checked;
      const list = MathGen.WORDS.filter(k => all || k.grade === grade).sort((a, b) => a.grade - b.grade);
      $('mqWordKinds').innerHTML = list.map(k => `<label class="mq-kind"><input type="checkbox" data-word-kind="${k.id}"${MQ.wordPicked.has(k.id) ? ' checked' : ''}>
        <span>${escapeHtml(k.label)}${all ? `<small>${k.grade} 年級</small>` : ''}</span>
        <input class="input mq-count" type="number" min="1" max="10" data-word-count="${k.id}" value="${MQ.wordCounts[k.id] || 2}" title="題數"></label>`).join('');
    }
    $('mqWordKinds').addEventListener('change', e => {
      const box = e.target.closest('[data-word-kind]');
      if (box) { if (box.checked) MQ.wordPicked.add(box.dataset.wordKind); else MQ.wordPicked.delete(box.dataset.wordKind); }
    });
    $('mqWordKinds').addEventListener('input', e => {
      const n = e.target.closest('[data-word-count]');
      if (n) MQ.wordCounts[n.dataset.wordCount] = Math.max(1, Math.min(10, Number(n.value) || 1));
    });
    function mqRenderKinds() {
      mqRenderWordKinds();
      const grade = Number($('mqGrade').value), all = $('mqAllGrades').checked;""")
rep("""      MQ.picked.clear();
      MathGen.KINDS.filter(k => k.grade === Number($('mqGrade').value)).slice(0, 2).forEach(k => MQ.picked.add(k.id));""",
    """      MQ.picked.clear();
      MQ.wordPicked.clear();
      MathGen.KINDS.filter(k => k.grade === Number($('mqGrade').value)).slice(0, 2).forEach(k => MQ.picked.add(k.id));
      MathGen.WORDS.filter(k => k.grade === Number($('mqGrade').value)).slice(0, 1).forEach(k => MQ.wordPicked.add(k.id));""")

# 畫面：程式出的應用題放在計算題後面、AI 應用題前面
rep("""      const kinds = MathGen.KINDS.filter(k => MQ.picked.has(k.id));
      if (!kinds.length && !MQ.word.length) {""", """      const kinds = MathGen.KINDS.filter(k => MQ.picked.has(k.id));
      const wordKinds = MathGen.WORDS.filter(k => MQ.wordPicked.has(k.id));
      if (!kinds.length && !wordKinds.length && !MQ.word.length) {""")
rep("""        if (MQ.word.length) {
          const startNo = no;""", """        if (wordKinds.length) {
          const startNo = no, problems = [];
          wordKinds.forEach((k, ki) => problems.push(...MathGen.generateWords(k.id, MQ.wordCounts[k.id] || 2, MQ.seed + vi * 1000003 + 50021 + ki * 7919)));
          const items = problems.map(p => {
            no += 1;
            return `<div class="mq-word"><span class="mq-no">${no}.</span><div style="flex:1">
              <div class="mq-word-q">${MathGen.textHtml(p.q)}</div>
              <div class="mq-work">${p.eq ? '等式：' : '算式：'}</div><div>答：<span class="mq-blank" style="min-width:140px"></span></div></div></div>`;
          }).join('');
          sections.push(`<div class="mq-section"><div class="mq-section-head">${MQ_CN[sections.length] || sections.length + 1}、應用題</div>${items}</div>`);
          key.progWord = problems.map((p, i) => `${startNo + i + 1}. ${p.eq ? `${MathGen.exprHtml(p.eq)}，` : ''}${MathGen.exprHtml(p.expr)} ＝ ${MathGen.textHtml(p.answerText)}`);
        }
        if (MQ.word.length) {
          const startNo = no;""")
rep("""          sections.push(`<div class="mq-section"><div class="mq-section-head">${MQ_CN[kinds.length] || kinds.length + 1}、應用題</div>${items}</div>`);""",
    """          sections.push(`<div class="mq-section"><div class="mq-section-head">${MQ_CN[sections.length] || sections.length + 1}、${wordKinds.length ? '應用題（二）' : '應用題'}</div>${items}</div>`);""")
rep("""            ${key.word ? `<div class="mq-section"><div style="font-weight:800">${MQ_CN[key.groups.length] || key.groups.length + 1}、應用題</div><div class="mq-key-word">${key.word.map(a => `<div>${a}</div>`).join('')}</div></div>` : ''}`).join('')}""",
    """            ${key.progWord ? `<div class="mq-section"><div style="font-weight:800">${MQ_CN[key.groups.length] || key.groups.length + 1}、應用題</div><div class="mq-key-word">${key.progWord.map(a => `<div>${a}</div>`).join('')}</div></div>` : ''}
            ${key.word ? `<div class="mq-section"><div style="font-weight:800">${MQ_CN[key.groups.length + (key.progWord ? 1 : 0)] || ''}、${key.progWord ? '應用題（二）' : '應用題'}</div><div class="mq-key-word">${key.word.map(a => `<div>${a}</div>`).join('')}</div></div>` : ''}`).join('')}""")
rep("""      const total = kinds.reduce((sum, k) => sum + (MQ.counts[k.id] || 6), 0);""",
    """      const total = kinds.reduce((sum, k) => sum + (MQ.counts[k.id] || 6), 0) + wordKinds.reduce((sum, k) => sum + (MQ.wordCounts[k.id] || 2), 0);""")
rep("""      $('mqMeta').textContent = `計算題 ${total} 題（程式驗算，答案正確）""", """      $('mqMeta').textContent = `程式出題 ${total} 題（答案由程式算，一定正確）""")

path.write_text(s, encoding='utf-8')
print('ok')
