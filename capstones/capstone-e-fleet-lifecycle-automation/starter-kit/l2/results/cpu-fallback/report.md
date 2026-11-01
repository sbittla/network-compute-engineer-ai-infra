# Capstone E L2: node burn-in and acceptance evidence through the L1 gate

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:15:52Z.

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

## Read-only inventory and health

No GPU visible (CPU fallback).

## Burn-in (90 s sustained torch.float32 GEMM n=1024, ~1 s windows)

| Metric | median | p95 | min | max |
|---|---|---|---|---|
| TFLOP/s per window | 0.36 | 0.40 | 0.28 | 0.41 |

Throughput first vs last quarter: 0.34 -> 0.38 TFLOP/s; window CV 9.5 %.

## Bandwidth and storage (>= 5 repetitions)

| Test | median | worst rep | best rep |
|---|---|---|---|
| host memory copy (GB/s, r+w) | 66.6 | 61.1 | 76.5 |
| sequential read, 512 MiB on overlay (GB/s) | 2.59 | 2.52 | 2.85 |

## Acceptance gate (L1 `evaluate_acceptance()`, unchanged)

Source: `instructor/reference/fleet.py`. Record written in the `acceptance_results.json` schema (see results.json, `acceptance_record`).

| Policy | passed | failing checks |
|---|---|---|
| acceptance-2026.10 (ORION HX8) | False | burn_in_duration, dcgm_diag, gpu_count, h2d_bw, nic_link_speed, nic_pcie_link, nvlink_bw, rdma_bw, storage_bw |
| local-cpu-host-calibration (this host) | True | - |

Not gated in the local policy (no evidence can be collected here; never counted as passed):

- `dcgm_diag`: dcgmi not installed (DCGM absent on this host)
- `nvlink_bw`: no NVLink on a single PCIe GPU
- `rdma_bw`: no RDMA NIC (/sys/class/infiniband absent)
- `nic_pcie_link / nic_link_speed`: no backend NIC visible (container network: lo)
- `xid_events`: kernel log not readable in the container (dmesg: Operation not permitted)
- `ecc_uncorrected`: no GPU
- `gpu_count`: no GPU: expected_gpus set to 0 for a CPU-only host
- `gpu_pcie_link`: no GPU
- `h2d_bw`: no GPU
- `thermal`: no GPU temperature sensor read
- `row_remap`: no GPU

## Not runnable here

- **DCGM level-3 diagnostics (dcgmi diag -r 3)**. Probe: dcgmi on PATH=False. Needs: DCGM installed, data-center GPU.
- **nvbandwidth device<->device / NVLink P2P**. Probe: nvbandwidth=False, NVLink in topo=False, GPUs=0. Needs: 2+ NVLink-connected GPUs.
- **nccl-tests intra-node bus bandwidth (-g 8)**. Probe: all_reduce_perf=False, GPUs=0. Needs: 8-GPU node.
- **RDMA NIC link speed, PCIe and ib_write_bw (L3)**. Probe: /sys/class/infiniband=none, ibv_devinfo=False. Needs: RDMA NICs, second node on the same rail.
- **Redfish/IPMI out-of-band inventory**. Probe: BMC_HOST set=False, ipmitool=False. Needs: BMC with a read-only account.
- **Kernel Xid scan (dmesg | grep -i xid)**. Probe: dmesg readable=False. Needs: host kernel log access (root).
- **provisioning (Ironic/MAAS/Metal3) and scheduler drain/undrain (L3)**. Probe: single container, no lab provisioner. Needs: lab provisioning system, lab Slurm or Kubernetes.

## What to conclude

- The ORION policy correctly rejects this host. A laptop is not an HX8 node: wrong GPU count, a Gen4 x8 link, no NICs, and no DCGM. That rejection is the gate working.
- A burn-in is judged on stability (first vs last quarter, window CV, clock-event reasons, temperature), not on one peak number. Power-cap or thermal reasons that appear only late in the run are exactly what a short test misses.
- Thresholds are calibrations: derive them from repeated runs on >= 2 known-good nodes of the *same* SKU, as the local policy here does for one node, and keep the checks you cannot evidence visibly ungated.
- _CPU fallback: no GPU was used. GPU telemetry, PCIe, peak-FLOP and memory-peak invariants were skipped._

- Burn-in windows are ~1 s of back-to-back GEMMs timed with CUDA events (GPU) or perf_counter (CPU); telemetry sampled every 250 ms by nvidia-smi -lms; the first second of load is excluded (clock ramp).
- Burn-in length 90 s (quick mode 8 s): a real acceptance burn-in is >= 12 h (policy burn_in_hours_min 12.0). This run calibrates the tooling, not the node.
- Bandwidth: >= 5 repetitions after 3 warm-ups; the policy gates on the worst repetition (h2d_GBps_min).
- This record is evidence from ONE node: the README asks for calibration on >= 2 known-good nodes before any threshold is trusted.
