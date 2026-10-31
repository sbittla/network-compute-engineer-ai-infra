# Lab 5 L2: real host topology capture, PCIe link measurement and the GDR gate

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:37:37Z.

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

## Table 5.3 GPUDirect RDMA evidence on this host

| Item | Evidence (captured now) | Verdict |
|---|---|---|
| 1 Topology | topo -m devices: GPU0; PCI network controllers: 0; /sys/class/infiniband: absent | FAIL: no NIC to pair with the GPU |
| 2 Peer memory | peer-memory modules: none (36 modules visible); kernel 6.18.54.1-microsoft-standard-WSL2 | FAIL: no nvidia_peermem, and DMA-BUF needs an RDMA NIC driver |
| 3 Versions | driver 592.82; CUDA runtime 12.4; ofed_info absent; ibv_devinfo absent | INCOMPLETE: no NIC stack or firmware to match against the support matrix |
| 4 IOMMU | /proc/cmdline: initrd=\initrd.img WSL_ROOT_INIT=1 panic=-1 nr_cpus=24 hv_utils.timesync_implicit=1 printk.devkmsg=on page_reporting.page_reporting_order=5 hv_storvsc.storvsc_m | n/a: WSL2 guest kernel; the IOMMU belongs to the Windows host |
| 5 ACS | no lspci and no root; the guest PCI view is 4 paravirtual functions (2 Microsoft GPU-PV render devices, class 0x0302) | NOT READABLE here: needs root lspci -vvv on bare metal |
| 6 Runtime | NCCL /GDRDMA channel lines or ib_write_bw --use_cuda need an RDMA NIC and a peer | NOT RUNNABLE: no RDMA NIC, no second host |

**GDR verdict: impossible on this host.** RDMA devices in /sys/class/infiniband: 0; PCI network controllers: 0; GPU-NIC pairs within the PXB gate: 0. With no NIC there is no GPU-NIC path to classify, so NCCL would fall back to host-staged or socket transport for any inter-node traffic.

## nvidia-smi topo -m (raw)

```
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

## PCIe link of the GPU

| State | Gen | Width | Host max Gen |
|---|---|---|---|
| capability (GPU max) | 4 | x8 | 5 |
| idle (current) | 4 | x8 |  |
| under H2D load (current) | 4 | x8 |  |

| Case | Size (MiB) | GB/s (median) | GB/s at p95 time | n |
|---|---|---|---|---|
| h2d_pinned | 256 | 12.66 | 12.41 | 10 |
| h2d_pageable | 256 | 11.76 | 9.36 | 10 |
| d2h_pinned | 256 | 13.12 | 12.93 | 10 |

Link ceiling Gen4 x8 = **15.75 GB/s** per direction `[MODELED]`; pinned H2D reached **12.66 GB/s** (80 %) `[MEASURED]`.

What to conclude:

- The GPU is a x8 device: the host could run Gen5, the GPU trains Gen4 x8. Always read capability *and* current state; a laptop or riser slot can halve a link without any error.
- Idle link generation was Gen4, under load Gen4. A reading taken at idle can show a power-managed lower generation; capture LnkSta under load before calling a link downtrained.
- The lab's model caps a host-staged path at 18.0 GB/s on an HX8 (Gen5 x16) node. On this host the same path would be capped by this link (about 12.66 GB/s measured), which is why the model's parameters must be recalibrated per platform.
- This is a laptop Ada GPU in a WSL2 guest, not an HX8 node: there is no PCIe switch, no NIC and no second GPU, so the PIX/PXB/SYS distinctions of the lab cannot be exercised here.

## Not runnable on this host

- **Exercise 5.15 runtime proof: NCCL NET/IB/.../GDRDMA channel lines or ib_write_bw --use_cuda**: needs an RDMA NIC (ConnectX-class or similar) on the GPU's PCIe switch, nvidia_peermem or DMA-BUF support, a second host on an RDMA fabric.
- **L2 capture script (capture/capture_topology.sh) with lspci -vvv ACS/LnkSta, lstopo, ibdev2netdev, LLDP**: needs root on bare metal (not a WSL2 guest), lspci, lstopo, rdma-core, an RDMA NIC.
- **NVLink / fabric manager status (nvidia-smi nvlink --status)**: needs an NVLink-equipped multi-GPU host.

- Every row of the Table 5.3 checklist is built from a command or sysfs file read during this run; the raw topo -m output and the PCI scan are in results.json.
- GDR gate from lab/data/path_model.yaml: a GPU-NIC pair is GDR-eligible when its relation is at most PXB.
- Bandwidth: median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on the CPU).
