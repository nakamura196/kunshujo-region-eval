"""check_regions.py の補足: はみ出しの大きさと、重複の帖別の数。 python3 -I check_regions2.py regions.tsv manifestフォルダ"""
import csv, json, os, sys, collections
size = {}
for f in os.listdir(sys.argv[2]):
    m = json.load(open(os.path.join(sys.argv[2], f)))
    for c in (m['sequences'][0]['canvases'] if 'sequences' in m else m.get('items', [])): size[c.get('@id') or c['id']] = (c['width'], c['height'])
R = list(csv.DictReader(open(sys.argv[1]), delimiter='\t'))
ov = []; 
for r in R:
    x, y, w, h = (float(r[k]) for k in 'xywh'); W, H = size[r['canvas']]
    d = max(-x, -y, x+w-W, y+h-H)
    if d > 0.5: ov.append((round(d, 1), r['book']))
print('outside max px', max(ov), 'books', collections.Counter(b for _, b in ov), 'sorted', sorted(d for d, _ in ov))
by = collections.defaultdict(list)
for r in R: by[r['canvas']].append(tuple(float(r[k]) for k in 'xywh') + (r['book'],))
def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1]); x2, y2 = min(a[0]+a[2], b[0]+b[2]), min(a[1]+a[3], b[1]+b[3])
    i = max(0, x2-x1)*max(0, y2-y1); return i/(a[2]*a[3]+b[2]*b[3]-i)
c = collections.Counter(); fr = set()
for k, L in by.items():
    for i in range(len(L)):
        for j in range(i+1, len(L)):
            if iou(L[i], L[j]) > .9: c[L[i][4]] += 1; fr.add(k)
print('dup by book', c, 'frames', len(fr))
tiny = sorted((float(r['w'])*float(r['h']), r['book']) for r in R)[:5]; print('smallest', tiny)
