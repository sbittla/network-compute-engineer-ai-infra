# Capstone F — Instructor Grading Guide (INSTRUCTOR ONLY)

Removed from student releases by `scripts/make_student_release.py`. Contains the planted findings,
expected numbers, rubric interpretation, common failure patterns and oral questions. Reference
solution: [reference/gameday.py](reference/gameday.py). Abridged 90+ submission:
[EXEMPLAR.md](EXEMPLAR.md).

## 1. Verifying the kit

```bash
cd capstones/capstone-f-reliability-game-day/starter-kit
python check.py --impl solution     # 11/11 PASS, exit 0, ≈ 9 s
python check.py                     # 2/11 PASS (dataset + simulator determinism), 9 TODO, exit 1
python ../../../scripts/validate_labs.py capstone-f
```

## 2. Planted findings in the recorded game day (and in the defaults)

All values `[SIMULATED]` with the shipped simulator parameters.

| # | Where | What is planted | What a strong submission finds | What it teaches |
|---|---|---|---|---|
| P1 | `default_alert_rules.yaml` `JobStalled` | Threshold 30 s with `for: 0s`; a checkpoint stalls training for 20 s on top of a 17.4 s step | 7 false alerts on a fault-free 6 h run (one per training checkpoint); on the recorded day 8 of 11 alerts are this rule, 5 of them checkpoint-stall noise (1,845 s, 5,430 s, 10,860 s, 14,025 s, 15,840 s) | Thresholds must sit above normal pauses; `for` durations; alert fatigue |
| P2 | defaults | No rule on the scheduler | F4 (20-min scheduler outage) is **undetected**; F5's drain waits 840 s for the scheduler | Absence alerting (`absent()`) for components that fail silent |
| P3 | defaults | `CheckpointStale` at 7,200 s (4 × interval) and no storage-throughput rule | F2 (storage at 2 % for 1 h) is **undetected** | Symptom alerts on slow signals miss causes; alert on the cause (write throughput) too |
| P4 | defaults | `NicLinkDown` with `for: 300s` | Fires 300 s after F1/F5 (the stall rule happened to fire earlier) | Cause alerts should be fast; slow `for` is a design smell |
| P5 | F2 + F3 overlap | Node lost at 11,000 s while the checkpoint started just before (step 517) is still writing at 1.6 GB/s (612 s write) | `ckpt_aborted` step 517; hang at step 525; restore from durable step 414; 111 steps lost = 103.0 GPU-h of work, not 8 steps = 7.4 GPU-h | "Last checkpoint" means last *durable* one; RPO widens silently under storage degradation |
| P6 | F3 restart | Restart load at degraded read bandwidth: 980 GB / 3.2 GB/s = 306 s | Recovery 1,203.8 s vs 903.5 s for F1 | Storage health affects RTO as well as RPO |
| P7 | F1 → F3 → F5 | Each failure consumes a spare; drained nodes are never returned even after the fault clears (orion-n07 link back at 3,600 s) | F5: `requeue_blocked` (need 1, available 0); training job down from 16,487 s to the horizon; ≥ 307.9 GPU-h lost and **unrecovered** | The failed component is not the cause: spare exhaustion and no return-to-service path are Quantitatively: training-partition failures arrive at 24 × 24 / 1,536 = 0.375/day; with the canonical 5-day MTTR, 0.375 × 5 ≈ 1.9 nodes are in repair on average (Poisson), and P(≤ 2) ≈ 0.71 — two spares are insufficient on ≈ 29 % of days even before any return-to-service delay |
| P8 | F4 + F5 overlap | Link fault during scheduler outage | Drain pending 16,560 → 17,400 s; mitigation 900 s after F5 | Control-plane outages convert small faults into long ones |
| P9 | `backlog_candidates.csv` | The score ignores the capacity cost of spares and the toil cost of noisy alerts | RB-05 ranks first by score (12,000) but 2 more spares reserve 2 × 8 × 8,760 = 140,160 GPU-h/yr; RB-06 scores 0 but removes ~28 false pages per day | Formulas are inputs to judgment, not substitutes for it |

## 3. Expected numbers

| Item | Expected | Class |
|---|---|---|
| Default rules, fault-free 6 h | 7 alerts, all `JobStalled` | SIMULATED |
| Reference rules, fault-free 6 h | 0 alerts | SIMULATED |
| Canonical detection (reference rules) | node_loss 70 s, link_down 40 s, scheduler_outage 70 s, storage_slow 70 s (fault at 5,000 s; next scrape 5,010 s) | SIMULATED |
| Recorded day detection (default rules) | F1 30 s, F2 none, F3 25 s, F4 none, F5 30 s | SIMULATED |
| Recorded day lost GPU-h | F1 94.4 (45.5 work + 49.0 idle); F2 0; F3 167.8 (103.0 + 64.8); F4 0; F5 ≥ 307.9 (35.3 + 272.7, truncated at horizon); total 570.1 | SIMULATED |
| Recorded day recovery | F1 903.5 s; F3 1,203.8 s; F5 never; F2/F4 recover at rollback (3,600 s / 1,200 s) | SIMULATED |
| Re-run of recorded plan with reference rules | F2 detected 60 s, F4 detected 60 s; lost GPU-h unchanged (alerts alone do not shorten recovery) | SIMULATED |
| Single node loss (S1) | 110.3 GPU-h; with `fast_fail=True` 81.5 GPU-h — saving 28.8 GPU-h, matching the model (600 − 60) × 192 / 3600 | SIMULATED vs MODELED |
| Recorded plan with `fast_fail=True` | total 474.3 GPU-h (F1 65.6, F3 72.5, F5 ≥ 336.2). Not a clean comparison: the whole trajectory (checkpoint phase at each fault) shifts — students who notice and use single-fault scenarios for attribution deserve credit | SIMULATED |
| Backlog order | RB-01 (safety), RB-05 12,000, RB-04 4,500, RB-03 1,972.8 (137 interruptions/yr from the canonical MTBF), RB-02 1,200, RB-06 0 | MODELED |

