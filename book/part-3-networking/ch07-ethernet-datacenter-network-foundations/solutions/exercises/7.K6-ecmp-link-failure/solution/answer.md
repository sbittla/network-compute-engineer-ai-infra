# 7.K6 — ECMP-aware ingress after one link failure (worked solution)

All numbers `[MODELED]` (one direction, uniform demand, unweighted ECMP). Relies on manuscript Section
7.9 ("Link failure") and Table 7.8.

## Raw uplink capacity of orion-be-leaf-r0

Baseline: 4 spines × 8 links × 400 Gb/s = 12,800 Gb/s. After one link fails:

31 × 400 Gb/s = **12,400 Gb/s**, a drop of 400 / 12,800 = **3.1 %**.

## ECMP-aware ingress capacity

Traffic *to* rail 0 comes from the other seven leaves. Each of them still sees `orion-be-spine-1`
advertising rail 0's prefix (spine-1 still has 7 working links to leaf-r0), so each sends **one
quarter** of its rail-0 traffic through spine-1, exactly as before. Spine-1 must deliver that quarter
over 7 links instead of 8. The narrowest bundle sets the limit for every spine's equal share:

ingress = usable spines × min(bundle) × 400 Gb/s = 4 × min(7, 8, 8, 8) × 400 = 4 × 7 × 400 =
**11,200 Gb/s**, a drop of 1,600 / 12,800 = **12.5 %**.

Equivalently, each of spine-1's 7 links runs at 8/7 ≈ 114 % of its fair share. The fabric saturates
when those 7 links fill, while the other 24 links still have 1/8 headroom.

## Mechanism (one sentence)

Unweighted ECMP splits traffic equally across the four spines regardless of how many links each spine
still has to the destination, so the weakened spine's bundle limits the whole leaf.

`solve.py` reproduces both numbers by hand and with the reference `fabric_capacity` (identical:
12,400 and 11,200 Gb/s). Weighted (unequal-cost) multipath that carries link bandwidth in BGP would
recover the difference and bring ingress back to ≈ 12,400 Gb/s.

## Common wrong answers

- 12.4 Tb/s for both: ignores how remote leaves spread traffic.
- 25 %: confuses a link failure with losing the whole spine.
