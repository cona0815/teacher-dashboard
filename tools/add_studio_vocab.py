"""教材小工場新增 📒 生詞本（老師 2026-11-02「貼上生字，產生生詞本」）
- 注音、部首、筆畫：全字庫開放資料（assets/studio/hanzi-data.js，tools/build_hanzi_data.py 產生），不靠 AI
- 破音字：AI 只能從全字庫的讀音裡挑；沒有 AI 時列出所有讀音給老師刪
- 造詞（附注音）、造句、解釋：AI 依年級產生，系統檢查詞裡有這個字、每個字的注音都在全字庫讀音內，不符的標 ⚠
- 田字格：示範字＋描紅＋空格，年級越低格子越大
python tools/add_studio_vocab.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'page-vocab' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""    <button class="tab-button" type="button" data-page="math">🔢 數學出題</button>""",
    """    <button class="tab-button" type="button" data-page="math">🔢 數學出題</button>
    <button class="tab-button" type="button" data-page="vocab">📒 生詞本</button>""")

rep("""    /* 🔢 數學出題 */""", """    /* 📒 生詞本 */
    .vb-sheet { font-size:15px; }
    .vb-card { width:100%; border-collapse:collapse; margin:0 0 12px; break-inside:avoid; page-break-inside:avoid; }
    .vb-card td { border:1.5px solid #333; padding:6px 8px; vertical-align:top; }
    .vb-big { width:92px; text-align:center; vertical-align:middle !important; }
    .vb-big-in { display:inline-flex; align-items:center; gap:2px; }
    .vb-char { font-family:"DFKai-SB","BiauKai","標楷體","TW-Kai","Kaiti TC",serif; font-size:58px; line-height:1; }
    /* 直式注音：符號由上往下，聲調在最後一個符號右邊，輕聲點在最上面（同國語課本） */
    .zy { display:inline-flex; align-items:flex-end; font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif; font-weight:400; line-height:1; vertical-align:middle; }
    .zy-col { display:inline-flex; flex-direction:column; align-items:center; }
    .zy-col > span { display:block; font-size:var(--zy, 12.5px); line-height:1.08; }
    .zy-col > .zy-dot { line-height:.7; }
    .zy-tone { font-size:calc(var(--zy, 12.5px) * .95); line-height:1.08; width:.55em; }
    .vb-zy { --zy:19px; cursor:pointer; margin-left:2px; }
    .vb-zy[data-readings]:hover { outline:2px dashed #e0a21a; outline-offset:2px; }
    .vb-c { display:inline-flex; align-items:center; gap:1px; font-family:"DFKai-SB","BiauKai","標楷體","TW-Kai","Kaiti TC",serif; font-size:26px; }
    .vb-word { display:inline-flex; margin-right:20px; vertical-align:middle; }
    .vb-info { width:150px; font-size:14px; line-height:1.8; }
    .vb-info b { font-weight:900; }
    .vb-alt { font-size:12.5px; color:#555; }
    .vb-label { font-weight:900; margin-right:4px; }
    .vb-line { line-height:1.8; }
    .vb-grid { display:flex; gap:0; }
    .vb-cell { width:var(--vb-cell, 56px); height:var(--vb-cell, 56px); border:1.5px solid #333; margin-left:-1.5px; position:relative; display:flex; align-items:center; justify-content:center;
      font-family:"DFKai-SB","BiauKai","標楷體","TW-Kai","Kaiti TC",serif; font-size:calc(var(--vb-cell, 56px) * .78); line-height:1;
      background:linear-gradient(to right, transparent calc(50% - .5px), #bbb calc(50% - .5px), #bbb calc(50% + .5px), transparent calc(50% + .5px)),
                 linear-gradient(to bottom, transparent calc(50% - .5px), #bbb calc(50% - .5px), #bbb calc(50% + .5px), transparent calc(50% + .5px)); }
    .vb-cell:first-child { margin-left:0; }
    .vb-cell.trace { color:#c9c9c9; }
    .vb-blank { display:inline-block; width:calc(100% - 3.5em); min-width:200px; border-bottom:1px solid #777; height:1.5em; vertical-align:bottom; }
    .vb-source { font-size:11.5px; color:#555; margin-top:10px; border-top:1px solid #999; padding-top:4px; }
    .vb-edit:focus { outline:2px dashed #e0a21a; outline-offset:2px; }
    /* 🔢 數學出題 */""")

