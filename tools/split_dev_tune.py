"""課題を見つける帖 (dev) 47 帖を「学習」と「調整 (tune)」に分ける。

    python3 -I tools/kunshujo/split_dev_tune.py strengthening/kunshujo-eval/split.tsv > strengthening/kunshujo-eval/dev-tune.tsv

決まり (docs/notes/kunshujo-eval.md 2026-10-16「残りの条件の決めごと」):
  - 第 1〜18 帖 (group A) から 2 帖、それ以外 (group B) から 7 帖を調整に回す。
  - 各グループで帖の ID を並べ、random.Random(20261016).shuffle して先頭から取る
    (グループごとに乱数を作り直す)。残りが学習。
"""
import csv, random, sys

SEED = 20261016
NTUNE = {'A': 2, 'B': 7}
rows = [r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t') if r['split'] == 'dev']
print('book_id\tgroup\trole')
for g in ('A', 'B'):
    ids = sorted(r['book_id'] for r in rows if r['group'] == g)
    assert all((int(i[1:]) <= 180) == (g == 'A') for i in ids if i.startswith('k'))
    random.Random(SEED).shuffle(ids)
    for n, b in enumerate(ids):
        print(f"{b}\t{g}\t{'tune' if n < NTUNE[g] else 'train'}")
