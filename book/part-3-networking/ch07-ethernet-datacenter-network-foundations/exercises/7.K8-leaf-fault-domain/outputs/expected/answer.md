# 7.K8 — Why one leaf is a cluster-wide fault domain (worked solution)

Relies on manuscript Section 7.7 ("Rail-optimized topology") and Section 7.9 ("Leaf failure").

## The rail-mapping argument

ORION-256 is **rail-optimized**: `orion-be-leaf-r<r>` connects NIC *r* (`mlx5_r`) of **every** node,
`orion-n01` through `orion-n32`. Rail *r* is one leaf wide. When `orion-be-leaf-r3` fails, the
spines withdraw `10.100.3.0/24` within a second, and the fabric is "converged". But **all 32 nodes
lose one of their eight backend NICs at the same moment**, and nothing reroutes: no other leaf serves
rail 3.

## Effect on a 256-GPU job

A 256-GPU W-TRAIN job uses every node and every rail. NCCL builds its rings and trees per rail. GPU 3
on each node talks through NIC 3, and same-rail traffic is single-hop through leaf-r3. Every
communicator channel that uses rail 3 loses its transport at once. Its QPs hit retry-exceeded errors,
and the collective errors out or hangs until the NCCL or framework timeout. The job then **fails and
restarts from its last checkpoint** (Chapter 19), usually after the leaf is replaced or the job is
reconfigured to exclude the rail. The cost is the restart plus the lost work since the last checkpoint
for the whole cluster, not "1/8 of the bandwidth". A synchronous job cannot run on 7/8 of its GPUs'
paths.

## Contrast: a top-of-rack leaf

In a conventional top-of-rack design, a leaf connects all NICs of the servers *in its rack*. When it
fails, those servers (for example one rack of 4 nodes) go offline, and every other node keeps all its
NICs. A scheduler can drain one rack and keep running elsewhere. The failure domain is one rack;
in ORION it is one rail of the entire cluster.

## Common wrong answers

- "Only 1/8 of bandwidth is lost": ignores that synchronous collectives fail as a whole.
- Assuming traffic fails over to another rail: routing cannot help, because rail 3's NICs
  connect only to leaf-r3. NCCL does not move a running communicator to other NICs; recovery means
  a restart.
