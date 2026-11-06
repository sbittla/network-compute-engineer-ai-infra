# 13.11 — Validate GPUDirect RDMA and GPU/NIC locality (O3) (★★, L2)

Type: outline-mandated · Kind: written

## Prompt

<!-- prompt:start -->
**13.11 (O3) ★★ L2/L3 — Validate GPUDirect RDMA and GPU/NIC locality.** Propose a measurement plan
for a supported two-node platform: the checks (configuration and performance), exact commands, what
result passes or fails, repetitions, and what to record. Include a deliberately misaligned GPU/NIC
test and a GDR-off control. Mark vendor-specific items.
*Evidence required:* a plan table with ≥ 8 rows (question, command, pass criterion, record), and a
safety note.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/measurement_plan.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

On a single GPU host you can execute the link-check part with `python scripts/hw_labs.py run ch13 --device gpu`
(CPU fallback with `--device cpu`). The NIC and GDR rows need RDMA hardware and are reported as not runnable. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.