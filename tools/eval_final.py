"""しきい値を固定した条件どうしを、同じコマの集合で比べる（論文の表を作る）。

    python3 -I tools/kunshujo/eval_final.py bounds --index <index.json> --frames <dev の frames.json> --split <split.tsv>
    python3 -I tools/kunshujo/eval_final.py run --index <index.json> --split <split.tsv> --config <config.json> --out <出力フォルダ> [--allow-test]

config.json:
  {"frames": "<frames.json>", "subset": "<コマの canvas の一覧 JSON（任意）>",
   "size_bounds": [b1, b2],
   "conditions": {"b1": {"pred": "<予測フォルダ>", "conf": 0.31}, "a2": {"pred": "...", "conf": 0.0, "no_score": true}, ...},
   "pairs": [["c", "b0"], ["b1", "b2"], ...]}

決まり:
  - 一致の取り方は eval_detections.py と同じ（コマごとに IoU の大きい順の貪欲法で 1 対 1）。
  - 確信度のしきい値は config で固定する。ここでは探さない。
  - 信頼区間: 帖を単位に復元抽出（1 万回、種 20261016）。条件どうしの差も同じ抽出で対にして出す。
  - AP: COCO と同じ数え方（確信度の高い順に、まだ対応していない人手のうち IoU 最大のものと対応、101 点補間）。
    IoU 0.5 と 0.5:0.95（0.05 刻み）。no_score の条件は出さない。しきい値は掛けず、予測を全部使う。
  - 大きさ別の再現率: 人手の範囲の面積がコマの面積に占める割合で 3 つに分ける。境目は bounds で
    課題を見つける帖の範囲の 3 分位として決め、config に書く。
  - classes（条件ごと、任意）: 予測の 6 番目の値（種類）がこの一覧にある枠だけを使う。DocLayout-YOLO の「図」は 3。
  - min_side（config、既定 0）: 幅か高さがこの画素以下の人手の範囲を除く（点のような入力の誤り）。
    除いた結果、範囲が 0 になったコマは評価から外す。主な集計は 10、感度の確かめとして 0 でも流す。
  - 確かめる帖を含む frames は --allow-test が無いと止まる（数字を確定させる 1 回だけ使う）。
"""
import argparse, csv, json, os, random, statistics as st, sys
from collections import defaultdict



def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    u = a[2] * a[3] + b[2] * b[3] - i
    return i / u if u else 0.0


def match(P, H, thr):
    """貪欲法。対応した (予測の番号, 人手の番号, IoU) を返す。"""
    pairs = sorted(((iou(p, h), i, j) for i, p in enumerate(P) for j, h in enumerate(H)), reverse=True)
    up, uh, res = set(), set(), []
    for v, i, j in pairs:
        if v < thr or v <= 0:
            break
        if i in up or j in uh:
            continue
        up.add(i); uh.add(j); res.append((i, j, v))
    return res


def f1(tp, np_, nh):
    p = tp / np_ if np_ else 0.0
    r = tp / nh if nh else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def ap_at(frames, thr):
    """frames: [(P, H)]。COCO 式の AP（101 点補間）。"""
    dets, nh = [], 0
    for fi, (P, H) in enumerate(frames):
        nh += len(H)
        for p in P:
            dets.append((p[4], fi, p))
    dets.sort(key=lambda d: -d[0])
    used = defaultdict(set)
    tps = []
    for _, fi, p in dets:
        H = frames[fi][1]
        best, bj = thr, -1
        for j, h in enumerate(H):
            if j in used[fi]:
                continue
            v = iou(p, h)
            if v >= best:
                best, bj = v, j
        if bj >= 0:
            used[fi].add(bj); tps.append(1)
        else:
            tps.append(0)
    if not nh:
        return 0.0
    rec, prec, tp = [], [], 0
    for k, t in enumerate(tps, 1):
        tp += t
        rec.append(tp / nh); prec.append(tp / k)
    for k in range(len(prec) - 2, -1, -1):
        prec[k] = max(prec[k], prec[k + 1])
    s, k = 0.0, 0
    for r in [i / 100 for i in range(101)]:
        while k < len(rec) and rec[k] < r:
            k += 1
        s += prec[k] if k < len(rec) else 0.0
    return s / 101


