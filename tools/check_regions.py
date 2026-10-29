"""確認 1: index.json の範囲が矩形か、キャンバスの外に出ていないか、重複が無いかを数える。
    python3 -I tools/kunshujo/check_regions.py <index.json> <manifestフォルダ> <split.tsv> <出力TSV>
出力TSVは (canvas, x, y, w, h, book) の全範囲（以降の確認で使う）。
"""
import csv, hashlib, json, os, re, sys, collections
rows = json.load(open(sys.argv[1])); mdir = sys.argv[2]
split = {r['book_id'] for r in csv.DictReader(open(sys.argv[3]), delimiter='\t')}
size = {}; 
for f in os.listdir(mdir):
    m = json.load(open(os.path.join(mdir, f)))
    cs = m['sequences'][0]['canvases'] if 'sequences' in m else m.get('items', [])
    for c in cs: size[c.get('@id') or c['id']] = (c['width'], c['height'])
num = r'-?\d+(?:\.\d+)?'
pat = re.compile(r'^#xywh=(%s),(%s),(%s),(%s)$' % ((num,) * 4)); 
cnt = collections.Counter(); regs = []; ex = collections.defaultdict(list)
for r in rows:
    b = r['book'][0][1:r['book'][0].index(']')] if r.get('book') else ''
    if b not in split: cnt['not_in_94_books'] += 1; continue
    mem = r['member']; can, sep, frag = mem.partition('#')
    cnt['total'] += 1
    m = pat.match(sep + frag) if sep else None
    if not m:
        k = 'no_selector' if not sep else 'other_selector'; cnt[k] += 1; ex[k].append(mem); continue
    x, y, w, h = map(float, m.groups())
    if x < 0 or y < 0: cnt['negative_xy'] += 1; ex['negative_xy'].append(mem)
    if w <= 0 or h <= 0: cnt['nonpositive_size'] += 1; ex['nonpositive_size'].append(mem); continue
    if can not in size: cnt['canvas_not_in_manifest'] += 1; ex['canvas_not_in_manifest'].append(mem); continue
    W, H = size[can]
    if x + w > W + 0.5 or y + h > H + 0.5: cnt['outside_canvas'] += 1; ex['outside_canvas'].append((mem, W, H))
    if w * h < 0.0005 * W * H: cnt['tiny(<0.05% of canvas)'] += 1
    if w * h > 0.9 * W * H: cnt['huge(>90% of canvas)'] += 1
    if any(abs(v - round(v)) > 1e-9 for v in (x, y, w, h)): cnt['non_integer'] += 1
    regs.append((can, x, y, w, h, b))
def iou(a, b):
    x1, y1 = max(a[1], b[1]), max(a[2], b[2]); x2, y2 = min(a[1]+a[3], b[1]+b[3]), min(a[2]+a[4], b[2]+b[4])
    i = max(0, x2-x1) * max(0, y2-y1); u = a[3]*a[4] + b[3]*b[4] - i
    return i / u if u else 0
by = collections.defaultdict(list)
for g in regs: by[g[0]].append(g)
dup = exact = 0
for c, L in by.items():
    for i in range(len(L)):
        for j in range(i+1, len(L)):
            v = iou(L[i], L[j])
            if v > 0.9: dup += 1
            if L[i][1:5] == L[j][1:5]: exact += 1
cnt['dup_pairs_iou>0.9'] = dup; cnt['dup_pairs_exact'] = exact; cnt['regions_ok'] = len(regs); cnt['frames'] = len(by)
for k, v in cnt.items(): print(k, v)
for k, v in ex.items(): print('EX', k, v[:3])
regs.sort(key=lambda g: (g[0], g[1], g[2], g[3], g[4]))
with open(sys.argv[4], 'w') as f:
    f.write('canvas\tx\ty\tw\th\tbook\n')
    for g in regs: f.write('\t'.join(map(str, g)) + '\n')
