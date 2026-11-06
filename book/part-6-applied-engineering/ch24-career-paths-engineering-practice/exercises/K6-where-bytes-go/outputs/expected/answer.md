# K6 — Where the bytes go: model answer

Sources: Section 24.6 ("Communication across the fabric", Figure 24.3) and Section 24.7 ("Sizing the Clos",
"What changed versus ORION-256"); topology from `docs/REFERENCE_CLUSTER.md`.

**ORION-256: 1 leaf per rail.** The backend is rail-optimized: NIC *r* of every one of the 32 nodes
attaches to rail leaf *r*, which has 32 host ports and 32 uplinks. W-TRAIN keeps TP = 8 on NVSwitch; its
DP and PP peers are the *same local rank on different nodes*, so with a rail-aligned rank mapping GPU *r*
on node A talks to GPU *r* on node B through NIC *r* → leaf *r* → NIC *r*. Source and destination sit under
the same leaf, so the traffic is switched inside that leaf and never reaches a spine. The spines carry only
cross-rail traffic, which NCCL largely avoids by moving data over NVLink to the GPU whose NIC is on the
destination rail (PXN, Chapter 13).

**1,024 GPUs: 4 leaves per rail.** With 128 nodes, each rail has 128 NICs; a 64-port leaf at 1:1 takes 32,
so each rail needs 128 / 32 = 4 leaves, each serving a 32-node *block* (32 leaves, 16 spines in total). A DP
all-reduce across 128 nodes now has peers under different leaves of the same rail, so traffic between
blocks crosses the spine layer. Placement and ECMP entropy matter again: pack jobs of ≤ 32 nodes inside one
block, and expect hash collisions on the uplinks (Section 24.7).

**Caveat (worth stating).** "Never crosses a spine" holds only if the job's rank-to-GPU mapping is
rail-aligned; a misaligned map or another job's placement puts traffic on spines even at 256 GPUs.

**Common mistakes.** Saying "because the fabric is non-blocking" (that is about capacity, not path);
forgetting the rail-aligned mapping condition (deduct 1).
