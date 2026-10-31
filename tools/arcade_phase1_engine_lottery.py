"""班級工具遊戲化 第一階段：Arcade 引擎（畫布層、星空、粒子、圓形物理）＋抽籤轉盤＋扭蛋機。

python tools/arcade_phase1_engine_lottery.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'Arcade 引擎' not in s, '第一階段已套用'


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)


# ------------------------------------------------------------------ CSS
CSS = r'''
        /* ===== 班級工具遊戲化（Arcade 第二版）：深色太空舞台＋畫布特效 ===== */
        .arcade { position: relative; overflow: hidden; border-radius: 22px; color: #fff;
          background: radial-gradient(60% 70% at 18% 20%, rgba(124,77,255,.38), transparent 60%),
                      radial-gradient(55% 60% at 88% 85%, rgba(0,190,255,.26), transparent 60%),
                      radial-gradient(40% 40% at 70% 10%, rgba(255,90,160,.18), transparent 60%),
                      linear-gradient(160deg, #191340 0%, #0d0b25 60%, #090818 100%);
          box-shadow: inset 0 0 0 2px rgba(160,140,255,.22), 0 18px 40px -22px rgba(20,10,60,.8); }
        .arcade > .arcade-bg, .arcade > .arcade-fx { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
        .arcade > .arcade-bg { z-index: 0; }
        .arcade > .arcade-fx { z-index: 6; }
        .arcade > :not(canvas) { position: relative; z-index: 2; }
        .arcade-flash { position: absolute !important; inset: 0; background: radial-gradient(circle, rgba(255,255,255,.85), rgba(255,255,255,0) 70%); z-index: 5 !important; pointer-events: none; animation: arcadeFlash .45s ease-out forwards; }
        @keyframes arcadeFlash { from { opacity: 1; } to { opacity: 0; } }
        .arcade.shake { animation: arcadeShake .42s cubic-bezier(.36,.07,.19,.97); }
        @keyframes arcadeShake { 10%, 90% { transform: translate(-2px, 1px); } 20%, 80% { transform: translate(4px, -2px); } 30%, 50%, 70% { transform: translate(-7px, 3px); } 40%, 60% { transform: translate(7px, -3px); } }
        .arcade-num { font-weight: 900; color: #ffd166; -webkit-text-stroke: 6px #2a1a5e; paint-order: stroke fill; text-shadow: 0 6px 0 #2a1a5e, 0 14px 28px rgba(0,0,0,.45); }

        /* 抽籤舞台 */
        .lottery-stage.arcade { background-color: #0d0b25; min-height: 470px; gap: 40px; padding: 26px 22px; box-shadow: inset 0 0 0 2px rgba(160,140,255,.25), 0 18px 40px -22px rgba(20,10,60,.8); }
        .lottery-stage .lot-bulbs, .lottery-stage .lot-wheel-pointer { display: none; }
        .lottery-stage .lot-wheel-wrap, .lottery-stage #lotWheel { width: 420px !important; height: 420px !important; }
        .lottery-stage .lot-wheel-wrap.punch { animation: wheelPunch .5s cubic-bezier(.3,1.6,.5,1); }
        @keyframes wheelPunch { 0% { transform: scale(1); } 30% { transform: scale(1.06); } 100% { transform: scale(1); } }
        .lottery-stage .lot-wheel-wrap canvas { filter: drop-shadow(0 18px 26px rgba(0,0,0,.55)); }
        .lottery-stage .lot-wheel-hub { width: 92px; height: 92px; border: 0; color: #2a1a5e; font-size: 34px;
          background: radial-gradient(circle at 35% 30%, #fff, #ffe9a8 45%, #e0a21a 100%); box-shadow: 0 0 0 6px #2a1a5e, 0 0 0 10px #ffd166, 0 8px 20px rgba(0,0,0,.5); }
        .lottery-stage .lot-result { font-size: 140px; color: #ffd166; -webkit-text-stroke: 9px #2a1a5e; paint-order: stroke fill; text-shadow: 0 8px 0 #2a1a5e, 0 18px 34px rgba(0,0,0,.5); }
        .lottery-stage .lot-result small { color: #fff; -webkit-text-stroke: 4px #2a1a5e; font-size: 28px; }
        .lottery-stage .lot-rays { background: repeating-conic-gradient(from 0deg, rgba(255,209,102,.30) 0 8deg, rgba(255,209,102,0) 8deg 16deg); width: 520px; height: 520px; margin: -260px; }
        .lottery-stage .lot-mascot { display: none; }
        .lottery-stage #lotGacha { width: 340px; height: 430px; }
        #lotGachaCanvas { width: 340px; height: 430px; display: block; }
        .lottery-stage .lot-claw-frame { box-shadow: 0 0 0 3px rgba(255,255,255,.25), 0 18px 30px rgba(0,0,0,.5); }
        .tool-panel:fullscreen .lottery-stage .lot-wheel-wrap, .tool-panel:fullscreen .lottery-stage #lotWheel { width: min(72vh, 58vw) !important; height: min(72vh, 58vw) !important; }
        .tool-panel:fullscreen .lottery-stage.arcade { min-height: 82vh; }
        .tool-panel:fullscreen .lottery-stage .lot-result { font-size: clamp(150px, 22vh, 260px); }
'''
rep('      </style>\n      <div class="panel">\n        <div class="tool-tabs" id="toolTabs">', CSS + '      </style>\n      <div class="panel">\n        <div class="tool-tabs" id="toolTabs">')

# ------------------------------------------------------------------ HTML
rep('<div class="lottery-stage" id="lotteryStage">', '<div class="lottery-stage arcade" id="lotteryStage">')
rep('<canvas id="lotWheelCanvas" width="600" height="600"></canvas>', '<canvas id="lotWheelCanvas" width="1000" height="1000"></canvas>')
rep('''            <div class="lot-anim lot-gacha" id="lotGacha" hidden>
              <div class="lot-gacha-globe" id="lotGachaGlobe"></div>
              <div class="lot-gacha-base">
                <div class="lot-gacha-knob"></div>
                <div class="lot-gacha-chute"></div>
                <div class="lot-gacha-capsule"><div class="cap-bottom"></div><div class="lot-gacha-prize" id="lotGachaPrize"></div><div class="cap-top"></div></div>
              </div>
            </div>''', '''            <div class="lot-anim lot-gacha" id="lotGacha" hidden>
              <canvas id="lotGachaCanvas"></canvas>
            </div>''')

# ------------------------------------------------------------------ JS：Arcade 引擎（放在吉祥物 helpers 後面）
ENGINE = r'''
  // =================================================================
  // 🎮 Arcade 引擎（班級工具遊戲化）：畫布層、星空、粒子特效、圓形物理
  // =================================================================
  const Arcade = (() => {
    const tickers = new Set();
    let raf = 0, last = 0;
    function loop(now) {
      const dt = Math.min(1 / 30, (now - (last || now)) / 1000);
      last = now;
      let alive = false;
      tickers.forEach(t => { if (t.active()) { alive = true; t.tick(dt, now / 1000); } });
      if (alive) raf = requestAnimationFrame(loop); else { raf = 0; last = 0; }
    }
    function wake() { if (!raf) raf = requestAnimationFrame(loop); }
    function add(t) { tickers.add(t); wake(); return t; }
    const shown = el => !!el && el.getClientRects().length > 0;
    // 跟著宿主大小的畫布（高解析度螢幕不糊）
    function layer(host, cls) {
      const canvas = document.createElement('canvas');
      canvas.className = cls;
      host.insertBefore(canvas, host.firstChild);
      const ctx = canvas.getContext('2d');
      const L = { canvas, ctx, w: 1, h: 1, resize() {
        const r = host.getBoundingClientRect();
        if (!r.width) return;
        const dpr = Math.min(2, window.devicePixelRatio || 1);
        L.w = r.width; L.h = r.height;
        canvas.width = Math.round(r.width * dpr); canvas.height = Math.round(r.height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      } };
      if (window.ResizeObserver) new ResizeObserver(() => L.resize()).observe(host);
      L.resize();
      return L;
    }
    function hexRgb(hex) { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
    function shade(hex, k) {   // k>0 變亮、k<0 變暗
      const [r, g, b] = hexRgb(hex);
      const f = v => Math.round(k >= 0 ? v + (255 - v) * k : v * (1 + k));
      return `rgb(${f(r)},${f(g)},${f(b)})`;
    }
    // 星空：閃爍＋緩慢漂移
    function starfield(count) {
      const stars = Array.from({ length: count }, () => ({ x: Math.random(), y: Math.random(), z: .25 + Math.random() * .75, p: Math.random() * 6.28 }));
      return function draw(ctx, w, h, t, speed) {
        ctx.clearRect(0, 0, w, h);
        stars.forEach(st => {
          st.x -= .0025 * st.z * (speed || 1) / 30;
          if (st.x < 0) st.x += 1;
          const a = (.3 + .7 * (.5 + .5 * Math.sin(t * (1.2 + st.z * 2) + st.p))) * st.z;
          ctx.globalAlpha = a; ctx.fillStyle = st.z > .85 ? '#ffe9a8' : '#ffffff';
          ctx.beginPath(); ctx.arc(st.x * w, st.y * h, .6 + st.z * 1.5, 0, 6.283); ctx.fill();
        });
        ctx.globalAlpha = 1;
      };
    }
    // 粒子：火花、碎片、衝擊波、描邊飄字
    const PAL = ['#ffd166', '#ff6b6b', '#4dd4ff', '#9b5de5', '#6bcb77', '#ff9f43', '#ffffff'];
    function fx() {
      const parts = [], rings = [], texts = [];
      return {
        burst(x, y, o = {}) {
          const n = o.count || 40, colors = o.colors || PAL;
          for (let i = 0; i < n; i += 1) {
            const a = o.angle != null ? o.angle + (Math.random() - .5) * (o.spread || 1) : Math.random() * 6.283;
            const sp = (o.speed || 520) * (.3 + Math.random() * .7);
            const life = (o.life || .9) * (.6 + Math.random() * .6);
            parts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life, max: life, size: (o.size || 6) * (.55 + Math.random() * .9),
              color: colors[i % colors.length], g: o.gravity != null ? o.gravity : 700, drag: o.drag != null ? o.drag : 1.8,
              shape: o.shape || (i % 3 === 0 ? 'star' : i % 3 === 1 ? 'spark' : 'chip'), rot: Math.random() * 6.28, vr: (Math.random() - .5) * 14 });
          }
        },
        ring(x, y, o = {}) { rings.push({ x, y, r0: o.r0 || 8, r1: o.r || 160, life: o.life || .55, max: o.life || .55, color: o.color || '#ffffff', w: o.width || 8 }); },
        text(x, y, str, o = {}) { texts.push({ x, y, str, life: o.life || 1.1, max: o.life || 1.1, size: o.size || 52, color: o.color || '#ffd166', vy: o.vy != null ? o.vy : -110 }); },
        busy() { return parts.length + rings.length + texts.length > 0; },
        update(dt) {
          for (let i = parts.length - 1; i >= 0; i -= 1) {
            const p = parts[i];
            p.life -= dt; if (p.life <= 0) { parts.splice(i, 1); continue; }
            p.vx -= p.vx * p.drag * dt; p.vy -= p.vy * p.drag * dt; p.vy += p.g * dt;
            p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.vr * dt;
          }
          for (let i = rings.length - 1; i >= 0; i -= 1) { rings[i].life -= dt; if (rings[i].life <= 0) rings.splice(i, 1); }
          for (let i = texts.length - 1; i >= 0; i -= 1) { const t = texts[i]; t.life -= dt; t.y += t.vy * dt; t.vy *= .96; if (t.life <= 0) texts.splice(i, 1); }
        },
        draw(ctx) {
          rings.forEach(r => {
            const k = 1 - r.life / r.max, e = 1 - Math.pow(1 - k, 3);
            ctx.globalAlpha = 1 - k; ctx.strokeStyle = r.color; ctx.lineWidth = r.w * (1 - k * .7);
            ctx.beginPath(); ctx.arc(r.x, r.y, r.r0 + (r.r1 - r.r0) * e, 0, 6.283); ctx.stroke();
          });
          ctx.globalCompositeOperation = 'lighter';
          parts.forEach(p => {
            const a = Math.min(1, p.life / p.max * 1.6);
            ctx.globalAlpha = a; ctx.fillStyle = p.color; ctx.strokeStyle = p.color;
            if (p.shape === 'spark') {
              ctx.lineWidth = p.size * .45; ctx.lineCap = 'round';
              ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * .04, p.y - p.vy * .04); ctx.stroke();
            } else if (p.shape === 'star') {
              ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.beginPath();
              for (let k = 0; k < 10; k += 1) { const rr = k % 2 ? p.size * .45 : p.size; const aa = k * Math.PI / 5; ctx.lineTo(Math.cos(aa) * rr, Math.sin(aa) * rr); }
              ctx.closePath(); ctx.fill(); ctx.restore();
            } else {
              ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * .66); ctx.restore();
            }
          });
          ctx.globalCompositeOperation = 'source-over';
          texts.forEach(t => {
            const age = 1 - t.life / t.max;
            const pop = 1 + .6 * Math.max(0, 1 - age * 7);
            ctx.globalAlpha = Math.min(1, t.life / t.max * 2.5);
            ctx.save(); ctx.translate(t.x, t.y); ctx.scale(pop, pop);
            ctx.font = `900 ${t.size}px "Noto Sans TC","Microsoft JhengHei",sans-serif`;
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
            ctx.lineWidth = t.size * .2; ctx.strokeStyle = '#2a1a5e'; ctx.strokeText(t.str, 0, 0);
            ctx.fillStyle = t.color; ctx.fillText(t.str, 0, 0);
            ctx.restore();
          });
          ctx.globalAlpha = 1;
        }
      };
    }
    // 圓形物理：重力、球與球碰撞、罐子（開口朝上的 U 形）與圓形罩邊界
    function world(o = {}) {
      const W = { bodies: [], gx: 0, gy: o.gravity != null ? o.gravity : 2000, jars: [], domes: [] };
      W.add = b => { b.vx = b.vx || 0; b.vy = b.vy || 0; b.m = b.r * b.r; b.rot = b.rot || 0; W.bodies.push(b); return b; };
      function pair(a, b) {
        const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy), min = a.r + b.r;
        if (d >= min || d === 0) return;
        const nx = dx / d, ny = dy / d, ia = a.fixed ? 0 : 1 / a.m, ib = b.fixed ? 0 : 1 / b.m, sum = ia + ib;
        if (!sum) return;
        const ov = (min - d) / sum;
        a.x -= nx * ov * ia; a.y -= ny * ov * ia; b.x += nx * ov * ib; b.y += ny * ov * ib;
        const rv = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny;
        if (rv > 0) return;
        const jn = -(1 + .28) * rv / sum;
        a.vx -= jn * nx * ia; a.vy -= jn * ny * ia; b.vx += jn * nx * ib; b.vy += jn * ny * ib;
        const tx = -ny, ty = nx, rt = (b.vx - a.vx) * tx + (b.vy - a.vy) * ty, jt = -rt * .15 / sum;
        a.vx -= jt * tx * ia; a.vy -= jt * ty * ia; b.vx += jt * tx * ib; b.vy += jt * ty * ib;
        if (Math.abs(rv) > 260 && W.onHit) W.onHit(Math.abs(rv));
      }
      function jar(b, j) {
        if (b.x < j.x0 - b.r || b.x > j.x1 + b.r || b.y + b.r < j.y0) return;
        if (b.x - b.r < j.x0) { b.x = j.x0 + b.r; b.vx = Math.abs(b.vx) * .3; }
        if (b.x + b.r > j.x1) { b.x = j.x1 - b.r; b.vx = -Math.abs(b.vx) * .3; }
        if (b.y + b.r > j.y1) { b.y = j.y1 - b.r; if (b.vy > 0) { if (b.vy > 300 && W.onHit) W.onHit(b.vy); b.vy = -b.vy * .3; } b.vx *= .94; }
      }
      function dome(b, c) {
        const dx = b.x - c.x, dy = b.y - c.y, d = Math.hypot(dx, dy) || 1, lim = c.r - b.r;
        if (d <= lim) return;
        const nx = dx / d, ny = dy / d;
        b.x = c.x + nx * lim; b.y = c.y + ny * lim;
        const vn = b.vx * nx + b.vy * ny;
        if (vn > 0) { b.vx -= 1.35 * vn * nx; b.vy -= 1.35 * vn * ny; }
      }
      W.step = dt => {
        const sub = 5, h = dt / sub;
        for (let s = 0; s < sub; s += 1) {
          W.bodies.forEach(b => {
            if (b.fixed) return;
            b.vx += W.gx * h; b.vy += W.gy * h;
            b.vx *= .9995; b.vy *= .9995;
            b.x += b.vx * h; b.y += b.vy * h; b.rot += b.vx * h / b.r;
          });
          for (let i = 0; i < W.bodies.length; i += 1) for (let k = i + 1; k < W.bodies.length; k += 1) pair(W.bodies[i], W.bodies[k]);
          W.bodies.forEach(b => { if (b.fixed) return; W.jars.forEach(j => jar(b, j)); W.domes.forEach(c => dome(b, c)); });
        }
      };
      return W;
    }
    // 像行星一樣的球：漸層＋條紋＋高光＋描邊號碼
    function ball(ctx, b, label) {
      const { x, y, r } = b, c = b.color || '#4d96ff';
      const g = ctx.createRadialGradient(x - r * .38, y - r * .42, r * .08, x, y, r);
      g.addColorStop(0, shade(c, .55)); g.addColorStop(.5, c); g.addColorStop(1, shade(c, -.45));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.clip();
      ctx.translate(x, y); ctx.rotate(b.rot || 0);
      ctx.fillStyle = 'rgba(255,255,255,.16)'; ctx.fillRect(-r, -r * .18, r * 2, r * .2); ctx.fillRect(-r, r * .3, r * 2, r * .12);
      ctx.restore();
      ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.ellipse(x - r * .35, y - r * .45, r * .32, r * .18, -.6, 0, 6.283); ctx.fill();
      ctx.lineWidth = Math.max(1.5, r * .08); ctx.strokeStyle = 'rgba(20,10,50,.55)'; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.stroke();
      if (label != null && label !== '') {
        const fs = r * (String(label).length > 2 ? .72 : .95);
        ctx.font = `900 ${fs}px "Noto Sans TC","Microsoft JhengHei",sans-serif`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
        ctx.lineWidth = fs * .26; ctx.strokeStyle = 'rgba(25,15,60,.9)'; ctx.strokeText(label, x, y + fs * .04);
        ctx.fillStyle = '#fff'; ctx.fillText(label, x, y + fs * .04);
      }
    }
    function flash(host) { const f = document.createElement('div'); f.className = 'arcade-flash'; host.appendChild(f); setTimeout(() => f.remove(), 500); }
    function shake(host) { host.classList.remove('shake'); void host.offsetWidth; host.classList.add('shake'); }
    // 一個舞台＝星空背景層＋特效層，只有看得到時才跑
    function stage(host, opts = {}) {
      const bg = layer(host, 'arcade-bg'), top = layer(host, 'arcade-fx');
      const stars = starfield(opts.stars || 90);
      const fxs = fx();
      const S = { host, bg, top, fx: fxs, speed: 1, extra: null,
        local(el) { const a = el.getBoundingClientRect(), h = host.getBoundingClientRect(); return { x: a.left - h.left + a.width / 2, y: a.top - h.top + a.height / 2, w: a.width, h: a.height }; } };
      add({ active: () => shown(host), tick(dt, t) {
        stars(bg.ctx, bg.w, bg.h, t, S.speed);
        fxs.update(dt);
        top.ctx.clearRect(0, 0, top.w, top.h);
        if (S.extra) S.extra(dt, t);
        fxs.draw(top.ctx);
      } });
      return S;
    }
    return { add, wake, shown, layer, stage, fx, world, ball, shade, flash, shake, PAL };
  })();
  const CANDY = ['#ff6b6b', '#ffb347', '#ffd93d', '#6bcb77', '#4d96ff', '#9b5de5', '#f15bb5'];
'''
rep("  const REDUCED_MOTION_ALL = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;",
    "  const REDUCED_MOTION_ALL = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;" + ENGINE)

# ------------------------------------------------------------------ JS：抽籤舞台＋粒子取代舊紙屑
rep('''  // ---- 跑馬燈燈泡：繞轉盤一圈，轉動時加速 ----
  const lotStage = $('lotteryStage');''', '''  // ---- 跑馬燈燈泡：繞轉盤一圈，轉動時加速 ----
  const lotStage = $('lotteryStage');
  const lotArcade = Arcade.stage(lotStage, { stars: 110 });''')
rep('''  function burstConfetti() {
    const stage = $('lotteryStage');''', '''  function burstConfetti() {
    // 遊戲化：揭曉時閃光＋衝擊波＋彩色粒子（畫在舞台特效層）
    const at = lotArcade.local($('lotResult'));
    Arcade.flash(lotStage);
    lotArcade.fx.ring(at.x, at.y, { r: 260, width: 14, color: '#ffd166', life: .6 });
    lotArcade.fx.ring(at.x, at.y, { r: 180, width: 8, color: '#4dd4ff', life: .45 });
    lotArcade.fx.burst(at.x, at.y, { count: 120, speed: 900, life: 1.3, gravity: 900, size: 9 });
    lotArcade.fx.burst(at.x, at.y - 40, { count: 40, speed: 420, life: 1.8, gravity: 260, shape: 'star', size: 12, colors: ['#ffd166', '#fff3b0'] });
    Arcade.wake();
    return;
    const stage = $('lotteryStage');''')

# ------------------------------------------------------------------ JS：新轉盤（光澤盤面、燈泡、釘子、會被撥動的指針）
rep('''  function drawWheel(rotation, highlightIndex = -1) {
    const pool = remainingPool();
    const n = pool.length;
    wctx.clearRect(0, 0, 600, 600);
    wctx.save();
    wctx.translate(300, 300);''', '''  const wheelFx = { flap: 0, flapV: 0, speed: 0, bulbPhase: 0, win: -1, winAt: 0 };
  function drawWheel(rotation, highlightIndex = -1) {
    if (highlightIndex >= 0) { wheelFx.win = highlightIndex; wheelFx.winAt = performance.now(); }
    if (highlightIndex < 0 && !lotteryBusy && wheelFx.win >= 0 && performance.now() - wheelFx.winAt > 60000) wheelFx.win = -1;
    drawArcadeWheel(rotation);
  }
  function drawArcadeWheel(rotation) {
    const pool = remainingPool();
    const n = pool.length;
    const c = wctx, K = 1000 / 600;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, 1000, 1000);
    c.setTransform(K, 0, 0, K, 0, 0);
    // 外框（深紫金屬環）
    const rim = c.createRadialGradient(300, 300, 270, 300, 300, 300);
    rim.addColorStop(0, '#5b3fb0'); rim.addColorStop(.6, '#2a1a5e'); rim.addColorStop(1, '#140c33');
    c.fillStyle = rim; c.beginPath(); c.arc(300, 300, 298, 0, 6.283); c.fill();
    c.lineWidth = 3; c.strokeStyle = '#ffd166'; c.beginPath(); c.arc(300, 300, 276, 0, 6.283); c.stroke();
    // 燈泡：轉越快、追逐越快
    const bulbs = 30;
    for (let i = 0; i < bulbs; i += 1) {
      const a = i / bulbs * Math.PI * 2;
      const on = ((i + Math.floor(wheelFx.bulbPhase)) % 3) === 0;
      const bx = 300 + Math.cos(a) * 288, by = 300 + Math.sin(a) * 288;
      if (on) { c.shadowColor = '#ffd166'; c.shadowBlur = 18; }
      c.fillStyle = on ? '#fff6c8' : '#8a6a2a';
      c.beginPath(); c.arc(bx, by, on ? 6.5 : 5, 0, 6.283); c.fill();
      c.shadowBlur = 0;
    }
    c.save();
    c.translate(300, 300);
    if (!n) {
      c.fillStyle = '#2a1a5e'; c.beginPath(); c.arc(0, 0, 272, 0, 6.283); c.fill();
      c.fillStyle = '#ffd166'; c.font = '900 40px "Noto Sans TC","Microsoft JhengHei"'; c.textAlign = 'center';
      c.fillText('抽完了 🎉', 0, 14); c.restore(); return;
    }
    const seg = Math.PI * 2 / n;
    c.rotate(rotation);
    const pulse = wheelFx.win >= 0 ? .5 + .5 * Math.sin(performance.now() / 120) : 0;
    for (let i = 0; i < n; i += 1) {
      const start = -Math.PI / 2 + i * seg;
      let color = CANDY[i % CANDY.length];
      if (i === n - 1 && n > 1 && color === CANDY[0]) color = CANDY[3];
      const g = c.createRadialGradient(0, 0, 30, 0, 0, 272);
      const isWin = i === wheelFx.win;
      g.addColorStop(0, Arcade.shade(color, -.35)); g.addColorStop(.7, color); g.addColorStop(1, Arcade.shade(color, isWin ? .5 : .18));
      c.fillStyle = g;
      c.beginPath(); c.moveTo(0, 0); c.arc(0, 0, 272, start, start + seg); c.closePath(); c.fill();
      if (isWin) { c.fillStyle = `rgba(255,255,255,${.25 + .35 * pulse})`; c.fill(); }
      c.strokeStyle = 'rgba(255,233,168,.95)'; c.lineWidth = n > 30 ? 1.5 : 3; c.stroke();
      // 號碼（描邊白字）
      c.save();
      c.rotate(start + seg / 2);
      c.textAlign = 'right'; c.textBaseline = 'middle';
      const fontSize = n <= 10 ? 50 : n <= 16 ? 40 : n <= 26 ? 31 : n <= 40 ? 22 : 15;
      c.font = `900 ${fontSize}px "Noto Sans TC","Microsoft JhengHei"`;
      const label = String(pool[i]).length > 4 ? String(pool[i]).slice(0, 4) + '…' : String(pool[i]);
      c.lineJoin = 'round'; c.lineWidth = fontSize * .22; c.strokeStyle = 'rgba(30,15,70,.85)';
      c.strokeText(label, 246, 0);
      c.fillStyle = '#fff'; c.fillText(label, 246, 0);
      c.restore();
      // 釘子（在格線外緣）
      c.save(); c.rotate(start);
      c.fillStyle = '#ffd166'; c.beginPath(); c.arc(262, 0, n > 30 ? 3 : 5, 0, 6.283); c.fill();
      c.restore();
    }
    c.restore();
    // 光澤（不跟著轉）
    const gloss = c.createLinearGradient(80, 60, 400, 420);
    gloss.addColorStop(0, 'rgba(255,255,255,.32)'); gloss.addColorStop(.45, 'rgba(255,255,255,.04)'); gloss.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = gloss; c.beginPath(); c.arc(300, 300, 272, 0, 6.283); c.fill();
    // 指針：上方的紅色撥片，被釘子撥到會擺動
    c.save();
    c.translate(300, 6);
    c.rotate(wheelFx.flap);
    c.shadowColor = 'rgba(0,0,0,.45)'; c.shadowBlur = 10; c.shadowOffsetY = 4;
    const pg = c.createLinearGradient(-22, 0, 22, 0);
    pg.addColorStop(0, '#ff8a80'); pg.addColorStop(.5, '#ff3b3b'); pg.addColorStop(1, '#b3122a');
    c.fillStyle = pg;
    c.beginPath(); c.moveTo(-22, 0); c.quadraticCurveTo(-24, 30, 0, 64); c.quadraticCurveTo(24, 30, 22, 0); c.arc(0, 0, 22, 0, Math.PI, true); c.fill();
    c.shadowBlur = 0; c.shadowOffsetY = 0;
    c.fillStyle = '#fff3b0'; c.beginPath(); c.arc(0, 2, 9, 0, 6.283); c.fill();
    c.restore();
  }
  // 撥片彈簧、燈泡追逐、得獎格閃爍：在背景持續更新
  Arcade.add({ active: () => Arcade.shown(wheelCanvas) && (lotteryBusy || Math.abs(wheelFx.flap) > .002 || wheelFx.win >= 0 || true), tick(dt) {
    wheelFx.flapV += (-180 * wheelFx.flap - 14 * wheelFx.flapV) * dt;
    wheelFx.flap += wheelFx.flapV * dt;
    wheelFx.flap = Math.max(-.9, Math.min(.9, wheelFx.flap));
    wheelFx.bulbPhase += dt * (2.2 + Math.min(40, wheelFx.speed * 2.2));
    if (!lotteryBusy) drawArcadeWheel(wheelRotation);
  } });
  function legacyDrawWheel(rotation, highlightIndex = -1) {
    const pool = remainingPool();
    const n = pool.length;
    wctx.clearRect(0, 0, 600, 600);
    wctx.save();
    wctx.translate(300, 300);''')

# 轉動：更長的減速、速度驅動燈泡與撥片、每過一根釘子撥一下＋音效、停下時衝擊
rep('''    const duration = 4300;
    const startTime = performance.now();
    let lastTickIndex = -1;
    const pointer = $('lotPointer');
    const frame = now => {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - t, 4);   // easeOutQuart：後段緩慢滑行、充滿懸念
      wheelRotation = startRotation + total * eased;
      drawWheel(wheelRotation);
      const pointerIndex = Math.floor(((((-Math.PI / 2 - wheelRotation) % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2)) / seg + .5);
      if (pointerIndex !== lastTickIndex) {
        lastTickIndex = pointerIndex;
        pointer.classList.remove('tick'); void pointer.offsetWidth; pointer.classList.add('tick');
        if ($('lotSound').checked && t < .96) beep(1180, .035, 'square', .05);
      }
      if (t < 1) { requestAnimationFrame(frame); }
      else { drawWheel(wheelRotation, pickedIndex); done(); }
    };
    requestAnimationFrame(frame);''', '''    const duration = 5600;
    const startTime = performance.now();
    let lastPeg = Math.floor(startRotation / seg);
    wheelFx.win = -1;
    const P = 3.6;   // 減速曲線：前段飛快、後段一格一格爬，懸念拉滿
    const frame = now => {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - t, P);
      wheelRotation = startRotation + total * eased;
      wheelFx.speed = total * P * Math.pow(1 - t, P - 1) / (duration / 1000);   // 弧度／秒
      const peg = Math.floor(wheelRotation / seg);
      if (peg !== lastPeg) {
        lastPeg = peg;
        wheelFx.flapV -= Math.min(14, 2.5 + wheelFx.speed * .35);
        if ($('lotSound').checked) beep(900 + Math.min(500, wheelFx.speed * 30), .03, 'square', .045);
      }
      drawArcadeWheel(wheelRotation);
      if (t < 1) { requestAnimationFrame(frame); }
      else {
        wheelFx.speed = 0;
        drawWheel(wheelRotation, pickedIndex);
        const wrap = document.querySelector('.lot-wheel-wrap');
        wrap.classList.remove('punch'); void wrap.offsetWidth; wrap.classList.add('punch');
        const top = lotArcade.local(wheelCanvas);
        lotArcade.fx.ring(top.x, top.y - top.h / 2 + 40, { r: 120, width: 10, color: '#ff6b6b', life: .5 });
        lotArcade.fx.burst(top.x, top.y - top.h / 2 + 40, { count: 50, speed: 600, life: .9, gravity: 900 });
        Arcade.shake(lotStage);
        done();
      }
    };
    requestAnimationFrame(frame);''')

# ------------------------------------------------------------------ JS：扭蛋機改成真的物理球罩
rep('''  // ---- 扭蛋機：小球翻滾 → 轉柄 → 膠囊掉落 → 彈開 ----
  const gachaBalls = [];
  (function buildGachaBalls() {''', '''  // ---- 扭蛋機（遊戲化）：所有座號變成小球，在玻璃罩裡真的翻滾碰撞 ----
  const gacha = { canvas: $('lotGachaCanvas'), world: null, crank: 0, stir: 0, prize: null, key: '' };
  gacha.ctx = gacha.canvas.getContext('2d');
  const GW = 340, GH = 430, DOME = { x: 170, y: 162, r: 140 };
  function sizeGacha() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const rect = gacha.canvas.getBoundingClientRect();
    const scale = rect.width ? rect.width / GW : 1;
    gacha.canvas.width = Math.round(GW * scale * dpr); gacha.canvas.height = Math.round(GH * scale * dpr);
    gacha.ctx.setTransform(scale * dpr, 0, 0, scale * dpr, 0, 0);
  }
  function buildGachaWorld() {
    const pool = remainingPool().filter(v => !gacha.prize || v !== gacha.prize.label);
    gacha.key = pool.join(',');
    const W = Arcade.world({ gravity: 1500 });
    W.domes.push(DOME);
    const r = Math.max(10, Math.min(22, Math.sqrt(DOME.r * DOME.r * .5 / Math.max(1, pool.length))));
    pool.forEach((label, i) => {
      const a = Math.random() * 6.283, d = Math.random() * (DOME.r - r - 6);
      W.add({ x: DOME.x + Math.cos(a) * d, y: DOME.y + Math.sin(a) * d * .6 + 30, r, label, color: CANDY[i % CANDY.length] });
    });
    W.onHit = v => { if (gacha.stir > 0 && $('lotSound').checked && Math.random() < .08) beep(500 + Math.random() * 500, .02, 'triangle', .03); };
    gacha.world = W;
  }
  function drawGacha() {
    const c = gacha.ctx;
    c.clearRect(0, 0, GW, GH);
    // 底座
    const base = c.createLinearGradient(0, 270, 0, 420);
    base.addColorStop(0, '#ff7b7b'); base.addColorStop(.5, '#e53950'); base.addColorStop(1, '#9e1b37');
    c.fillStyle = base; c.beginPath(); c.roundRect(46, 268, 248, 150, [26, 26, 30, 30]); c.fill();
    c.fillStyle = 'rgba(255,255,255,.25)'; c.beginPath(); c.roundRect(60, 278, 220, 18, 9); c.fill();
    // 出口
    c.fillStyle = '#2a0f22'; c.beginPath(); c.roundRect(196, 330, 76, 62, 16); c.fill();
    c.fillStyle = 'rgba(255,255,255,.12)'; c.fillRect(202, 336, 64, 8);
    // 轉柄
    c.save(); c.translate(120, 350); c.rotate(gacha.crank);
    c.fillStyle = '#fff6e0'; c.beginPath(); c.arc(0, 0, 30, 0, 6.283); c.fill();
    c.lineWidth = 6; c.strokeStyle = '#7c2b3c'; c.stroke();
    c.fillStyle = '#7c2b3c'; c.beginPath(); c.roundRect(-24, -7, 48, 14, 7); c.fill();
    c.restore();
    // 球罩底環
    c.fillStyle = '#5b3fb0'; c.beginPath(); c.ellipse(DOME.x, 286, 120, 20, 0, 0, 6.283); c.fill();
    // 球罩玻璃（內側）
    c.save(); c.beginPath(); c.arc(DOME.x, DOME.y, DOME.r, 0, 6.283); c.clip();
    const glass = c.createRadialGradient(DOME.x - 50, DOME.y - 60, 20, DOME.x, DOME.y, DOME.r);
    glass.addColorStop(0, 'rgba(255,255,255,.18)'); glass.addColorStop(1, 'rgba(140,170,255,.10)');
    c.fillStyle = glass; c.fillRect(0, 0, GW, GH);
    gacha.world.bodies.forEach(b => Arcade.ball(c, b, b.label));
    c.restore();
    // 玻璃反光與外框
    c.lineWidth = 6; c.strokeStyle = 'rgba(255,255,255,.55)'; c.beginPath(); c.arc(DOME.x, DOME.y, DOME.r, 0, 6.283); c.stroke();
    c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 10; c.lineCap = 'round';
    c.beginPath(); c.arc(DOME.x, DOME.y, DOME.r - 22, Math.PI * 1.08, Math.PI * 1.38); c.stroke();
    c.lineWidth = 6; c.beginPath(); c.arc(DOME.x, DOME.y, DOME.r - 22, Math.PI * 1.45, Math.PI * 1.52); c.stroke();
    // 掉出來的那顆
    if (gacha.prize) Arcade.ball(c, gacha.prize, gacha.prize.label);
  }
  Arcade.add({ active: () => Arcade.shown(gacha.canvas), tick(dt, t) {
    if (!gacha.world || (!gacha.prize && !lotteryBusy && gacha.key !== remainingPool().join(','))) { sizeGacha(); buildGachaWorld(); }
    if (gacha.stir > 0) {
      gacha.stir -= dt;
      gacha.crank += dt * 9;
      const ang = t * 7;
      gacha.world.gx = Math.cos(ang) * 2600; gacha.world.gy = Math.sin(ang) * 2600 - 400;
      gacha.world.bodies.forEach(b => { b.vx += (Math.random() - .5) * 2600 * dt; b.vy += (Math.random() - .5) * 2600 * dt; });
    } else { gacha.world.gx = 0; gacha.world.gy = 1500; }
    gacha.world.step(dt);
    if (gacha.prize && gacha.prize.anim) gacha.prize.anim(dt);
    drawGacha();
  } });
  function runGacha(picked, done) {
    sizeGacha();
    gacha.prize = null;
    buildGachaWorld();
    gacha.stir = 2.0;
    const sound = $('lotSound').checked;
    if (sound) { let c = 0; const ti = setInterval(() => { beep(200 + Math.random() * 160, .05, 'square', .05); if (++c > 12) clearInterval(ti); }, 150); }
    setTimeout(() => {
      // 抽中的球從罩底出口掉到出貨口
      const W = gacha.world;
      let body = W.bodies.find(b => b.label === picked);
      if (!body) return done();
      W.bodies.splice(W.bodies.indexOf(body), 1);
      const from = { x: body.x, y: body.y };
      const prize = { x: from.x, y: from.y, r: body.r, label: picked, color: body.color, rot: 0, t: 0 };
      const path = [from, { x: DOME.x, y: DOME.y + DOME.r - body.r }, { x: 234, y: 300 }, { x: 234, y: 360 }];
      prize.anim = dt => {
        prize.t += dt;
        const T = prize.t;
        if (T < .55) {   // 沿罩底滑到出口、往下掉
          const k = T / .55, e = k * k;
          const seg = Math.min(2, Math.floor(e * 3)), f = e * 3 - seg;
          prize.x = path[seg].x + (path[seg + 1].x - path[seg].x) * f;
          prize.y = path[seg].y + (path[seg + 1].y - path[seg].y) * f;
          prize.rot += dt * 10;
        } else if (T < 1.1) {   // 在出貨口彈兩下
          const k = (T - .55) / .55;
          prize.x = 234; prize.y = 360 - Math.abs(Math.sin(k * Math.PI * 2.2)) * 40 * (1 - k);
        } else if (T < 1.6) {   // 放大準備爆開
          const k = (T - 1.1) / .5;
          prize.r = body.r + (52 - body.r) * (1 - Math.pow(1 - k, 3));
          prize.y = 360 - 70 * k; prize.x = 234 - 60 * k;
        } else if (!prize.popped) {
          prize.popped = true;
          const at = lotArcade.local(gacha.canvas);
          const sx = at.x - at.w / 2 + (prize.x / GW) * at.w, sy = at.y - at.h / 2 + (prize.y / GH) * at.h;
          lotArcade.fx.ring(sx, sy, { r: 150, width: 10, color: '#ffd166' });
          lotArcade.fx.burst(sx, sy, { count: 70, speed: 700, life: 1, gravity: 900 });
          if (sound) beep(880, .14);
          gacha.prize = null;
          done();
        }
      };
      gacha.prize = prize;
      if (sound) beep(180, .2, 'square', .12);
    }, 2000);
  }
  const gachaBalls = [];
  (function buildGachaBalls() {
    if (!$('lotGachaGlobe')) return;''')
rep('''  function gachaTumble(active) {
    if (!active) { if (gachaTumbleRaf) cancelAnimationFrame(gachaTumbleRaf); gachaTumbleRaf = 0; return; }''', '''  function gachaTumble(active) {
    if (!$('lotGachaGlobe')) return;
    if (!active) { if (gachaTumbleRaf) cancelAnimationFrame(gachaTumbleRaf); gachaTumbleRaf = 0; return; }''')
rep('''  function runGacha(picked, done) {
    const gacha = $('lotGacha');
    gacha.classList.remove('dropped', 'opened');''', '''  function legacyRunGacha(picked, done) {
    const gacha = $('lotGacha');
    gacha.classList.remove('dropped', 'opened');''')
rep("    $('lotGacha').classList.remove('dropped', 'opened');\n    lotStage.classList.remove('revealed', 'spinning');",
    "    lotStage.classList.remove('revealed', 'spinning');\n    gacha.prize = null; gacha.key = '';")
# 抽籤時不再顯示吉祥物（v4 動畫完成前先拿掉）
for old in ["    setMascot($('lotMascot'), 'sign', true);\n", "    setMascot($('lotMascot'), 'think', true);\n", "    setMascot($('lotMascot'), 'idle', true);\n", "  setMascot($('lotMascot'), 'idle');\n"]:
    rep(old, '')
# 轉盤停下要在「揭曉」前就畫好得獎格；轉動時 lotteryBusy 才會跑畫面
rep("    if (lotteryMode !== 'wheel') drawWheel(wheelRotation);   // 轉盤保留停格畫面到下一次抽", "    if (lotteryMode !== 'wheel') drawWheel(wheelRotation);   // 轉盤保留停格畫面到下一次抽\n    if (lotteryMode === 'gacha') gacha.key = '';")

path.write_text(s, encoding='utf-8')
print('ok', len(s))
