# M2 - two designs `[MODELED]`

| Metric | A | B |
|---|---|---|
| nodes_power_fit | 87 | 62 |
| nodes_cooling_fit | None | 87 |
| nodes | 87 | 62 |
| gpus | 696 | 496 |
| useful_units | 442.3 | 644.9 |
| tco_musd | 16.572 | 20.478 |
| per_musd | 26.69 | 31.49 |
| per_facility_mw | 395.6 | 645.0 |
| usd_per_gpu_year | 23810 | 41286 |
| usd_per_useful_unit_year | 37465 | 31752 |
| power_share | 0.047 | 0.034 |

Break-even: 2.2 × 26.69 / 31.49 = **1.86×**

If B's network does not scale with compute: step at 2:1 = 0.611 of A's -> 1.64× per GPU -> **25.2 per $M** (below A's 26.69)

| B per-GPU throughput | B per $M | A per $M | Winner |
|---|---|---|---|
| 1.6 | 22.9 | 26.69 | A |
| 1.8 | 25.77 | 26.69 | A |
| 1.86 | 26.63 | 26.69 | A |
| 2.0 | 28.63 | 26.69 | B |
| 2.2 | 31.49 | 26.69 | B |
| 2.4 | 34.36 | 26.69 | B |

| $/kWh | A per $M | B per $M | B / A |
|---|---|---|---|
| 0.06 | 27.01 | 31.77 | 1.176 |
| 0.08 | 26.69 | 31.49 | 1.18 |
| 0.12 | 26.08 | 30.96 | 1.187 |
| 0.15 | 25.63 | 30.58 | 1.193 |
| 0.2 | 24.92 | 29.96 | 1.202 |
