"""範囲の無いコマを乱数で選び、縮小画像を 1 枚の一覧にまとめる（目で見るため）。

    python3 -I tools/kunshujo/sample_empty_frames.py <index.json> <manifest のフォルダ> <出力フォルダ> [件数] [種]

帖の途中（範囲のある最初と最後のコマの間）にある、範囲の無いコマから選ぶ。
画像は IIIF で高さ 500 px に縮めて取る。機械の出力は重ねない。
"""
import collections, hashlib, json, os, random, sys, time, urllib.request
from PIL import Image, ImageDraw

rows = json.load(open(sys.argv[1])); mdir = sys.argv[2]; out = sys.argv[3]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 30
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 20261016
os.makedirs(out, exist_ok=True)

man_of = collections.defaultdict(set); hit = collections.defaultdict(set)
for r in rows:
    b = r['book'][0][1:r['book'][0].index(']')]
    man_of[b].add(r['manifest']); hit[b].add(r['member'].split('#')[0])

cands = []
for b in sorted(man_of):
    cs = []
    for u in sorted(man_of[b]):
        m = json.load(open(os.path.join(mdir, hashlib.md5(u.encode()).hexdigest() + '.json')))
        cs += m['sequences'][0]['canvases']
    idx = [i for i, c in enumerate(cs) if c['@id'] in hit[b]]
    for i in range(idx[0], idx[-1] + 1):
        if cs[i]['@id'] not in hit[b]:
            cands.append((b, i + 1, cs[i]['images'][0]['resource']['service']['@id']))
pick = sorted(random.Random(seed).sample(cands, min(n, len(cands))))
tiles = []
for b, k, svc in pick:
    p = os.path.join(out, f'{b}_{k:03d}.jpg')
    if not os.path.exists(p):
        open(p, 'wb').write(urllib.request.urlopen(f'{svc}/full/,500/0/default.jpg', timeout=60).read())
        time.sleep(0.5)
    tiles.append((f'{b} {k}', Image.open(p).convert('RGB')))
    print(b, k, svc)
W = 6; tw, th = 420, 330
sheet = Image.new('RGB', (W * tw, ((len(tiles) + W - 1) // W) * th), 'white')
d = ImageDraw.Draw(sheet)
for j, (lab, im) in enumerate(tiles):
    im.thumbnail((tw - 10, th - 30)); x, y = (j % W) * tw, (j // W) * th
    sheet.paste(im, (x + 5, y + 25)); d.text((x + 5, y + 5), lab, fill='black')
sheet.save(os.path.join(out, 'sheet.jpg'), quality=85)
print('candidates', len(cands), 'picked', len(pick))
