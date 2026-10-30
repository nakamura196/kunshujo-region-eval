# What was fixed before the test volumes were scored

Section 3.1 of the paper states which parts of the evaluation were fixed in advance, and when. This file lists the relevant entries of the author's laboratory notebook and the dates of the commits that contain them.

The notebook is a Markdown file (`docs/notes/kunshujo-eval.md`) in the author's private Git repository, written in Japanese. It is not a public registration, and readers cannot inspect the commits listed below. What this file adds is the exact dates and the values recorded in each entry, so that they can be compared with the files in this repository (`eval/tune/*/tune.txt`, `eval/test-eval/config-*.json`, `classify/PROMPT.md`).

## Commits of the notebook

| Commit (private repository) | Date (PDT) | Date (UTC) | Relevant content |
|---|---|---|---|
| `0390b8a4` | 2026-10-17 18:19:16 | 2026-10-18 01:19:16 | Notebook entries of 16–17 October; `classify/PROMPT.md`; the tuning split `dev-tune.tsv`; the scripts `split_books.py`, `split_dev_tune.py`, `eval_final.py`, `disagreements.py`, `kappa.py` |
| `4ed48a58` | 2026-10-29 18:45:49 | 2026-10-30 01:45:49 | Notebook entries of 20–21 October and later; the test-set results |

There were no commits of the notebook between these two.

## When the test volumes were scored

