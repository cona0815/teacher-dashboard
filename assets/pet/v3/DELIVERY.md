# 交件說明：phase 2（2026-09-28）

分支：`codex/pet-sprites-v3-phase2`。新增 10 組、78 格；第一批 11 組與 redo1 成果保持原樣。這次只交圖，不接桌寵程式。

## 交件結果

| 動作 | 格數 | 檢查結果 | 來源（自生／raw） | 備註 |
|---|---:|---|---|---|
| idle_blink | 6 | PASS | 自生 | 睜眼、閉眼彎線、小幅側頭、睜眼；葉片固定同側。 |
| idle_grade | 8 | PASS | 自生（第三稿） | 坐姿改作業，同一側持紅筆；書頁只有粗勾。前兩稿換手已淘汰。 |
| mail | 8 | PASS | 自生 | 抱實心淺綠空白泡泡、小跳與晃動；沒有 Logo 或內部圓點。 |
| drink | 8 | PASS | 自生 | 雙前腳抬淡藍杯、閉眼喝水、放下。 |
| stretch | 8 | PASS | 自生 | 前腳伸低、背拱起、站回與輕晃；頭保持圓形。 |
| medicine | 8 | PASS | 自生 | 空白金色鬧鐘、白藥盒、短粗震動線；輕拍幅度較小。 |
| focus | 8 | PASS | 自生 | 坐姿看空白書、逐格翻頁；番茄計時器沒有字或刻度。 |
| watch | 8 | PASS | 自生 | 舉深綠望遠鏡、側頭看、放下與噘嘴，再回復表情。 |
| note | 8 | PASS | 自生 | 逐步畫出兩條粗波浪線，將金色便利貼放到身旁。 |
| sign | 8 | PASS | 自生（第二稿） | 雙前腳把空白白邊深綠板抬到頭頂；第一稿單手持牌已淘汰。 |

正式驗收：**21 PASS、0 WARN、0 FAIL，退出碼 0**。新圖為一橫排；idle_blink 為 3072×512，其餘為 4096×512。RGBA 真透明、alpha 二值化；沒有補格、刪格或以複製格湊數。

## 來源、提示詞與整理

全部由內建 image_gen 生成，使用原有 `reference/sheep_ref.png` 與 `sheets/idle.png` 雙參考；沒有第三方素材、DeskCat、CLI 生圖或 API 金鑰。使用 imagegen／generate2dsprite 技能，依老師要求覆蓋技能的洋紅底預設，採透明底與指定單橫排。程式只做既有圖片清理、切格、整組等比例缩放、對齊，不繪製角色。

提示詞集合以本次 `spec.json` 的 common_prompt 及十個 phase 2 action prompt 為基礎，每組填入實際格數。共同加強：固定小黑點眼睛、臉的位置與頭身比、葉根在畫面右側、道具小而實心並靠近身體、完整留在各自格內、無字／數字／Logo／洋紅。

最終補充控制：idle_blink 指定六格睜閉順序與極小側頭；idle_grade 固定畫面左側持筆，右頁先有一個粗勾，筆只在左頁畫另一勾；mail 指定小幅起跳與落地；drink 指定抬杯—喝水—放下；stretch 指定伸低—拱背—站回—輕晃；medicine 指定空白鐘面、白盒及貼近鐘的粗短線；focus 指定書頁連著書脊翻動、番茄無刻度；watch 指定鏡片是道具而非放大的眼睛；note 只用兩條無圈的粗波浪線；sign 指定兩前腳分別抓看板左右下角、板貼近毛頂而不向遠處伸高。

原圖原樣保存在 `raw/<動作>.png`。三張未採用稿件保存在 `raw/rejected/idle_grade-phase2-attempt1.png`、`idle_grade-phase2-attempt2.png`、`sign-phase2-attempt1.png`；沒有刪除原圖。

先執行既有整理程式，**一定使用 --only，避免重新輸出第一批**：

```sh
python assets/pet/v3/normalize_raw.py --phase 2 --only idle_blink idle_grade mail drink stretch medicine focus watch note sign
```

