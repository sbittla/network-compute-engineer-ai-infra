# W2 — result `[MODELED]`

- (a) (16 − 1) × 50 KB/µs = **750 KB/µs**
- (b) 1,500 KB / 750 KB/µs = **2.0 µs**
- (c) feedback needs ≥ 1 RTT = 6 µs > 2.0 µs → **no** (the 6 MB share would fill in 8 µs without PFC)
- (d) 16 × 2 MB / 50 GB/s = **640 µs**
- (e) log₂ 16 = **4 halvings**; ≈ 6 + 3 × 50 = **156 µs** = 24 % of (d) (alternative 4 × 50 = 200 µs ≈ 31 %)
- (f) BDP = 50 KB/µs × 6 µs = **300 KB**; Kmin ≤ 1 BDP, well below 1.5 MB
