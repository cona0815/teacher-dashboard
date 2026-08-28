# 資安與發布檢查

## 資料邊界

- 網頁任務、進度與設定：目前瀏覽器的 `localStorage`。
- 桌寵任務、記事與附件：目前 Windows 帳號的 `%APPDATA%\XiaoMianZhuSecretary\`。
- 網頁與桌寵：只透過 `http://127.0.0.1:8767` 交換資料。
- AI：只有開啟 AI 並送出內容時，才會連線到設定的模型服務；送出前須人工檢查去識別化結果。

## 已採取的防護

1. 桌寵伺服器只綁定 IPv4 回環位址，不接受區域網路或外網連線。
2. 只提供 `/health` 與 `/sync`，拒絕其他路徑；限制來源、方法、Content-Type 與 5 MB 請求大小。
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
| `Code.gs` 對外端點 | `doGet` 只吐 HTML 殼，資料函式一律先過 `assertAuthorized_()`；`doPost`（小綿助同步）先驗 `DESKTOP_PET_SYNC_KEY`，單次上限 1000 筆 |
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
  所有建議都要老師按下確認才寫入。仍請維持人工複核。
- **桌寵本機端點沒有金鑰**：`127.0.0.1:8767` 的 `/sync` 只靠來源白名單，不驗證金鑰。
  只綁回環位址，同機器上的其他程式仍可存取。若機器已被惡意程式入侵，此防線本就無效；
  一般使用情境下風險可接受。
- **Gemini 金鑰放在網址查詢參數**：這是 Google Generative Language API 的官方用法
  （`?key=`）。若要更保守，可改用 `x-goog-api-key` 標頭。

已修正：**試算表公式注入**。寫進試算表的自由文字（班級、科目、進度、聯絡本、
LINE 收件匣、檔案備份標題）若以 `=`、`+`、`-`、`@` 開頭，Google Sheets 會當公式執行，
例如被寫入 `=IMAGE("http://…")` 時，老師一開啟試算表就會對外連線。
已加入 `sheetText_()`，寫入前補前導單引號強制為文字。

## 已知限制

- `localStorage` 不是加密保管庫。同一 Windows／瀏覽器帳號的使用者，以及網站本身執行的程式碼，都可能存取資料。
- 本機 `file://` 預覽在瀏覽器中使用 `Origin: null`；為方便本機測試，桌寵允許此來源。正式使用應優先開啟官方 Netlify／GitHub Pages 網址。
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
