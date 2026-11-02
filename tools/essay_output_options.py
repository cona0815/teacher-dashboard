"""作文批改：輸出內容可以勾選，加「錯字訂正單」（老師 2026-11-02「作文批改有改錯字的選項嗎」「輸出的選項，可以勾選嗎」）
- 「批改重點」真的會限制 AI 找的類別（以前只勾錯別字，AI 還是連標點、語句一起抓）
- 「輸出內容」九項可勾：評分、寫得好的地方、原文逐段標記、修改清單、段落修改指引、結構與內容、老師的話、規準表、錯字訂正單
  沒勾的項目不放進提示詞（比較快），也不出現在批改單
- 一鍵「只改錯字」：批改重點只留錯別字、不評分、只輸出原文標記＋修改清單＋錯字訂正單
- 錯字訂正單：每個正確字附注音（AI 給、對照全字庫讀音；只有一個讀音就直接用全字庫）與田字格，沿用生詞本的格子
- 勾選會記在這台電腦
python tools/essay_output_options.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'esOutputs' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 畫面 ----------
rep("""          <div class="field"><label>批改重點（可複選）</label>""",
    """          <div class="field"><label>快速選擇</label>
            <div class="check-row"><button class="mini" type="button" id="esPresetFull">📋 完整批改</button><button class="mini" type="button" id="esPresetTypo">🔤 只改錯字</button></div></div>
          <div class="field"><label>批改重點（可複選；AI 只找勾的類別）</label>""")
rep("""          <div class="field"><label>評分方式</label>
            <select class="select" id="esScoring">""", """          <div class="field"><label>輸出內容（可複選；沒勾的不會產生）</label>
            <div class="check-row" id="esOutputs">
              <label><input type="checkbox" class="esOut" value="score" checked>評分</label>
              <label><input type="checkbox" class="esOut" value="strengths" checked>寫得好的地方</label>
              <label><input type="checkbox" class="esOut" value="markup" checked>原文逐段標記</label>
              <label><input type="checkbox" class="esOut" value="list" checked>修改清單</label>
              <label><input type="checkbox" class="esOut" value="paraNotes" checked>段落修改指引</label>
              <label><input type="checkbox" class="esOut" value="structure" checked>結構與內容</label>
              <label><input type="checkbox" class="esOut" value="comment" checked>老師的話</label>
              <label><input type="checkbox" class="esOut" value="rubric" checked>規準表</label>
              <label><input type="checkbox" class="esOut" value="typoSheet">錯字訂正單（田字格）</label>
            </div></div>
          <div class="field"><label>評分方式</label>
            <select class="select" id="esScoring">""")

# ---------- 勾選狀態：記在這台電腦、快速選擇 ----------
rep("""    const ES_CATEGORY_COLORS = { '錯字': '#d32f2f', '標點': '#ef6c00', '用字': '#7b1fa2', '語詞': '#1565c0', '語句': '#2e7d32' };""",
    """    const ES_CATEGORY_COLORS = { '錯字': '#d32f2f', '標點': '#ef6c00', '用字': '#7b1fa2', '語詞': '#1565c0', '語句': '#2e7d32' };
    // 批改重點 → AI 要找的類別；結構、內容深度另外靠段落指引與結構建議
    const ES_FOCUS_CATS = { '錯別字': ['錯字', '用字'], '標點符號': ['標點'], '句子通順': ['語詞', '語句'] };
    const ES_OUT_KEY = 'studio_essay_outputs_v1';
    const esOut = name => !!document.querySelector(`.esOut[value="${name}"]:checked`);
    function esSaveOutputs() {
      try {
        localStorage.setItem(ES_OUT_KEY, JSON.stringify({ out: [...document.querySelectorAll('.esOut:checked')].map(c => c.value),
          focus: [...document.querySelectorAll('.esFocus:checked')].map(c => c.value), scoring: $('esScoring').value }));
      } catch (e) {}
    }
    (function esLoadOutputs() {
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem(ES_OUT_KEY) || 'null'); } catch (e) { saved = null; }
      if (!saved) return;
      if (Array.isArray(saved.out)) document.querySelectorAll('.esOut').forEach(c => { c.checked = saved.out.includes(c.value); });
      if (Array.isArray(saved.focus)) document.querySelectorAll('.esFocus').forEach(c => { c.checked = saved.focus.includes(c.value); });
      if (saved.scoring && $('esScoring').querySelector(`option[value="${saved.scoring}"]`)) $('esScoring').value = saved.scoring;
    })();
    document.querySelectorAll('.esOut, .esFocus').forEach(c => c.addEventListener('change', esSaveOutputs));
    $('esScoring').addEventListener('change', esSaveOutputs);
    function esPreset(outs, focus, scoring) {
      document.querySelectorAll('.esOut').forEach(c => { c.checked = outs.includes(c.value); });
      document.querySelectorAll('.esFocus').forEach(c => { c.checked = focus.includes(c.value); });
      $('esScoring').value = scoring;
      esSaveOutputs();
    }
    $('esPresetFull').addEventListener('click', () => { esPreset(['score', 'strengths', 'markup', 'list', 'paraNotes', 'structure', 'comment', 'rubric'], ['錯別字', '標點符號', '句子通順'], '六級分'); showToast('已切換成完整批改。'); });
    $('esPresetTypo').addEventListener('click', () => { esPreset(['markup', 'list', 'typoSheet'], ['錯別字'], '不評分'); showToast('已切換成只改錯字：不評分，只標錯字並產生訂正單。'); });
    // 錯字訂正單：每個「正確字」一列，注音＋田字格（字表與格子沿用生詞本）
    function esTypoSheetHtml(data) {
      const seen = new Set(), rows = [];
      (data.corrections || []).filter(c => c.category === '錯字' && c.corrected).forEach(c => {
        const wrong = [...String(c.original || '')], right = [...String(c.corrected || '')];
        const zys = Array.isArray(c.correctedZhuyin) ? c.correctedZhuyin.map(z => String(z || '').trim()) : [];
        right.forEach((ch, i) => {
          if (!VB_HAN.test(ch) || seen.has(ch)) return;
          if (wrong.length === right.length && wrong[i] === ch) return;   // 同一個位置原本就寫對的字不用訂正
          seen.add(ch);
          const info = window.HANZI_DATA ? vbLookup(ch) : null;
          let zy = '';
          if (zys[i] && vbReadingOk(ch, zys[i])) zy = zys[i];
          else if (info && info.readings.length === 1) zy = info.readings[0];
          rows.push({ ch, zy, word: right.join(''), wrong: wrong.join('') });
        });
      });
      if (!rows.length) return '';
      return `<div class="sheet ws-answerpage vb-sheet">
        <div class="ws-head"><div class="ws-title">錯字訂正單</div></div>
        <div class="ws-meta"><span>題目：${escapeHtml($('esTopic').value.trim() || '＿＿＿＿＿')}</span><span>座號：${escapeHtml($('esSeat').value.trim() || '＿＿＿')}</span><span>共 ${rows.length} 個字</span></div>
        <div style="height:8px"></div>
        ${rows.map(r => `<table class="vb-card"><tr>
          <td class="vb-big"><span class="vb-big-in"><span class="vb-char">${escapeHtml(r.ch)}</span>${r.zy ? `<span class="vb-zy" data-word-text="${escapeHtml(r.zy)}">${vbZy(r.zy)}</span>` : ''}</span></td>
          <td style="width:190px;font-size:14px;line-height:1.9"><div>原本寫：<span style="color:#d32f2f">「${escapeHtml(r.wrong)}」</span></div><div>正確：<b>${escapeHtml(r.word)}</b></div></td>
          <td><div class="vb-grid" style="--vb-cell:54px"><div class="vb-cell">${escapeHtml(r.ch)}</div><div class="vb-cell trace">${escapeHtml(r.ch)}</div>${'<div class="vb-cell"></div>'.repeat(6)}</div></td>
        </tr></table>`).join('')}
        <div class="vb-source">注音：AI 依作文用法標注並對照數位發展部全字庫開放資料（政府資料開放授權條款第1版）；沒標的是破音字，請老師補上。</div>
      </div>`;
    }""")

# ---------- 修改標記與清單：只放勾的類別、各自可關 ----------
rep("""    function essayMarkupHtml(data) {
      const corrections = (data.corrections || []).map((c, i) => ({""", """    function essayMarkupHtml(data, cats, showMarkup, showList) {
      const corrections = (data.corrections || []).filter(c => !cats || cats.includes(c.category)).map((c, i) => ({""")
rep("""      return `
          ${paragraphs.length ? `<div class="ws-section">📖 原文逐段批改""", """      return `
          ${showMarkup !== false && paragraphs.length ? `<div class="ws-section">📖 原文逐段批改""")
rep("""          <div class="ws-section">✏️ 修改清單（共 ${corrections.length} 處：${summary || '無'}）</div>
          <table style="width:100%;border-collapse:collapse;font-size:13.5px">
            <tr><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:34px">#</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:64px">段落</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:66px">類別</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">原文</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">正確答案</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">說明</th></tr>
            ${rows || '<tr><td colspan="6" style="border:1px solid #999;padding:8px;text-align:center;color:#666">沒有需要修改的地方 🎉</td></tr>'}
          </table>`;""", """          ${showList === false ? '' : `<div class="ws-section">✏️ 修改清單（共 ${corrections.length} 處：${summary || '無'}）</div>
          <table style="width:100%;border-collapse:collapse;font-size:13.5px">
            <tr><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:34px">#</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:64px">段落</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3;width:66px">類別</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">原文</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">正確答案</th><th style="border:1px solid #999;padding:5px;background:#f3f3f3">說明</th></tr>
            ${rows || '<tr><td colspan="6" style="border:1px solid #999;padding:8px;text-align:center;color:#666">沒有需要修改的地方 🎉</td></tr>'}
          </table>`}`;""")

# ---------- 提示詞：只要勾的類別、只產生勾的內容 ----------
rep("""      const focus = [...document.querySelectorAll('.esFocus:checked')].map(c => c.value);
      const scoring = $('esScoring').value;""", """      const focus = [...document.querySelectorAll('.esFocus:checked')].map(c => c.value);
      const scoring = esOut('score') ? $('esScoring').value : '不評分';
      const pickedCats = [...new Set(focus.flatMap(f => ES_FOCUS_CATS[f] || []))];
      const cats = pickedCats.length ? pickedCats : Object.keys(ES_CATEGORY_COLORS);
      const wantCorrections = esOut('markup') || esOut('list') || esOut('typoSheet');
      if (!document.querySelector('.esOut:checked')) return showToast('「輸出內容」至少要勾一項。', true);
      if (esOut('typoSheet')) await vbLoadData().catch(() => null);""")
rep("""        '2. 逐段、逐句找出「所有」需要修改的地方，不要省略：category 只能是 錯字／標點／用字／語詞／語句 五種之一。',
        '   ・錯字＝寫錯的字（含注音代替）；標點＝標點缺漏或用錯；用字＝字沒錯但這裡用得不恰當；語詞＝詞彙搭配不當或可更精準；語句＝句子不通順、重複、缺主詞或太長。',
        '3. 每一處都要給 paragraph（第幾段，從 1 起算）、original（原文片段，抄原樣、最多 25 字）、corrected（正確或更好的寫法）、reason（一句話說明為什麼）。',
        '4. 逐段給「段落修改指引」paragraphNotes：""", """        wantCorrections ? `2. 逐段、逐句找出${cats.length < 5 ? '下列類別' : '「所有」'}需要修改的地方，不要省略：category 只能是 ${cats.join('／')} 之一${cats.length < 5 ? '；其他類別的問題這次不用列' : ''}。` : '2. 這次不用列修改處，corrections 回空陣列。',
        wantCorrections ? '   ・錯字＝寫錯的字（含注音代替）；標點＝標點缺漏或用錯；用字＝字沒錯但這裡用得不恰當；語詞＝詞彙搭配不當或可更精準；語句＝句子不通順、重複、缺主詞或太長。手寫看不清楚的字用□，不要當成錯字。' : '',
        wantCorrections ? `3. 每一處都要給 paragraph（第幾段，從 1 起算）、original（原文片段，抄原樣、最多 25 字）、corrected（正確或更好的寫法）、reason（一句話說明為什麼）${esOut('typoSheet') ? '；錯字另外給 correctedZhuyin：corrected 每個字的注音陣列（台灣注音，一聲不標）' : ''}。` : '',
        esOut('paraNotes') && '4. 逐段給「段落修改指引」paragraphNotes：""")
rep("""若某段寫得好也要說明為什麼好、可以怎麼再加分。',
        '5. 評語 comment 固定三條""", """若某段寫得好也要說明為什麼好、可以怎麼再加分。',
        esOut('comment') && '5. 評語 comment 固定三條""")

# ---------- 批改單：只放勾的區塊 ----------
rep("""        const band = scoring === '六級分' ? esBand($('esGrade').value) : '';""",
    """        const band = scoring === '六級分' ? esBand($('esGrade').value) : '';
        const typoSheet = esOut('typoSheet') ? esTypoSheetHtml(data) : '';""")
rep("""        $('esPreview').innerHTML = `<div class="sheet" style="position:relative">
          ${gradeBadge}
          <div class="ws-head"><div class="ws-title">作文批改單</div></div>""", """        $('esPreview').innerHTML = `<div class="sheet" style="position:relative">
          ${esOut('score') ? gradeBadge : ''}
          <div class="ws-head"><div class="ws-title">作文批改單</div></div>""")
rep("""          ${dimensionTable}
          <div class="ws-section">🌟 寫得很棒的地方</div>
          <ul style="font-size:15px;margin-left:2em">${(data.strengths || []).map(s => `<li style="margin:4px 0">${escapeHtml(s)}</li>`).join('')}</ul>
          ${essayMarkupHtml(data)}
          ${(data.paragraphNotes || []).length ? `<div class="ws-section">🧭 段落修改指引""", """          ${esOut('score') ? dimensionTable : ''}
          ${esOut('strengths') ? `<div class="ws-section">🌟 寫得很棒的地方</div>
          <ul style="font-size:15px;margin-left:2em">${(data.strengths || []).map(s => `<li style="margin:4px 0">${escapeHtml(s)}</li>`).join('')}</ul>` : ''}
          ${wantCorrections && (esOut('markup') || esOut('list')) ? essayMarkupHtml(data, cats, esOut('markup'), esOut('list')) : ''}
          ${esOut('paraNotes') && (data.paragraphNotes || []).length ? `<div class="ws-section">🧭 段落修改指引""")
rep("""          <div class="ws-section">🏗 結構與內容</div>
          <p style="font-size:15px">${escapeHtml(data.structure || '')}</p>
          <div class="ws-section">💬 老師的話（兩個做得好・一個再進步）</div>
          <div style="font-size:15.5px;background:#fff7e6;border-radius:10px;padding:10px 14px">
            ${(() => { const c = data.comment || {}; const praise = Array.isArray(c.praise) ? c.praise : (typeof c === 'string' ? [c] : []); const improve = c.improve || ''; return praise.slice(0, 2).map(t => `<div style="margin:3px 0">⭐ ${escapeHtml(t)}</div>`).join('') + (improve ? `<div style="margin:6px 0 0;color:#1f514a">🌱 ${escapeHtml(improve)}</div>` : ''); })()}
          </div>
          ${band ? esRubricTableHtml(band) : ''}
          <p style="text-align:right;font-size:14px;margin-top:14px">老師簽名：＿＿＿＿＿＿＿＿</p>
        </div>`;""", """          ${esOut('structure') ? `<div class="ws-section">🏗 結構與內容</div>
          <p style="font-size:15px">${escapeHtml(data.structure || '')}</p>` : ''}
          ${esOut('comment') ? `<div class="ws-section">💬 老師的話（兩個做得好・一個再進步）</div>
          <div style="font-size:15.5px;background:#fff7e6;border-radius:10px;padding:10px 14px">
            ${(() => { const c = data.comment || {}; const praise = Array.isArray(c.praise) ? c.praise : (typeof c === 'string' ? [c] : []); const improve = c.improve || ''; return praise.slice(0, 2).map(t => `<div style="margin:3px 0">⭐ ${escapeHtml(t)}</div>`).join('') + (improve ? `<div style="margin:6px 0 0;color:#1f514a">🌱 ${escapeHtml(improve)}</div>` : ''); })()}
          </div>` : ''}
          ${band && esOut('rubric') ? esRubricTableHtml(band) : ''}
          <p style="text-align:right;font-size:14px;margin-top:14px">老師簽名：＿＿＿＿＿＿＿＿</p>
        </div>${typoSheet}`;
        if (esOut('typoSheet') && !typoSheet) showToast('這篇沒有找到錯字，所以沒有產生訂正單。');""")

path.write_text(s, encoding='utf-8')
print('ok')
