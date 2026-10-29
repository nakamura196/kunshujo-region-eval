"""著者が 50 件を盲検で判定するための画面を作る（AI の判定は載せない）

    python3 -I tools/kunshujo/make_blind50.py --index <index.json> --dir strengthening/kunshujo-eval/classify/b1-test300

1 件ごとに、同じ範囲を切り出した「人の枠だけ」「機械の枠だけ」の 2 枚と、コマ全体の位置図を作る。
枠は 1 つずつ色を変えて薄く塗るので、重なっていても区別できる。出力は <dir>/blind50/（index.html を開く）
画像が既にあれば取り直さず、ページだけを作り直す（--redraw で画像も描き直す）。画面の拡大表示は IIIF の元画像を直接読む
"""
import argparse, csv, io, json, os, sys, urllib.request
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from eval_final import load_human  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--index', required=True)
ap.add_argument('--dir', required=True)
ap.add_argument('--pred', default='strengthening/kunshujo-eval/test-pred/b1-yolo11s')
ap.add_argument('--conf', type=float, default=0.31)
ap.add_argument('--min-side', type=float, default=10)
ap.add_argument('--redraw', action='store_true', help='画像があっても描き直す')
a = ap.parse_args()

out = os.path.join(a.dir, 'blind50')
os.makedirs(os.path.join(out, 'img'), exist_ok=True)
ids = [int(r['id']) for r in csv.DictReader(open(os.path.join(a.dir, 'author50_template.tsv')), delimiter='\t')]
items = {int(r['id']): r for r in csv.DictReader(open(os.path.join(a.dir, 'items.tsv')), delimiter='\t')}
canvases = {items[i]['canvas'] for i in ids}
hum = load_human(a.index, canvases)
service = {}
for r in json.load(open(a.index)):
    can = r['member'].partition('#')[0]
    if can in canvases and can not in service:
        service[can] = r['thumbnail'].split('.tif/')[0] + '.tif'

BLUES = [(30, 90, 255), (0, 160, 220), (90, 60, 220), (0, 110, 160), (70, 140, 255)]
ORANGES = [(255, 140, 0), (220, 90, 0), (255, 190, 0), (200, 120, 40), (255, 100, 60)]


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return Image.open(io.BytesIO(r.read())).convert('RGB')


def draw(im, boxes, colors, origin, s, target, target_mine):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for k, b in enumerate(boxes):
        c = colors[k % len(colors)]
        xy = [(b[0] - origin[0]) * s, (b[1] - origin[1]) * s, (b[0] + b[2] - origin[0]) * s, (b[1] + b[3] - origin[1]) * s]
        d.rectangle(xy, fill=c + (40,), outline=c + (255,), width=4)
    t = [(target[0] - origin[0]) * s, (target[1] - origin[1]) * s, (target[0] + target[2] - origin[0]) * s, (target[1] + target[3] - origin[1]) * s]
    if target_mine:
        d.rectangle(t, outline=(230, 0, 0, 255), width=9)
    else:  # 相手側の赤枠の場所を、枠と見間違えないよう四隅のかぎ印だけで示す
        x0, y0, x1, y1 = t
        L = max(18, min(x1 - x0, y1 - y0) * 0.18)
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            d.line([cx, cy, cx + sx * L, cy], fill=(230, 0, 0, 255), width=6)
            d.line([cx, cy, cx, cy + sy * L], fill=(230, 0, 0, 255), width=6)
    return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')


data = []
for n, i in enumerate(ids, 1):
    it = items[i]
    can = it['canvas']
    pred = json.load(open(os.path.join(a.pred, __import__('hashlib').md5(can.encode()).hexdigest() + '.json')))
    W, H = pred['width'], pred['height']
    Hb = [h for h in hum[can] if min(h[2], h[3]) > a.min_side]
    Pb = [p[:4] for p in pred['boxes'] if p[4] >= a.conf]
    tgt = json.loads(it['box'])
    other = json.loads(it['other_best_box']) if it['other_best_box'] else None
    # 切り出す範囲: 赤枠と、相手側でいちばん近い枠を含め、周りに余白を足す
    xs = [tgt[0], tgt[0] + tgt[2]] + ([other[0], other[0] + other[2]] if other else [])
    ys = [tgt[1], tgt[1] + tgt[3]] + ([other[1], other[1] + other[3]] if other else [])
    mx = max(0.35 * (max(xs) - min(xs)), 0.06 * W)
    my = max(0.35 * (max(ys) - min(ys)), 0.06 * H)
    x0, y0 = max(0, min(xs) - mx), max(0, min(ys) - my)
    x1, y1 = min(W, max(xs) + mx), min(H, max(ys) + my)
    region = f"{int(tgt[0])},{int(tgt[1])},{int(tgt[2])},{int(tgt[3])}"
    data.append({'n': n, 'id': i, 'kind': it['kind'], 'book': it['book_id'], 'canvas': can, 'region': region,
                 'service': service[can], 'W': W, 'H': H, 'target': tgt, 'crop': [x0, y0, x1 - x0, y1 - y0],
                 'human': [[round(v) for v in b] for b in Hb], 'machine': [[round(v) for v in b] for b in Pb]})
    print(n, i, it['kind'], len(Hb), len(Pb), file=sys.stderr)
    if os.path.exists(os.path.join(out, 'img', f'{n:02d}-page.jpg')) and not a.redraw:
        continue
    cw = 1100
    crop = fetch(f"{service[can]}/{int(x0)},{int(y0)},{int(x1 - x0)},{int(y1 - y0)}/{cw},/0/default.jpg")
    s = crop.size[0] / (x1 - x0)
    mine_h = it['kind'] == 'human'
    draw(crop, Hb, BLUES, (x0, y0), s, tgt, mine_h).save(os.path.join(out, 'img', f'{n:02d}-human.jpg'), quality=88)
    draw(crop, Pb, ORANGES, (x0, y0), s, tgt, not mine_h).save(os.path.join(out, 'img', f'{n:02d}-machine.jpg'), quality=88)
    full = fetch(f"{service[can]}/full/900,/0/default.jpg")
    fs = full.size[0] / W
    d = ImageDraw.Draw(full)
    d.rectangle([x0 * fs, y0 * fs, x1 * fs, y1 * fs], outline=(120, 120, 120), width=2)
    d.rectangle([tgt[0] * fs, tgt[1] * fs, (tgt[0] + tgt[2]) * fs, (tgt[1] + tgt[3]) * fs], outline=(230, 0, 0), width=4)
    full.save(os.path.join(out, 'img', f'{n:02d}-page.jpg'), quality=85)

html = open(os.path.join(os.path.dirname(__file__), 'blind50_template.html')).read()
open(os.path.join(out, 'index.html'), 'w').write(html.replace('/*DATA*/[]', json.dumps(data, ensure_ascii=False)))
print('wrote', out, len(data))
