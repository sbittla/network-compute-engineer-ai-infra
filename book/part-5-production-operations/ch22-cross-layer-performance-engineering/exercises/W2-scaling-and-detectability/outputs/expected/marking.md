# Marking scheme: W2 Scaling efficiency and detectability

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** formulas, substituted values, results with units; a clear yes/no with n.

| Criterion | Points |
|---|---|
| (a) tokens/s at 64/128/256 GPUs and E_weak 98.6 % and 97.1 % (weak, not strong scaling) | 3 |
| (b) straggler terms 0.175 s of 0.24 s and 0.325 s of 0.52 s, with the remainder stated | 3 |
| (c) MDE at n = 5 is 0.195 s > 0.15 s, so no | 2 |
| (c) n = 2 × (2.8σ/δ)² = 8.43, rounded up to 9 runs per arm | 2 |
