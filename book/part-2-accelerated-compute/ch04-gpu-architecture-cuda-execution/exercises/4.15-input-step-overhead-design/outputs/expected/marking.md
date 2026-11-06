# Marking scheme: 4.15 Input and step-overhead strategy for HX8

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** a one-page design with PCIe budget arithmetic, pinned-memory budget, NUMA placement, the overhead strategy with a rejected alternative, and a validation plan.

| Criterion | Points |
|---|---|
| PCIe budget arithmetic: 104,857,600 B / 60 ms = 1.75 GB/s per GPU (about 3.5 % of 50 GB/s), 3.5 GB/s per shared switch uplink | 3 |
| Pinned-memory budget (for example 3 × 100 MiB per rank = 2,400 MiB per node) and NUMA placement of ranks, loaders and buffers per socket | 3 |
| Optimizer overhead strategy (fused or foreach AdamW) defended against one rejected alternative (for example whole-step CUDA Graph) | 2 |
| Validation plan: nsys shows overlapped copies and few optimizer kernels; median step time over repeated runs vs the 60 ms target | 2 |
