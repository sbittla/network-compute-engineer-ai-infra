# K2 — Why 98 % GPU utilization is not busy compute (★, L1)

Knowledge check · difficulty ★ · tier L1 · kind `written` · [exercise index](../README.md)

<!-- prompt:start -->
**K2 ★ (L1).** A dashboard shows 98 % "GPU utilization" on every GPU of a job whose step time rose 15 %.
Explain why this does not show the GPUs are busy computing, and name two better signals.
*Evidence required:* definition of the utilization metric; two named alternatives and what each measures.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
