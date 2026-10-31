# M1 — Node acceptance test design (HX8)

Fail-fast order (Figure 16.3): seconds-long checks first, the 24 h burn-in late, the single-node NCCL
test last because it exercises everything together. Thresholds are `[ILLUSTRATIVE]` teaching values
from Table 16.4 unless marked; production values are derived from a measured known-good population
(exercise R1).

| # | Check | Command / tool | Measures | Pass criterion | FAIL / WARN | Duration |
|---|---|---|---|---|---|---|
| 1 | Inventory diff | Redfish `FirmwareInventory`, `dmidecode`, `lspci` vs CMDB | Serials, BDFs, part numbers | Matches CMDB record | FAIL (`INVENTORY_MISMATCH`) | 1 min |
| 2 | Firmware matrix | inventory vs `compat_matrix.yaml`, per device | Every component version | Exact production bundle | FAIL off-matrix/blocked; WARN deprecated | < 1 min |
| 3 | PCIe topology | `nvidia-smi topo -m`, `lspci -vv` | GPU↔NIC paths, ACS, width | Expected topology; x16 width | FAIL (`PCIE_DEGRADED`) | 1 min |
| 4 | GPU discovery, HBM | `nvidia-smi -L`, `--query-gpu` | Count, product, memory | 8 × H100 SXM 80 GB, ≥ 81,000 MiB | FAIL (`GPU_COUNT`, `HBM_CAPACITY`) | < 1 min |
| 5 | ECC and row remap | `nvidia-smi -q -d ECC,ROW_REMAPPER`, `dcgmi diag -r 1` | DBE, SBE, pending/failed remap | 0 DBE; no pending/failure; SBE ≤ 10 | FAIL DBE/remap; WARN SBE > 10 | 2 min |
| 6 | NVLink / fabric | `nvidia-smi nvlink --status`, Fabric Manager state | Links up, fabric state | 18/18 links per GPU; fabric `Completed` | FAIL (`NVLINK_DOWN`) | 2 min |
| 7 | NIC link | `ethtool`, `ibv_devinfo` | Link, speed, MTU | 8 × 400 Gb/s up, MTU 9000, `active_mtu` 4096; 2 × 200 Gb/s frontend | FAIL (`NIC_SPEED`, `NIC_MTU`) | 1 min |
| 8 | RDMA pair per rail | `ib_write_bw` vs a same-rail reference node | Pair bandwidth | ≥ 360 Gb/s per rail | FAIL (`RDMA_PAIR_BW_LOW`) | 15 min |
| 9 | Storage | `nvme smart-log`, read-only `fio` | Drive count, media errors, read GB/s | 8 drives, 0 media errors, ≥ 40 GB/s | FAIL | 10 min |
| 10 | PCIe under load | `--query-gpu pcie.link.gen.current` during stress | Gen under load | Gen 5 under load (idle Gen 1 is normal) | FAIL | during 11 |
| 11 | DCGM long | `dcgmi diag -r 3 -j` | Compute, memory bandwidth, targeted power | Level ≥ 3, Pass | FAIL (`DCGM_DIAG_FAIL`) | 45 min |
| 12 | Burn-in + thermals | 24 h stress, log temperature and clock-event reasons | Thermal/power-brake slowdown, max temperature, new SBE | No thermal slowdown or power brake; max < 87 °C | FAIL (`THERMAL_THROTTLE`); SBE growth WARN | 24 h |
| 13 | Kernel log | `dmesg`, journal | Xid events during the run | None | FAIL (`XID_PRESENT`) | continuous |
| 14 | Single-node NCCL | `all_reduce_perf -g 8`, record NCCL version and algorithm | busbw at 8 GiB | ≥ 400 GB/s (NVLS) / ≥ 330 GB/s (Ring); algorithm recorded | FAIL (`NCCL_BUSBW_LOW`, `NCCL_ALGO_UNRECORDED`) | 10 min |

**Total duration** `[MODELED from ILLUSTRATIVE step times]`: 31 min of quick checks + 45 min DCGM `-r 3`
+ 1,440 min burn-in + 10 min NCCL = 1,526 min ≈ **25.4 h** per node; nodes run in parallel, so a
32-node delivery takes ≈ 25.4 h wall clock (Section 16.6).

**Recorded with every run:** `policy_version` (e.g. `acceptance-policy v3, sha256:…`), bundle ID,
node serial, run ID, tool versions (driver, DCGM, NCCL), operator/automation identity, and the raw
outputs of every check. WARN results need a waiver ID with an expiry to pass to `validated`.

**Design notes.** Judge PCIe speed under load, not idle; test RDMA against a *same-rail* peer, not
host loopback; the NCCL floor depends on the algorithm (the lab's orion-n15 Ring distractor); count
GPUs against the *expected* number so tests do not silently adapt to 7 GPUs (orion-n04).
Multi-node NCCL and fabric validation run after a group of nodes is validated (Chapter 12).

Source: Section 16.5, Table 16.4, Figure 16.3, Section 16.6 Step 3.

## Hardware run

`python scripts/hw_labs.py run ch16 --device gpu` executes the single-GPU subset of this design in fail-fast
order: discovery and inventory, the memory write/verify pattern test, PCIe link under load, a GEMM throughput
check, and a sustained burn-in with temperature, power, clock and clock-event-reason sampling. It evaluates the
result with the lab policy, recording `policy_version` as `acc-2026.10+local-sku`. It shows that `SW_POWER_CAP`
under load is normal (ignored by the policy) and that the burn-in duration is a real field, not a constant. The
checks in the table that need an HX8 (NVLink, RDMA pair bandwidth, single-node NCCL, DCGM `-r 3`, NVMe/fio) are
probed and listed as not runnable in `lab/l2/results/*/report.md`. With `--device cpu` the same harness runs on
host RAM and CPU cores.
