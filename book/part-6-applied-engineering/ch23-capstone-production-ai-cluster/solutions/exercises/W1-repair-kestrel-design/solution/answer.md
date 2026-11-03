# W1 — Repairing the Kestrel design

**Source:** manuscript Section 23.4 (Table 23.5 invariants 1, 2, 4–9, 11); docs/REFERENCE_CLUSTER.md
(node power 10.2 kW max = 4.6 kW base + 8 × 700 W); key W1. All values `[MODELED]` from the stated
inputs.

## 1. GPU accounting and parallelism

- Invariant 1: (nodes − declared spares) × GPUs/node = training GPUs. The bundle has 34 × 8 = 272 ≠ 256
  with `spares: 0`. Declare `spares: 2`: (34 − 2) × 8 = **256 GPUs** ✓.
- Invariant 2: TP × PP × DP = 8 × 4 × 16 = 512 ≠ 256. Correct DP = 256 / (8 × 4) = **8**.

## 2. Leaf port arithmetic and a consistent configuration

- As drawn: 34 downlinks + 32 uplinks = 66 > 64 radix ✗ (PORT-001).
- Keeping both spares cabled needs 34 downlinks, so uplinks ≤ 64 − 34 = 30. An equal number to each of
  4 spines needs a multiple of 4, so **28 uplinks = 7 per spine**. Ports used 34 + 28 = 62 (2 free).
- Oversubscription (same-speed ports): all 34 nodes active 34:28 = **1.21:1**; spares idle 32:28 =
  **1.14:1**. The "1:1" claim is false under any 34-downlink design (PORT-002). For rail-aligned
  W-TRAIN traffic, which stays inside the leaf, the ratio has negligible effect; it matters for
  cross-rail traffic.
- Spine ports: 8 leaves × 7 = **56 of 64**.
- Backend cables: 8 × (34 + 28) = **496** (8 × 34 = 272 host–leaf + 8 × 28 = 224 leaf–spine). The bundle's
  512 is wrong under every configuration considered; the drawn 34 + 32 would need 8 × 66 = 528
  (CABLE-001).
- Also acceptable: do not cable the spares (32 + 32 = 64, 1:1, 512 cables) and accept recabling at swap
  time, or use a larger-radix leaf. Whatever is chosen, the claimed ratio must match the arithmetic.

## 3. Racks at the 45 kW planned budget

- 45 kW = 50 kW rack limit × 0.9 transient margin (Chapter 21; A-09). Use it as is; do not apply
  the margin again.

- Nodes per rack = floor(45 / 10.2) = floor(4.41) = **4**. Racks = ceil(34 / 4) = ceil(8.5) = **9**.
- With only 8 racks: (i) keep the 2 spares outside the GPU row or unracked; (ii) obtain a larger budget
  from Facilities; (iii) cap node power at 45 / 5 = **9.0 kW** in the two 5-node racks (not 50 / 5 = 10.0 kW, which ignores the margin). With the node
  power model 4.6 kW + 8·P ≤ 9.0 kW, the GPU cap is P ≤ (9.0 − 4.6) / 8 = **550 W** versus 700 W, so
  throughput (A-04 MFU) must be re-measured, the cap must be enforced in firmware, not by convention,
  and the change touches A-03/A-04 and needs an ADR.

**Common wrong answers.** Using sustained power (8.5 kW → 5 nodes per rack, 51 kW at maximum);
choosing 30 uplinks (not divisible by 4 spines); forgetting the cable count or leaving it at 512;
fixing DP but not declaring spares (or vice versa).
