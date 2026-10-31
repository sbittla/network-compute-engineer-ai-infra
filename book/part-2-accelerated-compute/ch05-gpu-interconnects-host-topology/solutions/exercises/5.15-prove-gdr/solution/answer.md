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

## Hardware run (L2 harness)

The course harness (`python scripts/hw_labs.py run ch05 --device gpu`) builds the Table 5.3 evidence
table from what the host actually shows. It captures raw `topo -m` parsed with the lab's
`parse_topo_matrix`, the peer-memory modules from `/proc/modules`, driver/CUDA versions and
`/proc/cmdline`, notes that ACS is not readable without root on bare metal, and runs a PCI/sysfs scan for
RDMA devices. It then applies the lab's GDR distance gate. On the reference laptop (one GPU, no NIC,
WSL2) the only correct verdict is **GDR impossible: there is no NIC to pair with the GPU**. Items 1-2
fail, item 3 is incomplete, items 4-5 cannot be judged inside a WSL2 guest, and item 6 is not runnable. A
harness report earns the raw-evidence marks for the items it shows and the verdict marks if the verdict
matches that evidence. It cannot earn the runtime-test marks, which need a host with an RDMA NIC and a
peer. CPU fallback: the same probes without a GPU; the gate fails for want of both GPU and NIC.