再做兩組一致倍率的尺寸整理：sign 各格的非透明外框整組乘 **1.12**；stretch 各格整組乘 **382/419（約 0.91169451）**。每格裁切非透明外框後以同一倍率 Lanczos 縮放、alpha 以 128 二值化、清除透明 RGB、水平置中、底部對 y=488。未逐格變倍率、未拉伸長寬比。這是為了避免舉牌把羊身縮小，以及伸展站姿大於 idle。此步只處理這兩張 sheet，未修改 normalize_raw.py；日後從 raw 重建時須在 normalize 後重做此步，**不要在已調整的 sheet 上重複乘倍率**。

## 目視檢查與限制

已檢視 `_preview/overview.png`，並解碼十個 GIF 的全部 78 格、加上原 idle 比對，產生 `_preview/phase2-gif-review.png` 逐格目視檢查。這是 GIF 逐格檢視，並非在桌寵程式中實播驗收。預覽沿用既有 .gitignore，不納入 commit。

- 十組均維持同一角色外觀，沒有可見文字、字母、數字或 Logo；書本／鐘面／板面留白，便利貼只保留指定波浪線，作業本只保留勾形。
- 原 idle 奶油色外框高度約 382 px。新一般站姿／坐姿約 372～387 px；mail 蹲姿約 349 px。sign 第一格調整後約 382 px；stretch 站姿調整後約 382 px，伸展格依 free_scale 變低。這是排除綠葉與黑臉、以奶油色色域估算的外框，不是精確骨架量測；道具遮擋與抬手會影響外框。
- idle_blink 奶油色外框寬 373～384 px、高 376～381 px；最大／最小寬差約 2.95%、高差約 1.33%。這只支持小幅輪廓變化，不等同逐像素輪廓距離小於 3%。
- 正面眼睛與臉的位置目視接近 idle，仍有生成式圖像的小幅輪廓差異，不是逐像素複製。坐姿、持物與伸展不會有完全相同的身體外框。
- 本批全部毫秒設定均可被 GIF 的 10 ms 單位表示，沒有本批播放時間捨入問題。未變更 spec 或桌寵播放設定。

## 需要老師重生的圖（phase 2）

目前沒有尚未處理的錯格、文字、換手持筆或單手持牌問題。以下美術限制如需更嚴格可再重生；沒有擅改規格或用程式重畫：

- **精確色票／純扁平限制（十組）**：生成圖仍帶有參考圖的極淡奶油明暗，道具像素也含縮放／生成造成的近似色，不保證只含六個精確 RGB。若六色必須是逐像素白名單，本批仍需更嚴格重生或由老師另外授權道具限色處理。建議「exact solid palette fills, no shading, no texture, no intermediate colors」。
- **medicine**：拍鐘的前腳位移很小，主要動感来自粗短震動線；若希望在小尺寸顯示時也清楚看出拍打，建議增大前腳抬起—落下幅度，保持鐘面空白、其他比例不變。
- **idle_grade 的循環銜接**：最後已有兩個勾，回到第一格會重置為一個既有勾；這是本次繪畫循環的重置點，不是無縫連續書寫。若需要無縫循環，建議重生加入翻到新空白頁的回復段，但仍維持 8 格，不自行改 spec。

## check_sprites.py 完整輸出（phase 2）

命令：`python assets/pet/v3/check_sprites.py --phase 2 --preview`。Pillow DeprecationWarning 是既有 getdata API 的未來淘汰提示，不是 sprite WARN；依要求未修改驗收程式。

```text
C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\check_sprites.py:80: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
  magenta = sum(1 for r, g, b, a in fr.getdata() if a >= 32 and is_magenta(r, g, b))
[PASS] idle（6 格）
[PASS] walk_right（8 格）
[PASS] drag（6 格）
[PASS] sleep（6 格）
[PASS] listen（6 格）
[PASS] think（8 格）
[PASS] success（8 格）
[PASS] warning（8 格）
[PASS] peek（6 格）
[PASS] greet（8 格）
[PASS] overdue（8 格）
[PASS] idle_blink（6 格）
[PASS] idle_grade（8 格）
[PASS] mail（8 格）
[PASS] drink（8 格）
[PASS] stretch（8 格）
[PASS] medicine（8 格）
[PASS] focus（8 格）
[PASS] watch（8 格）
[PASS] note（8 格）
[PASS] sign（8 格）
預覽：C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\_preview\overview.png

結果：21/21 通過
```

