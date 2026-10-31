# 3.16 — Why the Section 3.11 cost is an upper bound

Source: manuscript Section 3.11 Steps 4–6.

**Assumptions that make it an upper bound.**

1. **No overlap.** The full DP all-reduce time is counted as exposed. Frameworks overlap it with the
   backward pass; with PP only ≈ 70 ms is hidden, so the bound is nearly tight but still a bound.
2. **No routing around the slow link.** NCCL can send some rank-3 traffic through another GPU's NIC over
   NVLink (PXN), so the observed penalty can be smaller.
3. **Illustrative rates.** 45 GB/s achievable on a healthy rail and 82 % PCIe efficiency are assumptions
   inside a 79–87 % band. A higher real efficiency on the degraded link lowers the extra time.
4. **Only the DP all-reduce is affected.** Pipeline sends and checkpoint traffic are ignored here.
   Including them would *raise* the cost, so this assumption cuts the other way; say so.

**L3 measurement that replaces it.** In a dedicated test allocation containing the degraded node:

- Run `all_reduce_perf -b 1G -e 8G -f 2 -g 1` across the eight nodes' local-rank-3 GPUs (the affected
  ring), and the same on a healthy rail (for example local rank 2). Use ≥ 5 runs after warm-up and report
  the median bus bandwidth and the p95 time at the 4–8 GB sizes.
- Run 200 W-TRAIN steps (after warm-up) with and without the degraded node in the allocation, ≥ 3
  repetitions each, and report the median and p95 step time and their difference with its spread
  (min–max across repetitions).

The measured step-time delta replaces the ≤ 1.015 s bound and is labelled `[MEASURED]`; record NCCL
version, `NCCL_DEBUG=INFO` transport lines (to see whether PXN is used), and the link state during the
run.
