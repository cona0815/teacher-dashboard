"""小綿助 v4 動畫驗收：檢查 render 出來的連續影格是否「流暢、可無縫切換」。

用法（專案根目錄）：
    python assets/pet/v4/check_sequences.py                       # 檢查 out/ 底下所有角色
    python assets/pet/v4/check_sequences.py --character sheep     # 只檢查一個角色
    python assets/pet/v4/check_sequences.py --only idle walk_right
    python assets/pet/v4/check_sequences.py --preview             # 另外輸出 _preview/<角色>/*.gif 與 overview.png

影格位置：assets/pet/v4/out/<角色>/<動作>/<動作>_0001.png（從 0001 起連號，512×512 RGBA）。
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
CHARACTERS = [c["id"] for c in SPEC["characters"]]
SMALL = 128

# 單次動作開頭／結尾要回到基準姿勢（該角色 idle 第 1 格）。
# 有 starts_from／ends_into 的動作改成對接那個動作的第 1 格；以下是其他例外
NO_NEUTRAL_START = {"peek", "turn"}
NO_NEUTRAL_END = {"peek", "turn"}
NEUTRAL_LIMIT = 6.0      # 與基準姿勢的平均差（0–255）上限
POP_RATIO = 5.0          # 相鄰格差超過「中位數 × 5」視為跳格
POP_FLOOR = 4.0          # 但差值本身要大於這個才算（避免整段靜止時誤判）
SEAM_RATIO = 2.0         # 循環接縫差 ≤ 一般相鄰格差 × 2
BASE_TOL = 5             # 腳底線容許誤差（px）
GAZE_STEP = 8.0          # gaze 相鄰兩個方向的差上限


def frames_of(char: str, name: str) -> list[Path]:
    return sorted((OUT / char / name).glob(f"{name}_*.png"))


def small(img: Image.Image) -> Image.Image:
    return img.resize((SMALL, SMALL), Image.Resampling.BILINEAR)


def first_small(char: str, name: str) -> Image.Image | None:
    files = frames_of(char, name)
    return small(Image.open(files[0])) if files else None


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


def check_gaze(smalls, neutral):
    """gaze 是 5×5 的看方向姿勢表，不是播放的動畫：檢查正中＝基準、相鄰方向只差一小步。"""
    errors = []
    if neutral is not None and diff(smalls[12], neutral) > NEUTRAL_LIMIT:
        errors.append(f"第 13 格（正中）不是基準姿勢（差 {diff(smalls[12], neutral):.1f}）")
    for r in range(5):
        for c in range(5):
            i = r * 5 + c
            for j in ([i + 1] if c < 4 else []) + ([i + 5] if r < 4 else []):
                d = diff(smalls[i], smalls[j])
                if d > GAZE_STEP:
                    errors.append(f"第 {i + 1} 格與第 {j + 1} 格方向差太大（{d:.1f}），眼睛跟游標時會跳")
    return errors


def check(char: str, action: dict, neutral: Image.Image | None):
    name, n = action["name"], action["frames"]
    errors, warns = [], []
    files = frames_of(char, name)
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

    # 每個動作要附 meta.json（每格的頭部位置、腳著地），引擎用來放對話框和影子
    meta = OUT / char / name / "meta.json"
    if not meta.is_file():
        warns.append("缺 meta.json（每格 head、feet、bbox）")
    else:
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
            if len(m.get("frames", [])) != n:
                errors.append(f"meta.json 的 frames 有 {len(m.get('frames', []))} 筆，應為 {n}")
        except ValueError:
            errors.append("meta.json 不是合法 JSON")

    if action.get("kind") == "poses":
        return errors + check_gaze(smalls, neutral), warns, imgs

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

    # 回到基準姿勢、或對接指定動作（動作之間才能無縫切換）
    if not action.get("loop"):
        src, dst = action.get("starts_from"), action.get("ends_into")
        start_ref = first_small(char, src) if src else (None if name in NO_NEUTRAL_START else neutral)
        end_ref = first_small(char, dst) if dst else (None if name in NO_NEUTRAL_END else neutral)
        if start_ref is not None and diff(smalls[0], start_ref) > NEUTRAL_LIMIT:
            what = f"{src} 第 1 格" if src else "基準姿勢"
            errors.append(f"第 1 格不是{what}（差 {diff(smalls[0], start_ref):.1f}），切過來會瞬移")
        if end_ref is not None and diff(smalls[-1], end_ref) > NEUTRAL_LIMIT:
            what = f"{dst} 第 1 格" if dst else "基準姿勢"
            errors.append(f"最後一格沒接到{what}（差 {diff(smalls[-1], end_ref):.1f}），切過去會瞬移")
        if src and start_ref is None:
            warns.append(f"還沒有 {src} 的影格，無法檢查開頭對接")
        if dst and end_ref is None:
            warns.append(f"還沒有 {dst} 的影格，無法檢查結尾對接")

    # 腳底線（perch 之類坐在邊緣上的動作用 ground_line）
    line = action.get("ground_line")
    if action.get("ground") or line:
        target = line or BASE
        ends = [imgs[0], imgs[-1]] if not action.get("loop") else imgs[::max(1, len(imgs) // 6)]
        for img in ends:
            b = bottom(img)
            if line:
                break   # 坐在邊緣時腳會垂到線下，只由 meta 判斷
            if b is not None and abs(b - target) > BASE_TOL and not action.get("free_scale"):
                errors.append(f"腳底在 y={b}，應在 y={target}±{BASE_TOL}")
                break
    return errors, warns, imgs


def write_preview(char, action, imgs):
    folder = PREVIEW / char
    folder.mkdir(parents=True, exist_ok=True)
    shown = []
    for im in imgs:
        bg = Image.new("RGBA", im.size, (236, 242, 238, 255)); bg.alpha_composite(im)
        shown.append(bg.convert("RGB").resize((256, 256)))
    ms = 250 if action.get("kind") == "poses" else round(1000 / SPEC["fps"])
    shown[0].save(folder / f"{action['name']}.gif", save_all=True, append_images=shown[1:], duration=ms, loop=0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", nargs="*", help="角色 id：" + "、".join(CHARACTERS))
    ap.add_argument("--only", nargs="*", help="只檢查這些動作")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    actions = SPEC["actions"]
    if args.only:
        unknown = set(args.only) - {a["name"] for a in actions}
        if unknown:
            print("不認得的動作：", ", ".join(sorted(unknown))); return 2
        actions = [a for a in actions if a["name"] in args.only]
    chars = args.character or [c for c in CHARACTERS if (OUT / c).is_dir()]
    unknown = set(chars) - set(CHARACTERS)
    if unknown:
        print("不認得的角色：", ", ".join(sorted(unknown))); return 2
    if not chars:
        print(f"out/ 底下還沒有任何角色資料夾（{'、'.join(CHARACTERS)}）"); return 1

    failed = total = 0
    for char in chars:
        print(f"\n===== {char} =====")
        neutral = first_small(char, "idle")
        if neutral is None:
            print("⚠ 還沒有 idle 的影格，無法檢查「回到基準姿勢」")
        sheet = []
        for action in actions:
            errors, warns, imgs = check(char, action, neutral)
            status = "FAIL" if errors else ("WARN" if warns else "PASS")
            failed += bool(errors); total += 1
            kind = "姿勢表" if action.get("kind") == "poses" else ("循環" if action.get("loop") else "單次")
            print(f"[{status}] {action['name']}（{action['frames']} 格・{kind}）")
            for m in errors[:6]: print(f"    ✗ {m}")
            if len(errors) > 6: print(f"    ✗ …另外 {len(errors) - 6} 項")
            for m in warns: print(f"    △ {m}")
            if imgs and args.preview:
                write_preview(char, action, imgs)
                sheet.append([imgs[i] for i in range(0, len(imgs), max(1, len(imgs) // 8))][:8])
        if args.preview and sheet:
            cell = 112
            S = Image.new("RGB", (8 * cell, len(sheet) * cell), (236, 242, 238))
            for r, row in enumerate(sheet):
                for c, im in enumerate(row):
                    t = im.resize((cell, cell)); S.paste(t, (c * cell, r * cell), t)
            S.save(PREVIEW / char / "overview.png")
            print(f"預覽：{PREVIEW / char / 'overview.png'}")
    print(f"\n結果：{total - failed}/{total} 通過（{len(chars)} 個角色）")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
