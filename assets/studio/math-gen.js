/* 教材小工場：🔢 數學出題小幫手的出題引擎
   - 計算題由程式出、答案由程式算（分數、小數都用有理數精確計算），不靠 AI，所以答案一定對
   - 應用題由 AI 出，但 AI 要附算式，系統用 evaluate() 驗算，答案對不上就標出來給老師看
   瀏覽器：window.MathGen；Node 測試：require('../assets/studio/math-gen.js') */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MathGen = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------- 可重現的亂數：同一個號碼＝同一份卷（A／B 卷就是號碼 +1） ----------
  function makeRng(seed) {
    let a = seed >>> 0;
    const next = () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const int = (lo, hi) => lo + Math.floor(next() * (hi - lo + 1));
    const pick = list => list[Math.floor(next() * list.length)];
    const digits = n => int(10 ** (n - 1), 10 ** n - 1);
    return { next, int, pick, digits };
  }

  // ---------- 有理數 ----------
  const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b); while (b) [a, b] = [b, a % b]; return a; };
  const lcm = (a, b) => a / gcd(a, b) * b;
  function Q(n, d) {
    if (d === undefined) d = 1;
    if (d === 0) throw new Error('除數不能是 0');
    if (d < 0) { n = -n; d = -d; }
    const g = gcd(n, d) || 1;
    return { n: n / g, d: d / g };
  }
  const add = (x, y) => Q(x.n * y.d + y.n * x.d, x.d * y.d);
  const sub = (x, y) => Q(x.n * y.d - y.n * x.d, x.d * y.d);
  const mul = (x, y) => Q(x.n * y.n, x.d * y.d);
  const div = (x, y) => Q(x.n * y.d, x.d * y.n);
  const eq = (x, y) => x.n === y.n && x.d === y.d;
  const isInt = x => x.d === 1;
  // 小數：整數 n 除以 10^places
  const dec = (n, places) => Q(n, 10 ** places);
  // 小數題裡的小數要真的有小數位（不要出現 2.0 被約成 2 的「小數 × 整數」）
  const realDec = (r, lo, hi, places) => { let q; do q = dec(r.int(lo, hi), places); while (isInt(q)); return q; };

  // ---------- 驗算：看得懂 + − × ÷ ( )、小數、分數 a/b、帶分數「2又1/3」 ----------
  function evaluate(expr) {
    let s = String(expr == null ? '' : expr)
      .replace(/\s+/g, '')
      .replace(/[（]/g, '(').replace(/[）]/g, ')')
      .replace(/[＋]/g, '+').replace(/[−－–—]/g, '-')
      .replace(/[＊*xX╳]/g, '×').replace(/[／]/g, '/')
      .replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFF10 + 48))
      .replace(/[．]/g, '.')
      .replace(/[＝=]+$/, '');
    s = s.replace(/(\d+)又(\d+)\/(\d+)/g, '($1+$2/$3)');
    let i = 0;
    const peek = () => s[i];
    function primary() {
      if (peek() === '(') {
        i += 1;
        const v = sum();
        if (s[i] !== ')') throw new Error('括號沒有對齊');
        i += 1;
        return v;
      }
      if (peek() === '-') { i += 1; const v = primary(); return Q(-v.n, v.d); }
      const m = /^\d+(?:\.\d+)?/.exec(s.slice(i));
      if (!m) throw new Error('看不懂算式：' + (s.slice(i, i + 8) || '（空的）'));
      i += m[0].length;
      const [whole, frac = ''] = m[0].split('.');
      const value = Q(Number(whole + frac), 10 ** frac.length);
      // 數字緊接「/數字」是一個分數（分數線比 ÷ 先算：3/4÷1/4 ＝ (3/4)÷(1/4)）
      const bar = /^\/(\d+)/.exec(s.slice(i));
      if (bar) { i += bar[0].length; return div(value, Q(Number(bar[1]))); }
      return value;
    }
    function product() {
      let v = primary();
      while (peek() === '×' || peek() === '÷' || peek() === '/') {
        const op = s[i]; i += 1;
        const r = primary();
        v = op === '×' ? mul(v, r) : div(v, r);
      }
      return v;
    }
    function sum() {
      let v = product();
      while (peek() === '+' || peek() === '-') {
        const op = s[i]; i += 1;
        const r = product();
        v = op === '+' ? add(v, r) : sub(v, r);
      }
      return v;
    }
    const v = sum();
    if (i !== s.length) throw new Error('算式有多出來的字：' + s.slice(i));
    return v;
  }
  // AI 的答案可能帶單位（12公尺）：只取開頭的數字部分再算
  function parseAnswer(text) {
    const m = /^[\s]*[-−]?[0-9０-９][0-9０-９.．\/／又]*/.exec(String(text == null ? '' : text));
    if (!m) throw new Error('答案不是數字');
    return evaluate(m[0]);
  }

  // ---------- 顯示 ----------
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // 分數顯示：mixed＝帶分數（國小慣用）、improper＝假分數
  function fracText(q, style) {
    if (isInt(q)) return String(q.n);
    const sign = q.n < 0 ? '-' : '';
    const n = Math.abs(q.n);
    if (style !== 'improper' && n > q.d) return `${sign}${Math.floor(n / q.d)}又${n % q.d}/${q.d}`;
    return `${sign}${n}/${q.d}`;
  }
  function fracHtml(q, style) {
    if (isInt(q)) return String(q.n);
    const n = Math.abs(q.n);
    const sign = q.n < 0 ? '-' : '';
    const stack = (a, b) => `<span class="mf-f"><span>${a}</span><span>${b}</span></span>`;
    // data-word-text：存 Word 時換成文字（Word 不認得上下疊的寫法）
    if (style !== 'improper' && n > q.d) {
      return `<span class="mf" data-word-text="${esc(fracText(q, style))}">${sign}<span class="mf-w">${Math.floor(n / q.d)}</span>${stack(n % q.d, q.d)}</span>`;
    }
    return `<span class="mf" data-word-text="${esc(fracText(q, style))}">${sign}${stack(n, q.d)}</span>`;
  }
  // 小數顯示：分母是 2、5 的乘積才寫成小數，否則退回分數
  function decText(q) {
    let k = 0;
    while (k < 9 && (10 ** k) % q.d !== 0) k += 1;   // 最少要幾位小數（已約分，所以最後一位不會是 0）
    if ((10 ** k) % q.d !== 0) return fracText(q, 'improper');
    const scaled = q.n * (10 ** k / q.d);
    if (!k) return String(scaled);
    const sign = scaled < 0 ? '-' : '';
    const s = String(Math.abs(scaled)).padStart(k + 1, '0');
    return `${sign}${s.slice(0, -k)}.${s.slice(-k)}`;
  }
  function numText(q, mode, style) { return mode === 'dec' ? decText(q) : mode === 'frac' ? fracText(q, style) : String(q.n); }
  function numHtml(q, mode, style) { return mode === 'frac' && !isInt(q) ? fracHtml(q, style) : esc(numText(q, mode, style)); }

  // ---------- 題型 ----------
  // grade：建議年級（依 108 課綱國小數學大致的學習順序，老師可以跨年級勾）
  // gen(r) 回傳 { terms:[有理數…], ops:['+'…], mode:'int'|'frac'|'dec', answer, vertical? } 或特殊題型
  const KINDS = [];
  const kind = (id, grade, label, gen, extra) => KINDS.push(Object.assign({ id, grade, label, gen }, extra || {}));
  const I = n => Q(n);
  const two = (a, op, b, mode, ans, more) => Object.assign({ terms: [a, b], ops: [op], mode, answer: ans }, more || {});

  kind('add10', 1, '10 以內的加法', r => { const a = r.int(1, 9), b = r.int(1, 10 - a); return two(I(a), '+', I(b), 'int', I(a + b)); });
  kind('sub10', 1, '10 以內的減法', r => { const a = r.int(2, 10), b = r.int(1, a - 1); return two(I(a), '-', I(b), 'int', I(a - b)); });
  kind('add20', 1, '20 以內的進位加法', r => { const a = r.int(2, 9), b = r.int(11 - a, 9); return two(I(a), '+', I(b), 'int', I(a + b)); });
  kind('sub20', 1, '20 以內的退位減法', r => { const b = r.int(2, 9), a = r.int(11, 9 + b); return two(I(a), '-', I(b), 'int', I(a - b)); }, { note: '個位不夠減，要退位' });
  kind('add100', 2, '二位數的加法', r => { const a = r.int(10, 89), b = r.int(10, 99 - a); return two(I(a), '+', I(b), 'int', I(a + b), { vertical: true }); });
  kind('sub100', 2, '二位數的減法', r => { const a = r.int(20, 99), b = r.int(10, a - 1); return two(I(a), '-', I(b), 'int', I(a - b), { vertical: true }); });
  kind('mul99', 2, '九九乘法', r => { const a = r.int(2, 9), b = r.int(1, 9); return two(I(a), '×', I(b), 'int', I(a * b)); });
  kind('add3', 3, '多位數的加法（三、四位數）', r => { const a = r.digits(r.int(3, 4)), b = r.digits(r.int(3, 4)); return two(I(a), '+', I(b), 'int', I(a + b), { vertical: true }); });
  kind('sub3', 3, '多位數的減法（三、四位數）', r => { const a = r.digits(r.int(3, 4)), b = r.int(100, a - 1); return two(I(a), '-', I(b), 'int', I(a - b), { vertical: true }); });
  kind('mul1', 3, '多位數 × 一位數', r => { const a = r.digits(r.int(2, 4)), b = r.int(2, 9); return two(I(a), '×', I(b), 'int', I(a * b), { vertical: true }); });
  kind('div1', 3, '÷ 一位數（整除）', r => { const b = r.int(2, 9), q = r.int(10, 999); return two(I(b * q), '÷', I(b), 'int', I(q)); });
  kind('div1r', 3, '÷ 一位數（有餘數）', r => {
    const b = r.int(2, 9), q = r.int(10, 300), rem = r.int(1, b - 1);
    return { special: 'rem', dividend: b * q + rem, divisor: b, quot: q, rem };
  }, { wide: true });
  kind('fracSame', 3, '同分母分數的加減', r => {
    const d = r.int(3, 12);
    if (r.next() < 0.5) { const a = r.int(1, d - 1), b = r.int(1, d - 1); return two(Q(a, d), '+', Q(b, d), 'frac', Q(a + b, d), { raw: [[a, d], [b, d]] }); }
    const a = r.int(2, d - 1), b = r.int(1, a - 1);
    return two(Q(a, d), '-', Q(b, d), 'frac', Q(a - b, d), { raw: [[a, d], [b, d]] });
  });
  kind('mul2', 4, '多位數 × 二位數', r => { const a = r.digits(r.int(2, 3)), b = r.int(11, 99); return two(I(a), '×', I(b), 'int', I(a * b), { vertical: true }); });
  kind('div2', 4, '÷ 二位數', r => {
    const b = r.int(11, 99), q = r.int(2, 99), rem = r.next() < 0.5 ? 0 : r.int(1, b - 1);
    return rem ? { special: 'rem', dividend: b * q + rem, divisor: b, quot: q, rem } : two(I(b * q), '÷', I(b), 'int', I(q));
  }, { wide: true });
  kind('decAdd', 4, '小數的加減', r => {
    const pa = r.int(1, 2), pb = r.int(1, 2);
    const a = realDec(r, 10, 99 * 10 ** pa, pa), b = r.next() < 0.3 ? I(r.int(1, 99)) : realDec(r, 10, 99 * 10 ** pb, pb);
    if (r.next() < 0.5) return two(a, '+', b, 'dec', add(a, b));
    const [x, y] = a.n / a.d >= b.n / b.d ? [a, b] : [b, a];
    return eq(x, y) ? two(x, '+', y, 'dec', add(x, y)) : two(x, '-', y, 'dec', sub(x, y));
  });
  // 先乘除後加減、括號先算；數字設計成答案一定是正整數
  kind('mixed4', 4, '整數四則混合（含括號）', r => {
    const a = r.int(2, 50), b = r.int(2, 12), c = r.int(2, 12), q = r.int(2, 12);
    return { expr: r.pick([
      `${a} + ${b} × ${c}`,
      `(${a} + ${b}) × ${c}`,
      `${b * c + r.int(0, 40)} - ${b} × ${c}`,
      `${b * q} ÷ ${b} + ${a}`,
      `${a + b + c} - (${a} + ${b})`,
      (() => { const x = r.int(1, b * q - 1); return `(${x} + ${b * q - x}) ÷ ${b}`; })()
    ]) };
  }, { wide: true });
  kind('fracDiff', 5, '異分母分數的加減', r => {
    let a, b;
    do { const d1 = r.int(2, 12), d2 = r.int(2, 12); a = Q(r.int(1, d1 - 1), d1); b = Q(r.int(1, d2 - 1), d2); } while (a.d === b.d);
    if (r.next() < 0.5) return two(a, '+', b, 'frac', add(a, b));
    const diff = sub(a, b);
    return diff.n > 0 ? two(a, '-', b, 'frac', diff) : two(b, '-', a, 'frac', sub(b, a));
  });
  kind('fracMulInt', 5, '分數 × 整數', r => {
    const d = r.int(2, 12), f = Q(r.int(1, d - 1), d), k = I(r.int(2, 12));
    return r.next() < 0.5 ? two(f, '×', k, 'frac', mul(f, k)) : two(k, '×', f, 'frac', mul(k, f));
  });
  kind('fracMul', 5, '分數 × 分數', r => {
    const d1 = r.int(2, 10), d2 = r.int(2, 10);
    const a = Q(r.int(1, d1 - 1), d1), b = Q(r.int(1, d2 - 1), d2);
    return two(a, '×', b, 'frac', mul(a, b));
  });
  kind('decMulInt', 5, '小數 × 整數', r => { const p = r.int(1, 2), a = realDec(r, 11, 9 * 10 ** p + 9, p), k = I(r.int(2, 30)); return two(a, '×', k, 'dec', mul(a, k)); });
  kind('decMul', 5, '小數 × 小數', r => { const a = realDec(r, 11, 99, 1), p = r.int(1, 2), b = realDec(r, 11, 10 ** (p + 1) - 1, p); return two(a, '×', b, 'dec', mul(a, b)); });
  kind('decDivInt', 5, '小數 ÷ 整數（整除）', r => { const k = r.int(2, 19), q = realDec(r, 11, 999, r.int(1, 2)); return two(mul(q, I(k)), '÷', I(k), 'dec', q); });
  kind('gcd', 5, '最大公因數', r => {
    const g = r.int(2, 12);
    let m = r.int(2, 9), n = r.int(2, 9);
    while (n === m || gcd(m, n) !== 1) { m = r.int(2, 9); n = r.int(2, 9); }
    return { special: 'gcd', a: g * m, b: g * n, answer: g };
  }, { wide: true });
  kind('lcm', 5, '最小公倍數', r => {
    let a = r.int(2, 30), b = r.int(2, 30);
    while (a === b || lcm(a, b) > 240) { a = r.int(2, 30); b = r.int(2, 30); }
    return { special: 'lcm', a, b, answer: lcm(a, b) };
  }, { wide: true });
  kind('fracDiv', 6, '分數 ÷ 分數', r => {
    const d1 = r.int(2, 10), d2 = r.int(2, 10);
    const a = r.next() < 0.25 ? I(r.int(1, 9)) : Q(r.int(1, d1 - 1), d1);
    const b = Q(r.int(1, d2 - 1), d2);
    return two(a, '÷', b, 'frac', div(a, b));
  });
  kind('decDiv', 6, '小數 ÷ 小數（整除）', r => {
    const b = realDec(r, 2, 99, 1), q = r.next() < 0.4 ? I(r.int(2, 60)) : realDec(r, 11, 999, r.int(1, 2));
    return two(mul(q, b), '÷', b, 'dec', q);
  });

  // ---------- 方程式（未知數） ----------
  // 低年級用 □ 填空，六年級用 x 表示未知數；題目是一條等式、答案是未知數的值（測試會把答案代回去，兩邊要相等）
  const eqItem = (lhs, rhs, answer, sym, mode) => ({ special: 'eq', lhs, rhs, answer, sym, mode: mode || 'int' });
  function boxAddSub(a, b, sym) {   // a + b = c 的四種藏法
    const c = a + b;
    return [eqItem(`${a} + ${sym}`, `${c}`, I(b), sym), eqItem(`${sym} + ${b}`, `${c}`, I(a), sym),
      eqItem(`${c} - ${sym}`, `${a}`, I(b), sym), eqItem(`${sym} - ${b}`, `${a}`, I(c), sym)];
  }
  function boxMulDiv(a, b, sym) {   // a × b = c 的四種藏法
    const c = a * b;
    return [eqItem(`${a} × ${sym}`, `${c}`, I(b), sym), eqItem(`${sym} × ${b}`, `${c}`, I(a), sym),
      eqItem(`${c} ÷ ${sym}`, `${a}`, I(b), sym), eqItem(`${sym} ÷ ${a}`, `${b}`, I(c), sym)];
  }
  kind('eqBox1', 1, '□ 填空（10 以內加減）', r => { const a = r.int(1, 8), b = r.int(1, 10 - a); return r.pick(boxAddSub(a, b, '□')); });
  kind('eqBox2', 2, '□ 填空（二位數加減）', r => { const a = r.int(10, 80), b = r.int(5, 99 - a); return r.pick(boxAddSub(a, b, '□')); });
  kind('eqBox3', 3, '□ 填空（乘除）', r => { const a = r.int(2, 9), b = r.int(2, 9); return r.pick(boxMulDiv(a, b, '□')); });
  kind('eqX', 6, '解方程式（整數、小數）', r => {
    if (r.next() < 0.3) {   // 小數版：x 比 a 大，x - a 才是正的
      let x, a;
      do { x = realDec(r, 11, 999, 1); a = realDec(r, 11, 999, r.int(1, 2)); } while (x.n * a.d <= a.n * x.d);
      return r.pick([
        eqItem(`x + ${decText(a)}`, decText(add(x, a)), x, 'x', 'dec'),
        eqItem(`x - ${decText(a)}`, decText(sub(x, a)), x, 'x', 'dec'),
        eqItem(`${decText(add(x, a))} - x`, decText(a), x, 'x', 'dec')
      ]);
    }
    if (r.next() < 0.5) return r.pick(boxAddSub(r.int(2, 99), r.int(2, 99), 'x'));
    return r.pick(boxMulDiv(r.int(2, 12), r.int(2, 30), 'x'));
  }, { wide: true });
  kind('eqXfrac', 6, '解方程式（分數）', r => {
    const t = v => fracText(v, 'improper');
    // 數字控制在國小好算的範圍：分母不超過 24、分子不超過 50，x 不是 1，也不是一眼看出來的題目
    const small = v => v.d <= 24 && Math.abs(v.n) <= 50;
    let item;
    do {
      const d1 = r.int(2, 9), d2 = r.int(2, 9);
      const x = Q(r.int(1, 2 * d1), d1), a = Q(r.int(1, d2 - 1), d2), k = I(r.int(2, 6));
      item = r.pick([
        eqItem(`x + ${t(a)}`, t(add(x, a)), x, 'x', 'frac'),
        eqItem(`${t(a)} × x`, t(mul(a, x)), x, 'x', 'frac'),
        eqItem(`x ÷ ${t(k)}`, t(div(x, k)), x, 'x', 'frac'),
        eqItem(`${t(k)} × x`, t(mul(k, x)), x, 'x', 'frac')
      ]);
    } while (eq(item.answer, I(1)) || !small(evaluate(item.rhs)) || item.lhs.includes(item.rhs));
    return item;
  }, { wide: true });
  // ---------- 應用題（不用 AI）：生活情境模板，數字隨機、答案由算式算 ----------
  // gen(r) 回傳 { q:題目, expr:算式, unit:單位 } 或有餘數的 { q, special:'rem', dividend, divisor, unitQ, unitR }
  const NAMES = ['小明', '小美', '小華', '阿傑', '小芳', '小安', '小宇', '小晴'];
  const WORDS = [];
  const word = (id, grade, label, gen, extra) => WORDS.push(Object.assign({ id, grade, label, gen }, extra || {}));
  const ft = q => fracText(q, 'mixed');
  word('wAdd20', 1, '加法（20 以內）', r => { const n = r.pick(NAMES), a = r.int(2, 9), b = r.int(2, 9);
    return r.pick([
      { q: `${n}有 ${a} 顆彈珠，哥哥又給他 ${b} 顆，現在${n}有幾顆彈珠？`, expr: `${a} + ${b}`, unit: '顆' },
      { q: `花園裡有 ${a} 朵紅花和 ${b} 朵黃花，一共有幾朵花？`, expr: `${a} + ${b}`, unit: '朵' }]); }, { int: true });
  word('wSub20', 1, '減法（20 以內）', r => { const b = r.int(2, 9), a = r.int(b + 1, 18);
    return r.pick([
      { q: `樹上有 ${a} 隻小鳥，飛走了 ${b} 隻，樹上還有幾隻小鳥？`, expr: `${a} - ${b}`, unit: '隻' },
      { q: `盒子裡有 ${a} 塊餅乾，吃掉 ${b} 塊，還剩幾塊？`, expr: `${a} - ${b}`, unit: '塊' }]); }, { int: true });
  word('wAddSub100', 2, '二位數加減', r => { const n = r.pick(NAMES), a = r.int(25, 80), b = r.int(11, 99 - a), c = r.int(11, a - 5);
    return r.pick([
      { q: `${n}有 ${a} 張貼紙，生日又收到 ${b} 張，${n}現在有幾張貼紙？`, expr: `${a} + ${b}`, unit: '張' },
      { q: `圖書室有 ${a} 本故事書，借出 ${c} 本，還剩幾本？`, expr: `${a} - ${c}`, unit: '本' },
      { q: `一條繩子長 ${a} 公分，剪掉 ${c} 公分，還剩幾公分？`, expr: `${a} - ${c}`, unit: '公分' }]); }, { int: true });
  word('wMul99', 2, '乘法（九九乘法）', r => { const a = r.int(2, 9), b = r.int(2, 9);
    return r.pick([
      { q: `每盒有 ${a} 枝鉛筆，${b} 盒一共有幾枝鉛筆？`, expr: `${a} × ${b}`, unit: '枝' },
      { q: `一張桌子有 ${a} 個人坐，${b} 張桌子可以坐幾個人？`, expr: `${a} × ${b}`, unit: '人' }]); }, { int: true });
  word('wMul', 3, '乘法（多位數 × 一位數）', r => { const p = r.int(12, 250), k = r.int(2, 9);
    return r.pick([
      { q: `一張電影票 ${p} 元，買 ${k} 張要多少元？`, expr: `${p} × ${k}`, unit: '元' },
      { q: `一箱蘋果有 ${p} 顆，${k} 箱共有幾顆？`, expr: `${p} × ${k}`, unit: '顆' }]); }, { int: true });
  word('wDiv', 3, '除法（平分，整除）', r => { const b = r.int(2, 9), q = r.int(3, 40);
    return r.pick([
      { q: `${b * q} 顆糖果平分給 ${b} 個小朋友，每人分到幾顆？`, expr: `${b * q} ÷ ${b}`, unit: '顆' },
      { q: `${b * q} 個學生，每 ${b} 人一組，可以分成幾組？`, expr: `${b * q} ÷ ${b}`, unit: '組' }]); }, { int: true });
  word('wDivR', 3, '除法（有餘數）', r => { const b = r.int(3, 9), q = r.int(3, 30), rem = r.int(1, b - 1);
    return { q: `${b * q + rem} 枝鉛筆，每 ${b} 枝裝一盒，可以裝滿幾盒？還剩幾枝？`, special: 'rem', dividend: b * q + rem, divisor: b, unitQ: '盒', unitR: '枝' }; }, { int: true });
  word('wFracSame', 3, '同分母分數', r => { const d = r.int(4, 12), a = r.int(1, d - 2), b = r.int(1, d - 1 - a);
    return r.pick([
      { q: `一個披薩平分成 ${d} 片，哥哥吃了 ${a} 片，弟弟吃了 ${b} 片，兩人一共吃了這個披薩的幾分之幾？`, expr: `${a}/${d} + ${b}/${d}`, unit: '' },
      { q: `一條緞帶，用掉 ${a}/${d} 條，又用掉 ${b}/${d} 條，一共用掉幾條？`, expr: `${a}/${d} + ${b}/${d}`, unit: '條' }]); });
  word('wMul2', 4, '乘法（× 二位數）', r => { const p = r.int(15, 95), k = r.int(12, 45);
    return { q: `學校買了 ${k} 顆籃球，每顆 ${p * 5} 元，一共要付多少元？`, expr: `${p * 5} × ${k}`, unit: '元' }; }, { int: true });
  word('wDiv2', 4, '除法（÷ 二位數）', r => { const b = r.int(12, 48), q = r.int(3, 40);
    return { q: `工廠做了 ${b * q} 瓶果汁，每 ${b} 瓶裝一箱，可以裝成幾箱？`, expr: `${b * q} ÷ ${b}`, unit: '箱' }; }, { int: true });
  word('wMixed', 4, '兩步驟（四則混合）', r => { const n = r.pick(NAMES), a = r.int(2, 6), p = r.int(3, 30) * 5, c = r.int(2, 20) * 5, pay = (a * p + c) + r.int(1, 10) * 10;
    return r.pick([
      { q: `${n}買 ${a} 枝 ${p} 元的筆和 1 本 ${c} 元的筆記本，一共要付多少元？`, expr: `${a} × ${p} + ${c}`, unit: '元' },
      { q: `${n}帶 ${pay} 元，買了 ${a} 個 ${p} 元的便當，還剩多少元？`, expr: `${pay} - ${a} × ${p}`, unit: '元' }]); }, { int: true });
  word('wDecAdd', 4, '小數加減', r => { const a = realDec(r, 30, 99, 1), b = realDec(r, 11, 29, 1);
    return r.pick([
      { q: `一條繩子長 ${decText(a)} 公尺，剪掉 ${decText(b)} 公尺，還剩幾公尺？`, expr: `${decText(a)} - ${decText(b)}`, unit: '公尺' },
      { q: `${r.pick(NAMES)}昨天跑了 ${decText(a)} 公里，今天跑了 ${decText(b)} 公里，兩天一共跑了幾公里？`, expr: `${decText(a)} + ${decText(b)}`, unit: '公里' }]); });
  word('wFracDiff', 5, '異分母分數加減', r => { let a, b; do { a = Q(r.int(1, 5), r.int(2, 8)); b = Q(r.int(1, 5), r.int(2, 8)); } while (a.d === b.d || a.n >= a.d || b.n >= b.d || a.n * b.d <= b.n * a.d);
    return r.pick([
      { q: `一瓶果汁有 ${ft(a)} 公升，喝掉 ${ft(b)} 公升，還剩多少公升？`, expr: `${ft(a)} - ${ft(b)}`, unit: '公升' },
      { q: `${r.pick(NAMES)}上午看了一本書的 ${ft(b)}，下午又看了 ${ft(sub(a, b))}，一共看了這本書的幾分之幾？`, expr: `${ft(b)} + ${ft(sub(a, b))}`, unit: '' }]); });
  word('wFracMul', 5, '分數 × 整數', r => { const d = r.int(3, 9), f = Q(r.int(1, d - 1), d), k = r.int(2, 9);
    return { q: `每個小朋友吃 ${ft(f)} 個蛋糕，${k} 個小朋友一共吃了幾個蛋糕？`, expr: `${ft(f)} × ${k}`, unit: '個' }; });
  word('wDecMul', 5, '小數 × 整數', r => { const p = r.int(2, 9) * 10, w = realDec(r, 11, 59, 1);
    return { q: `一公尺緞帶 ${p} 元，買 ${decText(w)} 公尺要多少元？`, expr: `${p} × ${decText(w)}`, unit: '元' }; });
  word('wGcd', 5, '最大公因數（平分）', r => { const g = r.int(2, 9); let m, n; do { m = r.int(2, 7); n = r.int(2, 7); } while (m === n || gcd(m, n) !== 1);
    return { q: `有 ${g * m} 顆紅球和 ${g * n} 顆藍球，要平分裝成一樣的禮物袋，每袋紅球一樣多、藍球也一樣多，而且都沒有剩，最多可以裝成幾袋？`, special: 'gcd', a: g * m, b: g * n, unit: '袋' }; }, { int: true });
  word('wLcm', 5, '最小公倍數（同時）', r => { let a, b; do { a = r.int(4, 20); b = r.int(4, 20); } while (a === b || lcm(a, b) > 120 || lcm(a, b) === Math.max(a, b));
    return { q: `甲公車每 ${a} 分鐘發一班，乙公車每 ${b} 分鐘發一班。兩班車早上 7 點同時發車後，至少再過幾分鐘會再同時發車？`, special: 'lcm', a, b, unit: '分鐘' }; }, { int: true });
  word('wPercent', 5, '百分率', r => { const p = r.pick([10, 20, 25, 30, 40, 50, 60, 75]), n = r.int(2, 8) * (p === 25 || p === 75 ? 4 : 10);
    return { q: `全校有 ${n * 10} 位學生，其中 ${p}% 的學生參加社團，參加社團的有幾位？`, expr: `${n * 10} × ${p} ÷ 100`, unit: '位' }; }, { int: true });
  word('wFracDiv', 6, '分數 ÷ 分數', r => { const d = r.int(2, 8), b = Q(1, d), k = r.int(2, 9), a = mul(b, I(k));
    return { q: `有 ${ft(a)} 公升的牛奶，每杯裝 ${ft(b)} 公升，可以裝滿幾杯？`, expr: `${ft(a)} ÷ ${ft(b)}`, unit: '杯' }; }, { int: true });
  word('wSpeed', 6, '速率', r => { const v = r.int(4, 12) * 10, t = r.int(2, 5);
    return r.pick([
      { q: `一輛汽車每小時行駛 ${v} 公里，${t} 小時可以行駛幾公里？`, expr: `${v} × ${t}`, unit: '公里' },
      { q: `一輛汽車 ${t} 小時行駛了 ${v * t} 公里，平均每小時行駛幾公里？`, expr: `${v * t} ÷ ${t}`, unit: '公里' }]); }, { int: true });
  word('wEqX', 6, '用 x 列式求解', r => { const n = r.int(2, 9), x = r.int(3, 30) * 5, extra = r.int(2, 9) * 10;
    return r.pick([
      { q: `一本書 x 元，買 ${n} 本一共付了 ${n * x} 元。用 x 列出等式，並求出一本書多少元。`, expr: `${n * x} ÷ ${n}`, unit: '元', eq: `${n} × x = ${n * x}` },
      { q: `${r.pick(NAMES)}原本有 x 元，存了 ${extra} 元以後，變成 ${x + extra} 元。用 x 列出等式，並求出原本有多少元。`, expr: `${x + extra} - ${extra}`, unit: '元', eq: `x + ${extra} = ${x + extra}` }]); }, { int: true });

  // 出 count 題應用題：{ q, expr, unit, value, answerText, check? }
  function generateWords(id, count, seed) {
    const k = WORDS.find(x => x.id === id);
    if (!k) throw new Error('沒有這個應用題：' + id);
    const r = makeRng(seed), seen = new Set(), list = [];
    for (let tries = 0; list.length < count && tries < count * 60; tries += 1) {
      const p = k.gen(r);
      if (seen.has(p.q)) continue;
      seen.add(p.q);
      if (p.special === 'rem') {
        const quot = Math.floor(p.dividend / p.divisor), rem = p.dividend % p.divisor;
        list.push(Object.assign(p, { expr: `${p.dividend} ÷ ${p.divisor}`, answerText: `${quot} ${p.unitQ}，剩 ${rem} ${p.unitR}`, check: { quot, rem } }));
      } else if (p.special === 'gcd' || p.special === 'lcm') {
        const v = p.special === 'gcd' ? gcd(p.a, p.b) : lcm(p.a, p.b);
        list.push(Object.assign(p, { expr: `${p.a} 和 ${p.b} 的${p.special === 'gcd' ? '最大公因數' : '最小公倍數'}`, value: I(v), answerText: `${v} ${p.unit}` }));
      } else {
        const value = evaluate(p.expr);
        list.push(Object.assign(p, { value, answerText: `${/\./.test(p.expr) ? decText(value) : ft(value)}${p.unit ? ' ' + p.unit : ''}` }));
      }
    }
    return list;
  }

  // 算式排版：分數上下疊、帶分數、□ 方格、x 斜體、全形運算符號（題目、答案、AI 應用題的算式都用這個）
  const BOX_HTML = '<span class="mq-box" data-word-text="□"></span>';
  function exprHtml(s) {
    return String(s == null ? '' : s).replace(/(\d+)又(\d+)\/(\d+)|(\d+)\/(\d+)|□|x|[+\-*()]|[^\d□x+\-*()]+|\d+(?:\.\d+)?/g, (tok, w, n, d, n2, d2) => {
      if (w) return fracHtml({ n: Number(w) * Number(d) + Number(n), d: Number(d) }, 'mixed');
      if (n2) return fracHtml({ n: Number(n2), d: Number(d2) }, 'improper');
      if (tok === '□') return BOX_HTML;
      if (tok === 'x') return '<i class="mq-x">x</i>';
      const op = { '+': '＋', '-': '－', '*': '×', '(': '（', ')': '）' }[tok];
      return op || esc(tok);
    });
  }
  // 一般文字（AI 應用題的題目）：只把分數、帶分數排成上下疊，其他照原樣
  function textHtml(s) {
    return esc(String(s == null ? '' : s))
      .replace(/(^|[^A-Za-z])x(?![A-Za-z])/g, '$1<i class="mq-x">x</i>')   // 題目裡單獨的 x 是未知數，用斜體
      .replace(/(\d+)又(\d+)\/(\d+)|(\d+)\/(\d+)/g, (tok, w, n, d, n2, d2) =>
        (w ? fracHtml({ n: Number(w) * Number(d) + Number(n), d: Number(d) }, 'mixed') : fracHtml({ n: Number(n2), d: Number(d2) }, 'improper')));
  }

  const OP_SHOW = { '+': '＋', '-': '－', '×': '×', '÷': '÷' };
  // 把一題整理成 { text, html, answerText, answerHtml, vertical }
  function build(item, style) {
    if (item.special === 'eq') {
      const symHtml = item.sym === 'x' ? '<i class="mq-x">x</i>' : '□';
      return {
        text: `${item.lhs} = ${item.rhs}`, html: `${exprHtml(item.lhs)} ＝ ${exprHtml(item.rhs)}`,
        answerText: `${item.sym} = ${numText(item.answer, item.mode, style)}`,
        answerHtml: `${symHtml} ＝ ${numHtml(item.answer, item.mode, style)}`, value: item.answer, equation: item
      };
    }
    if (item.special === 'rem') {
      return {
        text: `${item.dividend} ÷ ${item.divisor} =`, html: `${item.dividend} ÷ ${item.divisor} ＝`, remainder: true,
        answerText: `商 ${item.quot}，餘 ${item.rem}`, answerHtml: `商 ${item.quot}，餘 ${item.rem}`, check: item
      };
    }
    if (item.special === 'gcd' || item.special === 'lcm') {
      const name = item.special === 'gcd' ? '最大公因數' : '最小公倍數';
      return {
        text: `${item.a} 和 ${item.b} 的${name}是`, html: `${item.a} 和 ${item.b} 的${name}是`,
        answerText: String(item.answer), answerHtml: String(item.answer), check: item
      };
    }
    if (item.expr) {
      const value = evaluate(item.expr);
      return { text: `${item.expr} =`, html: `${exprHtml(item.expr)} ＝`, answerText: String(value.n), answerHtml: String(value.n), value };
    }
    const mode = item.mode;
    // 題目裡的分數照「未約分」的原樣出（例如 2/4 不先約成 1/2），答案才約到最簡
    const termText = (t, k) => (item.raw && item.raw[k] ? `${item.raw[k][0]}/${item.raw[k][1]}` : numText(t, mode, 'improper'));
    const termHtml = (t, k) => (item.raw && item.raw[k] ? fracHtml({ n: item.raw[k][0], d: item.raw[k][1] }, 'improper') : numHtml(t, mode, 'improper'));
    let text = termText(item.terms[0], 0), html = termHtml(item.terms[0], 0);
    item.ops.forEach((op, k) => {
      text += ` ${op} ${termText(item.terms[k + 1], k + 1)}`;
      html += ` ${OP_SHOW[op]} ${termHtml(item.terms[k + 1], k + 1)}`;
    });
    const out = {
      text: `${text} =`, html: `${html} ＝`,
      answerText: numText(item.answer, mode, style), answerHtml: numHtml(item.answer, mode, style), value: item.answer
    };
    if (item.vertical && mode === 'int') out.vertical = { a: item.terms[0].n, b: item.terms[1].n, op: item.ops[0] };
    return out;
  }

  // 出 count 題：同一份卷裡不重複
  function generate(kindId, count, seed, options) {
    const k = KINDS.find(x => x.id === kindId);
    if (!k) throw new Error('沒有這個題型：' + kindId);
    const style = (options && options.fracStyle) || 'mixed';
    const r = makeRng(seed);
    const seen = new Set(), list = [];
    for (let tries = 0; list.length < count && tries < count * 60; tries += 1) {
      const q = build(k.gen(r), style);
      if (seen.has(q.text)) continue;
      seen.add(q.text);
      list.push(q);
    }
    return list;
  }

  // 直式（加、減、乘）：右對齊的數字格
  function verticalHtml(v) {
    const a = String(v.a), b = String(v.b);
    const width = Math.max(a.length, b.length) + 1 + (v.op === '×' ? b.length : 1);
    const cells = (s, lead) => {
      const pad = width - s.length - (lead ? 1 : 0);
      return '<td></td>'.repeat(Math.max(0, pad)) + (lead ? `<td class="mv-op">${lead}</td>` : '') + [...s].map(ch => `<td>${ch}</td>`).join('');
    };
    const blank = '<td></td>'.repeat(width);
    const work = v.op === '×' && b.length > 1 ? `<tr class="mv-gap">${blank}</tr>`.repeat(b.length) : '';
    return `<table class="mv"><tr>${cells(a)}</tr><tr class="mv-line">${cells(b, OP_SHOW[v.op])}</tr>${work}${work ? `<tr class="mv-line">${blank}</tr>` : ''}<tr class="mv-gap">${blank}</tr></table>`;
  }

  return { KINDS, generate, evaluate, parseAnswer, makeRng, Q, add, sub, mul, div, eq, gcd, lcm, fracText, fracHtml, decText, numText, verticalHtml, exprHtml, textHtml, WORDS, generateWords };
});
