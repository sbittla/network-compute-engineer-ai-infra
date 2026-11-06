# R3 — What acceptance cannot prove about NCCL hangs

Node acceptance proves that one node is healthy *in isolation*: its GPUs, NVLink, PCIe, NICs at
link level, a pair test per rail against one reference node, and a single-node 8-GPU NCCL run. A
multi-node NCCL hang involves things the suite never exercises:

1. **Multi-node fabric behaviour under load:** switch-side counters, ECN marking and PFC behaviour
   under many-to-one traffic, cross-rail routing (PXN), ECMP hashing/polarization, MTU along the
   whole path. Covered by Chapter 9 (congestion control and lossless fabrics) and Chapter 10
   (physical layer and link commissioning).
2. **Multi-node collectives at scale:** NCCL topology detection across nodes, ring/tree construction
   with many peers, timeouts at 32 nodes rather than 1. Covered by Chapter 12 (multi-node
   `all_reduce_perf`, bus bandwidth) and Chapter 13 (GPUDirect RDMA path validation).
3. **Long-tail intermittent faults:** a link that flaps once per day, a GPU that fails after 30 h,
   which a 24 h burn-in may miss.
4. **Interaction with other tenants' traffic** sharing leaves and spines.

Production telemetry closes the remaining gap: per-rank collective wait, link-flap and retransmit
counters, and step-time stragglers (Chapter 18), plus fault isolation and quarantine (Chapter 19).
The acceptance record should state that it covers node scope only (Section 16.5 notes that
multi-node NCCL runs after a group of nodes is validated).
