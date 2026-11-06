# Marking scheme: 8.17 What a two-node ib_write_bw does not tell you

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** three distinct gaps, each tied to a mechanism (e.g., congestion, rail collisions, GPUDirect path).

| Criterion | Points |
|---|---|
| Gap 1 tied to a mechanism (e.g. congestion/incast across many senders) | 1 |
| Gap 2 tied to a mechanism (e.g. ECMP/rail collisions with many flows) | 1 |
| Gap 3 tied to a mechanism (e.g. GPUDirect RDMA path, NCCL overheads, stragglers, long-run stability) | 1 |
