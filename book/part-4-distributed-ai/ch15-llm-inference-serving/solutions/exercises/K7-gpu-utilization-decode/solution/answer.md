# K7 — GPU utilization does not show saturation: worked solution

**What the counter measures (Section 15.2, Chapter 13).** `nvidia-smi`'s `utilization.gpu` is the
fraction of the sample period during which **at least one kernel** was executing. A decode loop launches
kernels back to back, so the counter reads ≈ 100 % whether the replica runs batch 4 or batch 128. It says
nothing about how many SMs are active, whether Tensor Cores are used, or how close HBM bandwidth is to
its limit. A memory-bound decode loop reads 100 % while using a small fraction of peak FLOP/s. In the lab
trace `gpu_busy_pct` is 97.6 % at baseline and 100 % in both the burst and the storm `[SIMULATED]`, so it
cannot tell healthy from overloaded.

**Two better signals:**

1. **DCGM DRAM active** (`DCGM_FI_PROF_DRAM_ACTIVE`, field 1005) `[VENDOR-SPEC, 2026-10]`: the fraction
   of cycles the HBM interface is busy. Decode is HBM-bound (K1), so this is the binding resource itself.
   Near ≈ 0.7–0.8 of peak means the bandwidth is saturated and more batch will lengthen the step. Pair it
   with tensor-pipe or SM active to see the compute side, for example during prefill.
2. **Engine-level signals:** running sequences against the concurrency cap, KV cache usage %, waiting
   queue depth, preemption counter, and step time against batch. These name *which* resource binds:
   running = cap with KV low means slot-bound (raise the cap or add replicas), KV ≈ 100 % with preemptions
   means memory-bound, and a growing queue with neither means a capacity shortfall. They map directly to
   actions.

**Common wrong answer.** "Look at SM clock or power." Clocks show throttling, not saturation.
