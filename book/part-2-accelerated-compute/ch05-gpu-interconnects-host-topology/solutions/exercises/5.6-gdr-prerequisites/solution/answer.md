# 5.6 — GPUDirect RDMA prerequisites and runtime proof (model answer)

Relies on manuscript Section 5.7 (Table 5.3) and Section 5.9 (GDR distance gate).

| # | Prerequisite | How to check |
|---|---|---|
| 1 | Platform P2P support, with the GPU and NIC under one PCIe switch (PIX/PXB) | `nvidia-smi topo -m`, `lspci -tv` |
| 2 | A peer-memory mechanism: `nvidia_peermem` (legacy `nv_peer_mem`) loaded, **or** a verified DMA-BUF path (recent kernel, driver and NIC stack; no `nvidia_peermem` needed) | `lsmod \| grep peermem`; driver/kernel versions for DMA-BUF |
| 3 | A supported combination of GPU driver, CUDA, NCCL, NIC driver (OFED/DOCA) and firmware | Versions vs the vendor support matrix |
| 4 | IOMMU configured per vendor guidance (often `iommu=pt`, passthrough) | `/proc/cmdline` |
| 5 | No ACS redirect on the switch ports above the GPU and NIC | `lspci -vvv` → `ACSCtl: ReqRedir- CmpltRedir-` |
| 6 | Runtime proof that the path is used | see below |

**Runtime evidence.** With `NCCL_DEBUG=INFO`, NCCL's channel lines end in **`/GDRDMA`** when the network
transport reads and writes GPU memory directly (e.g. `... via NET/IB/0/GDRDMA`); without it the channel is
host-staged. Alternatively `ib_write_bw --use_cuda=<gpu>` between two hosts shows GPU-memory RDMA at near line
rate. Also confirm the GPU↔NIC distance is within `NCCL_NET_GDR_LEVEL` (≈ PXB default).

**Not sufficient:** the `GPU Direct RDMA Enabled for GPU … / HCA … (distance X <= Y)` lines. They report only
NCCL's distance check, not that peer memory works. And no NCCL release prints a line of the form
`NET/IB : GPU Direct RDMA Enabled for HCA`; citing it loses marks.

**Common wrong answers.** Treating a missing `nvidia_peermem` as proof GDR is off (DMA-BUF may be in use);
treating a loaded module as proof it is on (ACS, IOMMU or the distance gate can still defeat it).
