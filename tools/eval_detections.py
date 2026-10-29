"""予測した範囲を人手の範囲と比べ、適合率・再現率・F1 を出す。

    python3 -I tools/kunshujo/eval_detections.py --index <index.json> --split <split.tsv> --frames <frames.json> --pred <pred/> --out <出力フォルダ>

出力: <out>/summary.json, <out>/per-book.tsv

決まり:
  - 対象は frames.json にあり、予測 JSON があるコマだけ (split=='dev' のみ。test の帖は読まない)。
  - コマごとに人手と予測を IoU の大きい順の貪欲法で 1 対 1 に対応づける。IoU がしきい値未満の組は対応にしない。
  - IoU しきい値: 0.5 (主), 0.75 (副)。確信度しきい値: 0.25 と、IoU 0.5 で dev 全体の F1 が最大になる値 (0.01 刻み)。
  - 点数の差 = コマごとの (しきい値以上の予測数 - 人手の数)。
  - 「0.5 では対応するが 0.75 では外れる」組 = IoU 0.5 の対応のうち、IoU が 0.75 未満の組。
  - 座標は canvas 原寸の画素 [x, y, w, h]。
"""
import argparse, csv, json, os, statistics as st
from collections import defaultdict


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    u = a[2] * a[3] + b[2] * b[3] - i
    return i / u if u else 0.0


def match(P, H, thr):
    """P: 予測, H: 人手。対応した IoU のリストを返す。"""
    pairs = sorted(((iou(p, h), i, j) for i, p in enumerate(P) for j, h in enumerate(H)), reverse=True)
    up, uh, res = set(), set(), []
    for v, i, j in pairs:
        if v < thr or v <= 0:
            break
        if i in up or j in uh:
            continue
        up.add(i); uh.add(j); res.append(v)
    return res


def prf(tp, np_, nh):
    p = tp / np_ if np_ else 0.0
    r = tp / nh if nh else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def score(frames, conf, thr):
    """frames: [(pred, human)]。"""
    tp = np_ = nh = 0
    diffs = []
    for P, H in frames:
        Pc = [p for p in P if p[4] >= conf]
        m = match(Pc, H, thr)
        tp += len(m); np_ += len(Pc); nh += len(H)
        diffs.append(len(Pc) - len(H))
    p, r, f = prf(tp, np_, nh)
    return {'tp': tp, 'pred': np_, 'human': nh, 'precision': round(p, 4), 'recall': round(r, 4), 'f1': round(f, 4),
            'frames': len(frames), 'diff_mean': round(st.mean(diffs), 3) if diffs else None,
            'diff_median': st.median(diffs) if diffs else None}


def main():
    ap = argparse.ArgumentParser()
    for k in ('index', 'split', 'frames', 'pred', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
    fr = {f['canvas']: f for f in json.load(open(a.frames))}
    hum = defaultdict(list)
    for r in json.load(open(a.index)):
        can, _, frag = r['member'].partition('#xywh=')
        if can in fr and frag:
            hum[can].append([float(v) for v in frag.split(',')])
    data = []  # (book, group, pred, human)
    nopred = 0
    for can, f in fr.items():
        assert split[f['book_id']]['split'] == 'dev'
        p = os.path.join(a.pred, f['key'] + '.json')
        if not os.path.exists(p):
            nopred += 1
            continue
        d = json.load(open(p))
        data.append((f['book_id'], split[f['book_id']]['group'], d['boxes'], hum[can]))
    allf = [(p, h) for _, _, p, h in data]
    grid = [round(0.05 + 0.01 * i, 2) for i in range(91)]
    sweep = {c: score(allf, c, 0.5)['f1'] for c in grid}
    best = max(grid, key=lambda c: (sweep[c], -c))
    confs = {'0.25': 0.25, 'best': best}
    out = {'frames_evaluated': len(data), 'frames_without_pred': nopred, 'best_conf': best, 'best_f1_iou0.5': sweep[best],
           'f1_sweep_iou0.5': {str(c): sweep[c] for c in grid[::5]}, 'results': {}}
    sets = {'all': allf, 'A': [(p, h) for _, g, p, h in data if g == 'A'], 'B': [(p, h) for _, g, p, h in data if g == 'B']}
    for sn, fs in sets.items():
        for cn, c in confs.items():
            for thr in (0.5, 0.75):
                out['results'][f'{sn}|conf={cn}({c})|iou={thr}'] = score(fs, c, thr)
    # 0.5 で合い 0.75 で外れる組
    for cn, c in confs.items():
        n50 = n75 = 0
        for P, H in allf:
            m = match([p for p in P if p[4] >= c], H, 0.5)
            n50 += len(m); n75 += sum(v >= 0.75 for v in m)
        out[f'pairs_match50_conf={cn}({c})'] = {'matched_at_0.5': n50, 'of_which_iou>=0.75': n75, 'match_0.5_not_0.75': n50 - n75}
    json.dump(out, open(os.path.join(a.out, 'summary.json'), 'w'), ensure_ascii=False, indent=1)
    byb = defaultdict(list)
    for b, g, p, h in data:
        byb[b].append((p, h))
    with open(os.path.join(a.out, 'per-book.tsv'), 'w') as fo:
        w = csv.writer(fo, delimiter='\t')
        w.writerow(['book_id', 'group', 'frames', 'human', 'conf', 'iou', 'pred', 'tp', 'precision', 'recall', 'f1', 'diff_mean', 'diff_median'])
        for b in sorted(byb):
            for cn, c in confs.items():
                for thr in (0.5, 0.75):
                    s = score(byb[b], c, thr)
                    w.writerow([b, split[b]['group'], s['frames'], s['human'], c, thr, s['pred'], s['tp'], s['precision'],
                                s['recall'], s['f1'], s['diff_mean'], s['diff_median']])
    print(json.dumps({k: v for k, v in out.items() if k != 'f1_sweep_iou0.5'}, ensure_ascii=False, indent=1))


main()
