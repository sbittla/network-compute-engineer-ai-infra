# K2 — Why 98 % GPU utilization is not busy compute (solution)

**What the metric is.** `GPU-Util` in `nvidia-smi`, and `DCGM_FI_DEV_GPU_UTIL`, report the fraction of the
sample period during which *at least one kernel* was executing on the GPU. It says nothing about how many
streaming multiprocessors (SMs) were busy or whether the kernel did useful arithmetic.

**Why 98 % does not show compute.** In a synchronous training step, NCCL collectives are kernels. A rank
that waits for a slow peer (a split TP group, a straggler, a lost packet being retransmitted) sits inside
an NCCL kernel spinning on a flag, so the GPU is "utilized" for the whole wait. A job whose step time
rose 15 % can therefore show the same or even higher `GPU-Util`: the extra seconds are spent in
communication kernels. The manuscript's lab shows the opposite signal in the better metric: SM active
falls from 0.57 to 0.40 on TP-split jobs `[SIMULATED]` while step time rises by ≈ 9 s.

**Better signals (name two):**

| Signal | What it measures |
|---|---|
| `DCGM_FI_PROF_SM_ACTIVE` | Fraction of cycles in which an SM has at least one resident warp, averaged over all SMs: falls when the GPU is waiting rather than computing |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Fraction of cycles the Tensor Core pipes are active: the closest DCGM proxy for GEMM throughput (MFU) |
| SM clock plus clock-event reasons (`nvidia-smi -q -d PERFORMANCE`) | Whether compute itself slowed (thermal or power slowdown) |
| Nsight Systems timeline | Compute versus communication kernel time per step, and overlap |

**Common wrong answers.** "100 % util means compute-bound"; treating `GPU-Util` as SM occupancy; naming
memory utilization (also a time-fraction metric) as the alternative.

Manuscript reference: Section 22.2 (evidence by layer) and Table 22.1.
