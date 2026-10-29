#!/usr/bin/env zsh
# 条件 (b): dev の帖だけで学習し、調整 9 帖でしきい値を決める。
# 使い方: zsh tools/kunshujo/train_b.zsh <ul|v5> <名前> <モデル> <data.yaml> [seed]
#   ul: ultralytics (YOLO11s は yolo11s.pt、RT-DETR-l は rtdetr-l.pt)  v5: YOLOv5x (v7.0 の clone)
# EPOCHS（既定 100）で最大エポックを変えられる。
# DEVICE（既定 mps。GPU なら 0）、WORKERS（v5 の dataloader、既定 2）、R・IDX（リポジトリと index.json の場所）も環境変数で変えられる。
# TEST=1 なら、しきい値を決めた後に確かめる帖 ($S/test_frames.json, $S/frames_test) にも確信度 0.001 で推論し、
# strengthening/kunshujo-eval/test-pred/<名前> に出す（採点はしない）。
# 前提: 環境変数 S (作業用フォルダ) と、$S/yolo-dev, $S/dev_frames.json, $S/tune_frames.json, $S/frames_dev がある。
set -uo pipefail
kind=$1 name=$2 model=$3 data=$4 seed=${5:-0}
R=${R:-~/git/digital-archive-papers}
DEVICE=${DEVICE:-mps}
TB=$R/strengthening/kunshujo-eval/train-b
IDX=${IDX:-~/git/utda/kunshujo/static/data/index.json}
mkdir -p $TB/runs
cd $TB
t0=$(date +%s)
if [[ $kind == ul ]]; then
  PY=$S/venv-ul/bin/python
  $S/venv-ul/bin/yolo detect train model=$model data=$data imgsz=640 epochs=${EPOCHS:-100} patience=20 batch=${BATCH:-32} device=$DEVICE seed=$seed project=$TB/runs name=$name exist_ok=True plots=False > $TB/runs/$name.log 2>&1
  W=$TB/runs/$name/weights/best.pt
  $PY -I $R/tools/kunshujo/predict_ul.py --weights $W --frames $S/tune_frames.json --cache $S/frames_dev --out $TB/pred-$name/pred-0.001 --conf 0.001 --device $DEVICE $( [[ $model == rtdetr* ]] && echo --rtdetr ) > $TB/runs/$name.pred.log 2>&1
else
  cd $S/yolo_env/yolov5
  PYTHONPATH=$S/v5extra $S/yolo_env/venv/bin/python $R/tools/kunshujo/train_v5.py --weights yolov5x.pt --data $data --img 640 --epochs ${EPOCHS:-100} --patience 20 --batch-size ${BATCH:-16} --device $DEVICE --workers ${WORKERS:-2} --noplots --seed $seed --project $TB/runs --name $name --exist-ok > $TB/runs/$name.log 2>&1
  W=$TB/runs/$name/weights/best.pt
  $S/yolo_env/venv/bin/python -I $R/tools/kunshujo/predict_v5.py --yolov5 $S/yolo_env/yolov5 --weights $W --frames $S/tune_frames.json --cache $S/frames_dev --out $TB/pred-$name/pred-0.001 --conf 0.001 --device $DEVICE > $TB/runs/$name.pred.log 2>&1
fi
t1=$(date +%s)
python3 -I $R/tools/kunshujo/tune_eval.py --index $IDX --split $R/strengthening/kunshujo-eval/split.tsv --frames $S/tune_frames.json --pred $TB/pred-$name/pred-0.001 --out $TB/pred-$name > $TB/pred-$name/tune.txt 2>&1
echo "$name train+predict seconds: $((t1-t0)); sha256: $(shasum -a 256 $W | cut -d' ' -f1)" >> $TB/pred-$name/tune.txt
cat $TB/pred-$name/tune.txt
if [[ ${TEST:-0} == 1 ]]; then
  TP=$R/strengthening/kunshujo-eval/test-pred/$name
  if [[ $kind == ul ]]; then
    $PY -I $R/tools/kunshujo/predict_ul.py --weights $W --frames $S/test_frames.json --cache $S/frames_test --out $TP --conf 0.001 --device $DEVICE $( [[ $model == rtdetr* ]] && echo --rtdetr ) > $TB/runs/$name.test.log 2>&1
  else
    $S/yolo_env/venv/bin/python -I $R/tools/kunshujo/predict_v5.py --yolov5 $S/yolo_env/yolov5 --weights $W --frames $S/test_frames.json --cache $S/frames_test --out $TP --conf 0.001 --device $DEVICE > $TB/runs/$name.test.log 2>&1
  fi
  echo "$name test predictions: $(ls $TP | wc -l | tr -d ' ') files in $TP"
fi
