# Marking scheme: 4.9 Launch-bound loop and copy cost

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** three results with formulas and units; label `[MODELED]`.

| Criterion | Points |
|---|---|
| (a) eager iteration 4.0 ms (CPU-limited, 400 × 10 µs) and kernel-busy 60 % | 3 |
| (b) CUDA Graph iteration 2,814 µs = about 2.81 ms, speedup about 1.42×, kernel-busy about 85 % | 3 |
| (c) pageable 22.4 ms vs pinned 5.37 ms for 268,435,456 B, and the steady state recognized as copy-bound at max(2.81, 5.37) = 5.37 ms | 4 |
