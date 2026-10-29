"""確認 3: compare_kld.py と同じ対応づけで、IoU が 0 の組を含む画像を挙げる。
    python3 -I kld_zero_iou.py dataset.json index.json
"""
import json, sys, hashlib
from collections import defaultdict
d = json.load(open(sys.argv[1])); rows = json.load(open(sys.argv[2]))
img = {i['id']: i for i in d['images']}
ds = defaultdict(list)
for a in d['annotations']: ds[a['image_id']].append(a['bbox'])
hu = defaultdict(list); canon = {}
for r in rows:
    can, _, frag = r['member'].partition('#xywh=')
    if frag: k = hashlib.md5(can.encode()).hexdigest(); hu[k].append([float(v) for v in frag.split(',')]); canon[k] = can
def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1]); x2, y2 = min(a[0]+a[2], b[0]+b[2]), min(a[1]+a[3], b[1]+b[3])
    i = max(0, x2-x1)*max(0, y2-y1); u = a[2]*a[3]+b[2]*b[3]-i; return i/u if u else 0
def match(A, B):
    pairs = sorted(((iou(a, b), i, j) for i, a in enumerate(A) for j, b in enumerate(B)), reverse=True)
    ua, ub, res = set(), set(), []
    for v, i, j in pairs:
        if i in ua or j in ub or v <= 0: continue
        ua.add(i); ub.add(j); res.append((v, i, j))
    return res
for iid, boxes in ds.items():
    im = img[iid]; k = im['file_name'].rsplit('.', 1)[0].split('/')[-1]; H = hu.get(k)
    if not H: continue
    best = (-1,)
    for s in [x/1000 for x in range(1000, 12001, 5)]:
        m = match(boxes, [[v/s for v in b] for b in H]); sc = sum(v for v, _, _ in m)
        if sc > best[0]: best = (sc, s, m)
    sc, s, m = best
    if sc == 0 or len(m) < min(len(boxes), len(H)):
        print(k, canon[k], 'img', im['width'], im['height'], 'scale', s, 'ds', len(boxes), 'human', len(H), 'matched', len(m))
        print('  ds boxes', boxes[:4]); print('  human/scale', [[round(v/s, 1) for v in b] for b in H[:4]]); print('  human raw', H[:4])
