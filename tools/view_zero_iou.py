"""確認 3: IoU 0 の 3 コマの全体図に、人の範囲（赤）を描いて並べる。 python3 view_zero_iou.py <regions.tsv> <manifestフォルダ> <出力jpg>"""
import csv, json, os, sys, time, urllib.request
from PIL import Image, ImageDraw
T = [('7529b21b', 'p87'), ('a9055dc2', 'p145'), ('173cf4f6', 'p24')]
R = list(csv.DictReader(open(sys.argv[1]), delimiter='\t')); svc = {}; size = {}
for f in os.listdir(sys.argv[2]):
    for c in json.load(open(os.path.join(sys.argv[2], f)))['sequences'][0]['canvases']: svc[c['@id']] = c['images'][0]['resource']['service']['@id']; size[c['@id']] = (c['width'], c['height'])
tiles = []
for u, p in T:
    can = [c for c in svc if f'/{u}' in c and c.endswith('/canvas/' + p)][0]
    im = Image.open(urllib.request.urlopen(f'{svc[can]}/full/,700/0/default.jpg', timeout=60)).convert('RGB'); time.sleep(0.5)
    s = im.height / size[can][1]; d = ImageDraw.Draw(im)
    for r in R:
        if r['canvas'] == can:
            x, y, w, h = (float(r[k]) * s for k in 'xywh'); d.ellipse([x-12, y-12, x+w+12, y+h+12], outline='red', width=3); print(u, p, r['x'], r['y'], r['w'], r['h'], r['book'])
    tiles.append(im)
sh = Image.new('RGB', (sum(t.width for t in tiles), 700), 'white'); x = 0
for t in tiles: sh.paste(t, (x, 0)); x += t.width
sh.save(sys.argv[3], quality=85)
