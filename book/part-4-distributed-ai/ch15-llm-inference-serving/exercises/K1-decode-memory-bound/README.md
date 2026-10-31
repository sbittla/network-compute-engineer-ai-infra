# K1 — Why decode is memory-bound (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**K1. ★ L1 — Why decode is memory-bound.** In three or four sentences, explain why a decode step
for W-INFER at batch 32 is HBM-bandwidth-bound while a 2,048-token prefill is compute-bound.
Use arithmetic intensity and the H100-class BF16 ridge point.
*Evidence required:* both intensities (approximate is fine) compared with the ridge in FLOP/B.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
