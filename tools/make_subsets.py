"""学習曲線用に、学習の帖 38 帖から入れ子の部分集合 (5・10・19・38 帖) を作る。

    python3 -I tools/kunshujo/make_subsets.py --dev-tune <dev-tune.tsv> --yolo <yolo-dev/> --out-tsv <subsets.tsv>

決まり (docs/notes/kunshujo-eval.md 改訂 3):
  - 学習の帖を group A / B に分け、それぞれ ID を並べて random.Random(20261016).shuffle (グループごとに乱数を作り直す)。
  - n 帖のとき、A は round-half-up(n * |A| / 38) 帖、B は残りを、それぞれの並べ替えの先頭から取る。入れ子になる。
  - <yolo>/images/train の画像のうち該当する帖のものを列挙した <yolo>/train-<n>.txt と、
    それを使う <yolo>/data-<n>.yaml (検証は同じ tune) を書く。帖は dev_frames から引くので --frames も要る。
"""
import argparse, csv, json, math, os, random

ap = argparse.ArgumentParser()
for k in ('dev-tune', 'yolo', 'out-tsv', 'frames'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
rows = [r for r in csv.DictReader(open(a.dev_tune), delimiter='\t') if r['role'] == 'train']
order = {}
for g in ('A', 'B'):
    ids = sorted(r['book_id'] for r in rows if r['group'] == g)
    random.Random(20261016).shuffle(ids)
    order[g] = ids
N = len(rows)
key2book = {f['key']: f['book_id'] for f in json.load(open(a.frames))}
tr = os.path.join(a.yolo, 'images', 'train')
imgs = sorted(os.listdir(tr))
out = ['n\tgroup\tbook_ids']
for n in (5, 10, 19, 38):
    na = math.floor(n * len(order['A']) / N + 0.5)
    sel = order['A'][:na] + order['B'][:n - na]
    out.append(f"{n}\tA={na},B={n - na}\t{','.join(sel)}")
    s = set(sel)
    lst = [os.path.abspath(os.path.join(tr, i)) for i in imgs if key2book[i[:-4]] in s]
    open(os.path.join(a.yolo, f'train-{n}.txt'), 'w').write('\n'.join(lst) + '\n')
    open(os.path.join(a.yolo, f'data-{n}.yaml'), 'w').write(
        f"path: {os.path.abspath(a.yolo)}\ntrain: {os.path.abspath(os.path.join(a.yolo, f'train-{n}.txt'))}\nval: images/val\nnames:\n  0: region\n")
    print(n, na, n - na, len(lst), 'images')
open(a.out_tsv, 'w').write('\n'.join(out) + '\n')
