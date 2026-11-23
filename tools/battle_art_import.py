"""答題對戰手繪美術匯入（2026-11-22）

把交接站 BAT-01 驗收通過的圖，轉成網頁用的 WebP，放到 assets/battle/：
  角色：assets/battle/spr/<id>/<表情>.webp（384×384，帶透明）
  背景：assets/battle/bg_<場景>.webp（2000×900）
  門板：assets/battle/door_left.webp、door_right.webp（200×500，帶透明）

用法：python tools/battle_art_import.py  [--rounds R1,R2] [--spr-rounds R6]
角色只從 --spr-rounds 拿（2026-11-23 起是 R6 新造型；R1 舊造型老師退件，不可再用）。
沒有的檔案會跳過並列出來（遊戲會自動退回向量畫法）。
"""
import argparse
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CASE = r'C:/Users/cona0/Documents/Codex/2026-08-10/ai-100-100-px-2d-windows/claude-codex-handoff/cases/BAT-01_答題對戰手繪美術/art'
OUT = os.path.join(REPO, 'assets', 'battle')

MOODS = {
    'mon': ['normal', 'happy', 'roar', 'hurt', 'sleep', 'win'],
    'boss': ['normal', 'angry', 'roar', 'hurt', 'friend', 'sleepy'],
    'minion': ['normal', 'happy', 'dash'],
    'ghost': ['normal', 'near', 'laugh'],
}
SPR = {
    'fire': 'mon', 'zap': 'mon', 'rock': 'mon', 'pumpkin': 'mon', 'imp': 'mon', 'ice': 'mon',
    'gulu': 'boss', 'turtle': 'boss', 'octo': 'boss',
    'imp0': 'minion', 'imp1': 'minion', 'imp2': 'minion', 'imp3': 'minion', 'imp4': 'minion', 'ghost': 'ghost',
}
BG = ['bg_monster', 'bg_boss', 'bg_castle', 'bg_dungeon']
DOOR = ['door_left', 'door_right']


def find(rounds, *names):
    """在各輪資料夾（新的優先）找檔案"""
    for r in reversed(rounds):
        base = os.path.join(CASE, r)
        if not os.path.isdir(base):
            continue
        for sub in ['', 'A', 'B', 'C', 'D']:
            for n in names:
                p = os.path.join(base, sub, n)
                if os.path.isfile(p):
                    return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rounds', default='R1,R2')
    ap.add_argument('--spr-rounds', default='R6')
    a = ap.parse_args()
    rounds = a.rounds.split(',')
    spr_rounds = a.spr_rounds.split(',')
    old = os.path.join(OUT, 'spr')
    if os.path.isdir(old):
        shutil.rmtree(old)  # 先清掉舊角色圖，免得新舊混在一起
    missing, done = [], 0
    for sid, kind in SPR.items():
        for m in MOODS[kind]:
            p = find(spr_rounds, os.path.join(sid, m + '.png'))
            if not p:
                missing.append(f'{sid}/{m}')
                continue
            im = Image.open(p).convert('RGBA')
            if im.size != (512, 512):
                print('尺寸不對（應為 512×512）：', p, im.size)
            os.makedirs(os.path.join(OUT, 'spr', sid), exist_ok=True)
            im.resize((384, 384), Image.LANCZOS).save(os.path.join(OUT, 'spr', sid, m + '.webp'), 'WEBP', quality=88, method=6)
            done += 1
    for n in BG:
        p = find(rounds, n + '.png')
        if not p:
            missing.append(n)
            continue
        Image.open(p).convert('RGB').resize((2000, 900), Image.LANCZOS).save(os.path.join(OUT, n + '.webp'), 'WEBP', quality=82, method=6)
        done += 1
    for n in DOOR:
        p = find(rounds, n + '.png')
        if not p:
            missing.append(n)
            continue
        Image.open(p).convert('RGBA').resize((200, 500), Image.LANCZOS).save(os.path.join(OUT, n + '.webp'), 'WEBP', quality=88, method=6)
        done += 1
    print(f'轉好 {done} 張，放在 assets/battle/')
    if missing:
        print(f'還沒有的 {len(missing)} 項（遊戲會用向量畫法）：', '、'.join(missing))
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print(f'assets/battle 合計 {total / 1024:.0f} KB')


if __name__ == '__main__':
    sys.exit(main())
