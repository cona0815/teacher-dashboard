// 數學出題小幫手引擎：每個題型出很多份卷，逐題重新驗算，確定答案一定對
const assert = require("node:assert/strict");
const M = require("../assets/studio/math-gen.js");

const { Q, eq, evaluate, gcd, lcm } = M;

// 驗算器本身
assert.ok(eq(evaluate("1/2 + 1/3"), Q(5, 6)));
assert.ok(eq(evaluate("2又1/3 × 3"), Q(7)));
assert.ok(eq(evaluate("（12 + 8）÷ 4"), Q(5)));
assert.ok(eq(evaluate("0.1 + 0.2"), Q(3, 10)), "小數要精確，不能有 0.30000000000000004");
assert.ok(eq(evaluate("3 + 4 × 2"), Q(11)), "先乘除後加減");
assert.ok(eq(evaluate("3/4 ÷ 1/4"), Q(3)), "分數線比 ÷ 先算");
assert.ok(eq(evaluate("(3 + 1)/4"), Q(1)), "括號後面的 / 是除法");
assert.ok(eq(evaluate("１２０－３５"), Q(85)), "全形數字與符號");
assert.ok(eq(M.parseAnswer("12 公尺"), Q(12)), "答案帶單位");
assert.ok(eq(M.parseAnswer("3又1/4"), Q(13, 4)));
assert.throws(() => evaluate("3 + "), "算式不完整要報錯");
assert.throws(() => evaluate("5 ÷ 0"), "除以 0 要報錯");
assert.equal(M.decText(Q(5, 4)), "1.25");
assert.equal(M.decText(Q(3)), "3");
assert.equal(M.decText(Q(1, 20)), "0.05");
assert.equal(M.fracText(Q(7, 3)), "2又1/3");
assert.equal(M.fracText(Q(7, 3), "improper"), "7/3");

// 同一個號碼＝同一份卷
assert.deepEqual(M.generate("fracDiff", 5, 42).map(q => q.text), M.generate("fracDiff", 5, 42).map(q => q.text));
assert.notDeepEqual(M.generate("fracDiff", 5, 42).map(q => q.text), M.generate("fracDiff", 5, 43).map(q => q.text));

let total = 0;
for (const kind of M.KINDS) {
  assert.ok(kind.grade >= 1 && kind.grade <= 6, `${kind.id} 年級要在 1–6`);
  for (let seed = 1; seed <= 60; seed += 1) {
    const list = M.generate(kind.id, 10, seed * 7919);
    assert.equal(list.length, 10, `${kind.id} 每份要出得滿 10 題`);
    assert.equal(new Set(list.map(q => q.text)).size, 10, `${kind.id} 同一份不能重複`);
    for (const q of list) {
      total += 1;
      const where = `${kind.id}：${q.text} ${q.answerText}`;
      if (q.check && q.check.special === "rem") {
        const c = q.check;
        assert.ok(c.rem > 0 && c.rem < c.divisor, `${where} 餘數要小於除數`);
        assert.equal(c.quot * c.divisor + c.rem, c.dividend, where);
        continue;
      }
      if (q.check && (q.check.special === "gcd" || q.check.special === "lcm")) {
        const want = q.check.special === "gcd" ? gcd(q.check.a, q.check.b) : lcm(q.check.a, q.check.b);
        assert.equal(Number(q.answerText), want, where);
        continue;
      }
      if (q.equation) {
        // 方程式：把答案代回未知數，等號兩邊要相等
        const e = q.equation;
        const put = side => evaluate(side.replace(e.sym, `(${M.fracText(q.value, "improper")})`));
        assert.ok(eq(put(e.lhs), evaluate(e.rhs)), `${where} 代回去兩邊不相等`);
        assert.ok(q.value.n > 0, `${where} 未知數要是正的`);
        assert.ok(evaluate(e.rhs).n >= 0, `${where} 右邊不能是負的`);
        assert.equal(e.lhs.split(e.sym).length + e.rhs.split(e.sym).length - 2, 1, `${where} 未知數只出現一次`);
        assert.match(q.html, e.sym === "x" ? /mq-x/ : /mq-box/, where);
        continue;
      }
      const recomputed = evaluate(q.text);
      assert.ok(eq(recomputed, q.value), `${where} 重新驗算不一致`);
      assert.ok(recomputed.n >= 0, `${where} 答案不能是負的`);
      assert.ok(eq(M.parseAnswer(q.answerText), q.value), `${where} 答案文字要能讀回同一個數`);
      assert.ok(Number.isSafeInteger(recomputed.n) && Number.isSafeInteger(recomputed.d), `${where} 數字太大`);
      if (/^(add|sub|mul|div)/.test(kind.id) && kind.id !== "div1r") assert.equal(recomputed.d, 1, `${where} 整數題答案要是整數`);
      assert.doesNotMatch(q.html, /undefined|NaN/, where);
    }
  }
}
assert.ok(total > 10000, "應驗算超過一萬題");

