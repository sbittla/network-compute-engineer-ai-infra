# 7.R2 — Better and worse than the ECMP-aware number (model answer)

Relies on manuscript Section 7.6 (per-flow hashing, low entropy, polarization) and Section 7.9 (the
capacity model behind Table 7.8, `[MODELED]`: unweighted ECMP, uniform demand).

The ECMP-aware ingress figure (for example 11.2 Tb/s for leaf-r0 with one spine-1 link down) assumes
every remote leaf sends equal shares to every spine, and that traffic fills links perfectly up to the
narrowest bundle.

## Two ways a real fabric can do *better*

1. **Weighted ECMP / UCMP or adaptive routing.** If spines advertise link bandwidth (BGP link-bandwidth
   community) or the ASIC steers flowlets by queue occupancy, remote leaves send less to the weakened
   spine. Capacity approaches the raw uplink number (12.4 Tb/s) instead of 11.2 Tb/s.
2. **Non-uniform demand.** Real traffic is not "every leaf sends to leaf-r0 at once". ORION's backend
   load is mostly same-rail, single-hop, and never touches a spine. A weakened leaf may never need its
   full cross-rail ingress, so the job sees no slowdown.

## Two ways it can do *worse*

1. **Hash collisions and polarization.** With few large flows, ECMP is a lottery: 8 flows on 8 links
   use only ≈ 5.25 links on average `[MODELED]`, and the most-loaded link carries ≥ 2 flows 99.8 % of
   the time. Correlated hashing (7.K5) can leave 6 of 8 spine links idle. Delivered capacity can fall
   well below the formula with every link healthy.
2. **Congestion dynamics.** Incast at the destination, PFC pauses that spread congestion upstream (head-
   of-line blocking of unrelated flows), and DCQCN rate cuts all keep goodput below link capacity.
   Retransmissions after loss (go-back-N) waste capacity on top (Chapter 9).

(Other acceptable "worse" answers: resilient-hashing churn after a failure, reordering-driven
retransmissions, a gray link that is up but dropping.)
