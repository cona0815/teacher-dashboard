# 國小教師工作台（Google Apps Script）

一套以 Google Sheet 為資料底座、Google Apps Script 為服務層的國小教師工作台。安裝時只需要設定學校名稱與主要工作身分，不再要求先選擇教務處、學務處等細部處室。

系統保留四大工作主軸：**教學、行政、學年主任、導師**。其中「行政」是教師可能承接的工作身分與工作分類，不代表必須建立或管理完整的行政處室架構。

## 功能

- 教師、導師、學年主任、行政四種工作身分
- 任務新增、編輯、完成、重開與封存
- 主任務／子任務專案階層、進度流程圖與日曆拖曳改期
- 獨立 Windows「教師秘書・小綿助」：今日／逾期／待追蹤、健康提醒、早晚簡報、文字與 Windows 語音輸入，以及圖片／文件／貼上附件
- 原創小羊桌面寵物動畫：待機、左右走動、聆聽、思考、成功、警告、睡覺與拖曳
- 狀態、優先級、期限、負責人與下一步行動
- 關鍵字與多條件篩選
- 直向、低動畫、黑白高對比的電子紙看板
- Google Sheet 下拉選單、格式與條件格式
- 工作紀錄稽核、CSRF 驗證、寫入鎖與 Workspace 網域限制
- 舊欄位遷移前自動備份

## 安裝

1. 建立或開啟一份 Google Sheet。
2. 選擇「擴充功能 → Apps Script」。
3. 將本專案的 `Code.gs`、`Installer.html`、`Index.html`、`Board.html` 與 `appsscript.json` 加入該 Apps Script 專案。
4. 回到試算表重新整理。
5. 選擇「校務任務系統 → 安裝教師工作台」。
6. 設定學校名稱、主要工作身分（教師、導師、學年主任或行政），以及是否加入教師範例任務。
7. 第一次安裝會要求授權。

安裝精靈不會建立或要求設定細部處室。舊版若曾使用處室 profile，程式仍保留必要的相容程式，可安全讀取既有任務；新的選項清單統一以教師四大工作主軸與既有任務類型為來源。

### Windows 桌面小綿助

小綿助是獨立的 Windows 桌面程式，不會出現在網頁內。動畫素材位於 `assets/pet/`，程式位於 `desktop_pet_preview.py` 與 `desktop_pet_secretary.py`，啟動檔是 `啟動小綿助秘書.bat`。

使用前請安裝 Python 3.10 以上與 Pillow：

```powershell
py -m pip install -r requirements.txt
```

接著雙擊 `啟動小綿助秘書.bat`。桌面版資料目前保存在使用者的 AppData，不會自動寫入 GitHub、Netlify 或 GAS；之後若要同步，再另行設定 GAS 連線。

## AI、雲端備份與 Drive 資料庫

1. 在工作台按「設定 → 教師資訊」，填寫職稱、任教科目、年級班級與參與的會議／委員會。
2. 在「AI 設定」勾選「開啟 AI 功能」，再填入模型、端點與 API 金鑰。可至 [Google AI Studio](https://aistudio.google.com/app/apikey) 申請 Gemini API 金鑰；免費額度與限制以 Google 當時公告為準。
3. API 金鑰只保留於目前瀏覽器工作階段，不會寫入 JSON 或 Drive 備份。正式部署應把金鑰改存 GAS 的 Script Properties，並由伺服器端呼叫模型。
4. 「備份與還原 → 立即雲端備份」會在登入者的 Google Drive 建立 `School Admin Dashboard/Backups`。
5. 「Drive 資料庫」會把圖片、PDF、JSON、文字及常見 Office 檔案存入 `School Admin Dashboard/Workspace Files`。單檔上限為 35 MB。

雲端端點已包含：`backupDashboardToDrive`、`listDashboardBackups`、`getDashboardBackup`、`uploadWorkspaceFile`、`listWorkspaceFiles`。所有寫入均需通過 Workspace 授權、CSRF 驗證及 `LockService`。

### Netlify／本機離線模式

將 `Index.html` 與靜態資產部署到 Netlify、但尚未設定 GAS 時，系統會使用瀏覽器離線模式：任務新增、狀態變更、封存、模擬備份與檔案索引會保存於該瀏覽器的 `localStorage`，每位使用者彼此分開。資料不會自動跨電腦同步；請使用「備份與還原 → 下載 JSON 備份」搬移資料。

離線模式採用約 4 MB 的保守應用程式容量上限，設定頁會顯示使用量，接近上限時會提醒先匯出並清理。原始附件不直接寫入 `localStorage`；需要保存圖片、PDF 或 Office 檔案時，請設定 GAS 使用 Google Drive。

設定 GAS 後，任務與相關功能改由 Google Sheet、Drive 及 Google 日曆等雲端端點處理，是否能跨使用者共享則依 Google Workspace 授權與部署權限決定。

## 部署 Web App

1. 在 Apps Script 右上角選擇「部署 → 新增部署」。
2. 類型選擇「網頁應用程式」。
3. 建議使用：執行身分選部署者，存取權依學校 Workspace 政策設定。
4. 部署後可使用管理台網址與 `?page=board` 電子紙看板網址。

在 `系統設定` 的 `ALLOWED_DOMAIN` 填入例如 `school.edu.tw`，可再限制登入網域。留空表示程式不額外檢查，但 Web App 部署權限仍是第一層防護。

## GitHub 與 clasp

此資料夾不含固定試算表 ID、Token 或學校資料，可直接作為 GitHub repository 的內容。若使用 [clasp](https://github.com/google/clasp)，請把個人的 `.clasp.json` 留在本機；本專案的 `.gitignore` 已排除它。

```bash
npm install -g @google/clasp
clasp login
clasp create --type sheets --title "國小教師工作台"
clasp push
```

## 本機檢查

```bash
node tests/profile_config.test.js
# 或
npm test
```

## 授權

本專案是在 [mihozip/school-admin-daily-dashboard](https://github.com/mihozip/school-admin-daily-dashboard) 基礎上修改，原始專案採 MIT 開源授權；本版本亦依 MIT License 發布。原作者與第三方素材的來源說明集中放在系統設定的「授權」分頁及 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

[MIT License](LICENSE)
