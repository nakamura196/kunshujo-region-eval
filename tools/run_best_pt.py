"""dev の帖のコマに、既存の YOLOv5 重み best.pt を流して範囲を予測する。

    python3 -I tools/kunshujo/run_best_pt.py frames  --index <index.json> --split <split.tsv> --manifests <フォルダ> --out <frames.json>
    python3 -I tools/kunshujo/run_best_pt.py fetch   --frames <frames.json> --cache <frames_dev/> [--limit N]
    python3 -I tools/kunshujo/run_best_pt.py infer   --frames <frames.json> --cache <frames_dev/> --yolov5 <v7.0 の clone> --weights <best.pt> --out <pred/> [--limit N] [--size 640] [--device cpu|mps]

決まり:
  - 確かめる帖 (split=test) の画像は取得も推論もしない。frames で split=='dev' に絞り、
    fetch / infer でも frames.json に載っているコマだけを扱う (frames.json に test は入らない)。
  - 画像は IIIF の <service>/full/1024,/0/default.jpg (幅 1024)。既存のファイルは取り直さない。
    並列 2、間隔 0.4 秒。
  - 推論は HF Space の app.py に合わせる: torch.hub 相当 (v7.0, custom) の AutoShape に画像を渡す。
    app.py は max 辺 1024 に縮めて model(im) を呼ぶので、AutoShape の既定 size=640 で動く。
    確信度は 0.05 で全部保存 (iou は NMS 0.45)。
  - 枠は canvas の原寸座標 [x, y, w, h, conf] に直す (canvas の幅 / 画像の幅)。
"""
import argparse, collections, csv, hashlib, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor


def canvases(man):
    for c in man['sequences'][0]['canvases']:
        yield c['@id'], c['width'], c['height'], c['images'][0]['resource']['service']['@id']


def cmd_frames(a):
    split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
    rows = json.load(open(a.index))
    frames = collections.OrderedDict()
    mans = collections.defaultdict(set)
    for r in rows:
        b = r['book'][0][1:r['book'][0].index(']')]
        if split[b]['split'] != 'dev':
            continue
        can, _, frag = r['member'].partition('#xywh=')
        if not frag:
            continue
        mans[b].add(r['manifest'])
        frames.setdefault(can, {'canvas': can, 'book_id': b})
    info = {}
    for b, us in mans.items():
        for u in us:
            m = json.load(open(os.path.join(a.manifests, hashlib.md5(u.encode()).hexdigest() + '.json')))
            for cid, w, h, svc in canvases(m):
                info[cid] = (w, h, svc)
    out, miss = [], 0
    for can, f in frames.items():
        if can not in info:
            miss += 1
            continue
        f['width'], f['height'], f['service'] = info[can]
        f['key'] = hashlib.md5(can.encode()).hexdigest()
        out.append(f)
    assert all(f['book_id'] in split and split[f['book_id']]['split'] == 'dev' for f in out)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False)
    print('dev frames', len(out), 'unmatched canvases', miss, 'books', len({f['book_id'] for f in out}))


def sel(a):
    fr = json.load(open(a.frames))
    return fr[:a.limit] if a.limit else fr


def cmd_fetch(a):
    os.makedirs(a.cache, exist_ok=True)
    fr = [f for f in sel(a) if not os.path.exists(os.path.join(a.cache, f['key'] + '.jpg'))]
    print('to fetch', len(fr), flush=True)
    fails = []

    def one(f):
        p = os.path.join(a.cache, f['key'] + '.jpg')
        url = f['service'] + '/full/1024,/0/default.jpg'
        for t in range(3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'kunshujo-eval/1.0 (research)'})
                d = urllib.request.urlopen(req, timeout=60).read()
                if len(d) < 1000 or d[:2] != b'\xff\xd8':  # 空・JPEG でない応答は失敗として扱う
                    raise ValueError('bad image response, %d bytes' % len(d))
                open(p + '.part', 'wb').write(d)
                os.replace(p + '.part', p)
                time.sleep(0.4)
                return True
            except Exception as e:
                err = str(e)
                time.sleep(2 * (t + 1))
        fails.append((f['canvas'], err))
        return False
    n = 0
    with ThreadPoolExecutor(2) as ex:
        for ok in ex.map(one, fr):
            n += 1
            if n % 100 == 0:
                print(n, 'done', 'fails', len(fails), flush=True)
    print('finished; fails', len(fails))
    json.dump(fails, open(os.path.join(a.cache, '_fails.json'), 'w'))


def cmd_infer(a):
    import torch
    from PIL import Image
    ol = torch.load
    torch.load = lambda *x, **k: ol(*x, **{**k, 'weights_only': False})
    model = torch.hub.load(a.yolov5, 'custom', path=a.weights, source='local', device=a.device)
    torch.load = ol
    model.conf = 0.05
    model.iou = 0.45
    model.max_det = 300
    os.makedirs(a.out, exist_ok=True)
    n = skip = miss = 0
    bad = []
    t0 = time.time()
    for f in sel(a):
        o = os.path.join(a.out, f['key'] + '.json')
        p = os.path.join(a.cache, f['key'] + '.jpg')
        if os.path.exists(o):
            skip += 1
            continue
        if not os.path.exists(p):
            miss += 1
            continue
        try:
            im = Image.open(p).convert('RGB')
        except Exception as e:  # 壊れた画像は飛ばして数える (fetch を取り直す)
            bad.append(f['canvas'])
            print('bad image', f['key'], e, flush=True)
            continue
        g = 1024 / max(im.size)  # app.py と同じ: max 辺 1024 に
        im2 = im.resize(tuple(int(x * g) for x in im.size), Image.BICUBIC)
        r = model(im2, size=a.size).xyxy[0].cpu().numpy()
        sc = f['width'] / im2.size[0]  # canvas 原寸 / 推論に渡した画像の幅
        boxes = [[round(float(x1 * sc), 1), round(float(y1 * sc), 1), round(float((x2 - x1) * sc), 1),
                  round(float((y2 - y1) * sc), 1), round(float(c), 4)] for x1, y1, x2, y2, c, _ in r]
        json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': f['width'], 'height': f['height'],
                   'infer_size': a.size, 'boxes': boxes}, open(o, 'w'), ensure_ascii=False)
        n += 1
        if n % 200 == 0:
            print(n, 'inferred', round(time.time() - t0), 's', flush=True)
    print('inferred', n, 'skipped(existing)', skip, 'no image', miss, 'bad image', len(bad))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest='cmd', required=True)
for name, args in {'frames': ['index', 'split', 'manifests', 'out'], 'fetch': ['frames', 'cache'],
                   'infer': ['frames', 'cache', 'yolov5', 'weights', 'out']}.items():
    p = sp.add_parser(name)
    for x in args:
        p.add_argument('--' + x, required=True)
    if name != 'frames':
        p.add_argument('--limit', type=int, default=0)
    if name == 'infer':
        p.add_argument('--size', type=int, default=640)
        p.add_argument('--device', default='cpu')
a = ap.parse_args()
{'frames': cmd_frames, 'fetch': cmd_fetch, 'infer': cmd_infer}[a.cmd](a)
