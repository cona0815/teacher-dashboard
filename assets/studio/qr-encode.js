/* 螢幕公告的 QR Code 編碼（ISO/IEC 18004，位元組模式、容錯等級 M）
   本站安全設定不允許外部程式，所以自己算。瀏覽器：window.QREncode；Node 測試：require('../assets/studio/qr-encode.js')
   encode(文字) 回傳 { size, modules:[[true/false…]…] }；太長（超過 40 版）回傳 null */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.QREncode = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // 容錯等級 M：每版每個區塊的校正碼數、區塊數（索引是版本，0 不用）
  const ECC_PER_BLOCK = [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28];
  const NUM_BLOCKS = [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49];
  const FORMAT_LEVEL_M = 0;

  function rawDataModules(ver) {
    let n = (16 * ver + 128) * ver + 64;
    if (ver >= 2) {
      const align = Math.floor(ver / 7) + 2;
      n -= (25 * align - 10) * align - 55;
      if (ver >= 7) n -= 36;
    }
    return n;
  }
  const dataCodewords = ver => Math.floor(rawDataModules(ver) / 8) - ECC_PER_BLOCK[ver] * NUM_BLOCKS[ver];

  // ---------- Reed-Solomon（GF(256)，多項式 0x11D） ----------
  function gfMul(a, b) {
    let r = 0;
    for (let i = 7; i >= 0; i -= 1) {
      r = (r << 1) ^ ((r >>> 7) * 0x11D);
      r ^= ((b >>> i) & 1) * a;
    }
    return r & 0xFF;
  }
  function rsDivisor(degree) {
    const d = new Array(degree).fill(0);
    d[degree - 1] = 1;
    let root = 1;
    for (let i = 0; i < degree; i += 1) {
      for (let j = 0; j < degree; j += 1) {
        d[j] = gfMul(d[j], root);
        if (j + 1 < degree) d[j] ^= d[j + 1];
      }
      root = gfMul(root, 2);
    }
    return d;
  }
  function rsRemainder(data, divisor) {
    const out = new Array(divisor.length).fill(0);
    data.forEach(byte => {
      const factor = byte ^ out.shift();
      out.push(0);
      divisor.forEach((coef, i) => { out[i] ^= gfMul(coef, factor); });
    });
    return out;
  }

  // ---------- 資料 → 碼字 ----------
  function buildCodewords(bytes, ver) {
    const bits = [];
    const push = (value, len) => { for (let i = len - 1; i >= 0; i -= 1) bits.push((value >>> i) & 1); };
    push(4, 4);   // 位元組模式
    push(bytes.length, ver <= 9 ? 8 : 16);
    bytes.forEach(b => push(b, 8));
    const capacity = dataCodewords(ver) * 8;
    push(0, Math.min(4, capacity - bits.length));
    push(0, (8 - bits.length % 8) % 8);
    for (let pad = 0xEC; bits.length < capacity; pad ^= 0xEC ^ 0x11) push(pad, 8);
    const data = [];
    for (let i = 0; i < bits.length; i += 8) data.push(bits.slice(i, i + 8).reduce((a, b) => a * 2 + b, 0));

    // 分區塊、算校正碼、交錯排列
    const blocksTotal = NUM_BLOCKS[ver], eccLen = ECC_PER_BLOCK[ver], raw = Math.floor(rawDataModules(ver) / 8);
    const shortBlocks = blocksTotal - raw % blocksTotal, shortLen = Math.floor(raw / blocksTotal) - eccLen;
    const divisor = rsDivisor(eccLen), blocks = [], eccs = [];
    for (let i = 0, at = 0; i < blocksTotal; i += 1) {
      const len = shortLen + (i < shortBlocks ? 0 : 1);
      const block = data.slice(at, at + len);
      at += len;
      blocks.push(block);
      eccs.push(rsRemainder(block, divisor));
    }
    const out = [];
    for (let i = 0; i <= shortLen; i += 1) blocks.forEach(block => { if (i < block.length) out.push(block[i]); });
    for (let i = 0; i < eccLen; i += 1) eccs.forEach(ecc => out.push(ecc[i]));
    return out;
  }

  // ---------- 排版 ----------
  function alignmentPositions(ver) {
    if (ver === 1) return [];
    const count = Math.floor(ver / 7) + 2, size = ver * 4 + 17;
    const step = ver === 32 ? 26 : Math.floor((ver * 8 + count * 3 + 5) / (count * 4 - 4)) * 2;
    const out = [6];
    for (let pos = size - 7; out.length < count; pos -= step) out.splice(1, 0, pos);
    return out;
  }
  function drawFunctionPatterns(ver) {
    const size = ver * 4 + 17;
    const m = Array.from({ length: size }, () => new Array(size).fill(false));
    const fixed = Array.from({ length: size }, () => new Array(size).fill(false));
    const set = (x, y, dark) => { m[y][x] = dark; fixed[y][x] = true; };
    for (let i = 0; i < size; i += 1) { set(6, i, i % 2 === 0); set(i, 6, i % 2 === 0); }
    const finder = (cx, cy) => {
      for (let dy = -4; dy <= 4; dy += 1) for (let dx = -4; dx <= 4; dx += 1) {
        const x = cx + dx, y = cy + dy;
        if (x < 0 || y < 0 || x >= size || y >= size) continue;
        const d = Math.max(Math.abs(dx), Math.abs(dy));
        set(x, y, d !== 2 && d !== 4);
      }
    };
    finder(3, 3); finder(size - 4, 3); finder(3, size - 4);
    const pos = alignmentPositions(ver), last = pos.length - 1;
    pos.forEach((cy, i) => pos.forEach((cx, j) => {
      if ((i === 0 && j === 0) || (i === 0 && j === last) || (i === last && j === 0)) return;
      for (let dy = -2; dy <= 2; dy += 1) for (let dx = -2; dx <= 2; dx += 1) set(cx + dx, cy + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
    }));
    drawFormat(m, fixed, 0);
    if (ver >= 7) {
      let rem = ver;
      for (let i = 0; i < 12; i += 1) rem = (rem << 1) ^ ((rem >>> 11) * 0x1F25);
      const bits = ver * 4096 + rem;
      for (let i = 0; i < 18; i += 1) {
        const dark = Math.floor(bits / 2 ** i) % 2 === 1;
        const a = size - 11 + i % 3, b = Math.floor(i / 3);
        set(a, b, dark); set(b, a, dark);
      }
    }
    return { m, fixed, size };
  }
  function drawFormat(m, fixed, mask) {
    const size = m.length;
    const data = (FORMAT_LEVEL_M << 3) | mask;
    let rem = data;
    for (let i = 0; i < 10; i += 1) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
    const bits = ((data << 10) | rem) ^ 0x5412;
    const bit = i => ((bits >>> i) & 1) === 1;
    const set = (x, y, dark) => { m[y][x] = dark; fixed[y][x] = true; };
    for (let i = 0; i <= 5; i += 1) set(8, i, bit(i));
    set(8, 7, bit(6)); set(8, 8, bit(7)); set(7, 8, bit(8));
    for (let i = 9; i < 15; i += 1) set(14 - i, 8, bit(i));
    for (let i = 0; i < 8; i += 1) set(size - 1 - i, 8, bit(i));
    for (let i = 8; i < 15; i += 1) set(8, size - 15 + i, bit(i));
    set(8, size - 8, true);   // 固定的暗模組
  }
  function drawCodewords(m, fixed, codewords) {
    const size = m.length;
    let i = 0;
    for (let right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (let v = 0; v < size; v += 1) for (let j = 0; j < 2; j += 1) {
        const x = right - j, upward = ((right + 1) & 2) === 0, y = upward ? size - 1 - v : v;
        if (!fixed[y][x] && i < codewords.length * 8) {
          m[y][x] = ((codewords[i >>> 3] >>> (7 - (i & 7))) & 1) === 1;
          i += 1;
        }
      }
    }
  }
  const MASKS = [
    (x, y) => (x + y) % 2 === 0, (x, y) => y % 2 === 0, x => x % 3 === 0, (x, y) => (x + y) % 3 === 0,
    (x, y) => (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0, (x, y) => x * y % 2 + x * y % 3 === 0,
    (x, y) => (x * y % 2 + x * y % 3) % 2 === 0, (x, y) => ((x + y) % 2 + x * y % 3) % 2 === 0
  ];
  function applyMask(m, fixed, mask) {
    const fn = MASKS[mask];
    for (let y = 0; y < m.length; y += 1) for (let x = 0; x < m.length; x += 1) if (!fixed[y][x] && fn(x, y)) m[y][x] = !m[y][x];
  }
  // 選遮罩用的扣分（規格的四條規則）
  function penalty(m) {
    const size = m.length;
    let score = 0, dark = 0;
    const FINDER_A = '10111010000', FINDER_B = '00001011101';
    const line = cells => {
      let run = 1;
      for (let i = 1; i <= cells.length; i += 1) {
        if (i < cells.length && cells[i] === cells[i - 1]) { run += 1; continue; }
        if (run >= 5) score += run - 2;
        run = 1;
      }
      const text = cells.map(c => (c ? '1' : '0')).join('');
      for (const pattern of [FINDER_A, FINDER_B]) for (let at = text.indexOf(pattern); at !== -1; at = text.indexOf(pattern, at + 1)) score += 40;
    };
    for (let i = 0; i < size; i += 1) { line(m[i]); line(m.map(row => row[i])); }
    for (let y = 0; y < size; y += 1) for (let x = 0; x < size; x += 1) {
      if (m[y][x]) dark += 1;
      if (x + 1 < size && y + 1 < size && m[y][x] === m[y][x + 1] && m[y][x] === m[y + 1][x] && m[y][x] === m[y + 1][x + 1]) score += 3;
    }
    score += Math.floor(Math.abs(dark * 20 - size * size * 10) / (size * size)) * 10;
    return score;
  }

  function encode(text) {
    const bytes = [...new TextEncoder().encode(String(text))];
    let ver = 1;
    while (ver <= 40 && 4 + (ver <= 9 ? 8 : 16) + bytes.length * 8 > dataCodewords(ver) * 8) ver += 1;
    if (ver > 40) return null;
    const { m, fixed, size } = drawFunctionPatterns(ver);
    drawCodewords(m, fixed, buildCodewords(bytes, ver));
    let best = 0, bestScore = Infinity;
    for (let mask = 0; mask < 8; mask += 1) {
      applyMask(m, fixed, mask);
      drawFormat(m, fixed, mask);
      const score = penalty(m);
      if (score < bestScore) { best = mask; bestScore = score; }
      applyMask(m, fixed, mask);   // 還原
    }
    applyMask(m, fixed, best);
    drawFormat(m, fixed, best);
    return { size, version: ver, mask: best, modules: m };
  }
  return { encode };
});
