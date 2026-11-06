# 13.5 — Overlap window for the DP reduction: worked solution

**Answer.** With pipeline parallelism and gradient accumulation, the DP gradient reduction can hide only
behind the **backward pass of the final micro-batch** on the stage. That window is ≈ 72 ms for W-TRAIN on
ORION, against ≈ 170 ms of DP communication, so at least ≈ 98 ms is exposed per step `[MODELED]`.

**Why that window (Section 13.6).** The gradients are final only after the last micro-batch's backward
has accumulated into them. Earlier micro-batches' backward passes produce partial sums that cannot be
reduced yet (reducing each micro-batch would multiply DP traffic by 128). The optimizer step depends on
the reduced gradients, so it cannot overlap either. The only independent compute left is the remainder
of the last backward pass as buckets fill, the DDP-style bucketed overlap.

**Arithmetic `[MODELED]`:**

```text
compute per step (pipeline busy time)   = 13.9 s
micro-batches per step                  = 128
compute per micro-batch                 = 13.9 s / 128 = 108.6 ms
backward share of a micro-batch         = 2/3   (backward ≈ 2× forward FLOPs)
window                                  = 108.6 ms × 2/3 = 72.4 ms ≈ 72 ms
DP all-reduce time                      = 7.66 GB / 45 GB/s = 170 ms
exposed = max(0, T_comm − T_window)     = 170 − 72 = 98 ms   (≈ 100 ms)
```

This is the value Chapter 11's step model uses (≈ 98 ms exposed).

**Ways to widen the window** (not required): overlap the reduction with the next step's first forward
(ZeRO/FSDP-style prefetch), reduce in finer buckets, or shrink DP bytes (FP8/BF16 gradient compression).

**Common wrong answers.** Using the whole backward pass (≈ 9.3 s) as the window, which would suggest full
overlap. Ignoring gradient accumulation. Forgetting the 2/3 backward share (108 ms window).
