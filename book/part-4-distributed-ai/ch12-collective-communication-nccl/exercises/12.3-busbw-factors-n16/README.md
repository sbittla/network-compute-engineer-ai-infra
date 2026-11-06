# 12.3 — busbw factors for n = 16 (★, L1)

**Type:** Knowledge check · **Kind:** computed · **Points:** 5

## Prompt

<!-- prompt:start -->
**12.3 ★ L1.** Give the nccl-tests busbw correction factor for all-reduce, all-gather, reduce-scatter,
broadcast, and all-to-all on n = 16 ranks. *Evidence required:* five numbers.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/12.3-busbw-factors-n16/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
