# Lab 2 L2: GPU power, clocks and throttle reasons under compute- and memory-bound load

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:33:02Z.

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

## Throughput per phase (0.5 s windows)

| Phase | Unit | Median | p95 | Min | Max | Windows |
|---|---|---|---|---|---|---|
| gemm | TFLOP/s | 27.63 | 27.91 | 2.71 | 28.22 | 93 |
| copy | GB/s | 227.63 | 227.83 | 213.41 | 228.05 | 62 |

## Power, clocks and throttle reasons (nvidia-smi, 100 ms)

| Phase | Samples | Power median (W) | p95 | p99 | Max | SM clock median (MHz) | SM clock min | Temp max (C) | Samples power-capped | Event reasons seen |
|---|---|---|---|---|---|---|---|---|---|---|
| idle | 114 | 2.1 | 18.8 | 18.9 | 19.0 | 240 | 210 | 58 | 0 % | gpu_idle |
| gemm | 405 | 80.1 | 80.8 | 81.2 | 82.5 | 2280 | 210 | 79 | 99 % | gpu_idle, sw_power_cap |
| copy | 271 | 53.4 | 53.7 | 53.9 | 54.0 | 2520 | 2520 | 79 | 0 % | - |
| cooldown | 75 | 2.3 | 22.3 | 22.4 | 22.5 | 210 | 210 | 65 | 0 % | gpu_idle |

Enforced power limit (read, not changed): **80.0 W**. GEMM: **0.3451 TFLOP/s per W**; copy: **4.264 GB/s per W** `[MEASURED]`.
FP16 tensor peak at the max SM clock 38.15 TFLOP/s; at the clock the GEMM actually ran (2280 MHz) 28.02 TFLOP/s, so the GEMM reached 99 % of it `[MODELED peak, MEASURED rate]`.

## Against the ORION capacity model

| Quantity | ORION model | Basis | This GPU | Basis |
|---|---|---|---|---|
| sustained / maximum power | 0.833 | node 8.5 kW / 10.2 kW [MODELED] | 1.001 | GPU GEMM median power / enforced power limit [MEASURED] |
| peak / sustained power | 1.1 | rack design load = max x (1 + 0.1) transient margin [MODELED] | 1.031 | GPU max instant sample / GEMM median (100 ms sampling) [MEASURED] |
| memory-bound / compute-bound power | - | not modeled (the model sizes for the compute-bound worst case) | 0.667 | copy median power / GEMM median power [MEASURED] |
| cluster IT sustained kW if nodes behaved like this GPU | 327.6 | solutions/lab/capacity_model.py: compute_power_cooling [MODELED] | 382.3 | same model, node_sustained_kw = node_max_kw x measured ratio [MODELED from MEASURED, method illustration only] |

**This is one laptop Ada GPU (RTX 4060 Laptop class, 80 W-class limit), not an HX8 node with 8 x H100-class GPUs.** Ratios transfer as *method*, not as numbers. What to conclude:

- The compute-bound GEMM ran at 100 % of the enforced limit, with the SW Power Cap reason active in 99 % of samples and the SM clock at 2280 MHz of a 3105 MHz table maximum: the power limit, not the clock table, sets throughput. This is the regime where a lower cap (Exercise 2.8) trades a little throughput for a lot of power.
- The memory-bound copy drew 67 % of the GEMM's power and was not power-capped: a cap costs memory-bound work little. Throughput per watt is a different number for each workload.
- Under the GEMM the 100 ms peak was 1.03 x the sustained median, inside the model's 1.10 transient margin, but 100 ms sampling cannot see millisecond steps. Size racks on the maximum plus margin and energy on the sustained figure, and replace both with BMC readings on the real platform. A GPU that sits at its limit under load also shows why the sustained/max ratio of a whole node (0.83 in the model) is lower than a single GPU's: CPUs, NICs, fans and PSU losses do not all peak together.

## Not runnable on this host

- **Server (node) power from the BMC: ipmitool dcmi power reading / Redfish PowerSubsystem**: needs a BMC with IPMI/Redfish read access, network access to it.
- **Exercise 2.8 power-cap sweep (nvidia-smi -pl <W> from max down to 55 %)**: needs root on a dedicated, authorised GPU server, a driver that permits power-limit changes (not WSL2 GPU paravirtualisation).

- Workload: GEMM 4096x4096x4096 float16 (torch.matmul, out=), copy 256 MiB buffer-to-buffer (read + write counted); phases idle 15 s, GEMM 45 s, copy 30 s, idle 10 s.
- Throughput is timed in ~0.5 s windows after 3 warm-up steps (>= 5 windows per phase); power, clocks and temperature are nvidia-smi samples every 100 ms during the same phase.
- The cumulative clock-event counters did not advance during this run although the active bitmask reported SW Power Cap (seen on this driver under WSL2); time power-capped is therefore the fraction of 100 ms samples whose active bitmask has the SW Power Cap bit set.
- The first 0.4 s of each phase is excluded from its telemetry statistics (nvidia-smi output lags the switch).
- power.draw.instant is used for distribution statistics; power.draw (a ~1 s average) hides transients. Even 100 ms sampling cannot see millisecond-scale load steps: the model's transient margin covers those.
