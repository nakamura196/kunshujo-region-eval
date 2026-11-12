# Threshold sweep on the external frames (Section 4.3)

The YOLOv5 thresholds in Table 3 (0.46 public, 0.52 retrained) were set on the Kunshūjō.
Here the saved predictions (kept down to confidence 0.05) are rescored on the 44 external frames at
thresholds 0.05–0.52. The best values (public 0.838 at 0.15, retrained 0.775 at 0.20) are chosen on the
same frames, so they are an optimistic upper bound for the detectors.

```
python3 -I tools/eval_final.py run --index external/human-index.json --split external/split.tsv --config external/results/threshold-sweep/config-sweep.json --out out/ext-sweep
python3 -I tools/eval_final.py run --index external/human-index.json --split external/split.tsv --config external/results/threshold-sweep/config-best.json --out out/ext-best
```

`summary-best.json` holds the differences from Gemini: public −0.097 [−0.174, −0.023], retrained −0.160 [−0.229, −0.088] (YOLOv5 minus Gemini).
