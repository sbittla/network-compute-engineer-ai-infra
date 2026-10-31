# K6 — GQA and KV bytes per token (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**K6. ★ L1 — GQA.** W-INFER has 64 query heads and 8 KV heads. Compute the KV bytes per token
with and without GQA, and explain the effect on maximum concurrency.
*Evidence required:* both byte counts with the formula.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
