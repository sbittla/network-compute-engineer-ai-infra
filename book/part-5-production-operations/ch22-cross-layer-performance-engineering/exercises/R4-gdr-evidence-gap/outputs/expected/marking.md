# Marking scheme: R4 What L1 cannot show about GPUDirect RDMA

Type reflection · kind written · tier L1 · 4 points

**Evidence required:** concise written answers, each naming the evidence (or missing evidence) it relies on.

| Criterion | Points |
|---|---|
| States what the L1 bundle shows (correlation, bounce-copy metric, channel lines, lsmod) and that it cannot quantify lost bandwidth | 1 |
| L2 evidence: peer-memory module absent AND DMA-BUF unavailable on that stack | 1 |
| L3 evidence: all_reduce_perf R550 vs R570 with and without the module, >= 5 runs, busbw median and spread | 1 |
| Channel lines with /GDRDMA recorded with a manifest | 1 |