rep("""    <section class="page" id="page-review">""", """    <!-- 📚 備課：📒 生詞本（注音、部首、筆畫用全字庫開放資料；造詞、造句、解釋 AI 草稿） -->
    <section class="page" id="page-vocab">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>標題</label>
            <input class="input" id="vbTitle" placeholder="例：第三課 生詞本"></div>
          <div class="field"><label>年級</label>
            <select class="select" id="vbGrade"><option value="1">一年級</option><option value="2" selected>二年級</option><option value="3">三年級</option><option value="4">四年級</option><option value="5">五年級</option><option value="6">六年級</option></select></div>
          <div class="field"><label>貼上生字（最多 30 字）</label>
            <textarea class="textarea" id="vbChars" style="min-height:110px" placeholder="直接貼一串字：晨 曦 陽 樂&#10;要指定課文裡的讀法，就一行寫「字 詞語」：&#10;樂 音樂&#10;長 長大"></textarea></div>
          <div class="field"><label>每個字要附</label>
            <div class="check-row"><label><input type="checkbox" id="vbInfo" checked> 注音、部首、筆畫</label>
              <label><input type="checkbox" id="vbWords" checked> 造詞（2–3 個）＋造句</label>
              <label><input type="checkbox" id="vbMeaning" checked> 簡單解釋</label>
              <label><input type="checkbox" id="vbGridOn" checked> 田字格練習</label></div>
            <div class="check-row" style="margin-top:6px"><label>田字格 <select class="select" id="vbCells" style="width:auto;margin:0"><option value="6">6 格</option><option value="8" selected>8 格</option><option value="10">10 格</option></select>（第 1 格示範、2–3 格描紅）</label></div></div>
          <button class="go-button" type="button" id="vbGoButton">📒 產生生詞本</button>
          <div class="status" id="vbStatus"></div>
          <div class="hint">注音、部首、筆畫來自<strong>數位發展部全字庫</strong>官方資料，不是 AI 猜的。造詞、造句、解釋由 AI 依年級產生（要先在工作台設好 Gemini 金鑰；沒有金鑰只產生字卡和田字格）。破音字 AI 只能從官方讀音裡挑，挑不出來或詞語注音對不上的會標 ⚠。內容都可以直接點進去修改，核對後勾「老師已核對」。</div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <label class="es-confirm" id="vbCheckedLabel" style="display:none"><input type="checkbox" id="vbChecked"> 老師已核對</label>
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('vbPreview','生詞本','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('vbPreview','生詞本',false)">⬇ PDF</button>
            <span class="status" id="vbMeta">貼上生字，按「產生生詞本」。</span>
          </div>
          <div class="preview-host" id="vbPreview"></div>
        </div>
      </div>
    </section>

    <section class="page" id="page-review">""")

