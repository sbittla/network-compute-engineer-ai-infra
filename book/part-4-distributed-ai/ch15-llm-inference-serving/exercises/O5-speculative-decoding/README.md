# O5 — Speculative decoding trade-off (★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O5. ★★ L1 — Speculative decoding trade-off.** For α ∈ {0.6, 0.8, 0.9} and k ∈ {2, 4, 8}, with a
draft cost of 0.05, compute expected tokens per step and speedup. First assume memory-bound
verification (cost 1). Then derive the verification cost at B = 128 on T-tp4-fp8 from the
roofline for each k (compute time of B × (k + 1) tokens vs the 20.2 ms decode step) and repeat. Recommend k for
an interactive tier and decide whether to enable speculation on the throughput tier.
*Evidence required:* two 3 × 3 tables and the recommendation with its reasoning.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
