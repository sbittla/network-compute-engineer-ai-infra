# Marking scheme: K6 Weak- and strong-scaling efficiency

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** both formulas; the choice with the reason (what is held constant).

| Criterion | Points |
|---|---|
| E_strong formula with fixed global problem | 1 |
| E_weak formula with throughput and fixed per-GPU work | 1 |
| Chooses weak scaling for 64 -> 256 GPUs | 1 |
| Reason: DP grows 2 -> 8 and global batch 256 -> 1,024 sequences, so per-GPU work is constant | 1 |
