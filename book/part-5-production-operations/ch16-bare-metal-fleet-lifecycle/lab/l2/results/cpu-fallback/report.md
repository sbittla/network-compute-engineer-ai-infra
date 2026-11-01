# Lab 16 L2: single-GPU acceptance and burn-in against the acceptance policy

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:01:14Z.

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

## Acceptance measurements

| Check | Result | Note |
|---|---|---|
| Memory write/verify (1024 MiB, 5 patterns) | 0 mismatches | fill 5.13 GB/s |
| FP32 GEMM | 397.0 GFLOP/s | CPU fallback |

## Burn-in (90.6 s soak, 356 telemetry samples)

| Signal | median / p95 / min-max |
|---|---|
| Throughput per 1 s window | 376.0 / 390.0 / 334.0-395.0 GFLOP/s |
| CPU busy | 57.0 / 62.9 / 53.5-74.8 % |
| CPU MHz (/proc/cpuinfo) | 2304.0 / 2304.0 / 2304.0-2304.0 MHz |

## Verdict from the lab evaluator

Model: `solutions/lab/fleet_lifecycle.py`, policy `acc-2026.10` thresholds unchanged; `expected` adapted to this SKU: `any GPU`, ≥ 1 MiB, Gen1 x1, 1 GPU, 0 NVLinks.

**Verdict on the checks that apply here: FAIL** ['GPU_COUNT']

- GPU_COUNT: 0 GPUs visible, expected 1

The evaluator also raised ['DCGM_DIAG_FAIL', 'FW_OFF_MATRIX', 'NCCL_ALGO_UNRECORDED', 'NIC_COUNT', 'NVME_COUNT', 'STORAGE_THROUGHPUT_LOW']: those checks have no input on this host (table below), so they are reported as not runnable, not as node faults. A real acceptance run must supply them.

## Not runnable on this host

| Policy check | Probe | Needs |
|---|---|---|
| NVLINK_DOWN (18 links per GPU) | nvidia-smi nvlink --status lists 0 links | NVLink/NVSwitch GPUs (HX8 baseboard) |
| ECC_DBE / ECC_SBE_ELEVATED | no GPU visible | a data-centre GPU with HBM ECC enabled |
| DCGM_DIAG_FAIL (dcgmi diag -r 3) | dcgmi on PATH: False | DCGM host engine + dcgmi (data-centre GPU, root) |
| NIC_COUNT / NIC_SPEED / NIC_MTU / RDMA_PAIR_BW_LOW | /sys/class/infiniband present: False; container runs with --network none | 8 x 400G RDMA NICs + 2 front-end NICs, perftest, a reference node per rail |
| NVME_COUNT / NVME_MEDIA_ERRORS / STORAGE_THROUGHPUT_LOW | /dev/nvme*: none visible; uid 1000 | root, nvme-cli, fio, dedicated data drives |
| NCCL_BUSBW_LOW / NCCL_ALGO_UNRECORDED | torch.cuda.device_count() = 0 | >= 2 GPUs (8 on NVSwitch for NVLS), nccl-tests |
| XID_PRESENT (kernel log scan) | dmesg rc=1: dmesg: read kernel buffer failed: Operation not permitted | kernel log access on the host (root, journalctl -k) |
| FW_OFF_MATRIX (BIOS/BMC/NIC firmware bundle) | no BMC/Redfish endpoint on a laptop | BMC with Redfish FirmwareInventory, a platform compatibility matrix |

## What to conclude

- _CPU fallback: no GPU was visible, so the acceptance record has no GPU section and the lab evaluator FAILs it with `GPU_COUNT`. That is the correct outcome for a node whose GPU has fallen off the bus. The memory and burn-in measurements exercise the same harness on host RAM and CPU cores; GPU-only invariants were skipped._

- Burn-in is a short scripted soak, not the policy's 24 h burn-in: duration_h in the record is the real duration.
- Telemetry sampled every 250 ms with nvidia-smi -lms (GPU) or /proc/stat (CPU); medians and p95 over the soak.
- GPU evidence runs are serial; another job on the same GPU would show up as dips in the per-window TFLOP/s.
