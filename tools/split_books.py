"""捃拾帖 94 帖を「課題を見つける帖 (dev)」と「確かめる帖 (test)」に乱数で分ける。

    python3 -I tools/kunshujo/split_books.py <index.json> > strengthening/kunshujo-eval/split.tsv

決まり（docs/notes/kunshujo-eval.md 2026-10-16「帖の分割」）:
- 単位は帖。同じ帖のコマを両側に分けない（同じ切り手・同じ資料の癖が漏れるため）
- 第 1〜18 帖（k010〜k180、摺物データベース由来）と、それ以外の 76 帖とで、別々に半分ずつ分ける
- 種は 20261016。帖の ID を並べてから random.Random(種).shuffle し、前半を dev にする
"""
import collections
import json
import random
import sys

SEED = 20261016

rows = json.load(open(sys.argv[1]))
books = collections.defaultdict(lambda: [0, set()])
for r in rows:
    b = r['book'][0]
    books[b][0] += 1
    books[b][1].add(r['member'].split('#')[0])

def bid(b):
    return b[1:b.index(']')]

def group(b):
    i = bid(b)
    return 'A' if i.startswith('k') and int(i[1:]) <= 180 else 'B'

rng = random.Random(SEED)
out = []
for g in ('A', 'B'):
    ids = sorted(b for b in books if group(b) == g)
    rng.shuffle(ids)
    half = len(ids) // 2
    for n, b in enumerate(ids):
        out.append((bid(b), b, g, 'dev' if n < half else 'test', len(books[b][1]), books[b][0]))

print('book_id\tbook\tgroup\tsplit\tframes_with_regions\tregions')
for row in sorted(out):
    print('\t'.join(map(str, row)))
