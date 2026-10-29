"""DocLayout-YOLO (DocStructBench 公開重み) を流して、コマごとに全クラスの枠を保存する。学習はしない。

    <venv-dly>/bin/python -I tools/kunshujo/run_doclayout.py --frames <frames.json> --cache <frames_dev/> --weights <.pt> --out <pred/> [--keys-file <list>] [--imgsz 1024] [--device mps|cpu]

  - frames.json に載っているコマだけを扱う。確かめる帖の画像は、設定を凍結するまで渡さない。
  - 確信度 0.01 以上を全部保存する。枠は canvas 原寸 [x, y, w, h, conf, class_id]。
    クラス名は出力 JSON の names に入れる。
  - 出力形式は run_best_pt.py と同じ (boxes の各要素の後ろにクラス番号が付く)。
"""
import argparse, json, os, time


def main():
    ap = argparse.ArgumentParser()
    for k in ('frames', 'cache', 'weights', 'out'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--keys-file', help='処理するコマの key を 1 行ずつ書いたファイル')
    ap.add_argument('--imgsz', type=int, default=1024)
    ap.add_argument('--conf', type=float, default=0.01)
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    from doclayout_yolo import YOLOv10
    model = YOLOv10(a.weights)
    os.makedirs(a.out, exist_ok=True)
    fr = json.load(open(a.frames))
    if a.keys_file:
        keys = {l.strip() for l in open(a.keys_file) if l.strip()}
        fr = [f for f in fr if f['key'] in keys]
    t0 = time.time(); n = 0
    for f in fr:
        ip = os.path.join(a.cache, f['key'] + '.jpg')
        op = os.path.join(a.out, f['key'] + '.json')
        if not os.path.exists(ip) or os.path.exists(op):
            continue
        r = model.predict(ip, imgsz=a.imgsz, conf=a.conf, device=a.device, verbose=False)[0]
        h, w = r.orig_shape
        sx, sy = f['width'] / w, f['height'] / h
        boxes = []
        for (x1, y1, x2, y2), c, k in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist()):
            boxes.append([round(x1 * sx, 1), round(y1 * sy, 1), round((x2 - x1) * sx, 1), round((y2 - y1) * sy, 1), round(c, 4), int(k)])
        json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': f['width'], 'height': f['height'],
                   'names': {str(i): v for i, v in r.names.items()}, 'boxes': boxes}, open(op, 'w'), ensure_ascii=False)
        n += 1
    print('done', n, 'frames', round(time.time() - t0, 1), 's')


main()
