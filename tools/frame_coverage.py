"""帖ごとに、マニフェストのコマ数と、index.json で範囲のあるコマ数を並べる。

    python3 -I tools/kunshujo/frame_coverage.py <index.json> <manifest のフォルダ> <split.tsv>

manifest のフォルダには、マニフェストを URL の MD5 + .json の名前で置く。
範囲の無いコマが「貼り込みが無い」のか「描かれていない」のかを見分ける手がかりにする。
"""
import collections
import csv
import hashlib
import json
import os
import sys

rows = json.load(open(sys.argv[1]))
mdir = sys.argv[2]
split = {r['book_id']: r for r in csv.DictReader(open(sys.argv[3]), delimiter='\t')}

def canvases(man):
    if 'sequences' in man:
        return [c['@id'] for c in man['sequences'][0]['canvases']]
    return [c['id'] for c in man.get('items', [])]

man_of = collections.defaultdict(set)
hit = collections.defaultdict(set)
for r in rows:
    b = r['book'][0][1:r['book'][0].index(']')]
    man_of[b].add(r['manifest'])
    hit[b].add(r['member'].split('#')[0])

print('book_id\tgroup\tsplit\tcanvases\twith_regions\twithout\tfirst_hit\tlast_hit\tgaps_inside')
for b in sorted(man_of):
    cs = []
    for u in sorted(man_of[b]):
        cs += canvases(json.load(open(os.path.join(mdir, hashlib.md5(u.encode()).hexdigest() + '.json'))))
    idx = [i for i, c in enumerate(cs) if c in hit[b]]
    unknown = len(hit[b] - set(cs))
    first, last = (idx[0] + 1, idx[-1] + 1) if idx else (0, 0)
    gaps = (last - first + 1 - len(idx)) if idx else 0
    s = split[b]
    print(f"{b}\t{s['group']}\t{s['split']}\t{len(cs)}\t{len(idx)}\t{len(cs)-len(idx)}\t{first}\t{last}\t{gaps}" + (f'\tUNMATCHED={unknown}' if unknown else ''))
