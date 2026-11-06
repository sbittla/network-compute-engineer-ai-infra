# Marking scheme: 5.2 nvidia-smi topo legend and ordering

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** five meanings and an ordering with one-line justification.

| Criterion | Points |
|---|---|
| PIX (at most one PCIe bridge) and PXB (multiple bridges, no host bridge) defined | 1 |
| PHB (through a PCIe host bridge, typically the CPU) defined | 1 |
| NODE (between host bridges within a NUMA node) and SYS (across the SMP interconnect between NUMA nodes) defined | 1 |
| Ordering best to worst: PIX, PXB, PHB, NODE, SYS | 1 |
| Justification: each step adds bridges, root-complex or inter-socket traversal, lowering P2P bandwidth and raising variance; GDR may be refused beyond the NCCL_NET_GDR_LEVEL gate | 1 |
