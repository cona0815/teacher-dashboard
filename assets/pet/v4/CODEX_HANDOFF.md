# 小綿助 v4 動畫：Codex 交接手冊

> 給 Codex 的工作說明，請整份讀完再動手。
> 分工：**Codex 做「六個角色的骨架＋動作＋渲染腳本」**；接到桌寵程式、行為大腦、觸發時機、播放引擎由 Claude 處理。

## 1. 目標

小綿助是教師工作台的桌面寵物（Python＋Tkinter）。現在的動畫每個動作只有 6～8 格，而且是 AI 逐張生圖，播起來會跳、每格長得不太一樣。

這次要做到三件事：

- **極為流暢**：每秒 30 格，一個動作 0.5～4 秒。
- **同一隻角色每一格都完全一致**：不能逐格重畫。任兩個動作之間都能無縫切換，不會瞬移。
- **放在桌面上像活的**：一直在呼吸、會眨眼、眼睛跟著游標、被摸會撒嬌、無聊會打哈欠。詳見第 5 節。

老師可以在**六個角色**之間切換，六個角色做的是同一套動作：

| id | 角色 | 身形 | 基準姿勢 | 個性與動作風格 |
|---|---|---|---|---|
| sheep | 綿羊（小綿助本尊） | 四足 | 四腳站立 | 溫和愛睏；動作柔軟、回彈大 |
| tabby | 灰白虎斑貓 | 四足 | 端坐 | 好奇愛乾淨；反應最快，鬍鬚會跟著晃 |
| blackcat | 黑貓 | 四足 | 端坐、尾巴上捲 | 高冷；振幅小、最滑順，尾巴尖獨立捲動 |
| samoyed | 薩摩耶 | 四足 | 四腳站立、微笑 | 熱情；尾巴一直慢搖，蓬毛有次級晃動 |
| shiba | 柴犬 | 四足 | 四腳站立 | 活潑倔強；最有彈性，捲尾像彈簧 |
| robot | 小機器人 | 雙足 | 站立、雙手扠腰 | 認真；機械感的起停與小過衝，表情全在螢幕上 |

完整的角色設定在 `spec.json` 的 `characters`。

## 2. 做法：骨架動畫（必須）

**不要用 AI 逐格生圖。** 請寫一套「零件拼裝＋關鍵影格補間」的渲染器：

1. 每個角色拆成零件（每個零件一張透明 PNG），用該角色的 `pivots.json` 記每個零件的軸心與父子關係。
2. **動作的關鍵影格六個角色共用**（`rig/common/actions/<動作>.json`），寫的是語意上的零件（頭、耳朵、前腳…）。
3. 角色不合的地方放 `rig/<角色>/overrides/<動作>.json` 覆寫。例如機器人用雙腳走路、貓的 groom 舔腳掌。
4. 角色個性用一份 `rig/<角色>/style.json` 調整：振幅倍率、次級動作延遲、過衝量。
5. `render.py` 逐格計算並合成，輸出 512×512 的 PNG 連續影格。

### 角色外表

老師提供了六個角色的**參考圖**，請在 Codex 對話裡看附圖。

- **參考圖只當風格參考**：照著它的造型、配色、比例，**自己重新畫**成可動的零件。
- 不要直接裁切參考圖當零件，參考圖也不要 commit 進 repo（這是公開 repo）。
- 老師之後如果要換外表，只要把同名零件換掉、調好 `pivots.json`，重跑 `render.py`，所有動作就換新。

## 3. 檔案結構

```
assets/pet/v4/
  spec.json                 ← 角色、動作清單（格數、循環、觸發、分段節拍、變體）。不要改
  check_sequences.py        ← 驗收工具。不要改
  rig/
    common/
      actions/<動作>.json    ← 共用關鍵影格
      props/*.png            ← 道具（筆、水杯、月曆…），六個角色共用
    <角色>/
      parts/front/*.png      ← 正面 3/4 零件
      parts/side/*.png       ← 正側面朝右零件（走路、跑步、轉身用）
      pivots.json            ← 零件軸心、父子關係、圖層順序
      style.json             ← 個性參數
      overrides/<動作>.json  ← 這個角色專屬的關鍵影格（選用）
    render.py                ← 渲染器（只用 Python＋Pillow＋numpy）
    README.md                ← 怎麼換零件、怎麼新增角色、怎麼重渲染
  out/<角色>/<動作>/<動作>_0001.png …   ← 輸出（不要 commit，已列入 .gitignore）
  out/<角色>/<動作>/meta.json           ← 每格資料（見下面）
  DELIVERY.md               ← 交件說明
```

