"""把 v3 動作圖（sheets/*.png）裝進桌寵：切格、統一角色大小、鏡像出 walk_left／peek_left。

用法（專案根目錄）：
    python assets/pet/v3/install_frames.py            # 裝好已驗收的動作
    python assets/pet/v3/install_frames.py --dry-run  # 只量測、不寫檔

為什麼要統一大小：每張 sheet 在自己的 512 格裡已經置中對齊，但不同動作的
縮放比例不同（頭上有太陽、驚嘆號的動作會被整組縮小），直接播放時切換動作
會忽大忽小。這裡把每個動作縮放到同一個「身高」：
- 站姿動作：量奶油色身體（頭頂到身體底）的高度。眼睛大小在每次生成間
  會差 10～15%，用眼睛當尺會讓 idle 忽大忽小，所以站姿一律量身體。
- 會變形的動作（spec 的 free_scale：drag、sleep、stretch、peek）：身體被拉長
  或縮成一團，改用眼睛直徑（閉眼時用頭上葉子面積）換算成等效身高。

輸出：assets/pet/frames/pet_<動作>/pet_<動作>_NN.png（512x512，alpha 只有 0／255）。
由 Claude 維護；Codex 不需要執行。
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
SHEETS = HERE / "sheets"
FRAMES = REPO / "assets" / "pet" / "frames"
SIZE = 512
BASE_Y = SPEC["baseline_y"]
MARGIN = 6
MEASURE = 256  # 量測時先縮到 256 加速
# 左右鏡像：往左走、從左邊緣探頭
MIRRORS = {"walk_right": "walk_left", "peek": "peek_left"}


def _components(mask: bytearray, w: int, h: int):
    seen = bytearray(w * h)
    for i in range(w * h):
        if not mask[i] or seen[i]:
            continue
        q = deque([i])
        seen[i] = 1
        n, x0, y0, x1, y1 = 0, w, h, 0, 0
        while q:
            j = q.popleft()
            n += 1
            x, y = j % w, j // w
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    k = ny * w + nx
                    if mask[k] and not seen[k]:
                        seen[k] = 1
                        q.append(k)
        yield n, x0, y0, x1, y1


def _mask(img: Image.Image, test) -> bytearray:
    w, h = img.size
    data = img.load()
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if test(*data[x, y]):
                out[y * w + x] = 1
    return out


def eye_diameters(frame: Image.Image) -> list[float]:
    """眼睛＝近黑、接近正圓、實心的小塊。回傳 512 尺度下的直徑。"""
    small = frame.resize((MEASURE, MEASURE), Image.NEAREST)
    mask = _mask(small, lambda r, g, b, a: a > 128 and r < 70 and g < 70 and b < 70)
    result = []
    for n, x0, y0, x1, y1 in _components(mask, MEASURE, MEASURE):
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if n > 20 and 0.7 < bw / bh < 1.4 and n / (bw * bh) > 0.6:
            result.append((bw + bh) / 2 * SIZE / MEASURE)
    return result


def leaf_size(frame: Image.Image) -> float | None:
    """頭上葉子＝最上方的一塊中綠色；回傳 512 尺度下的 sqrt(面積)。"""
    small = frame.resize((MEASURE, MEASURE), Image.NEAREST)
    mask = _mask(small, lambda r, g, b, a: a > 128 and g > r + 25 and g > b + 10 and 110 < g < 200 and r < 140)
    comps = [c for c in _components(mask, MEASURE, MEASURE) if c[0] > 60]
    if not comps:
        return None
    return min(comps, key=lambda c: c[2])[0] ** 0.5 * SIZE / MEASURE


def load_frames(action: dict) -> list[Image.Image]:
    sheet = Image.open(SHEETS / f"{action['name']}.png").convert("RGBA")
    return [sheet.crop((i * SIZE, 0, (i + 1) * SIZE, SIZE)) for i in range(action["frames"])]


def body_height(frames: list[Image.Image]) -> float | None:
    """奶油色身體的高度（排除葉子、臉、道具、白紙）。取 75 百分位，偏向站直的格子。"""
    heights = []
    for fr in frames:
        small = fr.resize((MEASURE, MEASURE), Image.NEAREST)
        px = small.load()
        rows = [y for y in range(MEASURE) if any(
            (lambda r, g, b, a: a > 128 and r > 215 and g > 200 and b > 180 and min(r, g, b) < 246 and r - b > 8)(*px[x, y])
            for x in range(MEASURE))]
        if rows:
            heights.append((rows[-1] - rows[0]) * SIZE / MEASURE)
    if not heights:
        return None
    heights.sort()
    return heights[min(len(heights) - 1, int(len(heights) * 0.75))]


def measure(frames: list[Image.Image]) -> tuple[float | None, float | None]:
    eyes = [d for fr in frames for d in eye_diameters(fr)]
    leaves = [v for v in (leaf_size(fr) for fr in frames) if v]
    return (statistics.median(eyes) if eyes else None, statistics.median(leaves) if leaves else None)


def union_bbox(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [fr.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox() for fr in frames]
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def anchor_for(action: dict, box) -> tuple[float, float]:
    """縮放時固定不動的點。一般動作固定腳底中心；peek 固定右緣；drag 固定整組中心。"""
    if action.get("free_center"):
        return (SIZE, BASE_Y)
    if action["name"] == "drag":
        return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    return (SIZE / 2, BASE_Y)


def max_fit_scale(action: dict, box) -> float:
    ax, ay = anchor_for(action, box)
    limits = []
    if action["name"] == "drag":  # drag 之後會平移置中，只受整體寬高限制
        limits = [(SIZE - 2 * MARGIN) / (box[2] - box[0]), (SIZE - 2 * MARGIN) / (box[3] - box[1])]
    else:
        if box[1] < ay:
            limits.append((ay - MARGIN) / (ay - box[1]))
        if box[0] < ax:
            limits.append((ax - MARGIN) / (ax - box[0]))
        if box[2] > ax:
            limits.append((SIZE - MARGIN - ax) / (box[2] - ax))
    return min(limits) if limits else 9.0


def transform(frame: Image.Image, scale: float, anchor, shift=(0, 0)) -> Image.Image:
    ax, ay = anchor
    w = max(1, round(SIZE * scale))
    scaled = frame.resize((w, w), Image.Resampling.LANCZOS)
    ox = round(ax - ax * scale + shift[0])
    oy = round(ay - ay * scale + shift[1])
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(scaled, (ox, oy), scaled)
    # 桌寵視窗用洋紅當透明色：alpha 二值化，透明像素 RGB 清零，避免粉紅殘邊。
    px = canvas.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--target-body", type=float, default=336.0, help="統一的身高（px，512 尺度）。預設 336＝約佔格子 66%%，桌寵 PET_SIZE 184 依此設定")
    args = ap.parse_args()

    actions = [a for a in SPEC["actions"] if (SHEETS / f"{a['name']}.png").exists()]
    info = {}
    for a in actions:
        frames = load_frames(a)
        eye, leaf = measure(frames)
        body = None if a.get("free_scale") else body_height(frames)
        info[a["name"]] = {"action": a, "frames": frames, "eye": eye, "leaf": leaf, "body": body, "box": union_bbox(frames)}

    # 站姿動作的「身高／眼睛」「身高／葉子」比例，用來換算會變形的動作
    standing = [v for v in info.values() if v["body"]]
    body_per_eye = statistics.median([v["body"] / v["eye"] for v in standing if v["eye"]] or [17.0])
    body_per_leaf = statistics.median([v["body"] / v["leaf"] for v in standing if v["leaf"]] or [8.5])
    for v in info.values():
        if v["body"]:
            v["size"], v["ruler"] = v["body"], "身體"
        elif v["eye"]:
            v["size"], v["ruler"] = v["eye"] * body_per_eye, "眼睛"
        elif v["leaf"]:
            v["size"], v["ruler"] = v["leaf"] * body_per_leaf, "葉子"
        else:
            v["size"], v["ruler"] = None, "無"
        v["fit"] = max_fit_scale(v["action"], v["box"])

    target = args.target_body
    print(f"身高/眼睛 {body_per_eye:.1f}、身高/葉子 {body_per_leaf:.2f}；統一身高 {target:.0f}px（512 尺度）")

    for name, v in info.items():
        a = v["action"]
        scale = target / v["size"] if v["size"] else 1.0
        capped = scale > v["fit"] + 1e-6
        scale = min(scale, v["fit"])
        anchor = anchor_for(a, v["box"])
        shift = (0, 0)
        if name == "drag":
            cx, cy = (v["box"][0] + v["box"][2]) / 2, (v["box"][1] + v["box"][3]) / 2
            shift = (SIZE / 2 - cx, SIZE / 2 - cy)
        final = (v["size"] or 0) * scale
        print(f"  {name:11s} 用{v['ruler']}量 {v['size'] and round(v['size'])}px → 縮放 {scale:.3f} → {final:.0f}px{'（受格子限制）' if capped else ''}")
        if args.dry_run:
            continue
        out = FRAMES / f"pet_{name}"
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        done = [transform(fr, scale, anchor, shift) for fr in v["frames"]]
        for i, fr in enumerate(done, 1):
            fr.save(out / f"pet_{name}_{i:02d}.png", optimize=True)
        mirror = MIRRORS.get(name)
        if mirror:
            left = FRAMES / f"pet_{mirror}"
            if left.exists():
                shutil.rmtree(left)
            left.mkdir(parents=True)
            for i, fr in enumerate(done, 1):
                fr.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(left / f"pet_{mirror}_{i:02d}.png", optimize=True)
    if not args.dry_run:
        print(f"已輸出到 {FRAMES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