rep("""    // ============================================================
    // 📄 家長通知單""", """    // ============================================================
    // 📒 生詞本：注音／部首／筆畫查全字庫字表（assets/studio/hanzi-data.js，第一次用才載入）；造詞造句解釋 AI 草稿
    // ============================================================
    let vbDataPromise = null;
    function vbLoadData() {
      if (window.HANZI_DATA) return Promise.resolve();
      if (!vbDataPromise) {
        vbDataPromise = new Promise((resolve, reject) => {
          const tag = document.createElement('script');
          tag.src = 'assets/studio/hanzi-data.js';
          tag.onload = () => resolve();
          tag.onerror = () => { vbDataPromise = null; reject(new Error('字表載入失敗，請重新整理再試。')); };
          document.head.appendChild(tag);
        });
      }
      return vbDataPromise;
    }
    const VB_HAN = /[\\u3400-\\u9fff\\uf900-\\ufaff]/;
    // 解析輸入：一行「字 詞語」＝指定課文用法；其他行每個國字各算一個生字
    function vbParse(text) {
      const list = [], seen = new Set();
      String(text || '').split('\\n').forEach(line => {
        const m = /^\\s*([\\u3400-\\u9fff\\uf900-\\ufaff])\\s*[：:\\s]\\s*([\\u3400-\\u9fff\\uf900-\\ufaff]{2,8})\\s*$/.exec(line);
        if (m && m[2].includes(m[1])) {
          if (!seen.has(m[1])) { seen.add(m[1]); list.push({ ch: m[1], context: m[2] }); }
          return;
        }
        [...line].filter(c => VB_HAN.test(c)).forEach(c => { if (!seen.has(c)) { seen.add(c); list.push({ ch: c, context: '' }); } });
      });
      return list.slice(0, 30);
    }
    function vbLookup(ch) {
      const row = window.HANZI_DATA[ch];
      return row ? { strokes: row[0], radical: window.HANZI_RADICALS[row[1]] || '', readings: row[2].split(' ') } : null;
    }
    // 注音檢查：要在全字庫讀音內；輕聲（˙ㄧㄡ）只要聲韻對得上任一讀音就算
    const vbBase = zy => String(zy || '').replace(/[˙ˊˇˋ]/g, '');
    function vbReadingOk(ch, zy) {
      const info = vbLookup(ch);
      if (!info) return false;
      const z = String(zy || '').trim();
      if (info.readings.includes(z)) return true;
      return z.startsWith('˙') && info.readings.some(r => vbBase(r) === vbBase(z));
    }
    function vbZy(zy) {
      const z = String(zy || '').trim();
      const neutral = z.startsWith('˙');
      const tone = /[ˊˇˋ]$/.test(z) ? z.slice(-1) : '';
      const symbols = [...z.replace(/[˙ˊˇˋ]/g, '')];
      return `<span class="zy"><span class="zy-col">${neutral ? '<span class="zy-dot">˙</span>' : ''}${symbols.map(c => `<span>${escapeHtml(c)}</span>`).join('')}</span><span class="zy-tone">${escapeHtml(tone)}</span></span>`;
    }
    function vbRuby(word, zys) {
      const html = [...word].map((c, i) => `<span class="vb-c">${escapeHtml(c)}${zys[i] ? vbZy(zys[i]) : ''}</span>`).join('');
      return `<span class="vb-word" data-word-text="${escapeHtml(word + '（' + zys.join(' ') + '）')}">${html}</span>`;
    }
    // 點生字旁的注音：在全字庫的幾個讀音之間切換（破音字用）
    $('vbPreview').addEventListener('click', e => {
      const box = e.target.closest('.vb-zy[data-readings]');
      if (!box) return;
      const list = box.dataset.readings.split(' ');
      const next = list[(list.indexOf(box.dataset.zy) + 1) % list.length];
      box.dataset.zy = next;
      box.dataset.wordText = next;
      box.innerHTML = vbZy(next);
    });
    function vbRender(items) {
      const grade = Number($('vbGrade').value);
      const cellSize = grade <= 2 ? 62 : grade <= 4 ? 54 : 48;
      const showInfo = $('vbInfo').checked, showWords = $('vbWords').checked, showMeaning = $('vbMeaning').checked, showGrid = $('vbGridOn').checked;
      const cells = Number($('vbCells').value);
      const title = $('vbTitle').value.trim() || '生詞本';
      const cards = items.map(it => {
        const info = it.info;
        const reading = it.reading || (info ? info.readings[0] : '');
        const multi = info && info.readings.length > 1;
        const alt = (it.altWords || []).length ? `<div class="vb-alt">另讀：${it.altWords.map(a => `${escapeHtml(a.zy)}（${escapeHtml(a.word)}）`).join('、')}</div>` : '';
        const readingWarn = it.readingWarn ? `<div class="doc-verify">⚠ ${escapeHtml(it.readingWarn)}</div>` : '';
        const offlineMulti = multi && !it.aiReading ? `<div class="doc-verify">⚠ 破音字：點注音可換讀音（${escapeHtml(info.readings.join('、'))}）</div>` : '';
        const infoHtml = info
          ? `<div><b>部首</b> ${escapeHtml(info.radical)}</div><div><b>筆畫</b> ${info.strokes} 畫</div>${alt}${readingWarn}${offlineMulti}`
          : '<div class="doc-verify">⚠ 字表沒有這個字，注音、部首、筆畫請自己填</div>';
        const words = (it.words || []).map(w => vbRuby(w.word, w.zhuyin) + (w.warn ? `<span class="doc-verify">⚠ ${escapeHtml(w.warn)}</span>` : '')).join('');
        const row2 = [];
        if (showWords) {
          row2.push(`<div class="vb-line vb-words"><span class="vb-label">造詞</span><span class="vb-edit" contenteditable="true">${words || '＿＿＿＿　＿＿＿＿　＿＿＿＿'}</span></div>`);
          row2.push(`<div class="vb-line"><span class="vb-label">造句</span><span class="vb-edit" contenteditable="true">${it.sentence ? escapeHtml(it.sentence) : '<span class="vb-blank"></span>'}</span>${it.sentenceWarn ? `<span class="doc-verify">⚠ ${escapeHtml(it.sentenceWarn)}</span>` : ''}</div>`);
        }
        if (showMeaning) row2.push(`<div class="vb-line"><span class="vb-label">解釋</span><span class="vb-edit" contenteditable="true">${it.meaning ? escapeHtml(it.meaning) : '<span class="vb-blank"></span>'}</span></div>`);
        const grid = showGrid ? `<tr><td colspan="${showInfo ? 3 : 2}"><div class="vb-grid" style="--vb-cell:${cellSize}px">${Array.from({ length: cells }, (_, k) =>
          `<div class="vb-cell${k === 1 || k === 2 ? ' trace' : ''}">${k <= 2 ? escapeHtml(it.ch) : ''}</div>`).join('')}</div></td></tr>` : '';

        return `<table class="vb-card"><tr>
          <td class="vb-big"${row2.length ? ' rowspan="2"' : ''}><span class="vb-big-in"><span class="vb-char">${escapeHtml(it.ch)}</span>${showInfo && reading ? `<span class="vb-zy" data-zy="${escapeHtml(reading)}" data-word-text="${escapeHtml(reading)}"${multi ? ` data-readings="${escapeHtml(info.readings.join(' '))}" title="點一下換讀音"` : ''}>${vbZy(reading)}</span>` : ''}</span></td>
          ${showInfo ? `<td class="vb-info"${row2.length ? ' rowspan="2"' : ''}>${infoHtml}</td>` : ''}
          ${row2.length ? `<td>${row2[0]}</td></tr><tr><td>${row2.slice(1).join('')}</td>` : '<td></td>'}
        </tr>${grid}</table>`;
      }).join('');
      const usedAi = items.some(it => it.aiReading || (it.words || []).length);
      $('vbPreview').innerHTML = `<div class="sheet vb-sheet">
        <div class="ws-head"><div class="ws-title">${escapeHtml(title)}</div></div>
        <div class="ws2-name"><span>${escapeHtml($('vbGrade').options[$('vbGrade').selectedIndex].text)}</span><span>班級 <i></i></span><span>座號 <i></i></span><span>姓名 <i style="min-width:110px"></i></span></div>
        <div style="height:10px"></div>
        ${cards}
        <div class="vb-source">注音、部首、筆畫：${escapeHtml(window.HANZI_SOURCE || '數位發展部 全字庫開放資料')}，依政府資料開放授權條款第1版使用。${usedAi ? '造詞、造句、解釋：AI 協助草擬。' : ''}</div>
        ${usedAi ? '<div class="doc-ai-sign" style="display:none" data-export-hide="1">AI 協助草擬，內容已由老師核對</div>' : ''}
      </div>`;
      const warn = $('vbPreview').querySelectorAll('.doc-verify').length;
      // 有 AI 內容或 ⚠ 提醒就要老師核對；勾了「老師已核對」，⚠ 才不會印出來
      $('vbCheckedLabel').style.display = usedAi || warn ? '' : 'none';
      if (usedAi || warn) docApplyConfirm('vb');
      $('vbMeta').textContent = `${items.length} 個生字${usedAi ? '（🟡 造詞、造句、解釋是 AI 草稿' : '（未用 AI'}${warn ? `，⚠ ${warn} 處要核對` : ''}）；內容可以直接點進去修改。`;
    }
    $('vbGoButton').dataset.label = $('vbGoButton').textContent;
    $('vbGoButton').addEventListener('click', async () => {
      const picked = vbParse($('vbChars').value);
      if (!picked.length) return showToast('請先貼上生字。', true);
      busy($('vbGoButton'), true);
      try {
        $('vbStatus').textContent = '📖 載入全字庫字表…';
        await vbLoadData();
        $('vbStatus').textContent = '';
        const items = picked.map(p => Object.assign({}, p, { info: vbLookup(p.ch) }));
        const wantAi = ($('vbWords').checked || $('vbMeaning').checked) && geminiKey();
        if (($('vbWords').checked || $('vbMeaning').checked) && !geminiKey()) showToast('沒有設定 Gemini 金鑰：先產生字卡和田字格，造詞、造句、解釋留空讓你自己寫。');
        if (wantAi) {
          const grade = $('vbGrade').options[$('vbGrade').selectedIndex].text;
          const length = Number($('vbGrade').value) <= 2 ? '8 到 15 個字' : Number($('vbGrade').value) <= 4 ? '12 到 22 個字' : '18 到 30 個字';
          const lines = items.map(it => `${it.ch}｜候選讀音：${it.info ? it.info.readings.join('、') : '（字表沒有）'}${it.context ? `｜課文用法：${it.context}` : ''}`);
          const prompt = [
            `你是台灣國小${grade}的國語老師，要幫學生做生詞本。生字與官方（教育部／全字庫）候選讀音如下：`,
            ...lines,
            '規則：',
            '- reading：這個生字在課文或最常見用法的讀音，必須從候選讀音裡原樣挑一個（有寫課文用法就照那個詞的讀法）。',
            `- words：2 到 3 個常見、適合${grade}的詞語，每個詞都要包含這個生字；zhuyin 是詞裡每個字的注音陣列，用台灣注音、聲調寫在後面（一聲不標），輕聲寫成「˙ㄉㄜ」。`,
            '- 如果這個字是常見的破音字，可以有一個詞用另一個讀音，讓學生分辨。',
            `- sentence：用其中一個詞造句，${length}，生活化、正向，不要用真實人名。`,
            '- meaning：用學生聽得懂的話解釋這個字（或最常用的那個詞），25 個字以內。',
            '只回 JSON，不要其他文字：{"items":[{"char":"晨","reading":"ㄔㄣˊ","words":[{"word":"早晨","zhuyin":["ㄗㄠˇ","ㄔㄣˊ"]}],"sentence":"…","meaning":"…"}]}'
          ].join('\\n');
          const data = extractJson(await callGemini(prompt, null, $('vbStatus')));
          const byChar = new Map((data.items || []).map(x => [String(x.char || ''), x]));
          items.forEach(it => {
            const ai = byChar.get(it.ch);
            if (!ai) return;
            if (it.info && ai.reading) {
              if (it.info.readings.includes(String(ai.reading).trim())) { it.reading = String(ai.reading).trim(); it.aiReading = true; }
              else it.readingWarn = `AI 給的讀音「${String(ai.reading)}」不在全字庫讀音（${it.info.readings.join('、')}）裡，請確認`;
            }
            it.words = (Array.isArray(ai.words) ? ai.words : []).slice(0, 3).map(w => {
              const word = String(w.word || '').slice(0, 8);
              const zy = Array.isArray(w.zhuyin) ? w.zhuyin.map(z => String(z || '').trim()) : [];
              let warn = '';
              if (!word.includes(it.ch)) warn = '詞裡沒有這個生字';
              else if (zy.length !== [...word].length) warn = '注音字數和詞語對不上';
              else {
                const bad = [...word].filter((c, i) => window.HANZI_DATA[c] && !vbReadingOk(c, zy[i]));
                if (bad.length) warn = `「${bad.join('、')}」的注音不在全字庫讀音裡，請確認`;
              }
              return { word, zhuyin: zy, warn };
            }).filter(w => w.word);
            // 詞語裡生字的讀法和主讀音不同 → 列成「另讀」
            const pos = w => [...w.word].indexOf(it.ch);
            it.altWords = it.words.filter(w => !w.warn && it.reading && w.zhuyin[pos(w)] && vbBase(w.zhuyin[pos(w)]) !== vbBase(it.reading)).map(w => ({ word: w.word, zy: w.zhuyin[pos(w)] }));
            // 主讀音要至少有一個詞用到；都沒用到通常是 AI 挑錯讀音（例如「三」挑成ㄙㄚ）
            if (it.aiReading && it.words.length && !it.words.some(w => !w.warn && w.zhuyin[pos(w)] && vbBase(w.zhuyin[pos(w)]) === vbBase(it.reading))) {
              it.readingWarn = `主讀音「${it.reading}」和造詞裡的讀法都不一樣，請確認`;
              it.altWords = [];
            }
            it.sentence = String(ai.sentence || '').slice(0, 80);
            if (it.sentence && !it.sentence.includes(it.ch)) it.sentenceWarn = '句子裡沒有這個生字';
            it.meaning = String(ai.meaning || '').slice(0, 60);
          });
          if ($('vbChecked').checked) $('vbChecked').checked = false;
        }
        vbRender(items);
        const missing = items.filter(it => !it.info).map(it => it.ch);
        showToast(missing.length ? `字表沒有：${missing.join('、')}，請自己填注音、部首、筆畫。` : '生詞本產生好了，請核對後再印。', !!missing.length);
      } catch (e) {
        if (e.message !== 'no-key') showToast(e.message || '產生失敗，請再試一次。', true);
        $('vbStatus').textContent = '';
      } finally {
        busy($('vbGoButton'), false);
      }
    });

    // ============================================================
    // 📄 家長通知單""")

rep("""    docBindConfirm('mq');""", """    docBindConfirm('mq');
    docBindConfirm('vb');""")

path.write_text(s, encoding='utf-8')
print('ok')
