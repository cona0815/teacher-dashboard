/* 答題對戰題庫：解析與整理（Battle.html 大屏、Index.html 工作台共用）2026-11-17
 * 支援 NotebookLM 表格、Excel/試算表貼上（TSV）、CSV（含抽認卡 Front/Back）、「( B ) 1.」考卷格式、Q/A。
 * 存檔與雲端讀回的資料一律經 cleanQ／cleanBank 逐欄整理，不信任外來內容。 */
(function () {
'use strict';
const LET = ['A', 'B', 'C', 'D', 'E', 'F'];
// 讀存檔要逐欄整理（資安：不信任 localStorage 裡的內容）
const str = (v, n) => String(v ?? '').slice(0, n);
function cleanQ(q) {
  if (!q || typeof q !== 'object') return null;
  const text = str(q.q, 300).trim(); if (!text) return null;
  const exp = str(q.exp, 300);
  if (q.kind === 'open') return { kind: 'open', q: text, answer: str(q.answer, 200) || '（老師判斷）', exp };
  if (q.kind === 'tf') return { kind: 'tf', q: text, opts: ['○ 對', '✕ 錯'], ans: q.ans === 1 ? 1 : 0, exp };
  const opts = Array.isArray(q.opts) ? q.opts.slice(0, 6).map(o => str(o, 120)) : [];
  const ans = Number(q.ans);
  if (opts.length < 2 || !Number.isInteger(ans) || ans < 0 || ans >= opts.length) return null;
  return { kind: 'choice', q: text, opts, ans, exp };
}
function cleanBank(b) {
  if (!b || typeof b !== 'object' || !Array.isArray(b.questions)) return null;
  const questions = b.questions.slice(0, 500).map(cleanQ).filter(Boolean);
  return { id: str(b.id, 40).replace(/[^\w-]/g, '') || 'b' + Math.random().toString(36).slice(2), name: str(b.name, 30) || '我的題庫', questions, updated: Number(b.updated) || 0 };
}

// ---- 解析（NotebookLM 表格、Excel 貼上、CSV、一般題目文字） ----
const toHalf = s => String(s ?? '').replace(/[！-～]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0)).replace(/　/g, ' ');
function cleanCell(s) {
  return String(s ?? '').replace(/<br\s*\/?>/gi, ' ').replace(/\*\*|__/g, '').replace(/\[\d+(?:\s*[,，、\-–]\s*\d+)*\]/g, '')
    .replace(/[\u00B9\u00B2\u00B3\u2070-\u2079]+/g, '').replace(/[ \t\r\n\u00a0]+/g, ' ').trim();
}
function isTF(s) {
  const h = toHalf(s).trim().replace(/[()（）\s]/g, '');
  if (/^(○|o|◯|〇|⭕|對|是|正確|true|t|v|✓|✔|yes|y)$/i.test(h)) return 'T';
  if (/^(✕|x|×|╳|✖|❌|錯|否|錯誤|不對|false|f|no|n)$/i.test(h)) return 'F';
  return '';
}
const isLetterAns = s => /^[(（]?\s*[A-Fa-f]\s*[)）]?$/.test(toHalf(s).trim());
function resolveAnswer(a, opts) {
  const h = toHalf(a).trim(); if (!h) return -1;
  let m = h.match(/^[(（]?\s*([A-Fa-f])\s*[)）]?(?:[\s.、:：].*)?$/);
  if (m) { const i = LET.indexOf(m[1].toUpperCase()); if (i < opts.length) return i; }
  m = h.match(/^([1-6])$/); if (m && +m[1] <= opts.length) return +m[1] - 1;
  let i = opts.findIndex(o => o === h); if (i >= 0) return i;
  i = opts.findIndex(o => o.length >= 2 && h.includes(o)); return i;
}
function makeQ(raw) {
  let q = cleanCell(raw.q).replace(/^(?:第\s*)?\d{1,3}\s*(?:題)?\s*[.、．:：)）]\s*/, '');
  const exp = cleanCell(raw.exp || ''), a = cleanCell(raw.ans || '');
  const opts = (raw.opts || []).map(o => cleanCell(o).replace(/^[(（]?\s*[A-Fa-f]\s*[)）.．、:：]\s*/, '')).filter(Boolean);
  if (!q) return null;
  if (opts.length >= 2) {
    if (opts.length === 2 && isTF(opts[0]) === 'T' && isTF(opts[1]) === 'F') {
      const tf = isTF(a), i = tf ? (tf === 'T' ? 0 : 1) : resolveAnswer(a, opts);
      if (i < 0) return { err: '找不到答案', q };
      return { kind: 'tf', q, opts: ['○ 對', '✕ 錯'], ans: i, exp };
    }
    const i = resolveAnswer(a, opts);
    if (i < 0) return { err: a ? `答案「${a}」對不到選項（要寫 A、B、C、D）` : '沒有答案', q };
    return { kind: 'choice', q, opts: opts.slice(0, 6), ans: i, exp };
  }
  const tf = isTF(a);
  if (tf) return { kind: 'tf', q, opts: ['○ 對', '✕ 錯'], ans: tf === 'T' ? 0 : 1, exp };
  if (a) return { kind: 'open', q, answer: a, exp };
  return { err: '沒有答案', q };
}
function headerMap(cells) {
  const m = { opts: [] };
  cells.forEach((c, i) => {
    const h = toHalf(cleanCell(c)).replace(/\s/g, '').toLowerCase();
    if (/^(題目|問題|題幹|題目內容|question|questions|front|正面|q)$/.test(h)) m.q = i;
    else if (/^(選項)?[(（]?[a-f][)）]?$/.test(h) || /^option[a-f]$/.test(h)) m.opts['abcdef'.indexOf(h.match(/([a-f])[)）]?$/)[1])] = i;
    else if (/^(答案|正確答案|正解|解答|answer|back|背面)$/.test(h)) m.ans = i;
    else if (/^(解說|說明|解析|詳解|explanation|理由|補充)$/.test(h)) m.exp = i;
  });
  if (m.q == null) return null;
  const optCols = m.opts.filter(i => i != null);
  if (m.ans == null && optCols.length === 1) { m.ans = optCols[0]; m.opts = []; }
  return (m.ans != null || optCols.length) ? m : null;
}
function rowGuess(cells) {
  while (cells.length && !cleanCell(cells[cells.length - 1])) cells = cells.slice(0, -1);
  const n = cells.length, key = s => isLetterAns(s) || isTF(s);
  if (n < 2) return null;
  if (n === 2) return { q: cells[0], ans: cells[1] };
  if (key(cells[n - 1])) return { q: cells[0], opts: cells.slice(1, n - 1), ans: cells[n - 1] };
  if (key(cells[n - 2])) return { q: cells[0], opts: cells.slice(1, n - 2), ans: cells[n - 2], exp: cells[n - 1] };
  if (n === 3) return { q: cells[0], ans: cells[1], exp: cells[2] };
  return { q: cells[0], opts: cells.slice(1) };
}
function rowsToQs(rows, out) {
  let map = null, no = 0;
  rows.forEach(cells => {
    if (!cells.some(c => cleanCell(c))) return;
    const hm = headerMap(cells); if (hm) { map = hm; return; }
    const raw = map ? { q: cells[map.q], opts: map.opts.filter(i => i != null).map(i => cells[i] || ''), ans: map.ans != null ? cells[map.ans] : '', exp: map.exp != null ? cells[map.exp] : '' } : rowGuess(cells);
    if (!raw) return;
    no++; pushQ(raw, out, no);
  });
}
function pushQ(raw, out, no) {
  const q = makeQ(raw); if (!q) return;
  if (q.err) out.errs.push(`第 ${no} 題：${q.err}（${q.q.slice(0, 16)}…）`); else out.qs.push(q);
}
function parseCSV(t) {
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (q) { if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n') { row.push(f); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  return rows.filter(r => r.some(x => x.trim()));
}
function parseFree(text, out) {
  const list = []; let cur = null, no = 0;
  const start = (q, ans, qa) => { cur = { q, opts: [], ans: ans || '', exp: '', qa: !!qa }; list.push(cur); };
  for (const rawLine of text.split('\n')) {
    const l = rawLine.replace(/^\s*[-*•]\s+/, '').replace(/\*\*/g, '').replace(/^#+\s*/, '').replace(/[Ａ-Ｚａ-ｚ０-９　]/g, c => toHalf(c)).trim();
    if (!l) continue;
    let m;
    if ((m = l.match(/^[(（]\s*([A-Fa-f○Oo◯XxＸ✕╳×])\s*[)）]\s*(\d{1,3})\s*[.、．]\s*(.+)$/))) { start(m[3], m[1]); continue; }
    if ((m = l.match(/^(?:第\s*)?(\d{1,3})\s*(?:題)?\s*[.、．:：)）]\s*(.+)$/))) { start(m[2]); continue; }
    if ((m = l.match(/^(?:Q\d*|問|題目)\s*[:：.]\s*(.+)$/i))) { start(m[1], '', true); continue; }
    if (!cur) continue;
    if (cur.qa && !cur.opts.length && (m = l.match(/^(?:A|答)\s*[:：]\s*(.+)$/i))) { cur.ans = m[1]; continue; }
    if ((m = l.match(/^(?:正確答案|答案|解答|正解|answer|ans)\s*[:：]\s*(.+)$/i))) { cur.ans = m[1]; continue; }
    if ((m = l.match(/^(?:解說|說明|解析|詳解|explanation|理由)\s*[:：]\s*(.+)$/i)) || (m = l.match(/^💡\s*(.+)$/))) { cur.exp = m[1]; continue; }
    const inline = [...l.matchAll(/[(（]\s*([A-Fa-f])\s*[)）]\s*([^(（]*)/g)];
    if (inline.length >= 2) { inline.forEach(x => cur.opts.push(x[2].trim())); continue; }
    if ((m = l.match(/^[(（]?\s*([A-Fa-f])\s*[)）.．、:：]\s*(.+)$/))) { cur.opts.push(m[2]); continue; }
    if (cur.exp) cur.exp += ' ' + l; else if (!cur.opts.length && !cur.ans) cur.q += ' ' + l;
  }
  list.forEach(c => { no++; pushQ(c, out, no); });
}
function parseBankText(text, asCSV) {
  text = String(text || '').replace(/\r\n?/g, '\n').replace(/ /g, ' ');
  const out = { qs: [], errs: [] };
  if (asCSV) { rowsToQs(parseCSV(text), out); return out; }
  const lines = text.split('\n');
  const pipes = lines.filter(l => /^\s*\|/.test(l) && l.split('|').length >= 3);
  if (pipes.length >= 2) {
    rowsToQs(pipes.filter(l => l.replace(/[|:\-\s]/g, '') !== '').map(l => l.trim().replace(/^\|/, '').replace(/\|$/, '').split('|')), out);
    return out;
  }
  const tabs = lines.filter(l => l.includes('\t'));
  if (tabs.length >= 2) { rowsToQs(tabs.map(l => l.split('\t')), out); return out; }
  parseFree(text, out);
  if (!out.qs.length) {
    const rows = parseCSV(text).filter(r => r.length >= 2);
    if (rows.length) { const o2 = { qs: [], errs: [] }; rowsToQs(rows, o2); if (o2.qs.length) return o2; }
  }
  return out;
}
function bankToText(b) {
  const rows = ['| 題目 | A | B | C | D | 答案 | 解說 |', '| --- | --- | --- | --- | --- | --- | --- |'];
  const cell = s => String(s ?? '').replace(/\|/g, '／');
  b.questions.forEach(q => {
    if (q.kind === 'open') rows.push(`| ${cell(q.q)} |  |  |  |  | ${cell(q.answer)} | ${cell(q.exp)} |`);
    else if (q.kind === 'tf') rows.push(`| ${cell(q.q)} |  |  |  |  | ${q.ans === 0 ? '○' : '✕'} | ${cell(q.exp)} |`);
    else { const o = q.opts.slice(0, 4); while (o.length < 4) o.push(''); rows.push(`| ${cell(q.q)} | ${o.map(cell).join(' | ')} | ${LET[q.ans]} | ${cell(q.exp)} |`); }
  });
  return rows.join('\n');
}
const kindCount = qs => { const c = { choice: 0, tf: 0, open: 0 }; qs.forEach(q => c[q.kind]++); return c; };
const kindText = qs => { const c = kindCount(qs); return [c.choice && `選擇 ${c.choice}`, c.tf && `是非 ${c.tf}`, c.open && `問答 ${c.open}`].filter(Boolean).join('、'); };
function answerText(q) { return q.kind === 'open' ? q.answer : q.kind === 'tf' ? (q.ans === 0 ? '○ 對' : '✕ 錯') : `${LET[q.ans]}　${q.opts[q.ans]}`; }
function nlmPrompt(type, grade, n, topic) {
  const tail = '不要加引用編號，表格前後不要有其他文字。';
  const t = String(topic || '').trim().slice(0, 40);
  const from = t ? `請根據來源內容中和「${t}」有關的部分` : '請根據來源內容';
  if (type === 'tf') return `${from}，出 ${n} 題給${grade}學生的是非題，用「表格」輸出。
表格欄位依序是：題目｜答案｜解說
規則：
1. 答案欄只寫 ○ 或 ✕，○ 和 ✕ 的題數差不多
2. 題目 30 字以內，敘述要明確，不要模稜兩可
3. 解說用一句話說明為什麼，20 字左右
4. ${tail}`;
  if (type === 'open') return `${from}，出 ${n} 題給${grade}學生的搶答問答題，用「表格」輸出。
表格欄位依序是：題目｜答案｜解說
規則：
1. 答案要很短（10 字以內），方便老師當場判斷對錯
2. 題目 30 字以內，答案只有一個標準答案
3. 解說用一句話補充，20 字左右
4. ${tail}`;
  return `${from}，出 ${n} 題給${grade}學生的選擇題，用「表格」輸出。
表格欄位依序是：題目｜A｜B｜C｜D｜答案｜解說
規則：
1. 答案欄只寫一個英文字母（A、B、C 或 D），正確答案的位置要平均分散
2. 題目 30 字以內，選項 12 字以內，選項前面不要再寫 A. B. 編號
3. 解說用一句話說明為什麼，20 字左右
4. 不要出「以上皆是」「以上皆非」這種選項
5. ${tail}`;
}
// 讀檔：先試 UTF-8，不行再用 Big5（舊版 Excel 存的 CSV）
function decodeFile(buf) {
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(buf); } catch (err) { text = new TextDecoder('big5').decode(buf); }
  return text.replace(/^﻿/, '');
}
window.BattleBank = Object.freeze({ LET, str, cleanQ, cleanBank, toHalf, cleanCell, parseBankText, bankToText, kindCount, kindText, answerText, nlmPrompt, decodeFile });
})();
