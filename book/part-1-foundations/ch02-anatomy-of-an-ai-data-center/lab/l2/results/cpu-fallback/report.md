# Lab 2 L2: GPU power, clocks and throttle reasons under compute- and memory-bound load

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:34:52Z.

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

## Throughput per phase (0.5 s windows)

| Phase | Unit | Median | p95 | Min | Max | Windows |
|---|---|---|---|---|---|---|
| gemm | TFLOP/s | 0.36 | 0.42 | 0.33 | 0.43 | 95 |
| copy | GB/s | 35.20 | 35.71 | 34.02 | 36.13 | 62 |

_CPU fallback: no GPU and no power sensor were visible, so this run measured CPU throughput only. The power, clock and throttle invariants were skipped._

## Not runnable on this host

- **Server (node) power from the BMC: ipmitool dcmi power reading / Redfish PowerSubsystem**: needs a BMC with IPMI/Redfish read access, network access to it.
- **Exercise 2.8 power-cap sweep (nvidia-smi -pl <W> from max down to 55 %)**: needs root on a dedicated, authorised GPU server, a driver that permits power-limit changes (not WSL2 GPU paravirtualisation).
- **GPU and CPU power telemetry**: needs an NVIDIA GPU (nvidia-smi), or RAPL / hwmon power sensors exposed to the container.

- Workload: GEMM 2048x2048x2048 float32 (torch.matmul, out=), copy 128 MiB buffer-to-buffer (read + write counted); phases idle 15 s, GEMM 45 s, copy 30 s, idle 10 s.
- Throughput is timed in ~0.5 s windows after 3 warm-up steps (>= 5 windows per phase); power, clocks and temperature are nvidia-smi samples every 100 ms during the same phase.
- CPU fallback: no power sensor is visible, so only throughput is reported.
