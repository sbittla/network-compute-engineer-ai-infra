# R3 — Evidence labels in Section 1.9

Source: manuscript Section 1.9 Steps 1–7 and Table 1.12.

**`[MODELED]` (derived by formula from stated parameters):** W-TRAIN step FLOP 1.762 × 10¹⁸ and 6.95 s
compute bound; TP, DP and PP volumes (1,202.6 GB, 7.66 GB, 2.15 GB) and their bounds; dataset I/O
16.8 MB per step; W-INFER weights per GPU 17.5 GB; KV sizes (21.47 GB per batch, 2.68 GB per GPU); decode
6.02 ms and 0.57 ms bounds; prefill 36.2 ms; KV capacity ≈ 670 sequences.

**`[ILLUSTRATIVE]` (assumed, not derived or measured):** the W-TRAIN step of 17.4 s (modeled from an
*assumed* 40 % MFU, so the ceiling fraction 0.40 is circular); HBM traffic of ≈ 2.1 TB per GPU per step;
the observed decode step ≈ 9.5 ms and prefill ≈ 75 ms; the ≈ 10 µs fixed cost per all-reduce; the 10 %
KV reserve. The peaks themselves are `[VENDOR-SPEC, 2026-10]`.

**Must become `[MEASURED]` before a budget owner sees the answer:**

| Quantity | How to measure |
|---|---|
| W-TRAIN step time and MFU | Median of ≥ 5 runs after warm-up, with p95, from step-time logs |
| Decode TPOT distribution at the target batch and context | Serving benchmark under realistic load; p50/p95 |
| NVLink and NIC byte rates | DCGM NVLink fields, `ethtool -S`/RDMA counters over a known number of steps |
| All-reduce latency at 524 KB and 8.59 GB | `all_reduce_perf` on the target nodes |
| HBM activity | `DCGM_FI_PROF_DRAM_ACTIVE` during decode; Nsight Compute for exact bytes |

The verdicts ("training is compute-bound, decode is memory-bound") are robust to these measurements; the
capacity *numbers* (tokens per second per node, step time) are not, and they are what the budget depends
on.
