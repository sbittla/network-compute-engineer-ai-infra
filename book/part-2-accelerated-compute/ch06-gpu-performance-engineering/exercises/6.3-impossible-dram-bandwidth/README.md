# Exercise 6.3 — 4.6 TB/s of DRAM bandwidth on a 3.35 TB/s GPU

★ · Tier L1 · knowledge check · kind: `written`

<!-- prompt:start -->
**6.3** ★ L1 — A profiled kernel shows 4.6 TB/s of "DRAM" bandwidth on an ORION GPU. Give two explanations
and say what you would check. *Evidence required:* two mechanisms, one counter or experiment each.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
