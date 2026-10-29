"""人と機械の枠の「まとめ方」を数える（4.4.3 節）

    /opt/homebrew/bin/python3.13 -I tools/kunshujo/granularity.py --index <index.json>

確かめる帖の全コマで、片方の枠 1 つの中に、もう片方の枠が 2 つ以上入っている所を数える。
「入っている」は、相手の枠の面積の 80% 以上が重なること。人の範囲は幅か高さが 10 画素以下のものを除く。
"""
import argparse, glob, json, os, statistics, sys

sys.path.insert(0, os.path.dirname(__file__))
from eval_final import load_human  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--index', required=True)
ap.add_argument('--pred', default='strengthening/kunshujo-eval/test-pred/b1-yolo11s')
ap.add_argument('--conf', type=float, default=0.31)
ap.add_argument('--min-side', type=float, default=10)
ap.add_argument('--inside', type=float, default=0.8)
a = ap.parse_args()

P = {}
for f in glob.glob(os.path.join(a.pred, '*.json')):
    d = json.load(open(f))
    P[d['canvas']] = d
hum = load_human(a.index, set(P))


def inter(p, q):
    w = min(p[0] + p[2], q[0] + q[2]) - max(p[0], q[0])
    h = min(p[1] + p[3], q[1] + q[3]) - max(p[1], q[1])
    return max(0, w) * max(0, h)


def holds(outer, inner):
    return sum(1 for b in inner if inter(outer, b) >= a.inside * b[2] * b[3]) >= 2


frames = nh = nm = hmerge = mmerge = 0
ah, am = [], []
for c, d in P.items():
    H = [h for h in hum.get(c, []) if min(h[2], h[3]) > a.min_side]
    if not H:
        continue
    frames += 1
    M = [p[:4] for p in d['boxes'] if p[4] >= a.conf]
    A = d['width'] * d['height']
    nh += len(H)
    nm += len(M)
    ah += [h[2] * h[3] / A for h in H]
    am += [m[2] * m[3] / A for m in M]
    hmerge += sum(holds(h, M) for h in H)
    mmerge += sum(holds(m, H) for m in M)

print('frames', frames, 'human boxes', nh, 'machine boxes', nm, f'ratio {nm / nh:.2f}')
print('median area (frac of frame) human', round(statistics.median(ah), 4), 'machine', round(statistics.median(am), 4))
print('human box holding >=2 machine boxes:', hmerge, ' machine box holding >=2 human boxes:', mmerge)
