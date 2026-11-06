# Marking scheme: 3.16 Why the PCIe cost estimate is an upper bound

Type reflection · kind written · tier L1 · 4 points

**Evidence required:** At least three assumptions and a measurement plan (tools, repetitions, statistic).

| Criterion | Points |
|---|---|
| Assumption 1, no overlap of the DP all-reduce with backward compute | 1 |
| Assumption 2, NCCL does not route around the slow link (for example PXN) | 1 |
| Assumption 3, illustrative 45 GB/s healthy rail and 82 % PCIe efficiency, or only DP traffic considered | 1 |
| L3 measurement plan with tools (all_reduce_perf across the local-rank-3 GPUs; training steps with and without the node), at least 5 runs after warm-up, median and p95 | 1 |
