# Exercise 6.12 — Benchmark protocol for two NCCL versions

★★ · Tier L1 · outline-mandated · kind: `written`

<!-- prompt:start -->
**6.12** ★★ L1 — *Benchmark protocol.* Write a one-page protocol for comparing two NCCL versions'
all-reduce performance on two ORION nodes, controlling warm-up, repetitions, concurrency, input size,
software versions and measurement noise, with a pre-registered decision rule. *Evidence required:* the
protocol with every control and the decision rule; manifest fields.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
