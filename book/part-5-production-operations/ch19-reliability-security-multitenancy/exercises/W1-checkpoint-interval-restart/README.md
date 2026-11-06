# W1 — Checkpoint interval and restart overhead (★★, L1)

Type: Worked problem · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**W1 ★★ L1 — Checkpoint interval and restart overhead.**
(a) For a 32-node ORION job (δ = 1 min blocking checkpoint cost, R = 15 min), compute τ_opt and goodput.
(b) For a 512-node ORION-XL job at τ = 19 min, compute goodput with R = 15 min and with R = 5 min.
(c) Convert the difference in (b) into GPU-hours per day and dollars per day at $3.00/GPU-h `[MODELED]` (≈ the Chapter 21 owned-cluster cost).
*Evidence required:* Young's formulas with substitutions; results to 3 significant figures.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (substitutions and results)
