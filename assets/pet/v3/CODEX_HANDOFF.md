# 小綿助 v3 動作圖：Codex 交接手冊

> 給 Codex 的工作說明。請整份讀完再動手。
> 分工：**Codex 只負責做圖**。切格子、接到桌寵程式、觸發條件，全部由 Claude 驗收後處理。

## 1. 背景

小綿助是教師工作台的桌面寵物，一隻小綿羊，用 Python＋Tkinter 寫成。
老師已經用 ChatGPT 生出想要的新畫風，要把羊換成這個風格，並補上新動作。
新畫風是扁平向量、顏文字臉、奶油色、頭上有綠葉。

每個動作是一張「橫排連續動作圖」（sprite sheet）。桌寵會把它切成一格一格輪流播放。

## 2. 你會拿到的東西

| 位置 | 內容 |
|---|---|
| `assets/pet/v3/reference/` | 老師放的角色參考圖（新畫風的羊）。**以它為準，不要重新設計角色。** |
| `assets/pet/v3/spec.json` | 21 個動作的規格：名稱、格數、批次、提示詞、播放速度、系統觸發時機 |
| `assets/pet/v3/raw/`（可能有） | 老師用 ChatGPT 生好的原始圖，檔名是 `<動作名>.png`，尺寸與背景不一定合格 |
| `assets/pet/v3/check_sprites.py` | 驗收工具。交件前必須跑過 |

`reference/` 是空的時，先看對話附件。老師有附圖，就存成 `reference/sheep_ref.png` 再開始。都沒有就**停下來**，請老師先給參考圖，不要自己畫一隻羊。

## 3. 要交的東西

每個動作一張 PNG，放在 `assets/pet/v3/sheets/<動作名>.png`。

- **排列**：一橫排 N 格，N 照 `spec.json` 的 `frames`。
- **尺寸**：每格 512×512，整張寬 N×512、高 512。格子之間沒有間隙、沒有框線。
- **背景**：RGBA 真透明。不要白底、不要棋盤格、不要地面陰影。
- **角色**：每格同樣大小，約佔格子高度 75%，置中，腳底踩在 y≈488 的同一條線上。
  - 跳躍動作（`hop: true`）可以騰空，但起跳格和落地格要踩回這條線。
  - `free_scale: true` 的動作（drag、sleep、stretch、peek）可以變形或縮成一團，不受大小與腳底限制。
  - `peek` 的 `free_center: true`：只露頭，可以貼齊右邊。
- **邊緣**：銳利的硬邊。不要模糊、光暈、半透明陰影。桌寵會把 alpha<32 的像素直接砍掉，半透明邊會變鋸齒。
- **顏色**：
  - 絕對不要用洋紅色或粉紫色（#FF00FF 附近）。桌寵視窗用洋紅色當透明色，那些地方會被挖空。
  - 道具只能用這六色：深綠 #1F514A、淺綠 #7FB89A、金黃 #D8A33A、番茄紅 #D9573F、淡藍 #A9CFE8、白色。
- **禁止**：任何文字、字母、數字、Logo，包括看板、便利貼、行事曆上面也不行。LINE 泡泡不能出現 LINE 的 Logo。

### 批次

- **第一批（phase 1，先交）**：idle、walk_right、drag、sleep、listen、think、success、warning、peek、greet、overdue，共 11 個。
- **第二批（phase 2）**：idle_blink、idle_grade、mail、drink、stretch、medicine、focus、watch、note、sign，共 10 個。
- **不用做 walk_left**：Claude 會把 walk_right 左右鏡像。

## 4. 做法

依你的環境選一條路。

### A. 你能生圖

1. 對每個動作，把 `spec.json` 的 `common_prompt` 裡的 `{frames}` 和 `{action_prompt}` 換成該動作的 `frames` 與 `prompt`。
2. 附上 `reference/` 的參考圖一起生成。
3. 生出來的圖幾乎一定不合格，要照 B 的步驟整理成規格。

### B. 整理老師給的原始圖（`raw/`）

寫一支 `assets/pet/v3/normalize_raw.py`（Python＋Pillow），把 `raw/<名>.png` 轉成 `sheets/<名>.png`。

1. **去背**：用邊緣連通的背景填色，不要用全圖色鍵，免得挖掉羊身上的白色。去完後把 alpha 二值化成 0 或 255。
2. **切格**：依透明欄位或等寬切成 N 格。格數跟規格不同就回報，**不要自己補格或刪格**。
3. **統一大小**：同一個動作的每一格用同一個縮放比例，讓角色約佔 75% 高。
4. **對齊**：水平置中，腳底對到 y=488。
5. **清色**：把洋紅色與粉紫色雜點改成透明或最接近的鄰色。
6. 輸出成 N×512 乘 512 的 RGBA PNG。

原始圖本身畫錯的，照樣整理但不要硬修，寫進交件說明。畫錯的例子：角色變了樣、出現文字、動作不對。

## 5. 自我檢查（交件前必做）

```bash
pip install pillow
python assets/pet/v3/check_sprites.py --phase 1 --preview
```

- 本批每一項都要是 **PASS** 或 **WARN**，不能有 **FAIL**。
- 有 WARN 的，要在交件說明解釋原因。
- 打開 `assets/pet/v3/_preview/overview.png` 和各個 gif，用眼睛確認：
  - 每格都是同一隻羊。
  - 動作看得懂、播起來不抖。
  - 沒有字。
- 第二批交件時用 `--phase 2`。

## 6. 交件方式

1. 開分支 `codex/pet-sprites-v3-phase1`（第二批用 `-phase2`）。
2. 只加入或修改 `assets/pet/v3/` 底下這些東西：
   - `sheets/*.png`
   - `raw/`，老師放的原圖，照原樣保留
   - `normalize_raw.py`
   - `DELIVERY.md`
3. 寫 `assets/pet/v3/DELIVERY.md`：

```markdown
# 交件說明：phase 1（日期）

| 動作 | 格數 | 檢查結果 | 來源（自生／raw） | 備註 |
|---|---|---|---|---|
| idle | 6 | PASS | raw | |
| ... | | | | |

## 需要老師重生的圖
- （哪一張、哪裡不對、建議怎麼改提示詞）

## check_sprites.py 輸出
（貼完整輸出）
```

4. commit 訊息：`小綿助 v3 動作圖 phase 1（Codex 交件）`。
5. **不要 push 到 main、不要合併、不要打 tag。**

## 7. 不可以做的事

- 不要改任何程式，包括 `desktop_pet_*.py`、`FRAME_COUNTS`、`Index.html` 與測試檔。接線是 Claude 的工作。
- 不要動 `assets/pet/frames/` 和 `assets/pet/*.webp`，那是目前正在用的舊版圖。
- 不要改 `spec.json` 和 `check_sprites.py`。覺得規格有問題，寫進交件說明。
- 不要使用第三方素材，包括 DeskCat 或網路上的圖、字型、圖示。DeskCat 沒有授權條款，只能參考點子。
- 不要放 API 金鑰、token 或個人資料進 repo。

## 8. 交件之後（Claude 做，給你參考）

1. 重跑 `check_sprites.py`，驗收並合併。
2. 把 sheets 切成 `assets/pet/frames/pet_<動作>/` 的單格圖，並鏡像出 walk_left。
3. 更新 `FRAME_COUNTS`、播放速度，並把新動作接到觸發時機。觸發時機見 `spec.json` 的 `trigger`，例如逾期、LINE 新訊息、喝水、服藥、專注、大屏提示。
4. 重打包小綿助 EXE。
