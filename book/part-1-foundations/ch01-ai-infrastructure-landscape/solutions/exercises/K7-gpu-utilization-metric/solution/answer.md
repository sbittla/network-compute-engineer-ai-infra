# K7 — Why `nvidia-smi` "GPU utilization" is weak evidence of compute-bound work

Source: manuscript Section 1.6 (Pitfall after Table 1.7) and Section 1.11. Field names
`[VENDOR-SPEC, 2026-10]`.

`nvidia-smi` "GPU utilization" (DCGM `DCGM_FI_DEV_GPU_UTIL`, deprecated in DCGM 4.7 in favour of
`DCGM_FI_DEV_GPU_UTIL_RATIO`) is the fraction of the sample period during which *at least one kernel* was
running on the GPU. It says nothing about how many SMs were busy or whether the Tensor Cores were doing
math. An NCCL kernel spinning while it waits for a slow peer counts as 100 % busy. A memory-bound decode
kernel that keeps Tensor Cores idle also counts as busy. In the Section 1.11 incident, utilization stayed
at 96–97 % while the step time doubled.

**Better metrics:** `DCGM_FI_PROF_SM_ACTIVE` (fraction of SMs with work resident) and
`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` (Tensor Core pipe activity), plus `DCGM_FI_PROF_DRAM_ACTIVE` for
memory-bound phases. DCGM 4.6 and later name them `DCGM_FI_PROF_SM_UTIL_RATIO`,
`DCGM_FI_PROF_TENSOR_UTIL_RATIO` and `DCGM_FI_PROF_DRAM_UTIL_RATIO`, keeping the old names as aliases. For
a step-level view, use an Nsight Systems timeline, which shows communication time directly.

**Marking note:** the key gives 2 points; this folder scores it out of 4.
