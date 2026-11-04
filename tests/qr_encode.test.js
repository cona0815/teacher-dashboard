// QR Code 編碼器：矩陣雜湊來自 2026-11-04 的驗證（與 python qrcode 套件逐格相同，OpenCV 掃得出來）
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const Q = require("../assets/studio/qr-encode.js");

const hash = code => crypto.createHash("sha256").update(code.modules.map(row => row.map(x => (x ? 1 : 0)).join("")).join("\n")).digest("hex").slice(0, 16);
const GOLDEN = [
  [
    "https://www.google.com",
    2,
    2,
    "8bba4599296e9f75"
  ],
  [
    "https://t-borad2026.netlify.app/",
    3,
    0,
    "810204634e2adca8"
  ],
  [
    "https://scratch.tn.edu.tw/115slide.html",
    3,
    2,
    "fade463cb26008fc"
  ],
  [
    "a",
    1,
    5,
    "e8ab680854e4019c"
  ],
  [
    "今天的作業在班網",
    2,
    2,
    "68c0274014f0ed6d"
  ],
  [
    "https://example.com/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    5,
    0,
    "d65ebc2590d70889"
  ],
  [
    "https://e.tw/abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123abcDEF123",
    15,
    2,
    "e8598577eac9dcf5"
  ]
];
for (const [text, version, mask, digest] of GOLDEN) {
  const code = Q.encode(text);
  assert.equal(code.version, version, `${text} 的版本`);
  assert.equal(code.mask, mask, `${text} 的遮罩`);
  assert.equal(hash(code), digest, `${text} 的矩陣`);
  assert.equal(code.size, version * 4 + 17);
  assert.equal(code.modules.length, code.size);
  // 三個定位點的中心都是深色、外圈是淺色分隔
  for (const [x, y] of [[3, 3], [code.size - 4, 3], [3, code.size - 4]]) assert.equal(code.modules[y][x], true, "定位點");
  assert.equal(code.modules[7][7], false, "定位點旁的分隔");
  assert.equal(code.modules[code.size - 8][8], true, "固定的暗模組");
}
assert.equal(Q.encode("x".repeat(3000)), null, "超過容量要回 null，不可當機");
assert.ok(Q.encode("x".repeat(2331)), "40 版 M 級最多 2331 位元組");
assert.equal(Q.encode("x".repeat(2332)), null);
console.log("qr_encode.test.js: all checks passed");
