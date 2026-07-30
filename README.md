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
6. 選擇學校、處室、職務，以及是否加入範例任務。
7. 第一次安裝會要求授權。

也可以在 Apps Script 函式選單執行 `installSystem()` 開啟相同的安裝精靈。

安裝完成後會建立：

- `任務清單`
- `工作紀錄`
- `系統設定`
- `選項清單`
- 試算表編輯觸發器

若偵測到舊版欄位，系統會先建立隱藏的 `原始資料備份_yyyyMMdd_HHmmss` 工作表，再轉成標準 19 欄資料契約。

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
