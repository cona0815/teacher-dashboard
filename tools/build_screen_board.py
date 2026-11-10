"""產生 Screen.html：班級工具「📺 螢幕公告」（老師 2026-11-04 要求，來源是老師自己的 cona0815/classboard，MIT 授權）
為了放進本系統，對原始 index.html 做這些調整：
- 本站的安全設定不允許外部資源：拿掉 Google Fonts、Lucide、html2canvas 的 CDN。
  字型改用 assets/fonts 的粉圓、芫荽（含注音）與系統字；工具列圖示改 emoji；匯出 PNG 用 assets/vendor/html2pdf（要用時才載入）
- 預設內容拿掉，打開是空白畫面：原本的 11/4 比賽範本是「每天重複」的定時，放進來會每天跳「比賽即將開始」。比賽設定可用「匯入設定」帶回來
- 拿掉比賽範本專用的舊存檔遷移與自動套用
- 內嵌在大屏時：全螢幕交給大屏（瀏覽器不給全螢幕時才有備援）；定時跳出提醒時，大屏自動切到這個工具
用法：python tools/build_screen_board.py <classboard 的 index.html>
"""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
s = Path(sys.argv[1]).read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)


# ---------- 開頭 ----------
first_line_end = s.index('\n')
s = s[first_line_end + 1:]
head = """<!doctype html>
<!-- 螢幕公告｜班級工具。源自 cona0815/classboard v3.5（MIT，原創程式與美術，與 Classroomscreen 無關）。由 tools/build_screen_board.py 產生，要改請改那支或上游。 -->
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' data: blob:; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'">
<!--
【資安說明】螢幕公告（2026-11-06 稽核）
- 匯入的設定檔可能是別人分享的：id 只收英數、圖片只收 data:image 網址（cleanImported），放進 HTML 的 id 一律 esc()。
- 本頁與大屏同網站，被嵌在大屏裡；資料只存這台電腦。
-->
<script>
  // 資安：防點擊劫持。別的網站把本頁塞進 iframe 時改成整頁開啟（同網站的嵌入不受影響）。
  // 正式站的 netlify.toml 已用標頭擋；這段是放在其他主機（如 GitHub Pages）時的備援。
  try { if (window.top !== window.self && window.top.location.origin !== window.location.origin) throw new Error('framed'); }
  catch (error) { document.documentElement.style.display = 'none'; try { window.top.location.href = window.location.href; } catch (ignored) {} }
</script>
"""
s = re.sub(r'<link rel="(?:preconnect|stylesheet)"[^>]*>\n', '', s)
s = re.sub(r'<script src="https://[^"]*"></script>\n', '', s)
assert 'https://fonts' not in s and 'cdn.jsdelivr' not in s and 'cdnjs' not in s
rep('<title>競賽公告螢幕</title>', '<title>螢幕公告</title>')
s = head + s
rep('<style>\n', """<style>
/* 字型都在本站（只有選到才會下載） */
@font-face{font-family:"Huninn";font-display:swap;src:local("Huninn"),local("Huninn Regular"),url("assets/fonts/Huninn-Regular.ttf") format("truetype")}
@font-face{font-family:"Iansui";font-display:swap;src:local("Iansui"),local("Iansui Regular"),url("assets/fonts/Iansui-Regular.ttf") format("truetype")}
@font-face{font-family:"Bpmf Huninn";font-display:swap;src:local("Bpmf Huninn"),local("Bpmf Huninn Regular"),url("assets/fonts/BpmfHuninn-Regular.ttf") format("truetype")}
@font-face{font-family:"Bpmf Iansui";font-display:swap;src:local("Bpmf Iansui"),local("Bpmf Iansui Regular"),url("assets/fonts/BpmfIansui-Regular.ttf") format("truetype")}
""")

# ---------- 字型：本站沒有的換成系統字 ----------
for old, new in [('LXGW WenKai TC', 'DFKai-SB'), ('Noto Sans TC', 'Microsoft JhengHei'), ('Noto Serif TC', 'PMingLiU'),
                 ('Bpmf Zihi Kai Std', 'Bpmf Iansui'), ('Fredoka', 'Segoe UI'), ('Orbitron', 'Consolas'), ('Caveat', 'Segoe Print')]:
    s = s.replace(old, new)

# ---------- 工具列圖示：emoji ----------
rep("""<i data-lucide="${META[t][1]}"></i><span>${META[t][0]}</span>""", """<span class="ic">${TOOL_EMOJI[t]||'▫️'}</span><span>${META[t][0]}</span>""")
rep("""<i data-lucide="calendar-clock"></i>""", """<span class="ic">📅</span>""")
rep("""<i data-lucide="maximize"></i>""", """<span class="ic">⛶</span>""")
rep("""<i data-lucide="volume-2"></i>""", """<span class="ic">🔊</span>""")
rep("""<i data-lucide="chevron-down"></i>""", """<span class="ic">▾</span>""")
rep("""<i data-lucide="palette"></i>""", """<span class="ic">🎨</span>""")
rep("""const ORDER=KEEP;""", """const ORDER=KEEP;
const TOOL_EMOJI={text:'📝',schedule:'📋',clock:'🕒',timer:'⏱️',countdown:'⏳',stopwatch:'⏲️',alarm:'⏰',interval:'🔔',image:'🖼️',draw:'✏️'};""")
rep(""".tb .ic{height:22px;display:grid;place-items:center;font-weight:700;color:var(--accent)}""",
    """.tb .ic{height:22px;display:grid;place-items:center;font-weight:700;font-size:19px;line-height:1;color:var(--accent)}""")

# ---------- 匯出 PNG：要用時才載入本站的 html2pdf（內含 html2canvas） ----------
rep("""  if(!window.html2canvas){toast('需要網路才能匯出圖片');return}
""", """  if(!window.html2pdf){await new Promise(res=>{const t=document.createElement('script');t.src='assets/vendor/html2pdf.bundle.min.js';t.onload=res;t.onerror=res;document.head.appendChild(t)})}
  if(!window.html2pdf){toast('匯出工具載入失敗，請重新整理再試');return}
""")
rep("""const c=await html2canvas(stage,{backgroundColor:getComputedStyle(document.body).getPropertyValue('--bg').trim()||null,scale:Math.min(2,devicePixelRatio||1),useCORS:true,logging:false});""",
    """// html2pdf 會把畫布複製到紙張大小的容器：先把畫布固定成實際尺寸，紙張也設一樣大，匯出後還原
    const R=stage.getBoundingClientRect(),W=Math.round(R.width),H=Math.round(R.height),oldCss=stage.getAttribute('style');
    stage.style.width=W+'px';stage.style.height=H+'px';stage.style.position='relative';stage.style.inset='auto';
    let c;try{c=await html2pdf().set({margin:0,jsPDF:{unit:'px',format:[W,H],hotfixes:['px_scaling']},html2canvas:{backgroundColor:getComputedStyle(document.body).getPropertyValue('--bg').trim()||null,scale:Math.min(2,devicePixelRatio||1),useCORS:true,logging:false,width:W,height:H}}).from(stage).toCanvas().get('canvas')}
    finally{if(oldCss===null)stage.removeAttribute('style');else stage.setAttribute('style',oldCss)}""")

# ---------- 預設內容：拿掉（老師 2026-11-04「預設拿掉」）：打開是一個空白畫面、沒有任何定時 ----------
start = s.index('function defaults(){')
end = s.index('let S,IMG={};')
s = s[:start] + """function defaults(){
  // 第一次打開跟著大屏風格：可愛溫暖風配小島，其他配軟木板
  let style='cork';try{if((JSON.parse(localStorage.getItem('morningBoardSettings')||'{}')||{}).boardStyle==='cozy')style='isle'}catch(e){}
  return{v:2,tpl:'blank',style,cur:0,z:20,bg:'default',font:'auto',dfont:'auto',rotate:{on:false,sec:30},names:'',jobs:[],
    screens:[{id:uid(),name:'畫面 1',widgets:[]}]};
}
""" + s[end:]

# 比賽範本專用的舊存檔遷移（本頁沒有舊存檔）
start = s.index('if(!S.mig27){S.mig27=1;')
end = s.index('let saveT,imgT;')
s = s[:start] + s[end:]
start = s.index("if(S.tpl!=='1104'){")
end = s.index("addEventListener('load',icons);")
s = s[:start] + s[end:]

# ---------- 文字 ----------
rep("""在家裡做好，匯出後帶到比賽的電腦匯入即可。""", """在家裡做好，匯出後帶到別台電腦匯入即可。""")
rep("""id="resetAll">載入 11/4 比賽範本</button>""", """id="resetAll">清空成空白畫面</button>""")
rep("""armed(e.target,'載入 11/4 比賽範本',""", """armed(e.target,'清空成空白畫面',""")
rep("""saveFile('競賽公告螢幕設定_'""", """saveFile('螢幕公告設定_'""")
rep("""<div class="ver">v3.5 · 2026-11-04　快捷鍵：""", """<div class="ver">快捷鍵：""")
rep("""/* 競賽公告螢幕 v3.5 · 2026-11-04 */""", """/* 螢幕公告（源自 classboard v3.5） */""")

