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
rep("""countdown:()=>({time:'09:00',label:'距離比賽開始',done:'開始！',fired:''}),""", """countdown:()=>({time:'09:00',label:'距離開始',done:'開始！',fired:''}),""")
rep("""saveFile('競賽公告螢幕設定_'""", """saveFile('螢幕公告設定_'""")
rep("""<div class="ver">v3.5 · 2026-11-04　快捷鍵：""", """<div class="ver">快捷鍵：""")
rep("""/* 競賽公告螢幕 v3.5 · 2026-11-04 */""", """/* 螢幕公告（源自 classboard v3.5） */""")

s = s.replace('「比賽中」', '「考試中」')

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
