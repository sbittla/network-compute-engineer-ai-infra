# Capstone F — Abridged Exemplar of a Distinction-Level Submission (INSTRUCTOR ONLY)

> Abridged model answer in the learner's voice. All results `[SIMULATED]` with the shipped
> simulator (seed 7, parameters in its `DEFAULT_CONFIG`); arithmetic `[MODELED]`. No real system
> was touched. Suggested score ≈ 92/100 (see the closing note).

---

## 1. Problem statement and safety scope

Halcyon's first game day showed that ORION's recovery path works for single faults but was never
tested against overlapping faults, silent control-plane failures, or exhaustion of spare capacity.
This game day tests six hypotheses on the simulated ORION, never touches the rack-08 inference
partition, and produces a backlog ranked by simulated GPU-hours avoided *and* by cost. The
simulator models control flow and timing only; it does not model congestion, partial link
degradation, NCCL algorithms, stragglers, GPU errors, scheduler policy or human response, so every
conclusion below is about *mechanism and order of magnitude*, not about a real cluster's numbers.

## 2. Analysis of the recorded game day (default rules)

| Fault | Detect (s) | Mitigate (s) | Recover (s) | Lost GPU-h (work + idle) | Note |
|---|---|---|---|---|---|
| F1 link_down orion-n07 rail 4 | 30 | 60 | 903.5 | 94.4 (45.5 + 49.0) | detection by the noisy stall rule |
| F2 storage 2 % for 1 h | **none** | 3,600 (rollback) | 3,600 | 0 | silent; widened RPO |
| F3 node_loss orion-n18 | 25 | 70 | 1,203.8 | 167.8 (103.0 + 64.8) | in-flight checkpoint aborted |
| F4 scheduler outage 20 min | **none** | 1,200 (rollback) | 1,200 | 0 | silent |
| F5 link_down orion-n13 rail 0 | 30 | 900 | **never** | ≥ 307.9 (35.3 + 272.7) | spares exhausted |
| **Total** | | | | **≥ 570.1** | |

Key mechanism (F3): the checkpoint that started just before 11,000 s (step 517) needed 980 GB / 1.6 GB/s = 612.5 s
to write, so at 11,000 s it was still in flight and the lost node's writer aborted it. The job
restored from step 414, not 517: 192 × 111 × 17.4 / 3600 = 103.0 GPU-h of recomputation (hang at
step 525), versus 7.4 GPU-h if the aborted checkpoint had been usable. The restart also loaded 980 GB
at 3.2 GB/s (306 s), stretching recovery from 903.5 s to 1,203.8 s.

Key mechanism (F5): F1 and F3 each consumed a spare (orion-n27, orion-n28). orion-n07's link came back at
3,600 s but the node stayed drained — nothing returns repaired nodes to service. When F5 failed
the job at 17,100 s, the scheduler (back at 17,400 s) found zero spares and logged
`requeue_blocked`. The training job was down for the last 1.42 h of the run: (21,600 − 16,487.3)
× 192 / 3600 = 272.7 idle GPU-h and counting. The failed link is not the cause; capacity policy is.

## 3. Alert rules (excerpt)

| Rule | Expression | for | Detects | Why |
|---|---|---|---|---|
| NicLinkDown | `sim_nic_link_up == 0` | 30 s | link_down | cause signal; 2 scrapes to avoid single-sample blips |
| NodeDown | `sim_node_up == 0` | 60 s | node_loss | matches health-controller delay |
| JobStalled | `sim_job_progress_age_seconds > 120` | 60 s | link_down, node_loss | max normal age is step + stall ≈ 17.4 + 20 = 37.4 s; 120 s gives > 3× margin |
| StorageWriteDegraded | `sim_storage_write_GBps < 40` | 60 s | storage_slow | 50 % of 80 GB/s; checkpoint would take > 24.5 s |
| CheckpointStale | `sim_checkpoint_age_seconds > 3600` | 300 s | storage_slow | 2 × the 30-min interval |
| SchedulerHeartbeatAbsent | `absent(sim_scheduler_heartbeat)` | 60 s | scheduler_outage | the scheduler cannot report its own death |