s = s.replace('「比賽中」', '「考試中」')

# ---------- 文字可以換顏色（老師 2026-11-04）：色票＋自選 ----------
rep("""    el(node){box.appendChild(node);return this},""", """    el(node){box.appendChild(node);return this},
    colors(l,get,set){const r=row(l),wrap=document.createElement('div');wrap.className='swatches';
      const mark=()=>wrap.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x.dataset.c===get()));
      TEXT_COLORS.forEach(([v,t])=>{const b=document.createElement('button');b.type='button';b.className='swatch';b.title=t;b.setAttribute('aria-label',t);b.dataset.c=v;b.style.background=COLV[v]||v;b.onclick=()=>{set(v);mark();done()};wrap.appendChild(b)});
      const pick=document.createElement('label');pick.className='swatch-pick';pick.textContent='自選 ';const i=document.createElement('input');i.type='color';i.id='f'+uid();i.value=/^#/.test(get())?get():'#2c7be5';i.oninput=()=>{set(i.value);mark();done()};pick.appendChild(i);wrap.appendChild(pick);
      r.appendChild(wrap);mark();return this},""")
rep("""function form(box,W){""", """const TEXT_COLORS=[['ink','一般'],['#d93025','紅'],['#e8710a','橘'],['#b88a00','金'],['#188038','綠'],['#0b7fb5','藍'],['#6a3fb5','紫'],['#d6336c','粉'],['#ffffff','白']];
function form(box,W){""")
rep(""".seg('顏色',[['ink','一般'],['accent','強調'],['hot','醒目']],()=>W.d.color,v=>W.d.color=v).note(""", """.colors('顏色',()=>W.d.color,v=>W.d.color=v).note(""")
rep("""tx.style.color=COLV[d.color];""", """tx.style.color=COLV[d.color]||d.color;""")
rep(""".tx{scrollbar-width:none;""", """.swatches{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.swatch{width:28px;height:28px;padding:0;border-radius:50%;border:2px solid var(--btn-edge);cursor:pointer}
.swatch[aria-pressed="true"]{outline:3px solid var(--accent);outline-offset:2px}
.swatch-pick{display:inline-flex;align-items:center;gap:4px;font-size:.85rem;cursor:pointer}
.swatch-pick input{width:34px;height:28px;padding:0;border:1px solid var(--btn-edge);border-radius:6px;background:none;cursor:pointer}
.tx{scrollbar-width:none;""")

# ---------- 倒數（老師 2026-11-04「倒數沒反應」）：原本預設 09:00，時間已過就直接顯示「開始！」 ----------
# 新放的倒數預設 10 分鐘後；設定的時間今天已過，就倒數到明天那個時間（舊資料沒有 setAt，維持原本行為）
rep("""  countdown:()=>({time:'09:00',label:'距離比賽開始',done:'開始！',fired:''}),""", """  countdown:()=>({time:cdSoon(10),label:'距離開始',done:'時間到！',fired:'',setAt:Date.now()}),""")
rep("""const INIT={""", """// 幾分鐘後的時間（HH:MM）
function cdSoon(min){const t=new Date(Date.now()+min*60000);return String(t.getHours()).padStart(2,'0')+':'+String(t.getMinutes()).padStart(2,'0')}
// 倒數的目標時刻：今天的那個時間；如果老師設定時已經過了，就是明天
function cdTarget(d,now){const n=now?new Date(now):new Date(),[h,m]=d.time.split(':').map(Number),tg=new Date(n);tg.setHours(h||0,m||0,0,0);if(d.setAt&&tg.getTime()<=d.setAt)tg.setDate(tg.getDate()+1);return tg}
const INIT={""")
rep("""  tick(b,W){const d=W.d,n=new Date(),[h,m]=d.time.split(':').map(Number),tg=new Date(n);tg.setHours(h||0,m||0,0,0);
    const left=(tg-n)/1000,""", """  tick(b,W){const d=W.d,n=new Date(),tg=cdTarget(d,n);
    const left=(tg-n)/1000,""")
rep("""    b.querySelector('.ct').textContent='目標時間 '+d.time},""", """    b.querySelector('.ct').textContent='目標時間 '+(tg.getDate()!==n.getDate()?'明天 ':'')+d.time},""")
rep("""  settings(f,W){const d=W.d;f.inp('目標時間','time',()=>d.time,v=>{d.time=v;d.fired=''}).inp('標題'""", """  settings(f,W){const d=W.d,setTime=v=>{d.time=v;d.fired='';d.setAt=Date.now()};
    f.btns([[10,'10 分鐘後'],[30,'30 分鐘後'],[60,'1 小時後']].map(([min,t])=>[t,()=>{setTime(cdSoon(min));setTimeout(()=>rebuild(W))}]))
     .inp('目標時間','time',()=>d.time,setTime).inp('標題'""")
rep(""".note('倒數到 0 會全螢幕響鈴一次。')}""", """.note('倒數到 0 會全螢幕響鈴一次。今天已經過了的時間，會倒數到明天。')}""")
rep("""    if(W.type==='countdown'&&d.time===hm&&d.fired!==tk){d.fired=tk;save();ring(d.done||'時間到',d.label)}""",
    """    if(W.type==='countdown'&&d.fired!==tk){const at=cdTarget(d).getTime();if(now>=at&&now-at<60000){d.fired=tk;save();ring(d.done||'時間到',d.label)}}""")

# ---------- 🖊️ 畫筆（老師 2026-11-04）：在畫面任何地方註記，圖片、小工具上面也能畫 ----------
# 每個畫面各存一份筆跡（比例座標，換解析度不跑掉）；一條線是 {c:顏色, w:粗細(佔畫布高的比例), a:透明度, p:[x,y,x,y…]}
rep("""<button type="button" class="tb" id="schedTb">""", """<button type="button" class="tb${INK.on?' on':''}" id="inkTb"><span class="ic">🖊️</span><span>畫筆</span></button><button type="button" class="tb" id="schedTb">""")
rep("""  else if(b.id==='fsTb')toggleFs();""", """  else if(b.id==='inkTb')inkToggle();
  else if(b.id==='fsTb')toggleFs();""")
rep("""  if(e.key==='Escape'){ringOff();$('#lightbox').hidden=true;""", """  if(e.key==='Escape'&&INK.on&&$('#ring').hidden){inkToggle(false);return}
  if(e.key==='Escape'){ringOff();$('#lightbox').hidden=true;""")
