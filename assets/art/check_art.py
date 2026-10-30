"""教師工作台介面美術驗收：檔案齊不齊、尺寸格式、透明背景、安全範圍、檔案大小，並輸出實際使用情境的預覽。

用法（專案根目錄）：
    python assets/art/check_art.py                 # 檢查全部
    python assets/art/check_art.py --first-batch   # 只檢查第一批樣本
    python assets/art/check_art.py --review        # 另外輸出 assets/art/_review/*.png 給老師看

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
ACCENT = {"#1f7a52": "#e6f6ec", "#2457e6": "#e9eefc", "#d0631a": "#fff0e4", "#7b4fb8": "#f3ecfb", "#cf4433": "#fdeceb"}


def font(size: int):
    for name in ("msjhbd.ttc", "msjh.ttc", "NotoSansTC-Bold.otf", "NotoSansCJK-Bold.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def items(first_batch: bool):
    wanted = set(SPEC["first_batch"]) if first_batch else None
    for kind in KINDS:
        for it in SPEC[kind]:
            if wanted is None or f"{kind}/{it['id']}" in wanted:
                yield kind, it


def check(kind: str, it: dict):
    fmt = SPEC["formats"][kind]
    errors, warns = [], []
    web = HERE / kind / f"{it['id']}.webp"
    master = HERE / "_masters" / kind / f"{it['id']}.png"
    if not web.is_file():
        return [f"缺 {web.relative_to(HERE.parents[1])}"], warns, None
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
    hist = alpha.histogram()
    if sum(hist[16:240]) < 150:
        warns.append("邊緣幾乎沒有半透明像素，縮小後會有鋸齒")
    if not master.is_file():
        warns.append(f"缺原始大圖 _masters/{kind}/{it['id']}.png（{fmt['master'][0]}×{fmt['master'][1]}）")
    else:
        m = Image.open(master)
        if list(m.size) != fmt["master"]:
            errors.append(f"原始大圖尺寸 {m.size[0]}×{m.size[1]}，應為 {fmt['master'][0]}×{fmt['master'][1]}")
    return errors, warns, img


def review_icons(got):
    icons = [(it, im) for kind, it, im in got if kind == "icon" and im is not None]
    if not icons:
        return
    sizes = (22, 32, 48, 96)
    row_h, label_w, mid = 150, 210, 75
    S = Image.new("RGB", (label_w + 2 * sum(s + 2 * max(3, s // 6) + 14 for s in sizes) + 20, row_h * len(icons) + 50), "#ffffff")
    d = ImageDraw.Draw(S)
    d.text((12, 14), "介面圖示：實際大小（左半淺色底、右半深色底）", fill="#203a2c", font=font(20))
    for r, (it, im) in enumerate(icons):
        y = 50 + r * row_h
        d.text((12, y + mid - 10), f"{it['label']}  {it['id']}", fill="#203a2c", font=font(16))
        x = label_w
        for bg in ("#eef4ef", "#1d2a24"):
            for s in sizes:
                pad = max(3, s // 6)
                d.rounded_rectangle((x, y + mid - s // 2 - pad, x + s + 2 * pad, y + mid + s // 2 + pad), radius=max(4, s // 4), fill=bg)
                t = im.resize((s, s), Image.Resampling.LANCZOS)
                S.paste(t, (x + pad, y + mid - s // 2), t)
                x += s + 2 * pad + 14
    S.save(REVIEW / "icons.png")
    print(f"預覽：{REVIEW / 'icons.png'}")


def review_prompts(got):
    prompts = [(it, im) for kind, it, im in got if kind == "prompt" and im is not None]
    for it, im in prompts:
        # 模擬投影全螢幕：上面大字、下面插圖，背景是分類色漸層
        W, H = 1920, 1080
        S = Image.new("RGB", (W, H), "#ffffff")
        d = ImageDraw.Draw(S)
        top = Image.new("RGB", (1, H))
        a, b = ACCENT.get(it["accent"], "#ffffff"), "#ffffff"
        ca, cb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        for yy in range(H):
            k = min(1, yy / (H * .7))
            top.putpixel((0, yy), tuple(round(ca[c] + (cb[c] - ca[c]) * k) for c in range(3)))
        S.paste(top.resize((W, H)))
        f = font(118)
        tw = d.textlength(it["text"], font=f)
        d.text(((W - tw) / 2, 170), it["text"], fill=it["accent"], font=f)
        ih = int(H * 0.38)
        t = im.resize((int(im.width * ih / im.height), ih), Image.Resampling.LANCZOS)
        S.paste(t, ((W - t.width) // 2, 400), t)
        S.save(REVIEW / f"prompt_{it['id']}.jpg", quality=88)
    if prompts:
        cell = 320
        cols = 4
        rows = (len(prompts) + cols - 1) // cols
        G = Image.new("RGB", (cols * cell, rows * (cell + 40)), "#f4f6f4")
        d = ImageDraw.Draw(G)
        for k, (it, im) in enumerate(prompts):
            x, y = (k % cols) * cell, (k // cols) * (cell + 40)
            d.rectangle((x + 6, y + 6, x + cell - 6, y + cell - 6), fill=ACCENT.get(it["accent"], "#ffffff"))
            t = im.copy(); t.thumbnail((cell - 24, cell - 24))
            G.paste(t, (x + (cell - t.width) // 2, y + (cell - t.height) // 2), t)
            d.text((x + 10, y + cell + 4), it["text"][:16], fill="#203a2c", font=font(18))
        G.save(REVIEW / "prompts.png")
        print(f"預覽：{REVIEW / 'prompts.png'}（每張的投影模擬：_review/prompt_<id>.jpg）")


def review_quiet(got):
    q = [(it, im) for kind, it, im in got if kind == "quiet" and im is not None]
    if not q:
        return
    S = Image.new("RGB", (300 * len(q), 340), "#ffffff")
    d = ImageDraw.Draw(S)
    for k, (it, im) in enumerate(q):
        d.rectangle((k * 300 + 8, 8, k * 300 + 292, 292), fill=ACCENT.get(it["accent"], "#ffffff"))
        t = im.resize((230, 230), Image.Resampling.LANCZOS)
        S.paste(t, (k * 300 + 35, 35), t)
        d.text((k * 300 + 12, 300), it["state"], fill="#203a2c", font=font(18))
    S.save(REVIEW / "quiet.png")
    print(f"預覽：{REVIEW / 'quiet.png'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-batch", action="store_true", help="只檢查 art_spec.json 的 first_batch")
    ap.add_argument("--review", action="store_true", help="輸出 _review/ 預覽圖")
    args = ap.parse_args()
    failed = total = 0
    got = []
    for kind, it in items(args.first_batch):
        errors, warns, img = check(kind, it)
        total += 1; failed += bool(errors)
        status = "FAIL" if errors else ("WARN" if warns else "PASS")
        print(f"[{status}] {kind}/{it['id']}（{it.get('text') or it.get('state') or it.get('label')}）")
        for m in errors: print(f"    ✗ {m}")
        for m in warns: print(f"    △ {m}")
        got.append((kind, it, img.convert("RGBA") if img is not None else None))
    if args.review:
        REVIEW.mkdir(exist_ok=True)
        review_icons(got); review_prompts(got); review_quiet(got)
    print(f"\n結果：{total - failed}/{total} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
