# kunshujo-region-eval

Data and code for the paper “Evaluating item detection in Japanese scrapbooks against an existing catalogue: supervised detectors and a zero-shot large multimodal model on the *Kunshūjō*” (Satoru Nakamura, The University of Tokyo; submitted to *Digital Scholarship in the Humanities*).

Terms: this repository says "human boxes" where the paper says catalogue boxes (Kunshūjō) or reference boxes (external scrapbooks), and "machine boxes" for predicted boxes.

論文「貼込帖の紙片の自動検出を既存の目録で確かめる —『捃拾帖』における公開 YOLOv5・学習し直した YOLOv5・Gemini 4 の比較」の評価データとスクリプトです。

The human bounding boxes come from the public *Kunshūjō* catalogue data of the University of Tokyo General Library (`index.json` of [utda/kunshujo-i](https://github.com/utda/kunshujo-i)). Page images are not included; every frame is referenced by its IIIF canvas URI.

## Condition names

| Name in files | Method in the paper |
|---|---|
| `c` | Public YOLOv5 weights (`best.pt`, see `eval/public-weights-README.txt`) |
| `b0` (`b0-yolov5x`) | Retrained YOLOv5 (38 training volumes) |
| `gemini` (`a4` in the working notes) | Gemini 4 Argon, zero-shot |
| `a2` | Qwen2.5-VL-7B, zero-shot |
| `a1` | DocLayout-YOLO, zero-shot |
| `b1` (`b1-yolo11s`), `b2` (`b2-rtdetr-l`) | YOLO11s and RT-DETR-l trained on the training volumes (Section 4.1, last paragraph) |

## Contents

| Path | What it is | Paper |
|---|---|---|
| `data/split.tsv` | Book-level split (47 development / 47 test volumes, seed `20261016`) | 2.2 |
| `data/dev-tune.tsv` | Training (38) / validation (9) split of the development volumes | 2.2 |
| `data/test_frames.json` | The 5,929 test frames (after dropping human boxes whose shorter side is 10 px or less) | 2.2 |
| `data/test300_canvases.json` | The 300 test frames used to compare all methods | 2.2, Table 1 |
| `eval/tune/<condition>/` | Confidence thresholds selected on the tuning volumes (`tune.txt`, with weight SHA-256) | 3.1 |
| `eval/test-eval/sub300-ms10/` | Table 1: public and retrained YOLOv5, Qwen2.5-VL, DocLayout-YOLO on the 300 frames | 4.1 |
| `eval/test-eval/sub300-gemini/` | Table 1: Gemini on the 300 frames, its differences from the two YOLOv5 models, and the second Gemini run | 4.1, 6 |
| `eval/test-eval/main-ms10/` | All 5,929 test frames: public weights 0.801, retrained YOLOv5 0.756, YOLO11s 0.754, RT-DETR-l 0.766 | 4.1 |
| `eval/public-weights-README.txt` | Source and SHA-256 of the public weights `best.pt` | 3.1 |
| `gemini300/` | Gemini's raw answers and per-frame predictions on the 300 frames, two runs (see `gemini300/README.md`) | 3.1, 6 |
| `unmatched/` | The judging of unmatched boxes: sampled boxes, the author's judgements, sub-categories (see `unmatched/README.md`) | 3.3, Table 2 |
| `external/` | The two other scrapbooks: candidate frames, the author's boxes, all predictions and Gemini runs, configs and results (see `external/README.md`) | 2.3, Table 3 |
| `tools/` | All scripts used for splitting, training, inference, evaluation, sampling and judging | |
| Release assets `test-pred-*.tar.gz` | Per-frame predictions of every trained or zero-shot detector on all test frames (not in git because of size) | |

### Files from earlier analyses (not reported in the submitted paper)

These were made for an earlier version of the study and are kept for transparency.

| Path | What it is |
|---|---|
| `classify/` | Classification of 300 sampled disagreements of `b1` (YOLO11s) by Claude and Gemini, and the author's labels on 50 of them; the guideline is `classify/PROMPT.md` (Japanese) and `PROMPT.en.md` |
| `docs/fixed-in-advance.md` | What was fixed before the test volumes were scored, with notebook commit dates |
| `data/regions.tsv`, `data/frame-coverage.tsv`, `data/library-collection.tsv` | Region list and frame coverage used to audit the human boxes |
| `data/learning-curve-subsets.tsv`, `eval/tune/lc-*` | Learning-curve subsets (5/10/19 training volumes) |
| Release assets `empty-pred-*.tar.gz` | Predictions on frames without human boxes |

## Reproducing the numbers

Run the commands from the repository root. `<index.json>` is `index.json` from `utda/kunshujo-i`.

```
# Prediction archives from the GitHub release (only c and b0-yolov5x are needed for Gemini's part of Table 1)
mkdir -p predictions/test-pred
for f in test-pred-*.tar.gz; do tar -xzf $f -C predictions/test-pred; done

# Table 1 (YOLOv5, Qwen2.5-VL, DocLayout-YOLO)
python3 -I tools/eval_final.py run --index <index.json> --split data/split.tsv --config eval/test-eval/config-sub300-ms10.json --out out/sub300-ms10 --allow-test

# Table 1 (Gemini) and its differences
python3 -I tools/eval_final.py run --index <index.json> --split data/split.tsv --config eval/test-eval/config-sub300-gemini.json --out out/sub300-gemini --allow-test

# All test frames (Section 4.1)
python3 -I tools/eval_final.py run --index <index.json> --split data/split.tsv --config eval/test-eval/config-main-ms10.json --out out/main-ms10 --allow-test

# Table 2
python3 -I tools/count_unmatched.py
```

Table 3 is reproduced as described in `external/README.md`.

Some scripts still carry default paths from the original working tree (`~/git/tmp/...`, `strengthening/kunshujo-eval/...`); pass the paths explicitly.

`data/test_frames.json` and `data/test300_canvases.json` were regenerated on 2026-10-29 because the original files were lost (`tools/make_frames.py` with the IIIF manifests; the 300-frame list from the Qwen2.5-VL predictions). With them, all F1 values and bootstrap intervals in `eval/test-eval/` were reproduced exactly; AP values differed by at most 0.0001.

## Licence

Code: MIT. Data produced in this study (splits, predictions, judgements, the author's boxes): CC BY 4.0. The underlying *Kunshūjō* catalogue data and images belong to the University of Tokyo General Library and follow its terms of use. The Taitō City Library images are CC BY 4.0; the NDL images are in the public domain.
