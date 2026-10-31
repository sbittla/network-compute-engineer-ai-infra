# 13.4 — Why utilization.gpu stays near 100 %: worked solution

**Mechanism (Section 13.8).** `utilization.gpu`, as reported by `nvidia-smi` and NVML, is the fraction
of the sample period during which *at least one kernel* was executing on the GPU. It does not measure
how many SMs were busy or whether any useful arithmetic happened. A rank waiting for a straggler sits
inside an NCCL collective, and NCCL's collective kernels are already running, polling flags in memory
until the peer's data arrives. The GPU therefore counts as "busy" for the whole wait. In the lab bundle
`utilization.gpu` reads 99.7 % both before and after the incident, while SM activity falls from 58.5 %
to 54.7 % `[SIMULATED]`.

**Two better metrics:**

1. **DCGM profiling metrics:** `DCGM_FI_PROF_SM_ACTIVE` (fraction of SMs with at least one warp
   resident) or `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` (Tensor Core pipe activity) `[VENDOR-SPEC, 2026-10]`.
   NCCL's spinning kernels occupy only one block per channel, a few of 132 SMs, and issue no tensor
   work, so these metrics drop during collective waits.
2. **Per-rank phase timings** from CUDA events in the training loop: compute, wait-in-collective
   (before the last rank arrives), transfer (after the last arrival), and data-loader wait. These map
   directly to the decision table (Table 13.4): wait up for all but one rank means a straggler, transfer
   up for everyone means a communication problem.

**Also acceptable.** NIC throughput measured over the transfer phase only (burst rate), not the step
average.

**Common wrong answer.** "The GPU is computing the reduction." The reduction arithmetic is tiny. The time
is spent spinning while waiting.
