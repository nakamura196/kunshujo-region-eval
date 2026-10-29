"""YOLOv5 (v7.0) の重みで範囲を予測する。run_best_pt.py の infer と同じ手順 (max 辺 1024 に縮め、AutoShape size=640、NMS iou 0.45)。
確信度の下限だけ --conf で変えられる (既定 0.001)。出力形式は predict_ul.py と同じ。

    <yolov5 用 venv>/bin/python -I tools/kunshujo/predict_v5.py --yolov5 <v7.0 の clone> --weights <best.pt> --frames <frames.json> --cache <frames/> --out <pred/> [--conf 0.001] [--device mps] [--size 640]
"""
import argparse, json, os, time
import torch
from PIL import Image

ap = argparse.ArgumentParser()
for k in ('yolov5', 'weights', 'frames', 'cache', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--conf', type=float, default=0.001)
ap.add_argument('--size', type=int, default=640)
ap.add_argument('--device', default='cpu')
a = ap.parse_args()
ol = torch.load
torch.load = lambda *x, **k: ol(*x, **{**k, 'weights_only': False})
model = torch.hub.load(a.yolov5, 'custom', path=a.weights, source='local', device=a.device)
torch.load = ol
model.conf = a.conf
model.iou = 0.45
model.max_det = 300
os.makedirs(a.out, exist_ok=True)
n = skip = miss = 0
t0 = time.time()
for f in json.load(open(a.frames)):
    o = os.path.join(a.out, f['key'] + '.json')
    p = os.path.join(a.cache, f['key'] + '.jpg')
    if os.path.exists(o):
        skip += 1
        continue
    if not os.path.exists(p):
        miss += 1
        continue
    im = Image.open(p).convert('RGB')
    g = 1024 / max(im.size)
    im2 = im.resize(tuple(int(x * g) for x in im.size), Image.BICUBIC)
    r = model(im2, size=a.size).xyxy[0].cpu().numpy()
    sc = f['width'] / im2.size[0]
    boxes = [[round(float(x1 * sc), 1), round(float(y1 * sc), 1), round(float((x2 - x1) * sc), 1),
              round(float((y2 - y1) * sc), 1), round(float(c), 4)] for x1, y1, x2, y2, c, _ in r]
    json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': f['width'], 'height': f['height'],
               'infer_size': a.size, 'boxes': boxes}, open(o, 'w'), ensure_ascii=False)
    n += 1
print('predicted', n, 'skipped', skip, 'no image', miss, round(time.time() - t0), 's')
