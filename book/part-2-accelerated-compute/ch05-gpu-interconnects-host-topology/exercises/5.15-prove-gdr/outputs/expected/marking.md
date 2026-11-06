# Marking scheme: 5.15 Prove GPUDirect RDMA on a real host

Type outline-mandated · kind written · tier L2 · 10 points

**Evidence required:** raw command outputs per item, NCCL `/GDRDMA` lines or `ib_write_bw --use_cuda` results, and a verdict.

| Criterion | Points |
|---|---|
| Raw command output for each of the six Table 5.3 items | 6 |
| A runtime test showing GDR in use or not: NCCL /GDRDMA channel lines or ib_write_bw --use_cuda results | 2 |
| Verdict consistent with the evidence (e.g. DMA-BUF path when nvidia_peermem is absent); not based on the distance-check line alone | 2 |
