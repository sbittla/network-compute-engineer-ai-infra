# 11.8 — Memory audit (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 6

## Prompt

<!-- prompt:start -->
**11.8 ★★ L1 — Memory audit.** For TP = 4, PP = 4, DP = 16, micro-batch 2, ZeRO-1, selective
recompute, compute per-GPU model state, activations on stage 0, total, and say whether it fits the
68 GB planning limit. *Evidence required:* every intermediate value with units.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Model inputs (W-TRAIN):** 70 × 10⁹ parameters, 80 layers, hidden 8,192, sequence length 4,096, global batch 1,024 sequences, BF16 mixed-precision Adam (16 B/param of training state). Table 11.4 supplies the 68 GB planning limit; Section 11.2 gives the memory formulas.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/11.8-memory-audit/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
