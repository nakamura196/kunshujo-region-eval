"""2 つの分類（1 行 1 件の JSON: id, class）の一致率と Cohen のカッパ、内訳を出す。

    python3 -I tools/kunshujo/kappa.py <A.jsonl> <B.jsonl> [items.tsv]

items.tsv を渡すと、kind（human / machine）ごとの内訳も出す。
"""
import collections, csv, json, sys

CL = ['機械の誤り', '切り方の方針の違い', '正解側の誤り', '判断できない']


def load(p):
    return {int(d['id']): d['class'] for d in (json.loads(l) for l in open(p) if l.strip().startswith('{'))}


A, B = load(sys.argv[1]), load(sys.argv[2])
ids = sorted(set(A) & set(B))
n = len(ids)
po = sum(A[i] == B[i] for i in ids) / n
ca, cb = collections.Counter(A[i] for i in ids), collections.Counter(B[i] for i in ids)
pe = sum(ca[c] * cb[c] for c in CL) / n / n
out = {'n': n, 'only_A': len(set(A) - set(B)), 'only_B': len(set(B) - set(A)), 'agree': round(po, 4),
       'kappa': round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0,
       'A': {c: ca[c] for c in CL}, 'B': {c: cb[c] for c in CL},
       'confusion': {a: {b: sum(A[i] == a and B[i] == b for i in ids) for b in CL} for a in CL}}
if len(sys.argv) > 3:
    kind = {int(r['id']): r['kind'] for r in csv.DictReader(open(sys.argv[3]), delimiter='\t')}
    for k in ('human', 'machine'):
        out['A_' + k] = {c: sum(kind[i] == k and A[i] == c for i in ids) for c in CL}
        out['B_' + k] = {c: sum(kind[i] == k and B[i] == c for i in ids) for c in CL}
print(json.dumps(out, ensure_ascii=False, indent=1))