Fault-free 6 h: 7 → 0 alerts. Canonical detection: node 70 s, link 40 s, scheduler 70 s, storage
70 s (targets 120/120/120/300 s).

## 4. My game day: hypotheses versus observations

| Scenario | Expected lost GPU-h | Observed | Verdict | Explanation |
|---|---|---|---|---|
| S1 node loss | ≤ 120 (model: 96) | 110.3 | held | fault landed later in the checkpoint interval than the 900 s average |
| S2 link down | ≤ 120 | 110.3 | held | a dead rail is fatal to the collective, same path as S1 |
| S3 storage 5 % | 0 | 0 | held | no interruption; RPO stretched (write 245 s) |
| S4 scheduler outage | 0 | 0 | held | running jobs unaffected |
| S5 storage 2 % + node loss | ≤ 150 | 178.1 | **failed** | aborted in-flight checkpoint; slower load |
| S6 outage + link down | ≤ 120 | 142.4 | **failed** | requeue waited for the scheduler |

## 5. What-if validation of backlog items

| Change | Scenario | Lost GPU-h | Note |
|---|---|---|---|
| `fast_fail=True` | S1 | 110.3 → 81.5 | saves 28.8 = (600 − 60) × 192 / 3600, as modeled |
| `fast_fail=True` | recorded plan | 570.1 → 474.3 | trajectory shifts (different checkpoint phase at each fault), so I attribute savings only from single-fault runs |

## 6. Postmortem excerpt (contributing factors)

1. The control plane could fail silently: no absence alert on the scheduler (F4) and drains queued
   without a signal (F5, 840 s).
2. Checkpoint durability was invisible: dashboards showed "last checkpoint started", which made the
   F3 restore point look 103 steps newer than it was.
3. Spare capacity was sized for one failure per day with no automated return to service.
4. A noisy stall rule trained responders to ignore the alert that did, three times, signal real
   hangs.

## 7. Backlog (re-ranked with costs the formula omits)

| Rank | Item | Formula score | Adjustment | Why |
|---|---|---|---|---|
| 1 | RB-01 scheduler absence alert | safety | — | cheap, closes a silent failure |
| 2 | RB-06 de-flap stall alert | 0 | ↑ | ≈ 28 false pages/day (7 per 6 h) erode trust in a key signal; 0.1 week |
| 3 | RB-04 storage + staleness alerts | 4,500 | — | |
| 4 | RB-02 return-to-service via re-acceptance | 1,200 | ↑ | fixes the F5 root cause without reserving idle GPUs |
| 5 | RB-03 fast-fail | 1,972.8 | — | validated: 28.8 GPU-h per event × 137 interruptions/yr (canonical MTBF) |
| 6 | RB-05 grow spares to 4 | 12,000 | ↓ | two more idle nodes reserve 140,160 GPU-h/yr vs 12,000 avoided; only worth it if spares run preemptible work |

## 8. Final engineering review

Ship RB-01, RB-06 and RB-04 this sprint (≈ 0.5 engineer-week). Residual risks: (1) collective
timeout behaviour on real hardware may differ (process-group timeout configuration, watchdog) —
validate in the L3 lab, owner Training Infra; (2) return-to-service needs Capstone E acceptance
gates, owner Fleet; (3) simulator omits stragglers and partial link degradation — next game day
should add a degraded-rail scenario in the lab, owner SRE.

---

**Instructor note.** Distinction because hypotheses carry numbers and dates, every refuted
hypothesis is explained by mechanism with arithmetic, unrecovered loss is a lower bound, what-if
attribution avoids the trajectory confound, and the backlog is re-ranked with explicit capacity and
toil costs. Points lost: no L2/L3 evidence; postmortem lacks a "where we got lucky" section in this
abridged form.
