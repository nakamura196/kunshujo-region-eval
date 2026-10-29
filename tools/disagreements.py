"""1 つの条件の食い違い（IoU 0.5 で対応しなかった人の範囲と機械の範囲）から乱数で選び、分類用の画像を作る。

    python3 -I tools/kunshujo/disagreements.py --index <index.json> --split <split.tsv> --frames <frames.json> --pred <予測フォルダ> --conf 0.31 --cache <画像フォルダ> --out <出力フォルダ> [--n 300] [--seed 20261016] [--min-side 10] [--allow-test]

決まり:
  - 一致の取り方は eval_final.py と同じ（コマごとに IoU の大きい順の貪欲法で 1 対 1、IoU 0.5）。
  - 食い違い = 対応しなかった人の範囲（kind=human）と、対応しなかった機械の範囲（kind=machine）。
    全部を (canvas, kind, 番号) の順に並べてから random.Random(seed).sample で選ぶ。機械が間違えたかどうかで選ばない。
  - 画像: コマ全体（幅 1024）に、人の範囲を青、機械の範囲を橙で細く描き、対象の 1 つを赤の太線で描く。
    どの条件の出力かは画像に書かない。
  - items.tsv: 番号、コマ、帖、kind、対象の枠、相手側で IoU が最大の枠とその IoU。
"""
import argparse, csv, json, os, random, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_final import load_human, match, iou  # noqa: E402

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'frames', 'pred', 'cache', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--conf', type=float, required=True)
ap.add_argument('--n', type=int, default=300)
ap.add_argument('--seed', type=int, default=20261016)
ap.add_argument('--min-side', type=float, default=10)
ap.add_argument('--allow-test', action='store_true')
a = ap.parse_args()

split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
frames = json.load(open(a.frames))
if any(split[f['book_id']]['split'] == 'test' for f in frames) and not a.allow_test:
    sys.exit('確かめる帖のコマが入っている。数字を確定させた後にだけ --allow-test を付けて流す')
hum = load_human(a.index, {f['canvas'] for f in frames})
items = []
for f in frames:
    H = [h for h in hum[f['canvas']] if min(h[2], h[3]) > a.min_side]
    if not H:
        continue
    P = [p[:4] for p in json.load(open(os.path.join(a.pred, f['key'] + '.json')))['boxes'] if p[4] >= a.conf]
    m = match(P, H, 0.5)
    mp, mh = {i for i, _, _ in m}, {j for _, j, _ in m}
    for j, h in enumerate(H):
        if j not in mh:
            items.append((f, 'human', j, h, P))
    for i, p in enumerate(P):
        if i not in mp:
            items.append((f, 'machine', i, p, H))
items.sort(key=lambda t: (t[0]['canvas'], t[1], t[2]))
pick = random.Random(a.seed).sample(items, min(a.n, len(items)))
os.makedirs(os.path.join(a.out, 'img'), exist_ok=True)
w = csv.writer(open(os.path.join(a.out, 'items.tsv'), 'w'), delimiter='\t')
w.writerow(['id', 'canvas', 'book_id', 'kind', 'box', 'other_best_box', 'other_best_iou'])
for n, (f, kind, k, box, other) in enumerate(pick, 1):
    im = Image.open(os.path.join(a.cache, f['key'] + '.jpg')).convert('RGB')
    s = im.size[0] / f['width']
    d = ImageDraw.Draw(im)
    for h in hum[f['canvas']]:
        if min(h[2], h[3]) > a.min_side:
            d.rectangle([h[0] * s, h[1] * s, (h[0] + h[2]) * s, (h[1] + h[3]) * s], outline=(30, 90, 255), width=2)
    for p in json.load(open(os.path.join(a.pred, f['key'] + '.json')))['boxes']:
        if p[4] >= a.conf:
            d.rectangle([p[0] * s, p[1] * s, (p[0] + p[2]) * s, (p[1] + p[3]) * s], outline=(255, 150, 0), width=2)
    d.rectangle([box[0] * s, box[1] * s, (box[0] + box[2]) * s, (box[1] + box[3]) * s], outline=(230, 0, 0), width=6)
    im.save(os.path.join(a.out, 'img', f'{n:03d}.jpg'), quality=88)
    best = max(other, key=lambda o: iou(box, o), default=None)
    w.writerow([n, f['canvas'], f['book_id'], kind, json.dumps([round(v) for v in box]),
                json.dumps([round(v) for v in best]) if best else '', round(iou(box, best), 3) if best else 0])
print('disagreements', len(items), 'human', sum(t[1] == 'human' for t in items), 'machine', sum(t[1] == 'machine' for t in items), 'picked', len(pick))
