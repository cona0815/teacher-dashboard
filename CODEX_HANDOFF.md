# 專案交接

- 目標：完成臺南市國小教師／學年主任工作系統，並以獨立 Windows 桌面「小綿助」作為教師秘書。
- 階段：開發中；網頁任務系統功能持續完善，桌面秘書已完成第一個本機版本。
- 最新完成：教學進度的學校自訂假日改為「日期選擇器＋原因」多列編輯器，並支援舊文字格式自動轉換、儲存、備份與還原；系統設定新增「授權」分頁，標示原始校務系統、原作者 Facebook、DeskPet 流程參考及 Koboyo 圖示來源。小綿助已從網頁隱藏，新增 `desktop_pet_secretary.py` 與 Windows 啟動檔；支援今日、逾期、待追蹤、健康管理、早晚簡報、語音輸入、檔案選擇及剪貼簿圖片。Netlify 離線預覽的任務、模擬備份與檔案索引已改用 localStorage 持久保存，並有 4 MB 保守容量提示與清理入口；新增 `netlify.toml`、`requirements.txt` 與桌寵安裝說明。
- 重要檔案：`Index.html`、`desktop_pet_preview.py`、`desktop_pet_secretary.py`、`啟動小綿助秘書.bat`、`assets/pet/`。
- 測試：`python -m py_compile desktop_pet_preview.py desktop_pet_secretary.py`、`npm.cmd test` 均通過。
- 目前風險：桌面秘書資料仍存於本機 AppData，尚未與 Apps Script 任務、Google Calendar、Drive 或 AI API 正式同步。
- 下一個安全任務：定義桌面秘書與 GAS 的授權及同步資料格式，再實作唯讀取得任務，最後才加入經確認的寫入。
