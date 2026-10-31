# K1 — The ladder: worked solution

Source: manuscript Section 21.1 (table of the four definitions and Figure 21.1). Typical values are
ORION `[ILLUSTRATIVE]`.

| Rung | Numerator / denominator | Measured from | ORION typical |
|---|---|---|---|
| **Allocated** | GPU-hours allocated to jobs / *usable* GPU-hours | Scheduler accounting (Slurm `sacct`, Kubernetes requests) | 85 % |
| **Active** | GPU-hours with at least one kernel resident / *allocated* GPU-hours | `DCGM_FI_DEV_GPU_UTIL` (time occupancy) | 90–97 % |
| **MFU** | achieved model FLOP/s / peak FLOP/s of the GPUs, while the job runs | step time × model FLOPs per step (Chapter 6) | 40 % (W-TRAIN) |
| **Goodput** | GPU-hours that produced *retained* progress / allocated GPU-hours | step records, checkpoints, failure log (Chapters 18–19) | 88 % |

Each rung's denominator is the rung above, so the ladder multiplies: usable 0.850 × allocated 0.85 ×
goodput 0.88 = 0.636 of nominal GPU-hours become retained progress `[MODELED]`, and a useful GPU-hour
costs ≈ 1 / 0.636 = 1.57× a nominal one.

**Which rung does `avg(DCGM_FI_DEV_GPU_UTIL)` approximate?** The *active* rung. Mechanism: the
metric is the fraction of the sample period during which any kernel was resident on the GPU. An
NCCL kernel spinning while it waits for the network, or a tiny kernel occupying a few SMs, counts as
100 % busy, so the metric says nothing about useful math (MFU) or retained progress (goodput). When
it is averaged over *all* GPUs, the result also mixes in drained, idle and unallocated GPUs, so it
is not even a clean active figure (Section 21.11 decomposes such a 58 % into its rungs).

**Common wrong answers**

- Calling `GPU_UTIL` "compute utilization" or treating it as MFU.
- Using installed GPU-hours as the allocation denominator; the chapter uses usable GPU-hours, after
  the maintenance, repair and fragmentation reserves of Section 21.2.
- Defining goodput as "time not failed". Goodput also excludes work lost and recomputed after a
  restart since the last checkpoint.
