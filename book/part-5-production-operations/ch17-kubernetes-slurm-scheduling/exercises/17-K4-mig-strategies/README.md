# 17-K4 · MIG mixed versus single strategy (★★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**17-K4** ★★ L1 — A node has all eight H100s in MIG `all-1g.10gb` with the `mixed` strategy. What
resources does it advertise, and what happens to a pod requesting `nvidia.com/gpu: 1`? What changes
under the `single` strategy?
*Evidence required:* resource names and counts; the outcome under both strategies.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/17-K4-mig-strategies/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
