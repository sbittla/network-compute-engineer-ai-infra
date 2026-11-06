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
Blocking checkpoint cost δ = 60 s (Section 24.6; Chapter 23 Step 7: the 12.25 s write floor ÷ 50 %
efficiency × 2 for contention + ≈ 11 s metadata and barrier).
τ = √(2 × 60 s × 86,400 s) = √10,368,000 s² ≈ **3,220 s ≈ 54 min**.
- Checkpoint overhead 60 / 3,220 = 1.86 %
- Expected rework (τ/2)/M = 1,610 / 86,400 = 1.86 %
- Restart 900 / 86,400 = 1.04 %
- Total ≈ **4.77 %** of cluster time, versus ≈ 3.16 % at the canonical 48 h (1.32 + 1.32 + 0.52 %); the
  same 4.77 % as Chapter 23's W2, a useful cross-check.
τ shrinks only by √2 (4,554 s → 3,220 s) while the restart term doubles. With the 12.25 s floor the
answer would be τ = 1,455 s and 2.7 %: accept it only when labelled a lower bound.

**Common wrong answers.** Giving the leaf 64 uplinks (the non-blocking leaf has 32); counting idle *flows*
instead of idle uplinks; using node MTBF (768 h) directly in Young's formula instead of job MTBF; using the 12.25 s floor as δ
unlabelled; mixing
hours and seconds. `solve.py` asserts every number above.
