"""Normalize supplied/generated artwork, never synthesize or duplicate frames.

python assets/pet/v3/normalize_raw.py --phase 1
Pillow only. Background removal is edge-connected; alpha is binary.
One shared resize factor per action; preserve hop displacement and peek crops.
"""
from __future__ import annotations
import argparse
import json
from collections import deque
from pathlib import Path
from statistics import median
from PIL import Image

HERE = Path(__file__).resolve().parent


def components(mask, w, h):
    seen = bytearray(w * h)
    groups = []
    for start, active in enumerate(mask):
        if not active or seen[start]:
            continue
        seen[start] = 1
        todo = [start]
        group = []
        while todo:
            i = todo.pop()
            group.append(i)
            x, y = i % w, i // w
            for j in ((i-1 if x else -1), (i+1 if x+1<w else -1),
                      (i-w if y else -1), (i+w if y+1<h else -1)):
                if j >= 0 and mask[j] and not seen[j]:
                    seen[j] = 1
                    todo.append(j)
        groups.append(group)
    return groups


def clean(image):
    image = image.convert('RGBA')
    w, h = image.size
    px = list(image.getdata())
    # Opaque backgrounds only: flood matching corner colors from canvas edges.
    corners = [px[0], px[w-1], px[-w], px[-1]]
    if all(p[3] > 240 for p in corners):
        seeds = set(range(w)) | set(range((h-1)*w,h*w))
        seeds |= {y*w for y in range(h)} | {y*w+w-1 for y in range(h)}
        seen = bytearray(w*h)
        queue = deque(seeds)
        while queue:
            i = queue.popleft()
            if seen[i]:
                continue
            seen[i] = 1
            c = px[i]
            if min(max(abs(c[k]-bg[k]) for k in range(3)) for bg in corners) > 22:
                continue
            px[i] = (0,0,0,0)
            x,y=i%w,i//w
            for j in ((i-1 if x else -1),(i+1 if x+1<w else -1),(i-w if y else -1),(i+w if y+1<h else -1)):
                if j>=0 and not seen[j]: queue.append(j)
    # Cutout residue is removed before connected-component analysis.
    mask = bytearray(len(px))
    for i,(r,g,b,a) in enumerate(px):
        magenta = r>=190 and b>=190 and g<=165 and abs(r-b)<=85
        mask[i] = int(a>=224 and not magenta)
    groups = components(mask,w,h)
    minimum = max(16,int(w*h*0.00003))
    for group in groups:
        if len(group)<minimum:
            for i in group: mask[i]=0
    image.putdata([(r,g,b,255) if mask[i] else (0,0,0,0)
                   for i,(r,g,b,a) in enumerate(px)])
    return image


