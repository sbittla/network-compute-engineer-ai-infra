# Lab 19 L2: read-only GPU health queries and clock-event-reason interpretation

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T01:06:54Z.

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

## Read-only health queries

| Query | Value | Reading |
|---|---|---|
| Identity | `NVIDIA GeForce RTX 4060 Laptop GPU`, GPU-fe211e06-dfa3-0d80-fb58-b775a89cc629, BDF 00000000:01:00.0, serial [N/A] | serial is [N/A] on GeForce: track the UUID |
| Firmware | VBIOS 95.07.28.00.59, InfoROM G002.0000.00.03, driver 592.82 | record in the manifest |
| ECC | mode [N/A] | no ECC on this SKU; on HBM parts read volatile and aggregate counters |
| Row remapper | corr 0 / uncorr 0, pending No, failure No; bank availability {'Max': 64, 'High': 0, 'Partial': 0, 'Low': 0, 'None': 0} | pending=Yes means a reset is needed before the remap takes effect (exercise K2) |
| Retired pages pending | [N/A] | pre-Ampere mechanism |
| Recovery action | None | the driver's own recommendation |
| PCIe | Gen4 x8; device max Gen4 x8; host max Gen5; replays 0 (rollovers 0) | a rising replay count is the quiet-downtrain signal (exercise T1) |

Lab `gpu_actions` (`solutions/lab/incident_toolkit.py`) on this real row: **healthy (no action)**.

`nvidia-smi topo -m`:

```text
GPU0	CPU Affinity	NUMA Affinity	GPU NUMA ID
GPU0	 X 				N/A

Legend:

  X    = Self
  SYS  = Connection traversing PCIe as well as the SMP interconnect between NUMA nodes (e.g., QPI/UPI)
  NODE = Connection traversing PCIe as well as the interconnect between PCIe Host Bridges within a NUMA node
  PHB  = Connection traversing PCIe as well as a PCIe Host Bridge (typically the CPU)
  PXB  = Connection traversing multiple PCIe bridges (without traversing the PCIe Host Bridge)
  PIX  = Connection traversing at most a single PCIe bridge
  NV#  = Connection traversing a bonded set of # NVLinks
```

## Clock-event reasons by phase

| Phase | s | SM MHz | Mem MHz | Power W | Max C | Util % | Reasons (share of samples) | Counter delta (s) | Interpretation | Action |
|---|---|---|---|---|---|---|---|---|---|---|
| idle | 4.18 | 330.0 | 405.0 | 18.71 | 57.0 | 0.0 | {'GPU_IDLE': 1.0} | 0 | idle: clocks parked, nothing to run | none |
| gemm | 25.0 | 2295.0 | 8000.0 | 79.98 | 78.0 | 100.0 | {'SW_POWER_CAP': 1.0} | 0 | power-limited at the enforced limit: the normal state of a GPU working flat out | none: normal under full load (judge the sustained clock against peers) |
| copy | 12.01 | 2520.0 | 8000.0 | 52.32 | 67.0 | 99.0 | none | 0 | busy below max boost with no reason asserted: the voltage/frequency curve, not throttling | none: compare against peers' sustained clock |
| idle_after | 6.02 | 285.0 | 405.0 | 14.07 | 64.0 | 0.0 | {'GPU_IDLE': 0.731} | 0 | idle: clocks parked, nothing to run | none |

## What to conclude

- Under the GEMM soak the GPU sits at its **80 W enforced limit** with `SW_POWER_CAP` in 100 % of samples and the SM clock at 2295.0 MHz, below the 3105 MHz maximum. That is normal operation, not a fault (exercise K4): the clock that matters is the *sustained* clock compared with the GPU's peers.
- The memory-bound copy soak draws 52.32 W with `SW_POWER_CAP` in 0 % of samples: the reason depends on the workload, so compare like with like.
- A thermal or power-brake reason would change the action from "none" to "drain and inspect". A rising PCIe replay count, or a link below its maximum under load, is a hardware signal even when no job has failed yet.
- The driver's `sw_power_cap` counter advanced by 0.0 x the time the sampled bit said the cap was active. A ratio well below 1 means the counter lags or is not maintained on this platform (WSL2), so the sampled bitmask is the evidence here. A report must say which source it used.
- Right after a load ends, clocks and power take seconds to decay and `GPU_IDLE` is not yet asserted in every sample (the `idle_after` row). An idle health snapshot taken too early looks like a busy GPU.
- This is a **laptop Ada GPU** with an 80 W-class limit, not an H100 at 700 W. The reason codes and the decision rules transfer; the clock and power values do not.

## Not runnable on this host

| Part | Probe | Needs |
|---|---|---|
| ECC volatile/aggregate counters (nvidia-smi -q -d ECC) | ECC mode [N/A] on this SKU | a GPU with ECC-protected HBM/GDDR (data-centre SKU) |
| Xid / AER lines in the kernel log (journalctl -k | grep -E 'NVRM: Xid|AER') | dmesg rc=1: dmesg: read kernel buffer failed: Operation not permitted; journalctl present: False | host kernel-log access (root on the host, not in an unprivileged container) |
| PCIe AER capability (lspci -vvv -s <bdf>) | lspci rc=0; /sys/bus/pci/devices = ['5582:00:00.0', '61e4:00:00.0', '6294:00:00.0', 'a1c2:00:00.0'] (WSL2 exposes virtual PCI, not the GPU's BDF) | bare-metal Linux with pciutils and root |
| dcgmi diag -r 2/3 | dcgmi on PATH: False | DCGM host engine on a data-centre GPU |
| rank_map NIC columns (hca, hca_bdf, rail, leaf, leaf_port, backend_ip) | /sys/class/infiniband present: False; ibdev2netdev: False; lldpctl: False | RDMA HCAs, rdma-core, LLDP neighbours on the backend switches |
| L3 link-flap trials (3 s / 8 s / 15 s) vs NCCL_IB_TIMEOUT x NCCL_IB_RETRY_CNT | torch.cuda.device_count() = 1; no RDMA device | 2+ RDMA nodes in a dedicated partition and an authorised port to disable |
| host DRAM ECC (EDAC: /sys/devices/system/edac/mc) | EDAC sysfs absent | a server platform with ECC DIMMs and the EDAC driver |

- All health queries are read-only: nothing is reset, reconfigured, or written to the device.
- Clock-event reasons sampled every 200 ms (nvidia-smi -lms); per-reason counters read before and after each phase.
