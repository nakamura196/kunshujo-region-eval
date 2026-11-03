"""eval_final.py run と同じ設定で、コマを分けて F1 を出す（記述用）。

    python3 -I tools/kunshujo/eval_subgroups.py --index <index.json> --split <split.tsv> --config <config> --pairs b1:gemini,lc-10:gemini [--allow-test] [--by-group]

  - 分け方 1: 人の枠の数がコマの中央値以下か、それより多いか（簡単な帖は学習なしで足り、込み入った帖は学習した検出器が勝つ、という見立ての確認）。
  - 分け方 2（--by-group）: split.tsv の group ごと（外の帖の taito / ndl）。
  - 差の 95% 区間は、分けたコマの中でコマを単位にしたブートストラップ（帖ではなくコマ。外の帖は 1 コマ 1 帖として扱っているので同じ）。
  - IoU 0.5、min_side と conf は eval_final.py と同じ扱い。
"""
import argparse, csv, json, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_final import match, f1, load_human  # noqa: E402

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'config', 'pairs'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--allow-test', action='store_true')
ap.add_argument('--by-group', action='store_true')
a = ap.parse_args()
cfg = json.load(open(a.config))
split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
frames = json.load(open(cfg['frames']))
if cfg.get('subset'):
    keep = set(json.load(open(cfg['subset'])))
    frames = [f for f in frames if f['canvas'] in keep]
if any(split[f['book_id']]['split'] == 'test' for f in frames) and not a.allow_test:
    sys.exit('確かめる帖のコマが入っている。--allow-test を付ける')
hum = load_human(a.index, {f['canvas'] for f in frames})
ms = cfg.get('min_side', 0)
for can in list(hum):
    hum[can] = [h for h in hum[can] if min(h[2], h[3]) > ms]
frames = [f for f in frames if hum[f['canvas']]]
pairs = [p.split(':') for p in a.pairs.split(',')]
conds = sorted({c for p in pairs for c in p})
alt_empty = set(cfg.get('alt_empty', []))

# コマごとの (tp, pred, human)
cnt = {}
for cn in conds:
    c = cfg['conditions'][cn]
    conf = 0.0 if c.get('no_score') else c['conf']
    cnt[cn] = {}
    for f in frames:
        P = [p if len(p) > 4 else p + [1.0] for p in json.load(open(os.path.join(c['pred'], f['key'] + '.json')))['boxes']]
        Pc = [p for p in P if p[4] >= conf]
        H = hum[f['canvas']]
        if f['canvas'] in alt_empty and len(Pc) < len(Pc) + len(H) - 2 * len(match(Pc, H, 0.5)):
            H = []  # eval_final.py の alt_empty と同じ扱い
        cnt[cn][f['canvas']] = (len(match(Pc, H, 0.5)), len(Pc), len(H))


def score(cn, cans):
    tp = sum(cnt[cn][x][0] for x in cans); np_ = sum(cnt[cn][x][1] for x in cans); nh = sum(cnt[cn][x][2] for x in cans)
    return f1(tp, np_, nh)[2]


def ci(xs):
    xs = sorted(xs)
    return [round(xs[int(0.025 * len(xs))], 3), round(xs[int(0.975 * len(xs)) - 1], 3)]


def report(name, cans):
    rng = random.Random(20261102)
    draws = [[rng.choice(cans) for _ in cans] for _ in range(10000)]
    nh = [len(hum[x]) for x in cans]
    row = {'subset': name, 'frames': len(cans), 'human': sum(nh), 'human_per_frame_median': st.median(nh)}
    for cn in conds:
        row[cn] = round(score(cn, cans), 3)
    for x, y in pairs:
        row[f'{x}-{y}'] = [round(score(x, cans) - score(y, cans), 3), ci([score(x, d) - score(y, d) for d in draws])]
    print(json.dumps(row, ensure_ascii=False))


allc = [f['canvas'] for f in frames]
med = st.median(len(hum[x]) for x in allc)
print(f'frames {len(allc)}  median human boxes per frame {med}')
report('all', allc)
report(f'<= {med}', [x for x in allc if len(hum[x]) <= med])
report(f'> {med}', [x for x in allc if len(hum[x]) > med])
if a.by_group:
    g = {f['canvas']: split[f['book_id']]['group'] for f in frames}
    for gn in sorted(set(g.values())):
        report(f'group {gn}', [x for x in allc if g[x] == gn])
