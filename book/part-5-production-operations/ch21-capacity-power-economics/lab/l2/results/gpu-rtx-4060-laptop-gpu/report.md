# Lab 21 L2: power draw vs throughput across workload intensities, and perf/W

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T01:10:02Z.

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
**Invariants:** all passed (fixed-V/f checks skipped at 25 % duty: DVFS-shifted, SM clock below 80 % of the full-load clock)

## Intensity sweep (medians over the level; power sampled every 100 ms)

| Workload | Duty % | Throughput | rel. | Mean W | p5-p95 W | SM MHz | Max C | SW_POWER_CAP share | Perf/W | J per unit |
|---|---|---|---|---|---|---|---|---|---|---|
| gemm | 0 | 0.000 TFLOP/s | 0.0 | 8.56 | 1.54-18.56 | 225.0 | 56.0 | 0.0 | - | - |
| gemm | 25 | 1.373 TFLOP/s | 0.0533 | 3.94 | 1.72-6.99 | 300.0 | 54.0 | 0.0 | 0.34852 | 2.8693 |
| gemm | 50 | 15.068 TFLOP/s | 0.5844 | 57.01 | 42.16-72.88 | 2520.0 | 78.0 | 0.706 | 0.26431 | 3.7835 |
| gemm | 75 | 21.258 TFLOP/s | 0.8245 | 71.4 | 55.61-83.5 | 2310.0 | 88.0 | 0.768 | 0.29773 | 3.3587 |
| gemm | 100 | 25.783 TFLOP/s | 1.0 | 75.65 | 67.94-81.33 | 2220.0 | 88.0 | 0.296 | 0.34083 | 2.9341 |
| copy | 100 | 213.270 GB/s | - | 52.45 | 51.63-53.18 | 2520.0 | 76.0 | 0.0 | 4.06616 | 0.2459 |

Power limits (read-only): default 80.0 W, enforced 80.0 W, range 5.0-120.0 W. Linear fit over the GEMM levels: P = 6.06 W + 2.934 W per TFLOP/s (R² 0.9718) `[MODELED]` from `[MEASURED]` points.

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

Best cap for the legacy-hall case: **650 W** (manuscript Table 21.7).

## What to conclude

- **Inconclusive at light duty.** The fixed-V/f comparison could not be made: at 25 % duty the GPU ran at a different clock (DVFS idled it down between bursts), so those levels do not test duty-cycling at a fixed V/f point. Clock-matched levels: 50 % -> 0.26431 TFLOP/J, 75 % -> 0.29773 TFLOP/J, 100 % -> 0.34083 TFLOP/J. Lock clocks on a dedicated native-Linux lab host to test the light-duty levels.
- **The limit that binds is not always the power cap.** At 100 % GEMM it draws 75.65 W, below the enforced 80.0 W, with `SW_POWER_CAP` in only 30 % of samples at 88.0 C: the boost clock is being reduced for temperature, and the SM clock is 2220.0 MHz versus 2520.0 MHz in the memory-bound copy at 52.45 W. Compute-bound work hits the limits that memory-bound work does not (Section 21.8: the curve is workload-dependent; Section 21.7: thermal-performance coupling).
- **Transients are real at small scale.** Within one 200 ms duty period power swings by up to 30.72 W, which is the per-GPU version of the synchronized swing that drives the transient margin in Section 21.7.
- This is a **laptop Ada GPU** with an 80 W-class limit, not a 700 W H100. Do not put these watts into the lab's rack model. Replace `power_cap_curve.csv` only with a cap sweep measured on your own data-center GPU (not runnable here).

## Not runnable on this host

| Part | Probe | Needs | Instead |
|---|---|---|---|
| power-cap sweep (nvidia-smi -i 0 -pl <W> at each cap, >= 5 runs per cap) | euid=1000, WSL2=True; limits read-only: {'power.default_limit': 80.0, 'power.min_limit': 5.0, 'power.max_limit': 120.0, 'enforced.power.limit': 80.0, 'clocks.max.sm': 3105.0} | root on a bare-metal Linux GPU host (dedicated lab system), restore the default limit afterwards | duty-cycle sweep at the default limit + the lab's modeled cap curve |
| rack PDU power (L3: peak, p99, compute/communication swing) | no PDU on a laptop | read-only access to rack PDU and facility telemetry | per-period GPU power swing |

- Duty cycle in 200 ms periods; each level runs 15 s after a 0.5 s settle (dropped). Power is power.draw.instant sampled every 100 ms; energy = mean sampled power x wall time.
- Levels run from 0 % to 100 %, so the GPU warms through the sweep; temperature is recorded per level.
- The 0 % level follows the warm-up, so the GPU idles in a high performance state (SM clock still up). Deep idle (P8, about 2 W on this laptop) takes seconds to reach: the fitted static term is the price of being ready to work.
- Re-rendered on 2026-11-01 from this results.json with the current experiment.py (check() and report()); no measured value was changed. The original render reported Invariants: FAILED because the earlier check held the DVFS-shifted 25 % level (SM clock 300 MHz vs 2,220 MHz at 100 %) to the fixed-V/f rules; that evaluation is kept under invariants_history in results.json.
