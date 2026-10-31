# T1 — The breaker that tripped at job start: worked solution

Sources: manuscript Sections 21.6 (2N, continuous derating), 21.7 (transients) and 21.8 (capping,
Table 21.5). Evidence `[ILLUSTRATIVE]`; arithmetic `[MODELED]`, reproduced by `solve.py`.

**Observe.** lh-03 went from 12.1 kW idle to 41.6 kW within ≈ 3 s of a synchronized job start.
41.6 kW at 415 V and PF 0.95 = 41,600 / (√3 × 415 × 0.95) ≈ **60.9 A per phase**, against a PDU
electronic overcurrent setting of 48 A (= 32.78 kW). The PDU tripped 2 s later and all four nodes lost
input. The B side was de-energized for planned UPS-B maintenance.

**Hypotheses and discriminating evidence**

| Hypothesis | Evidence | Verdict |
|---|---|---|
| The capacity plan budgeted the rack against **both** sides ("41 kW ≤ 2 × 32.78"), so with B down the whole rack sat on one 32.78 kW circuit | Plan line; B de-energized 08:00–12:00; 41.6 kW measured on A | **Root cause (condition)** |
| Synchronized job start stepped 32 nodes to full power at once | 12.1 → 41.6 kW in ≈ 3 s; 61 A ≫ 48 A trip setting (not enough to trip the 60 A thermal-magnetic breaker in seconds) | **Trigger** |
| Faulty PDU or breaker | lh-04 (3 nodes, 30.9 kW ≈ 45.3 A) held on the same kind of circuit; main-hall racks have two circuits per side and held at 39–41 kW | Not supported (inspect anyway) |
| Node or PSU fault | All four BMCs logged "PSU input lost" in the same second as the trip | Consequence |

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

Note: lh-04's 30.9 kW is under the trip point but *above* the 29.5 kW planned budget. Three nodes at
the default 700 W limit (3 × 10.2 = 30.6 kW) violate the transient margin too.

**Immediate mitigation.** Keep lh-03 at three nodes (or drained) until B returns. Cap lh-04 and every
legacy rack's job nodes to 650 W while B is down. Requeue the 32-node job from its last checkpoint on
racks that fit (draining does not move a running job).

**Guardrail.**
1. *Standing rule:* legacy racks carry at most **3 nodes at ≤ 650 W** (29.4 kW). The capacity plan
   and the scheduler's rack power resource enforce it. Owner: Platform.
2. *Maintenance gate:* trigger = any planned single-side outage. Before opening B, an automated check
   verifies "every affected rack's planned peak ≤ one side's budget, else cap or drain first". The
   signal comes from Facilities (outage calendar, PDU telemetry) and the action from Platform.
3. *Ramp:* job starts > 500 kW ramp over ≥ 60 s (Table 21.5). Owner: Training Infra.

*Marking:* hypotheses 3, arithmetic 3, guardrail 3, blameless phrasing 1. Deduct for blaming the
on-call engineer or the job owner.
