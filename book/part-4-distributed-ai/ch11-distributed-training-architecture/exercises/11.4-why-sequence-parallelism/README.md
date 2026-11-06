# 11.4 — Why sequence parallelism? (★, L1)

**Type:** Knowledge check · **Kind:** computed · **Points:** 3

## Prompt

<!-- prompt:start -->
**11.4 ★ L1 — Why sequence parallelism?** Sequence parallelism does not reduce TP bytes on the wire.
What does it reduce, and by how much for TP = 8? *Evidence required:* two sentences naming the
quantity and the factor.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/11.4-why-sequence-parallelism/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
