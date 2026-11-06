# 2.1.7 — Allocation, MFU and goodput

Source: manuscript Section 2.9 ("Four kinds of utilization").

- **Allocation:** the fraction of the cluster's GPU-hours that the scheduler gives to jobs. Idle,
  draining, in-repair and fragmented GPUs count against it.
- **MFU (model FLOPs utilization):** useful model FLOP/s (for example 6 × N × tokens per second) divided
  by the peak FLOP/s of the GPUs the job holds, while it runs. Recomputation and padding do not count as
  useful.
- **Goodput:** the fraction of allocated, running time that turns into durable progress, after
  subtracting work lost since the last checkpoint, restart and re-warm time, and checkpoint stalls.

**Why they multiply:** each applies to what is left after the previous one. Unallocated hours produce
nothing; allocated hours run at MFU; and of that work, only the goodput fraction survives failures. The
fraction of peak capability that becomes durable progress is therefore the product. With the Exercise
2.3 values, 0.80 × 0.38 × 0.92 = **0.28** `[MODELED]`, so 72 % of the paid-for peak never becomes model
progress. Because they multiply, a 5-point gain in any one factor is worth the same relative gain
overall, and the team should improve whichever is cheapest to raise.
