"""確かめる帖のコマから 300 コマを乱数 (種 20261016) で選ぶ。画像は取得しない・開かない。

    python3 -I tools/kunshujo/sample_test300.py --split <split.tsv> --frames <frames.json> --out <選んだコマの frames.json> [--keys-out <key 一覧>]
    動作確認は dev のコマで: ... --which dev --n 300  (確かめる帖のコマ一覧を渡さずに論理だけ試す)

  - frames.json の形は run_best_pt.py の frames が作るもの (canvas, book_id, width, height, service, key)。
  - 対象は split.tsv で --which (既定 test) の帖のコマ。canvas の文字列順に並べてから
    random.Random(20261016).sample(並べたコマ, 300)。
  - 選んだ結果は canvas 順に並べ直して書く。
"""
import argparse, csv, json, random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', required=True)
    ap.add_argument('--frames', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--keys-out')
    ap.add_argument('--which', default='test', choices=['test', 'dev'])
    ap.add_argument('--n', type=int, default=300)
    a = ap.parse_args()
    sp = {r['book_id']: r['split'] for r in csv.DictReader(open(a.split), delimiter='\t')}
    fr = sorted((f for f in json.load(open(a.frames)) if sp.get(f['book_id']) == a.which), key=lambda f: f['canvas'])
    assert len(fr) >= a.n, f'{a.which} のコマが {len(fr)} しかない'
    pick = sorted(random.Random(20261016).sample(fr, a.n), key=lambda f: f['canvas'])
    json.dump(pick, open(a.out, 'w'), ensure_ascii=False)
    if a.keys_out:
        open(a.keys_out, 'w').write('\n'.join(f['key'] for f in pick) + '\n')
    print(a.which, 'frames', len(fr), 'picked', len(pick), 'books', len({f['book_id'] for f in pick}))


main()
