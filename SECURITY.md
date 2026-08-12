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

## 已知限制

- `localStorage` 不是加密保管庫。同一 Windows／瀏覽器帳號的使用者，以及網站本身執行的程式碼，都可能存取資料。
- 本機 `file://` 預覽在瀏覽器中使用 `Origin: null`；為方便本機測試，桌寵允許此來源。正式使用應優先開啟官方 Netlify／GitHub Pages 網址。
- 自動去識別化可能漏判，不能取代教師人工確認。
- 未簽章 EXE 可能觸發 SmartScreen；即使本機掃描乾淨，也不能證明未來所有防毒引擎都不會誤判。

## 每次發布前

1. 執行語法檢查與自動測試。
2. 用 Microsoft Defender 掃描實際要發出的 EXE／ZIP。
3. 對發布檔執行 `Get-FileHash -Algorithm SHA256`，把結果和檔案一起公布。
4. 檢查 `Get-AuthenticodeSignature`；正式大量發布建議使用受信任的程式碼簽章或 Microsoft Store。
5. 若 Defender 誤判，使用 Microsoft 官方提交入口送交分析；不要要求老師停用防毒或設定資料夾排除。

## 回報問題

回報時請提供版本、下載來源、SHA-256、Windows 版本與防毒偵測名稱；不要附上真實學生資料、API 金鑰或桌寵資料檔。

## v1.1 本機安全版驗證碼

請以 repository 最新發布頁或隨附的 `SHA256SUMS.txt` 為準；檔案重新打包後雜湊值一定會改變。
