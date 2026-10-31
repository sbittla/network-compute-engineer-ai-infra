# 2.1.3 — Usable capacity of a 2N rack with 2 × 60 A, 415 V three-phase circuits per side

Source: manuscript Section 2.5 ("Three-phase circuit arithmetic", "Redundancy modes"). `[MODELED]`;
`solve.py` checks the arithmetic.

```text
apparent power per circuit = √3 × 415 V × 60 A          = 43.13 kVA
real power, derated        = 43.13 kVA × 0.80 × 0.95    = 32.78 kW
per side (2 circuits)      = 2 × 32.78 kW               = 65.55 kW
rack usable capacity (2N)  = 65.55 kW                   (not 131.1 kW)
```

**Why not the sum of both sides:** in a 2N design each side (A and B, from independent UPS systems) must be
able to carry the *entire* rack when the other side is lost or in maintenance. During normal operation
the load splits roughly 50/50, but the design limit is what one side can deliver alone. Planning to
131 kW would trip the surviving side's breakers on the first feed loss. The 0.80 is the
continuous-load derate (NEC 80 % rule); the 0.95 is the power factor that converts kVA to kW.

**Common wrong answer:** adding both sides; forgetting √3 for three-phase (gives 24.9 kVA).
