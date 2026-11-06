# K1 — Why decode is memory-bound (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**K1. ★ L1 — Why decode is memory-bound.** In three or four sentences, explain why a decode step
for W-INFER at batch 32 is HBM-bandwidth-bound while a 2,048-token prefill is compute-bound.
Use arithmetic intensity and the H100-class BF16 ridge point.
*Evidence required:* both intensities (approximate is fine) compared with the ridge in FLOP/B.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
