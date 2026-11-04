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
    """const KEEP=['text','schedule','clock','timer','countdown','stopwatch','alarm','interval','image','draw','qr'];""")
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

assert '比賽' not in s, [m.group(0) for m in re.finditer(r'.{20}比賽.{10}', s)][:6]
(root / 'Screen.html').write_text(s, encoding='utf-8')
print('Screen.html', len(s) // 1024, 'KB')
