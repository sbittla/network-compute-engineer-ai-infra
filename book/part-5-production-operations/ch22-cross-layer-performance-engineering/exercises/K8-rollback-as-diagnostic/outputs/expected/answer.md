# K8 — Why a diagnostic rollback is a poor test (solution)

**Reason 1: confounding and time variation.** A rollback creates a second before/after comparison, with
the same weakness as the first: load, job mix, datasets, placement and other changes keep varying while
the rollback is in effect, so any change in step time mixes the rollback with everything else that
moved. A rollback also *destroys* the natural experiment already running for free. On ORION after
CW-2026-10-12, half the nodes run R570 and half R550, so comparing jobs that touched upgraded nodes with
jobs that did not, holding placement and tier fixed, already answers "does the driver matter?" (lab:
driver effect +0.90 ± 0.07 s `[SIMULATED]`). Rolling back removes that contrast.

**Reason 2: poor information per cost and risk.** Using the ranking rule of Section 22.3.4,
`priority = info / (cost_hours × risk_multiplier)`, the lab's driver rollback T5 has info 0.6, cost 8 h and
high risk in production, so it is rejected outright by the hard rule; even scored, it would be
0.6 / (8 × 5) = 0.015, two orders of magnitude below the offline NCCL channel-line check T2
(0.7 / (0.5 × 1) = 1.4). A rollback answers *one* leaf, slowly (days of drains and reboots), while an
offline partition answers several leaves in minutes without touching production.

**Even a safe rollback.** "Safe" removes the harm term but not the confounding or the cost, and a
rollback that "helps" invites last-change bias: the team stops looking for the other causes.

**Common wrong answers.** Two reasons that are really the same (for example "it is risky" and "it might
break things"); arguing the rollback is fine because it is reversible.
