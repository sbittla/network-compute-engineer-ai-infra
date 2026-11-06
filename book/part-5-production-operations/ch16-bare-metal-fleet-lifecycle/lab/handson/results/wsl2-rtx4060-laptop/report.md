# Chapter 16 hands-on: acceptance report for `srini` (`wsl2-rtx4060-laptop`)

Policy `acc-2026.10-wsl2-laptop` (derived from the chapter's `acc-2026.10`; adaptations listed below). Collected 2026-11-05T03:34:28Z; 13th Gen Intel(R) Core(TM) i7-13700HX, 7.8 GiB, kernel 6.18.54.1-rxe+. Every value in the evidence column is `[MEASURED]` on this machine by the stage named; thresholds are the chapter's `[ILLUSTRATIVE]` values unless marked lab-local.

**Verdict on the checks that ran: PASS** (17 PASS, 0 WARN, 0 FAIL).  
**Acceptance decision: NOT VALIDATED: 12 required checks produced no evidence (N/A).**

N/A is not PASS: an N/A check produced no evidence, so it cannot support a claim that the node is healthy. A fleet controller treats N/A on a required check like a missing test result and keeps the node out of `validated` (Figure 16.1).

| Stage | Check (reason code) | Status | Evidence `[MEASURED]` | Criterion |
|---|---|---|---|---|
| discovery | `GPU_COUNT` | **PASS** | 1 GPU(s) from nvidia-smi | == 1 |
| discovery | `GPU_PRODUCT` | **PASS** | NVIDIA GeForce RTX 4060 Laptop GPU | == NVIDIA GeForce RTX 4060 Laptop GPU |
| discovery | `HBM_CAPACITY` | **PASS** | 8188 MiB (GDDR6 on this SKU, not HBM) | >= 8000 MiB |
| pcie | `PCIE_DEGRADED` | **PASS** | under load Gen4 x8 (median of 226 samples); idle Gen4 x8 | Gen4 x8 (the GPU's maximum) under load |
| gpu-health | `NVLINK_DOWN` | **N/A** | Device does not have or support Nvlink | 18/18 links per GPU (HX8); this GPU has no NVLink, so there is nothing to test |
| gpu-health | `ECC_DBE / ECC_SBE_ELEVATED` | **N/A** | ecc.mode.current = [N/A] | 0 volatile DBE, SBE <= 10: needs a GPU with memory ECC enabled |
| gpu-health | `HBM_ROW_REMAP_PENDING / HBM_ROW_REMAP_FAILURE` | **N/A** | driver reports correctable=0 uncorrectable=0 pending=No failure=No, but with ECC off nothing detects the errors that would trigger a remap | no pending remap or failure, on a GPU whose ECC feeds the remapper |
| gpu-health | `DCGM_DIAG_FAIL` | **N/A** | dcgmi on PATH: False; DCGM does not support GeForce GPUs or WSL | dcgmi diag -r 3 Pass |
| gpu-health | `GPU_NUMERICS *(lab-local)*` | **PASS** | GEMM vs CPU reference: FP32 cold 3.5e-07 hot 3.5e-07; FP16 cold 5.1e-05 hot 5.1e-05; golden output 0/58 mismatched during stress | FP32 <= 1e-05, FP16 <= 0.002 (scaled by |A||B|); golden bit-identical |
| gpu-health | `GPU_MEM_PATTERN *(lab-local)*` | **PASS** | 1.50 GiB x 5 patterns: 0 mismatched words | 0 mismatches |
| burn-in | `THERMAL_THROTTLE` | **PASS** | max 76.0 C over 120 s; reasons seen under load ['SW_POWER_CAP']; counter deltas (us) sw_power_cap 0, sw_thermal_slowdown 0, hw_thermal_slowdown 0, hw_power_brake_slowdown 0 | max < 87 C; none of ['HW_THERMAL_SLOWDOWN', 'SW_THERMAL_SLOWDOWN', 'HW_POWER_BRAKE_SLOWDOWN']; soak >= 60 s |
| burn-in | `STRESS_PERF_DECAY *(lab-local)*` | **PASS** | GEMM 27.8 TFLOP/s in the first third, 27.6 in the last (+0.8 % decay) | decay <= 10 % (else WARN) |
| host | `HOST_MEM_CAPACITY *(lab-local)*` | **PASS** | MemTotal 7.75 GiB (the WSL2 VM's share, not the laptop's DIMMs) | >= 7.5 GiB |
| host | `HOST_MEM_PATTERN *(lab-local)*` | **PASS** | 512 MiB x 5 patterns: 0 bad 1 MiB chunks; HardwareCorrupted 0 B | 0 bad chunks (a user-space pattern test, not memtest86) |
| host | `HOST_ECC *(lab-local)*` | **N/A** | EDAC present: False (a VM sees no memory controller) | 0 corrected/uncorrected DIMM errors from EDAC or the BMC SEL |
| nic | `NIC_COUNT` | **PASS** | 1 device-backed netdev(s): eth0 (hv_netvsc); virtual (no device) skipped: 0 | 1 frontend, 0 compute |
| nic | `NIC_LINK_DOWN` | **PASS** | eth0 operstate up, carrier 1 | up |
| nic | `NIC_SPEED` | **PASS** | eth0 10000 Mb/s (a value the virtual NIC reports, not a negotiated PHY rate) | >= 1000 Mb/s |
| nic | `NIC_MTU` | **PASS** | eth0 MTU 1500 | == 1500 |
| nic | `RDMA_PAIR_BW_LOW` | **N/A** | RDMA devices: none (software rxe from other labs, if any: not a compute NIC) | ib_write_bw per rail against a reference node, median of 5 >= 360 Gb/s |
| nic | `LINK_BER_HIGH` | **N/A** | no physical link: no FEC histogram or pre-FEC BER exists | pre-FEC BER < 1e-6, 0 flaps |
| nic | `GDR_PATH_FAIL` | **N/A** | no RDMA NIC, no PCIe tree visible in WSL2 (no ACS, no peer memory) | GPU-buffer >= 90 % of host-buffer bandwidth per rail |
| storage | `NVME_COUNT` | **PASS** | 1 data disk(s): sdd (Virtual Disk); NVMe devices visible: 0 | >= 1 data disk (8 NVMe on HX8) |
| storage | `NVME_MEDIA_ERRORS` | **N/A** | SMART tool: None; a Hyper-V virtual disk exposes no SMART log | critical_warning 0, media_errors 0 |
| storage | `NVME_DRIVE_SLOW` | **PASS** | /dev/sdd median 7.63 GB/s (runs 7.15, 8.02, 7.63) | each >= 1.0 GB/s, fio read-only 1 MiB QD32 O_DIRECT, median of timed runs |
| storage | `STORAGE_THROUGHPUT_LOW` | **PASS** | sum of per-disk medians 7.63 GB/s | >= 1.0 GB/s |
| collective | `NCCL_BUSBW_LOW / NCCL_ALGO_UNRECORDED` | **N/A** | 1 GPU: there is no intra-node collective to run | all_reduce_perf -g 8 busbw >= 400 (NVLS) / 330 (Ring) GB/s |
| kernel-log | `XID_PRESENT` | **N/A** | dmesg scanned (931 lines, 0 Xid), but the nvidia kernel module is not loaded in this kernel (GPU reached through /dev/dxg: True): Xid events are logged by the Windows driver and cannot appear here | no Xid during acceptance, from a log the GPU driver writes to |
| firmware | `FW_OFF_MATRIX / FW_DEPRECATED` | **N/A** | driver 592.82, VBIOS 95.07.28.00.59 recorded; no BMC/Redfish, no platform bundle to compare against | BIOS, BMC, NIC, GPU firmware == the production bundle |

## Burn-in telemetry `[MEASURED]`

120 s of FP16 GEMM stress, nvidia-smi sampled every 500 ms (233 samples, 226 at >= 90 % utilisation).

| Signal under load | median | p95 | min-max |
|---|---|---|---|
| GEMM TFLOP/s per 1 s window | 27.7 | 28.1 | 27.0-28.2 |
| temperature C | 75.0 | 76.0 | 66.0-76.0 |
| power W | 79.9 | 80.0 | 53.6-80.2 |
| SM clock MHz | 2295.0 | 2325.0 | 2280.0-2355.0 |

Clock-event reasons under load (share of samples): {'SW_POWER_CAP': 1.0}; maximum SM clock 3105.0 MHz. Driver counters accrued during the soak (µs): {'sw_power_cap': 0.0, 'sw_thermal_slowdown': 0, 'hw_thermal_slowdown': 0, 'hw_power_brake_slowdown': 0}.

## The same evidence against the chapter's HX8 policy (`acc-2026.10`, unadapted)

| Code | Why |
|---|---|
| `GPU_COUNT` | 1 != 8 |
| `GPU_PRODUCT` | NVIDIA GeForce RTX 4060 Laptop GPU |
| `HBM_CAPACITY` | 8188 MiB < 81000 |
| `PCIE_DEGRADED` | Gen4 x8 != Gen5 x16 |
| `NVLINK_DOWN` | 0/18 links |
| `NIC_COUNT` | 0 compute / 1 frontend != 8 / 2 |
| `NIC_MTU` | MTU 1500 != 9000 |
| `NVME_COUNT` | 0 NVMe != 8 |
| `STORAGE_THROUGHPUT_LOW` | 7.63 GB/s < 40.0 |

A laptop is not an HX8 node, so the unadapted policy rejects it on hardware it does not have. That is why `expected` is per SKU and versioned, while the thresholds (87 C, throttle-reason classes, numerics) transfer.

## Policy adaptations

- gpu_count 8 -> 1; gpu_product H100-SXM-80GB -> NVIDIA GeForce RTX 4060 Laptop GPU; gpu memory >= 81000 MiB -> >= 8000 MiB
- gpu_pcie Gen5 x16 -> the GPU's own maximum (Gen4 x8 on the reference machine), judged under load
- compute NICs 8 x 400G -> none expected (no RDMA NIC on a laptop): compute NIC, RDMA, link-quality and GPUDirect checks are N/A
- frontend NICs 2 x 200G, MTU 9000 -> 1 virtual NIC, >= 1000 Mb/s reported, MTU 1500
- 8 NVMe drives, >= 5 GB/s each, >= 40 GB/s total -> the data disks this OS mounts, >= 1.0 GB/s each and in total [ILLUSTRATIVE floor, not a measured fleet baseline]
