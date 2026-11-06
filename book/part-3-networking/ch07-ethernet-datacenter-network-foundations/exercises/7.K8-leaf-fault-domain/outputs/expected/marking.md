# Marking scheme: 7.K8 Why one leaf is a cluster-wide fault domain

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** the rail mapping argument and its effect on a 256-GPU job.

| Criterion | Points |
|---|---|
| Rail mapping: orion-be-leaf-r<r> connects NIC r of every node, so a leaf loss removes one NIC from all 32 nodes | 1 |
| Job effect: every communicator using rail r breaks; the 256-GPU job fails and restarts (not just −1/8 bandwidth) | 1 |
| Contrast with a top-of-rack leaf, whose failure removes only its own rack's servers | 1 |
