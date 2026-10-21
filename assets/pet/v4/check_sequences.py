"""小綿助 v4 動畫驗收：檢查 render 出來的連續影格是否「流暢、可無縫切換」。

用法（專案根目錄）：
    python assets/pet/v4/check_sequences.py                 # 檢查全部
    python assets/pet/v4/check_sequences.py --only idle walk_right
    python assets/pet/v4/check_sequences.py --preview       # 另外輸出 _preview/*.gif 與 overview.png

影格位置：assets/pet/v4/out/<動作>/<動作>_0001.png（從 0001 起連號，512×512 RGBA）。
全部 PASS 才算合格；WARN 要在交件說明裡解釋。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover
    sys.exit("需要 Pillow：pip install pillow")

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
OUT = HERE / "out"
PREVIEW = HERE / "_preview"
SIZE, BASE = SPEC["canvas"], SPEC["baseline_y"]
SMALL = 128

# 單次動作開頭／結尾要回到基準姿勢（idle 第 1 格），以下是例外
NO_NEUTRAL_START = {"drop", "sleep_out", "peek", "turn", "walk_right"}
NO_NEUTRAL_END = {"drag_pick", "sleep_in", "peek", "turn"}
NEUTRAL_LIMIT = 6.0      # 與基準姿勢的平均差（0–255）上限
POP_RATIO = 5.0          # 相鄰格差超過「中位數 × 5」視為跳格
POP_FLOOR = 4.0          # 但差值本身要大於這個才算（避免整段靜止時誤判）
SEAM_RATIO = 2.0         # 循環接縫差 ≤ 一般相鄰格差 × 2
BASE_TOL = 5             # 腳底線容許誤差（px）


def frames_of(name: str) -> list[Path]:
    return sorted((OUT / name).glob(f"{name}_*.png"))


def small(img: Image.Image) -> Image.Image:
    return img.resize((SMALL, SMALL), Image.Resampling.BILINEAR)


def diff(a: Image.Image, b: Image.Image) -> float:
    d = ImageChops.difference(a, b)
    hist = d.histogram()
    total = sum(i * c for band in range(4) for i, c in enumerate(hist[band * 256:(band + 1) * 256]))
    return total / (SMALL * SMALL * 4)


def bottom(img: Image.Image) -> int | None:
    box = img.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()
    return box[3] if box else None


def magenta_count(img: Image.Image) -> int:
    return sum(1 for r, g, b, a in img.getdata() if a >= 128 and r >= 190 and b >= 190 and g <= 165 and abs(r - b) <= 85)


def check(action: dict, neutral: Image.Image | None):
    name, n = action["name"], action["frames"]
    errors, warns = [], []
    files = frames_of(name)
    if len(files) != n:
        return [f"格數 {len(files)}，規格是 {n}（{n / SPEC['fps']:.1f} 秒 @ {SPEC['fps']}fps）"], warns, []
    imgs = []
    for i, f in enumerate(files, 1):
        img = Image.open(f)
        if img.size != (SIZE, SIZE):
            errors.append(f"第 {i} 格尺寸 {img.size}，應為 {SIZE}×{SIZE}"); return errors, warns, []
        if img.mode != "RGBA":
            errors.append(f"第 {i} 格不是 RGBA（要透明背景）"); return errors, warns, []
        imgs.append(img)
    smalls = [small(im) for im in imgs]

    # 洋紅色會被桌寵視窗當成透明色挖空
    for i in (0, len(imgs) // 2, len(imgs) - 1):
        if magenta_count(small(imgs[i])) > 6:
            errors.append(f"第 {i + 1} 格有洋紅色，桌寵視窗會把它挖空")

    # 邊緣要有抗鋸齒（半透明像素），才不會鋸齒狀
    alpha_hist = imgs[0].getchannel("A").histogram()
    if sum(alpha_hist[16:240]) < 200:
        warns.append("邊緣幾乎沒有半透明像素，縮小顯示時會有鋸齒；請保留抗鋸齒")

    # 流暢度：相鄰格差的中位數與最大值
    steps = [diff(smalls[i], smalls[i + 1]) for i in range(len(smalls) - 1)]
    med = statistics.median(steps) if steps else 0
    for i, d in enumerate(steps, 1):
        if d > max(POP_FLOOR, med * POP_RATIO):
            errors.append(f"第 {i}→{i + 1} 格跳動太大（{d:.1f}，一般 {med:.1f}），中間缺補間格")
    if steps and max(steps) < .05:
        errors.append("整段幾乎沒有變化，沒有動作")

    # 循環接縫
    if action.get("loop"):
        seam = diff(smalls[-1], smalls[0])
        if seam > max(POP_FLOOR, med * SEAM_RATIO):
            errors.append(f"最後一格接回第一格會頓（接縫差 {seam:.1f}，一般 {med:.1f}）；最後一格不要重複第一格，要是第一格的前一步")

    # 回到基準姿勢（動作之間才能無縫切換）
    if neutral is not None and not action.get("loop"):
        if name not in NO_NEUTRAL_START and diff(smalls[0], neutral) > NEUTRAL_LIMIT:
            errors.append(f"第 1 格不是基準姿勢（差 {diff(smalls[0], neutral):.1f}），從待機切過來會瞬移")
        if name not in NO_NEUTRAL_END and diff(smalls[-1], neutral) > NEUTRAL_LIMIT:
            errors.append(f"最後一格沒回到基準姿勢（差 {diff(smalls[-1], neutral):.1f}），切回待機會瞬移")
    if name == "sleep_in" and frames_of("sleep"):
        if diff(smalls[-1], small(Image.open(frames_of("sleep")[0]))) > NEUTRAL_LIMIT:
            errors.append("sleep_in 最後一格要等於 sleep 第 1 格")
    if name == "sleep_out" and frames_of("sleep"):
        if diff(smalls[0], small(Image.open(frames_of("sleep")[0]))) > NEUTRAL_LIMIT:
            errors.append("sleep_out 第 1 格要等於 sleep 第 1 格")

    # 腳底線
    if action.get("ground"):
        ends = [imgs[0], imgs[-1]] if not action.get("loop") else imgs[::max(1, len(imgs) // 6)]
        for img in ends:
            b = bottom(img)
            if b is not None and abs(b - BASE) > BASE_TOL and not action.get("free_scale"):
                errors.append(f"腳底在 y={b}，應在 y={BASE}±{BASE_TOL}")
                break
    return errors, warns, imgs


def write_preview(action, imgs):
    PREVIEW.mkdir(exist_ok=True)
    shown = []
    for im in imgs:
        bg = Image.new("RGBA", im.size, (236, 242, 238, 255)); bg.alpha_composite(im)
        shown.append(bg.convert("RGB").resize((256, 256)))
    shown[0].save(PREVIEW / f"{action['name']}.gif", save_all=True, append_images=shown[1:], duration=round(1000 / SPEC["fps"]), loop=0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    actions = SPEC["actions"]
    if args.only:
        unknown = set(args.only) - {a["name"] for a in actions}
        if unknown:
            print("不認得的動作：", ", ".join(sorted(unknown))); return 2
        actions = [a for a in actions if a["name"] in args.only]
    idle_files = frames_of("idle")
    neutral = small(Image.open(idle_files[0])) if idle_files else None
    if neutral is None:
        print("⚠ 還沒有 idle 的影格，無法檢查「回到基準姿勢」")
    failed = 0
    sheet = []
    for action in actions:
        errors, warns, imgs = check(action, neutral)
        status = "FAIL" if errors else ("WARN" if warns else "PASS")
        failed += bool(errors)
        print(f"[{status}] {action['name']}（{action['frames']} 格・{'循環' if action.get('loop') else '單次'}）")
        for m in errors: print(f"    ✗ {m}")
        for m in warns: print(f"    △ {m}")
        if imgs and args.preview:
            write_preview(action, imgs)
            sheet.append([imgs[i] for i in range(0, len(imgs), max(1, len(imgs) // 8))][:8])
    if args.preview and sheet:
        cell = 112
        S = Image.new("RGB", (8 * cell, len(sheet) * cell), (236, 242, 238))
        for r, row in enumerate(sheet):
            for c, im in enumerate(row):
                t = im.resize((cell, cell)); S.paste(t, (c * cell, r * cell), t)
        S.save(PREVIEW / "overview.png")
        print(f"預覽：{PREVIEW / 'overview.png'}")
    print(f"\n結果：{len(actions) - failed}/{len(actions)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
