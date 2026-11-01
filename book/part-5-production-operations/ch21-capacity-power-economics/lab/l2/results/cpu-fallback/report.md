# Lab 21 L2: power draw vs throughput across workload intensities, and perf/W

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:11:45Z.

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

## Intensity sweep (medians over the level)

| Workload | Duty % | Throughput | rel. | CPU busy |
|---|---|---|---|---|
| gemm | 0 | 0.0000 TFLOP/s | 0.0 | 0.05 |
| gemm | 25 | 0.0677 TFLOP/s | 0.1761 | 0.229 |
| gemm | 50 | 0.1428 TFLOP/s | 0.3716 | 0.364 |
| gemm | 75 | 0.2550 TFLOP/s | 0.6636 | 0.489 |
| gemm | 100 | 0.3842 TFLOP/s | 1.0 | 0.565 |
| copy | 100 | 64.1711 GB/s | - | 0.61 |

## The lab's power-cap curve (`solutions/lab/capacity_model.py`, `[ILLUSTRATIVE]` H100-class curve)

| Cap W | rel. throughput | perf/W relative to 700 W | Nodes per rack | Cluster throughput |
|---|---|---|---|---|
| 350 | 0.7 | 1.4 | 3 | 33.6 |
| 400 | 0.79 | 1.3825 | 3 | 37.92 |
| 450 | 0.855 | 1.33 | 3 | 41.04 |
| 500 | 0.905 | 1.267 | 3 | 43.44 |
| 550 | 0.945 | 1.2027 | 3 | 45.36 |
| 600 | 0.972 | 1.134 | 3 | 46.66 |
| 650 | 0.99 | 1.0662 | 3 | 47.52 |
| 700 | 1.0 | 1.0 | 2 | 32.0 |

Best cap for the legacy-hall case: **650 W** (manuscript Table 21.4).

## What to conclude

- _CPU fallback: no GPU was visible and host power is not readable, so perf/W could not be measured. The sweep shows throughput and CPU busy time rising with duty. The lab's modeled cap curve stands in for the cap sweep. GPU-only invariants (power bounds, perf/W ordering, the tensor ceiling) were skipped._

## Not runnable on this host

| Part | Probe | Needs | Instead |
|---|---|---|---|
| power-cap sweep (nvidia-smi -i 0 -pl <W> at each cap, >= 5 runs per cap) | euid=1000, WSL2=True; limits read-only: no GPU | root on a bare-metal Linux GPU host (dedicated lab system), restore the default limit afterwards | duty-cycle sweep at the default limit + the lab's modeled cap curve |
| host power (RAPL) for CPU perf/W | /sys/class/powercap/intel-rapl present: False | bare-metal Linux with intel-rapl powercap readable | throughput and CPU busy only |
| rack PDU power (L3: peak, p99, compute/communication swing) | no PDU on a laptop | read-only access to rack PDU and facility telemetry | per-period GPU power swing |

- Duty cycle in 200 ms periods; each level runs 15 s after a 0.5 s settle (dropped). Power is power.draw.instant sampled every 100 ms; energy = mean sampled power x wall time.
- Levels run from 0 % to 100 %, so the GPU warms through the sweep; temperature is recorded per level.
- The 0 % level follows the warm-up, so the GPU idles in a high performance state (SM clock still up). Deep idle (P8, about 2 W on this laptop) takes seconds to reach: the fitted static term is the price of being ready to work.
