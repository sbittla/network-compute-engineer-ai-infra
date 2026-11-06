# Marking scheme: 17-D1 ORION-XL block placement rules

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** The config fragment, a modeled comparison of placements (show formula), and a wait-time trade-off with numbers.

| Criterion | Points |
|---|---|
| topology.conf (or Kueue TAS) fragment with 16 blocks of 32 nodes under pod/top switches | 3 |
| Modeled comparison: 2 blocks 3.1 %, 3 blocks 4.7 %, spread ≈ 95 % cross-block hops; per-block uplink 51.2 Tb/s | 4 |
| Wait trade-off: 512·w vs 0.03 × 240 × 512 ≈ 3,686 GPU-h → break-even ≈ 7.2 h; chosen bound defended | 3 |
