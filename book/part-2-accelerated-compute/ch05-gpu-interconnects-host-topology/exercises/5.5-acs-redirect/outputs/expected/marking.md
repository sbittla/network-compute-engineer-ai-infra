# Marking scheme: 5.5 ACS Request Redirect and GPUDirect RDMA

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** mechanism, isolation purpose, P2P cost.

| Criterion | Points |
|---|---|
| Mechanism: ACS Request/Completion Redirect forces peer TLPs from a switch downstream port up to the root complex for IOMMU validation | 1 |
| Isolation purpose: stops a passed-through device in one VM from DMAing into another guest's device | 1 |
| Bare-metal cost: one-hop in-switch GPU-NIC P2P becomes a root-complex round trip (lower bandwidth, more variance, or broken P2P) | 1 |
