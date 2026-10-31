# K1 — The lying utilization metric

**What `DCGM_FI_DEV_GPU_UTIL` measures.** Time-occupancy: over the sample period, the fraction of time
during which *at least one kernel* was executing, regardless of how many of the H100's 132 SMs it
used or whether it did any math. A one-block kernel occupying one SM all second reads 100 % while
`SM_ACTIVE` ≈ 1/132 ≈ 0.008.

**Role of NCCL kernels.** A training step alternates compute kernels with NCCL collective kernels.
NCCL kernels occupy a handful of SMs (one thread block per channel) and spend their time polling for
data from the network. When the fabric stalls, they simply stay resident longer, so occupancy stays
≈ 95–100 %: in INC-2291 GPU_UTIL stayed ≈ 97 % while step time rose from 17.4 s to 21.2 s
`[SIMULATED]`.

**Signals that reveal the stall:**
- `DCGM_FI_PROF_SM_ACTIVE` falls in proportion to the stall: 0.62 → ≈ 0.51 in the lab, the ratio
  17.4 / 21.2 ≈ 0.82, because fewer SMs have warps resident while only NCCL runs.
- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` falls because tensor math stops while ranks wait.
- `DCGM_FI_DEV_POWER_USAGE` falls (≈ 600–650 W dense BF16 vs ≈ 350–450 W blocked on communication
  `[ILLUSTRATIVE]`) because spinning kernels draw little power.
- Outside DCGM: the job's own step time or tokens per second (the training throughput SLI), the
  primary symptom.

**Common mistake:** "GPU_UTIL is averaged over SMs". It is not. Consequence: `GPUUtilLow` (page on
GPU_UTIL < 80) is noisy on idle inference nodes and blind to training stalls (lab planted anomaly 3).
Source: Section 18.3 ("GPU_UTIL versus SM_ACTIVE: the mechanism", "Power as a free efficiency proxy").
