# Marking scheme: K6 Where the bytes go

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the placement/rail argument for each case; the number of leaves per rail in each.

| Criterion | Points |
|---|---|
| ORION-256: one leaf per rail with all 32 nodes' NIC r; DP/PP peers share local rank, so traffic is leaf-local | 2 |
| 1,024 GPUs: four leaves per rail (32-node blocks); DP groups spanning blocks cross spines | 1 |
| States the dependence on rail-aligned rank mapping | 1 |
