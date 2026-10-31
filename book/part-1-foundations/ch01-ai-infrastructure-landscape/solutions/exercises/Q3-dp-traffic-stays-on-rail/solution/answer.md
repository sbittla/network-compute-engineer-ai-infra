# Q3 — Why W-TRAIN's data-parallel all-reduces never cross a spine

Source: manuscript Section 1.5, "Why rails?", and the ORION topology in `docs/REFERENCE_CLUSTER.md`.

1. A data-parallel group is the set of GPUs that hold the *same* shard of the model in different
   replicas: the same TP rank and the same pipeline stage. With TP = 8 filling a node and one pipeline
   stage per node, the GPUs of one DP group all have the **same local GPU index** (for example, GPU 3) on
   their eight nodes.
2. On an `HX8`, GPU *i* uses NIC *i*, which is cabled to **rail *i***.
3. Rail leaf *r* (`orion-be-leaf-rR`) connects NIC *r* of all 32 nodes. Traffic between same-index GPUs
   therefore enters and leaves the same leaf switch: one hop, no spine.

Consequence: the DP all-reduce (7.66 GB per GPU per step) uses only leaf downlinks. The pipeline sends
also stay on one rail, because stage *s* GPU *i* talks to stage *s* + 1 GPU *i*. Spine capacity is left
for genuinely cross-rail traffic (MoE all-to-all, jobs whose ranks are not rail-aligned). The property
breaks if a launcher maps ranks to GPUs inconsistently across nodes, which is one reason rank-placement
checks belong in job validation.
