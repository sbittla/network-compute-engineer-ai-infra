# Marking scheme: 13.4 Why utilization.gpu stays near 100 %

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** mechanism + two metrics

| Criterion | Points |
|---|---|
| Defines utilization.gpu as the fraction of sample time in which any kernel ran | 1 |
| Explains that NCCL kernels spin on flags while waiting, so the GPU counts as busy | 2 |
| Names DCGM SM active or tensor-pipe active as a better metric | 1 |
| Names per-rank phase timings (wait vs transfer vs compute) as a better metric | 1 |
