# 校務行政每日任務管理系統（Google Apps Script）

一套以 Google Sheet 為資料底座、Google Apps Script 為服務層的校務任務管理系統。安裝時可選擇處室與職務，系統會套用相對應的任務類型、範例、管理台名稱及直向電子紙看板。

## 支援的處室與職務

| 處室 | 可選職務 |
| --- | --- |
| 教務處 | 教務主任、教學組長、註冊組長、設備組長、資訊組長 |
| 學務處 | 學務主任、訓育組長、生教組長、體育組長、衛生組長 |
| 輔導室 | 輔導主任、輔導組長、資料組長、特教組長 |
| 總務處 | 總務主任、事務組長、出納組長、文書組長 |
| 人事室 | 人事主任、人事管理員 |
| 會計室 | 會計主任、會計員 |

各 profile 都有自己的任務類型與 3 筆可選範例。新增處室時，只需在 `Code.gs` 的 `OFFICE_PROFILES` 加入設定，不必複製 CRUD、權限或看板程式。

## 功能

- 安裝精靈選擇學校名稱、處室與主任／組長職務
- 任務新增、編輯、完成、重開與封存
- 主任務／子任務專案階層、進度流程圖與日曆拖曳改期
- 獨立 Windows「教師秘書・小綿助」：今日／逾期／待追蹤、健康提醒、早晚簡報、文字與 Windows 語音輸入，以及圖片／文件／貼上附件
- 原創小羊桌面寵物動畫：待機、左右走動、聆聽、思考、成功、警告、睡覺與拖曳；平常常駐桌面，點擊角色才展開秘書首頁
- 狀態、優先級、期限、負責人與下一步行動
- 關鍵字與多條件篩選
- 直向、低動畫、黑白高對比的電子紙看板
- Google Sheet 下拉選單、格式與條件格式
- 工作紀錄稽核、CSRF 驗證、寫入鎖與 Workspace 網域限制
- 舊欄位遷移前自動備份
- 切換處室時保留舊任務與舊任務類型

## 檔案

- `Code.gs`：處室 profiles、安裝、遷移、CRUD、權限、稽核、Sheet 與看板 API
- `Installer.html`：處室／職務安裝精靈
- `Index.html`：任務管理台
- `Board.html`：直向電子紙看板
- `appsscript.json`：GAS 時區、V8 與 Web App 設定
- `tests/profile_config.test.js`：處室設定的本機檢查

## 安裝

1. 建立或開啟一份 Google Sheet。
2. 選擇「擴充功能 → Apps Script」。
3. 將本專案的 `Code.gs`、`Installer.html`、`Index.html`、`Board.html` 與 `appsscript.json` 加入該 Apps Script 專案。
4. 回到試算表重新整理。
5. 選擇「校務任務系統 → 安裝／選擇處室」。

小綿助為獨立桌面程式，不會顯示在網頁中。在 Windows 雙擊 `啟動小綿助秘書.bat` 即可啟動；桌面本機版目前使用 AppData 儲存秘書資料，與 Apps Script 任務及 Google 日曆的正式同步會在後續階段串接。所有寫入動作仍須由使用者確認。小綿助為本專案原創角色，動畫原始格與透明 WebP 成品存放於 `assets/pet/`，不再使用 DeskPet 白貓素材。
6. 選擇學校、處室、職務，以及是否加入範例任務。
7. 第一次安裝會要求授權。

### Windows 桌面小綿助

桌寵會跟著本專案一起放在 GitHub：動畫素材位於 `assets/pet/`，程式位於 `desktop_pet_preview.py` 與 `desktop_pet_secretary.py`，啟動檔是 `啟動小綿助秘書.bat`。它是獨立的 Windows 桌面程式，不會出現在 Netlify 網頁內。

使用前請安裝 Python 3.10 以上與 Pillow：

```powershell
py -m pip install -r requirements.txt
```

接著雙擊 `啟動小綿助秘書.bat`。桌面版資料目前保存在使用者的 AppData，不會自動寫入 GitHub、Netlify 或 GAS；之後若要同步，再另行設定 GAS 連線。

也可以在 Apps Script 函式選單執行 `installSystem()` 開啟相同的安裝精靈。

安裝完成後會建立：

- `任務清單`
- `工作紀錄`
- `系統設定`
- `選項清單`
- 試算表編輯觸發器

若偵測到舊版欄位，系統會先建立隱藏的 `原始資料備份_yyyyMMdd_HHmmss` 工作表，再轉成標準 23 欄資料契約。最後四欄為 `專案ID`、`上層任務ID`、`任務層級`、`工作主軸`；前三者讓主任務與子任務維持同一個專案群組，`工作主軸`則保存教學、行政、學年主任或導師四大分類。

