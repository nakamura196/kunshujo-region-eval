#!/usr/bin/env zsh
# 条件 (b) の残りの学習を mdx（A100）で流す（docs/notes/kunshujo-eval.md 2026-10-20 の決めごと）。
# 使い方（mdx の上で）: nohup zsh ~/k42/repo/tools/kunshujo/run_rest_mdx.zsh > ~/k42/S/rest.log 2>&1 &
# 前提: ~/k42/S に dev_frames.json・test_frames.json・tune_frames.json・venv-ul・yolo_env があり、
#   画像の取得（run_best_pt.py fetch）が frames_dev・frames_test に向けて動いているか、済んでいる。
# 何をするか:
#   1. 画像の取得が終わるのを待つ（最大 3 時間）。取れなかった画像の数を出す
#   2. yolo-dev（make_yolo_dev.py）と学習曲線の部分集合（make_subsets.py）を作り、
#      部分集合が手元の learning-curve-subsets.tsv と同じかを確かめる
#   3. 2 列で学習する。列 1: b0 → b2（各 30 エポック）。列 2: lc-19 → b1-seed1 → b1-seed2 → b1-cuda
#      各モデルは train_b.zsh（TEST=1）で、学習 → 調整 9 帖でしきい値 → 確かめる帖の推論まで行う
set -uo pipefail
export S=~/k42/S R=~/k42/repo IDX=~/k42/idx/index.json DEVICE=0 WORKERS=8 TEST=1
K=$R/tools/kunshujo
SP=$R/strengthening/kunshujo-eval

i=0; while pgrep -f 'run_best_pt.py fetch' >/dev/null && [ $i -lt 1080 ]; do sleep 10; i=$((i+1)); done
pgrep -f 'run_best_pt.py fetch' >/dev/null && { echo "fetch still running after 3h; stop"; exit 1; }
echo "frames_dev $(ls $S/frames_dev | grep -c '\.jpg$') / 6434, frames_test $(ls $S/frames_test | grep -c '\.jpg$') / 5937"
tail -2 $S/fetch_dev.log $S/fetch_test.log

python3 -I $K/make_yolo_dev.py --index $IDX --split $SP/split.tsv --dev-tune $SP/dev-tune.tsv --frames $S/dev_frames.json --cache $S/frames_dev --out $S/yolo-dev || exit 1
python3 -I $K/make_subsets.py --dev-tune $SP/dev-tune.tsv --yolo $S/yolo-dev --out-tsv $S/learning-curve-subsets.tsv --frames $S/dev_frames.json || exit 1
if cmp -s $S/learning-curve-subsets.tsv $SP/learning-curve-subsets.tsv; then echo "subsets: same as before"; else echo "subsets differ from before; stop"; exit 1; fi

lane1() {
  EPOCHS=30 zsh $K/train_b.zsh v5 b0-yolov5x yolov5x.pt $S/yolo-dev/data.yaml 0
  EPOCHS=30 BATCH=16 zsh $K/train_b.zsh ul b2-rtdetr-l rtdetr-l.pt $S/yolo-dev/data.yaml 0
}
lane2() {
  zsh $K/train_b.zsh ul lc-19 yolo11s.pt $S/yolo-dev/data-19.yaml 0
  zsh $K/train_b.zsh ul b1-seed1 yolo11s.pt $S/yolo-dev/data.yaml 1
  zsh $K/train_b.zsh ul b1-seed2 yolo11s.pt $S/yolo-dev/data.yaml 2
  zsh $K/train_b.zsh ul b1-cuda yolo11s.pt $S/yolo-dev/data.yaml 0
}
# SERIAL=1: 列 1 → 列 2 を順に流す（同じ GPU で国絵図の学習を並行させるとき。2026-10-20）
if [[ ${SERIAL:-0} == 1 ]]; then
  echo "serial: lane1 then lane2"
  lane1 > $S/lane1.log 2>&1
  lane2 > $S/lane2.log 2>&1
else
  lane1 > $S/lane1.log 2>&1 &
  p1=$!
  lane2 > $S/lane2.log 2>&1 &
  p2=$!
  echo "lane1 pid $p1, lane2 pid $p2"
  wait $p1 $p2
fi
echo "all done $(date)"
