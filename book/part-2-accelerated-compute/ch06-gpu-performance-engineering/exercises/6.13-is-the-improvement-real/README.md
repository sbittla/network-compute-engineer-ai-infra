# Exercise 6.13 — Is the improvement real?

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**6.13** ★★ L1 — *Is the improvement real?* Run medians (ms) for an inference kernel: baseline 12.41,
12.37, 12.52, 12.44, 12.39, 12.47; candidate 12.10, 12.22, 12.05, 12.31, 12.95, 12.12. The candidate's
fifth run logged `sw_power_cap` on most iterations and had a median SM clock of 1,610 MHz; the other eleven
runs of both arms sat at 1,822–1,830 MHz (peer median 1,826 MHz). The A/A floor is 0.9 %; the practical
threshold is 2 %.
Using the lab's `permutation_test` and `bootstrap_ratio_ci` (seed 11, 4,000 replicates), decide with and without the fifth run
and justify which decision stands. *Evidence required:* arm means of the run medians, relative changes, p-values,
bootstrap bands, decisions, justification.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 6 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
