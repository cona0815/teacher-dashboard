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