def normalize(action, raw, out):
    image = clean(Image.open(raw))
    w,h=image.size
    n=action['frames']
    # Verify one substantial sheep component for each specified frame.
    mask=bytearray(a>0 for a in image.getchannel('A').getdata())
    groups=components(mask,w,h)
    bodies=[g for g in groups if len(g)>w*h*0.005]
    bodies.sort(key=lambda g: sum(i%w for i in g)/len(g))
    if len(bodies)!=n:
        raise ValueError(f'{action["name"]}: detected {len(bodies)} bodies, expected {n}; refusing to add/delete frames')
    centers=[sum(i%w for i in g)/len(g) for g in bodies]
    # Search low-occupancy columns near each expected boundary. This avoids
    # splitting ears when generated spacing is not precisely uniform.
    occupancy=[0]*w
    for i,a in enumerate(mask):
        if a: occupancy[i%w]+=1
    bounds=[0]
    for k in range(1,n):
        expected=w*k/n
        lo=max(int(centers[k-1])+1,round(expected-w/n*.15))
        hi=min(int(centers[k]),round(expected+w/n*.15))
        boundary=min(range(lo,hi+1),key=lambda x:(occupancy[x],abs(x-expected)))
        if occupancy[boundary]>max(4,int(h*.02)):
            raise ValueError(f'{action["name"]}: no clean split at frame {k}; regenerate raw')
        bounds.append(boundary)
    bounds.append(w)
    frames=[image.crop((bounds[k],0,bounds[k+1],h)) for k in range(n)]
    boxes=[f.getbbox() for f in frames]
    if any(b is None for b in boxes): raise ValueError('Empty frame; refusing to pad')
    heights=[b[3]-b[1] for b in boxes]
    widths=[b[2]-b[0] for b in boxes]
    ground=max(b[3] for b in boxes)
    envelope=ground-min(b[1] for b in boxes)
    scale=min(384/median(heights),450/max(heights),464/max(widths),
              (440 if action['name']=='drag' else 480)/envelope if action.get('hop') else 100)
    sheet=Image.new('RGBA',(n*512,512))
    report=[]
    for k,(fr,box) in enumerate(zip(frames,boxes)):
        crop=fr.crop(box)
        crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.LANCZOS)
        crop.putalpha(crop.getchannel('A').point(lambda a:255 if a>=128 else 0))
        # Clear invisible RGB for deterministic transparent pixels.
        crop.putdata([(r,g,b,255) if a else (0,0,0,0) for r,g,b,a in crop.getdata()])
        x=512-crop.width if action.get('free_center') else (512-crop.width)//2
        offset=round((ground-box[3])*scale) if action.get('hop') else 0
        bottom=488-offset
        if action['name']=='drag': bottom=450-offset
        y=bottom-crop.height
        if y<5: raise ValueError(f'{action["name"]} frame {k+1}: exceeds top safe area')
        sheet.alpha_composite(crop,(k*512+x,y))
        report.append({'frame':k+1,'source_box':box,'x':x,'y':y,'bottom':bottom})
    out.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(out)
    return {'action':action['name'],'frames':n,'source_size':[w,h],'shared_scale':scale,'cuts':bounds,'placements':report}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',type=int,default=1)
    ap.add_argument('--only',nargs='*')
    ap.add_argument('--review-gifs',action='store_true',help='Decode every preview GIF frame into a review contact sheet')
    args=ap.parse_args()
    spec=json.loads((HERE/'spec.json').read_text(encoding='utf-8'))
    if args.review_gifs:
        review=[]
        for action in spec['actions']:
            if action['phase']>args.phase: continue
            gif=Image.open(HERE/'_preview'/f'{action["name"]}.gif')
            row=Image.new('RGB',(8*160,160),(236,242,238))
            durations=[]
            for i in range(gif.n_frames):
                gif.seek(i)
                durations.append(gif.info.get('duration'))
                row.paste(gif.convert('RGB').resize((160,160)),(160*i,0))
            review.append(row)
            print(action['name'],'decoded GIF frames',gif.n_frames,'durations',durations)
        contact=Image.new('RGB',(1280,len(review)*160),(236,242,238))
        for i,row in enumerate(review): contact.paste(row,(0,i*160))
        contact.save(HERE/'_preview'/'gif-review.png')
        return 0
    failed=[]; reports=[]
    for action in spec['actions']:
        if action['phase']>args.phase or (args.only and action['name'] not in args.only):continue
        try:
            reports.append(normalize(action,HERE/'raw'/f'{action["name"]}.png',HERE/'sheets'/f'{action["name"]}.png'))
            print('NORMALIZED',action['name'])
        except (ValueError,FileNotFoundError) as exc:
            failed.append(str(exc));print('REGENERATE',exc)
    preview=HERE/'_preview';preview.mkdir(exist_ok=True)
    (preview/'normalization.json').write_text(json.dumps({'results':reports,'failures':failed},ensure_ascii=False,indent=2),encoding='utf-8')
    return bool(failed)


if __name__=='__main__':raise SystemExit(main())