## 範圍與接線

僅新增第二批 raw／sheets、三張淘汰稿與更新本文件。第一批 11 張 sheets、原 reference、spec.json、check_sprites.py、normalize_raw.py、舊 frames 與應用程式均未修改。資料契約、權限、安裝與部署不受影響，無需重跑安裝或重新部署；未做應用程式功能測試，桌寵接線與實播由 Claude 後續處理。未 push、未合併、未打 tag。

---

# 重做 redo1（2026-09-28）

分支 `codex/pet-sprites-v3-redo1`。依本次更新後的 `spec.json` 重生 idle、drag、sleep、warning、greet，共 34 格。使用原有 `reference/sheep_ref.png`、內建 image_gen 與現有 normalize_raw.py。未修改任何程式、spec 或驗收工具；其他六組 raw／sheets 保持原樣。

## 修改與檢視結果

| 動作 | 格數 | 結果 | 重做內容及檢視 |
|---|---:|---|---|
| idle | 6 | PASS | 葉根全程在畫面右側，只彎葉尖。第二次生成後奶油色輪廓外框高度六格皆 382 px、寬度 379～383 px，外框寬差約 1.06%、高差 0%；頭部比例與眼睛位置目視穩定。 |
| drag | 6 | PASS | 恢復圓頭和短圓雲朵毛，不再尖錐；圓口、垂腳與左右擺動。第一稿多畫人手已淘汰，第二稿第 3 格葉片換側，經 image_gen 修正後六格固定同側。 |
| sleep | 6 | PASS | 改為側躺的圓毛球，臉靠右下、腳完全收進毛裡，閉眼彎線、緩慢呼吸；沒有 z 或任何字母。 |
| warning | 8 | PASS | 全程正面、淺跳。奶油色身體外框第 1／8 格高 319 px，第 3／7 格高 301／304 px，蹲姿約 94.4%／95.3%，高於 85%。落地底線 y=488、最高騰空底線約 y=459；驚嘆號貼近毛頂。沒有 WARN。 |
| greet | 8 | PASS | 固定自身左前腳（畫面右側）揮動，另一側維持放下。太陽從毛後露出後逐格升高，八格都可見；金色區域頂端 y 約為 148、141、127、109、99、89、75、65，沒有中途突然出現或消失。 |

已讀取五個 `_preview/*.gif` 的全部 34 格，透過現有工具解碼為逐格接觸表，以眼睛檢視頭形、腳的位置、葉片、側躺、正面方向及太陽連續位置；並檢查最終 `_preview/overview.png`。屬逐格動畫檢視，未宣稱在桌寵程式中實播。GIF 時間量化沿用原工具，drag 的 125 ms 在 GIF 中為 120 ms；spec 未改。

「輪廓小於 3%」量測以排除綠葉／黑臉後的奶油色身體外框長寬為依據，不等同逐像素輪廓距離。結果加上逐格目視支持小幅呼吸；未藉逐格縮放或複製格子湊數。

## 原圖留存與重現

舊的五張原圖已按要求移至 `raw/rejected/<動作>-v1.png`，新的原圖在 `raw/<動作>.png`。redo1 未採用的稿件另存 `idle-redo1-attempt1.png`、`drag-redo1-attempt1.png`、`drag-redo1-attempt2.png`，沒有覆寫舊備份。

每次生成都使用更新後的 action prompt 與 common_prompt 的角色、透明底、單橫排、無字、無洋紅限制。補充提示：idle 固定頭高及眼睛 y；drag 隱形提起、不畫人手且禁止尖毛；sleep 明確側躺而非坐姿；warning 固定正面及 95% 蹲高；greet 明確自身左腳對應畫面右側並指定太陽每格上升。最終 idle 與 drag 使用 image_gen 參考編輯改善，不使用程式繪製／變形角色。

