# Marking scheme: 4.2 Coalescing and 32-byte sectors

Type knowledge-check · kind computed · tier L1 · 6 points

**Evidence required:** sector counts and useful-byte fractions with arithmetic.

| Criterion | Points |
|---|---|
| (a) consecutive: 128 B span, 4 sectors, 100 % useful, arithmetic shown | 2 |
| (b) stride 2: 256 B span, 8 sectors, 50 % useful, arithmetic shown | 2 |
| (c) stride 32: one sector per thread, 32 sectors = 1,024 B, 12.5 % useful, arithmetic shown | 2 |
