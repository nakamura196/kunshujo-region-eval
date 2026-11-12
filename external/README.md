# Two other scrapbooks (Sections 2.3 and 4.3, Table 3)

A check on two scrapbooks outside the *Kunshūjō*. All methods were run with the thresholds set on the *Kunshūjō* (public weights 0.46, retrained YOLOv5 0.52); nothing was retuned on these frames.

## Sources

| Group | Scrapbook | Frames | Licence |
|---|---|---|---|
| `taito` | 〔*Harimazechō*〕, Taitō City Library, IIIF manifest https://adeac.jp/viewitem/taito-lib/viewer/iiif/2017_WA_004/manifest.json | all 21 frames | CC BY 4.0 |
| `ndl` | 『*Harimazechō*』, 13 volumes, National Diet Library (NDL Digital Collections PIDs 2586692–2586704) | 30 frames drawn with seed `20261102` from the 567 frames that are not the first or last frame (cover) of a volume | Public domain |

Images were taken from each IIIF image service at 1,024 pixels wide (`tools/make_ext_frames.py`).

## The human boxes

The author drew all boxes in `tools/ext_draw_server.py` on blank images, without machine boxes shown. All 51 candidate frames were finished; 7 have no item, so 44 frames and 173 human boxes are scored.

The frames were drawn in two rounds:

- **First 18 frames** (2 November 2026). Interim results had been seen before all 18 were finished.
- **Remaining 33 frames** (3 November 2026), listed in `frames-added.json`. Fixed before drawing: all 33 unfinished frames, NDL and Taitō alternating, each shuffled with seed `20261103`. Machine output for these frames was not looked at until drawing was finished. 4 have no item, so 29 frames and 102 human boxes are scored (the last column of Table 3).

## Files

| Path | What it is |
|---|---|
| `candidates.json` | The 51 candidate frames (`canvas`, `book_id`, `width`, `height`, `service`, `key` = MD5 of the canvas URI) |
| `human/state.json` | The author's boxes as drawn (four corner points per box, in full-resolution pixels) and the frames marked as finished |
| `human-index.json`, `frames.json`, `split.tsv` | The 51 finished frames converted for `eval_final.py` by `tools/ext_prepare_eval.py --only-finished` (each frame is its own "book" so that the bootstrap resamples frames) |
| `frames-added.json` | The 33 frames of the second round, in the same form |
| `pred/<condition>/<key>.json` | Predictions on all 51 frames. `c` public weights, `b0-yolov5x` retrained YOLOv5, `gemini` Gemini 4 Argon (2 November 2026), `gemini-rerun1`, `gemini-rerun2` the same prompt run again (3 November 2026). Gemini has no confidence scores. The other folders (`b1-yolo11s`, `b2-rtdetr-l`, `b11x`, `lc-10`, `g-pl10`) are from earlier analyses not reported in the paper |
| `raw/<run>/batch_NN.gemini.out`, `batch_NN.keys` | Gemini's raw answers, one JSON line per frame; line *n* is the frame on line *n* of the `.keys` file (MD5 of the canvas URI). Converted with `tools/gen_lines_to_pred.py --order xy` |
| `gemini-prompt.txt` | The prompt (the same as for the *Kunshūjō*; 10 images per request, coordinates normalised to 0–1000) |
| `config.json`, `config-added.json` | Scoring configs for the 44 frames and the 29 frames of the second round |
| `results/44-frames/`, `results/29-added-frames/` | `summary.json` and `per-book.tsv` (Table 3) and `by-scrapbook.txt` (scores and differences per scrapbook) |

## Reproducing Table 3

```
python3 -I tools/eval_final.py run --index external/human-index.json --split external/split.tsv --config external/config.json --out out/external-44
python3 -I tools/eval_final.py run --index external/human-index.json --split external/split.tsv --config external/config-added.json --out out/external-29
python3 -I tools/eval_subgroups.py --index external/human-index.json --split external/split.tsv --config external/config-added.json --pairs c:gemini,b0:gemini --by-group
```

The first two commands give the precision, recall, F1 and intervals in Table 3, the differences quoted in Section 4.3 (pairs `c-gemini` and `b0-gemini`) and the reruns quoted in Section 6. The third gives the per-scrapbook values on the 29 frames (on the NDL frames alone the difference includes 0; Section 6).

## Limitations

The boxes were drawn by the author alone. The author's policy of boxing each piece separately is close to how Gemini boxes. See Section 6 of the paper.

`results/threshold-sweep/` rescores the saved YOLOv5 predictions at thresholds chosen on these 44 frames (an optimistic upper bound; Section 4.3).
