# Exercise 4.13 — Batch size and data layout

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**4.13** ★★ L1 — *Batch size and data layout.* (a) For a GEMM with output 8,192 × 2,048 tiled 128 × 256 on
132 SMs, compute tiles, waves and wave efficiency; repeat for output 1,024 × 2,048. (b) A tensor of shape
[8,192, 4,096] in BF16 is read along dimension 0 by adjacent threads (column access of a row-major
tensor). Explain the coalescing consequence and two ways to fix it. (c) Explain how halving the batch
changes GEMM arithmetic intensity and why nvidia-smi would not show the change.
*Evidence required:* wave arithmetic for both shapes, coalescing explanation, two fixes, intensity argument.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
