# D1 — ORION-384 backend options `[MODELED]`

| Option | Leaves | Leaf ports | Oversub | Spines | Per leaf–spine | Spine ports | Cables | Same-rail via spine |
|---|---|---|---|---|---|---|---|---|
| A | 8 | 64 / 64 | 3:1 | 4 | 4 | 32 / 64 | 512 | no |
| B | 16 | 48 / 64 | 1:1 | 6 | 4 | 64 / 64 | 768 | yes |
| C | 8 | 96 / 128 | 1:1 | 6 | 8 | 64 / 64 | 768 | no |

Racks: ceil(48 / 4) = 12; GPU-node power 48 × 10.2 = 489.6 kW; ASIC 51,200 / 400 = 128 ports at 400G
