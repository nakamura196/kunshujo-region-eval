"""ゼロショット条件 (a) の調整用の小道具。eval_detections.py の対応づけ・点数計算を借りて、
調整用の帖のコマだけを評価する。

    import zs_util as Z   (tools/kunshujo を sys.path に入れて使う)

決まり: 人手の範囲は eval_detections.py と同じ読み方 (member の #xywh)。呼び出し側が渡す frames に
確かめる帖のコマを入れない。
"""
import json, os

_here = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(_here, 'eval_detections.py')).read().split('def main():')[0]
_ns = {}
exec(compile(_src, 'eval_detections_head', 'exec'), _ns)   # iou, match, prf, score だけを借りる
match, prf, score, iou = _ns['match'], _ns['prf'], _ns['score'], _ns['iou']


def load_gt(index, frames):
    fr = {f['canvas'] for f in frames}
    hum = {}
    for r in json.load(open(index)):
        can, _, frag = r['member'].partition('#xywh=')
        if can in fr and frag:
            hum.setdefault(can, []).append([float(v) for v in frag.split(',')])
    return hum


def pairs_for(frames, hum, pred_dir, filt=lambda b: True):
    """[(frame, pred 枠のリスト, 人手)]。予測ファイルが無いコマは除く。"""
    out = []
    for f in frames:
        p = os.path.join(pred_dir, f['key'] + '.json')
        if os.path.exists(p):
            out.append((f, [b for b in json.load(open(p))['boxes'] if filt(b)], hum.get(f['canvas'], [])))
    return out
