# 10.M3 — Ports, cables and spares for a 24-node HX8 pod

Inputs (prompt): 24 nodes × 8 backend NICs at 400G, rail-optimized (one leaf per rail), 1:1,
64-port 400G switches, 400G-DR4 on every link; spares 3 % optics, 2 % cables, minimum 2 per type,
one spare switch per model `[ILLUSTRATIVE]` policy. All results `[MODELED]`; method Sections 10.10
and 10.12, same logic as the lab's `estimate_fabric_bom()`.

```text
downlinks max per leaf = 64 × 1/(1+1)            = 32 → 24 nodes fit: 1 leaf per rail
leaves                 = 8 rails × 1              = 8
per leaf               = 24 down, 24 up (1:1)
host links             = 24 nodes × 8 NICs        = 192
fabric links           = 8 leaves × 24 uplinks    = 192
spines                 = ceil(192 / 64)           = 3   (24 mod 3 = 0 → 8 uplinks per leaf per spine)
total links            = 192 + 192                = 384
optics                 = 2 ends × 384             = 768 (400G-DR4)
cables                 = 384 MPO-12 jumpers/trunks
leaf ports used / free = 8 × 48 = 384 / 8 × 16 = 128
spine ports used / free= 3 × 64 = 192 / 0
spares: optics  = max(2, ceil(768 × 0.03)) = ceil(23.04) = 24
        cables  = max(2, ceil(384 × 0.02)) = ceil(7.68)  = 8
        switches= 1 (leaf and spine are the same 64-port model)
```

**Operational spares beyond optics and cables.** One pre-imaged spare switch; field-replaceable PSUs
and fan trays; MPO jumpers in every used length (not just a total count); cleaning supplies
(one-click MPO cleaners, wipes), inspection probe tips; printed labels; spare breakout/patch-panel
cassettes.

**Growth to 32 nodes (≤ 80 words).** Each leaf then has 32 downlinks and needs 32 uplinks, so fabric
links rise to 8 × 32 = 256 and spines to ceil(256/64) = 4, still 8 uplinks per leaf per spine. The
existing 24 uplinks per leaf stay where they are and 8 new uplinks per leaf land on the new spine-4
— no re-cabling if spine port blocks were reserved — but every leaf port (32 + 32 = 64) is then used:
no free ports for growth or for maintenance.

**Common mistakes.** Counting optics = links (forgetting two ends); giving spines free ports by
rounding up to 4 at 24 nodes; spares below the minimum of 2.
