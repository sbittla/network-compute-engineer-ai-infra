# Chapter 18 — Exercise Answer Key (INSTRUCTORS ONLY)

All numbers below were computed twice (by hand and with the reference implementation where
applicable). Labels follow the style guide: `[MODELED]` for formula results, `[SIMULATED]` for values
taken from the synthetic lab bundle.

---

## Knowledge checks

**K1.** `DCGM_FI_DEV_GPU_UTIL` is time-occupancy: the fraction of the sample period during which at
least one kernel was executing, regardless of how many SMs it used or whether it did math. NCCL
collectives run as kernels that occupy a few SMs and poll for incoming data; when the network stalls,
those kernels stay resident longer, so occupancy remains ≈ 95–100 %. Signals that reveal the stall:
`DCGM_FI_PROF_SM_ACTIVE` (falls in proportion to the stall), `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` (tensor
math stops while waiting), `DCGM_FI_DEV_POWER_USAGE` (spinning kernels draw little), and outside DCGM
the job's own step time / tokens per second.
*Marking:* 2 pts definition, 1 pt NCCL mechanism, 1 pt per valid signal (max 3). Common mistake:
saying "GPU_UTIL is averaged over SMs" — it is not.

**K2.** (a) 2³² B = 4,294,967,296 B; 400 Gb/s = 50 × 10⁹ B/s; 4.295 × 10⁹ / 50 × 10⁹ = 0.086 s — the
counter wraps ≈ 11.6 times per second. (b) burst = 50 × 10⁹ B/s × 0.002 s = 100 MB; poll capacity =
50 × 10⁹ × 60 = 3 × 10¹² B; 1 × 10⁸ / 3 × 10¹² = 3.3 × 10⁻⁵ = 0.0033 % utilization. (c) 65,535 quanta
× 512 bit = 33,553,920 bit; / 400 × 10⁹ b/s = 83.9 µs.
*Marking:* 1 pt each for formula, substitution, result with units. Common mistake: using 400 GB/s.

**K3.** Throughput SLI = job-minutes with median step time ≤ 1.10 × baseline / running job-minutes.
Goodput SLI = accelerator time producing retained progress / allocated accelerator time. Example: a job
allocated 168 h in a week runs at full speed whenever it runs (throughput SLI 100 %) but crashes every
6 h (28 times) with hourly checkpoints. Each crash loses on average 0.5 h of work since the last
checkpoint plus 0.7 h to restart and reload — a deliberate variation; the canonical ORION restart is
0.25 h — = 1.2 h; 28 × 1.2 = 33.6 h lost; goodput = (168 − 33.6) / 168 = 0.80 `[MODELED]`. (With the
canonical 0.25 h: 28 × 0.75 = 21 h lost, goodput 0.875.)
*Marking:* 2 pts definitions; 2 pts a numerically consistent example. Accept any example reaching
80 % with correct arithmetic.

**K4.** The long window (e.g. 1 h at burn 14.4) prevents paging on short blips that consume a trivial
fraction of the budget — e.g. Lab 18's 7-minute deploy at 4 % errors gives a 5-minute burn of 40 but a
1 h burn of only 4.65. The short window (5 min) prevents a long-window alert from continuing to fire
(or firing late) after the problem is fixed — without it, a 1 h window stays above threshold for up to
an hour after a rollback, and a problem that started 50 minutes ago and stopped 10 minutes ago would
page now.
*Marking:* 2 pts each scenario.

**K5.** Host A (`rx_prio3_pause` rising): it *receives* pause frames — the switch is pausing this host's
transmissions on the lossless class, so the bottleneck is downstream (switch egress congestion or a
slow receiver elsewhere); host A is a victim. Host B (`tx_prio3_pause` rising): it *sends* pauses — its
own receive path cannot drain (PCIe, memory bandwidth, slow consumer, receive-buffer exhaustion), and it
is spreading backpressure into the fabric; it is a likely culprit. Check B's `out_of_buffer`, PCIe
counters, and CPU/IRQ placement.
*Marking:* 2 pts each; −1 if directions are reversed for one host.

