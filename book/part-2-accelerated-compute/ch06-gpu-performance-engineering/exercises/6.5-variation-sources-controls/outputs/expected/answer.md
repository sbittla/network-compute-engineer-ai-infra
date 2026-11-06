# 6.5 — Sources of run-to-run variation and their controls (model answer, 5 points)

Relies on manuscript Section 6.5 (clocks, power, thermal), Section 6.6 (benchmark protocol, Table 6.5) and
Section 6.8 (manifests). One point per valid source–control pair; any five.

| # | Source | Control |
|---|---|---|
| 1 | **Warm-up**: first iterations pay for allocation, kernel autotuning/selection, JIT and cold caches (Lab 6: iteration 0 ≈ 1.6× slower) | Discard a fixed, pre-registered number of warm-up iterations (Lab 6: `iter < 5`) |
| 2 | **Clocks, power and thermal state**: boost varies with temperature and power; throttling lowers clocks | Lock application clocks, or record `clocks_event_reasons`, SM clock and temperature per iteration and exclude runs by a pre-registered rule judged against peers |
| 3 | **Contention**: other processes or tenants on the GPU, host, NIC or storage | Dedicated GPU/node; check `nvidia-smi --query-compute-apps` before and after; no co-scheduled jobs |
| 4 | **Software versions**: driver, CUDA, framework or library changes alter kernel selection (Lab 6 run A3, PyTorch 2.3.1, ≈ 2.7 % faster) | Manifest every run; pin the container digest; exclude mismatched runs |
| 5 | **Time drift**: conditions change across a session (room temperature, background jobs) | Interleave arms (A, B, A, B, …) rather than running all of A then all of B |
| 6 | **Input size and data**: shape-dependent kernels, data-dependent work | Fixed sizes and seeds per comparison |
| 7 | **CPU frequency and affinity**: governor, turbo, migration of the launching thread | Performance governor, pin threads to the GPU's NUMA node |
| 8 | **Timing method**: host timers include launch and sync overhead | CUDA events around the measured region, synchronized once |

**Common wrong answers.** Naming a source without a control (no credit); "run more iterations" as the control
for every source (it reduces within-run noise only, see Exercise 6.6).