```sh
python assets/pet/v3/normalize_raw.py --only idle drag sleep warning greet
python assets/pet/v3/check_sprites.py --only idle drag sleep warning greet --preview
```

## 需要老師重生的圖（redo1）

本次五項動作修正均已可辨識，沒有尚未處理的指定動作問題。仍有生成式圖片的微小輪廓差異，並非數學上逐像素相同。greet 的細小太陽光芒經現有清理程式去雜點後大多消失，成為金色圓太陽，最後一格仍有短光芒；上升動作與同手揮動正確，若要求光芒也完全一致，建議日後重生提示指定「solid gold sun disk without detached rays」。未為此修改清理程式。舊版下方的待重生清單保留作歷史，這五張以上方 redo1 結果為準。

## check_sprites 完整輸出（redo1）

命令：`python assets/pet/v3/check_sprites.py --only idle drag sleep warning greet --preview`。退出碼 0；5 PASS、0 WARN、0 FAIL。Pillow 的 API 淘汰提示不是 sprite WARN。

```text
C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\check_sprites.py:80: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
  magenta = sum(1 for r, g, b, a in fr.getdata() if a >= 32 and is_magenta(r, g, b))
[PASS] idle（6 格）
[PASS] drag（6 格）
[PASS] sleep（6 格）
[PASS] warning（8 格）
[PASS] greet（8 格）
預覽：C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\_preview\overview.png

結果：5/5 通過
```

僅更新指定五張 sheets、其 raw／備份與本文件。無應用程式、資料契約、權限、安裝或部署變更。未 push、未合併。

---

# 交件說明：phase 1（2026-09-28）

分支：`codex/pet-sprites-v3-phase1`。本次只交圖與整理工具，不接桌寵程式。

## 交件結果

| 動作 | 格數 | 檢查結果 | 來源（自生／raw） | 備註 |
|---|---:|---|---|---|
| idle | 6 | PASS | 自生 | 呼吸、葉片擺動；見下方視覺限制 |
| walk_right | 8 | PASS | 自生 | 向右交替步態，保留原圖高低變化 |
| drag | 6 | PASS | 自生 | 懸吊擺動、圓口；拉伸較誇張 |
| sleep | 6 | PASS | 自生 | 閉眼縮身呼吸；未畫禁止的 z 字母 |
| listen | 6 | PASS | 自生 | 麥克風、側頭、聲波 |
| think | 8 | PASS | 自生（第二次） | 分紙、抬頭、橫向圓點依序出現 |
| success | 8 | PASS | 自生（第二次） | 蓋章、勾記、蹲身、小跳、落地 |
| warning | 8 | WARN | 自生 | 第 3、7 格蹲身高度 46%；見 WARN 說明 |
| peek | 6 | PASS | 自生 | 右側探頭及前蹄，首尾保留少量可見內容 |
| greet | 8 | PASS | 自生 | 揮蹄、金色太陽；見下方視覺限制 |
| overdue | 8 | PASS | 自生 | 無數字月曆格、紅圈、擔心表情、小跳 |

共 78 格。6 格圖尺寸 3072×512，8 格圖尺寸 4096×512；所有 PNG 為 RGBA，alpha 值僅 0／255。驗收結果為 10 PASS、1 WARN、0 FAIL。技術 PASS 不代表所有生成畫面已完全符合美術要求；下方列出尚需人工決定／重生的項目。

## 參考圖與來源

- 開始時 `raw/`、`reference/` 只有 README，沒有老師預先放入的原圖。
- 使用本對話最後生成的四視圖羊，原樣複製為 `reference/sheep_ref.png`，每次生成均附同一張參考圖。
- 參考圖 SHA-256：`8aad279194436ae4e9a1130cf2f18aebff9d2bc86bba23a920cd301588c1625d`。
- 全部使用內建 image_gen 生成，無 CLI/API 金鑰、無 DeskCat、無第三方素材。
- 每組選用原圖存於 `raw/<動作>.png`，未修改原圖像素。兩張重生前的失敗圖保留在 `raw/rejected/`。
- 僅改動 `assets/pet/v3/`；`spec.json`、`check_sprites.py`、舊版 frames/webp 及應用程式皆未修改。

