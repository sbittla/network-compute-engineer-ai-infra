# Exercise 6.11 — Roofline from supplied data

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**6.11** ★★ L1 — *Roofline from supplied data.* Classify and express as a fraction of the binding roof:

| Kernel | Precision | FLOP | DRAM bytes | Measured time |
|---|---|---|---|---|
| K1 softmax | BF16 | 1.0 × 10⁹ | 1.6 × 10⁹ | 0.60 ms |
| K2 GEMM | BF16 | 4.4 × 10¹² | 0.6 × 10⁹ | 7.4 ms |
| K3 decode attention | BF16 | 8.6 × 10⁹ | 2.15 × 10⁹ | 0.75 ms |
| K4 reduction | FP32 SIMT | 2.0 × 10¹¹ | 0.4 × 10⁹ | 5.0 ms |

Then take measured roofs of 2.95 TB/s HBM and 700 TFLOP/s dense BF16 `[ILLUSTRATIVE]` (Section 6.3,
"Empirical ceilings"; FP32 not measured), give K1–K3's fraction of the measured roof too, and say whether
it changes your ranking. Rank them by optimization opportunity and name the lever for each. *Evidence
required:* table with intensity, ridge, bound, fraction of vendor roof and of measured roof; ranked list
with levers.
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