**K6.** The IC must keep a global view — priorities, roles, decisions, stakeholder needs — which hands-on
debugging destroys (tunnel vision); and decisions such as "roll back now" need someone not invested in
their own hypothesis. For SEV2 the comms lead publishes every 60 minutes: impact, scope, current
status, next update time — never speculative cause. Example: "03:20 UTC — Both training jobs ~15–20 %
slower since ~02:12. Inference unaffected. Fabric and Training Infra investigating. Next update 04:20."
*Marking:* 2 + 1 + 1.

**K7.** TTD = detection − onset; TTM = mitigation (user impact stopped) − onset; TTR = resolution
(all-clear) − onset. Human reports lag onset by the time users take to notice and decide to complain
(48 min in INC-2291), so a human-reported onset understates TTD and impact, and hides the alerting gap
the postmortem must fix.

**K8.** Each unique label value creates a new series; unbounded labels explode memory and index size
and make queries slow. Steps per day = 86,400 / 17.4 = 4,966; series = 4,096 ranks × 4,966 steps ≈
20.3 million new series per day `[MODELED]` — enough to destabilise a Prometheus server in hours. Put
per-rank, per-step data in logs or a trace/flight-recorder store; export only aggregates (histogram by
`job_id`).
*Marking:* 2 pts reason, 2 pts arithmetic, 1 pt correct home for the data.

## Worked problems

**W1.**
(a) Requests per 30 days = 3,000 × 43,200 = 129.6 × 10⁶. Budget = 0.001 × 129.6 × 10⁶ = 129,600 failed
requests ≡ 0.001 × 43,200 = 43.2 minutes of total outage.
(b) Burn = 0.006 / 0.001 = 6. Budget consumed = 6 × 90 / 43,200 = 0.0125 = 1.25 % (check: 0.006 × 3,000 ×
90 = 1,620 failures; 1,620 / 129,600 = 1.25 %). Alert conditions at t = 90 min:
- Page (1 h > 14.4 and 5 m > 14.4): 1 h burn = 6 → **no**.
- Page (6 h > 6 and 30 m > 6): 30 m burn = 6, *not* > 6; 6 h burn = 0.006 × 90 / 360 / 0.001 = 1.5 →
  **no**.
- Ticket (3 d > 1 and 6 h > 1): 6 h = 1.5 > 1 but 3 d = 0.006 × 90 / 4,320 / 0.001 = 0.125 → **no**.
Nothing fires, by design: a 1.25 % budget spend does not justify waking anyone.
(c) Burn = 0.02 / 0.001 = 20. 1 h window exceeds 1.44 % when 0.02 × t / 60 > 0.0144 → t > 43.2 min; the
5 m window exceeds it after 3.6 min. Condition true from 43.2 min; with `for: 2m` the page fires at
≈ 45 min (plus up to one evaluation interval). The 6 h/30 m pair needs 0.02 × t / 360 > 0.006 → t > 108
min, after the incident ends. Budget consumed in 90 min = 20 × 90 / 43,200 = 4.17 %.
(d) 30 days / 6 = 5 days (120 h).
*Marking:* (a) 2, (b) 4, (c) 3, (d) 1. Common mistakes: forgetting that the long window dilutes errors
over its whole length; treating "= threshold" as firing.

**W2.**
(a) Ratio = 17.4 / 19.0 = 0.916; lost fraction = 1 − 0.916 = 0.084 (8.4 %).
(b) Case A: 6.5 h × 4,096 × 0.0842 = 2,242 GPU-h → $6,730. Case B: (12 + 30) min = 0.7 h; 0.7 × 4,096 ×
0.0842 = 241 GPU-h → $724. Detection saves ≈ 2,000 GPU-h ≈ $6,000 per incident `[MODELED]`.
(c) 19.0 / 17.4 = 1.092 < 1.10 → the rule does **not** fire. For jobs ≥ 1,024 GPUs a 1.05 threshold is
defensible: in Lab 18 the step-time noise is ≈ 1.2 % (sd); a 10-minute rolling median over ≈ 34 steps
has sd ≈ 1.25 × 1.2 % / √34 ≈ 0.26 %, so 5 % is ≈ 19 sd away. Evidence needed before adopting it: two or
more weeks of rolling-median ratios per large job (including checkpoint, evaluation, and data-shard
boundaries) showing a false-positive rate below the page budget, plus a check that legitimate
configuration changes reset the baseline.
*Marking:* (a) 2, (b) 4, (c) 4 (threshold 1, noise argument 2, evidence plan 1). Accept 1.03–1.07 with
a sound noise argument.

