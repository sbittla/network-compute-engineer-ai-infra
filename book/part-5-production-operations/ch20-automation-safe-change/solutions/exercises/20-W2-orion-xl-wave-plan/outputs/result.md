# Exercise 20-W2 — result `[MODELED]`

a. P = 1 − 0.98^8 = 0.149 (binomial); exact 1 − C(502, 8)/C(512, 8) = 0.147. For 90 %: k ≥ ln 0.1 / ln 0.98 = 113.97 → **114 nodes**.
b. P = 1 − (1 − 0.8)^2 = **0.96**.
c. Plan [2, 6, 24, 96, 128, 128, 128] (sum 512, max 128 = racks). Duration 7 × 75 = 525 min = 8.75 h; peak out 25 %; GPU-h = 512 × 8 × 1.25 h = 5,120.
d. After waves 0–2 (32 nodes): P = 1 − 0.98^32 = **0.476** (exact 0.479).