## 整理流程

`normalize_raw.py` 僅需 Python＋Pillow；它不畫角色、不增加或刪除格、不製造中間動作。

1. 若原圖為不透明底，用四角背景色做邊緣連通填色去背，避免全圖白色色鍵挖掉羊或紙張。此次原圖均已有 alpha。
2. 原始 alpha 以 224 為界二值化，去除透明邊緣殘留、洋紅色像素及小型獨立雜點，保留紙張、聲波、圓點等較大元件。
3. 核對主要角色連通元件數量必須等於規格格數，於預期格界附近找低佔用透明欄切格；不合格即回報重生。
4. 每個動作使用同一個縮放倍率，以約 384 px 高為目標，並同時考慮最寬格、最高格及跳躍整體範圍，保留安全邊界。不逐格拉伸、不改長寬比。
5. 一般動作水平置中，底線 y=488；跳躍保留來源相對位移。drag 為懸吊動作用較高底線；peek 依 `free_center` 靠右，保留進出裁切。
6. 縮放後再次二值化 alpha 並清除全透明像素 RGB，輸出單橫排 PNG。

可重現指令（從專案根目錄執行）：

```sh
python assets/pet/v3/normalize_raw.py --phase 1
python assets/pet/v3/check_sprites.py --phase 1 --preview
python assets/pet/v3/normalize_raw.py --phase 1 --review-gifs
```

已檢查 `_preview/overview.png`，並逐一打開、解碼全部 11 個 GIF 的 78 格，以 `_preview/gif-review.png` 逐格檢視。這是逐格檢視，不是桌寵程式實播驗收。GIF 格數皆與規格一致；沒有透過複製同格湊數。預覽依既有 `.gitignore` 不納入 commit，可用上述指令重建。

## WARN 與工具提示

- `warning` 第 3、7 格是原圖的蹲身壓縮姿勢，高度約 46%。警告符號和騰空格需要上方空間，因此以同一倍率處理整組後，蹲身格低於工具建議的 55% 下限。沒有逐格放大或放寬檢查。可播放，但不同動作切換時視覺大小仍需老師／Claude 檢查。
- Pillow 顯示 `Image.getdata()` 的 DeprecationWarning；這是未來 Pillow 14 的 API 淘汰提示，不是圖片 FAIL。未修改老師的驗收程式。
- GIF 以 10 ms 為單位記錄時長，因此 drag 125 ms 在預覽變 120 ms、listen 155 ms 變 150 ms、think 145 ms 變 140 ms。PNG、spec 及桌寵實际播放設定沒有修改。
- 現有驗收器不檢查角色長相、道具精確 RGB 或文字辨識；因此另作視覺檢視，不能只靠 PASS 當作美術完全合格。

## 需要老師重生的圖

以下問題沒有改規格或用程式硬修角色。技術檔案完整，但建議正式接線前依美術要求決定重生：

- **sleep：規格衝突。** prompt 要求「small z」，總規格與老師指示禁止所有字母。此次優先遵守無文字，未画 z。姿勢較像閉眼坐成一團，不是明確側躺蜷睡。建議先確認取消 z，重生提示加「curled on its side, legs tucked into wool, no z or any letters」。`spec.json` 未改。
- **drag：羊毛拉伸過長。** 頭頂被拉成尖長形，雖保留葉片、耳朵及圓口，但比參考形狀誇張。建議加「scruff stretches only slightly, preserve rounded head and short cloud tuft, never cone-shaped」。
- **idle：葉片方向與輪廓仍有漂移。** 第 3 格葉片轉向，部分格的身體形狀也不只是小幅呼吸。建議加「leaf bends without switching attachment side, body outline changes less than 3%, fixed head proportions」。
- **warning：蹲身造型與高度 WARN。** 第 3、7 格較矮且偏側面，與其餘正面格有轉向。建議加「fixed front view, crouch at least 85% of standing height, small exclamation close to tuft, shallow hop」。
- **greet：揮蹄不夠一致。** 中間幀看起來會換邊揮蹄；太陽出現較突然，沒有完整緩升過程。建議加「same anatomical front hoof waves throughout, other hoof stays down, sun rises gradually a few pixels across frames」。
- **整批色彩／純扁平要求：** 原參考本身含極淡明暗，生成圖仍有奶油色細微色差，部分道具邊緣和顏色也不是只含指定六個精確 RGB。此次沒有全圖限色，避免影響羊的原參考外觀或擅自重畫道具。若六色是逐像素硬限制，需重生／老師指定可用的道具色域整理方式。建議提示加入「props use exact solid palette fills, no outlines, no gradient, no intermediate shades」。

