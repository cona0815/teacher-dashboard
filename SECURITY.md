# 資安與發布檢查

## 資料邊界

- 網頁任務、進度與設定：目前瀏覽器的 `localStorage`。
- 桌寵任務、記事與附件：目前 Windows 帳號的 `%APPDATA%\XiaoMianZhuSecretary\`。
- 網頁與桌寵：只透過 `http://127.0.0.1:8767` 交換資料。
- AI：只有開啟 AI 並送出內容時，才會連線到設定的模型服務；送出前須人工檢查去識別化結果。

## 已採取的防護

1. 桌寵伺服器只綁定 IPv4 回環位址，不接受區域網路或外網連線；並檢查 Host（擋 DNS rebinding）。
2. 對網頁只提供 `/health` 與 `/sync`；`/panel`、`/panel-data`、`/panel-action` 只給秘書頁自己。限制來源（不接受 `Origin: null`）、方法、Content-Type（必須 `application/json`，在讀資料之前就檢查）與 5 MB 請求大小；回應禁止被其他網頁嵌入。
3. 桌寵資料採 UTF-8 JSON，寫入時先產生暫存檔再原子替換，降低中途關閉造成損毀的風險。
4. 網站部署標頭限制物件嵌入、外部腳本、表單目的地、Referrer 與不必要的裝置權限。
5. API 金鑰不放入 JSON 備份；使用者可選擇不記住金鑰。

## 程式碼掃描紀錄

### 2026-08-29（涵蓋 Index.html / Morning.html / Install.html / Intro.html / LineBot.gs / netlify.toml / desktop_pet_secretary.py）

掃描項目與結果：

| 項目 | 方法 | 結果 |
|---|---|---|
| 硬編碼金鑰／Token | 正則掃描 `api_key`、`token`、`secret`、`AIza*`、`sk-*`、`xai-*`、`ghp_*`，以及專案已知的敏感字串 | 無 |
| 第三方函式庫供應鏈 | 檢查是否夾帶 jQuery／Bootstrap／min.js 等外部程式碼 | 無夾帶，零 npm 執行期相依 |
| 外連主機 | 列出程式碼內所有 http(s) 目的地 | 僅 LINE、Google、OpenAI、xAI 等使用者自行設定的 API，與本專案自己的網址 |
| XSS | 檢查 `innerHTML` 是否插入未跳脫的雲端資料；`eval`／`new Function`／`document.write`／`srcdoc` | 所有動態欄位皆經 `escapeHtml()`；無高危 API |
| API 權限 | 檢視 `handleLineSyncApi_` 的兩層金鑰與動作白名單 | 教室金鑰僅限白名單動作，歷史查詢與備份需老師金鑰 |
| LINE Webhook | 檢視來源驗證 | 以 `?hook=` 密鑰＋`LINE_ALLOWED_USER_IDS` 白名單驗證（Apps Script 讀不到 request header，無法做 HMAC 簽章驗證，此為平台限制下的等效作法） |
| 金鑰是否進備份 | 追 `buildBackupPayload()` → `readSettingsForm()` | 備份只含 provider／model／endpoint 等設定，**不含金鑰**；雲端備份再額外移除 endpoint |
| 桌寵本機橋接 | 檢視綁定位址與 CORS 來源判斷 | 只綁 `127.0.0.1`；`bridge_origin_allowed()` 以來源白名單先行 403，再回應 CORS 標頭 |
| 試算表公式注入 | 檢查寫入 Sheets 的自由文字 | **發現並修正**（見下） |

### 2026-08-29 深度掃描（第二輪）

| 項目 | 結果 |
|---|---|
| Drive 檔案分享權限 | 未呼叫 `setSharing`／`addViewer`，備份檔維持雲端硬碟預設的「僅自己」 |
| AI 回應寫入畫面 | 主要輸出走 `textContent`；AI 產生的子任務名稱經 `escapeHtml()` — 惡意 PDF 無法藉 AI 回應注入 HTML |
| 還原備份 | 檢查 `kind`／`version`、任務數上限 5000、需使用者確認、逐筆過濾欄位 |
| 災難性回溯 regex（ReDoS） | 未發現巢狀量詞 |
| 收件匣洪水 | `MAX_INBOX_ROWS: 1000`＋`trimLineInbox_()` 自動裁切 |
| Referrer 外洩 | `Referrer-Policy: no-referrer`；同步 API 用 POST，金鑰不放網址 |
| 點擊劫持 | **發現並修正**（見下） |

