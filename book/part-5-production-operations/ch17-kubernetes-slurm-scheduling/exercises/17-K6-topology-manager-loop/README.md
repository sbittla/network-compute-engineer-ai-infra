# 17-K6 · Topology Manager rejection loop (★★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**17-K6** ★★ L1 — Why does the Kubernetes Topology Manager's `single-numa-node` policy not prevent
the scheduler from binding a pod to a node where alignment is impossible, and what failure pattern
results?
*Evidence required:* where the decision is made (scheduler vs kubelet) and the resulting loop.
<!-- prompt:end -->

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
