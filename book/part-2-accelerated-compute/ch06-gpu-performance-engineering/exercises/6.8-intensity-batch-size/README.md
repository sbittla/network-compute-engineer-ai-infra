# Exercise 6.8 — Intensity and batch size

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**6.8** ★★ L1 — *Intensity and batch size.* For a BF16 linear layer with *K* = *N* = 4,096: (a) for *M* =
4,096 tokens compute *W*, minimum *Q*, *I*, the bound and the time at roof; (b) repeat for *M* = 64;
(c) find the smallest *M* for which the layer is compute-bound on ORION. *Evidence required:* all
arithmetic; label `[MODELED]`.
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
