# 5.2 — nvidia-smi topo legend and ordering (model answer)

Relies on manuscript Section 5.6.1 (`nvidia-smi topo -m`) and Section 5.4 (GPU↔NIC data paths). Legend text
as printed in the Lab 5 capture `[SIMULATED]`.

| Code | Legend meaning | What the traffic crosses |
|---|---|---|
| PIX | Connection traversing at most a single PCIe bridge | Both devices on ports of the same PCIe switch |
| PXB | Connection traversing multiple PCIe bridges (without traversing the PCIe Host Bridge) | Several switch levels, still below the CPU |
| PHB | Connection traversing PCIe as well as a PCIe Host Bridge (typically the CPU) | Up to the root complex and back down |
| NODE | Connection traversing PCIe as well as the interconnect between PCIe Host Bridges within a NUMA node | Between two root complexes of one socket |
| SYS | Connection traversing PCIe as well as the SMP interconnect between NUMA nodes (e.g. QPI/UPI) | Across sockets |

**Ordering for GPU↔NIC RDMA, best → worst: PIX, PXB, PHB, NODE, SYS.** Each step adds bridges, then the root
complex, then the on-die fabric between host bridges, then the inter-socket link: more hops, shared links and
contention with host traffic, lower achievable P2P bandwidth and higher variance. NCCL also gates GPUDirect
RDMA by distance (`NCCL_NET_GDR_LEVEL`, ≈ PXB by default in recent releases, verify per release): a NIC at
PHB, NODE or SYS distance is host-staged by default even when peer memory works. Table 5.4 encodes the same
ordering as model parameters (48, 45, 40, 36, 24 GB/s `[ILLUSTRATIVE]`).

**Common wrong answers.** Ranking PHB above PXB "because the CPU is fast"; treating `NV#` as a PCIe class;
believing PIX means "same device".