此外，peek 提示詞的「完全滑出」與驗收器禁止空白格相衝突；本次第 6 格保留極少頭耳及前蹄。若要完全消失，應由 Claude 在播放結束後隱藏，或由老師決定未來規格；此次未修改程式或檢查器。

## 生圖提示詞紀錄

使用 spec 的角色／構圖限制及每個 action prompt，明確填入格數；生成器原始尺寸不符合 512 格規格，由整理程式重排。全部要求「單橫排、同一隻羊、透明底、無文字 Logo、無洋紅／粉紫、清晰硬邊」，沒有使用洋紅去背。

| 動作 | 最終提示內容及追加控制 |
|---|---|
| idle | 6 frames；front 3/4, gentle breathing, body rises/falls slightly, leaf sways, fixed feet |
| walk_right | 8 frames；right-facing side view; contact/down/passing/up repeated, alternating legs, ears flop |
| drag | 6 frames；lifted by scruff, legs pendulum left/center/right, round o mouth; no hand/cursor/rope |
| sleep | 6 frames；curled wool ball, curved closed eyes, inhale/exhale; no z/letters because forbidden |
| listen | 6 frames；head tilts toward small green/blue microphone, one ear raised, compact sound arcs |
| think | 8 frames；hold/lift/compare/restack blank papers, then one/two/three dots; final regenerate requires dots horizontally close above tuft, never vertically stacked |
| success | 8 frames；hold/raise/press/lift green stamp, reveal check, crouch/jump/descend/land; final regenerate keeps stamp in front of belly and sparkles close to shoulders |
| warning | 8 frames；neutral/notice/crouch/rise/apex/descend/land/settle, red exclamation pictogram close above head |
| peek | 6 frames；sliver/half/full head/look around/half/sliver from right; fixed head scale, no full body, no blank frame |
| greet | 8 frames；raise hoof/wave/lower/relax, gold circle-and-rays sun, no face on sun |
| overdue | 8 frames；hold/raise calendar, worried mouth, small hop/descend/land/tilt/settle; blank grid and one red circle, no dates/digits |

## check_sprites.py 輸出

執行：`python assets/pet/v3/check_sprites.py --phase 1 --preview`，退出碼 0。

```text
C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\check_sprites.py:80: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
  magenta = sum(1 for r, g, b, a in fr.getdata() if a >= 32 and is_magenta(r, g, b))
[PASS] idle（6 格）
[PASS] walk_right（8 格）
[PASS] drag（6 格）
[PASS] sleep（6 格）
[PASS] listen（6 格）
[PASS] think（8 格）
[PASS] success（8 格）
[WARN] warning（8 格）
    △ 第 3 格角色高度 46%，建議約 75%
    △ 第 7 格角色高度 46%，建議約 75%
[PASS] peek（6 格）
[PASS] greet（8 格）
[PASS] overdue（8 格）
預覽：C:\Users\cona0\Desktop\teacher-dashboard-repo\assets\pet\v3\_preview\overview.png

結果：11/11 通過
```

## 接線與部署

資料契約、權限、部署皆不變；不需要重跑安裝。未 push、未合併、未打 tag。下一步由 Claude 按原交接流程驗收、切格與接線。
