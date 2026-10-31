# W2 — scaling and detectability `[MODELED]`

| GPUs | Tokens/s | E_weak |
|---|---|---|
| 64 | 60,332 | 100.0 % |
| 128 | 119,021 | 98.6 % |
| 256 | 234,319 | 97.1 % |

Straggler share: 0.175 of 0.24 s (16 nodes); 0.325 of 0.52 s (32 nodes). After DP exposure, unexplained 0.016 s and 0.122 s.

MDE(n = 5) = 0.195 s > 0.15 s → not detectable; n = 8.43 → 9 runs per arm.
