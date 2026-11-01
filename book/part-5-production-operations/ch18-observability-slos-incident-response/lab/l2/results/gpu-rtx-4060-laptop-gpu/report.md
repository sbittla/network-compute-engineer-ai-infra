# Lab 18 L2: Prometheus exposition of real telemetry, step-time SLI and burn rate

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T01:04:53Z.

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

## Per-phase SLI and telemetry (computed from the scraped exposition)

Baseline step **19.70 ms** (median of ≥ 5 timed reps, after a 3 s clock warm-up and 3 warm-ups); SLO: step ≤ 1.1 x baseline = 21.67 ms (a histogram bucket sits exactly there), target 0.99.

| Phase | Scrapes | Steps | SLI (good/all) | Mean step ms (median) | Useful TFLOP/s | GPU util % (`nvsmi_gpu_utilization_percent`) | Power W | SM MHz | Max burn (10-scrape) | `GPUUtilLow` fires |
|---|---|---|---|---|---|---|---|---|---|---|
| healthy | 14 | 701 | 0.9957 | 19.943 | 27.4883 | 99.0 | 80.0 | 2302.0 | 0.4 | no |
| degraded | 15 | 523 | 0.0 | 28.594 | 19.2416 | 64.0 | 70.8 | 2520.0 | 100.0 | yes |
| recovered | 11 | 548 | 0.9964 | 20.063 | 27.4867 | 99.0 | 79.9 | 2280.0 | 86.26 | no |
| busy_idle | 9 | 506 | 0.998 | 17.733 | 0.0 | 99.0 | 25.1 | 2520.0 | - | no |

## Alerting from the scrapes

- SLI over the three training phases: **0.702** against a 0.99 target.
- Regression injected at t = 15.0 s; detected from the scraped mean step time at t = 17.0 s (delay 2.0 s); multi-window fast-burn page (long 10 and short 2 scrapes > 14.4) first true at t = 17.0 s (delay 2.0 s). Burn rate from `solutions/lab/telemetry_analysis.py`.
- Scrape interval median 1.0 s, p95 1.0002 s; nvidia-smi sample age at scrape p95 0.2407 s; 26 series and 2763 bytes per scrape; 0 format errors, 0 counter decreases.

## Exposition (last scrape, excerpt)

```text
# HELP nvsmi_gpu_utilization_percent Percent of the sample period a kernel was running (DCGM_FI_DEV_GPU_UTIL).
# TYPE nvsmi_gpu_utilization_percent gauge
nvsmi_gpu_utilization_percent{gpu="0",Hostname="6b024ac8c505"} 98
# HELP nvsmi_power_draw_watts Board power draw (DCGM_FI_DEV_POWER_USAGE).
# TYPE nvsmi_power_draw_watts gauge
nvsmi_power_draw_watts{gpu="0",Hostname="6b024ac8c505"} 25.01
# HELP nvsmi_sm_clock_hertz SM clock (DCGM_FI_DEV_SM_CLOCK, which is in MHz).
# TYPE nvsmi_sm_clock_hertz gauge
nvsmi_sm_clock_hertz{gpu="0",Hostname="6b024ac8c505"} 2.535e+09
# HELP nvsmi_temperature_celsius GPU temperature (DCGM_FI_DEV_GPU_TEMP).
# TYPE nvsmi_temperature_celsius gauge
nvsmi_temperature_celsius{gpu="0",Hostname="6b024ac8c505"} 63
# HELP nvsmi_clocks_event_reasons Active clock-event-reason bitmask (DCGM_FI_DEV_CLOCKS_EVENT_REASONS).
# TYPE nvsmi_clocks_event_reasons gauge
nvsmi_clocks_event_reasons{gpu="0",Hostname="6b024ac8c505"} 0
# HELP nvsmi_memory_used_bytes Framebuffer memory used (DCGM_FI_DEV_FB_USED, which is in MiB).
# TYPE nvsmi_memory_used_bytes gauge
nvsmi_memory_used_bytes{gpu="0",Hostname="6b024ac8c505"} 359661568
# HELP node_cpu_busy_ratio Host CPU busy fraction since the previous scrape (/proc/stat).
# TYPE node_cpu_busy_ratio gauge
node_cpu_busy_ratio{host="6b024ac8c505"} 0.0952965235
# HELP lab_phase_info Phase of the experiment (1 for the active phase).
# TYPE lab_phase_info gauge
lab_phase_info{job="l2",phase="warmup"} 0
lab_phase_info{job="l2",phase="healthy"} 0
lab_phase_info{job="l2",phase="degraded"} 0
lab_phase_info{job="l2",phase="recovered"} 0
lab_phase_info{job="l2",phase="busy_idle"} 1
# HELP train_steps_total Completed training steps.
# TYPE train_steps_total counter
train_steps_total{job="l2"} 2379
# HELP train_useful_flop_total FLOPs of useful (GEMM) work completed.
# TYPE train_useful_flop_total counter
train_useful_flop_total{job="l2"} 1.0302424e+15
# HELP train_main_thread_cpu_seconds_total CPU time of the training thread.
# TYPE train_main_thread_cpu_seconds_total counter
train_main_thread_cpu_seconds_total{job="l2"} 45.7162689
# HELP train_step_seconds Wall time of one training step.
# TYPE train_step_seconds histogram
train_step_seconds_bucket{job="l2",le="0.009849"} 0
train_step_seconds_bucket{job="l2",le="0.015758"} 0
train_step_seconds_bucket{job="l2",le="0.019698"} 547
train_step_seconds_bucket{job="l2",le="0.021667"} 1850
train_step_seconds_bucket{job="l2",le="0.024622"} 1854
train_step_seconds_bucket{job="l2",le="0.029546"} 2364
train_step_seconds_bucket{job="l2",le="0.039395"} 2378
train_step_seconds_bucket{job="l2",le="0.078791"} 2379
train_step_seconds_bucket{job="l2",le="+Inf"} 2379
train_step_seconds_sum{job="l2"} 50.9486831
train_step_seconds_count{job="l2"} 2379
```

## What to conclude

- **Utilization is not efficiency.** In the busy-idle phase GPU utilization stayed at 99.0 % (the `GPUUtilLow` rule did not fire) while useful work fell from 27.4883 to 0.0 TFLOP/s and power fell from 80.0 to 25.1 W. `utilization.gpu` only says that *a* kernel was resident. DCGM's `PROF_SM_ACTIVE` (not available on this GeForce laptop) or a job-level goodput SLI is what catches it.
- **The symptom-based SLI catches the injected stall within a scrape or two**, and the multi-window burn rate pages inside the long window, which is the lab's Task 3 design measured on a real loop.
- This is a **laptop Ada GPU** behind WSL2 with `nvidia-smi` as the exporter, not an H100 node with dcgm-exporter: metric names here are `nvsmi_*`, and the DCGM field each one stands for is in its `# HELP`. Absolute numbers do not transfer; the alert logic does.

- Scrape interval 1 s; nvidia-smi samples every 250 ms and the scrape exports the newest row (staleness recorded).
- Burn-rate windows are 10 and 2 scrapes in place of 1 h and 5 min; the threshold 14.4 is the SRE-workbook fast-burn page. The arithmetic is the lab's; only the time base is compressed.
- The degraded phase is an injected host-side sleep after each step (stall = 50 % of the baseline step), i.e. a real slowdown of a real loop, not a synthetic series.
- The baseline is calibrated after a fixed-time clock warm-up (3 s); without it a laptop GPU calibrates at idle clocks and the baseline comes out ~2x the healthy step.
