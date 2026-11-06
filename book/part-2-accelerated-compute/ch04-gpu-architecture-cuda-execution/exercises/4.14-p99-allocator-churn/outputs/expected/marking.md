# Marking scheme: 4.14 p99 tripled after a release

Type troubleshooting · kind written · tier L1 · 10 points

**Evidence required:** ranked hypotheses, evidence mapping, root cause, fix with rollout, validation with percentiles.

| Criterion | Points |
|---|---|
| Three ranked hypotheses, each with its discriminating evidence (allocator churn, genuine fragmentation, CPU-side pauses) | 4 |
| Root cause: per-request empty_cache() → cudaFree implicitly synchronizes the device, then cudaMalloc re-growth on the next request | 3 |
| Fix (remove the call; measure fragmentation; allocator configuration) with canary rollout, and validation by p50/p99/p99.9 at matched load and cudaFree count about 0 | 3 |
