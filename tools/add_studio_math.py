"""教材小工場新增 🔢 數學出題小幫手（老師 2026-11-02「教材應該可以更多…數學出題小幫手」）
- 計算題：assets/studio/math-gen.js 出題與算答案，不用 AI，答案一定正確（tests/math_gen.test.js 驗算上萬題）
- 應用題（選用）：AI 出題並附算式，系統用 MathGen.evaluate 重新計算，對不上的標 ⚠ 給老師看
- 版面：每列 2–4 題、加減乘可用直式、分數用上下疊的寫法（存 Word 時換成「2又1/3」文字）、A／B 卷、答案卷
python tools/add_studio_math.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'page-math' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 分頁 ----------
rep("""    <button class="tab-button active" type="button" data-page="ws">📝 學習單</button>""",
    """    <button class="tab-button active" type="button" data-page="ws">📝 學習單</button>
    <button class="tab-button" type="button" data-page="math">🔢 數學出題</button>""")

# ---------- CSS ----------
rep("""    @media print {
      body { background:#fff; }""", """    /* 🔢 數學出題 */
    .mq-kinds { display:grid; gap:4px; max-height:320px; overflow:auto; border:1px solid var(--line); border-radius:10px; padding:6px 8px; background:#fff; }
    .mq-kind { display:flex; align-items:center; gap:8px; font-size:14px; font-weight:700; cursor:pointer; }
    .mq-kind span { flex:1; }
    .mq-kind small { color:var(--muted); margin-left:6px; font-weight:600; }
    .mq-kind .mq-count { width:62px; padding:4px 6px; }
    .mq-sheet { font-size:17px; }
    .mq-section { margin-top:16px; }
    .mq-section-head { font-weight:900; font-size:17px; border-left:5px solid #2f7d5b; padding-left:8px; margin-bottom:10px; }
    .mq-grid { display:grid; grid-template-columns:repeat(var(--mq-cols, 3), minmax(0, 1fr)); gap:18px 18px; }
    .mq-item { display:flex; align-items:center; gap:6px; min-height:42px; break-inside:avoid; page-break-inside:avoid; }
    .mq-item.is-vertical { align-items:flex-start; min-height:150px; }
    .mq-no { font-weight:800; min-width:1.9em; }
    .mq-blank { display:inline-block; min-width:60px; flex:0 1 70px; border-bottom:1.5px solid #333; height:1.3em; }
    .mq-blank.mq-short { min-width:40px; flex-basis:44px; margin:0 3px; }
    .mq-q { white-space:nowrap; }
    .mf { display:inline-flex; align-items:center; gap:2px; vertical-align:middle; margin:0 1px; }
    .mf-f { display:inline-flex; flex-direction:column; align-items:center; line-height:1.15; font-size:.88em; }
    .mf-f > span:first-child { border-bottom:1.5px solid currentColor; padding:0 3px; }
    .mv { border-collapse:collapse; font-size:21px; font-family:"Consolas","Courier New",monospace; }
    .mv td { width:1.05em; height:1.35em; text-align:center; padding:0; }
    .mv .mv-line td { border-bottom:2px solid #222; }
    .mv .mv-gap td { height:1.55em; }
    .mq-word { display:flex; gap:6px; margin:12px 0 18px; break-inside:avoid; page-break-inside:avoid; }
    .mq-word-q { line-height:1.75; }
    .mq-work { margin-top:8px; min-height:70px; }
    .mq-check { display:inline-block; margin-top:4px; font-size:12.5px; font-weight:800; padding:2px 8px; border-radius:6px; }
    .mq-check.ok { color:#1f7a52; background:#e3f6ec; }
    .mq-check.bad { color:#b3261e; background:#fde8e5; }
    .mq-key { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); column-gap:24px; font-size:15px; line-height:1.95; }
    .mq-key-word { font-size:15px; line-height:1.9; margin-top:6px; }
    @media print {
      body { background:#fff; }""")

# ---------- 頁面 ----------
rep("""    <section class="page" id="page-review">""", """    <!-- 📚 備課：🔢 數學出題小幫手（計算題由程式出題算答案，不用 AI；應用題 AI 出、系統驗算） -->
    <section class="page" id="page-math">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>標題</label>
            <input class="input" id="mqTitle" value="數學練習"></div>
          <div class="field"><label>年級</label>
            <select class="select" id="mqGrade"><option value="1">一年級</option><option value="2">二年級</option><option value="3" selected>三年級</option><option value="4">四年級</option><option value="5">五年級</option><option value="6">六年級</option></select>
            <div class="check-row" style="margin-top:6px"><label><input type="checkbox" id="mqAllGrades"> 也顯示其他年級的題型</label></div></div>
          <div class="field"><label>計算題（勾題型，右邊填題數）</label>
            <div class="mq-kinds" id="mqKinds"></div></div>
          <div class="field"><label>版面</label>
            <div class="check-row"><label>每列 <select class="select" id="mqCols" style="width:auto;margin:0"><option>2</option><option selected>3</option><option>4</option></select> 題</label>
              <label><input type="checkbox" id="mqVertical"> 加、減、乘用直式</label></div>
            <div class="check-row" style="margin-top:6px"><label>分數答案寫成 <select class="select" id="mqFracStyle" style="width:auto;margin:0"><option value="mixed">帶分數</option><option value="improper">假分數</option></select></label></div>
            <div class="check-row" style="margin-top:6px"><label><input type="checkbox" id="mqAnswer" checked> 附答案卷</label>
              <label><input type="checkbox" id="mqAB"> 出 A、B 兩卷（題型一樣、數字不同）</label></div></div>
          <button class="go-button" type="button" id="mqGoButton">🎲 產生題目（每按一次換一組數字）</button>
          <div class="field" style="margin-top:14px"><label>應用題（選用：AI 出題，系統自動驗算）</label>
            <textarea class="textarea" id="mqWordTopic" placeholder="例：分數乘法，用買東西、做點心的生活情境"></textarea>
            <div class="check-row" style="margin-top:6px;align-items:center"><label>題數 <select class="select" id="mqWordCount" style="width:auto;margin:0"><option>3</option><option selected>5</option><option>8</option></select></label>
              <button class="mini" type="button" id="mqWordButton">✨ AI 出應用題</button>
              <button class="mini" type="button" id="mqWordClear">清除應用題</button></div></div>
          <div class="status" id="mqStatus"></div>
          <div class="hint">計算題<strong>不用 AI</strong>：題目與答案都由程式產生並重新驗算，答案一定正確。應用題由 AI 出，AI 必須附上算式，系統會自己再算一次；答案對不上的題目標 ⚠，請修改或刪掉後再勾「老師已核對」。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="mqCheckedLabel" style="display:none"><input type="checkbox" id="mqChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('mqPreview','數學練習','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('mqPreview','數學練習',false)">⬇ PDF</button>
            <span class="status" id="mqMeta">勾好題型，按「產生題目」。</span>
          </div>
          <div class="preview-host" id="mqPreview"></div>
        </div>
      </div>
    </section>

    <section class="page" id="page-review">""")

# ---------- 引擎 ----------
rep("""  <script src="assets/vendor/pdf-lib.min.js"></script>""",
    """  <script src="assets/vendor/pdf-lib.min.js"></script>
  <script src="assets/studio/math-gen.js"></script>""")

# ---------- 存 Word：上下疊的分數換成文字（Word 不認得這種排法） ----------
rep("""      clone.querySelectorAll('[contenteditable]').forEach(node => node.removeAttribute('contenteditable'));
      const mime = format === 'xls'""", """      clone.querySelectorAll('[contenteditable]').forEach(node => node.removeAttribute('contenteditable'));
      if (format === 'doc') clone.querySelectorAll('[data-word-text]').forEach(node => node.replaceWith(document.createTextNode(node.dataset.wordText)));
      const mime = format === 'xls'""")

# ---------- 程式 ----------
rep("""    // ============================================================
    // 📄 家長通知單""", """    // ============================================================
    // 🔢 數學出題小幫手：計算題 MathGen 出題算答案（不用 AI）；應用題 AI 出、MathGen.evaluate 驗算
    // ============================================================
    const MQ = { seed: Date.now() % 1000000007, picked: new Set(), counts: {}, word: [] };
    const MQ_CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'];
    function mqPreset() {
      // 換年級時先勾這個年級的前兩種題型
      MQ.picked.clear();
      MathGen.KINDS.filter(k => k.grade === Number($('mqGrade').value)).slice(0, 2).forEach(k => MQ.picked.add(k.id));
    }
    function mqRenderKinds() {
      const grade = Number($('mqGrade').value), all = $('mqAllGrades').checked;
      const list = MathGen.KINDS.filter(k => all || k.grade === grade).sort((a, b) => a.grade - b.grade);
      $('mqKinds').innerHTML = list.map(k => `<label class="mq-kind"><input type="checkbox" data-kind="${k.id}"${MQ.picked.has(k.id) ? ' checked' : ''}>
        <span>${escapeHtml(k.label)}${all ? `<small>${k.grade} 年級</small>` : ''}</span>
        <input class="input mq-count" type="number" min="1" max="40" data-count="${k.id}" value="${MQ.counts[k.id] || 6}" title="題數"></label>`).join('');
    }
    $('mqKinds').addEventListener('change', e => {
      const box = e.target.closest('[data-kind]');
      if (box) { if (box.checked) MQ.picked.add(box.dataset.kind); else MQ.picked.delete(box.dataset.kind); }
    });
    $('mqKinds').addEventListener('input', e => {
      const n = e.target.closest('[data-count]');
      if (n) MQ.counts[n.dataset.count] = Math.max(1, Math.min(40, Number(n.value) || 1));
    });
    $('mqGrade').addEventListener('change', () => { mqPreset(); mqRenderKinds(); });
    $('mqAllGrades').addEventListener('change', mqRenderKinds);
    mqPreset();
    mqRenderKinds();
    function mqFmt(value, expr) {
      return /\\./.test(String(expr || '')) ? MathGen.decText(value) : MathGen.fracText(value, $('mqFracStyle').value);
    }
    // 應用題驗算：算式算出來的值要等於 AI 寫的答案
    function mqCheck(p) {
      let value;
      try { value = MathGen.evaluate(p.expr); } catch (e) { return { ok: false, msg: `⚠ 算式看不懂（${String(p.expr || '')}），請自己算一次` }; }
      let given = null;
      try { given = MathGen.parseAnswer(p.answer); } catch (e) { given = null; }
      if (given && MathGen.eq(given, value)) return { ok: true, value, msg: '✓ 系統驗算：算式和答案一致' };
      return { ok: false, value, msg: `⚠ AI 寫的答案是「${String(p.answer || '')}」，算式算出來是 ${mqFmt(value, p.expr)}，請核對題目` };
    }
    function mqRender() {
      const kinds = MathGen.KINDS.filter(k => MQ.picked.has(k.id));
      if (!kinds.length && !MQ.word.length) { $('mqPreview').innerHTML = ''; $('mqMeta').textContent = '請先勾至少一種題型。'; return false; }
      const style = $('mqFracStyle').value, vertical = $('mqVertical').checked, cols = Number($('mqCols').value);
      const grade = $('mqGrade').options[$('mqGrade').selectedIndex].text;
      const title = $('mqTitle').value.trim() || '數學練習';
      const versions = $('mqAB').checked ? ['A', 'B'] : [''];
      const pages = [], keys = [];
      versions.forEach((ver, vi) => {
        let no = 0;
        const sections = [], key = { ver, groups: [] };
        kinds.forEach((k, ki) => {
          const list = MathGen.generate(k.id, MQ.counts[k.id] || 6, MQ.seed + vi * 1000003 + ki * 7919, { fracStyle: style });
          const items = list.map(q => {
            no += 1;
            const useVertical = vertical && q.vertical;
            const blank = q.remainder ? '商<span class="mq-blank mq-short"></span>，餘<span class="mq-blank mq-short"></span>' : '<span class="mq-blank"></span>';
            const body = useVertical ? MathGen.verticalHtml(q.vertical) : `<span class="mq-q">${q.html}</span>${blank}`;
            return `<div class="mq-item${useVertical ? ' is-vertical' : ''}"><span class="mq-no">${no}.</span>${body}</div>`;
          }).join('');
          key.groups.push({ title: k.label, list: list.map((q, i) => `${no - list.length + i + 1}. ${q.answerHtml}`) });
          sections.push(`<div class="mq-section"><div class="mq-section-head">${MQ_CN[ki] || ki + 1}、${escapeHtml(k.label)}</div><div class="mq-grid" style="--mq-cols:${k.wide ? Math.min(cols, 2) : cols}">${items}</div></div>`);
        });
        if (MQ.word.length) {
          const startNo = no;
          const items = MQ.word.map(p => {
            no += 1;
            const check = mqCheck(p);
            return `<div class="mq-word"><span class="mq-no">${no}.</span><div style="flex:1">
              <div class="mq-word-q">${escapeHtml(p.q)}</div>
              <div class="mq-work">算式：</div><div>答：<span class="mq-blank" style="min-width:140px"></span></div>
              <span class="doc-verify mq-check ${check.ok ? 'ok' : 'bad'}">${escapeHtml(check.msg)}</span></div></div>`;
          }).join('');
          sections.push(`<div class="mq-section"><div class="mq-section-head">${MQ_CN[kinds.length] || kinds.length + 1}、應用題</div>${items}</div>`);
          key.word = MQ.word.map((p, i) => {
            const check = mqCheck(p);
            const shown = check.value ? mqFmt(check.value, p.expr) : String(p.answer || '');
            return `${startNo + i + 1}. ${escapeHtml(String(p.expr || ''))} ＝ ${escapeHtml(shown)} ${escapeHtml(String(p.unit || ''))}${check.ok ? '' : '<span class="doc-verify">（⚠ 請核對）</span>'}`;
          });
        }
        keys.push(key);
        pages.push(`<div class="sheet mq-sheet${vi ? ' ws-answerpage' : ''}">
          <div class="ws-head"><div class="ws-title">${escapeHtml(title)}${ver ? `（${ver} 卷）` : ''}</div></div>
          <div class="ws2-name"><span>${escapeHtml(grade)}</span><span>班級 <i></i></span><span>座號 <i></i></span><span>姓名 <i style="min-width:110px"></i></span><span>得分 <i></i></span></div>
          ${sections.join('')}
        </div>`);
      });
      if ($('mqAnswer').checked) {
        pages.push(`<div class="sheet mq-sheet ws-answerpage"><div class="ws-head"><div class="ws-title">${escapeHtml(title)}｜答案卷</div></div>
          ${keys.map(key => `${key.ver ? `<div class="mq-section-head" style="margin-top:14px">${key.ver} 卷</div>` : ''}
            ${key.groups.map((g, gi) => `<div class="mq-section"><div style="font-weight:800">${MQ_CN[gi] || gi + 1}、${escapeHtml(g.title)}</div><div class="mq-key">${g.list.map(a => `<div>${a}</div>`).join('')}</div></div>`).join('')}
            ${key.word ? `<div class="mq-section"><div style="font-weight:800">${MQ_CN[key.groups.length] || key.groups.length + 1}、應用題</div><div class="mq-key-word">${key.word.map(a => `<div>${a}</div>`).join('')}</div></div>` : ''}`).join('')}
        </div>`);
      }
      $('mqPreview').innerHTML = pages.join('');
      const total = kinds.reduce((sum, k) => sum + (MQ.counts[k.id] || 6), 0);
      const bad = MQ.word.filter(p => !mqCheck(p).ok).length;
      $('mqMeta').textContent = `計算題 ${total} 題（程式驗算，答案正確）${MQ.word.length ? `＋應用題 ${MQ.word.length} 題（🟡 AI 草稿${bad ? `，⚠ ${bad} 題對不上` : '，已驗算'}，請核對後勾「老師已核對」）` : ''}`;
      $('mqCheckedLabel').style.display = MQ.word.length ? '' : 'none';
      if (MQ.word.length) docApplyConfirm('mq');
      return true;
    }
    $('mqGoButton').addEventListener('click', () => {
      MQ.seed = (MQ.seed * 48271 + 11) % 2147483647;
      if (mqRender()) showToast('已產生新的一組題目。');
    });
    ['mqCols', 'mqVertical', 'mqFracStyle', 'mqAnswer', 'mqAB', 'mqTitle'].forEach(id => $(id).addEventListener('change', () => { if ($('mqPreview').innerHTML.trim()) mqRender(); }));
    $('mqWordButton').dataset.label = $('mqWordButton').textContent;
    $('mqWordButton').addEventListener('click', async () => {
      const topic = $('mqWordTopic').value.trim();
      if (!topic) return showToast('請先寫應用題的單元或情境。', true);
      const grade = $('mqGrade').options[$('mqGrade').selectedIndex].text;
      const count = Number($('mqWordCount').value);
      const prompt = [
        `你是台灣國小數學老師。請出 ${count} 題「${grade}」數學應用題，單元或情境：${topic}。`,
        '規則：',
        '- 繁體中文、台灣國小用語與單位（公尺、公斤、元…），數字大小適合這個年級，一題一個問題。',
        '- 人名只用虛構的名字（例如小明、小美），不要用真實學生姓名。',
        '- 不要出需要看圖、量角器或作圖才能回答的題目。',
        '- 每題一定要附「算式」：只能用數字、+ - × ÷ 和括號；分數寫成 a/b，帶分數寫成「2又1/3」。系統會用算式自動驗算。',
        '- answer 只寫數字（分數、帶分數或小數都可以），單位另外寫在 unit。',
        '只回 JSON，不要其他文字：{"problems":[{"q":"題目","expr":"算式","answer":"答案","unit":"單位"}]}'
      ].join('\\n');
      busy($('mqWordButton'), true);
      try {
        const data = extractJson(await callGemini(prompt, null, $('mqStatus')));
        const problems = (data.problems || []).filter(p => p && p.q).slice(0, count)
          .map(p => ({ q: String(p.q).slice(0, 400), expr: String(p.expr || '').slice(0, 120), answer: String(p.answer == null ? '' : p.answer).slice(0, 40), unit: String(p.unit || '').slice(0, 10) }));
        if (!problems.length) throw new Error('AI 沒有出題，請再試一次。');
        MQ.word = problems;
        if ($('mqChecked').checked) $('mqChecked').checked = false;
        mqRender();
        const bad = problems.filter(p => !mqCheck(p).ok).length;
        showToast(bad ? `應用題出好了，但有 ${bad} 題算式和答案對不上（標 ⚠），請修改或重出。` : '應用題出好了，系統驗算都對；請再看一次題意。', !!bad);
      } catch (e) {
        if (e.message !== 'no-key') showToast(e.message || '出題失敗，請再試一次。', true);
        $('mqStatus').textContent = '';
      } finally {
        busy($('mqWordButton'), false);
      }
    });
    $('mqWordClear').addEventListener('click', () => { MQ.word = []; $('mqChecked').checked = false; mqRender(); });

    // ============================================================
    // 📄 家長通知單""")

# docBindConfirm 寫在比較後面，數學出題也要接上「老師已核對」
rep("""    docBindConfirm('rp');""", """    docBindConfirm('rp');
    docBindConfirm('mq');""")

path.write_text(s, encoding='utf-8')
print('ok')