Arithmetic for P5: lost work = 192 GPUs × 111 steps × 17.4 s / 3600 = 103.0 GPU-h; naive
(525 − 517 = 8 steps) = 192 × 8 × 17.4 / 3600 = 7.4 GPU-h. Arithmetic for F1 idle:
(3,603.464 − 2,685.461) s × 192 / 3600 = 49.0 GPU-h. Restart overhead in the simulator: 600 s
timeout + 280 s launch/warm-up + 6.1 s load + one step ≈ 903 s ≈ 15 min, the canonical value in
REFERENCE_CLUSTER.md.

## 4. Rubric interpretation (100 points; see ../../RUBRIC.md)

| Dimension | Weight | 9–10 | 7–8 | 5–6 | < 5 |
|---|---|---|---|---|---|
| Problem framing and assumptions | 10 | Dated hypotheses with numbers; simulator parameters listed with sources; safety scope explicit | Hypotheses qualitative | Hypotheses written after the run | None |
| Architecture and technical correctness | 20 | Correct causal chains (hang → timeout → requeue → durable restore); absence + cause + symptom alerting; explains P5–P8 mechanisms | Mostly correct, one mechanism wrong | Treats alerts as the recovery mechanism | Wrong model |
| Implementation / reproducibility | 15 | 11/11; one command reproduces every table; what-if runs scripted | 11/11 | 8–10/11 | < 8 |
| Measurement and analysis | 20 | Per-fault metrics with lower-bound handling; durable-vs-started; single-fault attribution of fixes; expected vs observed table | Metrics right, little attribution | Totals only | Unlabelled or wrong |
| Reliability, security and operations | 15 | Real abort/rollback steps; runbook changes; who may inject and how injections are audited; protected scope respected | Generic safety | Thin | Unsafe plan |
| Troubleshooting and engineering judgment | 10 | Finds P7 root cause (spares + no return-to-service), critiques P9 formula | Finds P7 symptom only | Accepts formula ranking | — |
| Communication and portfolio quality | 10 | Blameless postmortem a VP can read; timeline annotated | Clear but long | Blame language | — |

Pass ≥ 70 with ≥ 10/20 in both *Architecture and technical correctness* and *Measurement and
analysis*. Distinction ≥ 90 with reproducible evidence.

## 5. Common failure patterns

1. **Hypotheses written after the run.** Check commit history; without dated predictions the game
   day is a demo, not an experiment. Cap Problem framing at 6.
2. **Restoring from `ckpt_started`.** The checker catches ≈ 7 GPU-h for F3 with a specific message.
3. **Averaging MTTR over unrecovered faults** (or dropping them). F5 must be reported as unrecovered
   with a lower-bound loss.
4. **"Fix" for P1 that removes the stall rule entirely.** Then a hang is detected only by the
   collective timeout; T2 still passes via NodeDown/NicLinkDown, so probe in the oral review.
5. **Blaming the injected faults for F5.** The link recovered at 17,100 s; the job stayed down
   because no spare remained and drained nodes never return. Root cause is systemic.
6. **Accepting RB-05 as top priority without its capacity cost.** Expect P9 arithmetic.
7. **Fault plan that touches rack-08.** The checker rejects it; in the report, this is a safety finding.
8. **Postmortem with names.** Mark down under Communication; blameless means systems and decisions.
9. **Comparing what-if totals across shifted trajectories** without noting the confound.
10. **No statement of what the simulator does not capture.** Required by the style guide.

## 6. Oral review questions

1. Your stall alert fires at 120 s, but the job does not fail until 600 s. What would you change
   in the platform — not the alerting — and what is the risk of that change?
2. Why did adding alerts for F2 and F4 not reduce lost GPU-hours on the recorded day? What would?
3. Explain to a training engineer why their "checkpoint every 30 minutes" did not bound lost work
   at 30 minutes during F3.
4. Propose a return-to-service policy for drained nodes whose fault cleared. What evidence must the
   node produce first (Capstone E acceptance)?
5. You run the same plan in a real lab and the job fails at 300 s, not 600 s. List three reasons
   and how you would tell them apart.
6. Which fault in your plan carries the most risk in a real lab, and what is its abort condition?
