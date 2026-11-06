# M2 — Two designs (★★, L1)

Type: Outline-mandated · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**M2 ★★ L1 — Two designs.** Compare two cluster designs on **useful throughput per dollar and per watt** using
explicit assumptions (lab Task 4), add a sensitivity analysis on per-GPU throughput and electricity price,
and state the break-even.
*Evidence required:* comparison table; sensitivity table; break-even arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 21 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/comparison.md`
- `outputs/sensitivity.csv`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
