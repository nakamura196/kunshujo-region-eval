"""DocLayout-YOLO の出力 (run_doclayout.py) から、貼り込みとみなすクラスの組と確信度のしきい値を、
調整用の帖のコマだけで選ぶ。選ぶ基準は IoU 0.5 の F1 (しきい値 0.05〜0.95、0.01 刻み)。

    python3 -I tools/kunshujo/tune_doclayout.py --index <index.json> --frames <tune_frames.json> --pred <pred/> --out <summary.json>
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zs_util as Z

SETS = {
    'figure': {3},
    'figure+table': {3, 5},
    'non-text (all but plain text/title/abandon...)': {3, 4, 5, 6, 7, 8, 9},
    'all classes': set(range(10)),
}


def main():
    ap = argparse.ArgumentParser()
    for k in ('index', 'frames', 'pred', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    fr = json.load(open(a.frames))
    hum = Z.load_gt(a.index, fr)
    grid = [round(0.05 + 0.01 * i, 2) for i in range(91)]
    out = {'sets': {}}
    for name, cls in SETS.items():
        pr = Z.pairs_for(fr, hum, a.pred, lambda b: b[5] in cls)
        data = [(p, h) for _, p, h in pr]
        sw = {c: Z.score(data, c, 0.5)['f1'] for c in grid}
        best = max(grid, key=lambda c: (sw[c], -c))
        out['sets'][name] = {'classes': sorted(cls), 'frames': len(data), 'best_conf': best,
                             'iou0.5': Z.score(data, best, 0.5), 'iou0.75': Z.score(data, best, 0.75)}
        print(name, best, out['sets'][name]['iou0.5']['f1'], out['sets'][name]['iou0.75']['f1'])
    best_name = max(out['sets'], key=lambda n: out['sets'][n]['iou0.5']['f1'])
    out['chosen'] = best_name
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('chosen', best_name, json.dumps(out['sets'][best_name], ensure_ascii=False))


main()
