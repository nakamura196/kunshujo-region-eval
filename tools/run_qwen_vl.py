"""Qwen2.5-VL-7B-Instruct (mlx-vlm、手元で動かす) に、貼り込まれた紙片の枠を出させる。学習はしない。

    <venv-vlm>/bin/python -I tools/kunshujo/run_qwen_vl.py --frames <frames.json> --cache <frames_dev/> --model <モデルのフォルダ> --out <pred/> --prompt P1 [--keys-file <list>] [--limit N]

  - frames.json (または keys-file) に載っているコマだけを扱う。確かめる帖の画像は、設定を凍結するまで渡さない。
  - 画像は長辺 1008 以下・28 の倍数に自分で縮めてから渡す。モデルが出す座標はこの縮めた画像の画素なので、
    canvas 原寸への換算は (canvas 幅 / 縮めた幅) で行う。モデル側でそれ以上は縮められない。
  - 温度 0 (貪欲)、最大 2048 トークン。確信度は付かないので全部 1.0。
  - モデルの生の文章を raw に残す。JSON として読めなかったコマは parse_ok=false (枠は正規表現で拾えた分だけ入れる)。
"""
import argparse, json, os, re, time
from PIL import Image

PROMPTS = {
    'P1': ('This is a page from a Japanese scrapbook album. Pieces of paper (clippings, prints, letters, cards, '
           'documents) are pasted onto the page. Locate every pasted piece of paper and output its bounding box '
           'coordinates in JSON format.'),
    'P2': ('This image is a page of a Japanese scrapbook album. Each separate pasted paper item (a clipping, print, '
           'letter, card, document or sheet glued onto the album page) counts as one item. Do not include the album '
           'page itself, the binding, or empty background. If a pasted item is overlapped by another, still give one '
           'box per item. Detect all pasted paper items and output a JSON list, one entry per item, in the form '
           '[{"bbox_2d": [x1, y1, x2, y2], "label": "paper"}].'),
    'P3': ('Detect all the pasted paper items in this image. Output the bounding box of each item in JSON format: '
           '[{"bbox_2d": [x1, y1, x2, y2], "label": "pasted paper"}].'),
}


def resize(img, long_side=1008):
    w, h = img.size
    s = min(1.0, long_side / max(w, h))
    nw, nh = max(28, int(w * s) // 28 * 28), max(28, int(h * s) // 28 * 28)
    return img.resize((nw, nh), Image.LANCZOS)


def parse(text):
    """(boxes[x1,y1,x2,y2 リスト], parse_ok)。"""
    t = text.strip()
    m = re.search(r'```(?:json)?\s*(.*?)```', t, re.S)
    if m:
        t = m.group(1).strip()
    try:
        d = json.loads(t)
        if isinstance(d, dict):
            d = [d]
        bs = [x['bbox_2d'] for x in d if isinstance(x, dict) and isinstance(x.get('bbox_2d'), list) and len(x['bbox_2d']) == 4]
        return [[float(v) for v in b] for b in bs], True
    except Exception:
        bs = re.findall(r'"bbox_2d"\s*:\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]', t)
        return [[float(v) for v in b] for b in bs], False


def main():
    ap = argparse.ArgumentParser()
    for k in ('frames', 'cache', 'model', 'out'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--prompt', required=True, choices=sorted(PROMPTS))
    ap.add_argument('--keys-file')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--max-tokens', type=int, default=2048)
    ap.add_argument('--long-side', type=int, default=1008)
    a = ap.parse_args()
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    model, proc = load(a.model)
    cfg = model.config if hasattr(model, 'config') else None
    os.makedirs(a.out, exist_ok=True)
    fr = json.load(open(a.frames))
    if a.keys_file:
        order = [l.strip() for l in open(a.keys_file) if l.strip()]
        byk = {f['key']: f for f in fr}
        fr = [byk[k] for k in order if k in byk]
    if a.limit:
        fr = fr[:a.limit]
    prompt = apply_chat_template(proc, cfg, PROMPTS[a.prompt], num_images=1)
    tmp = os.path.join(a.out, '_resized.png')
    n = 0
    for f in fr:
        ip, op = os.path.join(a.cache, f['key'] + '.jpg'), os.path.join(a.out, f['key'] + '.json')
        if not os.path.exists(ip) or os.path.exists(op):
            continue
        img = resize(Image.open(ip).convert('RGB'), a.long_side)
        img.save(tmp)
        t0 = time.time()
        res = generate(model, proc, prompt, image=tmp, max_tokens=a.max_tokens, temperature=0.0, verbose=False)
        sec = time.time() - t0
        text = res.text if hasattr(res, 'text') else str(res)
        bs, ok = parse(text)
        sx, sy = f['width'] / img.size[0], f['height'] / img.size[1]
        boxes = []
        for x1, y1, x2, y2 in bs:
            x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2))
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img.size[0], x2), min(img.size[1], y2)
            if x2 > x1 and y2 > y1:
                boxes.append([round(x1 * sx, 1), round(y1 * sy, 1), round((x2 - x1) * sx, 1), round((y2 - y1) * sy, 1), 1.0])
        json.dump({'canvas': f['canvas'], 'book_id': f['book_id'], 'width': f['width'], 'height': f['height'],
                   'prompt': a.prompt, 'resized': list(img.size), 'seconds': round(sec, 2), 'parse_ok': ok,
                   'raw': text, 'boxes': boxes}, open(op, 'w'), ensure_ascii=False)
        n += 1
        print(n, f['key'][:8], round(sec, 1), 's', len(boxes), 'boxes', 'ok' if ok else 'PARSE_FAIL', flush=True)
    if os.path.exists(tmp):
        os.remove(tmp)


main()
