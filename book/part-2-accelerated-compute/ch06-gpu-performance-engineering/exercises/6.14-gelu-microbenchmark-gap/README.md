# Exercise 6.14 — 12 % faster kernel, unchanged step time

★★★ · Tier L1 · troubleshooting case · kind: `computed`

<!-- prompt:start -->
**6.14** ★★★ L1 — A kernel team reports their new GELU kernel is 12 % faster (microbenchmark at batch 1,
hidden 4,096, median of 1,000 iterations in one process). After deployment, W-TRAIN step time is
unchanged within noise. GELU accounts for ≈ 4 % of step time in the production profile. Explain the
discrepancy with at least three mechanisms, quantify the expected end-to-end gain, and design the
experiment that would have predicted it. *Evidence required:* mechanisms, Amdahl arithmetic, experiment design.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
