# Exercise 6.2 — GB/s for elementwise, TFLOP/s for GEMM

★ · Tier L1 · knowledge check · kind: `written`

<!-- prompt:start -->
**6.2** ★ L1 — Why is an elementwise kernel's performance judged in GB/s and a large GEMM's in TFLOP/s?
*Evidence required:* intensity argument for both.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 6 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
