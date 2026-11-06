# 13.2 — GPUDirect RDMA prerequisites and proof: worked solution

**The four prerequisites (Section 13.3, Table 13.5) `[VENDOR-SPEC, 2026-10]`:**

1. **A P2P-capable PCIe platform with a supported GPU and NIC.** The GPU and NIC should sit under the
   same PCIe switch (`PIX`) so that the NIC can DMA directly into GPU BAR memory.
2. **A peer-memory mechanism.** Either the `nvidia-peermem` kernel module (`lsmod | grep
   nvidia_peermem`) or the dma-buf path (kernel, driver and `rdma-core` support; perftest
   `--use_cuda_dmabuf` succeeds). Without one, the RDMA stack cannot register GPU memory.
3. **ACS and IOMMU configured for P2P.** PCIe Access Control Services must not redirect peer requests
   to the root complex (`ACSCtl: ReqRedir- CmpltRedir-` on the relevant downstream ports), and the IOMMU
   mode must match the validated platform configuration (for example `iommu=pt` on bare metal).
4. **Compatible versions.** The GPU driver, NIC driver/firmware (MLNX_OFED or inbox `rdma-core`), CUDA,
   NCCL and any NCCL network plugin must all be versions that are supported together.

**Why installing them proves nothing.** Every item above is a *capability*. NCCL silently falls back to
the host-staged path if any link in the chain fails at run time, for example when the module did not
load after a driver update or ACS redirects the traffic. Proof is observing the path in use: NCCL INFO
channel lines that end in `/GDRDMA`, a CUDA-buffer `ib_write_bw --use_cuda=<i>` at about line rate
(≈ 390 Gb/s on 400G), and a measurable difference between GDR on and `NCCL_NET_GDR_LEVEL=LOC` (GDR off).

**Common wrong answer.** Treating the `GPU Direct RDMA Enabled for GPU … / HCA …` INFO line as proof.
That line only reports that the PCIe distance is within `NCCL_NET_GDR_LEVEL`. It does not show that a
peer-memory mechanism works (Section 13.10, row 7).
