# 10.K7 — Why a miscabled, error-free uplink is a capacity problem

**Model answer (≤ 120 words).** ORION's backend links are routed: each leaf-to-spine link has its
own /31 with eBGP across it (Chapter 7), assigned to a specific pair of ports. If two jumpers are
swapped at a patch panel, both links train and run error-free, but each leaf port now faces a spine
port configured with a different /31. The eBGP sessions do not establish, so ECMP loses two members:
2 of the leaf's 32 uplinks = **6.25 %** of its uplink capacity, and the remaining paths carry more
load. Nothing is corrupted, so FEC, FCS and DOM stay clean. The check that detects it is **LLDP
neighbour vs cabling schedule** (commissioning gate "Verified", Section 10.11).

**Arithmetic** `[MODELED]`. ORION leaf: 32 uplinks (8 to each of 4 spines). Lost members 2 →
2/32 = 0.0625. If the routing design instead let the sessions come up on the wrong peers, the fabric
would still be asymmetric and harder to debug; either way the schedule is the source of truth.

**Why physical counters miss it.** Physical-layer counters measure whether bits arrive intact, not
*where* the cable goes. A swap is a topology error, so it needs a topology check: LLDP neighbour
names compared to `b_device:b_port` in the cabling schedule (lab ports Ethernet35/36, `MISCABLED`).

**Common wrong answer.** "BER would rise because the link is wrong." It does not; the optics and
fiber are good.
