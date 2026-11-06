# K1 — Scale and MTBF (★, L1)

Type: Knowledge check · Kind: `computed` · Points: 4

## Prompt

<!-- prompt:start -->
**K1 ★ L1 — Scale and MTBF.** Compute job MTBF and expected interruptions per day for jobs of 8, 32,
128, and 512 HX8 nodes.
*Evidence required:* formula and a four-row table.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/K1-scale-and-mtbf/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (formula and the four-row table)