rep("""  if(k==='b')toggleBar();else if(k==='f')toggleFs();""", """  if(k==='b')toggleBar();else if(k==='f')toggleFs();else if(k==='p')inkToggle();""")
rep("""快捷鍵：B 工具列｜F 全螢幕｜""", """快捷鍵：B 工具列｜F 全螢幕｜P 畫筆｜""")
rep("""  sc.widgets.forEach(buildWidget);drawBar();icons();
}""", """  sc.widgets.forEach(buildWidget);stage.appendChild(inkCv);inkDraw();drawBar();icons();
}""")
rep("""function renderScreen(){""", r"""/* ---------- 畫筆 ---------- */
const INK_COLORS=[['#e53935','紅'],['#fb8c00','橘'],['#fdd835','黃'],['#43a047','綠'],['#1e88e5','藍'],['#8e24aa','紫'],['#111111','黑'],['#ffffff','白']];
const INK_SIZES=[['s','細',.004],['m','中',.008],['l','粗',.016]];
const INK={on:false,color:'#e53935',size:'m',tool:'pen',cur:null,undo:[]};
const inkCv=document.createElement('canvas');inkCv.id='ink';
const inkBar=document.createElement('div');inkBar.id='inkBar';inkBar.hidden=true;document.body.appendChild(inkBar);
const inkList=()=>{const sc=scr();if(!Array.isArray(sc.ink))sc.ink=[];return sc.ink};
function inkStroke(ctx,st,W,H){
  const p=st.p;if(p.length<2)return;
  ctx.globalAlpha=st.a||1;ctx.strokeStyle=ctx.fillStyle=st.c;ctx.lineWidth=Math.max(1,st.w*H);ctx.lineCap=ctx.lineJoin='round';
  if(p.length===2){ctx.beginPath();ctx.arc(p[0]*W,p[1]*H,ctx.lineWidth/2,0,Math.PI*2);ctx.fill();return}
  ctx.beginPath();ctx.moveTo(p[0]*W,p[1]*H);
  // 取相鄰兩點的中點畫曲線，線條才滑順
  for(let i=2;i<p.length-2;i+=2){const x=p[i]*W,y=p[i+1]*H;ctx.quadraticCurveTo(x,y,(x+p[i+2]*W)/2,(y+p[i+3]*H)/2)}
  ctx.lineTo(p[p.length-2]*W,p[p.length-1]*H);ctx.stroke();
}
function inkDraw(){
  const W=stage.clientWidth,H=stage.clientHeight;if(!W||!H)return;
  const dpr=devicePixelRatio||1,cw=Math.round(W*dpr),ch=Math.round(H*dpr);
  if(inkCv.width!==cw||inkCv.height!==ch){inkCv.width=cw;inkCv.height=ch}
  const ctx=inkCv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  inkList().forEach(st=>inkStroke(ctx,st,W,H));if(INK.cur)inkStroke(ctx,INK.cur,W,H);ctx.globalAlpha=1;
}
function inkSnap(){INK.undo.push({id:scr().id,list:inkList().slice()});if(INK.undo.length>40)INK.undo.shift();inkDrawBar()}
const inkPos=e=>{const r=stage.getBoundingClientRect();return[+((e.clientX-r.left)/r.width).toFixed(4),+((e.clientY-r.top)/r.height).toFixed(4)]};
function inkEraseAt(x,y){
  const W=stage.clientWidth,H=stage.clientHeight,list=inkList();
  for(let i=list.length-1;i>=0;i-=1){const st=list[i],reach=Math.max(12,st.w*H/2+6);
    for(let j=0;j<st.p.length;j+=2){if(Math.hypot((st.p[j]-x)*W,(st.p[j+1]-y)*H)<=reach){list.splice(i,1);save();inkDraw();return}}}
}
let inkErasing=false;
inkCv.addEventListener('pointerdown',e=>{
  if(!INK.on||!e.isPrimary)return;e.preventDefault();inkCv.setPointerCapture(e.pointerId);const[x,y]=inkPos(e);
  if(INK.tool==='eraser'){inkSnap();inkErasing=true;inkEraseAt(x,y);return}
  const hl=INK.tool==='hl',size=INK_SIZES.find(s=>s[0]===INK.size)[2];
  INK.cur={c:INK.color,w:hl?size*3:size,a:hl?.35:1,p:[x,y]};inkDraw();
});
inkCv.addEventListener('pointermove',e=>{
  if(!e.isPrimary)return;
  if(inkErasing){const[x,y]=inkPos(e);inkEraseAt(x,y);return}
  if(!INK.cur)return;
  const pts=e.getCoalescedEvents?e.getCoalescedEvents():[e],p=INK.cur.p;
  (pts.length?pts:[e]).forEach(ev=>{const[x,y]=inkPos(ev);if(Math.hypot(x-p[p.length-2],y-p[p.length-1])>.0015)p.push(x,y)});inkDraw();
});
function inkEnd(){
  if(inkErasing){inkErasing=false;return}
  if(!INK.cur)return;inkSnap();inkList().push(INK.cur);INK.cur=null;save();inkDraw();
}
inkCv.addEventListener('pointerup',inkEnd);inkCv.addEventListener('pointercancel',inkEnd);
function inkDrawBar(){
  const tools=[['pen','🖊️ 筆'],['hl','🖍️ 螢光筆'],['eraser','🧽 橡皮擦']];
  inkBar.innerHTML=`<div class="ink-group">${INK_COLORS.map(([c,t])=>`<button type="button" class="swatch" title="${t}" aria-label="${t}" data-ink-color="${c}" aria-pressed="${INK.color===c&&INK.tool!=='eraser'}" style="background:${c}"></button>`).join('')}</div>
    <div class="ink-group">${INK_SIZES.map(([k,t,w])=>`<button type="button" class="ink-size" title="${t}" aria-label="${t}" data-ink-size="${k}" aria-pressed="${INK.size===k}"><i style="width:${Math.round(w*900)+3}px;height:${Math.round(w*900)+3}px"></i></button>`).join('')}</div>
    <div class="ink-group">${tools.map(([k,t])=>`<button type="button" class="btn" data-ink-tool="${k}" aria-pressed="${INK.tool===k}">${t}</button>`).join('')}</div>
    <div class="ink-group"><button type="button" class="btn" data-ink-act="undo"${INK.undo.some(u=>u.id===scr().id)?'':' disabled'}>↶ 復原</button><button type="button" class="btn" data-ink-act="clear">清除全部</button><button type="button" class="btn primary" data-ink-act="done">完成</button></div>`;
}
inkBar.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;const d=b.dataset;
  if(d.inkColor){INK.color=d.inkColor;if(INK.tool==='eraser')INK.tool='pen'}
  else if(d.inkSize){INK.size=d.inkSize;if(INK.tool==='eraser')INK.tool='pen'}
  else if(d.inkTool)INK.tool=d.inkTool;
  else if(d.inkAct==='undo'){for(let i=INK.undo.length-1;i>=0;i-=1){if(INK.undo[i].id===scr().id){scr().ink=INK.undo.splice(i,1)[0].list;save();inkDraw();break}}}
  else if(d.inkAct==='clear'){if(inkList().length){inkSnap();scr().ink=[];save();inkDraw();toast('已清除這個畫面的筆跡，按「復原」可以找回來')}}
  else if(d.inkAct==='done'){inkToggle(false);return}
  inkCv.classList.toggle('erase',INK.tool==='eraser');inkDrawBar();
});
function inkToggle(on){
  INK.on=on===undefined?!INK.on:on;INK.cur=null;inkErasing=false;
  inkCv.classList.toggle('on',INK.on);inkCv.classList.toggle('erase',INK.on&&INK.tool==='eraser');inkBar.hidden=!INK.on;
  if(INK.on){selId=null;stage.querySelectorAll('.w.sel').forEach(x=>x.classList.remove('sel'));if(document.activeElement&&document.activeElement.blur)document.activeElement.blur();$('#pop').hidden=true;$('#sched').hidden=true;$('#screens').hidden=true;inkDrawBar()}
  const tb=$('#inkTb');if(tb)tb.classList.toggle('on',INK.on);
}
new ResizeObserver(inkDraw).observe(stage);
function renderScreen(){""")
rep("""function goScr(i){lastRot=Date.now();S.cur=(i+S.screens.length)%S.screens.length;selId=null;OPEN.clear();save();renderScreen();""",
    """function goScr(i){lastRot=Date.now();S.cur=(i+S.screens.length)%S.screens.length;selId=null;OPEN.clear();save();renderScreen();if(INK.on)inkDrawBar();""")
rep(""".swatches{display:flex;""", """#ink{position:absolute;inset:0;width:100%;height:100%;z-index:8000;pointer-events:none;touch-action:none}
#ink.on{pointer-events:auto;cursor:crosshair}
#ink.on.erase{cursor:cell}
#inkBar{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(92px + env(safe-area-inset-bottom,0px));z-index:9100;display:flex;flex-wrap:wrap;justify-content:center;gap:6px 14px;max-width:calc(100% - 24px);width:max-content;padding:8px 14px;border-radius:18px;background:var(--bar,var(--panel,#fffaf0));color:var(--ink);border:2px solid var(--bar-edge,var(--btn-edge));box-shadow:0 8px 24px rgba(0,0,0,.28)}
#inkBar[hidden]{display:none}
#inkBar .ink-group{display:flex;align-items:center;gap:6px}
#inkBar .btn[aria-pressed="true"]{outline:3px solid var(--accent);outline-offset:1px}
#inkBar .btn:disabled{opacity:.45;cursor:default}
.ink-size{width:34px;height:34px;padding:0;display:grid;place-items:center;border:2px solid var(--btn-edge);border-radius:50%;background:var(--btn-bg);cursor:pointer}
.ink-size i{display:block;border-radius:50%;background:var(--ink)}
.ink-size[aria-pressed="true"]{outline:3px solid var(--accent);outline-offset:1px}
.tb.on{background:var(--btn-bg);box-shadow:inset 0 0 0 2px var(--accent)}
.swatches{display:flex;""")

# ---------- 🔳 QR Code（老師 2026-11-04「打上網址，會自動轉為 qrcode」）：編碼器 assets/studio/qr-encode.js，不靠外部 ----------
rep("""<script type="application/json" id="presetData"></script>""", """<script type="application/json" id="presetData"></script>
<script src="assets/studio/qr-encode.js"></script>""")
rep("""const KEEP=['text','schedule','clock','timer','countdown','stopwatch','alarm','interval','image','draw'];""",
    """const KEEP=['text','schedule','clock','timer','stopwatch','alarm','interval','image','draw','qr'];""")   # 老師 2026-11-04：倒數用不到，拿掉（要限時用計時器）
