# Gemini 4 Argon on the 300 test frames (Sections 3.1 and 6)

Gemini 4 Argon was run through the Google Antigravity command-line interface (model setting `gemini-4-argon-high`) with the prompt in `external/gemini-prompt.txt` (also in the Appendix of the paper). Ten frames, 1,024 pixels wide, were sent per request; 30 requests cover the 300 frames of `data/test300_canvases.json`.

| Path | What it is |
|---|---|
| `raw/run1/` | First run, 29 October 2026 (used in Table 1) |
| `raw/run2/` | Second run with the same prompt and the same batches, 3 November 2026 (Section 6) |
| `raw/<run>/batch_NN.gemini.out` | Raw answers, one JSON line per frame (`{"image": n, "boxes": [{"bbox_2d": [x1, y1, x2, y2], ...}]}`, coordinates normalised to 0–1000) |
| `raw/<run>/batch_NN.keys` | The frames of that request; line *n* is image *n* (MD5 of the canvas URI, as `key` in `data/test_frames.json`) |
| `pred/<run>/<key>.json` | Per-frame predictions converted to full-resolution pixels by `tools/gen_lines_to_pred.py --order xy`. Gemini gives no confidence scores, so every box has 1.0 |

Requests were prepared with `tools/gen_detect_batch.py`. Scores are in `eval/test-eval/sub300-gemini/` (F1 0.719 for run 1 and 0.713 for run 2).
