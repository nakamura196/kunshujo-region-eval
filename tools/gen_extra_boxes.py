"""a4・a5 の余分な枠（IoU0.5 で人の枠に対応しないもの）を集計し、20 コマを描く（緑=人の枠、赤=余分な枠と番号）。出力は ~/git/tmp/k42gen/det3/extra20。"""
import json, os, random, sys
from collections import Counter
sys.path.insert(0, os.path.expanduser('~/git/digital-archive-papers/tools/kunshujo'))
from eval_final import match, load_human
from PIL import Image, ImageDraw
K = os.path.expanduser('~/git/tmp/k42gen')
OUT = os.path.join(K, 'det3', 'extra20')
frames = json.load(open(f'{K}/test_frames.json'))
keep = set(json.load(open(f'{K}/test300_canvases.json')))
frames = [f for f in frames if f['canvas'] in keep]
hum = load_human(os.path.expanduser('~/git/utda/kunshujo/static/data/index.json'), keep)
for c in hum: hum[c] = [h for h in hum[c] if min(h[2], h[3]) > 10]
frames = [f for f in frames if hum[f['canvas']]]

def inter(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1]); x2, y2 = min(a[0]+a[2], b[0]+b[2]), min(a[1]+a[3], b[1]+b[3])
    return max(0, x2-x1) * max(0, y2-y1)

rows = []
for cn, d in (('a4', 'pred-gemini'), ('a5', 'pred-claude')):
    for f in frames:
        P = [b[:4] for b in json.load(open(f'{K}/det3/{d}/{f["key"]}.json'))['boxes']]
        H = hum[f['canvas']]
        m = match(P, H, 0.5); mp = {i for i, _, _ in m}
        for i, p in enumerate(P):
            if i in mp: continue
            a = p[2]*p[3] or 1
            inside = max((inter(p, h)/a for h in H), default=0)   # 余分な枠のうち人の枠に入っている割合
            cover = max((inter(p, h)/(h[2]*h[3]) for h in H), default=0)  # 人の枠のうち余分な枠が覆う割合
            ov = sum(inter(p, h) for h in H)/a
            kind = ('人の枠の内側' if inside >= .8 and cover < .8 else
                    '人の枠を包む' if cover >= .8 and inside < .8 else
                    '人の枠と重ならない' if ov < .1 else 'ずれ・部分重なり')
            rows.append(dict(cond=cn, key=f['key'], canvas=f['canvas'], book=f['book_id'], i=i, box=p,
                             inside=round(inside, 3), cover=round(cover, 3), kind=kind, area=round(a/(f['width']*f['height']), 4)))
json.dump(rows, open(f'{OUT}/extra.json', 'w'), ensure_ascii=False)
for cn in ('a4', 'a5'):
    r = [x for x in rows if x['cond'] == cn]
    print(cn, len(r), Counter(x['kind'] for x in r).most_common(), 'コマ', len({x['key'] for x in r}))

# 20 コマ: 余分な枠が両条件のどちらかにあるコマから乱数で
keys = sorted({x['key'] for x in rows})
pick = random.Random(20261016).sample(keys, 20)
fm = {f['key']: f for f in frames}
os.makedirs(f'{OUT}/img', exist_ok=True)
for n, k in enumerate(pick, 1):
    f = fm[k]; im = Image.open(f'{K}/frames_test/{k}.jpg').convert('RGB'); s = im.width / f['width']
    pans = []
    for cn in ('a4', 'a5'):
        c = im.copy(); dr = ImageDraw.Draw(c)
        for h in hum[f['canvas']]:
            dr.rectangle([h[0]*s, h[1]*s, (h[0]+h[2])*s, (h[1]+h[3])*s], outline=(0, 200, 0), width=3)
        for x in rows:
            if x['key'] == k and x['cond'] == cn:
                b = x['box']; dr.rectangle([b[0]*s, b[1]*s, (b[0]+b[2])*s, (b[1]+b[3])*s], outline=(255, 0, 0), width=4)
                dr.text((b[0]*s+6, b[1]*s+4), str(x['i']), fill=(255, 0, 0))
        dr.text((8, 8), f'{cn}  #{n} {f["book_id"]}', fill=(255, 0, 255))
        pans.append(c)
    W = Image.new('RGB', (im.width*2+10, im.height), 'white'); W.paste(pans[0], (0, 0)); W.paste(pans[1], (im.width+10, 0))
    W.save(f'{OUT}/img/{n:02d}_{k}.jpg', quality=85)
json.dump(pick, open(f'{OUT}/pick20.json', 'w'))
for n, k in enumerate(pick, 1):
    print(n, k, fm[k]['book_id'], fm[k]['canvas'].rsplit('/', 1)[-1], [(x['cond'], x['i'], x['kind']) for x in rows if x['key'] == k])
