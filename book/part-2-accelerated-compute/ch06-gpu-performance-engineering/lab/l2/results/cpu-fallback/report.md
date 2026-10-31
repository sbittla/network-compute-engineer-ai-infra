# Lab 6 L2: benchmark protocol, measured roofline and statistical decisions on a real GPU

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:39:00Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## Workload and protocol

Square GEMM n = 512; 8 runs per arm, {'base': 178, 'AA1': 176, 'AA2': 176, 'fast': 349, 'noop': 172, 'alt': 389} iterations per run (per arm, sized to ~1 s) (5 warm-up dropped); timer: perf_counter; order: round-robin, start rotated per round.

## Arms (cleaned iterations)

| Arm | What | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Run-median spread | TFLOP/s | SM clock (MHz) | Max temp (C) | Clock events |
|---|---|---|---|---|---|---|---|---|---|---|
| base | FP64 GEMM, 1 thread | 6.042 | 7.170 | 0.422 | 5.643-13.662 | 4.5 % | 0.04 | 2304 | 0 | none |
| AA1 | FP64 GEMM, 1 thread (A/A group 1) | 6.014 | 6.889 | 0.397 | 5.642-11.511 | 3.9 % | 0.04 | 2304 | 0 | none |
| AA2 | FP64 GEMM, 1 thread (A/A group 2) | 6.051 | 7.074 | 0.443 | 5.651-12.862 | 5.4 % | 0.04 | 2304 | 0 | none |
| fast | FP32 GEMM, 1 thread | 2.989 | 3.512 | 0.217 | 2.811-8.762 | 4.7 % | 0.09 | 2304 | 0 | none |
| noop | FP64 GEMM via torch.mm(out=), 1 thread | 6.095 | 7.158 | 0.416 | 5.698-11.325 | 5.2 % | 0.04 | 2304 | 0 | none |
| alt | FP64 GEMM, 4 threads | 2.245 | 3.889 | 0.573 | 1.715-11.054 | 6.4 % | 0.12 | 2304 | 0 | none |

## Decisions (`compare()` from the lab's reference analysis, unchanged)

A/A noise floor: **±2.44 %**; practical threshold 1 %.

| Candidate vs base | Clock rule | Point | 95 % band | p (perm.) | Cliff's d (runs) | Runs base/cand | Naive mean | Decision | Lab rule as written |
|---|---|---|---|---|---|---|---|---|---|
| FP32 GEMM, 1 thread | per-arm peer clock | -49.92 % | [-51.61 %, -49.26 %] | 0.000 | -1.00 | 8/8 | -50.38 % | **improvement** | improvement (8/8 runs kept) |
| FP64 GEMM, 4 threads | per-arm peer clock | -62.41 % | [-63.85 %, -61.27 %] | 0.000 | -1.00 | 8/8 | -59.08 % | **improvement** | improvement (8/8 runs kept) |
| FP64 GEMM via torch.mm(out=), 1 thread | lab rule (session-wide peer clock) | +1.94 % | [-1.81 %, +4.53 %] | 0.259 | +0.41 | 8/8 | +0.45 % | **not_significant** | not_significant (8/8 runs kept) |
| A/A (group 1 vs 2) | lab rule | -0.48 % | [-1.93 %, +2.44 %] | 0.717 | | | | not_significant | |

Clock rule: same-kernel comparisons (A/A, no-op) use `compare()` exactly as written. Different-kernel comparisons apply the same exclusion rules but judge each run's clock against runs of the same code, because under a power cap the sustained clock depends on the kernel (pre-registered in the experiment, not chosen after seeing the data).

## Roofline (measured CPU roofs)

| Kernel | AI (FLOP/B) | Median (us) | p95 (us) | Achieved TFLOP/s | Achieved GB/s | Ridge | Bound | % of roof |
|---|---|---|---|---|---|---|---|---|
| copy_fp32_256MiB | 0.0 | 15625.7 | 18876.8 | 0.000 | 34.4 | 6 | memory | 78 % |
| add_fp32_256MiB | 0.1 | 18314.0 | 25420.8 | 0.004 | 44.0 | 6 | memory | 100 % |
| gemm_3072x3072x4 | 2.0 | 7028.3 | 10072.0 | 0.011 | 5.4 | 6 | memory | 12 % |
| gemm_3072x3072x16 | 7.9 | 8460.9 | 9337.6 | 0.036 | 4.5 | 6 | compute | 13 % |
| gemm_3072x3072x64 | 30.7 | 10914.3 | 11793.9 | 0.111 | 3.6 | 6 | compute | 40 % |
| gemm_3072x3072x256 | 109.7 | 21570.7 | 24383.5 | 0.224 | 2.0 | 6 | compute | 80 % |
| gemm_3072x3072x1024 | 307.2 | 69455.9 | 77627.1 | 0.278 | 0.9 | 6 | compute | 100 % |

Measured roofs: compute **0.28 TFLOP/s**, memory **44.0 GB/s**, measured ridge **6 FLOP/B** `[MEASURED]`.

## What to conclude

- The real effect (FP32 GEMM, 1 thread: -49.92 %) against the A/A floor (±2.44 %): the decision is **improvement** (exact permutation test on run medians, p = 0.000; 5 + 5 runs cannot give p below 2/252 = 0.008).
- The no-op change (FP64 GEMM via torch.mm(out=), 1 thread) came out **not_significant**: a difference that small is either noise or not worth shipping, and the floor and the 1 % threshold stop it from being reported as a win.
- The naive mean of every iteration (Naive mean column) includes warm-up and excluded runs; compare it with the cleaned point.
- Below the ridge a kernel is limited by bytes, not FLOPs: a precision change only helps it through fewer bytes.

_CPU fallback: no GPU was used. The arms are CPU GEMMs and the roofline is classified against the measured CPU roofs (no vendor ceiling is asserted), so the GPU-only invariants — vendor TFLOP/s and DRAM bounds, BF16-faster-than-FP32 and clock telemetry — were skipped._

- Each run is 5 warm-up iterations (dropped by clean_runs) plus timed iterations; runs are interleaved round-robin with a rotated start. Runs share one process (a deviation from the lab's one-process-per-run rule, made so the GPU context and allocations are created once); run-to-run variance therefore understates cold-start effects.
- CPU fallback: no GPU telemetry; sm_clock_mhz holds the mean /proc/cpuinfo MHz (static under WSL2), temperature/power are 0 and clocks_event_reasons is 'none'. torch runs single-threaded (the 'alt' arm uses 4) so that other jobs on the host do not oversubscribe the cores mid-run.
- GEMM DRAM bytes are compulsory traffic (each operand read once, output written once) [MODELED]: a lower bound on real traffic, so the achieved bandwidth they imply is a lower bound too.
