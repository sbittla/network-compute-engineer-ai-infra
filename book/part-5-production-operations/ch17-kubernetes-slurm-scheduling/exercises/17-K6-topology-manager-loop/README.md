# 17-K6 · Topology Manager rejection loop (★★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**17-K6** ★★ L1 — Why does the Kubernetes Topology Manager's `single-numa-node` policy not prevent
the scheduler from binding a pod to a node where alignment is impossible, and what failure pattern
results?
*Evidence required:* where the decision is made (scheduler vs kubelet) and the resulting loop.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/17-K6-topology-manager-loop/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
