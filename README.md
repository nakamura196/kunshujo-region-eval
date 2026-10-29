# kunshujo-region-eval

Data and code for the paper “How humans draw boundaries of pasted ephemera and where machines diverge: evaluating region detection on the *Kunshūjō* scrapbook dataset” (Satoru Nakamura, The University of Tokyo; submitted to *Digital Scholarship in the Humanities*).

論文「貼り込み資料の切り出しを人はどう描き、機械はどこで外れるか —『捃拾帖』の範囲データによる領域検出の評価」の評価データとスクリプトです。

The human bounding boxes come from the public *Kunshūjō* catalog data of the University of Tokyo General Library (`index.json` of [utda/kunshujo-i](https://github.com/utda/kunshujo-i)). Page images are not included; every frame is referenced by its IIIF canvas URI.

## Contents

| Path | What it is |
|---|---|
| `data/split.tsv` | Book-level split (47 development / 47 test volumes, seed `20261016`) |
| `data/dev-tune.tsv`, `data/learning-curve-subsets.tsv` | Training/tuning split of the development volumes and the 5/10/19-volume subsets |
| `data/test_frames.json` | The 5,937 test frames (5,929 after excluding click-error regions ≤ 10 px) |
| `data/test300_canvases.json` | The 300-frame subset used for Qwen2.5-VL |
| `data/regions.tsv`, `data/frame-coverage.tsv`, `data/library-collection.tsv` | Region list and frame coverage used in the ground-truth audit (Section 2) |
| `eval/tune/<condition>/` | Thresholds selected on the tuning volumes (`tune.txt`, with weight SHA-256) and tuning results |
| `eval/test-eval/` | Evaluation configs and the test-set results (`summary.json`, `per-book.tsv`) reported in the paper |
| `eval/public-weights-README.txt` | Source and SHA-256 of the public weights `best.pt` (condition `c`) |
| `classify/PROMPT.md` | Pre-registered guideline for classifying disagreements |
| `classify/b1-test300/items.tsv` | The 300 sampled disagreements of `b1` (YOLO11s) |
| `classify/b1-test300/pass1.jsonl`, `pass2.jsonl` | Labels from Pass 1 (Claude Opus) and Pass 2 (Claude Sonnet) |
| `classify/b1-test300/gemini50.jsonl` | Labels from Gemini 4 Argon on the 50-item subset |
| `classify/b1-test300/author50_blind.original.tsv` | The author's first labels on the 50 items, made without seeing model labels (primary) |
| `classify/b1-test300/author50_revised.tsv` | The author's labels after re-examining 3 items (`original` and `revised` columns) |
| `classify/b1-test300/author50_nonblind.tsv` | An earlier check of the same 50 items made with the Pass 1 labels visible (not blind) |
| `classify/b1-test300/neighbors13.tsv` | Neighbouring-frame check of the 13 apparent omissions (Section 4.4.4) |
| `tools/` | All scripts used for splitting, training, inference, evaluation, sampling and classification |
| Release assets `test-pred-*.tar.gz`, `empty-pred-*.tar.gz` | Per-frame predictions of every condition (not in git because of size) |

## Reproducing the test-set numbers

```
# 1. Get index.json from utda/kunshujo-i and the prediction archives from the GitHub release
mkdir -p predictions/test-pred
for f in test-pred-*.tar.gz; do tar -xzf $f -C predictions/test-pred; done

# 2. Main evaluation (Table 2)
python3 -I tools/eval_final.py run --index <index.json> --split data/split.tsv --config eval/test-eval/config-main-ms10.json --out out/main-ms10 --allow-test
```

Run the commands from the repository root. Some scripts still carry default paths from the original working tree (`strengthening/kunshujo-eval/...`); pass the paths explicitly.

`data/test_frames.json` and `data/test300_canvases.json` were regenerated on 2026-10-29 because the original files were lost (`tools/make_frames.py` with the IIIF manifests; the 300-frame list from the Qwen2.5-VL predictions). With them, all F1 values and bootstrap intervals in `eval/test-eval/` were reproduced exactly; AP values differed by at most 0.0001.

Counting human boxes that contain two or more machine boxes and the reverse (Section 4.4.3):

```
python3 -I tools/granularity.py --index <index.json> --pred predictions/test-pred/b1-yolo11s
```

## Licence

Code: MIT. Data produced in this study (splits, predictions, labels): CC BY 4.0. The underlying *Kunshūjō* catalog data and images belong to the University of Tokyo General Library and follow its terms of use.
