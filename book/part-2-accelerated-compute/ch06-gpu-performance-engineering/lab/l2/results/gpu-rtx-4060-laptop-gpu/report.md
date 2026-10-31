# Lab 6 L2: benchmark protocol, measured roofline and statistical decisions on a real GPU

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:37:53Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## Workload and protocol

Square GEMM n = 4096; 8 runs per arm, {'base': 55, 'AA1': 55, 'AA2': 55, 'fast': 226, 'noop': 70, 'alt': 95} iterations per run (per arm, sized to ~1 s) (5 warm-up dropped); timer: CUDA events; order: round-robin, start rotated per round.

## Arms (cleaned iterations)

| Arm | What | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Run-median spread | TFLOP/s | SM clock (MHz) | Max temp (C) | Clock events |
|---|---|---|---|---|---|---|---|---|---|---|
| base | FP32 GEMM, TF32 off | 19.789 | 20.183 | 0.453 | 18.888-21.717 | 3.0 % | 6.95 | 1830 | 80 | sw_power_cap |
| AA1 | FP32 GEMM, TF32 off (A/A group 1) | 19.746 | 20.144 | 0.377 | 18.655-21.016 | 2.7 % | 6.96 | 1845 | 79 | sw_power_cap |
| AA2 | FP32 GEMM, TF32 off (A/A group 2) | 19.755 | 20.062 | 0.302 | 18.358-20.204 | 1.5 % | 6.96 | 1845 | 79 | sw_power_cap |
| fast | BF16 GEMM | 4.831 | 5.059 | 0.112 | 4.675-6.274 | 2.1 % | 28.45 | 2370 | 80 | sw_power_cap |
| noop | FP32 GEMM via torch.mm(out=) | 19.797 | 20.144 | 0.400 | 18.605-21.138 | 1.4 % | 6.94 | 1830 | 83 | sw_power_cap |
| alt | FP32 GEMM, TF32 allowed | 10.084 | 10.398 | 0.150 | 9.811-11.291 | 1.3 % | 13.63 | 2325 | 80 | sw_power_cap |

## Decisions (`compare()` from the lab's reference analysis, unchanged)

A/A noise floor: **±1.06 %**; practical threshold 1 %.

| Candidate vs base | Clock rule | Point | 95 % band | p (perm.) | Cliff's d (runs) | Runs base/cand | Naive mean | Decision | Lab rule as written |
|---|---|---|---|---|---|---|---|---|---|
| BF16 GEMM | per-arm peer clock | -75.55 % | [-75.81 %, -75.33 %] | 0.000 | -1.00 | 8/8 | -75.09 % | **improvement** | undecidable (0/8 runs kept) |
| FP32 GEMM, TF32 allowed | per-arm peer clock | -49.04 % | [-49.42 %, -48.56 %] | 0.000 | -1.00 | 8/8 | -48.10 % | **improvement** | undecidable (0/8 runs kept) |
| FP32 GEMM via torch.mm(out=) | lab rule (session-wide peer clock) | +0.22 % | [-0.50 %, +1.47 %] | 0.241 | +0.28 | 8/8 | +0.05 % | **not_significant** | not_significant (8/8 runs kept) |
| A/A (group 1 vs 2) | lab rule | +0.15 % | [-0.88 %, +1.06 %] | 0.764 | | | | not_significant | |

Clock rule: same-kernel comparisons (A/A, no-op) use `compare()` exactly as written. Different-kernel comparisons apply the same exclusion rules but judge each run's clock against runs of the same code, because under a power cap the sustained clock depends on the kernel (pre-registered in the experiment, not chosen after seeing the data).

**Lab rule as written, on this power-capped GPU:** for BF16 GEMM and FP32 GEMM, TF32 allowed the session-wide peer clock sits between the two arms' sustained clocks, so the 95 % rule excluded the slower-clocked arm's runs and left nothing to compare (undecidable). That is the lesson: a clock rule that assumes clocks are independent of the change is only valid with locked clocks or for changes that keep the same kernel.

Clock-event reasons over all samples: {'sw_power_cap': 4448}.

## Roofline (vendor-class ceilings for this GPU)

