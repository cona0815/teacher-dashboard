"""作文範文庫（升級規劃第一批第 4 項）：不侵權的範文來源
- AI 原創對照範文：依年段規準一次生成三篇不同程度＋「為什麼是這個程度」評析，固定標示「AI 生成示範文，非真實學生作品」
- 老師自己加入：要選來源並勾授權聲明；公有領域要填作者卒年（歿逾 50 年才收）；學生佳作要勾已匿名化與已取得同意
- 學生與家長同意書範本（Word）；資料只存這台電腦，可匯出／匯入 JSON 備份
python tools/add_model_essay_library.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'page-library' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''    <button class="tab-button" type="button" data-page="essay">✍️ 作文批改</button>''', '''    <button class="tab-button" type="button" data-page="essay">✍️ 作文批改</button>
    <button class="tab-button" type="button" data-page="library">📗 作文範文庫</button>''')

rep('''          <div class="preview-host" id="esPreview"></div>
        </div>
      </div>''', '''          <div class="preview-host" id="esPreview"></div>
        </div>
      </div>
    </section>

    <!-- 📗 作文範文庫（只收合法來源：AI 原創、老師自寫或授權、已同意的學生佳作、公有領域） -->
    <section class="page" id="page-library">
      <div class="workbench">
        <div class="panel">
          <div class="field"><label>年級</label>
            <select class="select" id="lbGrade"><option value="一">一年級</option><option value="二">二年級</option><option value="三">三年級</option><option value="四">四年級</option><option value="五" selected>五年級</option><option value="六">六年級</option></select></div>
          <div class="field"><label>題目</label>
            <input class="input" id="lbTopic" placeholder="例：難忘的校外教學／我的家人"></div>
          <div class="field"><label>文體</label>
            <select class="select" id="lbGenre"><option>記敘文</option><option>寫人</option><option>寫景</option><option>抒情文</option><option>說明文</option><option>想像文</option><option>看圖寫話</option></select></div>
          <button class="go-button" type="button" id="lbGoButton">🤖 生成三篇對照範文</button>
          <div class="status" id="lbStatus"></div>
          <div class="hint">AI 依「作文批改」同一份年段規準，寫出高、中、待加強三種程度的原創範文，每篇附「為什麼是這個程度」。適合上課比較：哪一篇好在哪裡、另一篇差在哪裡。</div>

          <div class="es-records">
            <h4>➕ 加入我自己的範文</h4>
            <div class="field"><label>來源</label>
              <select class="select" id="lbSource">
                <option value="teacher">我自己寫的</option>
                <option value="colleague">同事寫的（已取得同意）</option>
                <option value="student">學生佳作（已取得學生與家長同意）</option>
                <option value="public">公有領域名篇（作者過世超過 50 年）</option>
              </select></div>
            <div class="field" id="lbAuthorRow" hidden><label>作者與卒年</label>
              <div style="display:flex;gap:6px"><input class="input" id="lbAuthor" placeholder="作者"><input class="input" id="lbDeathYear" inputmode="numeric" placeholder="卒年（西元）" style="max-width:130px"></div></div>
            <div class="field"><label>範文題目</label><input class="input" id="lbOwnTitle" placeholder="範文題目"></div>
            <div class="field"><label>內文</label><textarea class="textarea" id="lbOwnText" placeholder="貼上範文"></textarea></div>
            <label style="font-size:13px;font-weight:700;display:block"><input type="checkbox" id="lbRights"> <span id="lbRightsText">這篇是我自己寫的，我擁有著作權</span></label>
            <label style="font-size:13px;font-weight:700;display:block" id="lbAnonRow" hidden><input type="checkbox" id="lbAnon"> 已拿掉姓名、座號、班級與認得出是誰的事件</label>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
              <button class="mini" type="button" id="lbAddButton">加入範文庫</button>
              <button class="mini" type="button" id="lbConsentButton">📄 同意書範本（Word）</button>
            </div>
            <div class="warn" style="margin-top:8px">不能放進來的：出版社作文書、補習班講義、作文網站或部落格的文章、報章雜誌、課本課文全文、沒經同意的學生作品，以及用 AI「改寫」上面任何一種。</div>
          </div>

          <div class="es-records">
            <h4>📚 範文庫（只存在這台電腦）</h4>
            <div id="lbList"></div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
              <button class="mini" type="button" id="lbExport">⬇ 匯出備份</button>
              <label class="mini" style="cursor:pointer">⬆ 匯入備份<input type="file" id="lbImport" accept=".json,application/json" hidden></label>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="preview-bar">
            <button class="mini" type="button" onclick="window.print()">🖨 列印</button>
            <button class="mini" type="button" onclick="downloadPreview('lbPreview','作文範文','doc')">⬇ Word</button>
            <button class="mini" type="button" onclick="downloadPdfFromHost('lbPreview','作文範文',false)">⬇ PDF</button>
            <span class="status" id="lbMeta">生成或點開範文庫的一篇，會顯示在這裡。</span>
          </div>
          <div class="preview-host" id="lbPreview"></div>
        </div>
      </div>''')

JS = r'''
    // ============================================================
    // 📗 作文範文庫（2026-11-01）：只收合法來源，資料只存這台電腦
    // ============================================================
    const LB_KEY = 'studio_model_essays_v1';
    const LB_AI_MARK = 'AI 生成示範文，非真實學生作品，僅供教學比較';
    const LB_SOURCES = {
      ai: { label: 'AI 原創示範', rights: '' },
      teacher: { label: '老師自寫', rights: '這篇是我自己寫的，我擁有著作權' },
      colleague: { label: '同事授權', rights: '作者（同事）已同意我在教學中使用這篇' },
      student: { label: '學生佳作（已同意）', rights: '學生與家長已簽同意書，同意匿名在教學中使用' },
      public: { label: '公有領域', rights: '作者過世已超過 50 年，屬公有領域' }
    };
    function lbItems() { try { const a = JSON.parse(localStorage.getItem(LB_KEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
    function lbSave(list) { try { localStorage.setItem(LB_KEY, JSON.stringify(list.slice(-400))); } catch (e) { showToast('範文庫存不下（這台電腦空間不足），請先匯出備份再刪舊的。', true); } }
    function lbSyncSource() {
      const v = $('lbSource').value;
      $('lbRightsText').textContent = LB_SOURCES[v].rights;
      $('lbAuthorRow').hidden = v !== 'public';
      $('lbAnonRow').hidden = v !== 'student';
    }
    $('lbSource').addEventListener('change', lbSyncSource);
    lbSyncSource();
    function lbSheetHtml(item) {
      const tag = LB_SOURCES[item.source] || LB_SOURCES.teacher;
      const paras = String(item.text || '').split(/\n+/).filter(Boolean).map(p => `<p style="font-size:15.5px;line-height:2;text-indent:2em;margin:4px 0">${escapeHtml(p)}</p>`).join('');
      return `<div style="margin-bottom:18px">
        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
          <div style="font-size:19px;font-weight:900">${escapeHtml(item.title || '（無題）')}${item.level ? `<span style="font-size:13px;color:#a33;margin-left:8px">${escapeHtml(item.level)}</span>` : ''}</div>
          <div style="font-size:12px;color:#666">${escapeHtml(item.grade || '')}年級・${escapeHtml(item.genre || '')}・${escapeHtml(tag.label)}${item.author ? '・' + escapeHtml(item.author) : ''}</div>
        </div>
        ${item.source === 'ai' ? `<div style="font-size:12px;color:#a33;border:1px dashed #d99;border-radius:6px;padding:2px 8px;display:inline-block;margin:4px 0">${LB_AI_MARK}</div>` : ''}
        ${paras}
        ${item.analysis ? `<div style="background:#f3f8f5;border-radius:8px;padding:8px 12px;font-size:13.5px;margin-top:6px"><b>為什麼是這個程度：</b>${escapeHtml(item.analysis)}</div>` : ''}
      </div>`;
    }
    function lbShow(items, heading) {
      $('lbPreview').innerHTML = `<div class="sheet">${heading ? `<div class="ws-head"><div class="ws-title">${escapeHtml(heading)}</div></div>` : ''}${items.map(lbSheetHtml).join('<hr style="border:0;border-top:1.5px dashed #ccc;margin:14px 0">')}
        ${items.some(i => i.source === 'ai') ? `<p style="font-size:10.5px;color:#666">${LB_AI_MARK}。評分依據同「作文批改」年段規準（架構參酌會考四向度六級分，描述為本系統自行撰寫）。</p>` : ''}</div>`;
    }
    function lbRender() {
      const list = lbItems().slice().reverse();
      $('lbList').innerHTML = list.length ? list.slice(0, 30).map(i => `<div class="es-rec">
          <span><b>${escapeHtml(i.title || '（無題）')}</b>${i.level ? '・' + escapeHtml(i.level) : ''}<br><span style="color:#888">${escapeHtml(i.grade)}年級・${escapeHtml((LB_SOURCES[i.source] || {}).label || '')}</span></span>
          <span><button class="mini" type="button" data-lb-open="${i.id}">開啟</button> <button class="mini" type="button" data-lb-del="${i.id}">刪除</button></span></div>`).join('')
        : '<div style="font-size:12.5px;color:#888">還沒有範文。可以先用上面的「生成三篇對照範文」。</div>';
    }
    $('lbList').addEventListener('click', event => {
      const open = event.target.closest('[data-lb-open]');
      const del = event.target.closest('[data-lb-del]');
      if (open) { const it = lbItems().find(x => x.id === open.dataset.lbOpen); if (it) lbShow([it]); }
      if (del && window.confirm('刪除這篇範文？')) { lbSave(lbItems().filter(x => x.id !== del.dataset.lbDel)); lbRender(); }
    });
    lbRender();

    $('lbGoButton').dataset.label = $('lbGoButton').textContent;
    $('lbGoButton').addEventListener('click', async () => {
      const topic = $('lbTopic').value.trim();
      if (!topic) return showToast('請先填題目。', true);
      const grade = $('lbGrade').value, band = esBand(grade), r = ES_RUBRICS[band];
      const levels = band === 'low' ? ['⭐⭐⭐', '⭐⭐', '⭐'] : ['5級分', '4級分', '3級分'];
      const prompt = [
        `請為臺灣國小${grade}年級寫三篇題目為「${topic}」的${$('lbGenre').value}示範作文，程度分別是：${levels.join('、')}。`,
        '這是教學用的對照範文：要讓學生比較出好在哪裡、差在哪裡。',
        '【著作權規定】三篇都必須是你自己全新創作的文字：不得引用、改寫或模仿任何已出版的作文、課文、書籍、網路文章或名人作品；不要放名言佳句；人物用一般稱呼（我、媽媽、同學），不要用真實人名或學校名。',
        `【評分規準（${r.label}）】\n${esRubricPrompt(band)}`,
        `每篇的程度要符合上面的規準描述；字數符合${grade}年級（低年級約 80～150 字、中年級 250～400 字、高年級 400～600 字），待加強那篇可以短一點。`,
        'analysis 用 2～3 句，對照規準說明這篇為什麼是這個程度、最明顯的優點或問題在哪一句。',
        '只回傳 JSON：{"essays":[{"level":"' + levels[0] + '","title":"","text":"段落之間用\\n分隔","analysis":""}, …三篇，依程度由高到低]}'
      ].join('\n');
      busy($('lbGoButton'), true);
      try {
        const data = extractJson(await callGemini(prompt, null, $('lbStatus')));
        const now = Date.now();
        const items = (data.essays || []).slice(0, 3).map((e, i) => ({ id: 'm' + (now + i).toString(36), ts: now, source: 'ai', grade, genre: $('lbGenre').value,
          title: String(e.title || topic).slice(0, 40), level: String(e.level || levels[i] || ''), text: String(e.text || ''), analysis: String(e.analysis || '') })).filter(e => e.text);
        if (!items.length) throw new Error('AI 沒有寫出範文，請再試一次。');
        lbSave(lbItems().concat(items));
        lbRender();
        lbShow(items, `對照範文：${topic}`);
        $('lbMeta').textContent = '已存進範文庫。三篇都是 AI 原創示範文，列印時會自動標示。';
        showToast('📗 三篇對照範文完成！');
      } catch (e) { if (e.message !== 'no-key') { $('lbStatus').textContent = ''; showToast(e.message, true); } }
      busy($('lbGoButton'), false);
    });

    $('lbAddButton').addEventListener('click', () => {
      const source = $('lbSource').value;
      const text = $('lbOwnText').value.trim();
      if (!text) return showToast('請先貼上範文。', true);
      if (!$('lbRights').checked) return showToast('要先勾選授權聲明才能加入。來源不確定的文章請不要放進來。', true);
      let author = '';
      if (source === 'public') {
        const year = parseInt($('lbDeathYear').value, 10);
        const limit = new Date().getFullYear() - 51;
        if (!year || year > limit) return showToast(`公有領域要作者過世超過 50 年（卒年 ${limit} 年以前）。這位作者的作品可能還受著作權保護。`, true);
        author = `${$('lbAuthor').value.trim() || '佚名'}（卒於 ${year}）`;
      }
      if (source === 'student' && !$('lbAnon').checked) return showToast('學生佳作要先拿掉姓名、座號、班級等可以認出是誰的資料。', true);
      const item = { id: 'm' + Date.now().toString(36), ts: Date.now(), source, grade: $('lbGrade').value, genre: $('lbGenre').value,
        title: $('lbOwnTitle').value.trim().slice(0, 40) || '（無題）', text, author, rights: LB_SOURCES[source].rights };
      lbSave(lbItems().concat(item));
      lbRender(); lbShow([item]);
      ['lbOwnTitle', 'lbOwnText', 'lbAuthor', 'lbDeathYear'].forEach(id => { $(id).value = ''; });
      $('lbRights').checked = false; $('lbAnon').checked = false;
      showToast('已加入範文庫。');
    });

    $('lbConsentButton').addEventListener('click', () => {
      const host = document.createElement('div');
      host.id = 'lbConsentHost';
      host.hidden = true;
      host.innerHTML = `<div class="sheet"><div class="ws-head"><div class="ws-title">作文作品教學使用同意書</div></div>
        <p style="font-size:15px;line-height:2">親愛的家長您好：</p>
        <p style="font-size:15px;line-height:2;text-indent:2em">孩子這次的作文「＿＿＿＿＿＿＿＿」寫得很好，老師想把它當作班上的作文範例，讓其他同學學習。使用時會<b>拿掉姓名、座號、班級</b>和可以認出是誰的內容，只用在本班（或本校）的作文教學，不會公開上網、不會用在商業用途。</p>
        <p style="font-size:15px;line-height:2;text-indent:2em">著作權仍然屬於孩子。您可以隨時告訴老師撤回同意，老師會把這篇從範文中拿掉。</p>
        <p style="font-size:15px;line-height:2">□ 同意　　□ 不同意</p>
        <p style="font-size:15px;line-height:2">學生簽名：＿＿＿＿＿＿＿　　家長簽名：＿＿＿＿＿＿＿　　日期：＿＿＿＿＿＿</p>
        <p style="font-size:15px;line-height:2;text-align:right">導師：＿＿＿＿＿＿ 敬上</p></div>`;
      document.body.appendChild(host);
      downloadPreview('lbConsentHost', '作文作品教學使用同意書', 'doc');
      setTimeout(() => host.remove(), 1500);
    });

    $('lbExport').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify({ kind: 'studio-model-essays', version: 1, items: lbItems() }, null, 1)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = `作文範文庫備份_${new Date().toISOString().slice(0, 10)}.json`; a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    });
    $('lbImport').addEventListener('change', async () => {
      const file = $('lbImport').files[0];
      if (!file) return;
      try {
        const data = JSON.parse(await file.text());
        const incoming = (data && data.kind === 'studio-model-essays' && Array.isArray(data.items)) ? data.items : null;
        if (!incoming) throw new Error('這不是範文庫的備份檔。');
        const have = new Set(lbItems().map(i => i.id));
        const add = incoming.filter(i => i && i.id && !have.has(i.id) && LB_SOURCES[i.source] && i.text);
        lbSave(lbItems().concat(add)); lbRender();
        showToast(`匯入 ${add.length} 篇（重複的略過）。`);
      } catch (e) { showToast(e.message || '匯入失敗。', true); }
      $('lbImport').value = '';
    });
'''
rep('''    // ============================================================
    // 📋 Google 表單產生器（經老師自己的 GAS 建立）''', JS + '''
    // ============================================================
    // 📋 Google 表單產生器（經老師自己的 GAS 建立）''')

path.write_text(s, encoding='utf-8')
print('ok', len(s))
