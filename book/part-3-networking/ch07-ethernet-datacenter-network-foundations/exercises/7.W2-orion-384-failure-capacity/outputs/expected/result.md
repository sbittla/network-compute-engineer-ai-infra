# 7.W2 — result `[MODELED]`

| Scenario | Raw uplink (Tb/s) | ECMP-aware ingress (Tb/s) | Bisection (Tb/s) |
|---|---|---|---|
| baseline | 12.8 | 12.8 | 102.4 |
| link_down | 12.4 | 9.6 | 102.0 |
| spine_down | 11.2 | 11.2 | 89.6 |

- Single-link penalty 25.0 % (ORION-256: 12.5 %); single-spine penalty 12.5 % (ORION-256: 25 %)
- P(no collision) = 4!/4⁴ = 24/256 = **9.4 %**; E[links used] = 4 × (1 − (3/4)⁴) = **2.73**
