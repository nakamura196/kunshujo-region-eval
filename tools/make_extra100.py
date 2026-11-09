"""Gemini（a4）の余分な枠から 100 枠を無作為に抜き、著者が判定する画面を作る（Claude の 20 コマの判定は載せない）

    python3 -I tools/kunshujo/make_extra100.py
    python3 -I tools/kunshujo/blind50_server.py ~/git/tmp/k42gen/det3/extra100 extra100_author.tsv 8768

学習し直した YOLOv5（b0、確信度 0.52）の余分な枠（237）から 50 枠を抜くとき（11-03、公平に比べるため）:

    python3 -I tools/kunshujo/make_extra100.py --cond b0 --n 50
    python3 -I tools/kunshujo/blind50_server.py ~/git/tmp/k42gen/det3/extra-b0 extra-b0_author.tsv 8769

b0 の余分な枠のうち 164 は Gemini の余分な枠と同じ場所（IoU 0.7 以上）にあるので、残りの 73 だけを全部判定する（11-03 に切り替え）:

    python3 -I tools/kunshujo/make_extra100.py --cond b0 --unshared
    python3 -I tools/kunshujo/blind50_server.py ~/git/tmp/k42gen/det3/extra-b0only extra-b0only_author.tsv 8769

余分な枠は gen_extra_boxes.py の extra.json（300 コマ、IoU 0.5 で人の枠に対応しない a4 の枠 518）。
枠単位で random.Random(20261103).sample の 100 枠。1 件ごとに、同じ範囲を切り出した「人の枠だけ」「機械の枠だけ」の
2 枚と、コマ全体の位置図を作る（blind50 と同じ描き方）。出力は ~/git/tmp/k42gen/det3/extra100/（index.html を開く）
画像が既にあれば取り直さない（--redraw で描き直す）。
"""
import argparse, io, json, os, random, sys, urllib.request
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from eval_final import load_human  # noqa: E402

K = os.path.expanduser('~/git/tmp/k42gen')
ap = argparse.ArgumentParser()
ap.add_argument('--cond', choices=['a4', 'b0'], default='a4')
ap.add_argument('--out')
ap.add_argument('--n', type=int, default=100)
ap.add_argument('--seed', type=int, default=20261103)
ap.add_argument('--redraw', action='store_true')
ap.add_argument('--unshared', action='store_true', help='b0: Gemini の余分な枠と IoU 0.7 以上で重なるものを除き、残りを全部載せる')
a = ap.parse_args()

# 描き方は make_blind50.py と同じ
BLUES = [(30, 90, 255), (0, 160, 220), (90, 60, 220), (0, 110, 160), (70, 140, 255)]
ORANGES = [(255, 140, 0), (220, 90, 0), (255, 190, 0), (200, 120, 40), (255, 100, 60)]


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


tag = 'extra100' if a.cond == 'a4' else f'extra-{a.cond}' + ('only' if a.unshared else '')
out = a.out or f'{K}/det3/{tag}'
os.makedirs(os.path.join(out, 'img'), exist_ok=True)
frames = {f['key']: f for f in json.load(open(f'{K}/test_frames.json'))}
INDEX = os.path.expanduser('~/git/utda/kunshujo/static/data/index.json')
B0 = os.path.join(os.path.dirname(__file__), '../../strengthening/kunshujo-eval/test-pred/b0-yolov5x')


def pred_boxes(key):
    if a.cond == 'a4':
        return [b[:4] for b in json.load(open(f'{K}/det3/pred-gemini/{key}.json'))['boxes']]
    return [b[:4] for b in json.load(open(f'{B0}/{key}.json'))['boxes'] if b[4] >= 0.52]  # config-sub300-v5gen.json の b0


if a.cond == 'a4':
    rows = [r for r in json.load(open(f'{K}/det3/extra20/extra.json')) if r['cond'] == 'a4']
    assert len(rows) == 518, len(rows)
else:  # gen_extra_boxes.py と同じ数え方（300 コマ、人の枠は 10 画素以下の辺を除く、IoU 0.5 で 1 対 1）
    from eval_final import match  # noqa: E402
    keep = set(json.load(open(f'{K}/test300_canvases.json')))
    hall = load_human(INDEX, keep)
    rows = []
    for f in frames.values():
        if f['canvas'] not in keep:
            continue
        H = [h for h in hall[f['canvas']] if min(h[2], h[3]) > 10]
        if not H:
            continue
        P = pred_boxes(f['key'])
        mp = {i for i, _, _ in match(P, H, 0.5)}
        rows += [dict(key=f['key'], canvas=f['canvas'], book=f['book_id'], i=i, box=p, kind='-')
                 for i, p in enumerate(P) if i not in mp]
    assert len(rows) == 237, len(rows)
    if a.unshared:
        from eval_final import iou as iou_  # noqa: E402
        ga = [r for r in json.load(open(f'{K}/det3/extra20/extra.json')) if r['cond'] == 'a4']
        rows = [r for r in rows if not any(g['key'] == r['key'] and iou_(r['box'], g['box']) >= 0.7 for g in ga)]
        assert len(rows) == 73, len(rows)
        a.n = len(rows)  # 全部を、並べ順だけ乱数で
