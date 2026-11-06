# W2 - capping in a tighter hall `[MODELED]`

Rack budget = 30.0 × (1 - 0.1) = 27.0 kW; node peak = 4.6 + 8 × cap

| Cap (W) | Node peak (kW) | Nodes/rack | Deployable, 16 racks | Throughput, 16 racks | Deployable, 22 racks | Throughput, 22 racks |
|---|---|---|---|---|---|---|
| 350 | 7.4 | 3 | 48 | 33.6 | 64 | 44.8 |
| 400 | 7.8 | 3 | 48 | 37.92 | 64 | 50.56 |
| 450 | 8.2 | 3 | 48 | 41.04 | 64 | 54.72 |
| 500 | 8.6 | 3 | 48 | 43.44 | 64 | 57.92 |
| 550 | 9.0 | 3 | 48 | 45.36 | 64 | 60.48 |
| 600 | 9.4 | 2 | 32 | 31.1 | 44 | 42.77 |
| 650 | 9.8 | 2 | 32 | 31.68 | 44 | 43.56 |
| 700 | 10.2 | 2 | 32 | 32.0 | 44 | 44.0 |

Best cap: 550 W on 16 racks and on 22 racks. A fourth node per rack would need a cap <= 269 W, below the curve.
