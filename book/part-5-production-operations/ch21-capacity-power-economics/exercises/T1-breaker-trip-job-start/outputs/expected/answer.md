# T1 — The breaker that tripped at job start: worked solution

Sources: manuscript Sections 21.6 (2N, continuous derating), 21.7 (transients) and 21.8 (capping,
Table 21.8). Evidence `[ILLUSTRATIVE]`; arithmetic `[MODELED]`, reproduced by `solve.py`.

**Observe.** lh-03 went from 12.1 kW idle to 40.8 kW within ≈ 3 s of a synchronized job start.
40.8 kW at 415 V and PF 0.95 = 40,800 / (√3 × 415 × 0.95) ≈ **59.7 A per phase**, against a PDU
electronic overcurrent setting of 48 A (= 32.78 kW). The PDU tripped 2 s later and all four nodes lost
input. The B side was de-energized for planned UPS-B maintenance.

**Hypotheses and discriminating evidence**

| Hypothesis | Evidence | Verdict |
|---|---|---|
| The capacity plan budgeted the rack against **both** sides ("41 kW ≤ 2 × 32.78"), so with B down the whole rack sat on one 32.78 kW circuit | Plan line; B de-energized 08:00–12:00; 40.8 kW measured on A | **Root cause (condition)** |
| Synchronized job start stepped 32 nodes to full power at once | 12.1 → 40.8 kW in ≈ 3 s; 60 A ≫ 48 A trip setting (not enough to trip the 60 A thermal-magnetic breaker in seconds) | **Trigger** |
| Faulty PDU or breaker | lh-04 (3 nodes, 30.6 kW ≈ 44.8 A) held on the same kind of circuit; main-hall racks have two circuits per side and held at 39–41 kW rack total (≈ 20 kW per side, both feeds up) | Not supported (inspect anyway) |
| Node or PSU fault | All four BMCs logged "PSU input lost" in the same second as the trip | Consequence |
| lh-04 latent violation | 30.6 kW (three uncapped nodes) held, but exceeds its 29.5 kW single-side plan (no transient margin) | Same root cause; cap lh-04 to 650 W now |

**Root cause (system, not person).** The legacy-hall capacity plan violated the 2N rule that a rack
must fit on **one** side, and the maintenance procedure had no check of single-side loading before
de-energizing B. No individual made an unusual mistake. The process allowed a plan that was only safe
while both feeds were up.

**Arithmetic for the cap.**

```text
single-side budget = 32.78 kW × (1 − 0.10) = 29.5 kW
four nodes:  ≤ 29.5 / 4 = 7.376 kW each → cap ≤ (7.376 − 4.6) / 8 ≈ 347 W
             below the curve's useful range (350 W → 0.70, and 4 × 7.4 = 29.6 kW still exceeds 29.5)
three nodes at 650 W: 3 × (4.6 + 8 × 0.65) = 29.4 kW ≤ 29.5 kW ✓
```

Note: lh-04's 30.6 kW (three nodes at the default 700 W limit, 3 × 10.2) is under the trip point but
*above* the 29.5 kW planned budget: it violates the transient margin too.

**Immediate mitigation.** Keep lh-03 at three nodes (or drained) until B returns. Cap lh-04 and every
legacy rack's job nodes to 650 W while B is down. Requeue the 32-node job from its last checkpoint on
racks that fit (draining does not move a running job).

**Guardrail.**
1. *Standing rule:* legacy racks carry at most **3 nodes at ≤ 650 W** (29.4 kW). The capacity plan
   and the scheduler's rack power resource enforce it. Owner: Platform.
2. *Maintenance gate:* trigger = any planned single-side outage. Before opening B, an automated check
   verifies "every affected rack's planned peak ≤ one side's budget, else cap or drain first". The
   signal comes from Facilities (outage calendar, PDU telemetry) and the action from Platform.
3. *Ramp:* job starts > 500 kW ramp over ≥ 60 s (Table 21.8). Owner: Training Infra.

*Marking:* hypotheses 3, arithmetic 3, guardrail 3, blameless phrasing 1; +1 bonus for spotting lh-04's latent violation. Deduct for blaming the
on-call engineer or the job owner.
