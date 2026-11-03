"""外の帖（台東区〔貼交帖〕・NDL『張交帖』）で確かめるコマの一覧 (frames.json) を作り、画像を取る。

    python3 -I tools/kunshujo/make_ext_frames.py --work <作業フォルダ> [--ndl-n 30] [--seed 20261102]

  - 台東区は全 21 コマ。NDL は 13 冊 593 コマから、各冊の最初と最後のコマ（表紙・裏表紙）を除いて乱数で --ndl-n コマ。
  - frames.json は make_frames.py と同じ形（canvas, book_id, width, height, service, key）。key は canvas URI の MD5。
  - 画像は <service>/full/1024,/0/default.jpg（捃拾帖の確かめる帖と同じ幅）を <work>/frames/<key>.jpg に。既にあれば取らない。
  - 描く前に固定した手順は docs/notes/kunshujo-eval.md の 2026-11-02 の節。
"""
import argparse, hashlib, json, os, random, time, urllib.request

TAITO = 'https://adeac.jp/viewitem/taito-lib/viewer/iiif/2017_WA_004/manifest.json'
NDL_PIDS = list(range(2586692, 2586705))  # [1]〜[13]

ap = argparse.ArgumentParser()
ap.add_argument('--work', required=True)
ap.add_argument('--ndl-n', type=int, default=30)
ap.add_argument('--seed', type=int, default=20261102)
a = ap.parse_args()
os.makedirs(os.path.join(a.work, 'manifests'), exist_ok=True)
os.makedirs(os.path.join(a.work, 'frames'), exist_ok=True)


def get(url, path=None):
    if path and os.path.exists(path):
        return open(path, 'rb').read()
    req = urllib.request.Request(url, headers={'User-Agent': 'kunshujo-region-eval (research)'})
    for i in range(4):
        try:
            b = urllib.request.urlopen(req, timeout=60).read()
            break
        except Exception:
            if i == 3:
                raise
            time.sleep(5 * (i + 1))
    if path:
        open(path, 'wb').write(b)
    return b


def manifest(url, name):
    b = get(url, os.path.join(a.work, 'manifests', name + '.json'))
    return json.loads(b.decode('utf-8-sig'))  # 台東区は先頭に BOM


def key(can):
    return hashlib.md5(can.encode()).hexdigest()


frames = []
# 台東区: IIIF Presentation 3
m = manifest(TAITO, 'taito')
for c in m['items']:
    body = c['items'][0]['items'][0]['body']
    svc = body['service'][0]
    sid = svc.get('id') or svc.get('@id')
    frames.append({'canvas': c['id'], 'book_id': 'taito', 'width': c['width'], 'height': c['height'],
                   'service': sid, 'key': key(c['id'])})
# NDL: IIIF Presentation 2
ndl = []
for i, pid in enumerate(NDL_PIDS, 1):
    m = manifest(f'https://dl.ndl.go.jp/api/iiif/{pid}/manifest.json', f'ndl-{pid}')
    cs = m['sequences'][0]['canvases']
    for c in cs[1:-1]:  # 表紙・裏表紙を除く
        ndl.append({'canvas': c['@id'], 'book_id': f'ndl{i:02d}', 'width': c['width'], 'height': c['height'],
                    'service': c['images'][0]['resource']['service']['@id'], 'key': key(c['@id'])})
print('ndl canvases (covers excluded):', len(ndl))
pick = random.Random(a.seed).sample(ndl, a.ndl_n)
pick.sort(key=lambda f: (f['book_id'], ndl.index(f)))
frames += pick
json.dump(frames, open(os.path.join(a.work, 'frames.json'), 'w'), ensure_ascii=False, indent=1)
print('frames:', len(frames), {b: sum(f['book_id'] == b for f in frames) for b in sorted({f['book_id'] for f in frames})})
n = 0
for f in frames:
    p = os.path.join(a.work, 'frames', f['key'] + '.jpg')
    if not os.path.exists(p):
        get(f['service'] + '/full/1024,/0/default.jpg', p)
        n += 1
        time.sleep(0.5)
print('fetched', n)