## Hands-on lab (L1) — reference results

Reference values from `solutions/lab/telemetry_analysis.py` `[SIMULATED]`:

| Quantity | Value |
|---|---|
| Baseline step time trn-70b / ft-13b (00:00–02:00, non-checkpoint median) | 17.389 s / 5.998 s |
| Plateau median (02:20–04:00) | 21.24 s / 7.09 s |
| Onset / recovery (both jobs) | 02:10 / 04:07 |
| Training SLI trn-70b / ft-13b (6 h) | 0.678 / 0.681 |
| Lost GPU-hours onset → recovery | 43.76 + 18.66 = 62.4 |
| Availability burn at 05:16: 5 m / 1 h; max 30 m / 6 h | 40.0 / 4.65; 9.78 / 0.95 |
| TTFT-SLO burn max 5 m | 2.4 |
| `GPUUtilLow` firings | 63 (all on orion-n25..n32), verdict noisy |
| `GPUTempHigh` | 1 firing, orion-n08, 01:53–02:35 |
| Goodput alert first firing | 02:19 both jobs |
| Fabric shift (02:30–03:30 vs 01:00–02:00) | leaf PFC TX × 91–98, ECN × 0.03; spine PFC RX × 104–107 |
| Trigger | CHG-4471; rejected FAC-0912 (does not cover ft-13b), CHG-4468 (monitoring only) |
| Timeline | onset 02:10, detected 02:58, declared 03:12, mitigated 04:08:12, resolved 04:30; TTD 48.0, TTM 118.2, TTR 140.0 min |

### Lab 18 — planted anomalies (do not distribute)

1. **Red herring — thermal.** One timeline: FAC-0912 (CRAH-3 maintenance in row B) starts 01:40; the BMC
   on orion-n08 logs an inlet-temperature warning at 01:44:48; the GPUs heat from 01:45 to 86–88 °C;
   `GPUTempHigh` correctly raises a *ticket* at 01:53 (> 85 °C for 5 min); FAC-0912 completes 02:40. It
   is not the cause: heating began 25 min (the alert 17 min) before the 02:10 onset; clocks and SM
   activity on orion-n08 are normal; and `ft-13b` (orion-n17..n24, no n08) regressed at the same minute.
   The incident bot's 03:28 hypothesis line in `events.jsonl` records the same rejection. Teaches scope
   reasoning.
2. **Red herring — monitoring change.** CHG-4468 (Grafana upgrade, 01:30) is in the lookback window;
   scope "monitoring" cannot affect step times.
3. **Noisy rule.** `GPUUtilLow` (page, `GPU_UTIL < 80` for 2 m) fires 63 times on the inference pool at
   normal low load and never for the training regression, because training GPU_UTIL stays ≈ 97 %.
4. **Missing rule.** No page-severity rule fires during the incident; detection is a chat message at
   02:58. The fix is a training-throughput (goodput) symptom alert.
5. **Inference blip.** DEP-41 (05:10–05:16) produces 4 % errors for 7 minutes; the multiwindow logic must
   *not* page (1 h burn 4.65 < 14.4). A learner who pages on the 5 m window alone is penalised.
6. **Checkpoint stalls.** +9 s every 30 min (trn-70b) and +4 s every 20 min (ft-13b), with GPU_UTIL dips
   to 83–89 %. They must be excluded from baselines and per-minute series (checked: max baseline-window
   minute < 18.5 s).
7. **Post-check gap.** CHG-4471's completion record says "post-checks PASS (interfaces up, BGP
   established, no discards)" — true, and irrelevant to RoCE performance. This is the key *prevent*
   action item.