已修正：**點擊劫持（clickjacking）**。站台標頭原本沒有 `frame-ancestors`／`X-Frame-Options`，
外部網站可以把工作台或大屏塞進 iframe，疊上透明元素誘導老師誤點（例如移除版面、還原備份）。
已在 `netlify.toml` 加上 `X-Frame-Options: SAMEORIGIN` 與 CSP `frame-ancestors 'self'`；
用 `'self'` 而非 `'none'`，是因為安裝教學頁需要以 iframe 嵌入自家的 `Code.gs`。

### 2026-08-29 深度掃描（第三輪：前兩輪沒涵蓋的檔案）

範圍：`Code.gs`、`Board.html`、`Installer.html`、`windows_ocr.ps1`、
`desktop_pet_preview.py`、`.github/workflows/`、`package.json`、`.gitignore`、`.claspignore`、
以及整段 git 歷史與實際部署後的回應標頭。

| 項目 | 結果 |
|---|---|
| 金鑰是否曾經進過版控 | 掃過全部 57 個 commit 的每一個檔案版本（`AIza*`／`sk-*`／`xai-*`／`ghp_*`／`AKfycb*`）：**零筆**，沒有「先 commit 再刪」殘留 |
| clasp 憑證 | `.clasp.json`／`.clasprc.json`（含 Google OAuth token）在 `.gitignore` 內，且**從未被 commit 過** |
| GitHub Actions | 用 `pull_request` 而非 `pull_request_target`（fork PR 拿不到 secrets）；`validate` 只有 `contents: read`，`build` 的 `contents: write` 僅供 tag 發版；未使用任何自訂 secret |
| npm 供應鏈 | `package.json` **零執行期相依**，`npm test` 只跑本地測試 |
| `Code.gs` 對外端點 | `doGet` 只吐 HTML 殼，資料函式一律先過 `assertAuthorized_()`；`doPost`（小助手同步）先驗 `DESKTOP_PET_SYNC_KEY`，單次上限 1000 筆 |
| GAS 頁框設定 | `setXFrameOptionsMode(DEFAULT)`（限同網域），非 `ALLOWALL` |
| GAS 樣板注入 | 未使用 `<?!= ?>` 這類不跳脫輸出 |
| PowerShell 指令注入 | `windows_ocr.ps1` 無 `Invoke-Expression`／`iex`／動態指令組裝 |
| 桌寵附件路徑穿越 | 檔名經 `[^\w.() -]+` 過濾並加上時間戳與 uuid 前綴，無法逃出附件資料夾 |
| 文件是否誤貼真實 ID | 未發現真實的 GAS 部署網址、試算表 ID 或 Token；README 的長字串是發版用的 SHA-256 校驗碼 |
| 部署後標頭實測 | `X-Frame-Options: SAMEORIGIN`、CSP `frame-ancestors 'self'`、`Referrer-Policy: no-referrer` 皆已生效 |

**本輪未發現新漏洞。**

補充說明：`netlify.toml` 的 `publish = "."` 會把所有版控檔案（含 `.md`、`tests/`、
`desktop_pet_secretary.py`）一併公開。因為 repository 本來就是公開的開源專案，
這不構成額外外洩；但新增檔案時仍要記得：**放進版控就等於公開發布**。

### 這一輪確認為「已知取捨」而非漏洞

- **AI 提示詞注入**：AI 助理會讀老師上傳的 PDF／圖片，內容若刻意寫入指示，可能影響
  AI 產出的摘要與任務建議。影響僅限「產生誤導性文字」，不會執行程式、不會自動送出；
  工作台的 AI 建議都要老師按下確認才寫入；2026-11-11 起 LINE 傳來的事項例外：老師可在 LINE 按［任務］［記事］［不要］，
  沒按的 10 分鐘後照 AI 建議自動建立（只收允許名單內老師本人傳的訊息，畫面一律跳脫）。轉傳來路不明的照片或檔案時，
  其內容可能誘導 AI 產生誤導性的任務文字，請在 LINE 按「不要」或傳「撤回」。仍請維持人工複核。
- **送 AI 前的個資檢查**（2026-11-11）：教材小工場所有 AI 路徑在 `fetchGemini` 統一檢查（含 Word／Excel／PPT 取出的文字），
  發現身分證、手機、Email、座位表姓名先詢問。LINE 小幫手呼叫 Gemini 改用 `x-goog-api-key` 標頭，金鑰不放網址。
- **文件遮蔽的範圍**（2026-11-11）：除了內文、表格、頁首頁尾，也掃修訂紀錄、欄位代碼、註解、圖表、樞紐分析表快取、
  `mailto:`／`tel:` 超連結並清空作者欄；內嵌檔案與圖片上的字無法自動處理，會在畫面上警告老師自行檢查。
- **桌寵本機端點沒有金鑰**：`127.0.0.1:8767` 的 `/sync` 只靠來源白名單，不驗證金鑰。
  只綁回環位址，同機器上的其他程式仍可存取。若機器已被惡意程式入侵，此防線本就無效；
  一般使用情境下風險可接受。
