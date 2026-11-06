# 11.7 — MFU versus recompute

**Answer: no — MFU went down.** Model FLOPs utilization is defined (Section 11.9) as

```text
MFU = 6·N·D / (GPUs × peak FLOP/s × step time)
```

It counts only the model's useful FLOPs (6 per parameter per token for forward + backward). Full
activation recomputation reruns each layer's forward pass during backward, adding ≈ 2·N·D FLOPs that
do no new work. The GPUs execute *more* FLOPs per second — hardware FLOPs utilization (HFU) can rise
by the reported 8 % — but each step now takes longer, so MFU, which has the step time in the
denominator and only useful FLOPs in the numerator, falls.

**Quantified with the chapter model** `[MODELED]` (candidate K in the lab, TP 8/PP 4/DP 8, full
recompute, recompute factor 1.333, TP collectives × 1.5 because the recomputed forward pass
re-runs its two TP all-reduce-equivalents per layer):

```text
compute = 13.916 s × 1.333 = 18.55 s;   TP = 4.11 s × 1.5 = 6.17 s (4.62 s exposed)
step    = 18.55 + 0.43 bubble + 4.62 + 0.07 DP + 0.03 PP = 23.71 s  (vs 17.45 s baseline)
MFU     = 6.958 s ideal / 23.71 s = 29.3 %   (vs 6.958 / 17.45 = 39.9 %)
```

**When recompute is still worth it.** Only when the memory it frees buys a faster layout — e.g. a
smaller TP, fewer pipeline stages, or a larger micro-batch — whose speedup exceeds the ≈ 36 % step-time
penalty (33 % compute plus the re-run TP collectives). The W-TRAIN baseline already fits with selective recompute (27.4 GB), so full recompute
is pure loss here.

**Common wrong answer.** "Yes, because the GPUs are busier." Busy is HFU; MFU measures useful
throughput.
