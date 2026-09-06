# 教師工作台＋小綿助：Claude 開發交接手冊

交接日期：2026-08-25  
交接版本：Git `942a187`（打包前基準）  
主要語言：繁體中文、HTML/CSS/JavaScript、Python  
授權：MIT；第三方來源另見 `THIRD_PARTY_NOTICES.md`

## 1. 一句話定位

這是一套給臺灣國小教師、導師、學年主任及兼任行政教師使用的本機優先工作台：以任務清單為主角，整合教學進度、日曆、選用 AI 助理，以及常駐 Windows 桌面的「小綿助」秘書。

## 2. 使用者已確認的產品原則

- 一般老師只要連上網頁即可使用，不需要 GAS、Google Sheet 或登入帳號。
- 每位老師的資料預設只存在自己的瀏覽器；不同瀏覽器、Windows 帳號與網站網域彼此獨立。
- 網頁必須可下載／還原 JSON 備份。
- AI 功能可關閉；Gemini API 金鑰由老師自行設定，且不進 Git、JSON 備份或雲端。
- 小綿助是桌面程式，不是網頁浮動角色；桌寵未啟動時網頁不能因此失效。
- 小綿助保留本機模式，網頁透過 loopback 本機橋接；v2.0 起可選擇直連老師自己的 GAS（`desktop_pet_cloud.py`，網域白名單硬擋），未設定時所有功能與 v1 相同。
- 修改流程固定為「先測本機 → 使用者確認 → 才更新 GitHub／Netlify」。

## 2.1 產品策略（使用者 2026-08-25 核定）

三層門檻對應三種老師：「連網頁就能用；想要桌面小夥伴就下載小綿助；進階玩家再裝 LINE 小幫手。」

1. **桌面小綿助收斂為三件事**：桌面儀表板（今日／逾期餘光可見）＋健康提醒＋情感陪伴。~~維護模式，不再加新功能。~~ **2026-09-04 更新：使用者核定 v2.0「專注小綿助」**——解除維護模式，在三件事範圍內加入：直連 GAS（方案 B）、分心提醒（前景視窗標題偵測）、專注陪伴模式、行為豐富化（探頭／蹭滑鼠／收到 LINE 跳一下）、大屏提示遙控。
2. **捕捉與通知全走 LINE 小幫手**：記事、任務、語音、照片、聯絡簿、晨間簡報推播——新功能投資以 LINE＋晨間大屏為主。
3. 桌寵保留的理由：零安裝門檻入口、完全離線、在電腦前的環境感提醒、產品個性；這些是 LINE 給不了的。
4. **2027 年 2 月左右再檢視**：若實際使用都集中在 LINE，屆時把桌寵標為「經典版，不再更新」；在那之前不移除。

## 3. 主要檔案與責任

| 檔案／資料夾 | 用途 |
| --- | --- |
| `Index.html` | 主要教師工作台；單檔 HTML/CSS/JS，包含任務、日曆、教學進度、AI、設定、備份與本機橋接。 |
| `Board.html` | 電子紙／看板頁面，相容上游 GAS 版。 |
| `Installer.html` | 上游 GAS 安裝介面，相容保留，不是目前一般老師的主要入口。 |
| `Code.gs`、`appsscript.json` | 上游 GAS 相容層與選用部署；現行產品不要求安裝。 |
| `desktop_pet_secretary.py` | Windows 小綿助主程式、秘書視窗、健康提醒、記事及 127.0.0.1 本機橋接。 |
| `desktop_pet_preview.py` | 桌寵動畫／素材預覽工具。 |
| `assets/pet/` | 小綿助 WebP 動畫與 PNG 影格；走路左右各 16 格，其餘狀態為 6～8 格。 |
| `tests/profile_config.test.js` | Node 靜態與前端契約測試。 |
| `tests/local_bridge_test.py` | Python 本機橋接、來源限制及資料處理測試。 |
| `netlify.toml` | Netlify 靜態部署與安全標頭。 |
| `README.md` | 使用者／開發者入口說明。 |
| `SECURITY.md` | 威脅模型、安全邊界及發布檢查。 |
| `LICENSE`、`THIRD_PARTY_NOTICES.md` | MIT 授權及素材／上游來源。 |
| `dist/` | 本機產生的發布包、預覽與編譯快取；不屬於 Git 追蹤原始碼，也不應整包交給 AI。 |

