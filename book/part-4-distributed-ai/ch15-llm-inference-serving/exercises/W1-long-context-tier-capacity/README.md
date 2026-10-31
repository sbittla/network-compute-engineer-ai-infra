# W1 — Capacity of an alternative layout (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**W1. ★★ L1 — Capacity of an alternative layout.** Halcyon AI considers a long-context tier: one
TP = 8 replica per HX8 with **FP8 weights (70 GB) and FP8 KV cache**, `memory_fraction` 0.90,
2 GB reserve per GPU, 16-token blocks.
(a) Compute the KV budget, the number of blocks, and the maximum number of concurrent 8,192-token
sequences. (b) Repeat with BF16 KV. (c) Compute the decode-step lower bound and the planning value
(efficiency 0.70, overhead 3 ms) at B = 64 with an average context of 6,000 tokens (FP8 KV), and
the resulting tokens/s.
*Evidence required:* every formula, substituted values and results with units. Lab Part A
functions may be used to check your arithmetic.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
