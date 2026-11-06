# Marking scheme: 5.13 Rank placement and its validation

Type outline-mandated · kind written · tier L1 · 10 points

**Evidence required:** mapping table, launcher settings, a validation checklist with pass criteria and the commands/log lines used.

| Criterion | Points |
|---|---|
| Mapping table: ranks 0-7 node A GPU0-7, ranks 8-15 node B; TP group per node over NVLink; DP pairs (r, r+8) over rail r via mlx5_r (PIX) | 3 |
| Launcher settings: CUDA_DEVICE_ORDER=PCI_BUS_ID, CPU and memory binding per NUMA node, NIC selection (NCCL topology detection or NCCL_IB_HCA excluding frontend NICs) | 3 |
| Validation checklist with pass criteria and evidence: mapping CSV golden, NCCL NET/IB Using and /GDRDMA lines, topology dump, taskset/numastat, nccl-tests ≥ fleet floor over 5 runs | 4 |
