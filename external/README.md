# External scrapbooks (Section 4.4)

A small post-hoc check on two scrapbooks outside the *Kunshūjō*. All conditions were run with the thresholds tuned on the *Kunshūjō* tuning volumes; nothing was retuned on these frames.

## Sources

| Group | Scrapbook | Frames | Licence |
|---|---|---|---|
| `taito` | *Harimazechō* 〔貼交帖〕, Taitō City Library, IIIF manifest https://adeac.jp/viewitem/taito-lib/viewer/iiif/2017_WA_004/manifest.json | all 21 frames are candidates | CC BY 4.0 |
| `ndl` | *Harimazechō* 『張交帖』, 13 volumes, National Diet Library (NDL Digital Collections PIDs 2586692–2586704) | 30 frames drawn with seed `20261102` from the 567 frames that are not the first or last frame (cover) of a volume | Public domain |

Images were taken from each IIIF image service at 1,024 pixels wide (`tools/make_ext_frames.py`).

## Files

| Path | What it is |
|---|---|
| `candidates.json` | The 51 candidate frames (`canvas`, `book_id`, `width`, `height`, `service`, `key` = MD5 of the canvas URI) |
| `human/state.json` | The author's boxes as drawn in `tools/ext_draw_server.py` (four corner points per box, in full-resolution pixels) and the frames marked as finished |
| `human-index.json`, `frames.json`, `split.tsv` | The 18 finished frames converted for `eval_final.py` by `tools/ext_prepare_eval.py --only-finished` (each frame is its own "book" so that the bootstrap runs over frames) |
| `pred/<condition>/<key>.json` | Predictions of every condition on all 51 candidates. `gemini` has no confidence scores; `b11x` is the YOLO11x model added post hoc |
| `gemini-prompt.txt` | The prompt given to Gemini 4 Argon (the same as for the 300 *Kunshūjō* frames; 10 images per request, coordinates normalised to 0–1000 and converted back to pixels) |
| `config.json` | Thresholds, `min_side` and the two frames for which "nothing to box" is also accepted (`alt_empty`) |
| `results/` | `summary.json` and `per-book.tsv` reported in Table 4 |

Three finished frames contain no item and are not counted by `eval_final.py`, so Table 4 uses 15 frames and 71 human boxes.

## Reproducing Table 4

```
python3 -I tools/eval_final.py run --index external/human-index.json --split external/split.tsv --config external/config.json --out out/external
python3 -I tools/eval_subgroups.py --index external/human-index.json --split external/split.tsv --config external/config.json --pairs b1:gemini,c:gemini,b0:gemini,b11x:gemini,b11x:b1 --by-group
```

The first command gives the per-condition scores and intervals in Table 4; the second gives the per-scrapbook scores and the differences quoted in the text.

## Limitations

The boxes were drawn by the author alone, from scratch and without machine boxes visible, but some were drawn after seeing interim results on the first 4 frames. The author's policy of boxing each piece separately is close to how Gemini boxes. See Sections 4.4 and 6 of the paper.
