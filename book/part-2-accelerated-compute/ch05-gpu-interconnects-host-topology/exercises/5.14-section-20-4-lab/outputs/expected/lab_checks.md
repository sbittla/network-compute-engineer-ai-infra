# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `parse_topo_matrix` | PASS parse_topo_matrix — 324 relations, NIC legend and CPU/NUMA affinity parsed |
| `parse_lstopo` | PASS parse_lstopo — 8 GPUs, 10 NICs, ancestors and names recovered |
| `build_mapping` | PASS build_mapping — mapping columns complete; n17 GPU3 and n23 GPU4/5 misalignment captured |
| `make_rank_map` | PASS make_rank_map — aligned, nearest, cross-socket and PXN policies produce the expected NIC choices |
| `model_allreduce` | PASS model_allreduce — deterministic case: 14.647 ms, busbw 142.0 GB/s; modifiers applied in order |
| `scenarios` | PASS scenarios — S1 352 GB/s, S2 41, S3 177, S4 139, S5 177, S4@SYS 186 [MODELED] |
