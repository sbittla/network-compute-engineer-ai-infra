# Marking scheme: K5 Blast radius: rack power versus rail leaf

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** numbers for (a); a mechanism-based explanation for (b)

| Criterion | Points |
|---|---|
| (a) 32 GPUs lost (4 nodes × 8), 12.5 % of 256; only jobs with ranks in that rack affected | 1 |
| (b) 0 GPUs lost, but rail r lost on all 32 nodes; every multi-node job using the rail affected (plan job-fatal) | 1 |
| Mechanism: rail-optimized wiring makes one switch a logical dependency of every node, while a rack is physically local | 2 |
