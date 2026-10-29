"""ultralytics の重み (YOLO11 / RT-DETR) でコマの範囲を予測し、eval_detections.py と同じ形式の JSON を出す。

    python3 -I tools/kunshujo/predict_ul.py --weights <best.pt> --frames <frames.json> --cache <frames/> --out <pred/> [--conf 0.01] [--imgsz 640] [--device mps] [--books k150,k120] [--limit N]

  - frames.json のコマだけを扱う。--books で帖を絞れる。既にある出力は飛ばす。
  - 枠は canvas 原寸の画素 [x, y, w, h, conf] (canvas の幅 / 画像の幅 で戻す)。
  - 帖の分割 (dev / test) はここでは確かめない。呼ぶ側が frames.json で決める。
"""
import argparse, json, os, time
from PIL import Image
from ultralytics import YOLO, RTDETR

ap = argparse.ArgumentParser()
for k in ('weights', 'frames', 'cache', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--conf', type=float, default=0.01)
ap.add_argument('--imgsz', type=int, default=640)
ap.add_argument('--device', default='mps')
ap.add_argument('--books', default='')
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--rtdetr', action='store_true')
a = ap.parse_args()
fr = json.load(open(a.frames))
if a.books:
    keep = set(a.books.split(','))
    fr = [f for f in fr if f['book_id'] in keep]
if a.limit:
    fr = fr[:a.limit]
model = (RTDETR if a.rtdetr else YOLO)(a.weights)
os.makedirs(a.out, exist_ok=True)
n = skip = miss = 0
t0 = time.time()
for f in fr:
    o = os.path.join(a.out, f['key'] + '.json')
    p = os.path.join(a.cache, f['key'] + '.jpg')
    if os.path.exists(o):
        skip += 1
        continue
    if not os.path.exists(p):
        miss += 1
        continue
    iw = Image.open(p).size[0]
    r = model.predict(p, imgsz=a.imgsz, conf=a.conf, max_det=300, device=a.device, verbose=False)[0]
    sc = f['width'] / iw
    boxes = []
    for (x1, y1, x2, y2), c in zip(r.boxes.xyxy.cpu().tolist(), r.boxes.conf.cpu().tolist()):
        boxes.append([round(x1 * sc, 1), round(y1 * sc, 1), round((x2 - x1) * sc, 1), round((y2 - y1) * sc, 1), round(c, 4)])
    json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': f['width'], 'height': f['height'],
               'infer_size': a.imgsz, 'boxes': boxes}, open(o, 'w'), ensure_ascii=False)
    n += 1
    if n % 200 == 0:
        print(n, 'predicted', round(time.time() - t0), 's', flush=True)
print('predicted', n, 'skipped(existing)', skip, 'no image', miss)
