# Lab 18 L2: Prometheus exposition of real telemetry, step-time SLI and burn rate

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:05:55Z.

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

## Per-phase SLI and telemetry (computed from the scraped exposition)

Baseline step **6.49 ms** (median of ≥ 5 timed reps, after a 3 s clock warm-up and 3 warm-ups); SLO: step ≤ 1.1 x baseline = 7.14 ms (a histogram bucket sits exactly there), target 0.99.

| Phase | Scrapes | Steps | SLI (good/all) | Mean step ms (median) | Useful TFLOP/s | main-thread CPU-time rate % | Power W | SM MHz | Max burn (10-scrape) | `GPUUtilLow` fires |
|---|---|---|---|---|---|---|---|---|---|---|
| healthy | 14 | 2673 | 0.9843 | 5.224 | 0.3451 | 99.8 | - | - | 1.73 | no |
| degraded | 15 | 1635 | 0.0031 | 9.076 | 0.1993 | 62.9 | - | - | 99.91 | yes |
| recovered | 11 | 2191 | 0.9913 | 5.001 | 0.3606 | 99.7 | - | - | 83.55 | no |
| busy_idle | 9 | 7162 | 0.9999 | 1.247 | 0.0 | 99.7 | - | - | - | no |

## Alerting from the scrapes

- SLI over the three training phases: **0.7398** against a 0.99 target.
- Regression injected at t = 15.0 s; detected from the scraped mean step time at t = 17.0 s (delay 2.0 s); multi-window fast-burn page (long 10 and short 2 scrapes > 14.4) first true at t = 18.0 s (delay 3.0 s). Burn rate from `solutions/lab/telemetry_analysis.py`.
- Scrape interval median 1.0 s, p95 1.0004 s; 20 series and 1633 bytes per scrape; 0 format errors, 0 counter decreases.

## Exposition (last scrape, excerpt)

```text
# HELP node_cpu_busy_ratio Host CPU busy fraction since the previous scrape (/proc/stat).
# TYPE node_cpu_busy_ratio gauge
node_cpu_busy_ratio{host="fb660dba3b7f"} 0.0824402308
# HELP lab_phase_info Phase of the experiment (1 for the active phase).
# TYPE lab_phase_info gauge
lab_phase_info{job="l2",phase="warmup"} 0
lab_phase_info{job="l2",phase="healthy"} 0
lab_phase_info{job="l2",phase="degraded"} 0
lab_phase_info{job="l2",phase="recovered"} 0
lab_phase_info{job="l2",phase="busy_idle"} 1
# HELP train_steps_total Completed training steps.
# TYPE train_steps_total counter
train_steps_total{job="l2"} 14044
# HELP train_useful_flop_total FLOPs of useful (GEMM) work completed.
# TYPE train_useful_flop_total counter
train_useful_flop_total{job="l2"} 1.24715784e+13
# HELP train_main_thread_cpu_seconds_total CPU time of the training thread.
# TYPE train_main_thread_cpu_seconds_total counter
train_main_thread_cpu_seconds_total{job="l2"} 45.3699168
# HELP train_step_seconds Wall time of one training step.
# TYPE train_step_seconds histogram
train_step_seconds_bucket{job="l2",le="0.003246"} 7140
train_step_seconds_bucket{job="l2",le="0.005193"} 9803
train_step_seconds_bucket{job="l2",le="0.006492"} 12044
train_step_seconds_bucket{job="l2",le="0.007141"} 12346
train_step_seconds_bucket{job="l2",le="0.008114"} 12664
train_step_seconds_bucket{job="l2",le="0.009737"} 13700
train_step_seconds_bucket{job="l2",le="0.012983"} 14041
train_step_seconds_bucket{job="l2",le="0.025966"} 14044
train_step_seconds_bucket{job="l2",le="+Inf"} 14044
train_step_seconds_sum{job="l2"} 50.8377259
train_step_seconds_count{job="l2"} 14044
```

## What to conclude

- _CPU fallback: no GPU was visible. The exposition carries host gauges and the job's counters; the SLI, burn rate and alert replay are computed exactly as on a GPU. GPU-only invariants (utilization, power, sample staleness) were skipped. The "utilization" column is the training thread's CPU-time rate, which stays high in the busy-idle phase while useful GFLOP/s collapse: the same lesson as `utilization.gpu`._

- Scrape interval 1 s; nvidia-smi samples every 250 ms and the scrape exports the newest row (staleness recorded).
- Burn-rate windows are 10 and 2 scrapes in place of 1 h and 5 min; the threshold 14.4 is the SRE-workbook fast-burn page. The arithmetic is the lab's; only the time base is compressed.
- The degraded phase is an injected host-side sleep after each step (stall = 50 % of the baseline step), i.e. a real slowdown of a real loop, not a synthetic series.
- The baseline is calibrated after a fixed-time clock warm-up (3 s); without it a laptop GPU calibrates at idle clocks and the baseline comes out ~2x the healthy step.
