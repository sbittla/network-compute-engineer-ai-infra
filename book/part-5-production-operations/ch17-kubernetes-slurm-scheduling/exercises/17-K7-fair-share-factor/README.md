# 17-K7 · Classic fair-share factor (★★ · L1)

Type: knowledge-check · Kind: computed · Points: 3

<!-- prompt:start -->
**17-K7** ★★ L1 — In Slurm's classic fair-share formula `F = 2^(−U/S)`, compute `F` for an account
with usage equal to its share, half its share, and twice its share.
*Evidence required:* three values with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/17-K7-fair-share-factor/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
