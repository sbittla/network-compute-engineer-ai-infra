# K1 result `[MODELED]`

- Ridge = 989e12 / 3.35e12 = 295 FLOP/B
- Decode B=32: 2N × 32 / 2N = 32 FLOP/B (attention with GQA 8 FLOP/B) -> memory-bound
- Prefill 2,048: 2048 FLOP/B -> compute-bound
