"""大屏班級工具新增「📺 螢幕公告」：內嵌 Screen.html（tools/build_screen_board.py 產生）
第一次點才載入；可全螢幕、可開新分頁；定時提醒跳出時自動切過來
python tools/add_screen_tool.py
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Morning.html'
s = path.read_text(encoding='utf-8')
assert 'screenFrame' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""frame-src https://www.youtube-nocookie.com https://www.youtube.com;""", """frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com;""")
rep("""<span class="tt-ico">📣</span><span>大屏提示</span></button>""", """<span class="tt-ico">📣</span><span>大屏提示</span></button>
          <button class="tool-tab" type="button" data-tool="screen"><span class="tt-ico">📺</span><span>螢幕公告</span></button>""")
rep("""        .tool-tab[data-tool="prompt"] { --tc: #1f514a; --tc-soft: #e8f2ee; }""", """        .tool-tab[data-tool="prompt"] { --tc: #1f514a; --tc-soft: #e8f2ee; }
        .tool-tab[data-tool="screen"] { --tc: #0f7d8c; --tc-soft: #e2f3f5; }
        .screen-board { height: max(420px, calc(100vh - 430px)); margin-top: 8px; }   /* 要留給上方工具列與底部「存到雲端」，內嵌的工具列才不會被蓋住 */
        .screen-board iframe { display: block; width: 100%; height: 100%; border: 2px solid var(--line); border-radius: 14px; background: var(--bg); }
        .screen-board:is(:fullscreen, .fake-fs) { height: 100vh; margin-top: 0 !important; }
        .screen-board:is(:fullscreen, .fake-fs) iframe { border: 0; border-radius: 0; }""")
rep("""          </details>
        </div>
      </div>
    </section>""", """          </details>
        </div>
        <div class="tool-panel" data-tool-panel="screen" hidden>
          <div class="tool-opts">
            <button class="ghost-button" type="button" id="screenFullscreenButton">⛶ 全螢幕播放</button>
            <a class="ghost-button" href="Screen.html" target="_blank" rel="noopener" style="text-decoration:none">↗ 開新分頁</a>
            <span class="status-text">自由擺放文字、時程表、時鐘、計時器、圖片、畫板，也能設定時跳提醒。設定只存在這台電腦；定時提醒要網頁開著才會跳。</span>
          </div>
          <div class="screen-board" id="screenBoard"><iframe id="screenFrame" title="螢幕公告" allow="fullscreen; autoplay; screen-wake-lock"></iframe></div>
        </div>
      </div>
    </section>""")
rep("""  document.querySelectorAll('.tab-button').forEach(btn => btn.addEventListener('click', () => { if (btn.dataset.page !== 'tools') stopQuiet(); }));""",
    """  document.querySelectorAll('.tab-button').forEach(btn => btn.addEventListener('click', () => { if (btn.dataset.page !== 'tools') stopQuiet(); }));
  // 📺 螢幕公告：第一次點才載入（裡面有定時，載入後切到別的分頁也繼續跑）
  const screenTile = document.querySelector('.tool-tab[data-tool="screen"]');
  screenTile.addEventListener('click', () => { if (!$('screenFrame').getAttribute('src')) $('screenFrame').src = 'Screen.html'; });
  $('screenFullscreenButton').addEventListener('click', () => fsToggle($('screenBoard')));
  document.addEventListener('fullscreenchange', () => {
    $('screenFullscreenButton').textContent = fsCurrent() === $('screenBoard') ? '⛶ 離開全螢幕' : '⛶ 全螢幕播放';
  });
  // 螢幕公告定時跳提醒時叫這個，不然提醒藏在別的分頁後面
  window.screenBoardShow = () => {
    if (!document.querySelector('.tab-button[data-page="tools"]').classList.contains('active')) toolsTab.click();
    if (!screenTile.classList.contains('active')) screenTile.click();
  };""")
path.write_text(s, encoding='utf-8')
print('ok')