### pivots.json 格式

```json
{
  "front": {
    "body":  { "image": "front/body.png",  "pivot": [256, 420], "parent": null,   "z": 10 },
    "head":  { "image": "front/head.png",  "pivot": [256, 300], "parent": "body", "z": 20 },
    "ear_l": { "image": "front/ear_l.png", "pivot": [200, 250], "parent": "head", "z": 15 }
  },
  "faces": { "eyes": { "open": "front/eyes_open.png", "closed": "front/eyes_closed.png" } }
}
```

座標以 512×512 畫布為準。零件可以用 1024px 繪製，渲染時縮放。

### meta.json（每個動作一份）

```json
{ "frames": [ { "head": [256, 210], "feet": [true, true, true, true], "bbox": [120, 150, 390, 488] } ] }
```

- `head`：頭頂中心，引擎用來放對話框和愛心。
- `feet`：四隻腳（機器人是兩手兩腳）有沒有著地，引擎用來畫影子、算走路位移。
- `bbox`：角色外框，引擎用來判斷滑鼠點到頭還是身體。

### 零件清單（名稱固定，外表照參考圖）

- **必備**：body、head、ear_l、ear_r、leg_fl、leg_fr、leg_bl、leg_br。正面與側面各一套。
- **選用**：tail、tail_tip、top_accessory、whiskers、fluff_chest、fluff_back、tongue。
- **機器人對應**：
  - leg_fl／leg_fr 是左右手臂，leg_bl／leg_br 是左右腿。
  - ear_l／ear_r 是耳機，top_accessory 是天線。
  - 沒有 tail。
- **表情**：
  - 眼睛：open、half、closed、happy、surprised、worried、sleepy
  - 嘴巴：smile、o、wide、worried、yawn、flat
  - 附加：blush、sweat、zzz_bubble、sparkle、heart
  - 機器人的眼睛和嘴巴是螢幕上的發光圖形，螢幕本身不動。
- **道具**：spec.json 每個動作的 `props` 欄位。全部實心，**不可有任何文字、數字、Logo**。

## 4. 動畫原則（每個動作都要做到）

- **緩動**：不准用等速。開始 ease-out、結束 ease-in，來回用 ease-in-out。
- **預備動作**：跳、揮手、舉東西之前先反方向縮一下，2～6 格。
- **跟隨與重疊**：耳朵、尾巴、頭頂飾品、毛、鬍鬚比身體晚 2～4 格才跟上，停下時多晃一下再停。
- **擠壓伸展**：最多 10%，而且要保持體積：橫向變寬時縱向等比變矮。
- **弧線**：手、頭、跳躍的軌跡走弧線，不走直線。
- **眼神先動**：轉頭時眼睛先到，頭晚 2 格。

## 5. 生命感（這次的重點）

`spec.json` 的 `alive_rules` 是硬規定：

- **永遠在呼吸**：任何停住的姿勢都有 ±1.5% 起伏，沒有完全靜止的格子。
- **會眨眼**：超過 2 秒的動作裡至少眨眼一次，刻意閉眼的段落除外。
- **有重量**：每一格都看得出重心在哪隻腳；跳之前先蹲，落地一定擠壓。
- **不對稱**：兩隻耳朵、兩隻腳不要同時同幅度動，至少錯開 1～2 格。
- **有個性**：同一個動作，六個角色依 `motion_style` 調整振幅與節奏。
  - 黑貓慢而小。
  - 柴犬彈。
  - 機器人有機械過衝。
- **不畫影子**：影子由引擎畫。

另外有 21 個專門讓牠「像活的」的動作（spec.json 的「生命感」與「移動」群組）：

- **gaze 是姿勢表**，不是播放的動畫：
  - 25 格排成 5×5 的看方向，第 13 格是正中。
  - 引擎會依游標方向一格一格移過去，讓眼睛一直跟著滑鼠。
  - 相鄰兩格只能差一小步。
- **對滑鼠的反應**：notice（游標靠近）、startle（游標衝過來）、pet（被摸）、poke_head、poke_belly（被點）。
- **自己找事做**：sit_down → sit → stand_up、scratch_ear、groom、yawn、sneeze、bored、hop、tail_chase（彩蛋）。
- **在桌面上移動**：
  - run_right：每循環前進 62px，不滑步。
  - fall → land：被甩出去或掉下視窗。
  - perch：坐在別的視窗頂端，腳垂在邊緣下，邊緣線 y=400。
- **陪老師工作**：watch_typing（老師打字時跟著看）。

