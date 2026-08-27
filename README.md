# 國小教師工作台＋小綿助

給國小教師、導師、學年主任與兼任行政教師使用的本機優先工作台。老師只要連上網站即可開始使用，不必申請 Google Apps Script、不必登入，也不需要共用資料庫。

## 使用方式

1. 開啟部署在 Netlify 的教師工作台。
2. 任務、教學進度、記事與介面設定會保存在這台電腦目前瀏覽器的 `localStorage`。
3. 下載並啟動 Windows 桌面程式「小綿助」，網頁會透過 `127.0.0.1:8767` 與它交換任務及記事。
4. 定期使用「系統設定 → 備份與還原 → 下載 JSON 備份」。

不同瀏覽器、Windows 帳號與網站網域的資料彼此獨立。清除網站資料、重灌電腦或更換瀏覽器前，務必先下載備份。系統保守使用約 4 MB 的瀏覽器空間，原始附件不存入 `localStorage`。

新使用者第一次開啟會看到空白任務清單，不會載入示範任務。曾使用舊版的人更新後，系統只會自動移除可明確辨識的 `demo@school.edu.tw`／`G6-xxx` 內建示範任務；自行新增的任務、課程進度、設定與記事都會保留。

## 主要功能

- 教學、行政、學年主任、導師四種工作分類
- 主任務／子任務、完成、重開、封存、期限與日曆拖曳
- 各任教課程獨立的教學與評量進度
- 本機 AI 輔助介面與去識別化提醒（需自行設定 Gemini API 金鑰）
- Windows 桌面小綿助：今日、逾期、待追蹤、記事、附件整理、喝水、起身與服藥提醒
- JSON 備份與還原
- LINE 小幫手（選用）：在 LINE 傳文字、語音或照片，經工作台「LINE 收件匣」確認後建立任務或記事；可查今日進度、產生聯絡簿公告、接收晨間簡報。安裝方式見 [LINE_BOT_INSTALL.md](LINE_BOT_INSTALL.md)
- 晨間大屏（選用）：`Morning.html` 教室觸控頁，以座號完成點名（病假／事假／遲到／未到）與各科作業繳交登記（已交綠／缺交紅／補交藍），送出即推播老師 LINE，並提供分科天數統計查詢；工作台日曆同步顯示每日出缺與缺交摘要

## 設計參考聲明

本專案的 LINE 整合與晨間大屏為獨立設計與實作。開發過程中曾參考網路上多篇 LINE＋GAS＋Gemini 的公開教學與產品介紹作為市場調研——包含 [ijun-ai 教師智慧管家的功能介紹頁](https://www.ijun-ai.com/tutor/line-bot/) 與 [黃暐鑫老師的 LINE 班級小幫手介紹頁](https://sites.google.com/view/weishinhuang/%E8%87%AA%E6%88%91%E9%96%8B%E7%99%BC%E7%9A%84%E9%9B%9C%E4%B8%83%E9%9B%9C%E5%85%AB/line%E7%8F%AD%E7%B4%9A%E5%B0%8F%E5%B9%AB%E6%89%8B)——未使用任何第三方程式碼；功能取捨與資料架構（localStorage 本機優先、收件匣確認制、晨間大屏班級經營）均為本專案原創決策，過程記錄於 `LINE_BOT_SPEC.md`。

## LINE 小幫手（選用）

由老師自行部署 `LineBot.gs` 到自己的 Google Apps Script，搭配自己的 LINE 官方帳號與試算表；試算表只是「轉運信箱」，訊息被工作台收下後正本仍在瀏覽器 `localStorage`。未啟用時，工作台與小綿助完全不受影響。金鑰與網址不會寫入 JSON 備份或 GitHub。桌面小綿助以唯讀方式顯示「LINE 待整理」清單（經本機橋接由網頁轉入，桌寵本身不連網）。

## 網頁與小綿助連動

小綿助啟動後只在本機回環位址 `127.0.0.1:8767` 提供同步服務，不監聽區域網路或網際網路。工作台會在開啟、切回頁面、資料變更及每 60 秒嘗試交換一次資料；未啟動小綿助時，網頁和桌寵仍各自保留本機功能。

桌寵資料位於：

```text
%APPDATA%\XiaoMianZhuSecretary\
```

桌面附件不會自動送進瀏覽器，網頁附件也不會自動寫入桌寵資料夾；同步內容限任務欄位、記事文字、時間與附件名稱。

### 從 Python 原始碼啟動

一般老師不需要安裝 Python。請下載 [小綿助 Windows 穩定強化版 v1.7](https://github.com/cona0815/teacher-dashboard/releases/download/xiaomianzhu-v1.7/xiaomianzhu-windows-portable.zip)，解壓縮後直接開啟 `XiaoMianZhu.exe`。

v1.7 SHA-256：`c39e8ed58802254d0dd83f93d7e18eedc2914e18c8360643cbec5959c2b4060a`

開發者若要從原始碼執行，才需要 Python 3.10 以上：

```powershell
py -m pip install -r requirements.txt
py desktop_pet_secretary.py
```

也可以雙擊 `啟動小綿助秘書.bat`。工作台的「系統設定 → 小綿助」可產生 `xiaomianzhu_settings.json`；把它放在程式旁邊並啟動一次，即可匯入名稱、提醒與自動啟動等偏好。

## AI 與隱私

AI 功能為選用。API 金鑰可選擇保存在目前瀏覽器；這可免除重複輸入，但同一台電腦上能使用該瀏覽器帳號的人也可能使用它。金鑰不會寫入 JSON 備份。

去識別化規則無法保證完全辨識個資。學生姓名、電話、地址、健康、輔導、性平或其他敏感紀錄，不應直接送到外部 AI；送出前仍須由老師人工確認。

## 資安與防毒說明

- 網頁不要求登入、GAS、Google Sheet 或 Drive 權限；預設資料不離開目前瀏覽器。
- 本機橋接只綁定 `127.0.0.1`，限制可接受的網站來源、HTTP 方法與 5 MB 請求上限，不提供任意檔案讀取。
- Netlify 設定包含 CSP、`nosniff`、Referrer Policy、Permissions Policy 與同源隔離標頭。
- 正式分享的檔案應附 SHA-256 驗證碼，並先用 Microsoft Defender 掃描。
- 未簽章的新 EXE 可能被 Windows SmartScreen 顯示「無法辨識的應用程式」。這是檔案信譽／程式碼簽章警告，不等同已判定為病毒，也無法保證每所學校的資訊政策都會允許執行。
- 不要要求使用者關閉防毒或把整個資料夾加入排除。若遭誤判，應提交檔案給 Microsoft 分析，並以簽章或 Microsoft Store 發布改善信譽。

完整威脅模型與發布檢查請見 [SECURITY.md](SECURITY.md)。

## Netlify 部署

repository 根目錄已有 `netlify.toml`。把 GitHub repository 連接到 Netlify，Publish directory 使用 `.` 即可。網站部署後，每位老師在自己的瀏覽器建立獨立資料，不會看到其他人的任務。

## 本機檢查

```powershell
python -m py_compile desktop_pet_preview.py desktop_pet_secretary.py
npm test
```

## 授權

本專案是在 [mihozip/school-admin-daily-dashboard](https://github.com/mihozip/school-admin-daily-dashboard) 基礎上修改，原始專案與本版本均依 MIT License 發布。原作者、Koboyo 圖示、本修改版插圖及小綿助動畫素材來源記錄於系統設定的「授權」分頁與 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

[MIT License](LICENSE)
