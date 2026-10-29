"""調整用の帖で確信度のしきい値を決める (IoU 0.5 の F1 最大)。

    python3 -I tools/kunshujo/tune_eval.py --index <index.json> --split <split.tsv> --frames <tune_frames.json> --pred <pred-0.001/> --out <出力フォルダ>

  - <pred> (確信度 0.001 以上の予測) から 0.01 以上だけを残した <out>/pred-0.01/ も作る。
  - eval_detections.py を呼び、しきい値 0.05〜0.95 (0.01 刻み) の中で F1@0.5 が最大の値を選ぶ。
  - 結果を <out>/summary.json (eval_detections の出力) と標準出力に出す。
"""
import argparse, glob, json, os, subprocess, sys

ap = argparse.ArgumentParser()
for k in ('index', 'split', 'frames', 'pred', 'out'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
d = os.path.join(a.out, 'pred-0.01')
os.makedirs(d, exist_ok=True)
for p in glob.glob(os.path.join(a.pred, '*.json')):
    j = json.load(open(p))
    j['boxes'] = [b for b in j['boxes'] if b[4] >= 0.01]
    json.dump(j, open(os.path.join(d, os.path.basename(p)), 'w'))
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, '-I', os.path.join(here, 'eval_detections.py'), '--index', a.index, '--split', a.split,
                '--frames', a.frames, '--pred', d, '--out', a.out], check=True, stdout=subprocess.DEVNULL)
s = json.load(open(os.path.join(a.out, 'summary.json')))
c = s['best_conf']
for thr in (0.5, 0.75):
    r = s['results'][f'all|conf=best({c})|iou={thr}']
    print(f"conf={c} IoU{thr}: P={r['precision']} R={r['recall']} F1={r['f1']} (tp {r['tp']}, pred {r['pred']}, human {r['human']}, frames {r['frames']})")
