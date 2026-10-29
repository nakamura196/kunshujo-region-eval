import json,sys,hashlib,statistics as st
from collections import defaultdict
d=json.load(open(sys.argv[1])); rows=json.load(open(sys.argv[2]))
img={i['id']:i for i in d['images']}
ds=defaultdict(list)
for a in d['annotations']: ds[a['image_id']].append(a['bbox'])
hu=defaultdict(list)
for r in rows:
    can,_,frag=r['member'].partition('#xywh=')
    if not frag: continue
    hu[hashlib.md5(can.encode()).hexdigest()].append([float(v) for v in frag.split(',')])
def iou(a,b):
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[0]+a[2],b[0]+b[2]),min(a[1]+a[3],b[1]+b[3])
    i=max(0,x2-x1)*max(0,y2-y1); u=a[2]*a[3]+b[2]*b[3]-i
    return i/u if u else 0
def match(A,B):
    pairs=sorted(((iou(a,b),i,j) for i,a in enumerate(A) for j,b in enumerate(B)),reverse=True)
    ua,ub,res=set(),set(),[]
    for v,i,j in pairs:
        if i in ua or j in ub or v<=0: continue
        ua.add(i);ub.add(j);res.append(v)
    return res
scales=[];ious=[];cnt_eq=0;nds=nhu=0;imgs=0;per=[]
for k,boxes in ds.items():
    H=hu.get(k)
    if not H: continue
    imgs+=1
    # 縮尺: 画像は幅 1024 に縮小。人の範囲を同じ縮尺へ。縮尺は格子で探す
    best=(-1,None)
    for s in [x/1000 for x in range(1000,12001,5)]:
        Hs=[[v/s for v in b] for b in H]
        m=match(boxes,Hs); sc=sum(m)
        if sc>best[0]: best=(sc,s,m)
    _,s,m=best; scales.append(s); ious+=m
    nds+=len(boxes); nhu+=len(H); cnt_eq+= len(boxes)==len(H)
    per.append((k,len(boxes),len(H),min(m) if m else 0))
print('images',imgs,'ds boxes',nds,'human boxes',nhu,'same count imgs',cnt_eq)
print('scale median',st.median(scales),'min',min(scales),'max',max(scales))
print('matched',len(ious),'IoU median',round(st.median(ious),4))
for t in (0.5,0.75,0.9,0.95,0.99): print(f'IoU>={t}',sum(v>=t for v in ious))
diff=[p for p in per if p[1]!=p[2]]
print('count-diff imgs',len(diff),'examples',diff[:8])
low=sorted(per,key=lambda p:p[3])[:8]; print('lowest min-IoU',low)
