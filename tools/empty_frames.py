"""帖の途中にある、人の範囲が無いコマの一覧 (frames.json と同じ形) を、帖の分け (dev / test) ごとに作る。

    python3 -I tools/kunshujo/empty_frames.py --index <index.json> --split <split.tsv> --manifests <フォルダ> --role test --out <frames.json>

帖の途中 = 範囲のある最初のコマと最後のコマの間。sample_empty_frames.py と同じ選び方。
確かめる帖の分は、機械の出した範囲の数を数えるためだけに使う。画像を目で見ない。
"""
import argparse, collections, csv, hashlib, json, os

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'manifests', 'role', 'out'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
man_of, hit = collections.defaultdict(set), collections.defaultdict(set)
for r in json.load(open(a.index)):
    b = r['book'][0][1:r['book'][0].index(']')]
    man_of[b].add(r['manifest']); hit[b].add(r['member'].split('#')[0])
out = []
for b in sorted(man_of):
    if split[b]['split'] != a.role:
        continue
    cs = []
    for u in sorted(man_of[b]):
        cs += json.load(open(os.path.join(a.manifests, hashlib.md5(u.encode()).hexdigest() + '.json')))['sequences'][0]['canvases']
    idx = [i for i, c in enumerate(cs) if c['@id'] in hit[b]]
    for i in range(idx[0], idx[-1] + 1):
        c = cs[i]
        if c['@id'] not in hit[b]:
            out.append({'canvas': c['@id'], 'book_id': b, 'page': i + 1, 'width': c['width'], 'height': c['height'],
                        'service': c['images'][0]['resource']['service']['@id'], 'key': hashlib.md5(c['@id'].encode()).hexdigest()})
json.dump(out, open(a.out, 'w'), ensure_ascii=False)
print(a.role, 'empty frames', len(out), 'books', len({f['book_id'] for f in out}))
