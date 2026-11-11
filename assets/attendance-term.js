/* 學期出缺席統計（2026-11-11，老師反應）——晨間大屏「設定」（存本機時）與教師工作台（接雲端時）共用。
 * - 只用座號，不放姓名。
 * - 學生半途轉入／轉出：「在籍異動」記每個座號的在籍期間，不在籍的日子不算應到，也不算缺席。
 * - 假別：病假、事假、公假、遲到（算出席）、未到。
 * - 上課日＝那天有點名紀錄；老師事後可把某天設為「放假」，那天整天不算。
 * - 匯出 Excel（.xlsx）與 Word（.docx），全部在瀏覽器裡產生，不上傳。
 */
(function () {
  'use strict';
  const STATUSES = ['病假', '事假', '公假', '遲到', '未到'];
  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  const pad = n => String(n).padStart(2, '0');
  const dateKey = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const md = key => `${Number(key.slice(5, 7))}/${Number(key.slice(8, 10))}`;
  const WEEK = ['日', '一', '二', '三', '四', '五', '六'];
  const weekday = key => WEEK[new Date(Number(key.slice(0, 4)), Number(key.slice(5, 7)) - 1, Number(key.slice(8, 10))).getDay()];

  /** 預設學期：8 月～隔年 1 月是上學期，2～7 月是下學期 */
  function defaultTerm(today = new Date()) {
    const y = today.getFullYear(), m = today.getMonth() + 1;
    if (m >= 8) return { start: `${y}-08-01`, end: `${y + 1}-01-31`, name: `${y - 1911} 學年度上學期` };
    if (m === 1) return { start: `${y - 1}-08-01`, end: `${y}-01-31`, name: `${y - 1912} 學年度上學期` };
    return { start: `${y}-02-01`, end: `${y}-07-31`, name: `${y - 1912} 學年度下學期` };
  }

  /** 清理設定（也用在匯入、雲端讀回）：日期格式、座號範圍、數量上限 */
  function normalizeTerm(raw) {
    const base = defaultTerm();
    const r = raw && typeof raw === 'object' ? raw : {};
    const start = DATE_RE.test(r.start) ? r.start : base.start;
    const end = DATE_RE.test(r.end) && r.end >= start ? r.end : (base.end >= start ? base.end : start);
    const holidays = [...new Set((Array.isArray(r.holidays) ? r.holidays : []).filter(d => DATE_RE.test(d)))].sort().slice(-200);
    const enroll = (Array.isArray(r.enroll) ? r.enroll : []).map(e => ({
      seat: Math.round(Number(e && e.seat)),
      from: DATE_RE.test(e && e.from) ? e.from : '',
      to: DATE_RE.test(e && e.to) ? e.to : '',
      note: String((e && e.note) || '').replace(/[<>]/g, '').slice(0, 20)
    })).filter(e => e.seat >= 1 && e.seat <= 99 && (!e.from || !e.to || e.from <= e.to)).slice(0, 80);
    const name = String(r.name || base.name).replace(/[<>]/g, '').slice(0, 30);
    const history = (Array.isArray(r.history) ? r.history : []).slice(-6).map(h => ({
      name: String((h && h.name) || '').replace(/[<>]/g, '').slice(0, 30),
      start: DATE_RE.test(h && h.start) ? h.start : '', end: DATE_RE.test(h && h.end) ? h.end : '',
      holidays: (Array.isArray(h && h.holidays) ? h.holidays : []).filter(d => DATE_RE.test(d)).slice(-200),
      enroll: (Array.isArray(h && h.enroll) ? h.enroll : []).slice(0, 80)
    }));
    const seatCount = Math.min(60, Math.max(0, Math.round(Number(r.seatCount) || 0)));
    const emptySeats = [...new Set((Array.isArray(r.emptySeats) ? r.emptySeats : []).map(Number).filter(n => n >= 1 && n <= 60))].sort((a, b) => a - b);
    return { name, start, end, holidays, enroll, history, seatCount, emptySeats };
  }

  /** 開始新學期：舊的設定收進 history（最多 6 學期），放假日與在籍異動清空 */
  function newTerm(term, today = new Date()) {
    const old = normalizeTerm(term);
    const next = defaultTerm(today);
    const history = [...old.history, { name: old.name, start: old.start, end: old.end, holidays: old.holidays, enroll: old.enroll }].slice(-6);
    return normalizeTerm({ ...next, holidays: [], enroll: [], history, seatCount: old.seatCount, emptySeats: old.emptySeats });
  }

  /**
   * 計算。
   * seats：目前大屏的座號（座號數扣掉空號）；有填在籍異動的座號改照異動算（可一個座號多段＝換人）。
   * schoolDays：有點名紀錄的日期；records：[{date, seat, status}]，沒有紀錄的＝到。
   * tooth：{日期: [已潔牙座號]}——有記潔牙的日子才算潔牙日；請假、未到、不在籍、放假的日子不算應潔牙。
   */
  function compute({ term, seats, schoolDays, records, tooth }) {
    const t = normalizeTerm(term);
    const holidaySet = new Set(t.holidays);
    const inTerm = d => d >= t.start && d <= t.end;
    const allDays = [...new Set((schoolDays || []).filter(d => DATE_RE.test(d) && inTerm(d)))].sort();
    const days = allDays.filter(d => !holidaySet.has(d));
    const status = new Map();
    (records || []).forEach(row => {
      if (!row || !DATE_RE.test(row.date) || !STATUSES.includes(row.status)) return;
      status.set(`${row.date}|${Number(row.seat)}`, row.status);
    });
    const bySeat = new Map();
    t.enroll.forEach(e => { if (!bySeat.has(e.seat)) bySeat.set(e.seat, []); bySeat.get(e.seat).push(e); });
    const periods = [];
    (seats || []).forEach(seat => { if (!bySeat.has(seat)) periods.push({ seat, from: '', to: '', note: '' }); });
    bySeat.forEach(list => list.forEach(e => periods.push(e)));
    periods.sort((a, b) => a.seat - b.seat || (a.from || '').localeCompare(b.from || ''));
    const toothMap = new Map();
    Object.entries(tooth && typeof tooth === 'object' ? tooth : {}).forEach(([d, list]) => {
      if (DATE_RE.test(d) && inTerm(d) && !holidaySet.has(d) && Array.isArray(list) && list.length) toothMap.set(d, new Set(list.map(Number)));
    });
    const toothDays = [...toothMap.keys()].sort();
    const rows = periods.map(p => {
      const from = p.from || t.start, to = p.to || t.end;
      const row = { seat: p.seat, from: p.from, to: p.to, note: p.note, expected: 0, present: 0, 遲到: 0, 病假: 0, 事假: 0, 公假: 0, 未到: 0, toothExpected: 0, toothDone: 0 };
      days.forEach(d => {
        if (d < from || d > to) return;
        row.expected += 1;
        const s = status.get(`${d}|${p.seat}`);
        if (!s || s === '遲到') { row.present += 1; if (s) row.遲到 += 1; } else row[s] += 1;
      });
      toothDays.forEach(d => {
        if (d < from || d > to) return;
        const s = status.get(`${d}|${p.seat}`);
        if (s && s !== '遲到') return;   // 請假、未到那天不用潔牙
        row.toothExpected += 1;
        if (toothMap.get(d).has(p.seat)) row.toothDone += 1;
      });
      const parts = [];
      if (p.from) parts.push(`${md(p.from)} 轉入`);
      if (p.to) parts.push(`${md(p.to)} 轉出`);
      row.label = `${p.seat} 號${parts.length ? `（${parts.join('、')}）` : ''}`;
      return row;
    });
    const sum = key => rows.reduce((n, r) => n + r[key], 0);
    return {
      term: t, days, allDays, holidays: allDays.filter(d => holidaySet.has(d)), rows, toothDays,
      toothCount: Object.fromEntries(toothDays.map(d => [d, toothMap.get(d).size])),
      totals: { expected: sum('expected'), present: sum('present'), 遲到: sum('遲到'), 病假: sum('病假'), 事假: sum('事假'), 公假: sum('公假'), 未到: sum('未到'), toothExpected: sum('toothExpected'), toothDone: sum('toothDone') }
    };
  }

  const pct = (done, all) => all ? `${Math.round(done / all * 100)}%` : '—';
  const BASE_COLUMNS = [['座號', r => r.label], ['應到天數', r => r.expected], ['出席', r => r.present], ['遲到', r => r.遲到], ['病假', r => r.病假], ['事假', r => r.事假], ['公假', r => r.公假], ['未到', r => r.未到]];
  const TOOTH_COLUMNS = [['應潔牙', r => r.toothExpected], ['已潔牙', r => r.toothDone], ['潔牙率', r => pct(r.toothDone, r.toothExpected)]];
  /** 這學期有記潔牙才多出潔牙三欄 */
  const columnsOf = result => [...BASE_COLUMNS, ...(result.toothDays && result.toothDays.length ? TOOTH_COLUMNS : []), ['備註', r => r.note || '']];
  function tableRows(result) {
    const cols = columnsOf(result);
    const total = { ...result.totals, label: '合計', note: '' };
    return [cols.map(c => c[0]), ...result.rows.map(r => cols.map(c => c[1](r))), cols.map(c => c[1](total))];
  }
  function summaryText(result) {
    const t = result.term;
    return `${t.name}｜${md(t.start)}～${md(t.end)}｜上課 ${result.days.length} 天${result.holidays.length ? `（已排除放假 ${result.holidays.length} 天）` : ''}${result.toothDays && result.toothDays.length ? `｜潔牙 ${result.toothDays.length} 天` : ''}`;
  }
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function tableHtml(result) {
    const [head, ...body] = tableRows(result);
    const total = body.pop();
    const cell = (v, i) => `<td${Number(v) > 0 && i >= 3 && i <= 7 ? ' class="at-hit"' : ''}>${esc(v)}</td>`;
    return `<table class="at-table"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead>`
      + `<tbody>${body.map(r => `<tr>${r.map(cell).join('')}</tr>`).join('')}</tbody>`
      + `<tfoot><tr>${total.map(v => `<th>${esc(v)}</th>`).join('')}</tr></tfoot></table>`;
  }

  // ---------- ZIP（只打包不壓縮）----------
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  const crc32 = d => { let c = 0xFFFFFFFF; for (let i = 0; i < d.length; i++) c = CRC[(c ^ d[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
  function makeZip(files, mime) {
    const enc = new TextEncoder(), parts = [], central = [];
    const now = new Date();
    const time = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
    const date = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
    let offset = 0;
    files.forEach(([path, text]) => {
      const name = enc.encode(path), data = enc.encode(text), crc = crc32(data);
      const h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(10, time, true); h.setUint16(12, date, true);
      h.setUint32(14, crc, true); h.setUint32(18, data.length, true); h.setUint32(22, data.length, true); h.setUint16(26, name.length, true);
      parts.push(h.buffer, name, data);
      const c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true); c.setUint16(12, time, true); c.setUint16(14, date, true);
      c.setUint32(16, crc, true); c.setUint32(20, data.length, true); c.setUint32(24, data.length, true); c.setUint16(28, name.length, true); c.setUint32(42, offset, true);
      central.push(c.buffer, name);
      offset += 30 + name.length + data.length;
    });
    const size = central.reduce((n, p) => n + p.byteLength, 0);
    const e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, size, true); e.setUint32(16, offset, true);
    return new Blob([...parts, ...central, e.buffer], { type: mime });
  }
  const xml = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '');
  const HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>';

  /** Excel：第一頁統計表、第二頁上課日與放假日 */
  function exportXlsx(result, title) {
    const colName = i => String.fromCharCode(65 + i);
    const sheet = rows => `${HEAD}<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cols><col min="1" max="1" width="24" customWidth="1"/><col min="2" max="12" width="10" customWidth="1"/></cols><sheetData>`
      + rows.map((row, r) => `<row r="${r + 1}">${row.map((v, c) => {
        const ref = `${colName(c)}${r + 1}`;
        return typeof v === 'number' ? `<c r="${ref}"><v>${v}</v></c>` : `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${xml(v)}</t></is></c>`;
      }).join('')}</row>`).join('') + '</sheetData></worksheet>';
    const statRows = [[title], [summaryText(result)], [], ...tableRows(result), [], ['說明：只用座號；遲到算出席；放假日與不在籍的日子不列入應到天數；請假、未到那天不列入應潔牙。']];
    const hasTooth = result.toothDays && result.toothDays.length;
    const dayRows = [['日期', '星期', '類型', ...(hasTooth ? ['潔牙人數'] : [])], ...result.allDays.map(d => [d, weekday(d), result.holidays.includes(d) ? '放假（不列入）' : '上課',
      ...(hasTooth ? [result.toothCount[d] || 0] : [])])];
    const wb = `${HEAD}<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="出缺席統計" sheetId="1" r:id="rId1"/><sheet name="上課日" sheetId="2" r:id="rId2"/></sheets></workbook>`;
    const wbRels = `${HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>`;
    const types = `${HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>`;
    const rels = `${HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`;
    return makeZip([['[Content_Types].xml', types], ['_rels/.rels', rels], ['xl/workbook.xml', wb], ['xl/_rels/workbook.xml.rels', wbRels],
      ['xl/worksheets/sheet1.xml', sheet(statRows)], ['xl/worksheets/sheet2.xml', sheet(dayRows)]], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  }

  /** Word：A4 直式，標題＋說明＋表格 */
  function exportDocx(result, title) {
    const run = (text, bold, size) => `<w:r><w:rPr>${bold ? '<w:b/>' : ''}${size ? `<w:sz w:val="${size}"/>` : ''}</w:rPr><w:t xml:space="preserve">${xml(text)}</w:t></w:r>`;
    const para = (text, bold, size, center) => `<w:p><w:pPr>${center ? '<w:jc w:val="center"/>' : ''}<w:spacing w:after="120"/></w:pPr>${run(text, bold, size)}</w:p>`;
    const all = tableRows(result);
    const widths = all[0].length > 9 ? [1900, 800, 650, 600, 600, 600, 600, 600, 700, 700, 700, 900] : [2400, 900, 800, 700, 700, 700, 700, 700, 1300];
    const cellXml = (v, i, bold) => `<w:tc><w:tcPr><w:tcW w:w="${widths[i]}" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="${i ? 'center' : 'left'}"/></w:pPr>${run(v, bold, 20)}</w:p></w:tc>`;
    const border = '<w:top w:val="single" w:sz="4" w:color="888888"/><w:left w:val="single" w:sz="4" w:color="888888"/><w:bottom w:val="single" w:sz="4" w:color="888888"/><w:right w:val="single" w:sz="4" w:color="888888"/><w:insideH w:val="single" w:sz="4" w:color="888888"/><w:insideV w:val="single" w:sz="4" w:color="888888"/>';
    const table = `<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>${border}</w:tblBorders></w:tblPr><w:tblGrid>${widths.map(w => `<w:gridCol w:w="${w}"/>`).join('')}</w:tblGrid>`
      + all.map((row, r) => `<w:tr>${r === 0 ? '<w:trPr><w:tblHeader/></w:trPr>' : ''}${row.map((v, i) => cellXml(v, i, r === 0 || r === all.length - 1)).join('')}</w:tr>`).join('') + '</w:tbl>';
    const holidayText = result.holidays.length ? `放假（不列入）：${result.holidays.map(md).join('、')}` : '';
    const body = para(title, true, 32, true) + para(summaryText(result), false, 22, true) + table
      + para('說明：只用座號；遲到算出席；放假日與不在籍的日子不列入應到天數；請假、未到那天不列入應潔牙。', false, 18) + (holidayText ? para(holidayText, false, 18) : '');
    const doc = `${HEAD}<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>${body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1000" w:right="900" w:bottom="1000" w:left="900" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr></w:body></w:document>`;
    const styles = `${HEAD}<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="微軟正黑體" w:cs="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>`;
    const types = `${HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>`;
    const rels = `${HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>`;
    const docRels = `${HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`;
    return makeZip([['[Content_Types].xml', types], ['_rels/.rels', rels], ['word/document.xml', doc], ['word/styles.xml', styles], ['word/_rels/document.xml.rels', docRels]],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
  }

  function download(blob, filename) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }

  /**
   * 共用面板：學期起訖、上課日清單（可點「設為放假」）、在籍異動、統計表、匯出、開始新學期。
   * host：要放面板的元素；opts.load() 回 {term, seats, schoolDays, records, className}；opts.save(term) 存設定；opts.title 檔名前綴。
   */
  const STYLE = `.at-panel{display:grid;gap:10px}.at-row{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.at-row label,.at-erow label{display:inline-flex;gap:6px;align-items:center;font-weight:700;font-size:14px}
.at-input{border:1.5px solid var(--line,#d8d2c4);border-radius:8px;padding:5px 8px;font:inherit;background:var(--surface,#fff);color:inherit}
.at-btn{border:1.5px solid var(--line,#d8d2c4);background:var(--surface,#fff);color:inherit;border-radius:9px;padding:6px 12px;font:inherit;font-weight:800;cursor:pointer}
.at-main{background:var(--primary,#1f514a);border-color:var(--primary,#1f514a);color:#fff}.at-warn{border-color:#c0392b;color:#c0392b}
.at-meta,.at-note{font-size:13px;color:var(--muted,#6b6b6b);line-height:1.6}
.at-wrap{overflow:auto;max-height:460px;border:1px solid var(--line,#d8d2c4);border-radius:10px}
.at-table{border-collapse:collapse;width:100%;font-size:14px;background:var(--surface,#fff)}
.at-table th,.at-table td{border-bottom:1px solid var(--line,#e6e0d4);padding:6px 8px;text-align:center;white-space:nowrap}
.at-table th:first-child,.at-table td:first-child{text-align:left}.at-table thead th{position:sticky;top:0;background:var(--surface-2,#f4efe4)}
.at-table tfoot th{background:var(--surface-2,#f4efe4)}.at-table td.at-hit{color:#b3261e;font-weight:800}
.at-box{border:1.5px dashed var(--line,#d8d2c4);border-radius:10px;padding:8px 12px}.at-box summary{cursor:pointer;font-weight:800}
.at-days{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.at-day{border:1.5px solid #9cc5a1;background:#eef8ef;color:#1d5c2a;border-radius:8px;padding:4px 8px;font:inherit;font-size:13px;cursor:pointer}
.at-day.off{border-color:#c9c2b4;background:#ece8df;color:#77705f;text-decoration:line-through}
.at-erow{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:6px 0;border-bottom:1px dashed var(--line,#e6e0d4)}`;
  function mountPanel(host, opts) {
    if (!document.getElementById('at-style')) { const st = document.createElement('style'); st.id = 'at-style'; st.textContent = STYLE; document.head.appendChild(st); }
    let data = null, term = null;
    host.classList.add('at-panel');
    host.innerHTML = `<div class="at-row"><label>學期名稱 <input class="at-input" data-at="name" maxlength="30"></label>
        <label>開始 <input class="at-input" type="date" data-at="start"></label><label>結束 <input class="at-input" type="date" data-at="end"></label>
        <button type="button" class="at-btn" data-at-act="reload">🔄 重新統計</button></div>
      ${opts.seatControl ? `<div class="at-row"><label>座號到 <input class="at-input" type="number" min="1" max="60" data-at="seatCount" style="width:70px"> 號</label>
        <label>空號 <input class="at-input" data-at="emptySeats" placeholder="例：4、13" style="width:140px"></label><span class="at-note">（跟教室大屏的設定一樣填）</span></div>` : ''}
      <div class="at-meta" data-at="meta"></div>
      <div class="at-wrap" data-at="table"></div>
      <div class="at-row"><button type="button" class="at-btn at-main" data-at-act="xlsx">⬇ 匯出 Excel</button><button type="button" class="at-btn at-main" data-at-act="docx">⬇ 匯出 Word</button></div>
      <details class="at-box"><summary>🗓 上課日與放假（那天放假卻被記成未到，點一下改成放假）</summary><div class="at-days" data-at="days"></div></details>
      <details class="at-box"><summary>👥 在籍異動（轉入、轉出、座號換人）</summary>
        <div class="at-note">只填有變動的座號。轉入日空白＝學期一開始就在；轉出日空白＝現在還在。同一個座號換了人，就填兩列。</div>
        <div data-at="enroll"></div><button type="button" class="at-btn" data-at-act="addEnroll">＋ 新增一列</button></details>
      <details class="at-box"><summary>🆕 開始新學期</summary>
        <div class="at-note">學期初按一次：學期起訖換成新學期，放假日與在籍異動清空重來。舊學期的點名紀錄不會刪，改回舊日期還是查得到。</div>
        <button type="button" class="at-btn at-warn" data-at-act="newTerm">🆕 開始新學期</button></details>`;
    const q = sel => host.querySelector(`[data-at="${sel}"]`);
    function persist() { term = normalizeTerm(term); return Promise.resolve(opts.save(term)).catch(e => { q('meta').textContent = `⚠️ 設定沒存成功：${e.message || e}`; }); }
    function renderEnroll() {
      q('enroll').innerHTML = term.enroll.length ? term.enroll.map((e, i) => `<div class="at-erow" data-i="${i}">
        <label>座號 <input class="at-input" type="number" min="1" max="99" value="${e.seat}" data-ef="seat" style="width:64px"></label>
        <label>轉入日 <input class="at-input" type="date" value="${e.from}" data-ef="from"></label>
        <label>轉出日 <input class="at-input" type="date" value="${e.to}" data-ef="to"></label>
        <label>備註 <input class="at-input" maxlength="20" value="${esc(e.note)}" data-ef="note" placeholder="例：轉學" style="width:110px"></label>
        <button type="button" class="at-btn" data-at-act="delEnroll" aria-label="刪除這列">✕</button></div>`).join('') : '<div class="at-note">目前沒有異動，全班整學期都在。</div>';
    }
    function render() {
      if (!data) return;
      const seats = opts.seatControl && term.seatCount
        ? Array.from({ length: term.seatCount }, (_, i) => i + 1).filter(n => !term.emptySeats.includes(n))
        : data.seats;
      const result = compute({ term, seats, schoolDays: data.schoolDays, records: data.records, tooth: data.tooth });
      q('name').value = term.name; q('start').value = term.start; q('end').value = term.end;
      if (opts.seatControl) { q('seatCount').value = term.seatCount || (data.seats || []).length || ''; q('emptySeats').value = term.emptySeats.join('、'); }
      q('meta').textContent = `${summaryText(result)}｜${data.source || ''}`;
      q('table').innerHTML = result.rows.length ? tableHtml(result) : '<div class="at-note">還沒有座號。請先在大屏「設定」填座號數。</div>';
      q('days').innerHTML = result.allDays.length ? result.allDays.slice().reverse().map(d => {
        const off = term.holidays.includes(d);
        return `<button type="button" class="at-day${off ? ' off' : ''}" data-day="${d}">${md(d)}（${weekday(d)}）${off ? '放假' : '上課'}</button>`;
      }).join('') : '<div class="at-note">這學期還沒有點名紀錄。</div>';
      renderEnroll();
      host._lastResult = result;
    }
    async function reload() {
      q('meta').textContent = '讀取中……';
      try {
        data = await opts.load();
        term = normalizeTerm(data.term);
        render();
      } catch (e) { q('meta').textContent = `⚠️ 讀取失敗：${e.message || e}`; }
    }
    host.addEventListener('change', event => {
      if (!term) return;
      const t = event.target;
      if (t.dataset.at === 'name') term.name = t.value;
      else if (t.dataset.at === 'start' || t.dataset.at === 'end') term[t.dataset.at] = t.value;
      else if (t.dataset.at === 'seatCount') term.seatCount = Number(t.value);
      else if (t.dataset.at === 'emptySeats') term.emptySeats = String(t.value).split(/[、,，\s]+/).map(Number).filter(Boolean);
      else if (t.dataset.ef) {
        const i = Number(t.closest('[data-i]').dataset.i);
        term.enroll[i][t.dataset.ef] = t.dataset.ef === 'seat' ? Number(t.value) : t.value;
      } else return;
      term = normalizeTerm(term);
      // 改學期起訖：存好後重新讀（接雲端時要重抓這段日期的紀錄）
      if (t.dataset.at === 'start' || t.dataset.at === 'end') { persist().then(reload); return; }
      // 等這次輸入事件跑完再重畫（重畫會移掉正在輸入的欄位，同步做會和 blur 打架）
      clearTimeout(host._atTimer);
      host._atTimer = setTimeout(render, 0);
      persist();
    });
    host.addEventListener('click', event => {
      const day = event.target.closest('[data-day]');
      if (day && term) {
        const d = day.dataset.day;
        term.holidays = term.holidays.includes(d) ? term.holidays.filter(x => x !== d) : [...term.holidays, d];
        term = normalizeTerm(term); render(); persist(); return;
      }
      const act = event.target.closest('[data-at-act]');
      if (!act) return;
      const a = act.dataset.atAct;
      if (a === 'reload') return reload();
      if (!term) return;
      const file = `${opts.title || '出缺席'}_${term.name}`.replace(/[\\/:*?"<>|]/g, '_');
      if (a === 'xlsx') return download(exportXlsx(host._lastResult, `${data.className || ''} ${term.name} 出缺席統計`.trim()), `${file}.xlsx`);
      if (a === 'docx') return download(exportDocx(host._lastResult, `${data.className || ''} ${term.name} 出缺席統計`.trim()), `${file}.docx`);
      if (a === 'addEnroll') { term.enroll.push({ seat: 1, from: '', to: '', note: '' }); renderEnroll(); return; }
      if (a === 'delEnroll') { term.enroll.splice(Number(act.closest('[data-i]').dataset.i), 1); term = normalizeTerm(term); render(); persist(); return; }
      if (a === 'newTerm') {
        if (!window.confirm(`確定開始新學期？\n「${term.name}」的放假日與在籍異動會收進紀錄，統計改從新學期算。點名紀錄不會刪。`)) return;
        term = newTerm(term); persist().then(reload);
      }
    });
    reload();
    return { reload };
  }

  window.AttendanceTerm = { STATUSES, defaultTerm, normalizeTerm, newTerm, compute, tableRows, tableHtml, summaryText, exportXlsx, exportDocx, download, mountPanel };
})();
