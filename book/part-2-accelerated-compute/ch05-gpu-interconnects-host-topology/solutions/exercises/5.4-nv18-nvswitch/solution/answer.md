# 5.4 — Why every GPU pair shows NV18 (model answer)

Relies on manuscript Section 5.3 (NVLink and NVSwitch) and Section 5.6.1. Values `[VENDOR-SPEC, 2026-10]`.

**Arithmetic.** Each H100-class GPU has 18 fourth-generation NVLink links at 25 GB/s per direction each:
18 × 25 GB/s = **450 GB/s per direction** (900 GB/s bidirectional). On an HGX board the 18 links are spread
across the NVSwitch chips (4 on H100 HGX), and every GPU connects to every switch. Any GPU pair therefore
talks through one switch hop using all 18 of its links' worth of bandwidth: `nvidia-smi topo -m` reports the
bonded set as `NV18` in every GPU–GPU cell. The matrix is uniform because the fabric is non-blocking, not
because the GPUs are directly wired to each other.

**What it says about GPU↔NIC locality: nothing.** NICs are not on NVLink; GPU↔NIC traffic (GPUDirect RDMA) is
purely a PCIe question, answered by the GPU–NIC cells (PIX…SYS) of the same matrix. A uniform `NV18` block
coexists with a misplaced NIC two sockets away. The one indirect link is PXN (NCCL can forward data over
NVLink to a peer GPU that is close to the right NIC), which uses NVLink capacity but does not change the PCIe
relation.

**Common wrong answers.** Reading `NV18` as "18 GB/s" or "18 hops"; concluding that because all GPUs are
equally close, any GPU can use any NIC equally well.
