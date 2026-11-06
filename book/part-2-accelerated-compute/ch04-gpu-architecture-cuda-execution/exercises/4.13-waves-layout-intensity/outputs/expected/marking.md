# Marking scheme: 4.13 Batch size and data layout

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** wave arithmetic for both shapes, coalescing explanation, two fixes, intensity argument.

| Criterion | Points |
|---|---|
| (a) 8,192 × 2,048: 512 tiles, 3.88 → 4 waves, 97 % efficiency; 1,024 × 2,048: 64 tiles, 1 wave, 48 % | 4 |
| (b) adjacent threads 8,192 B apart, one 32 B sector per 2 useful bytes, 6.25 % efficiency; two valid fixes | 3 |
| (c) intensity about m FLOP/B when m << k, n, so halving the batch halves intensity; nvidia-smi is a duty cycle and stays near 100 % | 3 |