8. **Silent discards rule.** `FabricOutDiscards` never fires: the lossless class pauses instead of
   dropping. Learners should not conclude "fabric healthy" from it.
9. **Consequence vs cause.** Spine PFC RX × ≈ 105 appears *after* the leaves change; it is propagation,
   not origin.

### Marking guidance (100 points, lab README Section 8)

- Tasks 1–2 (20): checker PASS = 14; explanation of checkpoint exclusion = 6 (must mention both the
  stall and the median/threshold effect).
- Task 3 (20): checker = 10; noisy-rule redesign = 5 (e.g. ticket on *allocated-but-idle* GPUs:
  `GPU_UTIL < 5` for 30 m on GPUs allocated to a job); PromQL goodput alert with `for:` justified = 5.
- Task 4 (15): checker = 7; proven-vs-correlated table = 8. "Proven" requires temporal precedence
  (leaf flips at 02:08–02:12 precede onset), scope (all affected jobs share the fabric), mechanism (ECN →
  PFC), and *intervention* evidence (rollback restores within minutes). Without the rollback evidence,
  the cause is only correlated — learners who say so earn full marks.
- Task 5 (25): timeline accuracy 6, impact with labels 5, blameless language 4, rejected hypotheses 4,
  action items 6 (≥ 5, typed, owned, dated).
- Task 6 (15): levels/questions 5, panel justification 5, drill-down keys 5.
- Reproducibility (5).

### Model postmortem excerpt (abridged)

> **INC-2291 — Cluster-wide training throughput regression after fabric QoS change.** SEV2. Owner:
> fabric-oncall. **Summary:** From 02:10 to 04:07 UTC on 2026-10-12, both training jobs on ORION ran
> 15–18 % slower after CHG-4471 raised ECN marking thresholds on all eight rail leaves; queues reached
> PFC thresholds before senders received congestion notifications, and the lossless class fell back
> to pausing. Rollback restored performance. **Impact:** 62.4 GPU-hours lost `[MODELED from step
> records]`; trn-70b throughput SLI 0.678 over the 6-hour window; inference unaffected. **Detection:**
> TTD 48 min, by a researcher; no alert covered training throughput (missing); `GPUUtilLow` paged 63
> times on idle inference nodes (noisy). **Action items:** (detect) `TrainingThroughputFastBurn` —
> training-infra, P1, 2026-10-19; (detect) convert `GPUUtilLow` to allocated-idle ticket — SRE, P2;
> (prevent) single-leaf canary with `all_reduce_perf` gate for QoS changes — fabric, P1; (prevent) add
> PFC/ECN rate-delta post-checks — netauto, P1; (mitigate) one-command QoS profile rollback — netauto, P2;
> (detect) fleet dashboard change annotations from netauto — SRE, P3.

## Troubleshooting case T1

| Rank | Hypothesis | Evidence for / against | Verdict |
|---|---|---|---|
| 1 | DEP-44 (32k context) made replica 7 run out of GPU memory; crashloop removed 1/8 of capacity; remaining replicas queue | DEP-44 at 19:52 precedes restarts (19:55→20:04) and TTFT rise; `OOMKilled`, exit 137; FB_USED 79.1 of 79.6 GiB; waiting queue 35–48 on surviving replicas; replica 7 series absent | Root cause (pending rollback confirmation) |
| 2 | Traffic surge | +2.3 % (3,050 → 3,120/min) — far too small to explain a 3× TTFT | Rejected |
| 3 | GPU hardware fault | No Xid; exit is an OOM kill, a software memory limit | Rejected |
| 4 | Fabric / storage | Both normal; TP = 8 serving does not use the backend fabric per request | Rejected |

Why TPOT is flat while TTFT explodes: TTFT includes *queueing* before prefill. With one replica down
and the others saturated, new requests wait in the scheduler queue (`num_requests_waiting` 35–48), so
TTFT grows. Requests already running decode at the normal per-token rate, so TPOT is unchanged.
(Only replica 7 crashed so far, plausibly because it was the first to receive a long enterprise
prompt; the others are at risk.)

