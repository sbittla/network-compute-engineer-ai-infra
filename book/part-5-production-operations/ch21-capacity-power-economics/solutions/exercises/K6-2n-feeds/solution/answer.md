# K6 — 2N feeds: worked solution

Sources: manuscript Sections 21.6 (power chain, continuous-load derating) and 21.7 (transient margin);
docs/REFERENCE_CLUSTER.md (circuit constants). Inputs `[ILLUSTRATIVE; jurisdiction- and
equipment-dependent]`; results `[MODELED]`.

**Circuit.** √3 × 415 V × 60 A × 0.95 PF × 0.80 continuous = 32.78 kW per circuit (48 A per phase).

**The failure scenario that sets the limit.** With 2N A/B feeds each side normally carries about half
the rack. When one side is lost (UPS maintenance, a breaker trip or a PDU failure), the surviving side
must carry the *whole* rack. The planning limit is therefore one side's capacity, not the sum of both.
A further 10 % is kept back for synchronized step-to-step and job-start power swings.

**(a) Canonical ORION rack, two circuits per side.**

```text
one side = 2 × 32.78 = 65.55 kW continuous
planned peak = 65.55 × (1 − 0.10) = 59.0 kW
```

A 4-node ORION rack at 40.8 kW maximum (4 × 10.2 kW) fits with 18.2 kW to spare. Four slots, not
power, limit the rack.

**(b) Legacy rack, one circuit per side.**

```text
one side = 32.78 kW continuous
planned peak = 32.78 × 0.90 = 29.5 kW
```

That fits two uncapped HX8 nodes (20.4 kW), or three nodes capped at ≤ 650 W per GPU:
3 × (4.6 + 8 × 0.65) = 29.4 kW. The cap that exactly fits three is (29.5 / 3 − 4.6) / 8 ≈ 654 W, so the
lab curve's 650 W step is the lightest usable cap (Section 21.8).

**Common wrong answers**

- Planning to 2 × 65.55 = 131.1 kW (both sides). The rack trips on the first feed loss. This is the
  root cause of troubleshooting case T1.
- Forgetting the 80 % continuous derating (41.0 kW per circuit at the full 60 A).
- Applying the transient margin to the breaker rating instead of to the continuous limit.
