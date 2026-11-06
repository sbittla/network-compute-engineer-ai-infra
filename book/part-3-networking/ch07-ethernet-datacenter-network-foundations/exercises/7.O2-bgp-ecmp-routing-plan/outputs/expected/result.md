# 7.O2 — result `[MODELED]`

| Failure | Affected leaf raw uplink (Tb/s) | Affected leaf ECMP-aware ingress (Tb/s) | Bisection (Tb/s) | ECMP width at orion-be-leaf-r7 |
|---|---|---|---|---|
| link | 12.4 | 11.2 | 50.8 | 32 |
| spine | 9.6 | 9.6 | 38.4 | 24 |
| leaf | 0.0 | 0.0 | 38.4 | 32 |

Link = one orion-be-leaf-r0↔orion-be-spine-1 link; spine = orion-be-spine-2 (affected leaf: any); leaf = orion-be-leaf-r3.
BFD detection 300 ms × 3 = 0.9 s.
