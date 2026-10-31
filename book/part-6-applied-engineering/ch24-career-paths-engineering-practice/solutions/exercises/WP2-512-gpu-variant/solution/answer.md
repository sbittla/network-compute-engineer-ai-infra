# WP2 — A 512-GPU variant: worked solution

All results `[MODELED]`; reliability inputs are ORION's canonical `[ILLUSTRATIVE]` assumptions
(`docs/REFERENCE_CLUSTER.md`), with node MTBF halved as the prompt states. Method follows the 1,024-GPU
sizing in Section 24.7 and the checkpoint arithmetic in Section 24.6.

**(a) Sizing.** 64 HX8 nodes → 64 NICs per rail. A non-blocking 64-port leaf has 32 down and 32 up.
- Leaves per rail = 64 / 32 = **2**; total leaves = 8 rails × 2 = **16**.
- Leaf uplinks = 16 × 32 = 512 → spines = 512 / 64 = **8**.
- Links per leaf–spine pair = 32 uplinks / 8 spines = **4**.
- Links = 512 host links + 512 fabric links = **1,024** (2,048 ports); 16 + 8 = **24 switches**.
Note what changed versus ORION-256: rail *r* now spans two leaves, so rail-aligned DP traffic between the
two 32-node blocks crosses the spines.

**(b) ECMP collisions.** Each flow hashes to one of 32 uplinks uniformly at random, so
P(uplink idle) = (31/32)^F.
- F = 32: (31/32)^32 = e^(32 × ln 0.96875) = e^(−1.016) = 0.362 → 32 × 0.362 = **11.6 idle uplinks**
  (36 % of uplink capacity unused).
- F = 128 (4 QPs per connection, each a quarter of the size): (31/32)^128 = 0.362⁴ = 0.0172 → 32 × 0.0172
  = **0.55 idle uplinks**.
More, smaller flows spread far better, but the load is still uneven: the mean is 4 flows per uplink and
some uplinks receive 7–8, and a synchronous collective is paced by the most loaded uplink.
(`NCCL_IB_QPS_PER_CONNECTION` exists, default 1, `[VENDOR-SPEC, 2026-10]`.)

**(c) Young's interval at node MTBF 768 h.** Job MTBF M = 768 node-h / 32 nodes = 24 h = 86,400 s.
τ = √(2 × 12.25 s × 86,400 s) = √2,116,800 s² ≈ **1,455 s ≈ 24.3 min**.
- Checkpoint overhead 12.25 / 1,455 = 0.84 %
- Expected rework (τ/2)/M = 727.5 / 86,400 = 0.84 %
- Restart 900 / 86,400 = 1.04 %
- Total ≈ **2.7 %** of cluster time, versus ≈ 1.7 % at the canonical 48 h (0.60 + 0.60 + 0.52 %).
τ shrinks only by √2 (2,058 s → 1,455 s) while the restart term doubles, so restart cost becomes the
largest single term.

**Common wrong answers.** Giving the leaf 64 uplinks (the non-blocking leaf has 32); counting idle *flows*
instead of idle uplinks; using node MTBF (768 h) directly in Young's formula instead of job MTBF; mixing
hours and seconds. `solve.py` asserts every number above.
