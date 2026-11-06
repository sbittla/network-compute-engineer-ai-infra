# O1 — corroboration and interactions `[SIMULATED]`

| Cause | Measurement | Value |
|---|---|---|
| TP split | backend tx per node, packed → split (after) | 6.06 → 95.93 GB/s |
| TP split | SM active, packed → split (after) | 0.57 → 0.40 |
| Capacity tier | data-wait delta, TP-packed (after) | +1.46 s |
| Capacity tier | CPU iowait hot → capacity (after) | 1.52 → 6.03 % |
| Capacity tier | per-job p99 (p50) hot → capacity | 18.8 → 35.0 s (18.17 → 18.24 s) |
| R570 / GDR | host bounce copy on R570 nodes, before → after | 0.40 → 9.50 GB/s |
| ECC alert | orion-n13 SBE; temperature | 0.7 → 152; 67.4 → 68.1 °C |

tp_x_storage -1.30 ± 0.15 s (8.6 SE): keep.
tp_x_driver +0.03 ± 0.13 s (0.3 SE): drop.
