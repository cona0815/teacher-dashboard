"""把 Codex 的透明影格（out_rgba）轉成小綿助 v5 執行用動畫包：每組一個動態 WebP＋manifest.json。

python tools/build_pet_pack.py <out_rgba 資料夾> assets/pet/v5

- 來源：Codex 專案 outputs/pet-silhouette-ten/out_rgba/<角色>/<動作>/0000.png…（320×320 RGBA、25fps）
- 連續完全相同的格合併、時間累加；q80＋alpha 60 在桌寵實際大小看不出和原圖的差別，四隻約 50MB
- 每組轉完都重新解碼檢查格數與總時長
"""
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('src', type=Path)
ap.add_argument('dst', type=Path)
ap.add_argument('--quality', type=int, default=80)
ap.add_argument('--alpha-quality', type=int, default=60)
args = ap.parse_args()

FRAME_MS = 40   # 來源 25fps
manifest = {'version': 1, 'fps': 25, 'size': 320, 'characters': {}}
total = 0
worst = []
for char_dir in sorted(p for p in args.src.iterdir() if p.is_dir()):
    char = char_dir.name
    manifest['characters'][char] = {}
    (args.dst / char).mkdir(parents=True, exist_ok=True)
    for act_dir in sorted(p for p in char_dir.iterdir() if p.is_dir()):
        act = act_dir.name
        files = sorted(act_dir.glob('[0-9][0-9][0-9][0-9].png'))
        meta = json.loads((act_dir / 'meta.json').read_text(encoding='utf-8'))
        frames, durations, last = [], [], None
        for f in files:   # 連續完全相同的格合併，時間累加
            im = Image.open(f).convert('RGBA')
            h = hashlib.md5(im.tobytes()).digest()
            if h == last:
                durations[-1] += FRAME_MS
            else:
                frames.append(im); durations.append(FRAME_MS); last = h
        out = args.dst / char / f'{act}.webp'
        frames[0].save(out, 'WEBP', save_all=True, append_images=frames[1:], duration=durations, loop=0,
                       quality=args.quality, alpha_quality=args.alpha_quality, method=4)
        total += out.stat().st_size
        # 驗證：可解碼、格數、總時長、畫質
        dec = Image.open(out)
        n = dec.n_frames
        dur = 0
        diffs = []
        for i in range(n):
            dec.seek(i); dec.load()   # Pillow 要 load() 之後 info['duration'] 才是這一格的
            dur += dec.info['duration']
            if i in (0, n // 2, n - 1):
                a = np.asarray(dec.convert('RGBA'), float); b = np.asarray(frames[i], float)
                # 以「疊在黑底」的結果比較，透明處的顏色不算
                ca = a[..., :3] * a[..., 3:] / 255; cb = b[..., :3] * b[..., 3:] / 255
                diffs.append(np.abs(ca - cb).mean() + np.abs(a[..., 3] - b[..., 3]).mean())
        assert n == len(frames), (char, act, n, len(frames))
        assert dur == len(files) * FRAME_MS, (char, act, dur, len(files) * FRAME_MS)
        worst.append((max(diffs), f'{char}/{act}'))
        manifest['characters'][char][act] = {
            'file': f'{char}/{act}.webp', 'label': meta.get('label', ''), 'source_frames': len(files),
            'unique_frames': len(frames), 'duration_ms': dur, 'durations': durations, 'loop': True}
        print(f'{char}/{act}: {len(files)} 格 → {len(frames)} 張不重複，{out.stat().st_size / 1024:.0f}KB', flush=True)
(args.dst / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
worst.sort(reverse=True)
print(f'\n總計 {total / 2**20:.1f}MB；畫質差最大的三組：{worst[:3]}')