// 算式排版
assert.match(M.exprHtml("3/4 - 1/3"), /mf-f[\s\S]*－[\s\S]*mf-f/, "算式裡的分數要上下疊、減號用全形");
assert.match(M.exprHtml("2又1/3 × x"), /mf-w">2<[\s\S]*mq-x/, "帶分數與 x");
assert.match(M.exprHtml("5 + □"), /mq-box/, "□ 要畫成方格");
assert.equal(M.textHtml("喝了 <b>1/3</b> 公升").includes("&lt;b&gt;"), true, "題目文字要先跳脫 HTML");
assert.match(M.textHtml("一本書 x 元，Excel 不變"), /<i class="mq-x">x<\/i> 元，Excel/, "題目裡的 x 用斜體，英文單字不動");
assert.ok(M.KINDS.some(k => k.id === "eqX") && M.KINDS.some(k => k.id === "eqBox1"), "要有方程式題型");

// 應用題（不用 AI）：每個模板出很多題，答案重新驗算，數字都要出現在題目裡
let wordTotal = 0;
for (const w of M.WORDS) {
  for (let seed = 1; seed <= 40; seed += 1) {
    for (const p of M.generateWords(w.id, 3, seed * 104729)) {
      wordTotal += 1;
      const where = `${w.id}：${p.q}`;
      assert.doesNotMatch(p.q, /undefined|NaN/, where);
      if (p.check) { assert.equal(p.check.quot * p.divisor + p.check.rem, p.dividend, where); assert.ok(p.check.rem > 0 && p.check.rem < p.divisor, where); continue; }
      if (p.special) { assert.equal(p.value.n, p.special === "gcd" ? gcd(p.a, p.b) : lcm(p.a, p.b), where); continue; }
      assert.ok(eq(evaluate(p.expr), p.value) && p.value.n > 0, `${where} 答案要是正的`);
      if (w.int) assert.equal(p.value.d, 1, `${where} 這類題答案要是整數`);
      for (const num of p.expr.match(/\d+(?:\.\d+)?/g) || []) {   // 分數拆成分子、分母各自檢查（「5 片吃 2 片」→ 2/5）
        if (num === "100" && /%/.test(p.q)) continue;
        assert.ok(p.q.includes(num), `${where} 算式的 ${num} 要出現在題目裡`);
      }
      if (p.eq) {
        const [l, r] = p.eq.split("=");
        assert.ok(eq(evaluate(l.replace("x", `(${M.fracText(p.value, "improper")})`)), evaluate(r)), `${where} 等式代回去要成立`);
      }
    }
  }
}
assert.ok(wordTotal > 2000, "應用題要驗算超過 2000 題");

// 直式
const v = M.verticalHtml({ a: 345, b: 78, op: "+" });
assert.match(v, /<table class="mv">/);
assert.match(v, /mv-op">＋/);

console.log(`math_gen.test.js: all checks passed（驗算計算題 ${total} 題、應用題 ${wordTotal} 題）`);

// 2026-11-10 年級對照 108 課綱數學領綱學習內容（條目備註的數字範圍）
{
  const g = id => (M.KINDS.find(k => k.id === id) || M.WORDS.find(k => k.id === id)).grade;
  assert.equal(g("eqBox1"), 2, "N-1-2 備註：一年級不做加數、被加數未知（□ 填空）→ 二年級");
  assert.equal(g("decAdd1"), 3, "N-3-10：一位小數的加減在三年級");
  assert.equal(g("fracTimes"), 4, "N-4-5：分數的整數倍在四年級");
  assert.equal(g("fracMixed"), 4, "N-4-5：帶分數在四年級");
  assert.equal(g("decMulInt"), 4, "N-4-7：小數的整數倍在四年級");
  assert.equal(g("wFracMul"), 4, "N-4-5：分數的整數倍應用題在四年級");
  for (let seed = 1; seed <= 300; seed += 1) {
    for (const q of M.generate("mul1", 10, seed)) assert.ok(+q.text.split(" × ")[0] <= 999, `N-3-3 被乘數只到三位數：${q.text}`);
    for (const q of M.generate("div1", 10, seed)) assert.ok(+q.text.split(" ÷ ")[0] <= 999, `N-3-5 被除數只到三位數：${q.text}`);
    for (const q of M.generate("div1r", 10, seed)) assert.ok(q.check.dividend <= 999, `N-3-5 被除數只到三位數：${q.text}`);
    for (const q of M.generate("fracSame", 10, seed)) {
      assert.doesNotMatch(q.answerText, /又/, `N-3-9 三年級不寫帶分數：${q.text} ${q.answerText}`);
      assert.ok(q.value.n <= 2 * q.value.d, `N-3-9 結果不超過 2：${q.text}`);
      const d = q.text.match(/\/(\d+)/)[1];
      if (q.answerText.includes("/")) assert.equal(q.answerText.split("/")[1], d, `三年級還沒學約分，答案照原分母：${q.text} ${q.answerText}`);
    }
    for (const q of M.generate("fracMixed", 10, seed)) assert.match(q.text, /又/, `帶分數題目要寫成帶分數：${q.text}`);
    for (const q of M.generate("fracDiff", 10, seed)) {
      const [a, b] = q.text.match(/\/(\d+)/g).map(x => +x.slice(1));
      const ok = (a < 10 && b < 10) || a % b === 0 || b % a === 0 || [2, 3, 4, 5].some(i => [2, 3, 4, 5].some(j => a * i === b * j));
      assert.ok(ok, `N-5-4 通分數字範圍：${q.text}`);
    }
  }
}
