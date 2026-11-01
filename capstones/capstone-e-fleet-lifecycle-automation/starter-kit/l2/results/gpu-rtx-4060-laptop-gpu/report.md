# Capstone E L2: node burn-in and acceptance evidence through the L1 gate

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:14:03Z.

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

## Read-only inventory and health

| GPU | UUID | bus | VBIOS | driver | PCIe max | ECC uncorr. | row remap pending/failed |
|---|---|---|---|---|---|---|---|
| 0 NVIDIA GeForce RTX 4060 Laptop GPU | GPU-fe211e06-... | 00000000:01:00.0 | 95.07.28.00.59 | 592.82 | Gen4 x8 | [N/A] | [0]/[0] |

## Burn-in (90 s sustained torch.float16 GEMM n=4096, ~1 s windows)

| Metric | median | p95 | min | max |
|---|---|---|---|---|
| TFLOP/s per window | 27.48 | 27.79 | 26.53 | 27.92 |
| power (W) | 80 | 80 | 77 | 80 |
| SM clock (MHz) | 2280 | 2295 | 2235 | 2520 |
| memory clock (MHz) | 8000 | 8000 | 8000 | 8000 |
| temperature (C) | 80 | 82 | 72 | 83 |
| utilization (%) | 100 | 100 | 74 | 100 |
| PCIe gen (under load) | 4 | 4 | 4 | 4 |

Throughput first vs last quarter: 27.74 -> 27.32 TFLOP/s; window CV 0.7 %.
Clock-event reasons active during load (share of samples): sw_power_cap 100 %. Cumulative counter deltas over the run (us): sw_power_capping 502645.
PCIe link generation idle -> under load: Gen4 -> Gen4. This is the README's pitfall: read link state under load.

## Bandwidth and storage (>= 5 repetitions)

| Test | median | worst rep | best rep |
|---|---|---|---|
| H2D pinned (GB/s) | 12.7 | 10.9 | 12.9 |
| D2H pinned (GB/s) | 13.1 | 13.0 | 13.2 |
| device copy (GB/s, r+w) | 226.6 | 225.6 | 227.4 |
| sequential read, 512 MiB on overlay (GB/s) | 1.84 | 1.72 | 2.09 |

## Acceptance gate (L1 `evaluate_acceptance()`, unchanged)

Source: `instructor/reference/fleet.py`. Record written in the `acceptance_results.json` schema (see results.json, `acceptance_record`).

| Policy | passed | failing checks |
|---|---|---|
| acceptance-2026.10 (ORION HX8) | False | burn_in_duration, dcgm_diag, gpu_count, gpu_pcie_link, h2d_bw, nic_link_speed, nic_pcie_link, nvlink_bw, rdma_bw, storage_bw |
| local-single-gpu-calibration (this host) | True | - |

Not gated in the local policy (no evidence can be collected here; never counted as passed):

- `dcgm_diag`: dcgmi not installed (DCGM absent on this host)
- `nvlink_bw`: no NVLink on a single PCIe GPU
- `rdma_bw`: no RDMA NIC (/sys/class/infiniband absent)
- `nic_pcie_link / nic_link_speed`: no backend NIC visible (container network: lo)
- `xid_events`: kernel log not readable in the container (dmesg: Operation not permitted)
- `ecc_uncorrected`: ECC not supported/enabled on this GPU (nvidia-smi reports N/A)

## Not runnable here

- **DCGM level-3 diagnostics (dcgmi diag -r 3)**. Probe: dcgmi on PATH=False. Needs: DCGM installed, data-center GPU.
- **nvbandwidth device<->device / NVLink P2P**. Probe: nvbandwidth=False, NVLink in topo=False, GPUs=1. Needs: 2+ NVLink-connected GPUs.
- **nccl-tests intra-node bus bandwidth (-g 8)**. Probe: all_reduce_perf=False, GPUs=1. Needs: 8-GPU node.
- **RDMA NIC link speed, PCIe and ib_write_bw (L3)**. Probe: /sys/class/infiniband=none, ibv_devinfo=False. Needs: RDMA NICs, second node on the same rail.
- **Redfish/IPMI out-of-band inventory**. Probe: BMC_HOST set=False, ipmitool=False. Needs: BMC with a read-only account.
- **Kernel Xid scan (dmesg | grep -i xid)**. Probe: dmesg readable=False. Needs: host kernel log access (root).
- **provisioning (Ironic/MAAS/Metal3) and scheduler drain/undrain (L3)**. Probe: single container, no lab provisioner. Needs: lab provisioning system, lab Slurm or Kubernetes.

## What to conclude

- The ORION policy correctly rejects this host. A laptop is not an HX8 node: wrong GPU count, a Gen4 x8 link, no NICs, and no DCGM. That rejection is the gate working.
- A burn-in is judged on stability (first vs last quarter, window CV, clock-event reasons, temperature), not on one peak number. Power-cap or thermal reasons that appear only late in the run are exactly what a short test misses.
- Thresholds are calibrations: derive them from repeated runs on >= 2 known-good nodes of the *same* SKU, as the local policy here does for one node, and keep the checks you cannot evidence visibly ungated.
- This is a **laptop Ada GPU (RTX 4060 class, ~80 W enforced limit), not an H100**: compare behaviour, not numbers.

- Burn-in windows are ~1 s of back-to-back GEMMs timed with CUDA events (GPU) or perf_counter (CPU); telemetry sampled every 250 ms by nvidia-smi -lms; the first second of load is excluded (clock ramp).
- Burn-in length 90 s (quick mode 8 s): a real acceptance burn-in is >= 12 h (policy burn_in_hours_min 12.0). This run calibrates the tooling, not the node.
- Bandwidth: >= 5 repetitions after 3 warm-ups; the policy gates on the worst repetition (h2d_GBps_min).
- This record is evidence from ONE node: the README asks for calibration on >= 2 known-good nodes before any threshold is trusted.