The conditions of the paper were scored once, on 21 October 2026 (notebook entry “2026-10-21 確かめる帖の採点（1 回のみ）”, “Scoring of the test volumes (once only)”). The output files `eval/test-eval/{main-ms10,sens-ms0,sub300-ms10,sub300-ms0}/summary.json` were written between 07:18 and 07:20 PDT that day (file modification times on the author's machine). Before that, predictions had been made on the test frames, but none had been compared with the human boxes. The test volumes were scored again from 29 October only for separate experiments with generative models, which are mentioned in Section 4.1 of the paper and are not among the conditions in Table 2.

## Items committed on 17 October (`0390b8a4`), before scoring

| Item | Value recorded | Notebook entry (date and heading) |
|---|---|---|
| Questions and measures | Unit of evaluation is the frame; one-to-one matching by IoU at 0.5 and 0.75; precision, recall, F1. The main measure is F1 at IoU 0.5 with a fixed threshold | 2026-10-16 問いと測り方（測る前に決める） “Questions and measures (decided before measuring)”; 2026-10-16 改訂 3 “Revision 3” |
| Split into development and test volumes | By volume; Volumes 1–18 and the rest split separately in halves; seed 20261016; 47 + 47 volumes (`data/split.tsv`) | 2026-10-16 帖の分割 “Splitting the volumes” |
| Training and tuning volumes | 38 training and 9 tuning volumes (2 from Volumes 1–18, 7 from the rest), seed 20261016 (`data/dev-tune.tsv`) | 2026-10-16 残りの条件の決めごと “Rules for the remaining conditions”; 2026-10-17 条件 (a) の設定の固定 “Fixing the settings of condition (a)” |
| Thresholds | For every condition, the confidence threshold that maximises F1 at IoU 0.5 on the tuning volumes; not changed on the test volumes | 2026-10-16 残りの条件の決めごと |
| Confidence intervals | Cluster bootstrap over volumes, 10,000 resamples, seed 20261016; paired differences on the same resamples; a difference whose interval includes zero is not reported as a difference | 2026-10-16 改訂 3 |
| Size bins | Tertiles of the area share of the human boxes on the development volumes: 0.06514 and 0.18505 | 2026-10-16 比べる道具と、大きさの境目 “Comparison tool and size bins” |
| Training budget | YOLO11s and RT-DETR-l: input 640, up to 100 epochs, stop if the tuning score does not improve for 20 epochs, default augmentation. Revised on 17 October, before scoring: YOLOv5x (b0) and RT-DETR-l (b2) up to 30 epochs. ultralytics 8.4.170, seed 0 | 2026-10-16 残りの条件の決めごと; 2026-10-17 条件 (a) の設定の固定と、学習の順番の見直し |
| a1 DocLayout-YOLO | juliozhao/DocLayout-YOLO-DocStructBench (rev 8c3299a3…), doclayout-yolo 0.0.4, input 1024, class “figure” only, confidence 0.05 | 2026-10-17 条件 (a) の設定の固定 |
| a2 Qwen2.5-VL-7B | mlx-community/Qwen2.5-VL-7B-Instruct-bf16 (rev 186c8dd5…), mlx-vlm 0.7.4, long side ≤ 1,008, temperature 0, max 2,048 tokens, prompt P2 (chosen from 3 on 50 tuning frames); run on 300 test frames chosen with seed 20261016; boxes from unclosed JSON are used as they are | 2026-10-17 条件 (a) の設定の固定; 2026-10-17 確かめる帖の推論（採点はまだ） “Inference on the test volumes (not yet scored)” |
| c public weights (best.pt) | sha256 afb897f715523f8a2a49b542124e667240f77f8c69a41fb789bd161060a63165; confidence 0.46 (chosen on all 47 development volumes, because this is a leaky reference) | 2026-10-16 best.pt の取得と ONNX への書き出し; 2026-10-16 best.pt を課題を見つける帖に流した結果 |
| b1 YOLO11s (38 volumes) | sha256 1f77f0c45c8dc747973b74e7ad08984fd075fc3121ff7a0c5350e93308c16343; confidence 0.31 | 2026-10-17 b1（YOLO11s）の固定 |
| lc-5 (5 volumes) | sha256 c58c65ae87cd8bfdb9022bc2ad010f73a830212db65120f277cc60308ffb603c; confidence 0.40 | 2026-10-17 学習曲線 lc-5（5 帖）の固定 |
| lc-10 (10 volumes) | sha256 dc343ead3df95ea808eec816930325c2fb53f41af8bff1fbfba6cf36b20adae0; confidence 0.34 | 2026-10-17 学習曲線 lc-10（10 帖）の固定 |
| Classification guideline | `classify/PROMPT.md` (unchanged since; English translation in `classify/PROMPT.en.md`); 300 disagreements of b1, seed 20261016; Claude Opus and Claude Sonnet, same images, 12 calls of 25 | 2026-10-16 残りの条件の決めごと; 2026-10-17 確かめる帖の推論（採点はまだ） |
| Author's check | The author labels 50 of the 300 items, chosen with `random.Random(20261016).sample(range(1, 301), 50)`, without seeing the model labels | 2026-10-17 分類の答え合わせを本人が行う “The author checks the classification” |
| Uncatalogued frames | b1 boxes counted on frames without human boxes in the middle of volumes; 30 development frames inspected | 2026-10-16 改訂 3; 2026-10-17 確かめる帖の推論（採点はまだ） |

The planned author's check was not carried out as written. Before the blind labelling, the author had already reviewed the same 50 items with the Pass 1 labels shown. Section 3.4 of the paper describes what was done.

## Items written on 21 October before scoring, but committed afterwards (`4ed48a58`)

These were written in the notebook entry “2026-10-21 残りの 6 本の固定（確かめる帖を測る前）” (“Fixing the remaining six models (before measuring the test volumes)”), which precedes the scoring entry of the same day. They were committed only on 29 October, after the scoring. The thresholds were chosen by the same rule as above.

| Condition | Weight sha256 | Confidence |
|---|---|---|
| b0 YOLOv5x (38 volumes, 30 epochs) | f544dfa38d1b03af840e8508fbdb7b99fbe52b3849b604a540106df3cff840c1 | 0.52 |
| b2 RT-DETR-l (38 volumes, 30 epochs) | 0e6fbb432e62e7fbda1865a25dfa63e59b4a2726a9c492cb2302e3be5ba918bf | 0.69 |
| lc-19 (19 volumes) | 074369279b1d1470aa6a76ba5c007a37b37153ab0f0a1be16046ee6c207e0c3f | 0.44 |
| b1-seed1 (A100) | a4a4995c7ac1f715c8a9b35bce1aab6fd929bcb0ea4106bc7b7b396af83a4249 | 0.44 |
| b1-seed2 (A100) | 97defe4ef53cbd84c26dcfdb19f163aa1bde465c04dda515e2b1b349e5225982 | 0.41 |
| b1-cuda (seed 0, A100) | 3d5bb6dfae6af678e194976d43b0ab458fd22e6b1513b71207fad873a25ca088 | 0.39 |

The plan to run these on a GPU server, including the added b1-cuda run and the unchanged 30-epoch limit for b0 and b2, was written in the entry of 20 October (“2026-10-20 残りの学習を mdx（A100）で再開する”) and was also committed only on 29 October.

The same thresholds and hashes are in `eval/tune/<condition>/tune.txt` and `eval/test-eval/config-main-ms10.json`.
