"""dev の帖のコマから YOLO 形式のデータを作る (学習 = train の帖、検証 = tune の帖)。

    python3 -I tools/kunshujo/make_yolo_dev.py --index <index.json> --split <split.tsv> --dev-tune <dev-tune.tsv> --frames <frames.json> --cache <frames_dev/> --out <yolo-dev/>

決まり:
  - split=='dev' の帖だけ。test の帖は frames.json に入っていないことを確かめる。
  - 画像は cache の幅 1024 の jpg へのシンボリックリンク。cache に無いコマは数えて飛ばす。
  - ラベルは class 0 (貼り込み)、cx cy w h を canvas の幅・高さで割った値。
"""
import argparse, csv, json, os
from collections import defaultdict

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'dev-tune', 'frames', 'cache', 'out'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
split = {r['book_id']: r['split'] for r in csv.DictReader(open(a.split), delimiter='\t')}
role = {r['book_id']: r['role'] for r in csv.DictReader(open(a.dev_tune), delimiter='\t')}
fr = json.load(open(a.frames))
assert all(split[f['book_id']] == 'dev' for f in fr)
fr = {f['canvas']: f for f in fr}
hum = defaultdict(list)
for r in json.load(open(a.index)):
    can, _, frag = r['member'].partition('#xywh=')
    if can in fr and frag:
        hum[can].append([float(v) for v in frag.split(',')])
cnt = defaultdict(int)
miss = 0
for can, f in fr.items():
    src = os.path.abspath(os.path.join(a.cache, f['key'] + '.jpg'))
    if not os.path.exists(src):
        miss += 1
        continue
    s = 'train' if role[f['book_id']] == 'train' else 'val'
    di, dl = (os.path.join(a.out, x, s) for x in ('images', 'labels'))
    os.makedirs(di, exist_ok=True); os.makedirs(dl, exist_ok=True)
    link = os.path.join(di, f['key'] + '.jpg')
    if not os.path.lexists(link):
        os.symlink(src, link)
    W, H = f['width'], f['height']
    lines = []
    for x, y, w, h in hum[can]:
        x1, y1, x2, y2 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x2 <= x1 or y2 <= y1:
            continue
        lines.append(f"0 {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}")
    open(os.path.join(dl, f['key'] + '.txt'), 'w').write('\n'.join(lines) + '\n')
    cnt[s] += 1
    cnt[s + '_boxes'] += len(lines)
open(os.path.join(a.out, 'data.yaml'), 'w').write(
    f"path: {os.path.abspath(a.out)}\ntrain: images/train\nval: images/val\nnames:\n  0: region\n")
print(dict(cnt), 'missing images', miss)
