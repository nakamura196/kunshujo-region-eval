"""実験 3（a4 Gemini・a5 Claude）と実験 2 の枠付けで、数コマずつの指示文を作る。モデルの呼び出しそのものは外で行う。

    python3 -I tools/kunshujo/gen_detect_batch.py --prompt-file <coordcheck/prompt.txt> --cache <画像> --keys-file <list> --work <作業フォルダ> [--batch 10]

  - 指示文は --prompt-file の「Images:」の行までをそのまま使い（座標の書式の確認で使ったもの）、その後に画像の一覧を付ける。
  - 画像は --work/img にハードリンクする（agy は --add-dir で渡したフォルダしか読まないため。容量は増えない）。
  - 出力は batch_XX.keys と batch_XX.prompt。答え（batch_XX.<tag>.out）は gen_lines_to_pred.py でバッチごとに予測に直す。
"""
import argparse, os

ap = argparse.ArgumentParser()
for k in ('prompt-file', 'cache', 'keys-file', 'work'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--batch', type=int, default=10)
a = ap.parse_args()
head = open(a.prompt_file).read().split('\nImages:\n')[0] + '\nImages:\n'
img = os.path.join(a.work, 'img')
os.makedirs(img, exist_ok=True)
keys = []
for k in (l.strip() for l in open(a.keys_file)):
    src, dst = os.path.join(a.cache, k + '.jpg'), os.path.join(img, k + '.jpg')
    if not k or not os.path.exists(src):
        continue
    if not os.path.exists(dst):
        os.link(src, dst)
    keys.append(k)
for i in range(0, len(keys), a.batch):
    ks, b = keys[i:i + a.batch], i // a.batch + 1
    open(os.path.join(a.work, f'batch_{b:02d}.keys'), 'w').write('\n'.join(ks) + '\n')
    lines = ''.join(f'- image={n} file: {os.path.abspath(os.path.join(img, k + ".jpg"))}\n' for n, k in enumerate(ks, 1))
    open(os.path.join(a.work, f'batch_{b:02d}.prompt'), 'w').write(head + lines)
print('frames', len(keys), 'batches', (len(keys) + a.batch - 1) // a.batch)
