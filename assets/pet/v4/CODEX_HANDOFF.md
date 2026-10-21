# 小綿助 v4 動畫：Codex 交接手冊

> 給 Codex 的工作說明，請整份讀完再動手。
> 分工：**Codex 做「角色骨架＋動作＋渲染腳本」**；接到桌寵程式、觸發時機、播放引擎由 Claude 處理。

## 1. 目標

小綿助是教師工作台的桌面寵物（Python＋Tkinter）。現在的動畫每個動作只有 6～8 格、而且是 AI 逐張生圖，播起來會跳、每格長得不太一樣。

這次要做到**極為流暢**：

- **每秒 30 格**，一個動作 0.5～4 秒。
- **同一隻角色**，每一格都完全一致，不能逐格重畫。
- **任兩個動作之間都能無縫切換**，不會瞬移。

## 2. 做法：骨架動畫（必須）

**不要用 AI 逐格生圖。** 請寫一套「零件拼裝＋關鍵影格補間」的渲染器：

1. 角色拆成零件（每個零件一張透明 PNG），用 `pivots.json` 記每個零件的軸心與父子關係。
2. 每個動作是一份關鍵影格檔（`actions/<動作>.json`）：在第幾格、哪個零件、位移／旋轉／縮放多少、用什麼緩動曲線。
3. `render.py` 逐格計算並合成，輸出 512×512 的 PNG 連續影格。

**角色外表由老師之後決定。** 你先用自己畫的簡單佔位零件（原創圖形即可，例如奶油色圓身體、圓耳朵），把骨架和所有動作做完。老師之後把**同名零件**換成正式美術、調好 `pivots.json`，重跑 `render.py` 就全部換新。

## 3. 檔案結構

```
assets/pet/v4/
  spec.json              ← 動作清單（格數、循環、觸發時機、分段節拍）。不要改
  check_sequences.py     ← 驗收工具。不要改
  rig/
    parts/front/*.png    ← 正面 3/4 零件
    parts/side/*.png     ← 正側面朝右零件（走路、轉身用）
    parts/props/*.png    ← 道具（筆、水杯、月曆…）
    pivots.json          ← 零件軸心、父子關係、圖層順序
    actions/<動作>.json  ← 每個動作的關鍵影格
    render.py            ← 渲染器（只用 Python＋Pillow＋numpy）
    README.md            ← 怎麼換零件、怎麼重渲染
  out/<動作>/<動作>_0001.png …   ← render.py 的輸出（不要 commit，已列入 .gitignore）
  DELIVERY.md            ← 交件說明
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

### 零件清單（名稱固定，外表不限）

- **身體部位**：body、head、ear_l、ear_r、leg_fl、leg_fr、leg_bl、leg_br、tail、top_accessory（頭頂飾品）。正面與側面各一套。
- **表情**：
  - 眼睛：open、half、closed、happy、surprised、worried、sleepy
  - 嘴巴：smile、o、wide、worried、yawn、flat
  - 附加：blush、sweat、zzz_bubble、sparkle
- **道具**：spec.json 每個動作的 `props` 欄位，全部實心、**不可有任何文字、數字、Logo**。

## 4. 動畫原則（每個動作都要做到）

- **緩動**：不准用等速。開始 ease-out、結束 ease-in，來回用 ease-in-out。
- **預備動作**：跳、揮手、舉東西之前先反方向縮一下，2～6 格。
- **跟隨與重疊**：耳朵、尾巴、頭頂飾品、毛比身體晚 2～4 格才跟上，停下時多晃一下再停。
- **擠壓伸展**：最多 10%，而且要保持體積：橫向變寬時縱向等比變矮。
- **弧線**：手、頭、跳躍的軌跡走弧線，不走直線。
- **永遠在呼吸**：任何停住的姿勢都保留 ±1.5% 的呼吸起伏，不能完全靜止。
- **眼神先動**：轉頭時眼睛先到，頭晚 2 格。

## 5. 技術規格

| 項目 | 規格 |
|---|---|
| 畫布 | 512×512，RGBA 透明背景 |
| 影格率 | 30 fps；格數照 spec.json |
| 角色大小 | 站立時身高約 336px |
| 位置 | 水平置中 x=256，腳底 y=488 |
| 邊緣 | 保留抗鋸齒（渲染時用 2 倍超取樣再縮小） |
| 顏色 | 不可用洋紅色或粉紫色（#FF00FF 附近），桌寵視窗會把它挖空 |
| 基準姿勢 | spec.json 的 `neutral_pose`，也就是 idle 第 1 格 |
| 單次動作 | 第 1 格與最後一格都要等於基準姿勢（例外列在 check_sequences.py） |
| 循環動作 | 最後一格是第 1 格的「前一步」，不要重複第 1 格 |
| 走路 | 前腳每步前進 31px 且著地時不滑步，配合桌寵移動速度 |
| 朝左 | 走路、轉身、探頭朝左的版本由 Claude 鏡像，不用做 |

## 6. 自我檢查（交件前必做）

```bash
pip install pillow numpy
python assets/pet/v4/rig/render.py
python assets/pet/v4/check_sequences.py --preview
```

- 每一項都要是 **PASS** 或 **WARN**，不能有 **FAIL**。WARN 要在交件說明裡解釋。
- 打開 `assets/pet/v4/_preview/` 的 gif 用眼睛看：
  - 有沒有抖動、滑步、瞬移。
  - 循環接得順不順。
  - 道具上有沒有字。

## 7. 交件方式

1. 開分支 `codex/pet-v4-rig`。
2. 只改 `assets/pet/v4/` 底下，`out/` 與 `_preview/` 不要 commit。
3. 寫 `assets/pet/v4/DELIVERY.md`，內容包括：
   - 每個動作一行：格數、檢查結果、備註。
   - 換零件的步驟。
   - check_sequences.py 的完整輸出。
   - 你覺得哪些動作還可以更好。
4. commit 訊息寫：`小綿助 v4 骨架動畫（Codex 交件）`。
5. 不要 push 到 main、不要合併、不要打 tag。

## 8. 不可以做的事

- 不要用 AI 逐格生圖，也不要逐格手繪；每一格都必須由骨架計算出來。
- 不要改任何程式：`desktop_pet_*.py`、`Morning.html`、`Index.html`、測試，以及 `assets/pet/frames/` 都不能動。
- 不要改 `spec.json` 和 `check_sequences.py`。覺得規格不合理，寫進交件說明。
- 不要使用第三方角色、素材、字型或圖示；佔位零件請自己畫。
- 不要放任何金鑰或個資。

## 9. 交件之後（Claude 做，給你參考）

- **播放引擎升級**：
  - 改用 Windows 分層視窗，支援半透明抗鋸齒邊緣，不再有洋紅鋸齒。
  - 播放提高到 30fps。
  - 用到的動作才載入，避免吃記憶體。
- **狀態機**：每個動作從基準姿勢進、回基準姿勢出。睡覺走 sleep_in、sleep、sleep_out；拖曳走 drag_pick、drag、drop；走路換方向插入 turn。
- **接上觸發時機**：依 spec.json 的 `trigger` 欄位，並重新打包小綿助安裝檔。
