# 17-DEL — Workload placement policy and scheduling troubleshooting guide (grading reference)

The deliverable combines 17-M2 and 17-M3; grade with their rubrics plus 10 % for the appendix.

**Part 1 — Placement policy (from 17-M2).** Must specify, consistently with the lab simulator:
eligibility filters in order (lifecycle → health → pool → GPU type → dedication → MIG → rail
completeness for gangs, expressed as features/labels rather than drains); topology rules (socket
best fit for 1/2/4 GPUs, whole nodes in multiples of 8 for gangs, rail-degraded nodes preferred for
single-node 8-GPU work, rack-compact gangs, ≤ 2 blocks on ORION-XL); quota model (nominal, cohort
borrowing into idle capacity, ≤ 1.2× overcommit); priority classes with asymmetric preemption;
fairness key (priority, share, age); gang mechanism with head-of-queue reservation; small-job
confinement; metrics (gang time-to-start p95, largest placeable gang, allocation %, fragmentation,
quota-blocked job-hours). Replay evidence: e.g. the `urgent-eval` QOS replay (J05 and J08 restored,
69 GPUs placed both ways) `[SIMULATED]`.

**Part 2 — Troubleshooting guide (from 17-M3).** Decision order: scheduler verdict → policy (quota,
priority) → node state → device plugin / MIG → placement constraints → topology/shape, with the exact
`kubectl` and Slurm commands and what each output proves. Applications: P03 (FRAGMENTATION: 34 free ≥
32, one whole node) and P11 (UNTOLERATED_TAINT: 8 + 4 = 12 < 16 eligible), with the evidence lines
quoted.

**Appendix.** The lab `placement-report.md` (five pending jobs with reasons and the fair-share, rail,
and lifecycle effects) and the checker output `9/9 checks passed`.

**Distinction:** replay evidence for at least two policy changes, and an L2 reproduction of at least
two pending causes with the real event text (`FailedScheduling` messages, `squeue %R`).

**Common deductions:** policy rules that contradict the simulator (e.g. treating `PreferNoSchedule`
as blocking, `≥` in quota checks); guide entries without a safe fix or a "do not"; recommending a
toleration for another tenant's dedication taint.
