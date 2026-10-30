# Guideline for classifying disagreements (English translation)

This is an English translation of [`PROMPT.md`](PROMPT.md), the guideline written in Japanese and fixed on 17 October 2026, before any test frame was scored. The Japanese file is the one given to the models; this translation was made afterwards (30 October 2026) for readers and was not used in any run. Where the two differ, the Japanese file is authoritative.

The category names in the label files (`b1-test300/pass1.jsonl`, `pass2.jsonl`, `gemini50.jsonl`, `author50_*.tsv`) are the Japanese strings of the guideline. The paper uses shorter English names. See the [table of category names](#category-names) at the end.

---

## Guideline for classifying disagreements (fixed 17 October 2026, before the test volumes were scored)

This is the text given unchanged to the classifying models (Claude Opus and Claude Sonnet). The two models receive the same text and the same images and are not shown each other's answers.

---

You will look at images of a Meiji-period scrapbook (an album of paper pieces pasted onto mounts) and judge how the extent of each item has been marked.

Each image is one frame (an opening) of an album. Boxes are drawn on it.
- Thin blue boxes: extents of items drawn by people (library staff and others)
- Thin orange boxes: extents of items output by a machine (a detector)
- Thick red box: the one box to be judged. It is either a human box or a machine box (the `kind` column of the list: human = a human box, machine = a machine box)

A red box is one for which "the other side has no box that overlaps it sufficiently (IoU 0.5 or more)".
Choose one of the following four reasons why they disagree.

1. Machine error (機械の誤り)
   - kind=machine: the machine box is not a proper extent for one pasted item. It covers the margin of the mount, the text or ruled lines of the album itself, only part of an item, several unrelated items together, and so on. The human box is the correct one.
   - kind=human: the human box correctly encloses one item, but the machine has not picked it up (or is far off).
2. Difference in cutting policy (切り方の方針の違い)
   - Both boxes are reasonable as the extent of an item. The difference lies in how items are grouped or where the boundary is drawn.
   - Examples: whether a continuous item (a spread of a booklet, a set of tickets, an envelope and its contents) is one box or several; whether the mount or edges are included; whether papers pasted over one another are seen as one item.
3. Error on the ground-truth side (正解側の誤り)
   - The human box is the improper one.
   - kind=machine: the machine box correctly encloses one item, but the person did not draw a box for that item (an omission).
   - kind=human: the human box does not fit an item (misplaced, as small as a dot, on an empty area, and so on).
4. Cannot judge (判断できない)
   - It cannot be decided because the image is small, dark, and so on.

Write the answer as one line of JSON per item.
`{"id": <number>, "class": "機械の誤り" | "切り方の方針の違い" | "正解側の誤り" | "判断できない", "reason": "<reason in 30 characters or fewer>"}`

(The `class` values are to be written in Japanese exactly as listed. The `reason` was written in Japanese.)

---

## Rules

- Items: chosen from the disagreements of condition b1 (YOLO11s) on the test volumes with `tools/disagreements.py` (seed 20261016, 300 items, min_side 10, the b1 threshold).
- Each call receives 25 items (25 images, plus the `id` and `kind` of the corresponding rows of `items.tsv`). The 300 items are split into 12 calls, in `id` order.
- Percent agreement and Cohen's kappa are computed on the four categories as they are. When the two models disagree, both answers are recorded. The breakdown in the text is given with Opus's answers, and Sonnet's breakdown is shown alongside.
- The guideline and the way the images are drawn were checked on 12 items from the 9 tuning volumes of the development set (disagreements of best.pt), for the output format only. The guideline is not revised after looking at the content of the classifications.

---

## Category names

| Label in the files (Japanese, as in the guideline) | Literal translation | Name in the English paper | Name in the Japanese paper |
|---|---|---|---|
| 機械の誤り | machine error | Machine error | 機械の誤り |
| 切り方の方針の違い | difference in cutting policy | Policy difference | 切り方の方針の違い |
| 正解側の誤り | error on the ground-truth side | Catalog error | 目録の誤り |
| 判断できない | cannot judge | Indeterminate | 判定不能 |

The paper renamed category 3 because the human boxes are the library's catalog records, not a ground truth made for this study. The definitions are unchanged. No item in the 300 was labelled 判断できない by either pass.
