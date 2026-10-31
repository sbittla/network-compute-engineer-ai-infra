# R4 — What L1 cannot show about GPUDirect RDMA (solution)

**What the L1 bundle shows** `[SIMULATED]`: a statistical association (jobs touching R570 nodes after the
window are +0.90 ± 0.07 s per step slower); a host bounce-copy metric that rises from 0.4 to 9.5 GB/s on
orion-n17..n32 after the window only; illustrative NCCL channel lines `via NET/IB/0` (no `/GDRDMA`) on
orion-n17 versus `via NET/IB/0/GDRDMA` on orion-n09; an empty `lsmod | grep nvidia_peermem` on orion-n17;
and inventory `peermem_module_loaded = no`.

**What it cannot show.**
- How much bandwidth host staging actually costs on ORION's hardware: the bundle's numbers are generated,
  not measured.
- That GDR is really unavailable: per docs/VERIFIED_FACTS.md, DMA-BUF can provide GPUDirect RDMA without
  `nvidia_peermem`, so an absent module is not proof of a host-staged path.
- That the module is the *only* cause: ACS/IOMMU settings on the PCIe switch ports above the GPU and NIC
  can also force staging.

**Evidence that closes the gap.**

| Tier | Evidence | Records |
|---|---|---|
| L2 (one upgraded node, drained) | Confirm `nvidia_peermem` absent *and* DMA-BUF unavailable for that kernel, driver and RDMA stack; check ACS (`lspci -vvv` ACSCtl); `ib_write_bw --use_cuda=<gpu>` per rail with and without the module | driver, CUDA, kernel, RDMA stack versions, `nvidia-smi topo -m` |
| L3 (two reserved nodes, one R550, one R570) | `all_reduce_perf` with and without the module loaded, ≥ 5 runs per arm, busbw median and min/max; NCCL `NCCL_DEBUG=INFO` channel lines showing `via NET/IB/x/GDRDMA` in the working arm only | manifest: NIC firmware, NCCL version, message sizes, warm-up, iterations, run count, concurrent fabric load |

With σ of the busbw known from the runs, state the MDE (Section 22.6.1) beside the measured gap and
label the result `[MEASURED]` with the manifest.

**Common wrong answers.** Treating `lsmod` as sufficient proof; proposing a production driver rollback
(T5, rejected); quoting a busbw number without run count or manifest.

## Hardware run

`python scripts/hw_labs.py run ch22 --device gpu` does not close this gap, and says so. A single laptop GPU has no
RDMA NIC, no `nvidia_peermem` path and no second node, so the L2 precondition and the L3 `/GDRDMA` A/B remain
hardware work. What the run does establish is that the attribution method used for the GDR hypothesis recovers
a *known* host-staging regression. Pageable (host-staged) input copies are injected next to a placebo factor. The
lab's estimator attributes the effect correctly, and the effect is corroborated by an interleaved A/B and a bytes ÷
bandwidth mechanism model. With `--device cpu` the data-path factor becomes a strided host gather.
