# 20-DEL — Automation sample and safe-change runbook: reference deliverable

**Relies on:** Lab 20 Parts 1–2 (`solutions/lab/safe_change.py`, checker lines `p1.*` and `p2.*`), the
manuscript's "Production operations notes: safe-change runbook excerpt" (Table 20.15), Sections 20.7–20.10,
and Table 20.13 (decision log) `[SIMULATED]`.

## 1. Automation sample

The reference sample is the completed lab reconciler and rollout controller. Its README must document four
safety defaults, each with where it lives in code and how it was tested:

| Default | Behaviour | Evidence |
|---|---|---|
| Dry run | `apply_plan(..., dry_run=True)` is the default; zero writes | `p1.apply_default_is_dry_run` |
| Cap | `max_targets` (8) limits each batch; capped targets return as `deferred_targets` | `p1.apply_cap_and_audit` |
| Audit | one record per action: seq, change ID, actor, target, key, before (read at apply time), after, result, dry_run | `p1.apply_cap_and_audit`, `p1.idempotent_converge_and_noop` (24 `noop` records on re-apply) |
| Kill-switch hook | not in the lab reference code: the learner adds a callable (for example `should_stop()` reading a flag in the change system) checked by `apply_plan` before every target and by `run_rollout` before every wave; when set, the run stops cleanly and records why | the learner's own unit test that flips it mid-run; the README must say where the flag lives |

Idempotency proof: three capped batches (8, 8, 6) converge and the re-plan is empty. Rollout logic: medians vs
own baseline, relative thresholds with absolute floors, precheck skip, hold on insufficient bake
(`p2.condition_semantics`, `p2.wave_decisions`, `p2.bake_insufficient_hold`, `p2.rollout_abort_and_rollback`).

## 2. Safe-change runbook: NIC firmware 28.42.1000 → 28.43.1014 on ORION

**Before (T − 2 days → T).** Change record with owner, approver, desired-state commit, rendered plan and
dry-run output. Bundle validated against the Chapter 16 compatibility matrix. Downgrade to 28.42.1000 rehearsed
in the lab with the same automation and timed. Wave plan 2/3/4/8/8/7, slot-major, stratified canary.
Maintenance reservation; no running jobs on targets. OOB access verified (BMC/Redfish). Baselines per node: 6
pair-test samples, CNP and PFC rates, error counters. Kill switch tested in the lab.

**During.**

| Signal | Threshold `[ILLUSTRATIVE]` | Source | Action |
|---|---|---|---|
| AC1 busbw per rail, median vs own baseline median | drop > 5 % | Table 20.9; noise ≈ 0.6 %/sample, 5 % ≈ 14 standard errors | abort, rollback all changed |
| AC2 CNP/s, median | > 3 × baseline and > 500/s | Table 20.9; lab wave 2: 986/s vs 200/s | abort |
| AC3 PFC pause/s, priority 3 | > 3 × baseline and > 150/s | Table 20.9 | abort |
| AC4 / AC5 Xid, link flaps | sum > 0 | Table 20.9 | abort |
| Missing telemetry | > 1 sample | Table 20.15 | hold |
| Target not back | 15 min after apply | Table 20.15 | stop wave, escalate to Fleet |
| Circuit breaker | > 2 targets or > 10 % fail | Table 20.11 | halt, kill switch on |

The thresholds are validated by the lab decision log: they ignored `orion-n09`'s single 7 % dip, skipped
`orion-n13` at precheck, and aborted on `orion-n25`/`n29` (−9.8 %, −9.9 %).

**Abort and rollback.** Controller aborts; on-call confirms within 10 min; flash 28.42.1000 on all changed nodes
(rehearsed time bound), reset, read back, pair test against baseline; return nodes to service only when within
3 % of baseline.

**After.** Final reconciler pass plans 0 actions; fleet read-back of firmware version; 24–72 h watch for slow
signals (Table 20.8).

**Escalation.** Fabric on-call → Fleet (firmware) → Training Infra (job impact) → SRE incident process on SLO
burn.

**Audit bundle.** Per-target before/after, decision log with reasons, baseline and bake metrics, rollback
records, approvals, plan hash, tool version.

## Marking (30 points)

Sample 15 (safety defaults 8, tests/checker 4, README 3) · runbook 15 (structure 5, thresholds with sources 5,
rollback/escalation/audit 5). Common weakness: thresholds copied from the chapter without a baseline method.