### AI、雲端備份與 Drive 資料庫

1. 在工作台按「設定 → 教師資訊」，填寫職稱、任教科目、年級班級與參與的會議／委員會。姓名只用於本機介面，不放入 AI 背景。
2. 在「AI 設定」勾選「開啟 AI 功能」，再填入模型、端點與 API 金鑰。可至 [Google AI Studio](https://aistudio.google.com/app/apikey) 申請 Gemini API 金鑰；免費額度與限制以 Google 當時公告為準。
3. API 金鑰只保留於目前瀏覽器工作階段，不會寫入 JSON 或 Drive 備份。正式部署應把金鑰改存 GAS 的 Script Properties，並由伺服器端呼叫模型。
4. 「備份與還原 → 立即雲端備份」會在登入者的 Google Drive 建立 `School Admin Dashboard/Backups`。
5. 「Drive 資料庫」會把圖片、PDF、JSON、文字及常見 Office 檔案存入 `School Admin Dashboard/Workspace Files`。單檔上限為 35 MB；這是為 Base64 膨脹及 GAS 單次傳輸保留空間後的實用上限。
6. 首次使用 Drive 功能時，Apps Script 會要求 Google Drive 權限。修改 `Code.gs` 後需建立新版部署，既有 Web App 網址才會載入新方法。

雲端端點已包含：`backupDashboardToDrive`、`listDashboardBackups`、`getDashboardBackup`、`uploadWorkspaceFile`、`listWorkspaceFiles`。所有寫入均需通過 Workspace 授權、CSRF 驗證及 `LockService`。

### Netlify／本機離線模式

將 `Index.html` 與靜態資產部署到 Netlify、但尚未設定 GAS 時，系統會使用瀏覽器離線模式：任務新增、狀態變更、封存、模擬備份與檔案索引會保存於該瀏覽器的 `localStorage`，每位使用者彼此分開。資料不會自動跨電腦同步；請使用「備份與還原 → 下載 JSON 備份」搬移資料。

離線模式採用約 4 MB 的保守應用程式容量上限，設定頁會顯示使用量，接近上限時會提醒先匯出並清理。原始附件不直接寫入 `localStorage`；需要保存圖片、PDF 或 Office 檔案時，請設定 GAS 使用 Google Drive。

設定 GAS 後，任務與相關功能改由 Google Sheet、Drive 及 Google 日曆等雲端端點處理，是否能跨使用者共享則依 Google Workspace 授權與部署權限決定。

### Netlify 靜態預覽

本 repository 已附 `netlify.toml`，連接 GitHub 後可直接以 repository 根目錄部署。Netlify 版本是本機離線預覽；要使用 Google Sheet、Drive、日曆與正式 GAS 授權，請改用 Apps Script Web App 網址或另外設定可用的 GAS 端點。

## 部署 Web App

1. 在 Apps Script 右上角選擇「部署 → 新增部署」。
2. 類型選擇「網頁應用程式」。
3. 建議使用：
   - 執行身分：部署者
   - 存取權：學校 Workspace 網域內的使用者
4. 部署後可使用：
   - 管理台：`你的部署網址`
   - 電子紙看板：`你的部署網址?page=board`

在 `系統設定` 的 `ALLOWED_DOMAIN` 填入例如 `school.edu.tw`，可再限制登入網域。留空表示程式不額外檢查，但 Web App 部署權限仍是第一層防護。

## 切換處室

再次開啟「校務任務系統 → 安裝／選擇處室」即可切換。切換時：

- 不刪除或封存既有任務
- 不重新加入範例任務
- 新增任務改用新處室類型
- 舊資料曾使用的類型仍保留，避免既有任務無法編輯
- 管理台、看板、預設負責人與系統名稱改成新處室／職務

## 看板顯示邏輯

- `強制顯示`：一定顯示
- `隱藏`：不顯示
- `自動`：高優先級、等待、進行中，或在 `AUTO_SHOW_DAYS` 天內到期時顯示

## GitHub 與 clasp

此資料夾不含固定試算表 ID、Token 或學校資料，可直接作為 GitHub repository 的內容。若使用 [clasp](https://github.com/google/clasp)，請把個人的 `.clasp.json` 留在本機；本專案的 `.gitignore` 已排除它。

```bash
npm install -g @google/clasp
clasp login
clasp create --type sheets --title "校務行政每日任務管理系統"
clasp push
```

`clasp create` 產生的 `.clasp.json` 含個人 Script ID，不建議提交公開 repository。

## 本機檢查

```bash
node tests/profile_config.test.js
# 或
npm test
```

GitHub Actions 也會在 push 與 pull request 時執行同一組檢查。

## 授權

[MIT License](LICENSE)

介面使用的第三方圖示與原創角色素材說明請見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
