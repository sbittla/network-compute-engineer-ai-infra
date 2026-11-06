# 17-K1 · Capacity 8, allocatable 7 (★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**17-K1** ★ L1 — A Kubernetes node reports `capacity nvidia.com/gpu: 8` and
`allocatable nvidia.com/gpu: 7`. `nvidia-smi -L` lists 8 GPUs. Explain the most likely mechanism
and what an 8-GPU pod will experience.
*Evidence required:* the component that sets the number, the mechanism, and the scheduler outcome.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 17 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
