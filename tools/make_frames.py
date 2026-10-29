"""帖の分け（dev / test）を指定して、コマの一覧 (frames.json) を作る。run_best_pt.py frames と同じ中身。

    python3 -I tools/kunshujo/make_frames.py --index <index.json> --split <split.tsv> --manifests <フォルダ> --role test --out <frames.json>

確かめる帖の一覧は、画像の取得（run_best_pt.py fetch）と、設定を固めた後の推論にだけ使う。画像を目で見ない。
"""
import argparse, collections, csv, hashlib, json, os

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'manifests', 'role', 'out'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
frames, mans = collections.OrderedDict(), collections.defaultdict(set)
for r in json.load(open(a.index)):
    b = r['book'][0][1:r['book'][0].index(']')]
    if split[b]['split'] != a.role:
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
        for c in m['sequences'][0]['canvases']:
            info[c['@id']] = (c['width'], c['height'], c['images'][0]['resource']['service']['@id'])
out, miss = [], 0
for can, f in frames.items():
    if can not in info:
        miss += 1
        continue
    f['width'], f['height'], f['service'] = info[can]
    f['key'] = hashlib.md5(can.encode()).hexdigest()
    out.append(f)
json.dump(out, open(a.out, 'w'), ensure_ascii=False)
print(a.role, 'frames', len(out), 'unmatched', miss, 'books', len({f['book_id'] for f in out}))
