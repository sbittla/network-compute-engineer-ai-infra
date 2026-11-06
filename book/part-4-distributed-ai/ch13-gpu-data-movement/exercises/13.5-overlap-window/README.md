# 13.5 — Overlap window for the DP reduction (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**13.5 ★ L1.** What limits how much of the DP gradient reduction can be overlapped with compute when
pipeline parallelism and gradient accumulation are used? *Evidence required:* the window and its
W-TRAIN value with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 13 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
