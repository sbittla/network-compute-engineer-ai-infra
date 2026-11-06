# Marking scheme: K1 The lying utilization metric

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** A definition of what GPU_UTIL measures; the role of NCCL kernels; three named signals with one sentence each on why they move.

| Criterion | Points |
|---|---|
| GPU_UTIL defined as time-occupancy (fraction of time any kernel runs), not an SM average | 2 |
| NCCL kernels stay resident polling for network data, so occupancy stays ≈ 97 % | 1 |
| Three valid signals (SM_ACTIVE, PIPE_TENSOR_ACTIVE, POWER_USAGE, job step time/tokens per second), one sentence each | 3 |
