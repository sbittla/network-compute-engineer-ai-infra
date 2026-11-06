# K7 — Transients (★★, L1)

Type: Knowledge check · Kind: `computed` · Points: 5

## Prompt

<!-- prompt:start -->
**K7 ★★ L1 — Transients.** Estimate the synchronized power swing of a 1,024-GPU job whose GPUs move between
650 W and 400 W each step. Name two mitigations.
*Evidence required:* arithmetic; two mitigations with owners.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 21 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
