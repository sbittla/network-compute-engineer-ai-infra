# T1 - the breaker that tripped at job start `[MODELED]`

- Circuit: 32.78 kW continuous = 48.0 A per phase at 415 V, PF 0.95
- Plan claimed 41.0 kW <= 2 × 32.78 = 65.56 kW (wrong: 2N means one side)
- lh-03 idle 08:55: 12.1 kW = 17.7 A
- lh-03 job start 09:02:10: 40.8 kW = 59.7 A
- lh-04 peak (3 nodes): 30.6 kW = 44.8 A
- Single-side budget = 32.78 × (1 - 0.1) = **29.5 kW**
- Four nodes: <= 7.376 kW each -> cap <= (7.376 - 4.6) / 8 = **347 W** (below the curve; at 350 W four nodes still need 29.6 kW)
- Guardrail: **3 nodes at <= 650 W** = 29.4 kW <= 29.5 kW