## 4. 網頁資料與安全邊界

### 瀏覽器資料

主要資料在 `localStorage`。核心 key 包含：

- `grade6PreviewTasks` 類型的一組 `LOCAL_PREVIEW_STORAGE_KEYS`：任務、模擬備份、資料庫索引、記事及資料版本（以 `Index.html` 內常數為準）。
- `grade6TeachingProgressBySubject`：各任教課程獨立的教學進度集合。
- `grade6TeachingProgress`：舊版單一課程相容資料。
- `grade6SelectedRoles`：多重身分。
- `grade6AssistantSettings`：介面與 AI 設定。
- `grade6AssistantApiKey`：僅在使用者勾選記住時保存；不得進 JSON 備份。
- `grade6PromptTemplates`：常用 Prompt。
- `grade6DeskpetInbox`、`grade6DeskpetDiary`、`grade6DeskpetHealth`：舊版網頁桌寵相容資料。

系統以約 4 MB 作保守容量警示；附件本體不可塞入 localStorage，只保留必要中繼資料。新使用者應看到空白任務清單，不載入展示任務。

### 桌面小綿助資料

桌面資料預設位於：

```text
%APPDATA%\XiaoMianZhuSecretary\
```

主資料檔為 `secretary_data.json`。本機橋接只監聽 `127.0.0.1:8767`，限制允許來源、HTTP 方法與請求大小，不提供任意檔案讀取。同步內容限任務欄位、記事文字、時間與附件名稱。

## 5. 教學進度目前模型

- 任教課程先在「系統設定 → 教師資訊」建立；同科教不同班應建立成不同課程名稱，例如「六年一班社會」「六年二班社會」。
- `grade6TeachingProgressBySubject` 對每一門課保存獨立 plan，切換課程不得共用或覆蓋別科進度。
- 每個單元可在文字列後填自訂節數；未填時使用「每課／單元幾節」預設值。
- 星期一至五各自有授課節數，可為 0；總和是每週節數。
- 排程必須以實際授課日容量分配。例如一至五各 1 節，四節的單元應跨四個授課日，不可顯示成同一天 4 節。
- 排程會扣除國定／自訂假日、評量前複習節數與定期評量，超過完成日期時標示「超出期限」。
- 進度存檔後會出現在工作台日曆；課程行程可編輯，日曆拖曳需維持資料一致。

關鍵函式集中在 `Index.html` 約教學區：`normalizeTeachingProgressPlan`、`buildTeachingWeeks`、`buildTeachingDays`、`arrangeTeachingProgress`、`saveTeachingProgressPlan`。請以函式名稱搜尋，不要依賴固定行號。

最近完成的兩個修正：

1. 每個單元可自訂不同節數。
2. 排程依星期別的實際節數逐日分配，不再把整週容量集中到同一天。

## 6. 任務系統重要行為

- 四個主分類：教學、行政、學年主任、導師；細項分類可不選。
- 主任務下可有子任務；子任務在清單中縮排呈現。
- 完成子任務只劃線並完成該子任務，不得直接完成整個主任務。
- 封存主任務時，其子任務必須一併封存。
- 完成主任務後仍應能封存。
- 日曆卡片可拖曳改期，拖曳時必須明確顯示正在移動哪一張卡片。

## 7. AI 助理範圍

- AI 是選用功能，關閉時任務與教學進度仍完整可用。
- 使用者輸入自然語言，系統自動判斷情境與訊息對象，套用內建 Prompt。
- 輸出可包含分析、勾選確認項目、給家長／老師的 LINE 文字，以及主任務／子任務建議。
- 對家長訊息要再檢查不雅、責備、標籤化或不適當語氣。
- 送出外部 AI 前必須顯示去識別化預覽並由老師確認；規則辨識不能宣稱百分之百可靠。

## 8. 小綿助現況與限制

已有功能：今日／逾期／待追蹤、早晚簡報、快速記事、附件名稱整理、喝水、久坐、服藥提醒、自訂名稱與打氣話、桌面位置保存、本機橋接。

