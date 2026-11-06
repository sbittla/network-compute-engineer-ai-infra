# K2 — Latency metrics (★, L1)

Type: knowledge-check · Kind: written

## Prompt

<!-- prompt:start -->
**K2. ★ L1 — Latency metrics.** Define TTFT, TPOT and ITL. Give one failure that is visible in
ITL p99 but almost invisible in mean TPOT.
*Evidence required:* the three definitions as formulas over request timestamps, plus the failure
and the reason it averages away.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
