# R4 — What L1 cannot show about GPUDirect RDMA (★, L1)

Reflection · difficulty ★ · tier L1 · kind `written` · [exercise index](../README.md)

<!-- prompt:start -->
**R4 ★ (L1).** What can the L1 lab not tell you about the GPUDirect RDMA hypothesis, and exactly what
L2/L3 evidence would close the gap?

*Evidence required (R1–R4):* concise written answers, each naming the evidence (or missing evidence) it
relies on.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 22 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

On a single GPU host, `python scripts/hw_labs.py run ch22 --device gpu` validates the attribution method on a known
host-staging regression (CPU fallback with `--device cpu`). The GDR evidence itself still needs RDMA hardware. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.