**v2.0（2026-09-04）新增**：`desktop_pet_cloud.py`（CloudLink 直連 GAS：白名單網域、固定動作、退避；ForegroundMonitor 前景視窗標題；FocusTracker 專注統計與提醒節奏）；秘書頁新增「☁️ 雲端連線」「📣 大屏提示遙控」「🍅 專注小綿助」三張卡；桌寵新行為 `start_walking`／`_movement_tick` 覆寫（探頭、蹭滑鼠、被罵衝到中央）。測試：`tests/local_bridge_test.py::CloudLinkTest`、`profile_config.test.js` 的 v2.0 契約。

已知發布風險：

- 未簽章 Windows EXE 可能被 SmartScreen 或 PC-cillin 判為低信譽／可疑；不可要求使用者關閉防毒。
- 正式發佈應提供 SHA-256、Defender 掃描結果，長期最好購買程式碼簽章或採 Microsoft Store／受信任安裝管道。
- `dist/` 曾包含 PyInstaller/Nuitka 快取與測試包，交接與 Git 不應攜帶這些巨大快取。
- 走路影格已增至左右各 16 格並修正腳底裁切，但角色步態仍屬可持續美術調校項目；修改時要同時檢查透明邊界、腳底基線、左右尺寸與循環首尾銜接。

### 8.1 Tkinter 繪圖不穩定與 v1.6 的處置（重要背景）

2026-08 在使用者機器（超寬螢幕＋150% 縮放）上發生「面板空白」與「桌寵整隻消失但程序仍活著」。逐步排查後確認：

- Tk 的**選單與嵌入式面板**共用同一條繪圖管線，在該環境會無聲崩潰或不繪製。
- 色鍵透明視窗（`WS_EX_LAYERED`）會被部分顯示卡直接丟棄畫面。

v1.6 的處置（現行架構，勿隨意回退）：

1. **完全移除 Tk 面板與 Tk 右鍵選單**。`_show_menu` 被覆寫成直接開啟瀏覽器版秘書頁並 `return "break"`；右鍵＝雙擊＝開 `http://127.0.0.1:8767/panel`。
2. 秘書頁改由**瀏覽器渲染**（`PANEL_PAGE_HTML`），資料與動作走本機橋接，任何顯示環境都可靠。
3. `SetProcessDpiAwareness(1)` ＋ `dpi_scale` 尺寸換算。
4. `_visibility_heartbeat` 每 4 秒 `deiconify/topmost/lift` 自我復活。

**若日後有人回報「右鍵沒有選單」**：這是設計如此，不是 bug。設定分別在秘書頁的「🌿 健康管理 → ⚙ 詳細提醒設定」與工作台「設定 → 小綿助」。

### 8.2 v2.0 重寫選項（尚未決定，2026-08-28 記錄）

僅在桌寵不穩定於**其他老師的機器**重現時才啟動；目前維持維護模式。

| | 現況 Tkinter | Electron | PySide6/Qt |
|---|---|---|---|
| 透明視窗 | 色鍵，GPU 會丟棄 | 原生 `transparent: true`，成熟 | 原生，成熟 |
| 右鍵選單 | 不穩（已停用） | 原生 `Menu.popup()` | 原生 `QMenu` |
| 秘書頁 | 開外部瀏覽器分頁 | **可直接內嵌**（現有 HTML 可重用） | 需 QtWebEngine（再 +80MB） |
| 下載體積 | 39 MB | 約 150 MB | 約 60–80 MB |
| 重寫成本 | — | 高（新技術棧，但 UI 已是 HTML） | 中（Python 業務邏輯可重用） |

**Electron 版的關鍵實作要點**（使用者 2026-08-28 提供，經查證與官方文件一致）：

