# 11.17 — Two effects that make DP matter more than < 1 % of step time

The model hides DP behind the backward pass of the last micro-batch and uses a clean 45 GB/s per rail.
Real effects that break that:

1. **The overlap window is tiny and fixed.** With gradient accumulation over 128 micro-batches, DP can
   only overlap with the *last* micro-batch's backward: 13.916 s / 128 × 0.667 ≈ 72 ms. The modeled DP
   time is already 170 ms, so every additional millisecond — from slower links, smaller effective
   bandwidth at bucket sizes below n½, or more parameters per GPU — lands directly on the critical path
   (Exercise 11.11 d: 3× DP time costs 0.34 s, not 0.1 s).
2. **Stragglers and jitter.** An all-reduce completes when the slowest rank arrives; a rank delayed by
   OS noise, a slow data loader, or a throttled GPU makes 63 other replicas wait inside the DP
   collective, and the wait is booked as "communication" in per-rank logs.

Also acceptable: FP32 gradient reduction (doubles DP bytes vs BF16); congestion from other jobs sharing
the spines, or ECMP collisions when DP traffic leaves its rail (Chapters 7 and 9); a rank map that is not
rail-aligned, so DP crosses the spines; ZeRO-3/FSDP turning DP into per-layer traffic that must be
prefetched in time; PFC pauses spreading from an unrelated incast.

The lesson: a small modeled *volume* does not mean a small *exposure*; measure exposed DP time in a
trace rather than inferring it from bytes.