rep("""qr:['QR碼','qr-code',.2,.38]""", """qr:['QR Code','qr-code',.26,.5]""")
rep("""image:'🖼️',draw:'✏️'};""", """image:'🖼️',draw:'✏️',qr:'🔳'};""")
rep("""  if(b.dataset.add)addW(b.dataset.add);""", """  if(b.dataset.add){const added=addW(b.dataset.add);if(added.type==='qr')ELS[added.id].b.querySelector('.qrin').focus()}""")
rep("""qr:()=>({text:'https://www.google.com',cap:'掃我看題目'})""", """qr:()=>({text:'',cap:''})""")
start = s.index('qr:{\n  render(b,W)')
end = s.index('}\n', s.index("settings(f,W){f.inp('網址或文字'", start)) + 1
end = s.index('}', end)
s = s[:start] + """qr:{
  render(b,W){const d=W.d;b.innerHTML='<div class="qrw"><div class="qrpaper"><canvas class="qrc"></canvas><div class="qrmsg"></div></div><div class="qrcap"></div><input class="qrin" type="text" placeholder="在這裡打上或貼上網址" spellcheck="false" autocomplete="off" aria-label="網址"></div>';
    const i=b.querySelector('.qrin');i.value=d.text;i.oninput=()=>{d.text=i.value;save();qrPaint(b,d)};qrPaint(b,d)},
  settings(f,W){f.inp('網址或文字','text',()=>W.d.text,v=>W.d.text=v).inp('說明','text',()=>W.d.cap,v=>W.d.cap=v).note('打上網址就會自動變成 QR Code。沒有打 https:// 也可以，系統會自動補上。')}
}""" + s[end + 1:]
rep("""const INIT={""", """// 網址沒打 https:// 時補上，手機掃了才會直接打開
function qrTarget(text){const t=String(text||'').trim();return /^[\\w-]+(\\.[\\w-]+)+([/?#:].*)?$/.test(t)?'https://'+t:t}
function qrPaint(b,d){
  const c=b.querySelector('.qrc'),msg=b.querySelector('.qrmsg'),cap=b.querySelector('.qrcap'),target=qrTarget(d.text);
  cap.textContent=d.cap||'';cap.hidden=!d.cap;
  const code=target&&window.QREncode?QREncode.encode(target):null;
  c.hidden=!code;msg.hidden=!!code;
  if(!code){msg.textContent=target?(window.QREncode?'內容太長，做不成 QR Code':'QR Code 工具載入失敗，請重新整理'):'打上網址，這裡就會出現 QR Code';return}
  const quiet=4,scale=8,n=code.size+quiet*2;c.width=c.height=n*scale;
  const x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.fillStyle='#000';
  code.modules.forEach((row,r)=>row.forEach((dark,k)=>{if(dark)x.fillRect((k+quiet)*scale,(r+quiet)*scale,scale,scale)}));
}
const INIT={""")
rep(""".swatches{display:flex;""", """.qrw{height:100%;min-height:0;display:flex;flex-direction:column;align-items:center;gap:6px}
.qrpaper{flex:1;min-height:0;aspect-ratio:1;max-width:100%;display:grid;place-items:center;background:#fff;border-radius:8px;overflow:hidden}
.qrc{display:block;width:100%;height:100%;image-rendering:pixelated}
.qrc[hidden],.qrmsg[hidden],.qrcap[hidden]{display:none}
.qrmsg{padding:10px;color:#555;font-weight:700;text-align:center;font-size:calc(var(--fs)*clamp(13px,6cqw,22px));line-height:1.35}
.qrcap{font-family:var(--title-font);font-weight:700;color:var(--ink);text-align:center;font-size:calc(var(--fs)*clamp(13px,6cqw,26px));line-height:1.2}
.qrin{flex:none;width:100%;box-sizing:border-box;padding:5px 10px;border:1px solid var(--btn-edge);border-radius:8px;background:var(--field);color:var(--ink);font:inherit;font-size:clamp(12px,4.2cqw,18px);text-align:center;text-overflow:ellipsis}
.swatches{display:flex;""")

# 工具列按鈕變多：寬度照內容算，放得下就不出現捲軸；box-sizing 要算進內距
rep("""#bar{position:fixed;left:50%;transform:translateX(-50%);""", """#bar{position:fixed;left:50%;transform:translateX(-50%);width:max-content;box-sizing:border-box;""")

# ---------- 內嵌在大屏 ----------
rep("""function toggleFs(){if(document.fullscreenElement)""", """function toggleFs(){const host=embedHost();if(host){host.fsToggle(host.document.getElementById('screenBoard'));return}if(document.fullscreenElement)""")
rep("""const ORDER=KEEP;""", """// 內嵌在大屏（同網域 iframe）時的大屏視窗；單獨開啟時是 null
function embedHost(){try{return window.parent!==window&&window.parent.fsToggle?window.parent:null}catch(e){return null}}
const ORDER=KEEP;""")
rep("""addEventListener('load',icons);""", """// 定時跳出提醒時，大屏切到這個工具，老師和學生才看得到
['#ring','#ack'].forEach(sel=>new MutationObserver(()=>{const host=embedHost();if(host&&!$(sel).hidden&&host.screenBoardShow)host.screenBoardShow()}).observe($(sel),{attributes:true,attributeFilter:['hidden']}));
addEventListener('load',icons);""")

# ---------- 資安（2026-11-06 稽核）：匯入的設定檔可能是別人分享的 ----------
rep(r"""$('#impJson').onclick=()=>$('#jsonIn').click();""", r"""$('#impJson').onclick=()=>$('#jsonIn').click();
// 資安：設定檔可能是別人分享的。id 只收英數（會放進 HTML），圖片只收真正的圖片 data URL（會放進 CSS），防夾帶程式碼。
const SAFE_ID=/^[\w-]{1,40}$/,SAFE_IMG=/^data:image\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$/;
function cleanImported(){
  S.screens.forEach(sc=>{if(!SAFE_ID.test(String(sc.id)))sc.id=uid();sc.widgets.forEach(w=>{if(!SAFE_ID.test(String(w.id)))w.id=uid()})});
  S.jobs=(Array.isArray(S.jobs)?S.jobs:[]).filter(j=>j&&SAFE_ID.test(String(j.id)));
  Object.keys(IMG).forEach(k=>{if(!SAFE_ID.test(k)||typeof IMG[k]!=='string'||!SAFE_IMG.test(IMG[k]))delete IMG[k]})}""")
rep(r"""S=o.S;IMG=o.IMG||{};S.screens.forEach(sc=>{sc.id=sc.id||uid();sc.widgets=sc.widgets.filter(w=>KEEP.includes(w.type))});""",
    r"""S=o.S;IMG=o.IMG&&typeof o.IMG==='object'?o.IMG:{};S.screens.forEach(sc=>{sc.id=sc.id||uid();sc.widgets=sc.widgets.filter(w=>w&&KEEP.includes(w.type))});
    cleanImported();""")
rep(r'''id="sn-${sc.id}"''', r'''id="sn-${esc(sc.id)}"''')
rep(r'''id="jt-${j.id}" aria-label="時間"><select id="ja-${j.id}"''', r'''id="jt-${esc(j.id)}" aria-label="時間"><select id="ja-${esc(j.id)}"''')
rep(r'''<select id="js-'+j.id+'">'+S.screens.map(x=>`<option value="${x.id}"''', r'''<select id="js-'+esc(j.id)+'">'+S.screens.map(x=>`<option value="${esc(x.id)}"''')
rep(r'''id="jx-${j.id}" placeholder="要跳出的公告文字"><label><input type="checkbox" id="jb-${j.id}">''', r'''id="jx-${esc(j.id)}" placeholder="要跳出的公告文字"><label><input type="checkbox" id="jb-${esc(j.id)}">''')
rep(r'''<select id="jw-'+j.id+'">'+tm.map(([id,t])=>`<option value="${id}"''', r'''<select id="jw-'+esc(j.id)+'">'+tm.map(([id,t])=>`<option value="${esc(id)}"''')
rep(r'''<input type="checkbox" id="jb-'+j.id+'"> 開始時響一聲''', r'''<input type="checkbox" id="jb-'+esc(j.id)+'"> 開始時響一聲''')

