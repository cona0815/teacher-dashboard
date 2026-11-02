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

// 直式
const v = M.verticalHtml({ a: 345, b: 78, op: "+" });
assert.match(v, /<table class="mv">/);
assert.match(v, /mv-op">＋/);

console.log(`math_gen.test.js: all checks passed（驗算 ${total} 題）`);