pick = random.Random(a.seed).sample(range(len(rows)), a.n)
canvases = {rows[i]['canvas'] for i in pick}
hum = load_human(INDEX, canvases)


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return Image.open(io.BytesIO(r.read())).convert('RGB')


def iou(p, q):
    x1, y1 = max(p[0], q[0]), max(p[1], q[1])
    x2, y2 = min(p[0] + p[2], q[0] + q[2]), min(p[1] + p[3], q[1] + q[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    return i / (p[2] * p[3] + q[2] * q[3] - i or 1)


def dist(p, q):
    return ((p[0] + p[2] / 2 - q[0] - q[2] / 2) ** 2 + (p[1] + p[3] / 2 - q[1] - q[3] / 2) ** 2) ** .5


data, keyrows = [], []
for n, i in enumerate(pick, 1):
    r = rows[i]
    f = frames[r['key']]
    W, H, svc = f['width'], f['height'], f['service']
    Hb = [h for h in hum[r['canvas']] if min(h[2], h[3]) > 10]
    Pb = pred_boxes(r['key'])
    tgt = r['box']
    # 切り出す範囲: 赤枠と、人の枠でいちばん重なるもの（重ならなければいちばん近いもの）を含め、周りに余白を足す
    other = max(Hb, key=lambda h: (iou(tgt, h), -dist(tgt, h))) if Hb else None
    xs = [tgt[0], tgt[0] + tgt[2]] + ([other[0], other[0] + other[2]] if other else [])
    ys = [tgt[1], tgt[1] + tgt[3]] + ([other[1], other[1] + other[3]] if other else [])
    mx = max(0.35 * (max(xs) - min(xs)), 0.06 * W)
    my = max(0.35 * (max(ys) - min(ys)), 0.06 * H)
    x0, y0 = max(0, min(xs) - mx), max(0, min(ys) - my)
    x1, y1 = min(W, max(xs) + mx), min(H, max(ys) + my)
    iid = f"{r['key'][:8]}-{r['i']}"
    data.append({'n': n, 'id': iid, 'kind': 'machine', 'book': r['book'], 'canvas': r['canvas'], 'service': svc,
                 'W': W, 'H': H, 'target': tgt, 'crop': [x0, y0, x1 - x0, y1 - y0],
                 'human': [[round(v) for v in b] for b in Hb], 'machine': [[round(v) for v in b] for b in Pb]})
    keyrows.append([iid, r['key'], r['book'], r['canvas'], r['i'], json.dumps(tgt), r['kind']])
    print(n, iid, r['book'], len(Hb), len(Pb), file=sys.stderr)
    if os.path.exists(os.path.join(out, 'img', f'{n:03d}-page.jpg')) and not a.redraw:
        continue
    crop = fetch(f"{svc}/{int(x0)},{int(y0)},{int(x1 - x0)},{int(y1 - y0)}/1100,/0/default.jpg")
    s = crop.size[0] / (x1 - x0)
    draw(crop, Hb, BLUES, (x0, y0), s, tgt, False).save(os.path.join(out, 'img', f'{n:03d}-human.jpg'), quality=88)
    draw(crop, Pb, ORANGES, (x0, y0), s, tgt, True).save(os.path.join(out, 'img', f'{n:03d}-machine.jpg'), quality=88)
    full = fetch(f"{svc}/full/900,/0/default.jpg")
    fs = full.size[0] / W
    d = ImageDraw.Draw(full)
    d.rectangle([x0 * fs, y0 * fs, x1 * fs, y1 * fs], outline=(120, 120, 120), width=2)
    d.rectangle([tgt[0] * fs, tgt[1] * fs, (tgt[0] + tgt[2]) * fs, (tgt[1] + tgt[3]) * fs], outline=(230, 0, 0), width=4)
    full.save(os.path.join(out, 'img', f'{n:03d}-page.jpg'), quality=85)

# 抜いた枠の一覧（判定とは別のファイル。機械で付けた形の分け方は画面に出さない）
with open(os.path.join(out, 'items.tsv'), 'w') as fo:
    fo.write('id\tkey\tbook_id\tcanvas\tbox_index\tbox\tgeom_kind\n')
    for k in keyrows:
        fo.write('\t'.join(map(str, k)) + '\n')
html = open(os.path.join(os.path.dirname(__file__), 'extra100_template.html')).read()
if a.cond != 'a4':  # 判定の保存先（ブラウザ内・TSV・保存係のポート）を Gemini の画面と分ける
    html = (html.replace('100件', f'{a.n}件').replace('100 件', f'{a.n} 件').replace('kunshujo-extra100-v1', f'kunshujo-{tag}-v1')
            .replace('127.0.0.1:8768', '127.0.0.1:8769').replace('extra100_author.tsv', f'{tag}_author.tsv'))
open(os.path.join(out, 'index.html'), 'w').write(html.replace('/*DATA*/[]', json.dumps(data, ensure_ascii=False)))
print('wrote', out, len(data), 'コマ', len({d['canvas'] for d in data}))
