# Q1 — Why "GPU utilization 97 %" is weak evidence of compute-bound training

Source: manuscript Section 1.6 (Pitfall) and Section 1.11; the same question as K7.

The utilization metric (`nvidia-smi`, DCGM `DCGM_FI_DEV_GPU_UTIL`) reports the fraction of time at least
one kernel was running. A training step that is waiting on a slow all-reduce still runs an NCCL kernel, so
it reads as busy: in the Section 1.11 incident the job's step time doubled while utilization stayed at
96–97 %. The metric cannot distinguish Tensor Core math from spinning in a collective or streaming memory.

Better evidence: `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` and `DCGM_FI_PROF_SM_ACTIVE` (DCGM 4.6+:
`DCGM_FI_PROF_TENSOR_UTIL_RATIO`, `DCGM_FI_PROF_SM_UTIL_RATIO`), step time scaling with FLOPs, and an
Nsight Systems timeline that shows how much of the step is compute kernels rather than communication.
