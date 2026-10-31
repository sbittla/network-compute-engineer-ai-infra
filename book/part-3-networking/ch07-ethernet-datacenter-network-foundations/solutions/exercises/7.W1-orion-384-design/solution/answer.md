# 7.W1 — Design a rail-optimized ORION-384 backend (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 7.7 ("The folded Clos", "Oversubscription",
"Rail-optimized topology", "Cabling arithmetic") and the lab's Task 1. `solve.py` recomputes every
count and calls the reference `size_two_tier` for (b).

Inputs: 12 racks × 4 HX8 nodes = 48 nodes, 8 × 400G backend NICs per node (one per rail) = 384
endpoints; 64 × 400G ports per switch.

## (a) Rail-optimized, 1:1

| Step | Formula | Result |
|---|---|---|
| Down/up split at 1:1 | 64 × 1/(1 + 1) | 32 down, 32 up |
| NICs per rail | 48 nodes × 1 | 48 |
| Leaves per rail | ⌈48 / 32⌉ | **2** (24 nodes per leaf) |
| Total leaves | 8 rails × 2 | **16** |
| Uplinks | 16 × 32 | 512 |
| Spines | 512 / 64 | **8** |
| Links per leaf-spine pair | 32 / 8 | **4** |
| Spine ports used | 16 leaves × 4 | 64 of 64 ✓ |
| Downlink ports used / total | 384 / (16 × 32 = 512) | **384 / 512 = 75 %** (24 per leaf) |
| Down:up ratio, as configured | 32:32 | **1:1** |
| Down:up ratio, as used | 24:32 | **0.75:1** (under-subscribed) |
| Host cables | 384 | **384** |
| Fabric cables | 512 | **512** |
| Total cables | 384 + 512 | **896** |
| Transceivers (all-optical, both ends) | 2 × 896 | **1,792** (before spares) |

*Accepted alternative (full marks if justified):* trim to 24 uplinks per leaf to be exactly 1:1 on
used ports. That gives 384 uplinks, 6 spines × 4 links (16 × 4 = 64 spine ports), 384 fabric cables,
768 total cables and 1,536 transceivers. The cost is no headroom to grow to 64 nodes per rail.

## (b) The lab's `size_two_tier(384, 64, 64, 1.0)`

Returns: 32 down / 32 up, **12 leaves**, 8 spines, 4 links per pair, 384 fabric cables, 768 total
cables, 1,536 transceivers. (Spines: ⌈384/64⌉ = 6, but 32 uplinks do not divide evenly by 6 or 7, so
the function steps up to 8.)

**Why it differs:** `size_two_tier` is not rail-aware. It packs the 384 endpoints as densely as
possible, ⌈384/32⌉ = 12 leaves. In a rail-optimized fabric every leaf serves exactly one rail, and
each rail has 48 NICs, which is 48/32 = 1.5 leaves' worth. A rail cannot share a leaf with another rail,
so each rail rounds up to 2 leaves: 16 leaves, with 25 % of downlink ports idle. Dense packing would
mix rails on leaves and break same-rail single-hop paths.

## (c) Inference variant at 3:1, rail-optimized

- Split: 64 × 3/4 = **48 down, 16 up**.
- Leaves per rail = ⌈48/48⌉ = 1 → **8 leaves** (one per rail, 48 nodes each, fully used).
- Uplinks = 8 × 16 = 128 → spines = max(2, 128/64) = **2**; links per pair = 16/2 = **8**
  (spine ports 8 × 8 = 64 ✓).
- Cables 384 + 128 = **512**; transceivers **1,024**.
- Cross-leaf capacity per leaf = 16 × 400 Gb/s = **6.4 Tb/s** against downlink capacity
  48 × 400 Gb/s = **19.2 Tb/s** (3:1).

Because each whole rail fits on one leaf, **same-rail traffic is still non-blocking** (single hop,
19.2 Tb/s); only cross-rail traffic sees the 3:1 limit.

## (d) ECMP's importance compared with ORION-256

In ORION-256 each rail is one leaf, so same-rail traffic (most collective traffic) is single-hop and
never consults ECMP. In design (a) **each rail spans two leaves**, so same-rail traffic between nodes on
different leaves of the rail crosses the spines. Those few large, low-entropy RoCE flows are now
hashed across 32 uplinks, and the collision effects of Section 7.6 (≈ 5.25 of 8 links used for
8 flows) land on the main collective path, as in ORION-XL. ECMP quality (entropy, QPs per
connection, adaptive routing) and rank-to-leaf placement become first-order performance factors.

## Common mistakes

- 12 leaves for a "rail-optimized" design (copying (b)).
- Transceivers = cables (forgetting both ends of each optical cable).
- Saying (c) blocks same-rail traffic.
