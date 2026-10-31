# 7.W2 — Failure capacity of ORION-384 (worked solution)

All numbers `[MODELED]` (one direction, uniform demand, unweighted ECMP). Relies on manuscript Section
7.9 (formulas: ECMP-aware ingress = usable spines × narrowest bundle × 400 Gb/s; bisection = worst
half/half leaf split), Section 7.6 (collision probabilities) and Table 7.8. `solve.py` runs the
reference `fabric_capacity` on the 7.W1(a) design (16 leaves × 8 spines × 4 links, 400 Gb/s) and
checks it against the hand arithmetic below.

## (a) Results table

| Scenario | Raw uplink (affected leaf) | ECMP-aware ingress (affected leaf) | Spine-layer bisection |
|---|---|---|---|
| Baseline | 32 × 0.4 = **12.8 Tb/s** | 8 × 4 × 0.4 = **12.8 Tb/s** | 8 spines × min(8 × 4, 8 × 4) = 256 links × 0.4 = **102.4 Tb/s** |
| One link (leaf L ↔ spine S) down | 31 × 0.4 = **12.4 Tb/s** | 8 × min(3, 4, …, 4) × 0.4 = 8 × 3 × 0.4 = **9.6 Tb/s** | (31 + 7 × 32) × 0.4 = 255 × 0.4 = **102.0 Tb/s** |
| One spine down | 28 × 0.4 = **11.2 Tb/s** | 7 × 4 × 0.4 = **11.2 Tb/s** | 7 × 32 × 0.4 = **89.6 Tb/s** |

Bisection detail for the link-down row: the worst split puts leaf L in half A. Spine S then has
7 × 4 + 3 = 31 links into half A and 32 into half B, so it carries min(31, 32) = 31 links across the
cut. The other 7 spines carry 32 each. The bisection barely moves (−0.4 %) because one link is 1/256
of the cut, while the per-leaf ingress falls by a quarter.

## (b) Comparison with ORION-256 (Table 7.8)

ORION-256 has 8 links per leaf-spine pair: one failed link costs 4 × 7 × 0.4 = 11.2 of 12.8 Tb/s,
**12.5 %** of ECMP-aware ingress. ORION-384 has only 4 links per pair: one failed link removes a
quarter of that spine's bundle, while unweighted ECMP still sends 1/8 of the leaf's traffic to that
spine. The leaf saturates at 8 × 3 × 0.4 = 9.6 Tb/s, a **25 %** penalty, twice as large. The trade
runs the other way for spines: losing one of 8 spines costs **12.5 %** here, against **25 %** for one
of 4 spines in ORION-256. More, narrower spine bundles give a smaller spine fault domain but a larger
per-link penalty. Weighted ECMP (link-bandwidth/UCMP) would cut the link penalty back to the raw
3.1 %.

## (c) Four 400 Gb/s flows on 4 links between one leaf and one spine

Each flow independently and uniformly picks one of 4 links.

- P(no collision) = (ways to assign 4 flows to 4 distinct links) / (all assignments)
  = 4! / 4⁴ = 24 / 256 = **9.4 %**.
- Expected number of links used = Σ over links of P(link used) = 4 × (1 − (3/4)⁴)
  = 4 × (1 − 81/256) = 4 × 0.6836 = **2.73 links**.

`solve.py` confirms both by enumerating all 256 outcomes. In 90.6 % of cases at least two flows share
a link and run at ≤ 200 Gb/s each; on average only 2.73 × 400 = 1.09 Tb/s of the bundle's 1.6 Tb/s
can be used by these four flows.

## Comparison summary (3–5 sentences)

ORION-384's 8-spine, 4-link design halves the spine fault domain (−12.5 % instead of −25 % per spine)
but doubles the cost of a single optic or link failure (−25 % instead of −12.5 % of ingress to the
affected leaf). Because link failures are far more frequent than spine failures, the new design's
common-case degradation is worse unless weighted ECMP is enabled. Narrower bundles also make hash
collisions worse: with 4 flows on 4 links, all four find their own link only 9.4 % of the time.
Since same-rail traffic crosses the spines in this design (7.W1(d)), these effects hit the main
collective path.

## Common mistakes

- Using raw uplink (12.4 Tb/s) as the link-down capacity.
- Leaving out the link-down bisection without explaining that it barely changes (accepted only with
  the explanation).
- P(no collision) = 1/4! or (3/4)³: confusing ordered and unordered assignments.
