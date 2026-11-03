# 2.10 — Growing ORION to 512 GPUs: model decision record

Method: manuscript Sections 2.4 (fabric counting), 2.5 (rack budget), 2.7 (cooling) and 2.10 (envelope),
plus the DLC node of Exercise 2.6. Inputs `[ILLUSTRATIVE]`; results `[MODELED]`, reproduced by `solve.py`.
Network power for the doubled fabric is assumed to double (32 → 64 kW) `[ILLUSTRATIVE]`.

**Constraints:** 32 more nodes (64 in total); at most 6 more racks (13 + 6 = 19 positions); ≤ 800 kW of IT
for the row; one more 300 kW CDU (600 kW in total); no structural work (1,200 kg/m²).

## Options considered

| Option | GPU racks | Positions needed | IT max | Liquid / CDU | Floor | Verdict |
|---|---:|---:|---:|---|---|---|
| A: air-cooled HX8, 4 per rack | 16 | 21 | ≈ 742 kW | 492 kW / 82 % | 1,139 ✓ | ✗ rack count (21 > 19); tight on power |
| B: DLC HX8, 5 per rack | 13 | 18 | ≈ 673 kW | 470 kW / 78 % | 1,326 ✗ | ✗ floor (Exercise 2.6) |
| C: DLC HX8, 4 per rack, support racks consolidated | 16 | 19 | ≈ 674 kW | 470 kW / 78.4 % | 1,139 ✓ | ✓ chosen, no CDU N+1 |

Criteria: fits every hard limit; risk (margin left on power, cooling, floor); feed-loss behaviour;
operating cost.

## Decision: Option C

64 DLC nodes in 16 GPU racks of 4. Two rack positions are reclaimed by moving management into the network
racks and consolidating storage into one rack: 16 GPU + 2 network + 1 storage = **19 racks = 13 + 6**.

```text
GPU rack     = 4 × 9.138 + 0.2 = 36.75 kW; × 1.10 = 40.4 kW per side ≤ 65.55 ✓
GPU racks    = 16 × 36.75       = 588 kW
IT maximum   = 588 + 64 (network) + 18 (storage) + 4 (management) = 674 kW ≤ 800 ✓
liquid       = 16 × 0.80 × 36.75 = 470.4 kW on 2 × 300 kW CDUs = 78.4 %  ✓ capacity, ✗ N+1
residual air = 0.20 × 36.75     = 7.35 kW per rack ≤ 12 kW ✓
floor        = (4 × 135 + 280) / 0.72 = 1,139 kg/m² ≤ 1,200 ✓
```

**Fabric change** (the current spines have no free ports): 64 nodes × 8 rails = 512 host links. A 64-port
leaf at 1:1 serves 32 nodes, so **16 rail leaves** (2 per rail), each with 32 uplinks: 512 uplinks.
**8 spines** of 64 ports, each leaf sending 4 uplinks to each spine. That is 24 backend switches, 1,024
backend links, 2,048 link ends (transceivers if all optical), and 102.4 Tb/s bisection per direction. The
existing 4 spines are re-cabled into the new 8-spine layer during a planned outage.

**SPOF removal (from the lab):** re-cord both frontend leaves across A and B; a second metadata server;
a backup Slurm controller; a second OOB aggregation path; and N+1 cooling, which needs a third CDU.

**What we gave up:** CDU redundancy (one CDU failure removes half the cooling: an outage of 8 racks), the
two support-rack positions (denser network racks; check their power), and the 742 kW air option's
simpler service model.

**Evidence before committing:** the DLC node's measured maximum at the BMC under burn-in (the 9.14 kW is
modeled); the CDU vendor's curve at 235 kW per unit; network-rack power for 24 switches; Facilities'
confirmation of the 800 kW row allocation; a third-CDU timeline.

**Common wrong answers:** forcing 5 DLC nodes per rack despite the floor rating; reusing ORION's 4 spines
without free ports; claiming N+1 cooling with two loaded CDUs.
