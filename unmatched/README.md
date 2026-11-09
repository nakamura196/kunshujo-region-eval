# Judging the unmatched boxes (Section 3.3, Table 2)

Predicted boxes on the 300 test frames that match no catalogue box at IoU 0.5 ("unmatched boxes") were judged by the author.

## Sampling

- **Gemini**: 518 unmatched boxes (`gemini/unmatched-518.json`, made by `tools/gen_extra_boxes.py`). 100 were drawn with `random.Random(20261103).sample` (`gemini/items.tsv`, in the order shown); the first 54 were judged.
- **Retrained YOLOv5** (`b0`, threshold 0.52): 237 unmatched boxes. 164 lie at the same place (IoU 0.7 or more) as an unmatched Gemini box in the same frame. The other 73 were put in random order with seed `20261103` (`b0-only/items.tsv`); the first 31 were judged.

`tools/make_extra100.py` makes both sets and the judging pages (`--cond a4` for Gemini, `--cond b0 --unshared` for YOLOv5); page images are fetched from IIIF and are not included here. The page template is `tools/extra100_template.html`, and `tools/blind50_server.py` saves the judgements. For each box the page shows two crops of the same region (catalogue boxes only, machine boxes only) and its position in the whole frame. It does not show which machine produced the box.

## Files

| Path | What it is |
|---|---|
| `<set>/items.tsv` | The sampled boxes: `id`, frame `key`, volume, IIIF `canvas`, `box` as [x, y, w, h] in full-resolution pixels |
| `<set>/judgements.tsv` | The author's category for each box (empty = not judged), with the author's notes in Japanese |
| `<set>/a-split-claude.tsv` | Claude's first-pass sub-category for the boxes judged A, with reasons (Japanese); `n` is the row in `items.tsv` |
| `a-subclass-author.tsv` | The author's final sub-category for all 30 boxes judged A (column `claude` is the first pass, `author` the final one; `set` 1 = Gemini, 2 = YOLOv5 only) |
| `b0-only/notes.tsv` | Notes on two YOLOv5-only boxes that could not be written on the page |

## Categories

The judging page used the following labels (Japanese in the files). `tools/count_unmatched.py` maps them to the categories of Table 2.

| Label | Meaning | Table 2 |
|---|---|---|
| `A 人の枠の中の区画` | inside a catalogue box; sub-category in `a-subclass-author.tsv` | see below |
| `A2` | one of several separate items that the catalogue merged into one box | Unit mismatch |
| `見開き` | one page of a booklet spread | Unit mismatch |
| `A1` | only part of a single sheet | Machine error |
| `A?` | undecidable | Undecidable |
| `B 人の枠が無い紙片` | an item with no catalogue box | Unit mismatch |
| `C 背景` | not an item (background, a decorative border) | Machine error |
| `D ずれ` | displaced box; all 6 in the YOLOv5-only set were several items merged by the machine into one box | Unit mismatch |
| `? 決められない` | undecidable | Undecidable |

```
python3 -I tools/count_unmatched.py
```

prints the counts in Table 2 (Gemini: 47 unit mismatch, 2 machine error, 5 undecidable; YOLOv5 only: 22, 4, 5).
