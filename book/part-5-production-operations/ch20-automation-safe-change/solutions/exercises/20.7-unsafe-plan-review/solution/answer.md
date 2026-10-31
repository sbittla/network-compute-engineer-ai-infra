# 20.7 — Review of the unsafe change plan: reference solution

**Relies on:** lab Part 3 (`lab/data/unsafe_change_plan.md`, `lab/data/gap_catalog.json`), the reference
`solutions/lab/findings.yaml` (17 gaps), and manuscript Sections 20.7–20.10 and the runbook excerpt.

## Findings

The reference `findings.yaml` records 17 real gaps; the checker passes it as 17/17 coverage, 0 false
positives, 17 findings with valid line citations and concrete fixes. Highlights, with plan lines:

| Gap | Lines | Why it matters |
|---|---|---|
| G-BUNDLED | 1, 10–12 | MTU, QoS and firmware together: no attribution, no partial rollback |
| G-CANARY, G-BLAST-RADIUS | 10, 11, 16, 18 | all 32 nodes and all 8 rail leaves at once |
| G-RATE-LIMIT, G-KILL-SWITCH | 18 | 32 backgrounded SSH sessions, 32 reboots at once, nothing can stop them |
| G-DRAIN | 18, 20 | reboots kill running jobs on all 256 GPUs |
| G-PRECHECK, G-DRYRUN, G-REVIEW-VCS | 16, 18 | config pasted from a wiki, no diff, no compatibility check |
| G-ORDERING | 16, 18 | leaves change before hosts: transitional DSCP/PFC mismatch |
| G-SUCCESS-CRITERIA, G-ABORT, G-BAKE | 5, 19, 20, 24 | "dashboards look good" is not measurable; no declared abort conditions; no bake time |
| G-ROLLBACK | 24 | revert by hand from memory; reimaging does not roll back firmware; nothing rehearsed or time-bounded |
| G-AUDIT | 16, 18, 24 | no before-state captured, no per-target record of what changed |
| G-WINDOW | 5 | Friday 16:30–17:00: 30 min for a fleet-wide change, unstaffed weekend after it |
| G-OOB-ACCESS | 16, 18 | a bad QoS or MTU push can cut in-band access; BMC/console never verified |

The full list is exactly these 17 gap IDs. Line 28 ("Low. The same change was tried on a lab node last
month.") is weak evidence and worth a comment in the rewrite, but the catalogue has no separate gap for it;
cite it as supporting evidence in G-PRECHECK or G-BAKE rather than as a new finding.

**Not gaps (false-positive traps):** owner (line 3), approval (line 4) and communications (line 6) are
covered. Reporting them costs precision.

## Rewritten plan: three changes, in this order

**Change 1 — NIC firmware 28.43.1014** (Chapter 16 validated bundle). Precheck: bundle in the compatibility
matrix with the installed driver, node healthy, links at 400G, baseline busbw/CNP/PFC recorded. Drain or
maintenance reservation. Waves 2/3/4/8/8/7, slot-major, ≤ 1 node per rack, bake 60 min under load. Abort on
AC1–AC5 (Table 20.9). Rollback: flash 28.42.1000, rehearsed in the lab and timed (and checked for anti-rollback).

**Change 2 — leaf RoCE QoS profile**, from git with CI policy checks and a dry-run diff per leaf, one rail leaf
per wave (`orion-be-leaf-r0` first), as in Exercise 20.6. Abort on TC 3 drops > 0, PFC pause > 3× baseline and
> 1,000/s, busbw drop > 5 %. Rollback: full-config replace from the previous commit with commit-confirm.

**Change 3 — RDMA MTU 4,096** via the reconciler: dry run, cap 8, audit, node waves 2/3/4/8/8/7; post-change
read-back of `active_mtu` and a pair test. Rollback: reconcile to the previous desired state, re-create QPs.

Every change: OOB access verified (BMC/Redfish, leaf console), kill switch tested, circuit breaker
(> 2 targets or > 10 % fail → halt), concurrency ≤ 4, staffed weekday window with time for full rollback,
audit bundle attached to its own change record.

## Marking (20 points)

Checker 10 (coverage 4, false positives 3, evidence quality 3) · rewrite 10 (three ordered changes 4, controls
per change 6). Common misses: G-ORDERING and G-OOB-ACCESS.
