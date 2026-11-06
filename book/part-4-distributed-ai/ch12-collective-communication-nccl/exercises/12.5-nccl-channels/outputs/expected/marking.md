# Marking scheme: 12.5 NCCL channels and 350 GB/s across two nodes

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** explanation with the 8 × 50 GB/s arithmetic.

| Criterion | Points |
|---|---|
| Defines a channel: an independent ring/tree instance run by one CUDA block, with its own buffers and NIC | 2 |
| Arithmetic: 8 NICs × 50 GB/s = 400 GB/s node egress; 350 GB/s ≈ 88 % of it, so no contradiction | 2 |