有 `variants` 的動作，照變體描述做該角色的版本（放在 `overrides/`）。

## 6. 技術規格

| 項目 | 規格 |
|---|---|
| 畫布 | 512×512，RGBA 透明背景 |
| 影格率 | 30 fps；格數照 spec.json |
| 角色大小 | 站立時身高約 336px（端坐的貓、機器人也一樣高） |
| 位置 | 水平置中 x=256，腳底 y=488（perch 的邊緣線是 y=400） |
| 邊緣 | 保留抗鋸齒（渲染時用 2 倍超取樣再縮小） |
| 顏色 | 不可用洋紅色或粉紫色（#FF00FF 附近），舊版桌寵視窗會把它挖空 |
| 基準姿勢 | 每個角色自己的 idle 第 1 格 |
| 單次動作 | 第 1 格與最後一格都要等於基準姿勢；有 `starts_from`／`ends_into` 的改成等於那個動作的第 1 格 |
| 循環動作 | 最後一格是第 1 格的「前一步」，不要重複第 1 格 |
| 走路 | 前腳每步前進 31px 且著地時不滑步，配合桌寵移動速度；跑步每循環 62px |
| 朝左 | 走路、跑步、轉身、探頭朝左的版本由 Claude 鏡像，不用做 |

## 7. 分兩批交件

1. **第一批**：
   - 渲染器，加上共用關鍵影格的全部 49 個動作。
   - 先做 **sheep** 和 **robot** 兩個角色，一個四足、一個雙足，確定架構撐得住兩種身形。
2. **第二批**：tabby、blackcat、samoyed、shiba。
   - 主要是畫零件、寫 style.json 和 overrides。
   - 動作不用重寫。

## 8. 自我檢查（交件前必做）

```bash
pip install pillow numpy
python assets/pet/v4/rig/render.py --character all
python assets/pet/v4/check_sequences.py --preview
```

- 每一項都要是 **PASS** 或 **WARN**，不能有 **FAIL**。WARN 要在交件說明裡解釋。
- 打開 `assets/pet/v4/_preview/<角色>/` 的 gif 用眼睛看：
  - 有沒有抖動、滑步、瞬移。
  - 循環接得順不順。
  - 道具上有沒有字。
  - 六個角色看起來是不是同一個「家族」的品質。

## 9. 交件方式

1. 開分支 `codex/pet-v4-rig`。
2. 只改 `assets/pet/v4/` 底下，`out/` 與 `_preview/` 不要 commit。
3. 寫 `assets/pet/v4/DELIVERY.md`，內容包括：
   - 每個角色、每個動作一行：格數、檢查結果、備註。
   - 換零件與新增角色的步驟。
   - check_sequences.py 的完整輸出。
   - 你覺得哪些動作還可以更好。
4. commit 訊息寫：`小綿助 v4 骨架動畫（Codex 交件，第 N 批）`。
5. 不要 push 到 main、不要合併、不要打 tag。

## 10. 不可以做的事

- 不要用 AI 逐格生圖，也不要逐格手繪；每一格都必須由骨架計算出來。
- 不要改任何程式：`desktop_pet_*.py`、`Morning.html`、`Index.html`、測試，以及 `assets/pet/frames/` 都不能動。
- 不要改 `spec.json` 和 `check_sequences.py`。覺得規格不合理，寫進交件說明。
- 不要直接裁切或描摹參考圖，也不要使用第三方角色、素材、字型或圖示；零件請照參考圖的風格自己畫。
- 不要放任何金鑰或個資。

## 11. 交件之後（Claude 做，給你參考）

- **播放引擎**：
  - Windows 分層視窗：半透明抗鋸齒邊緣、腳下柔和影子。
  - 30fps 播放；用到的動作才載入。
- **狀態機**：
  - 每個動作從基準姿勢進、回基準姿勢出。
  - 睡覺走 sleep_in → sleep → sleep_out；拖曳走 drag_pick → drag → drop；坐下走 sit_down → sit → stand_up；掉落走 fall → land；換方向插入 turn。
- **行為大腦**：
  - 精力、無聊、親密三個數值決定下一個動作，不是固定輪播；同一個小動作不連續出現。
  - 眼睛跟游標（gaze）。
  - 被摸、被點、被甩出去有物理慣性。
  - 會走到別的視窗頂端坐著（perch）。
  - 依時段變化：早上伸懶腰、午後打哈欠、下班睡覺。
- **選角色**：設定裡切換六個角色，記住老師的選擇，並重新打包小綿助安裝檔。
