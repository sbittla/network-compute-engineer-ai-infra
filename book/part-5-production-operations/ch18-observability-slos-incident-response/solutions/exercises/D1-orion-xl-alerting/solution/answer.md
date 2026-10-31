# D1 — Alerting for ORION-XL on one rotation

**Page set (≤ 8 rules)** `[ILLUSTRATIVE thresholds]`

| # | Rule | SLI or cause | Windows / threshold | Route |
|---|---|---|---|---|
| 1 | `TrainingThroughputFastBurn` (per job, grouped by cluster) | Throughput SLI, 99 % | 1 h and 5 m burn > 14.4 (ratio < 0.909; 1.05 for ≥ 1,024 GPUs, W2), `for: 2m` | training-infra primary, SRE secondary |
| 2 | `FleetTrainingRegression` | ≥ 3 jobs or ≥ 25 % of allocated GPUs burning at once | same windows | SRE + fabric; **inhibits rule 1** |
| 3–5 | `<service>AvailabilityFastBurn` / `TTFTFastBurn`, one per inference service | Availability 99.9 %, TTFT 95 % | 1 h/5 m > 14.4 or 6 h/30 m > 6 | inference |
| 6 | `GPUXidCritical` | Xid codes that guarantee job failure, on GPUs in running jobs | any, hardware codes only (Chapter 19 list) | fleet |
| 7 | `LosslessClassDiscards` | discards > 0 on the lossless class, any backend switch | 5 m | fabric |
| 8 | `CheckpointFailing` | no successful checkpoint in 2 × interval, jobs ≥ 512 GPUs | — | training-infra |

**Tickets (business hours):** correctable ECC rising; optic RX power drifting; node hot with normal
clocks; allocated-but-idle GPUs; power limit below default; slow-burn (3 d / 6 h) budget alerts.

**Which causes may page.** Only imminent-risk causes whose symptom would arrive too late or whose
damage is irreversible: a job-killing Xid, any discard on a lossless class (fabric-wide RoCE
degradation), failing checkpoints (RPO growing). Everything else pages through its SLO symptom.

**Preventing 40 pages for one fabric incident.** Alertmanager `group_by: [cluster, alertname]` with a
`group_wait` of ≈ 1 min collects per-job firings; rule 2 detects the shared-cause pattern and an
inhibit rule (`source: FleetTrainingRegression`, `target: TrainingThroughputFastBurn`, `equal:
[cluster]`) suppresses per-job pages; one notification lists the affected jobs.

**Estimated load** `[ILLUSTRATIVE assumptions]`: 12 h shifts → 60 shifts per 30 days. Training: 40 jobs
× 0.5 burn-pages per job-month = 20/month → 20 / 60 = **0.33 per shift** (fleet incidents count once,
thanks to grouping). Inference: 3 services × 6 pages/month = 18/month → **0.30 per shift**. Total ≈
**0.63 per shift**, well inside the budget of 2, leaving headroom for cause pages (rules 6–8). Without
grouping, a single fabric incident would produce up to 40 pages, 20× the shift budget.

`solve.py` reproduces the load estimate.
