# Marking scheme: 13.2 GPUDirect RDMA prerequisites and proof

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** four items and one sentence on proof

| Criterion | Points |
|---|---|
| P2P-capable PCIe platform with supported GPU and NIC | 1 |
| Peer-memory mechanism (nvidia-peermem or dma-buf) | 1 |
| ACS/IOMMU configured so P2P is not redirected through the root complex | 1 |
| Compatible driver/firmware/library versions | 1 |
| Proof requires observing the path in use (NCCL /GDRDMA, CUDA-buffer perftest at line rate, GDR on/off delta) | 1 |