- 除錯階段務必 `win.setIgnoreMouseEvents(false)`；設為 `true` 會讓所有滑鼠事件穿透視窗，右鍵直接失效（`forward` 只協助轉送移動事件）。
- 桌寵元素與可點擊按鈕要設 `-webkit-app-region: no-drag`，否則拖曳區會與右鍵衝突。
- `contextIsolation: true` 時，必須以 preload ＋ `contextBridge.exposeInMainWorld` 只暴露指定函式（`showContextMenu` / `setMousePassthrough` / `onMenuAction`）；Electron 29 後不可直接暴露整個 `ipcRenderer`。
- 選單由主行程 `Menu.buildFromTemplate(...).popup({ window })` 建立，renderer 只發 IPC。
- 三步驟診斷：① 關掉滑鼠穿透看是否恢復 ② renderer 的 `contextmenu` 是否有印出事件 ③ `window.petAPI` 是否為 `undefined`（前者是穿透問題、後者是 preload/IPC 接線問題）。
- 參考：Electron [contextBridge](https://www.electronjs.org/docs/latest/api/context-bridge)、[BrowserWindow](https://www.electronjs.org/docs/latest/api/browser-window)、[Context Menu 指南](https://www.electronjs.org/docs/latest/tutorial/context-menu)。

⚠️ 注意：本專案**目前沒有任何 Electron 檔案**（無 `main.js`／`preload.js`／`renderer.js`，`package.json` 也沒有 electron 依賴）。上述屬全新專案的設計，不是對現有程式的修改。採用前須一併重做 GitHub Actions 建置流程，並評估下載體積從 39MB 增至約 150MB 對老師的影響。

## 9. 本機開發與驗收

### 網頁

這是靜態網站，不需建置。不要用 `file://` 作為正式驗收，請從 repository 根目錄啟動本機 HTTP server，再開 `Index.html`。可使用任何靜態伺服器；若本機有 Python：

```powershell
python -m http.server 8766
```

### 自動測試

```powershell
npm.cmd test
python -m py_compile desktop_pet_preview.py desktop_pet_secretary.py
git diff --check
```

`npm.cmd test` 需要 Node.js 18+ 及 Python；一般使用者不需要這些工具，只有開發者需要。

### 手動測試清單

1. 新瀏覽器／無 localStorage 時任務清單為空。
2. 新增主任務與三個子任務；分別完成、重開、封存。
3. 切換清單／日曆；拖曳任務並重新整理確認日期保存。
4. 建立兩門不同課程；設定不同星期節數與單元節數，排程互不影響。
5. 測試假日、複習、定期評量、超出期限與日曆顯示。
6. 下載 JSON、清空測試資料、還原 JSON，確認 API 金鑰未包含其中。
7. 啟動小綿助後測 `http://127.0.0.1:8767` 連線；未啟動時網頁仍正常。
8. 測窄視窗、Windows 顯示縮放及所有下拉選單，不可被容器裁切。

## 10. Git、Netlify 與發布

- 開發 repository：`https://github.com/cona0815/teacher-dashboard.git`（remote 名稱 `fork`）。
- 上游來源：`https://github.com/mihozip/school-admin-daily-dashboard.git`（remote 名稱 `origin`）。
- Netlify 從 GitHub `main` 自動部署；repository 根目錄是 publish directory，設定見 `netlify.toml`。
- Fork 標示是 GitHub repository 關係，不代表侵權；MIT 授權與上游著作權聲明必須保留。
- 未經使用者明確確認，不要 push、重寫 main、刪除 remote、更新 Netlify 或建立 Release。

## 11. 不要做的事

- 不要把 GAS 重新變成一般老師的必填安裝步驟。
- 不要把任務、課程、API key、AppData 或測試者資料硬編碼進網站。
- 不要用破壞性方式清除 localStorage 來處理遷移。
- 不要將 `dist/build-venv`、`dist/nuitka-cache`、`.git`、`__pycache__` 或開發機個資放進交付 ZIP。
- 不要在沒有本機驗證時直接推 GitHub。
- 不要宣稱防毒一定不會攔截，或宣稱去識別化一定不會漏掉個資。

## 12. 建議 Claude 第一輪工作方式

1. 先讀 `CLAUDE.md`、本手冊、`README.md`、`SECURITY.md`。
2. 執行 `git status --short`、`git log -5 --oneline` 與自動測試，建立乾淨基準。
3. 以 `rg` 定位使用者指定功能，先解釋資料流，再小範圍修改。
4. 本機驗證、列出修改檔案與測試結果，交給使用者看效果。
5. 只有使用者明確說「更新 GitHub」後才 commit／push；Netlify 由 GitHub main 自動部署。

可直接貼給 Claude 的開場指令：

> 請先完整閱讀 CLAUDE.md、CLAUDE_HANDOFF.md、README.md 與 SECURITY.md。這是 localStorage 本機優先的國小教師工作台，GAS 不是必要條件。先執行既有測試並檢查 git 狀態；所有修改先在本機驗證，未經我明確同意不得 push GitHub、部署、清除資料或改變儲存格式。接著先告訴我你對目前架構、資料流與這次需求影響範圍的理解，再開始修改。
