# 5.15 — Prove GPUDirect RDMA on a real host (marking guide and reference procedure)

Tier L2: there is no single numeric answer; marks go to complete raw evidence and a verdict consistent with
it. Relies on manuscript Section 5.7 (Table 5.3).

| Item | Command (run on the host) | What a pass looks like |
|---|---|---|
| 1 Topology | `nvidia-smi topo -m`; `lspci -tv` | the chosen GPU and NIC are PIX (or PXB) |
| 2 Peer memory | `lsmod \| grep -E 'nvidia_peermem\|nv_peer_mem'`; `uname -r`; `nvidia-smi` driver version | module loaded, **or** kernel + driver + NIC stack recent enough for DMA-BUF |
| 3 Versions | `nvidia-smi`, `nvcc --version`, NCCL version (log header), `ofed_info -s` or DOCA version, `ibv_devinfo` firmware | combination in the vendor support matrix |
| 4 IOMMU | `cat /proc/cmdline`; `dmesg \| grep -i iommu` | passthrough (`iommu=pt`) or the vendor-recommended mode |
| 5 ACS | `sudo lspci -vvv -s <switch port>` for the ports above GPU and NIC | `ACSCtl: … ReqRedir- CmpltRedir-` |
| 6 Runtime | `NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,NET` all-reduce across two hosts; or `ib_write_bw --use_cuda=<gpu> -d mlx5_0` | channel lines `… via NET/IB/0/GDRDMA`; or GPU-memory RDMA near line rate |

**Verdict examples.**

- "`nvidia_peermem` absent, but NCCL channels show `/GDRDMA` → DMA-BUF path in use; consistent with driver
  and kernel versions." Correct.
- "Module loaded, but ACS `ReqRedir+` and channels without `/GDRDMA` → GDR not in use; fix the BIOS/ACS
  setting." Correct.
- "`GPU Direct RDMA Enabled for GPU … (distance 1 <= 3)` printed → GDR works." **Deduct**: that is only NCCL's
  distance check.

**Marking.** 6 points for raw output of all six items, 2 for the runtime test, 2 for a consistent verdict.
Outputs must be raw (not paraphrased), with host name, date and versions.
