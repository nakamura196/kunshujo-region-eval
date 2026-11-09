"""Rebuild Table 2 (judgements of unmatched boxes) from the files in unmatched/.

    python3 -I tools/count_unmatched.py

- judgements.tsv: the author's category for each judged box (A/B/C/D/?); rows with an empty category were not judged.
- a-subclass-author.tsv: the author's final sub-category for every box judged A
  (A1 = part of a single sheet, a machine error; A2 = one of several items merged by the catalogue;
  見開き = one page of a booklet spread; A? = undecidable). `n` is the 1-based row of items.tsv.
- In the YOLOv5-only set, all 6 boxes judged D are "items merged by the machine" (5 noted on the screen as まとめ,
  1 in notes.tsv); no box was a plain misplacement.
"""
import csv, os
from collections import Counter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'unmatched')
sub = {}
for r in csv.DictReader(open(os.path.join(D, 'a-subclass-author.tsv')), delimiter='\t'):
    sub[(r['set'], int(r['n']))] = r['author']
for s, name in (('1', 'gemini'), ('2', 'b0-only')):
    items = [r['id'] for r in csv.DictReader(open(os.path.join(D, name, 'items.tsv')), delimiter='\t')]
    j = {r['id']: r['author_class'] for r in csv.DictReader(open(os.path.join(D, name, 'judgements.tsv')), delimiter='\t')}
    c = Counter()
    for n, i in enumerate(items, 1):
        k = j.get(i, '')
        if not k:
            continue
        k = k[0]
        if k == 'A':
            k = {'A1': 'error', 'A2': 'merged by catalogue', '見開き': 'spread split', 'A?': 'undecidable'}[sub[(s, n)]]
        else:
            k = {'B': 'no catalogue box', 'C': 'error', 'D': 'merged by machine', '?': 'undecidable'}[k]
        c[k] += 1
    t = sum(c.values())
    unit = c['no catalogue box'] + c['merged by catalogue'] + c['merged by machine'] + c['spread split']
    print(f'{name}: judged {t}')
    print(f'  unit mismatch {unit} ({unit / t:.0%}): no catalogue box {c["no catalogue box"]}, merged by catalogue {c["merged by catalogue"]}, '
          f'merged by machine {c["merged by machine"]}, spread split {c["spread split"]}')
    print(f'  machine error {c["error"]} ({c["error"] / t:.0%}), undecidable {c["undecidable"]} ({c["undecidable"] / t:.0%})')
