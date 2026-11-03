# Lab 16 L2: single-GPU acceptance and burn-in against the acceptance policy

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:59:32Z.

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

## Acceptance measurements

| Check | Result | Note |
|---|---|---|
| Memory write/verify (1536 MiB, 5 patterns) | 0 mismatches | fill 247.45 GB/s |
| FP16 GEMM 4096³ | 30.25 TFLOP/s | 79 % of the 38.2 TFLOP/s dense FP16 tensor ceiling with FP32 accumulate, a reference value `[MODELED from VENDOR-SPEC]` (512 FLOP/clk/SM x SMs x max SM clock). Corrected 2026-11-01 from the FP16-accumulate rate (1024, 76.3 TFLOP/s); the measured value and the invariant result (pass: 30.25 < 38.2) are unchanged |
| PCIe link idle → under load | Gen4 → Gen4 x8 | expected Gen4 x8 under load; a low idle gen is normal power saving (exercise K2) |
| Row remapper | pending=False, failure=False | read-only `nvidia-smi` query |

## Burn-in (90.2 s soak, 348 telemetry samples)

| Signal | median / p95 / min-max |
|---|---|
| Throughput per 1 s window | 27.3 / 27.6 / 26.3-27.8 TFLOP/s |
| GPU temperature | 80.0 / 81.0 / 72.0-82.0 C |
| Power draw | 80.0 / 80.1 / 53.2-80.4 W |
| SM clock | 2280.0 / 2310.0 / 2235.0-2340.0 MHz |
| GPU utilization | 99.0 / 99.0 / 76.0-100.0 % |

Clock-event reasons seen under load: **SW_POWER_CAP** (share of samples: {'SW_POWER_CAP': 1.0}). Driver counters, seconds accrued during the soak: {'sw_power_cap': 0.497, 'sw_thermal_slowdown': 0.0, 'hw_thermal_slowdown': 0.0, 'hw_power_brake_slowdown': 0.0}. Enforced power limit 80.0 W.

## Verdict from the lab evaluator

Model: `solutions/lab/fleet_lifecycle.py`, policy `acc-2026.10` thresholds unchanged; `expected` adapted to this SKU: `NVIDIA GeForce RTX 4060 Laptop GPU`, ≥ 8000 MiB, Gen4 x8, 1 GPU, 0 NVLinks.

**Verdict on the checks that apply here: PASS** 


The evaluator also raised ['DCGM_DIAG_FAIL', 'FW_OFF_MATRIX', 'NCCL_ALGO_UNRECORDED', 'NIC_COUNT', 'NVME_COUNT', 'STORAGE_THROUGHPUT_LOW']: those checks have no input on this host (table below), so they are reported as not runnable, not as node faults. A real acceptance run must supply them.

## Not runnable on this host

| Policy check | Probe | Needs |
|---|---|---|
| NVLINK_DOWN (18 links per GPU) | nvidia-smi nvlink --status lists 0 links | NVLink/NVSwitch GPUs (HX8 baseboard) |
| ECC_DBE / ECC_SBE_ELEVATED | ecc.mode.current = [N/A] (no ECC on this SKU) | a data-centre GPU with HBM ECC enabled |
| DCGM_DIAG_FAIL (dcgmi diag -r 3) | dcgmi on PATH: False | DCGM host engine + dcgmi (data-centre GPU, root) |
| NIC_COUNT / NIC_SPEED / NIC_MTU / RDMA_PAIR_BW_LOW | /sys/class/infiniband present: False; container runs with --network none | 8 x 400G RDMA NICs + 2 front-end NICs, perftest, a reference node per rail |
| NVME_COUNT / NVME_MEDIA_ERRORS / STORAGE_THROUGHPUT_LOW | /dev/nvme*: none visible; uid 1000 | root, nvme-cli, fio, dedicated data drives |
| NCCL_BUSBW_LOW / NCCL_ALGO_UNRECORDED | torch.cuda.device_count() = 1 | >= 2 GPUs (8 on NVSwitch for NVLS), nccl-tests |
| XID_PRESENT (kernel log scan) | dmesg rc=1: dmesg: read kernel buffer failed: Operation not permitted | kernel log access on the host (root, journalctl -k) |
| FW_OFF_MATRIX (BIOS/BMC/NIC firmware bundle) | no BMC/Redfish endpoint on a laptop | BMC with Redfish FirmwareInventory, a platform compatibility matrix |

## What to conclude

- This is a **laptop Ada GPU** (`NVIDIA GeForce RTX 4060 Laptop GPU`), not an H100 SXM in an HX8. The policy thresholds (87 C, throttle-reason classes) transfer; the expected hardware does not, so `expected` is per-SKU and versioned.
- `SW_POWER_CAP` under a GEMM soak is the normal state of a GPU working at its power limit (policy `throttle_reasons_ignore`); a thermal reason (`SW/HW_THERMAL_SLOWDOWN`) or `HW_POWER_BRAKE_SLOWDOWN` is the failure signal (exercise K4). The counters say how long each reason held, which a 1 s sample can miss.
- A real acceptance run is the same code path fed by more collectors: DCGM, NCCL, perftest, NVMe, Xid and BMC. Until those exist, a PASS here means only that the listed GPU checks passed.

- Burn-in is a short scripted soak, not the policy's 24 h burn-in: duration_h in the record is the real duration.
- Telemetry sampled every 250 ms with nvidia-smi -lms (GPU) or /proc/stat (CPU); medians and p95 over the soak.
- GPU evidence runs are serial; another job on the same GPU would show up as dips in the per-window TFLOP/s.
