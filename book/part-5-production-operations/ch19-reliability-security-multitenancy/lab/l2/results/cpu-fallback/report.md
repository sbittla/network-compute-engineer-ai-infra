# Lab 19 L2: read-only GPU health queries and clock-event-reason interpretation

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:07:48Z.

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

## Read-only host health queries

| Query | Value |
|---|---|
| CPU / cores / memory | 13th Gen Intel(R) Core(TM) i7-13700HX / 24 / 7.8 GiB |
| Kernel | 6.18.54.1-microsoft-standard-WSL2 |
| EDAC (host ECC) present | False |
| PSI present | True |

## Pressure-stall information by phase

| Phase | s | CPU busy | PSI some stall (s) | share of wall time | Interpretation |
|---|---|---|---|---|---|
| idle | 4.02 | 0.047 | 3.067 | 0.763 | runnable tasks waited for a CPU (PSI is VM-wide: other workloads on the host count) |
| gemm | 25.01 | 0.565 | 6.919 | 0.277 | runnable tasks waited for a CPU (PSI is VM-wide: other workloads on the host count) |
| copy | 12.01 | 0.587 | 4.161 | 0.347 | runnable tasks waited for a CPU (PSI is VM-wide: other workloads on the host count) |
| idle_after | 6.02 | 0.047 | 3.711 | 0.616 | runnable tasks waited for a CPU (PSI is VM-wide: other workloads on the host count) |

_CPU fallback: no GPU was visible, so there are no clock-event reasons, no row remapper and no PCIe link to read. The host-side health queries ran read-only, and PSI stands in for "why is this device slower than it could be". GPU-only invariants were skipped._

## Not runnable on this host

| Part | Probe | Needs |
|---|---|---|
| Xid / AER lines in the kernel log (journalctl -k | grep -E 'NVRM: Xid|AER') | dmesg rc=1: dmesg: read kernel buffer failed: Operation not permitted; journalctl present: False | host kernel-log access (root on the host, not in an unprivileged container) |
| PCIe AER capability (lspci -vvv -s <bdf>) | lspci rc=0; /sys/bus/pci/devices = ['5582:00:00.0', '61e4:00:00.0', '6294:00:00.0', 'a1c2:00:00.0'] (WSL2 exposes virtual PCI, not the GPU's BDF) | bare-metal Linux with pciutils and root |
| dcgmi diag -r 2/3 | dcgmi on PATH: False | DCGM host engine on a data-centre GPU |
| rank_map NIC columns (hca, hca_bdf, rail, leaf, leaf_port, backend_ip) | /sys/class/infiniband present: False; ibdev2netdev: False; lldpctl: False | RDMA HCAs, rdma-core, LLDP neighbours on the backend switches |
| L3 link-flap trials (3 s / 8 s / 15 s) vs NCCL_IB_TIMEOUT x NCCL_IB_RETRY_CNT | torch.cuda.device_count() = 0; no RDMA device | 2+ RDMA nodes in a dedicated partition and an authorised port to disable |
| host DRAM ECC (EDAC: /sys/devices/system/edac/mc) | EDAC sysfs absent | a server platform with ECC DIMMs and the EDAC driver |

- All health queries are read-only: nothing is reset, reconfigured, or written to the device.
- Clock-event reasons sampled every 200 ms (nvidia-smi -lms); per-reason counters read before and after each phase.
