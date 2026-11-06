# R1 — Capacity-model assumptions to measure (★, L1)

Type: reflection · Kind: written

## Prompt

<!-- prompt:start -->
**R1. ★ L1.** Which three assumptions in the lab's capacity model would you most want to measure
on real hardware, and why those three?
*Evidence required:* three named parameters, the output each one drives, and the L2/L3
measurement that would replace it.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

To see two of these measurements on real hardware, run `python scripts/hw_labs.py run ch15 --device gpu`
(CPU fallback with `--device cpu`) and read `lab/l2/results/*/report.md`: the implied `hbm_efficiency`,
step overhead and `prefill_mfu` for that stack. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.