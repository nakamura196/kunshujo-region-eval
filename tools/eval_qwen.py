"""run_qwen_vl.py の出力を、調整用のコマだけで評価する (確信度なし。IoU 0.5 / 0.75 の P/R/F1、時間、読み取り失敗数)。

    python3 -I tools/kunshujo/eval_qwen.py --index <index.json> --frames <tune_frames.json> --keys-file <list> --pred <pred/>
"""
import argparse, json, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zs_util as Z

ap = argparse.ArgumentParser()
for k in ('index', 'frames', 'keys-file', 'pred'):
    ap.add_argument('--' + k, required=True)
a = ap.parse_args()
keys = [l.strip() for l in open(getattr(a, 'keys_file')) if l.strip()]
byk = {f['key']: f for f in json.load(open(a.frames))}
fr = [byk[k] for k in keys]
hum = Z.load_gt(a.index, fr)
pr = Z.pairs_for(fr, hum, a.pred)
data = [(p, h) for _, p, h in pr]
raw = [json.load(open(os.path.join(a.pred, f['key'] + '.json'))) for f, _, _ in pr]
print(json.dumps({'frames': len(data), 'iou0.5': Z.score(data, 0, 0.5), 'iou0.75': Z.score(data, 0, 0.75),
                  'parse_fail': sum(not r['parse_ok'] for r in raw), 'sec_mean': round(st.mean(r['seconds'] for r in raw), 2),
                  'sec_median': round(st.median(r['seconds'] for r in raw), 2),
                  'zero_box_frames': sum(not r['boxes'] for r in raw)}, ensure_ascii=False))
