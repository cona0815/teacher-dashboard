"""小綿助 v3 動作圖驗收工具。

用法：
    python assets/pet/v3/check_sprites.py            # 檢查第一批（phase 1）
    python assets/pet/v3/check_sprites.py --phase 2  # 檢查第一＋二批
    python assets/pet/v3/check_sprites.py --only idle greet
    python assets/pet/v3/check_sprites.py --preview  # 另外輸出 _preview/*.gif 與總覽圖

每張 sheets/<name>.png 必須是「一橫排 N 格、每格 512x512、透明背景」。
全部 PASS 才算交件合格；WARN 需在交件說明裡解釋。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:  # pragma: no cover
    sys.exit("需要 Pillow：pip install pillow")

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
SIZE = SPEC["frame_size"]
SHEETS = HERE / "sheets"
PREVIEW = HERE / "_preview"

# 門檻（與桌寵載入器的行為對齊：alpha<32 會被砍掉、洋紅色會被當成透明色）
EDGE_MARGIN = 4            # 內容離格子邊緣至少幾 px
MIN_TRANSPARENT = 0.30     # 每格至少 30% 完全透明
MAX_SOFT_ALPHA = 0.04      # 半透明像素（32<=a<224）佔角色像素的比例上限
BASELINE_SPREAD = 16       # 各格腳底 y 的最大差距
BASELINE_RANGE = (430, 508)
HEIGHT_RATIO = (0.55, 0.92)  # 角色高度 / 512
SCALE_SPREAD = 1.20        # 各格角色高度 最大/最小
MAGENTA_FRINGE = 80        # 少量洋紅雜點只提醒；超過就是真的用了洋紅色
MIN_MOTION = 1.0           # 相鄰格平均像素差，低於此視為沒在動


def is_magenta(r: int, g: int, b: int) -> bool:
    return r >= 190 and b >= 190 and g <= 165 and abs(r - b) <= 85


def check_sheet(action: dict) -> tuple[list[str], list[str], list[Image.Image]]:
    name, n = action["name"], action["frames"]
    errors: list[str] = []
    warns: list[str] = []
    path = SHEETS / f"{name}.png"
    if not path.exists():
        return [f"缺檔：sheets/{name}.png"], warns, []
    img = Image.open(path)
    if img.mode != "RGBA":
        errors.append(f"色彩模式是 {img.mode}，必須是 RGBA（透明背景）")
        img = img.convert("RGBA")
    if img.size != (n * SIZE, SIZE):
        errors.append(f"尺寸 {img.size[0]}x{img.size[1]}，應為 {n * SIZE}x{SIZE}（{n} 格）")
        return errors, warns, []

    frames = [img.crop((i * SIZE, 0, (i + 1) * SIZE, SIZE)) for i in range(n)]
    bottoms, heights = [], []
    free_scale = action.get("free_scale", False)
    free_center = action.get("free_center", False)
    for i, fr in enumerate(frames, 1):
        alpha = fr.getchannel("A")
        hist = alpha.histogram()
        total = SIZE * SIZE
        clear = hist[0] / total
        solid = sum(hist[32:]) or 1
        soft = sum(hist[32:224]) / solid
        bbox = alpha.point(lambda a: 255 if a >= 32 else 0).getbbox()
        if not bbox:
            errors.append(f"第 {i} 格是空的")
            continue
        if clear < MIN_TRANSPARENT:
            errors.append(f"第 {i} 格透明區只有 {clear:.0%}（背景沒去乾淨？）")
        if soft > MAX_SOFT_ALPHA:
            warns.append(f"第 {i} 格半透明像素 {soft:.1%}，邊緣不夠銳利（桌寵會砍掉 alpha<32 的部分）")
        magenta = sum(1 for r, g, b, a in fr.getdata() if a >= 32 and is_magenta(r, g, b))
        if magenta > MAGENTA_FRINGE:
            errors.append(f"第 {i} 格有 {magenta} 個洋紅色像素（桌寵會把它當透明挖掉）")
        elif magenta:
            warns.append(f"第 {i} 格邊緣有 {magenta} 個洋紅色雜點（去背殘留，最好清掉）")
        x0, y0, x1, y1 = bbox
        touches = []
        if x0 < EDGE_MARGIN:
            touches.append("左")
        if x1 > SIZE - EDGE_MARGIN and not free_center:
            touches.append("右")
        if y0 < EDGE_MARGIN:
            touches.append("上")
        if y1 > SIZE - EDGE_MARGIN + 3:
            touches.append("下")
        if touches:
            errors.append(f"第 {i} 格內容碰到{'、'.join(touches)}邊（會被切掉）")
        bottoms.append(y1)
        heights.append(y1 - y0)
        if not free_scale and not (HEIGHT_RATIO[0] <= (y1 - y0) / SIZE <= HEIGHT_RATIO[1]):
            warns.append(f"第 {i} 格角色高度 {(y1 - y0) / SIZE:.0%}，建議約 75%")

    if bottoms and not free_scale:
        spread = max(bottoms) - min(bottoms)
        if action.get("hop"):
            # 跳躍動作允許騰空，但至少要有 2 格踩在同一條地面線上（起跳與落地）
            ground = max(bottoms)
            on_ground = sum(1 for b in bottoms if ground - b <= BASELINE_SPREAD)
            if on_ground < min(2, len(bottoms)):
                errors.append(f"腳底線不一致：只有 {on_ground}/{len(bottoms)} 格踩在地面線上")
        elif spread > BASELINE_SPREAD:
            errors.append(f"腳底線上下差 {spread}px（上限 {BASELINE_SPREAD}px），播放時會抖")
        if not (BASELINE_RANGE[0] <= max(bottoms) <= BASELINE_RANGE[1]):
            warns.append(f"腳底在 y={max(bottoms)}，建議約 y={SPEC['baseline_y']}")
    if heights and not free_scale and not action.get("hop"):
        if max(heights) / max(1, min(heights)) > SCALE_SPREAD:
            errors.append(f"各格角色大小不一（最大/最小 = {max(heights) / min(heights):.2f}），播放時會忽大忽小")

    if len(frames) > 1:
        diffs = []
        for a, b in zip(frames, frames[1:]):
            diff = ImageChops.difference(a, b)
            diffs.append(sum(ImageStat.Stat(diff).mean))
        if max(diffs) < MIN_MOTION:
            errors.append("每一格幾乎一樣，沒有動作")
    return errors, warns, frames


def write_preview(name: str, action: dict, frames: list[Image.Image]) -> None:
    PREVIEW.mkdir(exist_ok=True)
    shown = []
    for fr in frames:
        bg = Image.new("RGBA", fr.size, (236, 242, 238, 255))
        bg.alpha_composite(fr)
        shown.append(bg.convert("RGB").resize((256, 256)))
    shown[0].save(PREVIEW / f"{name}.gif", save_all=True, append_images=shown[1:],
                  duration=action["ms"], loop=0)


def write_overview(results: list[tuple[dict, list[Image.Image]]]) -> Path:
    cell = 128
    cols = max(a["frames"] for a, _ in results)
    sheet = Image.new("RGB", (cols * cell, len(results) * cell), (236, 242, 238))
    for row, (_, frames) in enumerate(results):
        for col, fr in enumerate(frames):
            sheet.paste(fr.resize((cell, cell)), (col * cell, row * cell), fr.resize((cell, cell)))
    out = PREVIEW / "overview.png"
    sheet.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=1, help="檢查到第幾批（預設 1）")
    ap.add_argument("--only", nargs="*", help="只檢查這幾個動作")
    ap.add_argument("--preview", action="store_true", help="輸出 _preview/*.gif 與 overview.png")
    args = ap.parse_args()

    actions = [a for a in SPEC["actions"] if a["phase"] <= args.phase]
    if args.only:
        wanted = set(args.only)
        unknown = wanted - {a["name"] for a in SPEC["actions"]}
        if unknown:
            print("不認得的動作：", ", ".join(sorted(unknown)))
            return 2
        actions = [a for a in SPEC["actions"] if a["name"] in wanted]

    known = {a["name"] for a in SPEC["actions"]}
    extras = sorted(p.stem for p in SHEETS.glob("*.png") if p.stem not in known) if SHEETS.exists() else []

    failed = 0
    good: list[tuple[dict, list[Image.Image]]] = []
    for action in actions:
        errors, warns, frames = check_sheet(action)
        status = "FAIL" if errors else ("WARN" if warns else "PASS")
        failed += bool(errors)
        print(f"[{status}] {action['name']}（{action['frames']} 格）")
        for msg in errors:
            print(f"    ✗ {msg}")
        for msg in warns:
            print(f"    △ {msg}")
        if frames and args.preview:
            write_preview(action["name"], action, frames)
            good.append((action, frames))
    if extras:
        print(f"[WARN] sheets/ 裡有規格表沒有的檔案：{', '.join(extras)}")
    if args.preview and good:
        print(f"預覽：{write_overview(good)}")
    print(f"\n結果：{len(actions) - failed}/{len(actions)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
