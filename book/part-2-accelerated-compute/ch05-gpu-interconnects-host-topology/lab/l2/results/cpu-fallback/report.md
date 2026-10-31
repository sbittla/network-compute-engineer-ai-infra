# Lab 5 L2: real host topology capture, PCIe link measurement and the GDR gate

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:37:50Z.

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

## Table 5.3 GPUDirect RDMA evidence on this host

| Item | Evidence (captured now) | Verdict |
|---|---|---|
| 1 Topology | topo -m devices: no nvidia-smi; PCI network controllers: 0; /sys/class/infiniband: absent | FAIL: no NIC to pair with the GPU |
| 2 Peer memory | peer-memory modules: none (36 modules visible); kernel 6.18.54.1-microsoft-standard-WSL2 | FAIL: no nvidia_peermem, and DMA-BUF needs an RDMA NIC driver |
| 3 Versions | driver n/a; CUDA runtime 12.4; ofed_info absent; ibv_devinfo absent | INCOMPLETE: no NIC stack or firmware to match against the support matrix |
| 4 IOMMU | /proc/cmdline: initrd=\initrd.img WSL_ROOT_INIT=1 panic=-1 nr_cpus=24 hv_utils.timesync_implicit=1 printk.devkmsg=on page_reporting.page_reporting_order=5 hv_storvsc.storvsc_m | n/a: WSL2 guest kernel; the IOMMU belongs to the Windows host |
| 5 ACS | no lspci and no root; the guest PCI view is 4 paravirtual functions (2 Microsoft GPU-PV render devices, class 0x0302) | NOT READABLE here: needs root lspci -vvv on bare metal |
| 6 Runtime | NCCL /GDRDMA channel lines or ib_write_bw --use_cuda need an RDMA NIC and a peer | NOT RUNNABLE: no RDMA NIC, no second host |

**GDR verdict: impossible on this host.** RDMA devices in /sys/class/infiniband: 0; PCI network controllers: 0; GPU-NIC pairs within the PXB gate: 0. With no NIC there is no GPU-NIC path to classify, so NCCL would fall back to host-staged or socket transport for any inter-node traffic.

## Host memory copy

Host copy bandwidth: **26.36 GB/s** `[MEASURED]` (median of 10).

_CPU fallback: no GPU is visible, so no topo -m, link state or H2D bandwidth was measured; the GPU-only invariants were skipped. The GDR gate fails for want of both GPU and NIC._

## Not runnable on this host

- **Exercise 5.15 runtime proof: NCCL NET/IB/.../GDRDMA channel lines or ib_write_bw --use_cuda**: needs an RDMA NIC (ConnectX-class or similar) on the GPU's PCIe switch, nvidia_peermem or DMA-BUF support, a second host on an RDMA fabric.
- **L2 capture script (capture/capture_topology.sh) with lspci -vvv ACS/LnkSta, lstopo, ibdev2netdev, LLDP**: needs root on bare metal (not a WSL2 guest), lspci, lstopo, rdma-core, an RDMA NIC.
- **NVLink / fabric manager status (nvidia-smi nvlink --status)**: needs an NVLink-equipped multi-GPU host.

- Every row of the Table 5.3 checklist is built from a command or sysfs file read during this run; the raw topo -m output and the PCI scan are in results.json.
- GDR gate from lab/data/path_model.yaml: a GPU-NIC pair is GDR-eligible when its relation is at most PXB.
- Bandwidth: median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on the CPU).
