# Marking scheme: 5.6 GPUDirect RDMA prerequisites

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** six items; the NCCL log signature.

| Criterion | Points |
|---|---|
| Platform P2P support with GPU and NIC under one PCIe switch | 1 |
| Peer-memory mechanism: nvidia_peermem (legacy nv_peer_mem) or a verified DMA-BUF path | 1 |
| Supported driver/CUDA/NCCL/NIC driver/firmware combination | 1 |
| IOMMU configured per vendor guidance (often iommu=pt) | 1 |
| No ACS redirect on the GPU/NIC switch ports | 1 |
| Runtime proof: NCCL channel lines ending /GDRDMA or ib_write_bw --use_cuda; the distance-check line alone is not sufficient | 1 |
