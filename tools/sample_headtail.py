"""確認 4: 帖の頭・尻の範囲の無いコマ（318）から 30 を乱数で選び、一覧にする。
    python3 tools/kunshujo/sample_headtail.py <index.json> <manifestフォルダ> <出力フォルダ>
frame_coverage.py と同じ定義: 範囲のある最初のコマより前、最後のコマより後。種 20261016。
"""
import collections, hashlib, json, os, random, sys, time, urllib.request
from PIL import Image, ImageDraw
rows = json.load(open(sys.argv[1])); mdir = sys.argv[2]; out = sys.argv[3]; os.makedirs(out, exist_ok=True)
man_of = collections.defaultdict(set); hit = collections.defaultdict(set)
for r in rows:
    b = r['book'][0][1:r['book'][0].index(']')]; man_of[b].add(r['manifest']); hit[b].add(r['member'].split('#')[0])
cands = []
for b in sorted(man_of):
    cs = []
    for u in sorted(man_of[b]):
        cs += json.load(open(os.path.join(mdir, hashlib.md5(u.encode()).hexdigest() + '.json')))['sequences'][0]['canvases']
    idx = [i for i, c in enumerate(cs) if c['@id'] in hit[b]]
    for i in list(range(0, idx[0])) + list(range(idx[-1] + 1, len(cs))):
        cands.append((b, i + 1, 'head' if i < idx[0] else 'tail', cs[i]['images'][0]['resource']['service']['@id']))
print('candidates', len(cands))
pick = sorted(random.Random(20261016).sample(cands, 30))
tiles = []
for n, (b, k, ht, svc) in enumerate(pick):
    p = f'{out}/{b}_{k:03d}.jpg'
    if not os.path.exists(p):
        open(p, 'wb').write(urllib.request.urlopen(f'{svc}/full/,500/0/default.jpg', timeout=60).read()); time.sleep(0.5)
    tiles.append((f'{n} {b} {k} {ht}', Image.open(p).convert('RGB'))); print(n, b, k, ht)
W = 6; tw, th = 340, 300
sh = Image.new('RGB', (W*tw, 5*th), 'white'); d = ImageDraw.Draw(sh)
for j, (lab, im) in enumerate(tiles):
    im.thumbnail((tw-10, th-30)); x, y = (j % W)*tw, (j//W)*th; sh.paste(im, (x+5, y+25)); d.text((x+5, y+5), lab, fill='black')
sh.save(f'{out}/sheet.jpg', quality=85)
