# Exercise WP2 — FP8 serving on half a node

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** worked-problem · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
W-INFER is redeployed with FP8 weights at TP = 4, two replicas per `HX8` node, KV cache still BF16.
For a decode step at batch 32 and mean context 2,048 tokens per replica: (a) weight and KV bytes read
per GPU; (b) memory and compute lower bounds (FP8 dense peak ≈ 1,979 TFLOP/s per GPU); (c) per-node
output tokens/s if the ceiling fraction stays 0.63, compared with BF16 TP = 8 (≈ 3,370 tokens/s per
node); (d) the arithmetic intensity at batch 32 counting weights only, versus FP8 machine balance.

**Evidence required:** all arithmetic shown; a before/after table; one sentence on what would have
to be measured to trust (c).
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: all arithmetic, the before/after table and the sentence on what to measure

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
