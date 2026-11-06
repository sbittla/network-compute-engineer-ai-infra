# 17-K2 · nodeSelector versus toleration (★ · L1)

Type: knowledge-check · Kind: written · Points: 4

<!-- prompt:start -->
**17-K2** ★ L1 — State the difference between a `nodeSelector` and a toleration, and write the
minimal pod-spec fragment that runs a pod *only* on a node labelled and tainted
`halcyon.ai/dedicated=search:NoSchedule`.
*Evidence required:* one sentence on attract vs repel; a correct YAML fragment.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, or lab file you used, and label numbers with their evidence class
(`[SIMULATED]`, `[MODELED]`, `[ILLUSTRATIVE]`).
