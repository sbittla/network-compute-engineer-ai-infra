# K1 · The lying utilization metric (★ · L1)

Type: knowledge-check · Kind: written · Points: 6

<!-- prompt:start -->
**K1 ★ L1 — The lying utilization metric.** Explain the mechanism by which `DCGM_FI_DEV_GPU_UTIL`
stays near 97 % while a training job is stalled waiting on the network. Name two DCGM metrics and one
non-DCGM signal that would reveal the stall.
*Evidence required:* a definition of what GPU_UTIL measures; the role of NCCL kernels; three named
signals with one sentence each on why they move.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, metric, or lab data file you used, and label numbers with their evidence
class (`[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]`).
