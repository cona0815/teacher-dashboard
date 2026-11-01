# -*- coding: utf-8 -*-
"""工作台（Index.html）2026-11 升級：組 A 行政文書。

用法：python tools/upgrade_index_docs_2026_11.py [g7|g9|g8 ...]
不帶參數時依序套用尚未套用的步驟。每個補丁都是 exact-match（錨點必須恰好出現一次），
已套用的步驟用標記字串判斷並略過，可重複執行。

- G7 文書情境包：AI 行政助理新增「📝 行政文書」（簽呈、校內公告、研習心得、新聞稿／臉書貼文、致家長信純文字版）
- G9 晨會／升旗宣導稿：主題＋年級＋時長 → 講稿＋三句重點，可確認後推到大屏提示（既有 prompt_set）
- G8 填報截止橫幅：任務可標「📋 填報／繳交」（存在「下一步行動」開頭的 [填報] 標記，不改試算表欄位）
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "Index.html"


def insert(text, anchor, addition, where="after"):
    count = text.count(anchor)
    assert count == 1, f"錨點應恰好出現一次（實際 {count} 次）：{anchor[:80]!r}"
    if where == "after":
        return text.replace(anchor, anchor + addition, 1)
    if where == "before":
        return text.replace(anchor, addition + anchor, 1)
    if where == "replace":
        return text.replace(anchor, addition, 1)
    raise ValueError(where)


# ---------------------------------------------------------------- G7 ----
G7_MARKER = 'id="aiDocsPanel"'

G7_CSS_ANCHOR = "    .ai-workbench { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 14px; padding: 14px 18px 18px; }\n"
G7_CSS = r"""    /* 📝 行政文書（G7/G9） */
    .ai-docs { margin: 14px 18px 0; border: 2px solid var(--line); border-radius: 18px; background: var(--surface); }
    .ai-docs > summary { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 11px 14px; cursor: pointer; }
    .ai-docs-title { font-size: 14px; font-weight: 900; }
    .ai-docs-body { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 14px; padding: 0 14px 14px; }
    .ai-docs-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
    .ai-docs-row label { color: var(--muted); font-size: 12px; font-weight: 850; white-space: nowrap; }
    .ai-docs-row .select, .ai-docs-row .input { width: auto; flex: 1 1 160px; }
    .ai-docs-status { margin-top: 8px; color: var(--muted); font-size: 12px; font-weight: 800; }
    .ai-docs-status.is-error { color: #a33a2b; }
    .ai-docs-draft-badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; background: var(--gold-soft); color: #73571d; font-size: 12px; font-weight: 900; }
    .ai-docs-output { min-height: 220px; outline: none; border: 1.5px dashed transparent; }
    .ai-docs-output:focus { border-color: var(--primary); }
    @media (max-width: 860px) { .ai-docs-body { grid-template-columns: 1fr; } }
"""

G7_HTML_ANCHOR = '      <div class="ai-workbench">\n'
G7_HTML = r"""      <details class="ai-docs" id="aiDocsPanel">
        <summary><span class="ai-docs-title">📝 行政文書</span><span class="ai-hint">簽呈、校內公告、研習心得、新聞稿／臉書貼文、致家長信（LINE 純文字）｜AI 只出草稿，不會建立任務</span></summary>
        <div class="ai-docs-body">
          <div class="ai-docs-form">
            <div class="ai-docs-row">
              <label for="aiDocType">文書情境</label>
              <select class="select" id="aiDocType">
                <option value="memo">簽呈</option>
                <option value="notice">校內公告</option>
                <option value="reflection">研習心得</option>
                <option value="news">活動新聞稿／學校臉書貼文</option>
                <option value="parentLetter">致家長信（活動通知・LINE 純文字版）</option>
              </select>
            </div>
            <textarea class="textarea" id="aiDocInput" rows="5" placeholder="用幾句話說明要寫什麼；請勿輸入學生姓名。"></textarea>
            <div class="ai-actions">
              <button class="mini-button" type="button" id="aiDocAttachButton">📷 附公文照片／PDF</button>
              <input id="aiDocFileInput" type="file" accept="image/*,.pdf" multiple hidden>
              <span class="ai-hint" id="aiDocFileList">未附檔</span>
              <button class="mini-button" type="button" id="aiDocClearFilesButton" hidden>清除附件</button>
            </div>
            <p class="ai-hint" style="margin:8px 0 0">送出前會先自動去識別化；AI 只產生草稿，不會建立任何任務。</p>
            <div class="ai-actions">
              <button class="button button-dark" type="button" id="aiDocGenerateButton">✍️ 產生草稿</button>
              <button class="button button-light" type="button" id="aiDocRetryButton" hidden>🔁 重試 AI</button>
            </div>
            <div class="ai-docs-status" id="aiDocStatus" role="status"></div>
          </div>
          <div class="ai-docs-result" id="aiDocResultWrap" hidden>
            <div class="ai-pane-label"><span class="ai-docs-draft-badge">草稿，請核對</span><span class="ai-hint">可直接點進下方修改</span><button class="mini-button" type="button" id="aiDocCopyButton">📋 複製</button></div>
            <div class="ai-output ai-docs-output" id="aiDocOutput" contenteditable="true" spellcheck="false" aria-label="行政文書草稿（可編輯）"></div>
          </div>
        </div>
      </details>

"""

G7_JS_ANCHOR = "    // 網頁版舊桌寵已退役；只保留資料相容函式，不啟動動畫、健康計時器或舊面板。\n"
G7_JS = r"""    // ===== 📝 行政文書（G7/G9）：AI 只出草稿；不建任務、不送學生姓名 =====
    const ADMIN_DOC_COMMON_RULES = [
      '一律使用繁體中文與臺灣學校公文、行政文書的慣用語（例如「擬」「請鑒核」「敬陳」「惠請」「本校」）。',
      '不得出現任何學生姓名或可辨識個人的資料；需要提到學生時一律以「學生」「本班學生」「全校學生」代稱。',
      '日期、時間、地點、人數、金額只能來自老師提供的內容或附件；沒有提供就寫「〔請填〕」，不可虛構。',
      '內容由你依老師的輸入原創撰寫，不要引用或抄錄任何現成文章。',
      '只回傳一個 JSON 物件，不要 markdown、不要多餘文字。'
    ];
    const CHINESE_ORDINALS = ['一', '二', '三', '四', '五', '六', '七', '八'];
    function docText(value) {
      return String(value == null ? '' : value).replace(/\*\*/g, '').replace(/^\s*#+\s+/gm, '').trim();
    }
    function docLine(value) {
      return docText(value).replace(/\s*\n\s*/g, ' ') || '〔請填〕';
    }
    function docList(value, count, prefix, exact = false) {
      let items = (Array.isArray(value) ? value : value ? [value] : []).map(docLine).filter(item => item !== '〔請填〕');
      items = items.slice(0, exact ? count : 6);
      while (items.length < count) items.push('〔請填〕');
      return items.map((item, index) => `${prefix(index)}${item}`);
    }
    const docOrdinal = index => `${CHINESE_ORDINALS[index] || index + 1}、`;
    const docNumber = index => `${index + 1}. `;
    function docHashtags(value) {
      const tags = (Array.isArray(value) ? value : String(value || '').split(/\s+/))
        .map(tag => docText(tag).replace(/\s+/g, '').replace(/^#*/, '')).filter(Boolean).slice(0, 3).map(tag => `#${tag}`);
      while (tags.length < 3) tags.push('#〔請填〕');
      return tags.join(' ');
    }
    const ADMIN_DOC_TYPES = {
      memo: {
        label: '簽呈',
        placeholder: '例如：下週三想帶六年級到科博館校外教學，需借用兩台遊覽車，經費由家長會支應。',
        task: '撰寫一份校內簽呈（呈給校長的公文）。主旨一句話說清楚要做什麼，並以「，請鑒核。」收尾；說明分「依據、緣由、內容」三段；擬辦分項列出 2 到 4 點具體做法。',
        schema: '{"subject":"主旨一句","basis":"依據","reason":"緣由","content":"內容","proposals":["擬辦一","擬辦二"]}',
        render: d => [
          '簽呈', '',
          `主旨：${docLine(d.subject)}`, '',
          '說明：',
          `一、依據：${docLine(d.basis)}`,
          `二、緣由：${docLine(d.reason)}`,
          `三、內容：${docLine(d.content)}`, '',
          '擬辦：',
          ...docList(d.proposals, 2, docOrdinal), '',
          '敬陳',
          '校長'
        ]
      },
      notice: {
        label: '校內公告',
        placeholder: '例如：11/20 下午全校防災演練，請各班導師帶隊到操場集合，有問題找學務處。',
        task: '撰寫一則校內公告（給校內同仁或師生看），清楚、精簡、條列。重點剛好三條，每條一句話。',
        schema: '{"title":"公告標題","audience":"公告對象","points":["重點一","重點二","重點三"],"timePlace":"時間地點","contact":"聯絡窗口（處室或職稱）"}',
        render: d => [
          `【公告】${docLine(d.title)}`, '',
          `對象：${docLine(d.audience)}`,
          '重點：',
          ...docList(d.points, 3, docNumber, true),
          `時間地點：${docLine(d.timePlace)}`,
          `聯絡窗口：${docLine(d.contact)}`
        ]
      },
      reflection: {
        label: '研習心得',
        placeholder: '例如：10/30 下午參加「生成式 AI 融入教學」研習，講師示範用 AI 出差異化學習單，我想用在數學課。',
        task: '撰寫一份教師研習心得。內容摘要 80 到 150 字；心得與應用剛好三點，每點具體寫出可以怎麼用在自己的課堂；最後寫一段這次研習對教學的改變。',
        schema: '{"name":"研習名稱","time":"研習時間","summary":"內容摘要","insights":["心得與應用一","心得與應用二","心得與應用三"],"change":"對教學的改變"}',
        render: d => [
          '研習心得', '',
          `研習名稱：${docLine(d.name)}`,
          `研習時間：${docLine(d.time)}`, '',
          '一、內容摘要',
          docText(d.summary) || '〔請填〕', '',
          '二、心得與應用',
          ...docList(d.insights, 3, docNumber, true), '',
          '三、對教學的改變',
          docText(d.change) || '〔請填〕'
        ]
      },
      news: {
        label: '活動新聞稿／學校臉書貼文',
        placeholder: '例如：今天上午三年級到社區淨灘，撿了好幾袋垃圾，學生回來分享很有感。',
        task: '撰寫一則學校活動新聞稿／學校臉書貼文：正文 100 到 200 字，語氣溫暖正向，寫出活動目的與學生的學習收穫，絕不提任何學生姓名；最後附剛好三個 hashtag。',
        schema: '{"title":"標題","body":"正文 100 到 200 字","hashtags":["#標籤一","#標籤二","#標籤三"]}',
        render: d => [
          docLine(d.title), '',
          docText(d.body) || '〔請填〕', '',
          docHashtags(d.hashtags)
        ]
      },
      parentLetter: {
        label: '致家長信（LINE 純文字版）',
        placeholder: '例如：12/5 校外教學到科博館，7:50 到校集合、16:30 回校，要帶午餐和水壺，同意書 11/28 前交回。',
        task: '撰寫一則「致家長的活動通知」純文字版，要能直接貼到 LINE：不要用 markdown 符號（不要 **、#、表格），可用少量 emoji 與換行分段；正文寫活動名稱、時間地點與目的；請家長配合的事項分條列出；語氣禮貌親切。',
        schema: '{"greeting":"親愛的家長您好：","body":"正文（可含換行）","items":["請家長配合的事項"],"closing":"結語與署名，例如 ○年○班導師 敬上"}',
        render: d => [
          docLine(d.greeting || '親愛的家長您好：'), '',
          docText(d.body) || '〔請填〕', '',
          '請家長協助：',
          ...docList(d.items, 1, () => '・'), '',
          docText(d.closing) || '〔請填〕'
        ]
      }
    };
    const adminDocState = { files: [], busy: false };

    function adminDocExtra() {
      return {};
    }

    function buildAdminDocPrompt(type, safeText, extra) {
      const def = ADMIN_DOC_TYPES[type];
      const teacher = assistantSettings.teacher || {};
      const identity = [teacher.title, teacher.grade ? `${teacher.grade}年級` : '', teacher.className ? `${teacher.className}班` : ''].filter(Boolean).join('、');
      return [
        `你是臺灣國小的行政文書助理。今天是 ${localDateString(new Date())}。`,
        identity ? `撰寫者身分：${identity}。` : '',
        `文書類型：${def.label}。`,
        `任務：${typeof def.task === 'function' ? def.task(extra) : def.task}`,
        '規則：',
        ...ADMIN_DOC_COMMON_RULES.map((rule, index) => `${index + 1}. ${rule}`),
        `JSON 格式：${def.schema}`,
        '老師提供的內容（已去識別化，可能以〔遮蔽〕代替敏感字）：',
        safeText || '（老師沒有輸入文字，請依附件內容撰寫）'
      ].filter(Boolean).join('\n');
    }

    async function callAdminDocAi(prompt, files) {
      const cfg = providerConfig();
      if (!cfg.ready) throw new Error('AI 服務尚未設定');
      let response;
      if (cfg.kind === 'gemini') {
        const parts = [{ text: prompt }];
        for (const file of files) parts.push({ inline_data: { mime_type: file.type || 'image/png', data: await fileToBase64(file) } });
        response = await fetch(`${cfg.endpoint}/${cfg.model}:generateContent`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': cfg.key },
          body: JSON.stringify({ contents: [{ role: 'user', parts }], generationConfig: { temperature: 0.5, maxOutputTokens: 8192, responseMimeType: 'application/json' } })
        });
      } else {
        const content = [{ type: 'text', text: prompt }];
        for (const file of files) {
          if (/^image\//.test(file.type)) content.push({ type: 'image_url', image_url: { url: await fileToDataUrl(file) } });
          else content.push({ type: 'text', text: `附件「${file.name}」是 PDF，此服務無法直接讀取；要讀 PDF 請改用 Google Gemini。` });
        }
        response = await fetch(`${cfg.endpoint}/chat/completions`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${cfg.key}` },
          body: JSON.stringify({ model: cfg.model, messages: [{ role: 'user', content }], temperature: 0.5, response_format: { type: 'json_object' } })
        });
      }
      if (!response.ok) throw new Error(`AI 回應錯誤（HTTP ${response.status}）`);
      const data = await response.json();
      const rawText = cfg.kind === 'gemini'
        ? (data?.candidates?.[0]?.content?.parts || []).filter(part => !part.thought).map(part => part.text || '').join('')
        : String(data?.choices?.[0]?.message?.content || '');
      return parseAiJsonText(rawText);
    }

    function setAdminDocStatus(message, isError = false) {
      $('aiDocStatus').textContent = message;
      $('aiDocStatus').classList.toggle('is-error', !!isError);
    }

    function renderAdminDoc(type, data, extra) {
      const def = ADMIN_DOC_TYPES[type];
      $('aiDocOutput').textContent = def.render(data || {}, extra || {}).join('\n');
      $('aiDocOutput').dataset.docType = type;
      $('aiDocResultWrap').hidden = false;
    }

    function adminDocCountNote(type, data) {
      if (type === 'news') {
        const length = docText(data.body).replace(/\s/g, '').length;
        return `正文 ${length} 字（建議 100–200 字）。`;
      }
      return '';
    }

    async function generateAdminDoc() {
      if (adminDocState.busy) return;
      const type = $('aiDocType').value;
      const def = ADMIN_DOC_TYPES[type];
      if (!def) return;
      const raw = $('aiDocInput').value.trim();
      const extra = adminDocExtra(type);
      if (extra.error) return showToast(extra.error, true);
      const cfg = providerConfig();
      if (!cfg.ready) {
        const name = cfg.provider === 'gemini' ? 'Gemini' : (cfg.label || 'AI');
        setAdminDocStatus(`請先到設定填 ${name} 金鑰（⚙ 設定 → ② AI 設定）；下方先放空白格式，可直接手動填寫。`, true);
        $('aiDocRetryButton').hidden = true;
        renderAdminDoc(type, {}, extra);
        showToast(`請先到設定填 ${name} 金鑰。`, true);
        return;
      }
      if (!raw && !adminDocState.files.length && !extra.allowEmpty) return showToast('請先輸入幾句話，或附上公文照片。', true);
      const safe = redactSensitiveText(raw);
      const button = $('aiDocGenerateButton');
      adminDocState.busy = true;
      button.disabled = true;
      $('aiDocRetryButton').hidden = true;
      setAdminDocStatus(`✍️ ${cfg.label} 正在撰寫「${def.label}」草稿……`);
      try {
        const data = await callAdminDocAi(buildAdminDocPrompt(type, safe.text, extra), adminDocState.files);
        renderAdminDoc(type, data, extra);
        setAdminDocStatus(`AI 草稿完成：請逐字核對後再使用。${adminDocCountNote(type, data, extra)}${safe.count ? `（送出前已遮蔽 ${safe.count} 處敏感字）` : ''}`);
        showToast(`📝 ${def.label}草稿完成，請核對。`);
      } catch (error) {
        setAdminDocStatus(`AI 呼叫失敗：${String(error.message || error).slice(0, 120)}。請按「🔁 重試 AI」再試一次。`, true);
        $('aiDocRetryButton').hidden = false;
      } finally {
        adminDocState.busy = false;
        button.disabled = false;
      }
    }

    async function copyAdminDoc() {
      const text = $('aiDocOutput').innerText.trim();
      if (!text) return showToast('還沒有內容可複製。', true);
      try {
        await navigator.clipboard.writeText(text);
      } catch (error) {
        const range = document.createRange();
        range.selectNodeContents($('aiDocOutput'));
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        try { document.execCommand('copy'); } catch (copyError) {}
        selection.removeAllRanges();
      }
      showToast('📋 已複製草稿；貼上前請再核對一次。');
    }

    function renderAdminDocFiles() {
      const files = adminDocState.files;
      $('aiDocFileList').textContent = files.length ? files.map(file => file.name).join('、') : '未附檔';
      $('aiDocClearFilesButton').hidden = !files.length;
    }

    function syncAdminDocType() {
      const def = ADMIN_DOC_TYPES[$('aiDocType').value];
      if (def) $('aiDocInput').placeholder = `${def.placeholder}（請勿輸入學生姓名）`;
    }

    $('aiDocType').addEventListener('change', syncAdminDocType);
    $('aiDocGenerateButton').addEventListener('click', generateAdminDoc);
    $('aiDocRetryButton').addEventListener('click', generateAdminDoc);
    $('aiDocCopyButton').addEventListener('click', copyAdminDoc);
    $('aiDocAttachButton').addEventListener('click', () => $('aiDocFileInput').click());
    $('aiDocFileInput').addEventListener('change', event => {
      const picked = [...(event.target.files || [])].filter(file => /^image\//.test(file.type) || /\.pdf$/i.test(file.name));
      const tooBig = picked.filter(file => file.size > 8 * 1024 * 1024);
      adminDocState.files = picked.filter(file => file.size <= 8 * 1024 * 1024).slice(0, 4);
      if (tooBig.length) showToast('單一附件請小於 8 MB，過大的檔案已略過。', true);
      event.target.value = '';
      renderAdminDocFiles();
    });
    $('aiDocClearFilesButton').addEventListener('click', () => { adminDocState.files = []; renderAdminDocFiles(); });
    syncAdminDocType();
    // ===== 📝 行政文書 END =====

"""

G7_TEST_ANCHOR = None  # 契約測試另外寫在 tests/profile_config.test.js 檔尾


def step_g7(text):
    text = insert(text, G7_CSS_ANCHOR, G7_CSS, "after")
    text = insert(text, G7_HTML_ANCHOR, G7_HTML, "before")
    text = insert(text, G7_JS_ANCHOR, G7_JS, "before")
    return text


# ---------------------------------------------------------------- G9 ----
G9_MARKER = 'id="aiDocSpeechFields"'

G9_REPLACEMENTS = [
    # CSS
    (
        "    .ai-docs-output:focus { border-color: var(--primary); }\n",
        r"""    .ai-docs-output:focus { border-color: var(--primary); }
    .ai-docs-speech { margin-bottom: 4px; }
    .ai-docs-push { margin-top: 10px; padding: 10px 12px; border: 2px solid #b9cbbf; border-radius: 14px; background: #f2f7f2; }
    .ai-docs-push-row { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
    .ai-docs-push-row .input { flex: 1; padding: 6px 8px; }
""",
        "replace",
    ),
    # 摘要文字
    (
        "致家長信（LINE 純文字）｜AI 只出草稿，不會建立任務</span></summary>",
        "致家長信（LINE 純文字）、晨會／升旗宣導稿｜AI 只出草稿，不會建立任務</span></summary>",
        "replace",
    ),
    # 情境選項
    (
        '                <option value="parentLetter">致家長信（活動通知・LINE 純文字版）</option>\n',
        '                <option value="speech">晨會／升旗宣導稿</option>\n',
        "after",
    ),
    # 宣導稿欄位：主題、年級、時長
    (
        '            <textarea class="textarea" id="aiDocInput" rows="5"',
        r"""            <div class="ai-docs-speech" id="aiDocSpeechFields" hidden>
              <div class="ai-docs-row">
                <label for="aiDocSpeechTopic">宣導主題</label>
                <input class="input" id="aiDocSpeechTopic" list="aiDocSpeechTopicList" maxlength="40" placeholder="例如：交通安全（可自己打）">
                <datalist id="aiDocSpeechTopicList"><option value="防災演練"><option value="衛生保健（洗手、防流感）"><option value="交通安全"><option value="品德教育"><option value="節慶由來"><option value="反霸凌"><option value="校園安全"><option value="環境保護"><option value="網路安全"><option value="性別平等"></datalist>
              </div>
              <div class="ai-docs-row">
                <label for="aiDocSpeechGrade">對象</label>
                <select class="select" id="aiDocSpeechGrade"><option value="全校">全校（一到六年級）</option><option value="低年級">低年級</option><option value="中年級">中年級</option><option value="高年級">高年級</option><option value="一年級">一年級</option><option value="二年級">二年級</option><option value="三年級">三年級</option><option value="四年級">四年級</option><option value="五年級">五年級</option><option value="六年級">六年級</option></select>
                <label for="aiDocSpeechMinutes">時長</label>
                <select class="select" id="aiDocSpeechMinutes"><option value="1">1 分鐘（約 250 字）</option><option value="2" selected>2 分鐘（約 500 字）</option><option value="3">3 分鐘（約 750 字）</option></select>
              </div>
            </div>
""",
        "before",
    ),
    # 推到大屏提示
    (
        '            <div class="ai-output ai-docs-output" id="aiDocOutput" contenteditable="true" spellcheck="false" aria-label="行政文書草稿（可編輯）"></div>\n',
        r"""            <div class="ai-docs-push" id="aiDocPushWrap" hidden>
              <div class="ai-section-head"><h4>📣 推到大屏提示</h4><span class="ai-hint">選一句重點（可先改字），確認後才送出</span></div>
              <div id="aiDocPushList"></div>
              <div class="ai-actions">
                <button class="button button-light" type="button" id="aiDocPushButton">📣 推到大屏提示</button>
                <span class="ai-hint" id="aiDocPushHint"></span>
              </div>
            </div>
""",
        "after",
    ),
    # 每分鐘字數
    (
        "    const CHINESE_ORDINALS = ['一', '二', '三', '四', '五', '六', '七', '八'];\n",
        "    const ADMIN_SPEECH_CHARS_PER_MINUTE = 250;  // 晨會講稿：1 分鐘約 250 字\n",
        "after",
    ),
    # 情境定義
    (
        "          docText(d.closing) || '〔請填〕'\n        ]\n      }\n    };\n    const adminDocState = { files: [], busy: false };\n",
        r"""          docText(d.closing) || '〔請填〕'
        ]
      },
      speech: {
        label: '晨會／升旗宣導稿',
        placeholder: '選填：可補充想強調的事，例如：最近下課在走廊奔跑的情況變多',
        task: extra => `撰寫一篇在晨會或升旗時對國小${extra.gradeLabel}學生說的宣導稿，主題是「${extra.topic}」，時長約 ${extra.minutes} 分鐘。講稿正文約 ${extra.targetChars} 字（以每分鐘約 ${ADMIN_SPEECH_CHARS_PER_MINUTE} 字計，誤差不超過 15%），口語、親切、句子短、適合朗讀：開頭向師生問好，中間舉一個貼近校園生活的例子，結尾給一個今天就做得到的行動。另外給三句重點，每句 18 字以內，要能直接貼在教室大屏上提醒學生。`,
        schema: '{"title":"講稿標題","script":"講稿正文（可含換行）","keyPoints":["重點一","重點二","重點三"]}',
        render: (d, extra) => [
          `${docLine(d.title)}（${extra.gradeLabel || '〔對象〕'}・約 ${extra.minutes || 1} 分鐘）`, '',
          docText(d.script) || '〔請填〕', '',
          '三句重點：',
          ...docList(d.keyPoints, 3, docNumber, true)
        ]
      }
    };
    const adminDocState = { files: [], busy: false };
""",
        "replace",
    ),
    # 宣導稿參數
    (
        "    function adminDocExtra() {\n      return {};\n    }\n",
        r"""    function adminDocExtra(type) {
      if (type !== 'speech') return {};
      const topic = $('aiDocSpeechTopic').value.trim();
      if (!topic) return { error: '請先填宣導主題（例如：交通安全）。' };
      const minutes = Math.min(3, Math.max(1, Number($('aiDocSpeechMinutes').value) || 1));
      const grade = $('aiDocSpeechGrade').value || '全校';
      return { topic, minutes, targetChars: minutes * ADMIN_SPEECH_CHARS_PER_MINUTE, gradeLabel: grade === '全校' ? '全校（一到六年級）' : grade, allowEmpty: true };
    }
""",
        "replace",
    ),
    # 渲染後更新推送區
    (
        "      $('aiDocOutput').dataset.docType = type;\n      $('aiDocResultWrap').hidden = false;\n    }\n",
        r"""      $('aiDocOutput').dataset.docType = type;
      $('aiDocResultWrap').hidden = false;
      renderAdminDocPush(type, data || {});
    }

    function renderAdminDocPush(type, data) {
      const wrap = $('aiDocPushWrap');
      if (type !== 'speech') { wrap.hidden = true; return; }
      const points = docList(data.keyPoints, 3, () => '', true).map(point => point === '〔請填〕' ? '' : point);
      $('aiDocPushList').innerHTML = points.map((point, index) => `<div class="ai-docs-push-row"><input type="radio" name="aiDocPushPick" id="aiDocPushPick${index}" value="${index}"${index === 0 ? ' checked' : ''} aria-label="選第 ${index + 1} 句"><input class="input" id="aiDocPushText${index}" data-push-index="${index}" maxlength="40" value="${escapeHtml(point)}" placeholder="重點 ${index + 1}"></div>`).join('');
      const ready = lineBridgeReady();
      $('aiDocPushButton').hidden = !ready;
      $('aiDocPushHint').textContent = ready
        ? '會先跳出確認視窗，按「確定」才送到大屏。'
        : '要推到大屏，請先到「⚙ 設定 → ① 雲端／LINE 小幫手」填好 GAS 網址與 🔑C 並啟用。';
      wrap.hidden = false;
    }

    async function pushAdminDocPoint() {
      const picked = document.querySelector('input[name="aiDocPushPick"]:checked');
      const text = String((picked && $(`aiDocPushText${picked.value}`)?.value) || '').trim().slice(0, 40);
      if (!text) return showToast('請先選一句重點（空白的那句請先填字）。', true);
      if (!lineBridgeReady()) return showToast('要推到大屏，請先到「⚙ 設定 → ① 雲端／LINE 小幫手」填好 GAS 網址與 🔑C 並啟用。', true);
      if (!window.confirm(`確定要把這句送到教室大屏提示嗎？\n\n「${text}」\n\n送出後大屏約 20 秒內切換。`)) {
        showToast('已取消，沒有送到大屏。');
        return;
      }
      const button = $('aiDocPushButton');
      button.disabled = true;
      try {
        await callLineBridge('prompt_set', { text, img: 'class_focus.png' });
        showToast(`📣 已送出：「${text}」，大屏約 20 秒內切換。`);
      } catch (error) {
        showToast(error.message || '送出失敗。', true);
      } finally {
        button.disabled = false;
      }
    }
""",
        "replace",
    ),
    # 宣導稿字數提示
    (
        "    function adminDocCountNote(type, data) {\n",
        r"""    function adminDocCountNote(type, data, extra) {
      if (type === 'speech') {
        const length = docText(data.script).replace(/\s/g, '').length;
        const ratio = length / extra.targetChars;
        const hint = ratio < 0.8 ? '偏短，可再按一次「✍️ 產生草稿」或自行補充。' : ratio > 1.2 ? '偏長，可再按一次「✍️ 產生草稿」或自行刪減。' : '長度合適。';
        return `講稿 ${length} 字（${extra.minutes} 分鐘約 ${extra.targetChars} 字）：${hint}`;
      }
""",
        "replace",
    ),
    # 切換情境時顯示宣導稿欄位
    (
        "      if (def) $('aiDocInput').placeholder = `${def.placeholder}（請勿輸入學生姓名）`;\n",
        "      $('aiDocSpeechFields').hidden = $('aiDocType').value !== 'speech';\n",
        "after",
    ),
    # 事件
    (
        "    syncAdminDocType();\n    // ===== 📝 行政文書 END =====\n",
        r"""    $('aiDocPushButton').addEventListener('click', pushAdminDocPoint);
    $('aiDocPushList').addEventListener('focusin', event => {
      const input = event.target.closest('[data-push-index]');
      if (input) $(`aiDocPushPick${input.dataset.pushIndex}`).checked = true;
    });
""",
        "before",
    ),
]


def step_g9(text):
    for anchor, addition, where in G9_REPLACEMENTS:
        text = insert(text, anchor, addition, where)
    return text


# ---------------------------------------------------------------- G8 ----
# 標記存放位置：任務「下一步行動」（下一步行動欄）開頭加 [填報]。
# 不用 category 的原因：GAS validateTaskPayload_ 會用目前 profile 的「類型」清單驗證 category，
# 新增「填報」類型要改 OFFICE_PROFILES 與 Code.gs，也會和使用者原本選的細項分類互相覆蓋；
# 下一步行動是自由文字（cleanText_ 只整理空白、上限 1000 字），加前綴不改任何欄位與驗證。
G8_MARKER = 'id="filingBanner"'

G8_REPLACEMENTS = [
    # CSS
    (
        "    .today-notes-strip { border: 1.5px solid #e3c988; background: #fffdf4; border-radius: 12px; padding: 8px 12px; margin-bottom: 10px; }\n",
        r"""    .filing-banner { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; width: 100%; margin-bottom: 10px; padding: 9px 12px; border: 1.5px solid #9fc0d8; border-radius: 12px; background: #f1f7fc; color: #1f4d6b; font: inherit; text-align: left; cursor: pointer; }
    .filing-banner[hidden] { display: none; }
    .filing-banner:hover { border-color: #5f93b8; }
    .filing-banner.is-overdue { border-color: #d9826f; background: #fff3f0; color: #a33a2b; }
    .filing-banner-title { font-size: 13px; font-weight: 900; }
    .filing-chip { display: inline-flex; padding: 3px 8px; border: 1px solid #c8dcea; border-radius: 999px; background: #fff; color: #1f4d6b; font-size: 12px; font-weight: 800; }
    .filing-chip.is-overdue { border-color: #a33a2b; background: #a33a2b; color: #fff; }
    .filing-banner-hint { margin-left: auto; font-size: 12px; font-weight: 700; opacity: .8; }
    .filing-badge { display: inline-flex; margin-right: 4px; padding: 1px 6px; border-radius: 999px; background: #e6f0f8; color: #1f4d6b; font-size: 11px; font-weight: 900; }
""",
        "after",
    ),
    # 橫幅
    (
        '        <details class="today-notes-strip" id="todayNotesStrip" hidden>\n',
        '        <button class="filing-banner" type="button" id="filingBanner" hidden></button>\n',
        "before",
    ),
    # 期限篩選
    (
        '              <option value="none">未設定期限</option>\n',
        '              <option value="filing">📋 本週要交的填報</option>\n',
        "after",
    ),
    # 任務表單勾選（沒有 name，不進 FormData；由 formToPayload 轉成前綴）
    (
        '            <textarea class="textarea" id="nextAction" name="nextAction" maxlength="1000" placeholder="現在具體應該做什麼？"></textarea>\n          </div>\n',
        r"""          <div class="field field-wide">
            <label class="check-row" for="taskFilingFlag"><input type="checkbox" id="taskFilingFlag">📋 填報／繳交（線上填報、繳交計畫或成果等；到期前 3 天會出現在任務清單上方「本週要交的填報」）</label>
          </div>
""",
        "after",
    ),
    # 輔助函式
    (
        "      return date >= today && date <= end;\n    }\n",
        r"""
    // 📋 填報／繳交（G8）：標記存在「下一步行動」開頭的 [填報]，不改試算表欄位與類型驗證
    const FILING_MARK = '[填報]';
    const FILING_WINDOW_DAYS = 3;
    function isFilingTask(task) {
      return String(task?.nextAction || '').trimStart().startsWith(FILING_MARK);
    }
    function stripFilingMark(text) {
      const value = String(text || '');
      return value.trimStart().startsWith(FILING_MARK) ? value.trimStart().slice(FILING_MARK.length).replace(/^[ 　]+/, '') : value;
    }
    function applyFilingMark(text, flagged) {
      const clean = stripFilingMark(text);
      return flagged ? `${FILING_MARK} ${clean}`.trimEnd().slice(0, 1000) : clean;
    }
    function filingDaysLeft(task) {
      const date = parseDateOnly(task.dueDate);
      return date ? Math.floor((date - startOfToday()) / 86400000) : null;
    }
    function isFilingDueSoon(task) {
      if (!isFilingTask(task) || ['已完成', '取消', '封存'].includes(task.status) || task.archived === '是') return false;
      const days = filingDaysLeft(task);
      return days !== null && days <= FILING_WINDOW_DAYS;
    }
    function renderFilingBanner() {
      const banner = $('filingBanner');
      if (!banner) return;
      const items = state.tasks.filter(isFilingDueSoon).sort((a, b) => String(a.dueDate).localeCompare(String(b.dueDate)));
      if (!items.length) {
        banner.hidden = true;
        banner.innerHTML = '';
        return;
      }
      const overdue = items.filter(task => filingDaysLeft(task) < 0).length;
      const chips = items.slice(0, 6).map(task => {
        const days = filingDaysLeft(task);
        const when = days < 0 ? `逾期 ${-days} 天` : days === 0 ? '今天截止' : `剩 ${days} 天`;
        return `<span class="filing-chip${days < 0 ? ' is-overdue' : ''}">${escapeHtml(task.name)}｜${escapeHtml(formatDue(task))}（${when}）</span>`;
      }).join('');
      const more = items.length > 6 ? `<span class="filing-chip">…還有 ${items.length - 6} 件</span>` : '';
      banner.innerHTML = `<span class="filing-banner-title">📋 本週要交的填報（${items.length} 件${overdue ? `，逾期 ${overdue} 件` : ''}）</span>${chips}${more}<span class="filing-banner-hint">點一下只看這些</span>`;
      banner.classList.toggle('is-overdue', overdue > 0);
      banner.hidden = false;
    }
""",
        "after",
    ),
    # 每次重畫清單時更新橫幅
    (
        "      const tasks = state.filteredTasks;\n      $('taskMeta').textContent",
        "      const tasks = state.filteredTasks;\n      renderFilingBanner();\n      $('taskMeta').textContent",
        "replace",
    ),
    # 清單「下一步」顯示徽章、隱藏原始標記
    (
        "        const nextAction = task.nextAction || task.progress || '尚未填寫下一步行動';\n",
        "        const nextAction = stripFilingMark(task.nextAction) || task.progress || '尚未填寫下一步行動';\n",
        "replace",
    ),
    (
        'title="點一下看完整說明">${escapeHtml(nextFirst)}',
        'title="點一下看完整說明">${isFilingTask(task) ? \'<span class="filing-badge">📋 填報</span>\' : \'\'}${escapeHtml(nextFirst)}',
        "replace",
    ),
    # 篩選
    (
        "        if (due === 'none' && task.dueDate) return false;\n",
        "        if (due === 'filing' && !isFilingDueSoon(task)) return false;\n",
        "after",
    ),
    # 開表單：勾選框依標記、文字框不顯示標記
    (
        "      Object.keys(defaults).forEach(key => setFormValue(key, values[key]));\n",
        "      $('taskFilingFlag').checked = isFilingTask(values);\n      $('nextAction').value = stripFilingMark(values.nextAction);\n",
        "after",
    ),
    # 存檔：勾選 → 下一步行動加前綴
    (
        "      const payload = Object.fromEntries(formData.entries());\n",
        "      payload.nextAction = applyFilingMark(payload.nextAction, $('taskFilingFlag').checked);\n",
        "after",
    ),
    # 點橫幅套用篩選
    (
        "    $('taskForm').addEventListener('submit', saveCurrentTask);\n",
        r"""    $('filingBanner').addEventListener('click', () => {
      $('dueFilter').value = 'filing';
      applyFilters();
      $('taskTableWrap').scrollIntoView({ behavior: 'smooth', block: 'start' });
      showToast('📋 已篩選「本週要交的填報」；到篩選區按「清除」可看全部任務。');
    });
""",
        "after",
    ),
]


def step_g8(text):
    for anchor, addition, where in G8_REPLACEMENTS:
        text = insert(text, anchor, addition, where)
    return text


STEPS = [
    ("g7", G7_MARKER, step_g7),
    ("g9", G9_MARKER, step_g9),
    ("g8", G8_MARKER, step_g8),
]


def main(argv):
    wanted = [arg.lower() for arg in argv] or [name for name, _, _ in STEPS]
    eol = "\r\n" if b"\r\n" in INDEX.read_bytes()[:4096] else "\n"
    text = INDEX.read_text(encoding="utf-8")  # 通用換行讀入（CRLF → \n），寫回時還原
    for name, marker, func in STEPS:
        if name not in wanted:
            continue
        if marker in text:
            print(f"{name}: 已套用，略過")
            continue
        text = func(text)
        assert marker in text, f"{name}: 套用後找不到標記"
        print(f"{name}: 已套用")
    INDEX.write_text(text, encoding="utf-8", newline=eol)


if __name__ == "__main__":
    main(sys.argv[1:])