Ceilings `[MODELED]` at clocks.max.sm = 3105 MHz: BF16 tensor 38.2, TF32 19.1, FP32 19.1 TFLOP/s; DRAM 256 GB/s (128-bit). Source: SM count x dense FLOP/clock/SM (NVIDIA architecture whitepapers) x clocks.max.sm; DRAM = bus width (NVIDIA product spec) x 2 x clocks.max.memory.

| Kernel | AI (FLOP/B) | Median (us) | p95 (us) | Achieved TFLOP/s | Achieved GB/s | Ridge | Bound | % of roof |
|---|---|---|---|---|---|---|---|---|
| copy_fp32_256MiB | 0.0 | 2374.7 | 2413.4 | 0.000 | 226.1 | 75 | memory | 88 % |
| add_fp32_256MiB | 0.1 | 3515.7 | 3551.2 | 0.019 | 229.1 | 75 | memory | 89 % |
| gemm_4096x4096x8 | 8.0 | 150.0 | 165.9 | 1.789 | 224.5 | 149 | memory | 88 % |
| gemm_4096x4096x16 | 15.9 | 150.5 | 156.7 | 3.567 | 224.7 | 149 | memory | 88 % |
| gemm_4096x4096x32 | 31.5 | 137.7 | 151.6 | 7.800 | 247.5 | 149 | memory | 97 % |
| gemm_4096x4096x64 | 62.1 | 137.7 | 185.2 | 15.596 | 251.3 | 149 | memory | 98 % |
| gemm_4096x4096x128 | 120.5 | 169.7 | 198.7 | 25.310 | 210.1 | 149 | memory | 82 % |
| gemm_4096x4096x256 | 227.6 | 319.5 | 349.1 | 26.885 | 118.1 | 149 | compute | 70 % |
| gemm_4096x4096x512 | 409.6 | 612.4 | 647.2 | 28.056 | 68.5 | 149 | compute | 74 % |
| gemm_4096x4096x1024 | 682.7 | 1198.9 | 1212.5 | 28.658 | 42.0 | 149 | compute | 75 % |
| gemm_4096x4096x2048 | 1024.0 | 2411.0 | 2480.1 | 28.503 | 27.8 | 149 | compute | 75 % |
| gemm_4096x4096x4096 | 1365.3 | 4838.1 | 4913.2 | 28.408 | 20.8 | 149 | compute | 74 % |

Measured roofs: compute **28.66 TFLOP/s**, memory **229.1 GB/s**, measured ridge **125 FLOP/B** `[MEASURED]`.
The manuscript's H100-class part: 989 TFLOP/s BF16 and 3.35 TB/s, ridge ~295 FLOP/B `[VENDOR-SPEC]`. **This is a laptop Ada GPU, not an H100**: its absolute numbers are 25-40x lower, but the shape is the same — thin GEMMs (small K) ride the memory roof, square GEMMs flatten at the compute roof, and the ridge decides which kernels a faster memory system would help.

## What to conclude

- The real effect (BF16 GEMM: -75.55 %) against the A/A floor (±1.06 %): the decision is **improvement** (exact permutation test on run medians, p = 0.000; 5 + 5 runs cannot give p below 2/252 = 0.008).
- The no-op change (FP32 GEMM via torch.mm(out=)) came out **not_significant**: a difference that small is either noise or not worth shipping, and the floor and the 1 % threshold stop it from being reported as a win.
- The naive mean of every iteration (Naive mean column) includes warm-up and excluded runs; compare it with the cleaned point.
- Below the ridge a kernel is limited by bytes, not FLOPs: a precision change only helps it through fewer bytes.

- Each run is 5 warm-up iterations (dropped by clean_runs) plus timed iterations; runs are interleaved round-robin with a rotated start. Runs share one process (a deviation from the lab's one-process-per-run rule, made so the GPU context and allocations are created once); run-to-run variance therefore understates cold-start effects.
- Telemetry is sampled every 100 ms by nvidia-smi and attached to each iteration by timestamp, so several iterations share one sample.
- GEMM DRAM bytes are compulsory traffic (each operand read once, output written once) [MODELED]: a lower bound on real traffic, so the achieved bandwidth they imply is a lower bound too.
- Clocks were not locked (no root, and a shared laptop GPU); exclusions follow the lab's pre-registered rules: non-routine clock events on > 5 % of iterations, or median SM clock < 95 % of the peer median.
