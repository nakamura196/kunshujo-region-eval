"""確認 2: 範囲 30 点を乱数で選び、IIIF で切り出して一覧にする。
    python3 tools/kunshujo/sample_regions.py <regions.tsv> <manifestフォルダ> <出力フォルダ>
"""
import csv, json, os, random, sys, time, urllib.request
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
R = list(csv.DictReader(open(sys.argv[1]), delimiter='\t')); mdir = sys.argv[2]; out = sys.argv[3]; os.makedirs(out, exist_ok=True)
svc = {}
for f in os.listdir(mdir):
    m = json.load(open(os.path.join(mdir, f)))
    for c in m['sequences'][0]['canvases']: svc[c['@id']] = c['images'][0]['resource']['service']['@id']
R.sort(key=lambda r: (r['canvas'], float(r['x']), float(r['y']), float(r['w']), float(r['h'])))
pick = random.Random(20261016).sample(R, 30)
tiles = []
for i, r in enumerate(pick):
    x, y, w, h = (int(float(r[k])) for k in 'xywh'); p = f'{out}/r{i:02d}.jpg'
    if not os.path.exists(p):
        open(p, 'wb').write(urllib.request.urlopen(f'{svc[r["canvas"]]}/{x},{y},{w},{h}/,300/0/default.jpg', timeout=90).read()); time.sleep(0.5)
    tiles.append((f'{i} {r["book"]} {r["canvas"].split("/")[-1]} {w}x{h}', Image.open(p).convert('RGB')))
    print(i, r['book'], r['canvas'].split('/')[-1], x, y, w, h)
W = 6; tw, th = 340, 380
sh = Image.new('RGB', (W*tw, 5*th), 'white'); d = ImageDraw.Draw(sh)
for j, (lab, im) in enumerate(tiles):
    im.thumbnail((tw-10, th-30)); x, y = (j % W)*tw, (j//W)*th; sh.paste(im, (x+5, y+25)); d.text((x+5, y+5), lab, fill='black')
sh.save(f'{out}/sheet.jpg', quality=85)