- **Gemini 金鑰放在網址查詢參數**：這是 Google Generative Language API 的官方用法
  （`?key=`）。若要更保守，可改用 `x-goog-api-key` 標頭。

已修正：**試算表公式注入**。寫進試算表的自由文字（班級、科目、進度、聯絡本、
LINE 收件匣、檔案備份標題）若以 `=`、`+`、`-`、`@` 開頭，Google Sheets 會當公式執行，
例如被寫入 `=IMAGE("http://…")` 時，老師一開啟試算表就會對外連線。
已加入 `sheetText_()`，寫入前補前導單引號強制為文字。

### 2026-11-06 全面稽核（第四輪：8/29 之後新增的功能）

範圍：`Morning.html`、`Screen.html`、`Board.html`、`Index.html`、`Installer.html`、`Studio.html`、`LineBot.gs`、`Code.gs`、
小助手全部 `.py`、`netlify.toml`、`.github/workflows/`，以及全部 220 個 commit 的金鑰掃描。
修正處都在程式裡用「資安：」註解標明，主要頁面開頭另有【資安說明】；`tests/profile_config.test.js` 結尾與
`tests/local_bridge_test.py` 有回歸測試，防止日後改壞。

| 嚴重度 | 問題 | 修正 |
|---|---|---|
| 高 | **工作台還原備份可夾帶程式碼**：進度列 `type` 未跳脫就放進 class 屬性；任務連結可為 `javascript:`。別人給的「範本備份」能偷走 🔑C／🔑D | 進度列逐欄白名單、class 跳脫；任務連結一律 `safeUrl()`（還原、本機程式回傳、畫面三處） |
| 高 | **AI 工作室範文庫匯入可夾帶程式碼**：id 未跳脫放進屬性 | id 只收 `m` 開頭英數，所有欄位轉限長字串；畫面再跳脫 |
| 高 | **小助手本機橋接接受 `Origin: null`**：陌生 .html 附件或任何網站的沙箱 iframe 能讀走任務、記事，或改語音金鑰、啟動錄音 | 拒絕 null 來源 |
| 中 | **外站可不經預檢寫入小助手**：先寫入資料才回 403；也沒擋 DNS rebinding | POST 先驗 Host、來源與 Content-Type 再處理；回應禁止被嵌入 |
| 中 | **螢幕公告匯入設定檔可夾帶程式碼**（id、背景圖網址） | `cleanImported()` 清理 id 與圖片網址，id 放進 HTML 前跳脫；同步改進 `tools/build_screen_board.py` |
| 中 | **備份可悄悄關掉去識別化** | 備份只能「打開」去識別化；AI 設定不還原端點網址，服務商限清單 |
| 中 | **送 AI 前沒去識別化的路徑**：訊息整理（LINE 群組原文）、文字附件與檔名、AI 工作室 | 訊息整理與附件一律 `redactSensitiveText()`；AI 工作室送出前檢查身分證／手機／Email／座位表姓名，發現先問老師 |
| 中 | **🔑B 被拿去狂送點名**：推播內容用原始輸入（可塞假網址進老師的 LINE），也沒有次數上限 | 推播只用驗證過的座號與狀態；同一班一天最多推 6 次 |
| 中 | **🔑B 能讀全部班、改很久以前的補交** | 今天的紀錄一定要指定班級；補交只能改近 60 天；新增選單「🔄 重新產生 🔑B」 |
| 中 | **LINE 小幫手在群組裡會回覆出缺與座號查詢** | 只處理一對一聊天 |
| 中 | **Code.gs 沒有防試算表公式注入** | 加上 `sheetText_()`，任務文字欄位寫入前一律轉純文字 |
| 中 | **表單回覆副本可被當垃圾信跳板** | 每天最多寄 50 封，每題答案只附前 300 字 |
| 中 | **雲端備份分段以 `-`、`=` 開頭會被當公式**，還原失敗 | 分段一律 `sheetText_()` |
| 低 | 晨間大屏設定密碼：對話框直接寫「預設 1234」、不限次數、解鎖後整天開著 | 不提示預設值；錯 5 次鎖 1 分鐘；離開設定頁就重新上鎖；密碼欄改成遮蔽 |
| 低 | 安裝摘要把 🔑B／🔑C／🔑F 寫進 Apps Script 執行紀錄 | 拿掉 `Logger.log` |
| 低 | 收件匣「新增＋裁切」與「已匯入標記」沒上鎖，同時發生會標錯列 | 共用 `LockService` |
| 低 | 雲端回來的值未跳脫：大屏查詢的日期與狀態、小助手面板 | 全部跳脫 |
| 低 | 工作台查詢模型清單時 Gemini 金鑰放網址 | 改放 `x-goog-api-key` 標頭 |
| 低 | AI 回傳的數字與圖片格式未檢查（可卡死分頁）；超大 PDF | 行數限 1～6、圖片只收 png/jpeg/webp 的 base64；批改 PDF 一次最多 200 頁 |
| 低 | 晨間大屏、AI 工作室、螢幕公告放在其他主機時可被外站嵌入（點擊劫持） | 加防嵌入備援（同網站嵌入不受影響）。Index／Board 也由 Apps Script 以 iframe 提供，不能加 |
| 低 | 發版流程的第三方 action 用可變動的標籤 | `softprops/action-gh-release` 釘在固定 commit |

