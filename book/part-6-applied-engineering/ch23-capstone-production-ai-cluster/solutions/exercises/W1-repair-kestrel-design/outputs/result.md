# W1 — Kestrel repair `[MODELED]`

1. GPUs: (34 − 2) × 8 = 256; DP = 256 / (8 × 4) = 8 (claimed 16 gives 512)
2. Leaf: 34 + 32 = 66 > 64; uplinks ≤ 30, multiple of 4 → 28 (7 per spine)
   - oversubscription 34:28 = 1.214:1; spares idle 32:28 = 1.143:1
   - spine ports 8 × 7 = 56 of 64; cables 8 × (34 + 28) = 496 (272 + 224); as drawn 528; bundle says 512
3. Racks: floor(45.0 / 10.2) = 4 per rack → ceil(34 / 4) = 9 racks; 5-node cap 9.0 kW → GPU cap (9.0 − 4.6) / 8 = 550 W
