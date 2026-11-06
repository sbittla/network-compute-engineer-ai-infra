# Marking scheme: 4.7 Occupancy versus latency hiding

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** latency-hiding argument referencing warp groups/TMA and Little's law.

| Criterion | Points |
|---|---|
| GEMM: asynchronous warp-group MMA fed by TMA keeps many bytes and FLOPs in flight per warp; tile reuse keeps Tensor Cores fed despite 18.75 % occupancy | 2 |
| Little's law: 3.35 TB/s × 600 ns / 132 SMs = about 15.2 KB needed in flight per SM | 1 |
| Layernorm backward: 8 warps × about 3.25 × 128 B = about 3.3 KB in flight, 3.3 / 15.2 = about 22 % of HBM bandwidth | 2 |
