# Exercise 4.7 — Occupancy versus latency hiding

★★ · Tier L1 · knowledge check · kind: `computed`

<!-- prompt:start -->
**4.7** ★★ L1 — Why can a Tensor Core GEMM at 18.75 % theoretical occupancy run at 60 %+ of peak, while
a layernorm backward at 12.5 % occupancy runs at 22 % of HBM bandwidth?
*Evidence required:* latency-hiding argument referencing warp groups/TMA and Little's law.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 4 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
