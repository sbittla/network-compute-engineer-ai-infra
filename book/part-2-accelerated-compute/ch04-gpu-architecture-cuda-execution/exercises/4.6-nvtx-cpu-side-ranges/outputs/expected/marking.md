# Marking scheme: 4.6 NVTX ranges versus GPU kernel extent

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** explanation of CPU-side ranges and the join.

| Criterion | Points |
|---|---|
| NVTX ranges are recorded on the CPU thread: the CPU enqueues the forward kernels asynchronously in 2.3 ms while the GPU executes them over 19.6 ms | 2 |
| Correlation IDs join each GPU activity to the API call that launched it; the GPU-side extent of the range (projected NVTX range) follows from that join | 2 |
