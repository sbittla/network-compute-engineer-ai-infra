# K6 — Domain vs unit (★★, L1)

Type: Knowledge check · Kind: `written` · Points: 5

## Prompt

<!-- prompt:start -->
**K6 ★★ L1 — Domain vs unit.** Explain the difference between the *fault domain* and the *scheduling
unit removed* for a failed `mlx5_3` link on a node running a TP = 8, rail-optimized job. When could the
two coincide?
*Evidence required:* both definitions applied; one coinciding case.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
