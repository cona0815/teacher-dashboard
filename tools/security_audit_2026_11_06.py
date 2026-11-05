"""2026-11-06 老師：「最近資安事件很多，看這個程式沒有資安的問題，並註明在程式裡，並直接修正」。
這支只做兩件事（各檔的漏洞修正直接改在程式裡）：
1. 在主要頁面開頭加上【資安說明】註解；Morning／Studio／Screen 另加防點擊劫持的備援。
   Index／Board 也會由 Google Apps Script 以 iframe 方式提供，不能加，否則 GAS 版會打不開。
2. 把 Screen.html 的修正同步到 tools/build_screen_board.py，重新產生 Screen.html 時才不會被蓋掉。
一次性，不要重跑。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSP_PREFIX = '<meta http-equiv="Content-Security-Policy"'

FRAME_GUARD = """<script>
  // 資安：防點擊劫持。別的網站把本頁塞進 iframe 時改成整頁開啟（同網站的嵌入不受影響）。
  // 正式站的 netlify.toml 已用標頭擋；這段是放在其他主機（如 GitHub Pages）時的備援。
  try { if (window.top !== window.self && window.top.location.origin !== window.location.origin) throw new Error('framed'); }
  catch (error) { document.documentElement.style.display = 'none'; try { window.top.location.href = window.location.href; } catch (ignored) {} }
</script>"""

NOTES = {
    'Morning.html': """<!--
【資安說明】晨間大屏（2026-11-06 稽核）
- 本頁放在教室電腦，學生碰得到。設定頁密碼只是擋誤觸，不是加密；錯 5 次鎖 1 分鐘，離開設定頁就重新上鎖。
- 🔑B 教室金鑰權限受限（只能回報今天、看補交）；🔑C 工作台金鑰不要填在教室電腦。
- 網頁只准連 Google Apps Script（上面的 CSP），不載入任何外部程式；金鑰只放在 POST 內容，不放網址。
- 雲端、LINE、試算表回來的文字一律 escapeHtml() 或 textContent 後才上畫面。
- YouTube 只取 11 碼影片 ID，網域固定 youtube-nocookie.com。
-->""",
    'Studio.html': """<!--
【資安說明】AI 工作室（2026-11-06 稽核）
- AI 回覆可能被上傳的文件「下指令」影響，所以 AI 文字一律 escapeHtml() 後才上畫面，數字欄位限範圍。
- 匯入的範文庫備份可能是別人做的：id 只收本工具格式、每欄轉成限長字串。
- 送 AI 前檢查身分證、手機、Email 與座位表裡的學生姓名，發現了先問老師。
- 🔑D Gemini 金鑰只放在 x-goog-api-key 標頭，不放網址、不進匯出檔。
-->""",
    'Screen.html': """<!--
【資安說明】螢幕公告（2026-11-06 稽核）
- 匯入的設定檔可能是別人分享的：id 只收英數、圖片只收 data:image 網址（cleanImported），放進 HTML 的 id 一律 esc()。
- 本頁與大屏同網站，被嵌在大屏裡；資料只存這台電腦。
-->""",
    'Index.html': """<!--
【資安說明】教師工作台（2026-11-06 稽核）
- 還原備份：逐欄檢查（進度列種類與日期、任務連結只收 http/https）；備份只能打開去識別化，不能關掉；不還原 AI 端點。
- 送 AI 前去識別化：AI 助理有預覽；訊息整理、文字附件與檔名也會先遮蔽（redactSensitiveText）。
- 🔑C／🔑D 不進備份；可選擇不記住（只存在這個分頁）。Gemini 金鑰一律放標頭。
- 所有動態內容 escapeHtml() 後才上畫面；連結一律經 safeUrl()。
- 本頁也會由 Apps Script 以 iframe 提供，所以不加「禁止被嵌入」的程式；正式站由 netlify.toml 標頭保護。
-->""",
}


def rep(text, old, new, count=1):
    assert text.count(old) == count, (old[:70], text.count(old))
    return text.replace(old, new)


for name, note in NOTES.items():
    p = ROOT / name
    t = p.read_text(encoding='utf-8')
    start = t.index(CSP_PREFIX)
    end = t.index('>', start) + 1
    block = '\n' + note + ('\n' + FRAME_GUARD if name != 'Index.html' else '')
    t = t[:end] + block + t[end:]
    p.write_text(t, encoding='utf-8', newline='\n')

# ---------- Screen.html 的修正同步到產生器 ----------
p = ROOT / 'tools/build_screen_board.py'
t = p.read_text(encoding='utf-8')
t = rep(t, '''<meta http-equiv="Content-Security-Policy" content="default-src 'self' data: blob:; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'">
"""''', '''<meta http-equiv="Content-Security-Policy" content="default-src 'self' data: blob:; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'">
''' + NOTES['Screen.html'] + '\n' + FRAME_GUARD + '\n"""')
p.write_text(t, encoding='utf-8', newline='\n')
# 匯入清理與 id 跳脫的 rep() 步驟直接寫在 build_screen_board.py 結尾（避開這裡的多層引號）
print('done')
