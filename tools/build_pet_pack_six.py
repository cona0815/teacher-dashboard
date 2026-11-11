"""把 PET-03「六格精靈圖」做成小綿助動畫包（格式同 v5：manifest.json＋<角色>/<動作>.webp）。

python tools/build_pet_pack_six.py <PET-03 的 art 資料夾> assets/pet/v6

- 每個動作 6 格（320×320 RGBA）。同一組優先用 R3（比例修正版），沒有再用 R2，小綿羊 idle／notice／success／rest 用 R1。
- 一般動作每秒約 7 格；待機、休息慢一點，看起來比較安靜。
- 動作中文名沿用 v5 的 manifest（給選單顯示）。
"""
import argparse
import json
from pathlib import Path

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('art', type=Path)
ap.add_argument('dst', type=Path)
ap.add_argument('--quality', type=int, default=85)
ap.add_argument('--alpha-quality', type=int, default=80)
args = ap.parse_args()

CHARACTERS = ['lamb', 'cat', 'dog', 'robot']
ACTIONS = ['idle', 'notice', 'success', 'rest', 'acknowledge', 'cheer', 'listen', 'note', 'pet',
           'remind', 'report', 'rise', 'spin', 'stretch', 'task_due', 'think']
LOOP = {'idle', 'notice', 'success', 'rest', 'cheer', 'listen', 'note', 'think'}
FRAME_MS = 143                      # 約每秒 7 格
SLOW = {'idle': 260, 'rest': 320}   # 待機、休息慢一點

old = {}
old_manifest = Path(__file__).resolve().parent.parent / 'assets' / 'pet' / 'v5' / 'manifest.json'
if old_manifest.is_file():
    old = json.loads(old_manifest.read_text(encoding='utf-8')).get('characters', {})

manifest = {'version': 2, 'fps': round(1000 / FRAME_MS), 'size': 320, 'source': 'PET-03 六格精靈圖', 'characters': {}}
total = 0
for char in CHARACTERS:
    manifest['characters'][char] = {}
    (args.dst / char).mkdir(parents=True, exist_ok=True)
    for act in ACTIONS:
        folder = next((args.art / rnd / char / act for rnd in ('R3', 'R2', 'R1') if (args.art / rnd / char / act / '0000.png').is_file()), None)
        if folder is None:
            raise SystemExit(f'找不到 {char}/{act} 的影格')
        frames = [Image.open(folder / f'{i:04d}.png').convert('RGBA') for i in range(6)]
        if any(f.size != (320, 320) for f in frames):
            raise SystemExit(f'{char}/{act} 影格不是 320×320')
        step = SLOW.get(act, FRAME_MS)
        durations = [step] * 6
        if act not in LOOP:
            durations[-1] = step * 4   # 單次動作最後一格停久一點，再交回待機
        out = args.dst / char / f'{act}.webp'
        frames[0].save(out, 'WEBP', save_all=True, append_images=frames[1:], duration=durations, loop=0,
                       quality=args.quality, alpha_quality=args.alpha_quality, method=6)
        # 驗證：能解碼、6 格
        with Image.open(out) as check:
            assert getattr(check, 'n_frames', 1) == 6, (char, act, getattr(check, 'n_frames', 1))
        size = out.stat().st_size
        total += size
        manifest['characters'][char][act] = {
            'file': f'{char}/{act}.webp',
            'label': (old.get(char, {}).get(act) or {}).get('label', act),
            'source': folder.parent.parent.name,
            'unique_frames': 6,
            'duration_ms': sum(durations),
            'durations': durations,
            'loop': act in LOOP,
        }
        print(f'  {char}/{act}  {folder.parent.parent.name}  {size // 1024} KB')
(args.dst / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'完成：{len(CHARACTERS)} 角色 × {len(ACTIONS)} 動作，共 {total / 1048576:.1f} MB')