def load_human(index, canvases):
    hum = defaultdict(list)
    for r in json.load(open(index)):
        can, _, frag = r['member'].partition('#xywh=')
        if can in canvases and frag:
            hum[can].append([float(v) for v in frag.split(',')])
    return hum


def cmd_bounds(a):
    split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
    fr = {f['canvas']: f for f in json.load(open(a.frames)) if split[f['book_id']]['split'] == 'dev'}
    hum = load_human(a.index, fr)
    fr_area = [h[2] * h[3] / (fr[c]['width'] * fr[c]['height']) for c, hs in hum.items() for h in hs]
    q = st.quantiles(fr_area, n=3)
    print(json.dumps({'regions': len(fr_area), 'size_bounds': [round(x, 5) for x in q]}))


def cmd_run(a):
    cfg = json.load(open(a.config))
    split = {r['book_id']: r for r in csv.DictReader(open(a.split), delimiter='\t')}
    frames = json.load(open(cfg['frames']))
    if cfg.get('subset'):
        keep = set(json.load(open(cfg['subset'])))
        frames = [f for f in frames if f['canvas'] in keep]
    if any(split[f['book_id']]['split'] == 'test' for f in frames) and not a.allow_test:
        sys.exit('確かめる帖のコマが入っている。数字を確定させる 1 回だけ --allow-test を付けて流す')
    hum = load_human(a.index, {f['canvas'] for f in frames})
    ms = cfg.get('min_side', 0)
    dropped = 0
    if ms:
        for can in list(hum):
            k = [h for h in hum[can] if min(h[2], h[3]) > ms]
            dropped += len(hum[can]) - len(k)
            hum[can] = k
        frames = [f for f in frames if hum[f['canvas']]]
    b1, b2 = cfg['size_bounds']
    conds = cfg['conditions']
    # コマごとの予測を読む。予測ファイルが無いコマは、どの条件でも欠けがあれば止める（同じコマで比べるため）
    pred = {}
    for cn, c in conds.items():
        pred[cn] = {}
        for f in frames:
            p = os.path.join(c['pred'], f['key'] + '.json')
            if not os.path.exists(p):
                sys.exit(f'{cn}: 予測が無いコマ {f["canvas"]}')
            bx = json.load(open(p))['boxes']
            if 'classes' in c:  # 種類を出す検出器は、指定した種類だけを使う（6 番目の値が種類）
                bx = [x[:5] for x in bx if x[5] in c['classes']]
            pred[cn][f['canvas']] = bx
    books = sorted({f['book_id'] for f in frames})
    out = {'frames': len(frames), 'books': len(books), 'human': sum(len(hum[f['canvas']]) for f in frames),
           'size_bounds': [b1, b2], 'min_side': ms, 'human_dropped_min_side': dropped, 'conditions': {}}
    # 帖ごとの数（条件 × IoU しきい値）
    per_book = {cn: {thr: defaultdict(lambda: [0, 0, 0]) for thr in (0.5, 0.75)} for cn in conds}
    for cn, c in conds.items():
        conf = 0.0 if c.get('no_score') else c['conf']
        size_tp, size_n = [0, 0, 0], [0, 0, 0]
        loose = n50 = 0
        cnt_diff = []
        for f in frames:
            P = [p if len(p) > 4 else p + [1.0] for p in pred[cn][f['canvas']]]
            Pc = [p for p in P if p[4] >= conf]
            H = hum[f['canvas']]
            cnt_diff.append(len(Pc) - len(H))
            for thr in (0.5, 0.75):
                m = match(Pc, H, thr)
                t = per_book[cn][thr][f['book_id']]
                t[0] += len(m); t[1] += len(Pc); t[2] += len(H)
                if thr == 0.5:
                    n50 += len(m); loose += sum(v < 0.75 for _, _, v in m)
                    hit = {j for _, j, _ in m}
                    area = f['width'] * f['height']
                    for j, h in enumerate(H):
                        s = h[2] * h[3] / area
                        k = 0 if s < b1 else (1 if s < b2 else 2)
                        size_n[k] += 1; size_tp[k] += j in hit
        res = {'conf': conf}
        for thr in (0.5, 0.75):
            tp = sum(v[0] for v in per_book[cn][thr].values())
            np_ = sum(v[1] for v in per_book[cn][thr].values())
            nh = sum(v[2] for v in per_book[cn][thr].values())
            p, r, ff = f1(tp, np_, nh)
            res[f'iou{thr}'] = {'tp': tp, 'pred': np_, 'human': nh, 'precision': round(p, 4), 'recall': round(r, 4), 'f1': round(ff, 4)}
        res['match0.5_not0.75'] = {'matched_at_0.5': n50, 'iou_below_0.75': loose, 'share': round(loose / n50, 4) if n50 else None}
        res['recall_by_size'] = {nm: {'human': size_n[k], 'recall': round(size_tp[k] / size_n[k], 4) if size_n[k] else None}
                                 for k, nm in enumerate(('small', 'medium', 'large'))}
        res['count_diff'] = {'mean': round(st.mean(cnt_diff), 3), 'median': st.median(cnt_diff),
                             'exact_share': round(sum(d == 0 for d in cnt_diff) / len(cnt_diff), 4)}
        if not c.get('no_score'):
            fl = [(pred[cn][f['canvas']], hum[f['canvas']]) for f in frames]
            res['AP50'] = round(ap_at(fl, 0.5), 4)
            res['AP50_95'] = round(st.mean(ap_at(fl, t / 100) for t in range(50, 100, 5)), 4)
        out['conditions'][cn] = res
    # 帖を単位にしたブートストラップ
    rng = random.Random(20261016)
    draws = [[rng.choice(books) for _ in books] for _ in range(10000)]

    def boot_f1(cn, thr, d):
        t = per_book[cn][thr]
        tp = sum(t[b][0] for b in d); np_ = sum(t[b][1] for b in d); nh = sum(t[b][2] for b in d)
        return f1(tp, np_, nh)[2]

    def ci(xs):
        xs = sorted(xs)
        return [round(xs[int(0.025 * len(xs))], 4), round(xs[int(0.975 * len(xs)) - 1], 4)]

    for cn in conds:
        for thr in (0.5, 0.75):
            out['conditions'][cn][f'iou{thr}']['f1_ci95'] = ci([boot_f1(cn, thr, d) for d in draws])
    out['pairs'] = {}
    for x, y in cfg.get('pairs', []):
        for thr in (0.5, 0.75):
            ds = [boot_f1(x, thr, d) - boot_f1(y, thr, d) for d in draws]
            obs = out['conditions'][x][f'iou{thr}']['f1'] - out['conditions'][y][f'iou{thr}']['f1']
            out['pairs'][f'{x}-{y}|iou{thr}'] = {'f1_diff': round(obs, 4), 'ci95': ci(ds)}
    # 第 1〜18 帖と以降（記述）
    out['by_group'] = {}
    for cn in conds:
        for g in ('A', 'B'):
            t = per_book[cn][0.5]
            bs = [b for b in books if split[b]['group'] == g]
            tp = sum(t[b][0] for b in bs); np_ = sum(t[b][1] for b in bs); nh = sum(t[b][2] for b in bs)
            p, r, ff = f1(tp, np_, nh)
            out['by_group'][f'{cn}|{g}'] = {'books': len(bs), 'human': nh, 'precision': round(p, 4), 'recall': round(r, 4), 'f1': round(ff, 4)}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, 'summary.json'), 'w'), ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'per-book.tsv'), 'w') as fo:
        w = csv.writer(fo, delimiter='\t')
        w.writerow(['condition', 'book_id', 'group', 'iou', 'human', 'pred', 'tp', 'precision', 'recall', 'f1'])
        for cn in conds:
            for thr in (0.5, 0.75):
                for b in books:
                    tp, np_, nh = per_book[cn][thr][b]
                    p, r, ff = f1(tp, np_, nh)
                    w.writerow([cn, b, split[b]['group'], thr, nh, np_, tp, round(p, 4), round(r, 4), round(ff, 4)])
    print(json.dumps({cn: {'f1@0.5': v['iou0.5']['f1'], 'ci': v['iou0.5']['f1_ci95'], 'f1@0.75': v['iou0.75']['f1']}
                      for cn, v in out['conditions'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('bounds')
    for k in ('index', 'frames', 'split'):
        p.add_argument('--' + k, required=True)
    p = sp.add_parser('run')
    for k in ('index', 'split', 'config', 'out'):
        p.add_argument('--' + k, required=True)
    p.add_argument('--allow-test', action='store_true')
    a = ap.parse_args()
    {'bounds': cmd_bounds, 'run': cmd_run}[a.cmd](a)
