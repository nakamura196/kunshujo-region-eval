"""外の帖で人が描いた枠（ext_draw_server.py の state.json）を、eval_final.py run に渡せる形に直す。

    python3 -I tools/kunshujo/ext_prepare_eval.py --work <作業フォルダ> [--only-finished]

  - 人の枠は 4 点（または古い [x, y, w, h]）。外接する四角に直し、index.json と同じ形（member に #xywh=）で <work>/eval/human-index.json に書く。
  - コマを単位にブートストラップするため、frames の book_id をコマの key に置き換えた <work>/eval/frames.json と、
    split.tsv（split=ext、group=taito / ndl）を書く。--only-finished なら「描き終えた」印のコマだけ。
  - 人の枠が 0 のコマは eval_final.py が数えない（偽陽性が入らない）ので、その数と機械の枠の数を別に表示する。
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument('--work', required=True)
ap.add_argument('--only-finished', action='store_true')
a = ap.parse_args()
st = json.load(open(os.path.join(a.work, 'human', 'state.json')))
frames = json.load(open(os.path.join(a.work, 'frames.json')))
if a.only_finished:
    frames = [f for f in frames if st.get('finished', {}).get(f['key'])]


def rect(b):
    if isinstance(b[0], list):
        xs, ys = [p[0] for p in b], [p[1] for p in b]
        return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
    return b


idx, out_fr, empty = [], [], []
for f in frames:
    bs = [rect(b) for b in st.get('boxes', {}).get(f['key'], [])]
    for x, y, w, h in bs:
        idx.append({'member': f"{f['canvas']}#xywh={round(x)},{round(y)},{round(w)},{round(h)}"})
    if not bs:
        empty.append(f['key'])
    out_fr.append({**f, 'book_id': f['key'], 'group': 'taito' if f['book_id'] == 'taito' else 'ndl'})
d = os.path.join(a.work, 'eval')
os.makedirs(d, exist_ok=True)
json.dump(idx, open(os.path.join(d, 'human-index.json'), 'w'), ensure_ascii=False)
json.dump(out_fr, open(os.path.join(d, 'frames.json'), 'w'), ensure_ascii=False)
with open(os.path.join(d, 'split.tsv'), 'w') as fo:
    fo.write('book_id\tsplit\tgroup\n')
    for f in out_fr:
        fo.write(f"{f['key']}\text\t{f['group']}\n")
print('frames', len(out_fr), 'human boxes', len(idx), 'frames without human boxes', len(empty))
for k in empty:
    for c in sorted(os.listdir(os.path.join(a.work, 'pred'))):
        p = os.path.join(a.work, 'pred', c, k + '.json')
        if os.path.exists(p):
            print('  empty frame', k[:8], c, 'boxes(all scores)', len(json.load(open(p))['boxes']))