# ---------- 🔖 書籤（老師 2026-11-07「可以建立書籤」）：常用網站一點就開新分頁 ----------
# 資料 {title, items:[{id,name,url}]}；網址只收 http(s)（bmHref），名稱一律 textContent
rep("""'image','draw','qr'];""", """'image','draw','qr','bm'];""")
rep("""qr:['QR Code','qr-code',.26,.5]""", """qr:['QR Code','qr-code',.26,.5], bm:['書籤','bookmark',.3,.62]""")
rep("""draw:'✏️',qr:'🔳'};""", """draw:'✏️',qr:'🔳',bm:'🔖'};""")
rep("""  qr:()=>({text:'',cap:''})
};""", """  qr:()=>({text:'',cap:''}),
  bm:()=>({title:'常用網站',items:BM_DEFAULT.map(([name,url])=>({id:uid(),name,url}))})
};""")
rep("""if(added.type==='qr')ELS[added.id].b.querySelector('.qrin').focus()""", """if(added.type==='qr'||added.type==='bm')ELS[added.id].b.querySelector('.qrin').focus()""")
rep("""qr:{
  render(b,W)""", r"""bm:{
  render(b,W){const d=W.d;if(!Array.isArray(d.items))d.items=[];
    const shown=d.items.find(it=>it.id===d.qr&&bmHref(it.url));
    if(shown){const href=bmHref(shown.url);
      b.innerHTML='<div class="bmw"><div class="qrw"><div class="qrpaper"><canvas class="qrc"></canvas><div class="qrmsg"></div></div><div class="qrcap"></div></div><button type="button" class="bmback">🔖 回書籤</button></div>';
      qrPaint(b,{text:href,cap:bmLabel(shown,href)});
      b.querySelector('.bmback').onclick=()=>{d.qr='';bmRestoreBox(W);save();refresh(W)};return}
    b.innerHTML='<div class="bmw"><div class="ttl"></div><div class="bmlist"></div><input class="qrin bmin" type="text" placeholder="貼上網址按 Enter；要取名就打「名稱 網址」" spellcheck="false" autocomplete="off" aria-label="新增書籤的網址"></div>';
    const ttl=b.querySelector('.ttl');ttl.textContent=d.title||'';ttl.hidden=!d.title;
    const list=b.querySelector('.bmlist');
    if(!d.items.length){const m=document.createElement('div');m.className='bmmsg';m.textContent='在下面貼上網址，按 Enter 就會加進來；點書籤會開新分頁。';list.appendChild(m)}
    d.items.forEach(it=>{const href=bmHref(it.url),a=document.createElement(href?'a':'span');a.className='bmi'+(href?'':' bad');
      if(href){a.href=href;a.target='_blank';a.rel='noopener noreferrer'}
      const n=document.createElement('span');n.className='bmn';n.textContent='🔗 '+(bmLabel(it,href)||'請到「設定」填網址');
      const h=document.createElement('span');h.className='bmh';h.textContent=href&&bmLabel(it,href)!==bmHost(href)?bmHost(href):'';
      a.append(n,h);const row=document.createElement('div');row.className='bmr';row.dataset.id=it.id;
      const grip=document.createElement('span');grip.className='bmgrip';grip.textContent='⠿';grip.title='按住拖拉改變順序';grip.onpointerdown=e=>bmDragRow(e,row,list,d);row.append(grip,a);
      if(href){const q=document.createElement('button');q.type='button';q.className='bmq';q.textContent='QR';q.title='變成 QR Code';q.onclick=()=>{d.qr=it.id;bmGrowForQr(W);save();refresh(W)};row.appendChild(q)}
      list.appendChild(row)});
    const i=b.querySelector('.bmin');
    i.onkeydown=e=>{if(e.key!=='Enter'||e.isComposing)return;e.preventDefault();const named=i.value.trim().match(/^(.+?)\s+(\S+)$/),href=bmHref(named?named[2]:i.value);
      if(!href){toast('請貼上網址，例如 www.google.com');return}
      d.items.push({id:uid(),name:named?named[1].slice(0,60):'',url:href});save();refresh(W);ELS[W.id]?.b.querySelector('.bmin')?.focus();toast('已加入書籤；要改名字或順序，按標題列的「設定」')}},
  settings(f,W,box){f.inp('標題','text',()=>W.d.title,v=>W.d.title=v);bmEditor(box,W);f.note('點書籤會開新分頁，按旁邊的 QR 會變成 QR Code，按住 ⠿ 可以拖拉換順序。沒有打 https:// 也可以，系統會自動補上。')}
},
qr:{
  render(b,W)""")
rep("""const INIT={""", r"""// 資安：書籤只收 http(s) 網址（擋 javascript: 之類）；沒打 https:// 的自動補上
function bmHref(u){try{const x=new URL(qrTarget(u));return /^https?:$/.test(x.protocol)?x.href:''}catch(e){return ''}}
function bmHost(href){try{return new URL(href).hostname.replace(/^www\./,'')}catch(e){return ''}}
// 新書籤預設放台灣常用的學習平台；沒取名字的書籤，認得的網站直接顯示中文名稱
const BM_DEFAULT=[['因材網','https://adl.edu.tw/'],['均一教育平台','https://www.junyiacademy.org/'],['Cool English','https://www.coolenglish.edu.tw/'],['學習吧','https://www.learnmode.net/'],['PaGamO','https://www.pagamo.org/'],['教育雲','https://cloud.edu.tw/'],['布可星球','https://read.tn.edu.tw/']];
const BM_KNOWN=Object.assign({'dcps.tn.edu.tw':'大橋國小'},...BM_DEFAULT.map(([name,url])=>({[bmHost(url)]:name})));
function bmLabel(it,href){return it.name||BM_KNOWN[bmHost(href)]||bmHost(href)}
// 按 QR 時把小工具放大到 QR Code 看得清楚；回書籤時還原
function bmGrowForQr(W){const d=W.d,R=stage.getBoundingClientRect();d.qrBox={x:W.x,y:W.y,w:W.w,h:W.h};
  const h=Math.max(W.h,.76),w=Math.max(W.w,Math.min(1,h*R.height/R.width*.92));
  W.x=clamp(W.x+W.w/2-w/2,0,1-w);W.y=clamp(W.y+W.h/2-h/2,0,1-h);W.w=w;W.h=h;place(ELS[W.id].el,W)}
function bmRestoreBox(W){const q=W.d.qrBox;delete W.d.qrBox;if(!q)return;Object.assign(W,q);place(ELS[W.id].el,W)}
// 拖拉把手：按住上下移動換順序（手指、滑鼠都可以）
function bmDragRow(e,row,list,d){e.preventDefault();e.stopPropagation();row.classList.add('dragging');
  const move=ev=>{const edge=list.getBoundingClientRect();if(ev.clientY<edge.top+18)list.scrollTop-=12;else if(ev.clientY>edge.bottom-18)list.scrollTop+=12;
    const over=[...list.children].find(r=>{if(r===row)return false;const b=r.getBoundingClientRect();return ev.clientY>=b.top&&ev.clientY<=b.bottom});
    if(over){const b=over.getBoundingClientRect();list.insertBefore(row,ev.clientY<b.top+b.height/2?over:over.nextSibling)}};
  const end=()=>{removeEventListener('pointermove',move);removeEventListener('pointerup',end);removeEventListener('pointercancel',end);row.classList.remove('dragging');
    const order=[...list.children].map(r=>r.dataset.id);d.items.sort((a,b)=>order.indexOf(a.id)-order.indexOf(b.id));save()};
  addEventListener('pointermove',move);addEventListener('pointerup',end);addEventListener('pointercancel',end)}
// 匯入的設定檔可能是別人分享的：書籤逐欄整理
function bmClean(w){const d=w.d=w.d&&typeof w.d==='object'?w.d:{};d.title=String(d.title||'').slice(0,60);d.qr=/^[\w-]{1,40}$/.test(String(d.qr))?d.qr:'';
  const q=d.qrBox;if(q&&!['x','y','w','h'].every(k=>Number.isFinite(q[k])&&q[k]>=0&&q[k]<=1))delete d.qrBox;
  d.items=(Array.isArray(d.items)?d.items:[]).filter(it=>it&&typeof it==='object').slice(0,100).map(it=>({id:/^[\w-]{1,40}$/.test(String(it.id))?it.id:uid(),name:String(it.name||'').slice(0,60),url:bmHref(it.url)}))}
function bmEditor(box,W){
  const wrap=document.createElement('div');wrap.style.cssText='display:flex;flex-direction:column;gap:6px';
  const draw=()=>{wrap.innerHTML='';const a=W.d.items;a.forEach((it,i)=>{
    const r=document.createElement('div');r.className='erow bmrow';
    const n=document.createElement('input');n.type='text';n.id='f'+uid();n.value=it.name||'';n.placeholder='名稱（可空白）';n.oninput=()=>{it.name=n.value;save();refresh(W)};
    const u=document.createElement('input');u.type='text';u.id='f'+uid();u.value=it.url||'';u.placeholder='網址';u.spellcheck=false;u.onchange=()=>{it.url=bmHref(u.value);u.value=it.url;save();refresh(W)};
    const bs=document.createElement('div');bs.className='x';
    const B=(t,fn,c)=>{const b=document.createElement('button');b.type='button';b.className='btn '+(c||'');b.textContent=t;b.onclick=()=>{fn();save();refresh(W);draw()};bs.appendChild(b)};
    B('↑',()=>{if(i>0)[a[i-1],a[i]]=[a[i],a[i-1]]});B('↓',()=>{if(i<a.length-1)[a[i+1],a[i]]=[a[i],a[i+1]]});B('刪',()=>a.splice(i,1),'danger');
    r.append(n,u,bs);wrap.appendChild(r)});
    const add=document.createElement('button');add.type='button';add.className='btn primary';add.textContent='＋ 新增書籤';add.onclick=()=>{W.d.items.push({id:uid(),name:'',url:''});save();refresh(W);draw();const ins=wrap.querySelectorAll('.bmrow input');ins[ins.length-2]?.focus()};
    wrap.appendChild(add)};
  draw();box.appendChild(wrap);
}
const INIT={""")
rep("""sc.widgets.forEach(w=>{if(!SAFE_ID.test(String(w.id)))w.id=uid()})""", """sc.widgets.forEach(w=>{if(!SAFE_ID.test(String(w.id)))w.id=uid();if(w.type==='bm')bmClean(w)})""")
rep("""- 本頁與大屏同網站""", """- 書籤只收 http(s) 網址（bmHref），名稱用 textContent 顯示。
- 本頁與大屏同網站""")
rep(""".swatches{display:flex;""", """.bmw{height:100%;min-height:0;display:flex;flex-direction:column;gap:6px}
.bmw .ttl[hidden]{display:none}
.bmlist{flex:1;min-height:0;overflow:auto;display:flex;flex-direction:column;gap:6px;scrollbar-width:thin}
.bmi{flex:none;display:flex;align-items:baseline;gap:.6em;padding:.45em .7em;border-radius:10px;background:var(--field);border:1px solid var(--btn-edge);color:var(--ink);text-decoration:none;font-weight:700;font-size:calc(var(--fs)*clamp(14px,5.5cqw,26px));line-height:1.25}
a.bmi:hover{outline:3px solid var(--accent);outline-offset:-1px}
.bmi.bad{opacity:.55}
.bmn{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bmh{margin-left:auto;flex:0 1000 auto;min-width:0;max-width:45%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:400;font-size:.62em;color:var(--muted)}
.bmmsg{padding:10px;color:var(--muted);font-weight:700;text-align:center;font-size:calc(var(--fs)*clamp(13px,5cqw,20px));line-height:1.4}
.erow.bmrow{grid-template-columns:minmax(0,1fr) minmax(0,1.4fr) auto}
.swatches{display:flex;""")