**金鑰外洩掃描**：220 個 commit 的每個版本都沒有 Gemini／OpenAI／xAI／GitHub 金鑰、GAS 部署網址或 LINE userId。
唯一的長 ID 是安裝教學「建立試算表副本」用的公開範本，屬刻意公開。

**這一輪確認為「已知取捨」**：
- 🔑B 沒有限定班級（GAS 端沒有班級名單）。外洩時用選單「🔄 重新產生 🔑B」換掉。
- LINE 小幫手會把老師傳的文字、照片、語音送 Gemini 分類（第 3、4 級功能）。系統自己的出缺、座號資料不會送；老師傳訊時請不要打學生全名。
- 試算表「📋 安裝總表」會顯示金鑰，方便老師複製；試算表不要分享給別人。
- 所有頁面仍允許行內程式（`'unsafe-inline'`），所以「跳脫」是主要防線；新增畫面一律用 `escapeHtml()`／`textContent`。
- 小助手允許 `cona0815.github.io` 整個網域與本機任何埠號（瀏覽器的來源不含路徑，無法只限單一專案）。

## 小助手 v2.1 語音輸入的邊界

- 只有 `desktop_pet_voice.py` 會把音檔送出電腦，且 `default_opener` 只接受 `VOICE_ALLOWED_HOSTS`（`generativelanguage.googleapis.com`、`api.groq.com`）；桌寵主程式仍不直接呼叫 `urlopen`（測試契約看守）。
- 錄音只在按住快捷鍵期間（`Recorder.start/stop`），上限 120 秒；音檔只存在記憶體，不寫檔、不備份、不經本機橋接送到網頁。
- 🔑D／Groq 金鑰只存在小助手本機資料檔（與 🔑C 同檔），面板端點僅限本機來源；面板回傳只有 `hasGeminiKey` 布林，不回傳金鑰本文。
- 「打字模式」用剪貼簿＋Ctrl+V 貼上，0.8 秒後還原原本的剪貼簿內容；全域快捷鍵監聽（pynput）只比對設定的那一兩個鍵，不記錄其他按鍵。

## 已知限制

- `localStorage` 不是加密保管庫。同一 Windows／瀏覽器帳號的使用者，以及網站本身執行的程式碼，都可能存取資料。
- 本機 `file://` 預覽在瀏覽器中使用 `Origin: null`。2026-11-06 起桌寵**不再**接受此來源（任何網站的沙箱 iframe 也會送 null）；本機測試請用 `http://127.0.0.1` 或 `localhost` 的靜態伺服器。
- 設定頁密碼（晨間大屏）只是擋學生誤觸，不是加密；密碼存在教室電腦的瀏覽器裡，懂得開開發者工具的人看得到。
- 自動去識別化可能漏判，不能取代教師人工確認。
- 未簽章 EXE 可能觸發 SmartScreen；即使本機掃描乾淨，也不能證明未來所有防毒引擎都不會誤判。

## 每次發布前

1. 執行語法檢查與自動測試。
2. 執行上表的程式碼掃描項目（至少：硬編碼金鑰、XSS、外連主機、API 權限、寫入試算表的自由文字），並把日期與結果補進「程式碼掃描紀錄」。
3. 用 Microsoft Defender 掃描實際要發出的 EXE／ZIP。
4. 對發布檔執行 `Get-FileHash -Algorithm SHA256`，把結果和檔案一起公布。
5. 檢查 `Get-AuthenticodeSignature`；正式大量發布建議使用受信任的程式碼簽章或 Microsoft Store。
6. 若 Defender 誤判，使用 Microsoft 官方提交入口送交分析；不要要求老師停用防毒或設定資料夾排除。

## 回報問題

回報時請提供版本、下載來源、SHA-256、Windows 版本與防毒偵測名稱；不要附上真實學生資料、API 金鑰或桌寵資料檔。

## v1.1 本機安全版驗證碼

請以 repository 最新發布頁或隨附的 `SHA256SUMS.txt` 為準；檔案重新打包後雜湊值一定會改變。