Mitigation: roll back to rev 43 (change precedes symptom; rollback is the safest fastest action).
Validation: no new restarts for 30 min; `num_requests_waiting` < 5 on all replicas; TTFT p95 < 0.8 s;
5 m burn < 1 and the alert resolves. Follow-up: capacity model for 32k context (Chapter 15 KV-cache and
activation memory), CI check of memory headroom per max context, canary with long-prompt test traffic.
*Marking:* ranking 3, evidence citations 3, mitigation/validation 2, TTFT/TPOT explanation 2.

## Design challenge D1 — reference answer

Page set (≤ 8): (1) `TrainingThroughputFastBurn` per job, *grouped* by cluster and inhibited when (2)
fires; (2) `FleetTrainingRegression`: ≥ 3 jobs or ≥ 25 % of allocated GPUs burning simultaneously —
one page for a shared cause; (3–5) availability and TTFT fast-burn for each inference service
(multiwindow); (6) `GPUXidCritical` only for Xid codes that guarantee job failure on GPUs in running
jobs (Chapter 19 list); (7) `LosslessClassDiscards` > 0 for 5 m on any backend switch; (8)
`CheckpointFailing`: no successful checkpoint in 2 × interval for any job ≥ 512 GPUs. Tickets: correctable
ECC rising, optics RX power drifting, node temperature with normal clocks, allocated-idle GPUs,
power-limit below default. Routing: training pages → training-infra primary with SRE secondary; fabric
symptoms → fabric; Alertmanager `group_by: [cluster, alertname]` and an inhibit rule so (2) suppresses
(1). Estimated load: 40 jobs × historical 0.5 burn-pages/job-month ≈ 20/month ≈ 0.33 per shift, plus
inference ≈ 0.3 per shift → within 2 per shift `[ILLUSTRATIVE assumptions]`.
*Marking:* rule table 4, grouping/inhibition 3, load estimate 2, cause-paging justification 1.

## Reflection — guidance

- **R1:** Proven: the timing of the leaf flips, the scope covering both jobs, and recovery on rollback
  (an intervention). Correlated only: the exact ECN → PFC mechanism (no queue-depth telemetry in the
  bundle). Proof would need per-queue watermarks, pause durations, and a controlled re-application on a
  single leaf in a lab.
- **R2:** One-minute aggregates cannot show which ports or queues paused, microburst structure, or
  whether pauses formed storms; add per-port per-priority pause duration and queue watermarks at 1–10 s.
- **R3:** Baseline drift (re-baselining on a slow day), excluding too many steps as "checkpoints", jobs
  changing batch size (step time changes legitimately). Guards: baseline pinned to config hash; audit of
  exclusions; tokens/s alongside step time.
- **R4:** Signs of blamelessness: describes system conditions and decisions in context, no names
  attached to errors, contributing factors rather than a single culprit, action items on systems.

## Outline-mandated exercises

- **M1:** Model answer is Table 18.4 extended with recording rules from Sections 18.6 and 18.8.
  Required: targets that are achievable under the canon (recovery within RTO rather than "uninterrupted
  attempts": e^(−24/96) = 0.78 for 16 nodes; availability allowing ≈ 2.5 nodes in repair: ≥ 24 of 32 nodes, P(≤ 8) = 0.9989);
  training job completion/recovery SLI with an infrastructure-attribution rule; inference latency
  (TTFT and TPOT) as request/token-based ratios; cluster availability as schedulable-healthy GPU minutes;
  fabric health from probes and link-error windows. Budget arithmetic must be shown (e.g. 99.5 % ×
  30 d → 216 min). Deduct for SLIs that are component metrics (e.g. "GPU util > 90 %").
- **M2:** Model answer: Figure 18.2 + Table 18.6 + `dashboard_spec()` in the reference solution.
  Rejected-panel examples: fleet-wide average GPU_UTIL (misleading), per-port counters at fleet level
  (unreadable).
- **M3:** See the lab marking guidance and model postmortem above.
