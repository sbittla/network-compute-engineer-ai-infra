# K5 — Blast radius of a rack power failure versus a rail-leaf failure

**Source:** manuscript Section 23.5 (Figure 23.3, Table 23.6, "Blast radius is a logical, not a
physical, property"); docs/REFERENCE_CLUSTER.md; key K5. Values `[MODELED]`.

**(a) Rack power failure.** ORION racks hold 4 HX8 nodes (rack-power invariant: 4 × 10.2 kW =
40.8 kW ≤ 45 kW).
- GPUs lost = 4 nodes × 8 GPUs = **32 GPUs** = 32 / 256 = **12.5 %** of capacity.
- Jobs affected: only jobs with at least one rank in that rack. A 256-GPU W-TRAIN job is affected (it
  uses every node); a small job placed in other racks is untouched. Containment: dual A/B feeds and
  spreading DP replicas across racks.

**(b) Rail-leaf failure.** Rail leaf *r* connects NIC *r* of all 32 nodes.
- GPUs lost = **0**: every node and GPU stays up.
- Nodes affected = **32 of 32**: each loses 1 of its 8 backend rails, i.e. 1/8 = 12.5 % of its backend
  bandwidth and the direct path for GPU *r*'s traffic.
- Jobs affected: **every multi-node job** using rail *r*. At the time of writing, plan for this to be
  job-fatal (NCCL timeout or hang), detect it fast and restart (verify current NCCL fault-tolerance
  features against its documentation).

**Why they differ.** The physical hierarchy (facility → rack → node → GPU) groups components that
are *near* each other; a rack failure is local. Rail-optimized wiring instead makes a single switch a
cross-cutting *logical* dependency of every node, so the switch's blast radius is "one rail on every
node in the cluster". Blast radius is a property of dependency, not of location. For contrast, a
spine failure drops each leaf's uplinks from 32 to 24 (32:24 ≈ 1.33:1) yet barely affects
rail-aligned W-TRAIN traffic.

**Common wrong answers.** "A rail leaf has 32 ports so 32 GPUs are lost" (ports are lost, GPUs are
not); treating the leaf failure as harmless because no GPU is down; forgetting that the rack loss is
12.5 % of capacity *and* fatal to the full-size job.
