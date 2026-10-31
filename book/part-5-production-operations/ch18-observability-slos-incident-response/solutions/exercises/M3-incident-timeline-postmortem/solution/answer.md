# M3 — INC-2291 timeline and blameless postmortem (model answer)

**Timeline** `[SIMULATED]`, from machine evidence first (`job_steps.csv`, `events.jsonl`):

| Time (UTC, 2026-10-12) | Milestone | Evidence |
|---|---|---|
| 01:30 | CHG-4468 Grafana upgrade (monitoring only) | change record |
| 01:40–02:40 | FAC-0912 CRAH-3 maintenance, row B; orion-n08 heats from 01:45; `GPUTempHigh` ticket 01:53 | events, node metrics |
| 02:08–02:12 | CHG-4471 raises ECN marking thresholds on all eight rail leaves | change record |
| **02:10** | **Onset**: both jobs > 1.10 × baseline, sustained | step records |
| 02:19 | (Would-be) goodput alert fires; no such rule deployed | lab Task 3 |
| **02:58** | **Detection**: researcher reports slowness in chat | chat |
| **03:12** | **Declared** SEV2, IC assigned | incident bot |
| 04:02–04:08 | CHG-4471-RB rollback | change record |
| **04:08:12** | **Mitigated**: rollback complete, SLI recovering (within 1.05 × from 04:07) | change + SLI |
| **04:30** | **Resolved**: all-clear criteria met | incident bot |

TTD = 02:58 − 02:10 = **48.0 min**; TTM = 04:08:12 − 02:10 = **118.2 min**; TTR = 04:30 − 02:10 =
**140.0 min**.

**Postmortem (abridged).** *INC-2291 — Cluster-wide training throughput regression after fabric QoS
change.* SEV2. Owner: fabric-oncall.
- *Summary:* from 02:10 to 04:07 both training jobs ran 15–18 % slower after CHG-4471 raised ECN
  marking thresholds on all eight rail leaves; queues reached PFC thresholds before senders received
  congestion notifications, and the lossless class fell back to pausing. Rollback restored performance.
- *Impact:* 62.4 GPU-hours lost `[MODELED from step records]` (43.76 trn-70b + 18.66 ft-13b);
  trn-70b throughput SLI 0.678 over 6 h, ≈ 27 % of its monthly budget; inference unaffected.
- *Detection:* TTD 48 min, by a researcher; no alert covered training throughput (missing);
  `GPUUtilLow` paged 63 times on idle inference nodes (noisy).
- *Root cause and trigger:* CHG-4471; contributing factors: post-checks verified interfaces, BGP, and
  discards but not RoCE performance; fleet-wide rather than rail-by-rail rollout; no training-SLO alert.
- *Rejected hypotheses:* FAC-0912 thermal: heating began 25 min before onset, clocks and SM activity on
  n08 normal, and ft-13b (n17..n24, no n08) regressed at the same minute; CHG-4468: scope monitoring
  only. Spine PFC RX × ≈ 105 is propagation, not origin.
- *Action items:* (detect) `TrainingThroughputFastBurn`, training-infra, P1, 2026-10-19; (detect)
  convert `GPUUtilLow` to an allocated-idle ticket, SRE, P2; (prevent) single-leaf canary with an
  `all_reduce_perf` gate for QoS changes, fabric, P1; (prevent) PFC/ECN rate-delta post-checks,
  netauto, P1; (mitigate) one-command QoS profile rollback, netauto, P2; (detect) change annotations
  from netauto on the fleet dashboard, SRE, P3.

The lab checks verify the correlation (T4) and the timeline and rendering (T5).