assert '比賽' not in s,[m.group(0) for m in re.finditer(r'.{20}比賽.{10}', s)][:6]
rep(""".bmi.bad{opacity:.55}
""", """.bmi.bad{opacity:.55}
.bmr{flex:none;display:flex;gap:6px;align-items:stretch}
.bmr .bmi{flex:1;min-width:0}
.bmq,.bmback{flex:none;padding:0 .7em;border-radius:10px;border:1px solid var(--btn-edge);background:var(--field);color:var(--ink);font:inherit;font-weight:800;cursor:pointer;font-size:calc(var(--fs)*clamp(12px,4.4cqw,20px))}
.bmback{padding:.3em .7em}
.bmq:hover,.bmback:hover{outline:3px solid var(--accent);outline-offset:-1px}
.bmw .qrw{flex:1;height:auto}
.bmgrip{flex:none;display:flex;align-items:center;padding:0 .15em;color:var(--muted);cursor:grab;touch-action:none;user-select:none;font-size:calc(var(--fs)*clamp(16px,5.5cqw,26px))}
.bmr.dragging{opacity:.65}
.bmr.dragging .bmgrip{cursor:grabbing}
""")
rep("""const ORDER=KEEP;""", """const ORDER=KEEP.filter(t=>t!=='qr');   // QR Code 併進書籤；以前放好的 QR Code 照常顯示""")
# 老師 2026-11-09：計時器、碼錶、鬧鐘、間隔提醒合成一顆
rep(r"""  bar.innerHTML=ORDER.map(t=>`<button type="button" class="tb" data-add="${t}"><span class="ic">${TOOL_EMOJI[t]||'▫️'}</span><span>${META[t][0]}</span></button>`).join('')+""", r"""  bar.innerHTML=ORDER.map(t=>TIME_TOOLS.includes(t)?(t===TIME_TOOLS[0]?'<button type="button" class="tb" id="timeTb" aria-haspopup="true"><span class="ic">⏱️</span><span>計時</span></button>':''):`<button type="button" class="tb" data-add="${t}"><span class="ic">${TOOL_EMOJI[t]||'▫️'}</span><span>${META[t][0]}</span></button>`).join('')+""")
rep(r"""function drawBar(){
""", r"""// 計時器、碼錶、鬧鐘、間隔提醒收在同一顆按鈕；放上去後還是各自獨立運作
const TIME_TOOLS=['timer','stopwatch','alarm','interval'];
function toggleTimePop(btn){const pop=$('#timePop');
  if(!pop.children.length)pop.innerHTML=TIME_TOOLS.map(t=>`<button type="button" class="tb" data-add="${t}"><span class="ic">${TOOL_EMOJI[t]}</span><span>${META[t][0]}</span></button>`).join('');
  pop.hidden=!pop.hidden;if(pop.hidden)return;
  const r=btn.getBoundingClientRect(),half=pop.offsetWidth/2;pop.style.left=clamp(r.left+r.width/2,half+8,innerWidth-half-8)+'px';pop.style.bottom=(innerHeight-r.top+14)+'px'}
function drawBar(){
""")
rep(r"""  else if(b.id==='inkTb')inkToggle();
""", r"""  else if(b.id==='timeTb')toggleTimePop(b);
  else if(b.id==='inkTb')inkToggle();
""")
rep(r"""$('#barShow').onclick=toggleBar;
""", r"""$('#barShow').onclick=toggleBar;
$('#timePop').onclick=e=>{const b=e.target.closest('[data-add]');if(!b)return;$('#timePop').hidden=true;addW(b.dataset.add)};
""")
rep(r"""document.addEventListener('pointerdown',e=>{if(!$('#pop').hidden&&""", r"""document.addEventListener('pointerdown',e=>{if(!$('#timePop').hidden&&!e.target.closest('#timePop,#timeTb'))$('#timePop').hidden=true;if(!$('#pop').hidden&&""")
rep(r"""<nav id="bar" aria-label="小工具列"></nav>
""", r"""<nav id="bar" aria-label="小工具列"></nav>
<div class="timepop" id="timePop" role="menu" aria-label="選擇計時工具" hidden></div>
""")
rep(r"""#bar{position:fixed;""", r""".timepop{position:fixed;transform:translateX(-50%);z-index:9050;display:flex;gap:2px;background:var(--bar);border:1px solid var(--bar-edge);border-radius:14px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.timepop[hidden]{display:none}
.timepop .tb{min-width:68px;font-size:.82rem}
#bar{position:fixed;""")
# 老師 2026-11-09：拿掉計時器，碼錶、鬧鐘、間隔提醒寫上用法
rep(r"""stopwatch:['碼錶','watch',.26,.3]""", r"""stopwatch:['碼錶','watch',0.3,0.44]""")
rep(r"""alarm:['鬧鐘','alarm-clock',.22,.28]""", r"""alarm:['鬧鐘','alarm-clock',0.3,0.6]""")
rep(r"""interval:['間隔提醒','bell-ring',.28,.3]""", r"""interval:['間隔提醒','bell-ring',0.3,0.5]""")
rep(r"""const ORDER=KEEP.filter(t=>t!=='qr');""", r"""const ORDER=KEEP.filter(t=>t!=='qr'&&t!=='timer');""")
rep(r"""// 計時器、碼錶、鬧鐘、間隔提醒收在同一顆按鈕；放上去後還是各自獨立運作
const TIME_TOOLS=['timer','stopwatch','alarm','interval'];
""", r"""// 碼錶、鬧鐘、間隔提醒收在同一顆按鈕；放上去後還是各自獨立運作（倒數用大屏右上角的 5 分／10 分）
const TIME_TOOLS=['stopwatch','alarm','interval'];
const TIME_HELP={stopwatch:'從 0 往上計時，可以記錄每一筆時間',alarm:'設定幾點幾分，時間到全螢幕響鈴',interval:'每隔幾分鐘提醒一次，例如記得存檔'};
""")
rep(r"""  if(!pop.children.length)pop.innerHTML=TIME_TOOLS.map(t=>`<button type="button" class="tb" data-add="${t}"><span class="ic">${TOOL_EMOJI[t]}</span><span>${META[t][0]}</span></button>`).join('');
""", r"""  if(!pop.children.length)pop.innerHTML=TIME_TOOLS.map(t=>`<button type="button" class="tp" data-add="${t}"><span class="ic">${TOOL_EMOJI[t]}</span><span class="tpt"><b>${META[t][0]}</b><small>${TIME_HELP[t]}</small></span></button>`).join('')+'<div class="tpn">要有聲音，請先按工具列的「🔊」試一次。</div>';
""")
rep(r""".timepop{position:fixed;transform:translateX(-50%);z-index:9050;display:flex;gap:2px;background:var(--bar);border:1px solid var(--bar-edge);border-radius:14px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.timepop[hidden]{display:none}
.timepop .tb{min-width:68px;font-size:.82rem}
""", r""".timepop{position:fixed;transform:translateX(-50%);z-index:9050;display:flex;flex-direction:column;gap:2px;width:300px;box-sizing:border-box;background:var(--bar);border:1px solid var(--bar-edge);border-radius:14px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.timepop[hidden]{display:none}
.tp{display:flex;align-items:center;gap:12px;width:100%;padding:8px 10px;border:0;border-radius:10px;background:transparent;color:var(--ink);font:inherit;text-align:left;cursor:pointer}
.tp:hover{background:var(--btn-bg)}
.tp .ic{font-size:24px;line-height:1}
.tpt{display:flex;flex-direction:column;gap:1px;min-width:0}
.tpt b{font-size:1rem}
.tpt small{font-size:.78rem;color:var(--muted);line-height:1.3}
.tpn{padding:6px 10px 4px;font-size:.76rem;color:var(--muted);border-top:var(--rule);margin-top:2px}
.usage{flex:none;max-width:100%;color:var(--muted);font-size:clamp(12px,3.7cqw,15px);line-height:1.4;text-align:center}
.big.wordy{font-size:calc(var(--fs)*clamp(20px,9cqw,40px));white-space:normal}
.aladd{display:flex;gap:6px;width:100%;box-sizing:border-box;align-items:center}
.aladd input{min-width:0;box-sizing:border-box;padding:5px 8px;border:1px solid var(--btn-edge);border-radius:8px;background:var(--field);color:var(--ink);font:inherit;font-size:clamp(13px,4cqw,16px)}
.aladd input[type=time]{flex:none;width:9em}
.aladd input[type=text]{flex:1}
.aladd .btn{flex:none;white-space:nowrap}
.al-list{width:100%;max-height:24cqh;overflow:auto}
.al-list li{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2px 6px}
.aldel{flex:none;border:0;background:transparent;color:var(--muted);cursor:pointer;font:inherit;padding:0 4px}
""")
rep(r"""  else if(b.id==='soundTb'){unlock();chime()}
""", r"""  else if(b.id==='soundTb'){unlock();chime();toast('聽得到鈴聲，鬧鐘和提醒時就會響；聽不到請檢查電腦音量')}
""")
rep(r"""<span class="lb">${AC?'測試聲音':'開聲音'}</span>""", r"""<span class="lb" title="按一下試聽鈴聲；鬧鐘和提醒要出聲，瀏覽器規定要先按過一次">${AC?'測試聲音':'開聲音'}</span>""")
rep(r"""${ACTS.map(([k,t])=>`<option value="${k}"${j.action===k?' selected':''}>${t}</option>`).join('')}""", r"""${ACTS.filter(([k])=>k!=='timer'||j.action==='timer'||allW().some(w=>w.type==='timer')).map(([k,t])=>`<option value="${k}"${j.action===k?' selected':''}>${t}</option>`).join('')}""")
rep(r"""目前沒有計時器，先從工具列加一個。""", r"""目前沒有計時器，請換一個動作。""")
rep(r"""render(b,W){b.innerHTML=`<div class="ctr"><div class="big tdg sw"></div><div class="ctl opt-mid"><button type="button" class="btn primary go">開始</button><button type="button" class="btn lp">記錄</button><button type="button" class="btn rs">歸零</button></div><ol class="laps opt-tall"></ol></div>`;""", r"""render(b,W){b.innerHTML=`<div class="ctr"><div class="big tdg swtime"></div><div class="ctl opt-mid"><button type="button" class="btn primary go">開始</button><button type="button" class="btn lp">記錄</button><button type="button" class="btn rs">歸零</button></div><ol class="laps opt-tall"></ol><div class="usage opt-tall">按「開始」計時，「記錄」記下這一筆，「歸零」重新來。</div></div>`;""")
rep(r"""tick(b,W){const d=W.d;b.querySelector('.sw').textContent=swFmt(swNow(d));""", r"""tick(b,W){const d=W.d;b.querySelector('.swtime').textContent=swFmt(swNow(d));""")
rep(r"""<div class="ctl opt-mid"><button type="button" class="btn go"></button><button type="button" class="btn ts">試一次</button></div></div>`;
    b.querySelector('.go').onclick=()=>T.interval.primary(b,W);
""", r"""<div class="ctl opt-mid"><button type="button" class="btn go"></button><button type="button" class="btn ts">試一次</button><button type="button" class="btn st">設定</button></div><div class="usage opt-tall">每隔一段時間提醒一次。按「設定」改提示文字、間隔和時段，按「試一次」看效果。</div></div>`;
    b.querySelector('.go').onclick=()=>T.interval.primary(b,W);
    b.querySelector('.st').onclick=e=>{e.stopPropagation();OPEN.add(W.id);rebuild(W)};
""")
rep(r"""g.textContent=!d.on?'已暫停':nx?fmt(left):(d.mode==='now'?'--:--':'今天結束了');
""", r"""g.textContent=!d.on?'已暫停':nx?fmt(left):(d.mode==='now'?'--:--':'今天的時段結束了');g.classList.toggle('wordy',!nx&&(!d.on||d.mode!=='now'));
""")
rep(r"""render(b,W){b.innerHTML='<div class="ctr"><div class="lbl">下一個鬧鐘</div><div class="big tdg nt"></div><div class="ttl nl"></div><div class="lbl nd opt-mid"></div><ul class="al-list opt-tall"></ul></div>';b._k=null},
""", r"""render(b,W){b.innerHTML='<div class="ctr"><div class="lbl">下一個鬧鐘</div><div class="big tdg nt"></div><div class="ttl nl"></div><div class="lbl nd opt-mid"></div><div class="aladd opt-mid"><input type="time" class="alt" aria-label="鬧鐘時間"><input type="text" class="all" maxlength="30" placeholder="要提醒的事" aria-label="要提醒的事"><button type="button" class="btn primary ala">＋ 加入</button></div><ul class="al-list opt-tall"></ul><div class="usage opt-tall">選時間、打要提醒的事，按「加入」；時間到會全螢幕響鈴。</div></div>';b._k=null;
    const t=b.querySelector('.alt'),l=b.querySelector('.all');
    const add=()=>{if(!t.value){toast('請先選鬧鐘時間');t.focus();return}W.d.list.push({id:uid(),time:t.value,label:l.value.trim().slice(0,30),on:true,fired:''});t.value='';l.value='';save();b._k=null};
    b.querySelector('.ala').onclick=add;l.onkeydown=e=>{if(e.key==='Enter'&&!e.isComposing){e.preventDefault();add()}};
    b.querySelector('.al-list').onclick=e=>{const x=e.target.closest('.aldel');if(!x)return;W.d.list=W.d.list.filter(a=>a.id!==x.dataset.id);save();b._k=null}},
""")
rep(r"""b.querySelector('.nl').textContent=nx?(nx.label||'鬧鐘'):'今天沒有了';""", r"""b.querySelector('.nl').textContent=nx?(nx.label||'鬧鐘'):(L.length?'今天的鬧鐘都響完了':'還沒有鬧鐘，在下面加一個');""")
rep(r"""b.querySelector('.al-list').innerHTML=L.filter(a=>a!==nx).map(a=>`<li class="${a.on&&a.fired!==tk?'':'off'}">${esc(a.time)}　${esc(a.label||'鬧鐘')}</li>`).join('')},""", r"""b.querySelector('.al-list').innerHTML=L.map(a=>`<li class="${a.on&&a.fired!==tk?'':'off'}"><span>${esc(a.time)}　${esc(a.label||'鬧鐘')}</span><button type="button" class="aldel" data-id="${esc(a.id)}" title="刪除這個鬧鐘" aria-label="刪除這個鬧鐘">✕</button></li>`).join('')},""")
rep(r"""  alarm:()=>({list:[{id:uid(),time:'11:55',label:'收拾桌面',on:true,fired:''}]}),""", r"""  alarm:()=>({list:[]}),""")
# 老師 2026-11-09：工具列不要測試聲音、定時
rep(r"""<button type="button" class="tb" id="schedTb"><span class="ic">📅</span><span>定時${S.jobs.filter(j=>j.on).length?' '+S.jobs.filter(j=>j.on).length:''}</span></button>""", r"""""")
rep(r"""  <button type="button" class="tb ${AC?'':'warn'}" id="soundTb"><span class="ic">🔊</span><span class="lb" title="按一下試聽鈴聲；鬧鐘和提醒要出聲，瀏覽器規定要先按過一次">${AC?'測試聲音':'開聲音'}</span></button>
""", r"""""")
rep(r"""  else if(b.id==='schedTb'){$('#pop').hidden=true;$('#screens').hidden=true;$('#sched').hidden=!$('#sched').hidden;drawJobs()}
""", r"""""")
rep(r"""  else if(b.id==='soundTb'){unlock();chime();toast('聽得到鈴聲，鬧鐘和提醒時就會響；聽不到請檢查電腦音量')}
""", r"""""")
rep(r"""  S.jobs.forEach(j=>{if(j.on&&j.time===hm&&j.fired!==tk){j.fired=tk;save();runJob(j)}});
""", r"""""")
rep(r"""+'<div class="tpn">要有聲音，請先按工具列的「🔊」試一次。</div>';""", r""";""")
rep(r"""時間到會全螢幕顯示說明文字並響鈴（記得先開聲音）。""", r"""時間到會全螢幕顯示說明文字並響鈴。""")
# 老師 2026-11-10：review 修正；定時與自動輪播整段移除
rep(r"""function chime(){beep(988""", r"""function chime(){unlock();beep(988""")
rep(r"""if(!q)return;Object.assign(W,q);place(ELS[W.id].el,W)}""", r"""if(!q)return;W.x=q.x;W.y=q.y;W.w=q.w;W.h=q.h;place(ELS[W.id].el,W)}""")
rep(r"""const move=ev=>{const edge=list.getBoundingClientRect();""", r"""const move=ev=>{if(!ev.buttons){end();return}const edge=list.getBoundingClientRect();""")
rep(r""".job{display:grid;grid-template-columns:auto auto 1fr auto;gap:6px;align-items:center;padding:8px;border:1px solid var(--btn-edge);border-radius:8px}
.job.off{opacity:.5}
.job .pm{grid-column:1/-1;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.job input[type="time"],.job select,.job input[type="text"]{padding:5px 7px;border-radius:6px;border:1px solid var(--btn-edge);background:var(--field);min-width:0}
.job input[type="text"]{flex:1}
.job .btn{padding:4px 9px;font-size:.8rem}
""", r"""""")
rep(r"""<div class="pop" id="sched" hidden>
  <h3>定時</h3>
  <div class="pnote">到了設定的時間會自動執行，每天重複。網頁要保持開著才會執行。</div>
  <div id="jobs" style="display:flex;flex-direction:column;gap:8px"></div>
  <div class="frow"><button type="button" class="btn primary" id="jobAdd">＋ 新增定時</button></div>
  <h3>自動輪播畫面</h3>
  <div class="frow"><label><input type="checkbox" id="rotOn"> 開啟</label>每<input type="number" id="rotSec" min="5" max="3600" style="max-width:5em">秒換下一個畫面</div>
  <div class="pnote">有人點畫面或按鍵時，會暫停 20 秒再繼續輪播。</div>
</div>
""", r"""""")
rep(r"""S.rotate=S.rotate||{on:false,sec:30};S.jobs=S.jobs||[];""", r"""S.jobs=[];""")
rep(r"""S.jobs=(Array.isArray(S.jobs)?S.jobs:[]).filter(j=>j&&SAFE_ID.test(String(j.id)));""", r"""S.jobs=[];""")
rep(r"""S.jobs=S.jobs||[];S.rotate=S.rotate||{on:false,sec:30};S.bg=""", r"""S.jobs=[];S.bg=""")
rep(r"""function goScr(i){lastRot=Date.now();S.cur=""", r"""function goScr(i){S.cur=""")
rep(r"""if(!$('#sched').hidden&&!e.target.closest('#sched,#schedTb'))$('#sched').hidden=true;""", r"""""")
rep(r"""/* ---------- 定時 ---------- */
let lastRot=Date.now(),lastUser=0;
['pointerdown','keydown'].forEach(t=>document.addEventListener(t,()=>lastUser=Date.now()));
const ACTS=[['screen','切換畫面'],['notice','跳出公告'],['timer','開始計時器']];
function drawJobs(){
  const box=$('#jobs');box.innerHTML='';
  if(!S.jobs.length)box.innerHTML='<div class="pnote">還沒有定時。按「新增定時」，例如 9:00 自動切到「考試中」畫面。</div>';
  S.jobs.slice().sort((a,b)=>(a.time||'99').localeCompare(b.time||'99')).forEach(j=>{
    const r=document.createElement('div');r.className='job'+(j.on?'':' off');
    r.innerHTML=`<button type="button" class="btn ${j.on?'primary':''}" data-a="on">${j.on?'開':'關'}</button><input type="time" id="jt-${esc(j.id)}" aria-label="時間"><select id="ja-${esc(j.id)}" aria-label="動作">${ACTS.filter(([k])=>k!=='timer'||j.action==='timer'||allW().some(w=>w.type==='timer')).map(([k,t])=>`<option value="${k}"${j.action===k?' selected':''}>${t}</option>`).join('')}</select><button type="button" class="btn danger" data-a="del">刪除</button><div class="pm"></div>`;
    r.querySelector('input[type=time]').value=j.time||'';
    r.querySelector('input[type=time]').onchange=e=>{j.time=e.target.value;j.fired='';save()};
    r.querySelector('select').onchange=e=>{j.action=e.target.value;j.fired='';save();drawJobs()};
    r.querySelector('[data-a=on]').onclick=()=>{j.on=!j.on;j.fired='';save();drawJobs();drawBar();icons()};
    r.querySelector('[data-a=del]').onclick=()=>{S.jobs.splice(S.jobs.indexOf(j),1);save();drawJobs();drawBar();icons()};
    const pm=r.querySelector('.pm');
    if(j.action==='screen'){
      if(!S.screens.some(x=>x.id===j.screen))j.screen=S.screens[0].id;
      pm.innerHTML='到 <select id="js-'+esc(j.id)+'">'+S.screens.map(x=>`<option value="${esc(x.id)}"${x.id===j.screen?' selected':''}>${esc(x.name)}</option>`).join('')+'</select>';
      pm.querySelector('select').onchange=e=>{j.screen=e.target.value;save()};
    }else if(j.action==='notice'){
      pm.innerHTML=`<input type="text" id="jx-${esc(j.id)}" placeholder="要跳出的公告文字"><label><input type="checkbox" id="jb-${esc(j.id)}"> 響鈴</label>`;
      const t=pm.querySelector('input[type=text]');t.value=j.text||'';t.oninput=()=>{j.text=t.value;save()};
      const c=pm.querySelector('input[type=checkbox]');c.checked=!!j.sound;c.onchange=()=>{j.sound=c.checked;save()};
    }else{
      const tm=[];S.screens.forEach(x=>x.widgets.forEach(w=>{if(w.type==='timer')tm.push([w.id,x.name+'・'+(w.d.label||'計時器')+'（'+fmt(w.d.total)+'）'])}));
      if(!tm.length){pm.innerHTML='<span class="pnote">目前沒有計時器，請換一個動作。</span>'}
      else{if(!tm.some(x=>x[0]===j.timer))j.timer=tm[0][0];
        pm.innerHTML='<select id="jw-'+esc(j.id)+'">'+tm.map(([id,t])=>`<option value="${esc(id)}"${id===j.timer?' selected':''}>${esc(t)}</option>`).join('')+'</select><label><input type="checkbox" id="jb-'+esc(j.id)+'"> 開始時響一聲</label>';
        pm.querySelector('select').onchange=e=>{j.timer=e.target.value;save()};
        const c=pm.querySelector('input[type=checkbox]');c.checked=!!j.sound;c.onchange=()=>{j.sound=c.checked;save()}}
    }
    box.appendChild(r)});
  $('#rotOn').checked=S.rotate.on;$('#rotSec').value=S.rotate.sec;
}
$('#jobAdd').onclick=()=>{const n=new Date();n.setMinutes(n.getMinutes()+5);S.jobs.push({id:uid(),on:true,time:pad(n.getHours())+':'+pad(n.getMinutes()),action:'screen',screen:scr().id,text:'',sound:true,fired:''});save();drawJobs();drawBar();icons()};
$('#rotOn').onchange=e=>{S.rotate.on=e.target.checked;lastRot=Date.now();save()};
$('#rotSec').onchange=e=>{S.rotate.sec=clamp(+e.target.value||30,5,3600);e.target.value=S.rotate.sec;save()};
""", r"""""")
rep(r"""function runJob(j){
  if(j.action==='screen'){const i=S.screens.findIndex(x=>x.id===j.screen);if(i>=0)goScr(i)}
  else if(j.action==='notice')notice(j.text||'公告',j.sound);
  else if(j.action==='timer'){S.screens.forEach((x,si)=>{const W=x.widgets.find(w=>w.id===j.timer);if(!W)return;if(si!==S.cur)goScr(si);
    const d=W.d;d.remain=d.total;d.endAt=Date.now()+d.total*1000;d.running=true;save();if(j.sound)chime();toast('定時開始：'+(d.label||'計時器')+' '+fmt(d.total))})}
}
""", r"""""")
rep(r"""  if(S.rotate.on&&S.screens.length>1&&$('#ring').hidden&&!OPEN.size&&$('#pop').hidden&&$('#sched').hidden&&$('#screens').hidden&&now-lastUser>20000&&now-lastRot>S.rotate.sec*1000)goScr(S.cur+1);
""", r"""""")
s = s.replace("$('#sched').hidden=true;", "")
# 老師 2026-11-10：改完馬上關掉或切走時，不等延遲存檔，免得最後一筆沒存到
rep("""let saveT,imgT;
function save(){clearTimeout(saveT);saveT=setTimeout(()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}},250)}
function saveImgs(){clearTimeout(imgT);imgT=setTimeout(()=>{try{localStorage.setItem(IMGKEY,JSON.stringify(IMG))}catch(e){toast('圖片太多，瀏覽器存不下；這次仍可使用，重新整理後可能消失')}},400)}""", """let saveT=0,imgT=0;
function flushSave(){clearTimeout(saveT);saveT=0;try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}
function save(){clearTimeout(saveT);saveT=setTimeout(flushSave,250)}
function flushImgs(){clearTimeout(imgT);imgT=0;try{localStorage.setItem(IMGKEY,JSON.stringify(IMG))}catch(e){toast('圖片太多，瀏覽器存不下；這次仍可使用，重新整理後可能消失')}}
function saveImgs(){clearTimeout(imgT);imgT=setTimeout(flushImgs,400)}
// 改完馬上關掉或切走時，不等延遲存檔，免得最後一筆沒存到
function flushAll(){if(saveT)flushSave();if(imgT)flushImgs()}
['pagehide','beforeunload'].forEach(t=>addEventListener(t,flushAll));
document.addEventListener('visibilitychange',()=>{if(document.hidden)flushAll()});""")
(root / 'Screen.html').write_text(s, encoding='utf-8')
print('Screen.html', len(s) // 1024, 'KB')
