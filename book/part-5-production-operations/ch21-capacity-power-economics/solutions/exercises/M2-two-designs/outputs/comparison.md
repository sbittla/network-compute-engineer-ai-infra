# M2 - two designs `[MODELED]`

| Metric | A | B |
|---|---|---|
| nodes_power_fit | 87 | 62 |
| nodes_cooling_fit | None | 87 |
| nodes | 87 | 62 |
| gpus | 696 | 496 |
| useful_units | 442.3 | 644.9 |
| tco_musd | 16.67 | 20.565 |
| per_musd | 26.53 | 31.36 |
| per_facility_mw | 395.6 | 645.0 |
| usd_per_gpu_year | 23950 | 41463 |
| usd_per_useful_unit_year | 37687 | 31888 |
| power_share | 0.053 | 0.038 |

Break-even: 2.2 × 26.53 / 31.36 = **1.86×**

| B per-GPU throughput | B per $M | A per $M | Winner |
|---|---|---|---|
| 1.6 | 22.81 | 26.53 | A |
| 1.8 | 25.66 | 26.53 | A |
| 1.86 | 26.51 | 26.53 | A |
| 2.0 | 28.51 | 26.53 | B |
| 2.2 | 31.36 | 26.53 | B |
| 2.4 | 34.21 | 26.53 | B |

| $/kWh | A per $M | B per $M | B / A |
|---|---|---|---|
| 0.06 | 27.01 | 31.77 | 1.176 |
| 0.09 | 26.53 | 31.36 | 1.182 |
| 0.12 | 26.08 | 30.96 | 1.187 |
| 0.15 | 25.63 | 30.58 | 1.193 |
| 0.2 | 24.92 | 29.96 | 1.202 |
