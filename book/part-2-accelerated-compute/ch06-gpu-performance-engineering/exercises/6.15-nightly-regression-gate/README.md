# Exercise 6.15 — Nightly performance-regression gate

★★★ · Tier L1 · design challenge · kind: `computed`

<!-- prompt:start -->
**6.15** ★★★ L1 — Design a nightly performance-regression gate for ORION (32 HX8 nodes) with a budget of
16 GPU-hours per night. Choose workloads (microbenchmarks vs end-to-end), node selection and
stratification, clock policy, sample sizes, decision thresholds, what blocks a promotion, and how you keep
the A/A floor under 1 %. Defend one choice against a rejected alternative. *Evidence required:* a design
with budget arithmetic, the decision rule, and the rejected alternative.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
