# 17-K1 · Capacity 8, allocatable 7 (★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**17-K1** ★ L1 — A Kubernetes node reports `capacity nvidia.com/gpu: 8` and
`allocatable nvidia.com/gpu: 7`. `nvidia-smi -L` lists 8 GPUs. Explain the most likely mechanism
and what an 8-GPU pod will experience.
*Evidence required:* the component that sets the number, the mechanism, and the scheduler outcome.
<!-- prompt:end -->

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
