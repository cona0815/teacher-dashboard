"""教師工作台介面美術驗收（三套風格）：檔案齊不齊、尺寸格式、透明背景、安全範圍、檔案大小，並輸出實際使用情境的預覽。

用法（專案根目錄）：
    python assets/art/check_art.py                    # 檢查三套全部
    python assets/art/check_art.py --theme cozy       # 只檢查一套
    python assets/art/check_art.py --first-batch      # 只檢查第一批樣本
    python assets/art/check_art.py --review           # 另外輸出 assets/art/_review/ 預覽圖給老師看

全部 PASS 才算合格；WARN 要在交件說明裡解釋。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("需要 Pillow：pip install pillow")

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "art_spec.json").read_text(encoding="utf-8"))
REVIEW = HERE / "_review"
KINDS = ("prompt", "quiet", "icon")
THEMES = {t["id"]: t for t in SPEC["themes"]}


def font(size: int):
    for name in ("msjhbd.ttc", "msjh.ttc", "NotoSansTC-Bold.otf", "NotoSansCJK-Bold.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rgb(hex_: str):
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def mix(a: str, b: str, k: float):
    ca, cb = rgb(a), rgb(b)
    return tuple(round(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))


def items(first_batch: bool):
    wanted = set(SPEC["first_batch"]) if first_batch else None
    for kind in KINDS:
        for it in SPEC[kind]:
            if wanted is None or f"{kind}/{it['id']}" in wanted:
                yield kind, it


def label(it: dict) -> str:
    return it.get("text") or it.get("state") or it.get("label")


def check(theme: str, kind: str, it: dict):
    fmt = SPEC["formats"][kind]
    errors, warns = [], []
    web = HERE / theme / kind / f"{it['id']}.webp"
    master = HERE / "_masters" / theme / kind / f"{it['id']}.png"
    if not web.is_file():
        return [f"缺 {web.relative_to(HERE.parents[1]).as_posix()}"], warns, None
    img = Image.open(web)
    if img.format != "WEBP":
        errors.append(f"不是 webp（是 {img.format}）")
    if list(img.size) != fmt["web"]:
        errors.append(f"尺寸 {img.size[0]}×{img.size[1]}，應為 {fmt['web'][0]}×{fmt['web'][1]}")
    kb = web.stat().st_size / 1024
    if kb > fmt["web_max_kb"]:
        errors.append(f"檔案 {kb:.0f}KB，上限 {fmt['web_max_kb']}KB")
    if img.mode != "RGBA":
        errors.append("不是 RGBA（要透明背景）")
        return errors, warns, img
    w, h = img.size
    alpha = img.getchannel("A")
    corners = [alpha.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    if max(corners) > 8:
        errors.append("四個角不是透明的：背景要去掉，不要畫底色方塊")
    box = alpha.point(lambda a: 255 if a >= 24 else 0).getbbox()
    if not box:
        errors.append("整張是空的")
        return errors, warns, img
    lo = 0.08 if kind == "icon" else 0.06
    if box[0] < w * lo - 1 or box[1] < h * lo - 1 or box[2] > w * (1 - lo) + 1 or box[3] > h * (1 - lo) + 1:
        errors.append(f"主體超出安全範圍（{int(lo * 100)}%–{int(100 - lo * 100)}%），太貼邊")
    fill = (box[2] - box[0]) * (box[3] - box[1]) / (w * h)
    if fill < (0.30 if kind == "icon" else 0.25):
        warns.append(f"主體只佔畫面 {fill:.0%}，遠看會太小")
    if sum(alpha.histogram()[16:240]) < 150:
        warns.append("邊緣幾乎沒有半透明像素，縮小後會有鋸齒")
    if not master.is_file():
        warns.append(f"缺原始大圖 _masters/{theme}/{kind}/{it['id']}.png（{fmt['master'][0]}×{fmt['master'][1]}）")
    else:
        m = Image.open(master)
        if list(m.size) != fmt["master"]:
            errors.append(f"原始大圖尺寸 {m.size[0]}×{m.size[1]}，應為 {fmt['master'][0]}×{fmt['master'][1]}")
    return errors, warns, img


def review_icons(theme, got, out):
    pal = THEMES[theme]["palette"]
    icons = [(it, im) for kind, it, im in got if kind == "icon" and im is not None]
    if not icons:
        return
    sizes = (22, 32, 48, 96)
    row_h, label_w, mid = 150, 210, 75
    tiles = [pal["surface"], pal["bg"]]
    width = label_w + len(tiles) * sum(s + 2 * max(3, s // 6) + 14 for s in sizes) + 20
    S = Image.new("RGB", (width, row_h * len(icons) + 50), pal["bg"])
    d = ImageDraw.Draw(S)
    d.text((12, 14), f"{THEMES[theme]['name']}：介面圖示實際大小（22／32／48／96px）", fill=pal["ink"], font=font(20))
    for r, (it, im) in enumerate(icons):
        y = 50 + r * row_h
        d.text((12, y + mid - 10), f"{it['label']}  {it['id']}", fill=pal["ink"], font=font(16))
        x = label_w
        for bg in tiles:
            for s in sizes:
                pad = max(3, s // 6)
                d.rounded_rectangle((x, y + mid - s // 2 - pad, x + s + 2 * pad, y + mid + s // 2 + pad), radius=max(4, s // 4), fill=bg,
                                    outline=pal["muted"], width=1)
                t = im.resize((s, s), Image.Resampling.LANCZOS)
                S.paste(t, (x + pad, y + mid - s // 2), t)
                x += s + 2 * pad + 14
    S.save(out / "icons.png")


def prompt_board(theme, it, im, W=1920, H=1080):
    """模擬投影全螢幕的大屏提示：上面大字、下面插圖，背景是該風格的底色。"""
    pal = THEMES[theme]["palette"]
    color = pal[it["category"]]
    S = Image.new("RGB", (W, H), pal["bg"])
    grad = Image.new("RGB", (1, H))
    for yy in range(H):
        grad.putpixel((0, yy), mix(color, pal["bg"], min(1, .82 + yy / H * .5)))
    S.paste(grad.resize((W, H)))
    d = ImageDraw.Draw(S)
    f = font(118)
    tw = d.textlength(it["text"], font=f)
    d.text(((W - tw) / 2, 170), it["text"], fill=color if theme != "tech" else pal["ink"], font=f)
    ih = int(H * 0.38)
    t = im.resize((int(im.width * ih / im.height), ih), Image.Resampling.LANCZOS)
    S.paste(t, ((W - t.width) // 2, 400), t)
    return S


def review_prompts(theme, got, out):
    pal = THEMES[theme]["palette"]
    prompts = [(it, im) for kind, it, im in got if kind == "prompt" and im is not None]
    for it, im in prompts:
        prompt_board(theme, it, im).save(out / f"prompt_{it['id']}.jpg", quality=88)
    if prompts:
        cell, cols = 320, 4
        rows = (len(prompts) + cols - 1) // cols
        G = Image.new("RGB", (cols * cell, rows * (cell + 40)), pal["bg"])
        d = ImageDraw.Draw(G)
        for k, (it, im) in enumerate(prompts):
            x, y = (k % cols) * cell, (k // cols) * (cell + 40)
            d.rounded_rectangle((x + 6, y + 6, x + cell - 6, y + cell - 6), radius=14, fill=pal["surface"])
            t = im.copy(); t.thumbnail((cell - 24, cell - 24))
            G.paste(t, (x + (cell - t.width) // 2, y + (cell - t.height) // 2), t)
            d.text((x + 10, y + cell + 4), it["text"][:16], fill=pal["ink"], font=font(18))
        G.save(out / "prompts.png")


def review_quiet(theme, got, out):
    pal = THEMES[theme]["palette"]
    q = [(it, im) for kind, it, im in got if kind == "quiet" and im is not None]
    if not q:
        return
    S = Image.new("RGB", (300 * len(q), 340), pal["bg"])
    d = ImageDraw.Draw(S)
    for k, (it, im) in enumerate(q):
        d.rounded_rectangle((k * 300 + 8, 8, k * 300 + 292, 292), radius=18, fill=pal["surface"])
        t = im.resize((230, 230), Image.Resampling.LANCZOS)
        S.paste(t, (k * 300 + 35, 35), t)
        d.text((k * 300 + 12, 300), it["state"], fill=pal["ink"], font=font(18))
    S.save(out / "quiet.png")


def review_compare(results):
    """三套風格並排：同一個 id 一列，左到右是 tech、minimal、cozy，方便老師比較。"""
    themes = [t for t in THEMES if t in results]
    rows = []
    for kind, it in items(False):
        ims = {t: results[t].get((kind, it["id"])) for t in themes}
        if any(ims.values()):
            rows.append((kind, it, ims))
    if len(themes) < 2 or not rows:
        return
    cell, lab = 300, 220
    S = Image.new("RGB", (lab + cell * len(themes), 40 + cell * len(rows)), "#ffffff")
    d = ImageDraw.Draw(S)
    for c, t in enumerate(themes):
        d.text((lab + c * cell + 12, 10), THEMES[t]["name"], fill="#1f2328", font=font(20))
    for r, (kind, it, ims) in enumerate(rows):
        y = 40 + r * cell
        d.text((10, y + cell // 2 - 10), label(it)[:12], fill="#1f2328", font=font(16))
        for c, t in enumerate(themes):
            x = lab + c * cell
            d.rectangle((x + 4, y + 4, x + cell - 4, y + cell - 4), fill=THEMES[t]["palette"]["bg"])
            im = ims[t]
            if im is None:
                d.text((x + 20, y + cell // 2), "（還沒有）", fill="#9aa0a6", font=font(16))
                continue
            im = im.copy(); im.thumbnail((cell - 30, cell - 30))
            S.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2), im)
    S.save(REVIEW / "compare_themes.png")
    print(f"三套風格對照：{REVIEW / 'compare_themes.png'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", nargs="*", choices=list(THEMES), help="只檢查這幾套風格")
    ap.add_argument("--first-batch", action="store_true", help="只檢查 art_spec.json 的 first_batch")
    ap.add_argument("--review", action="store_true", help="輸出 _review/ 預覽圖")
    args = ap.parse_args()
    failed = total = 0
    results = {}
    for theme in args.theme or list(THEMES):
        print(f"\n===== {theme}（{THEMES[theme]['name']}） =====")
        got = []
        for kind, it in items(args.first_batch):
            errors, warns, img = check(theme, kind, it)
            total += 1; failed += bool(errors)
            status = "FAIL" if errors else ("WARN" if warns else "PASS")
            print(f"[{status}] {kind}/{it['id']}（{label(it)}）")
            for m in errors: print(f"    ✗ {m}")
            for m in warns: print(f"    △ {m}")
            got.append((kind, it, img.convert("RGBA") if img is not None else None))
        results[theme] = {(k, it["id"]): im for k, it, im in got if im is not None}
        if args.review:
            out = REVIEW / theme
            out.mkdir(parents=True, exist_ok=True)
            review_icons(theme, got, out); review_prompts(theme, got, out); review_quiet(theme, got, out)
            print(f"預覽：{out}")
    if args.review:
        review_compare(results)
    print(f"\n結果：{total - failed}/{total} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
