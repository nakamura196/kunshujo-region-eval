"""Gemini（agy）や Claude に 1 回で数コマずつ枠を答えさせた生の文章を、コマごとの予測 JSON に直す（実験 3 の a4・a5、実験 2 の枠付け）。

    python3 -I tools/kunshujo/gen_lines_to_pred.py --frames <frames.json> --keys-file <その回のコマの順> --raw <生の出力> --out <pred/> --model <名前> [--order xy|yx]

  - 生の出力は 1 コマ 1 行の JSON: {"image": n, "boxes": [{"bbox_2d": [x1, y1, x2, y2], ...}]}。n は --keys-file の行番号（1 から）。
  - 座標は 0〜1000 に正規化したものとして canvas 原寸に直す。--order yx なら [y1, x1, y2, x2] と読む（Gemini の既定の書き方）。
  - 確信度は付かないので全部 1.0。生の行を raw に残す。読めなかった行は数えて表示し、そのコマは書かない。
  - 同じ番号の行が 2 度出たら後の行を採る（agy は答えを途中から出し直すことがある。2026-10-29 に 10 コマ中 8 コマで起きた）。
"""
import argparse, json, os, re

ap = argparse.ArgumentParser()
for k in ('frames', 'keys-file', 'raw', 'out', 'model'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--order', default='xy', choices=['xy', 'yx'])
a = ap.parse_args()
keys = [l.strip() for l in open(a.keys_file) if l.strip()]
byk = {f['key']: f for f in json.load(open(a.frames))}
os.makedirs(a.out, exist_ok=True)
last, bad = {}, 0
for line in open(a.raw):
    m = re.search(r'\{.*\}', line)
    if not m:
        continue
    try:
        d = json.loads(m.group(0))
        n = int(d['image'])
        bs = [x['bbox_2d'] for x in d['boxes'] if isinstance(x, dict) and len(x.get('bbox_2d', [])) == 4]
    except Exception:
        bad += 1
        continue
    if not 1 <= n <= len(keys):
        bad += 1
        continue
    last[n] = (line, bs)
for n, (line, bs) in sorted(last.items()):
    f = byk[keys[n - 1]]
    W, H = f['width'], f['height']
    boxes = []
    for b in bs:
        x1, y1, x2, y2 = [float(v) for v in b]
        if a.order == 'yx':
            x1, y1, x2, y2 = y1, x1, y2, x2
        x1, x2 = sorted((max(0, x1), min(1000, x2)))
        y1, y2 = sorted((max(0, y1), min(1000, y2)))
        if x2 > x1 and y2 > y1:
            boxes.append([round(x1 * W / 1000, 1), round(y1 * H / 1000, 1), round((x2 - x1) * W / 1000, 1), round((y2 - y1) * H / 1000, 1), 1.0])
    json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': W, 'height': H, 'model': a.model,
               'coords': 'norm1000-' + a.order, 'raw': line.strip(), 'boxes': boxes},
              open(os.path.join(a.out, f['key'] + '.json'), 'w'), ensure_ascii=False)
print(f'written {len(last)}/{len(keys)} unreadable_lines {bad} missing {[i for i in range(1, len(keys) + 1) if i not in last]}')
