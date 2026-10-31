# 5.13 — Rank placement and its validation (model answer)

Relies on manuscript Section 5.8 (multi-rail assignment as a joint placement problem), Section 5.5 (NUMA) and
Section 5.7 (GDR proof). Node facts from `orion-n01`'s capture `[SIMULATED]` and docs/REFERENCE_CLUSTER.md.

## Mapping (2 HX8 nodes, TP = 8 inside a node, DP = 2 across nodes)

| Rank | Node | GPU | NIC (rail) | Relation | NUMA / cores |
|---|---|---|---|---|---|
| 0–3 | A | GPU0–3 | `mlx5_0`–`mlx5_3` (rails 0–3) | PIX | NUMA 0, cores 0–55,112–167 |
| 4–7 | A | GPU4–7 | `mlx5_4`–`mlx5_7` (rails 4–7) | PIX | NUMA 1, cores 56–111,168–223 |
| 8–11 | B | GPU0–3 | `mlx5_0`–`mlx5_3` | PIX | NUMA 0 |
| 12–15 | B | GPU4–7 | `mlx5_4`–`mlx5_7` | PIX | NUMA 1 |

TP group = the 8 ranks of one node (NVLink/NVSwitch traffic only). DP pairs are (*r*, *r* + 8): GPU*r* on node A
and GPU*r* on node B communicate over **rail *r***, each through its own PIX NIC, so cross-node traffic stays
on one leaf and never crosses rails.

## Launcher settings

- `CUDA_DEVICE_ORDER=PCI_BUS_ID`; `CUDA_VISIBLE_DEVICES` unset (or `0,…,7`) so local rank *i* = GPU*i* in bus order.
- CPU and memory binding per local rank: ranks 0–3 `numactl --cpunodebind=0 --membind=0`, ranks 4–7 node 1
  (or `--bind-to numa` / Slurm `--cpu-bind`).
- NIC selection: leave it to NCCL's topology detection (it picks the PIX NIC), optionally
  `NCCL_IB_HCA=mlx5_0,…,mlx5_7` to exclude the frontend `mlx5_8`/`mlx5_9` (list order does not set the pairing).

## Validation checklist (pass criteria and evidence)

| Check | Pass criterion | Evidence |
|---|---|---|
| Topology golden | Mapping CSV on both nodes equals the golden file (UUID/BDF/slot/NUMA/rail) | `topo_mapper` diff |
| Rails | LLDP neighbour of `mlx5_r`'s netdev is `orion-be-leaf-r<r>` | `lldpctl` / mapping CSV |
| NICs used | `NET/IB : Using` lists only `mlx5_0`–`mlx5_7` | NCCL log, `NCCL_DEBUG=INFO` |
| GDR | every inter-node channel line ends `/GDRDMA` | NCCL log |
| Pairing | each GPU paired with its PIX NIC | `NCCL_TOPO_DUMP_FILE` |
| Affinity | each rank's threads and pages on its GPU's NUMA node | `taskset -cp`, `numastat -p` |
| Performance | `all_reduce_perf` 2 nodes ≥ fleet floor, 5 launches, median and spread reported | nccl-tests output with manifest |

**Common wrong answers.** Putting TP across nodes; pairing ranks *r* with 15 − *r* (cross-rail traffic);
setting `NCCL_IB_HCA` order and believing it maps GPUs to NICs.
