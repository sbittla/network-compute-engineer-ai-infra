# Marking scheme: K2 Why 98 % GPU utilization is not busy compute

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** definition of the utilization metric; two named alternatives and what each measures.

| Criterion | Points |
|---|---|
| Correct definition: fraction of the sample period with at least one kernel resident (not SM occupancy) | 2 |
| Explains that NCCL kernels spinning while waiting for peers count as utilized | 1 |
| Two named better signals (e.g. DCGM_FI_PROF_SM_ACTIVE, DCGM_FI_PROF_PIPE_TENSOR_ACTIVE, clocks + event reasons, timeline breakdown) with what each measures | 1 |
