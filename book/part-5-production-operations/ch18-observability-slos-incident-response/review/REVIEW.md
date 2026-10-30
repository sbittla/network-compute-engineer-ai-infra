# Editorial Review — Chapter 18

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.08 | Fail (D1, D9 < 9.0 or near) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal) |
| I-1 | 2026-10-30 | Independent reviewer, iteration 1 | 9.23 | Fail |
| I-2 | 2026-10-30 | Independent reviewer, iteration 2 | 9.50 | Pass |
| 3 | 2026-10-30 | Author fixes for iteration-2 findings | see below | Submitted |

## Scores by dimension (latest)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy | 20 % | 8.5 | 9.5 | DCGM field names, gNMI modes, burn-rate math, and PFC quanta checked; clock-event naming aligned with docs/VERIFIED_FACTS.md; the troubleshooting scenario's clock/throughput arithmetic is now self-consistent. Version-sensitive names labelled. |
| D2 | Depth and production realism | 15 % | 9.5 | 9.5 | GPU_UTIL vs SM_ACTIVE mechanism, ECN→PFC regression, straggler-is-busier insight, alert hygiene, incident roles with ORION severities. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | Worked example walks all nine steps of the diagnostic loop with arithmetic; two figures; dashboard hierarchy table doubles as mock-up spec. |
| D4 | Lab quality | 15 % | 9.0 | 9.5 | 14 checks; planted noisy/missing alerts and red herrings; no-generator SKIP; validate_labs OK in all columns; L2/L3 commands real. |
| D5 | Exercises and assessment | 10 % | 9.5 | 9.5 | Full standard set + M1–M3 + deliverable; key with arithmetic and marking. |
| D6 | Measurement rigor / labels | 10 % | 9.5 | 9.5 | Every number labelled SIMULATED/MODELED/ILLUSTRATIVE/VENDOR-SPEC; lab-vs-hand burn-rate difference explained. |
| D7 | Cross-layer integration | 5 % | 9.0 | 9.5 | Canonical names (orion-nNN, orion-be-leaf-rR, orion-be-spine-S); links to Ch 9, 12, 14, 15, 17, 19–22. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Runbook with read-only steps, thresholds, safety callout. |
| D9 | Editorial polish | 5 % | 8.5 | 9.5 | Manuscript trimmed to 9,999 words; Mermaid labels fixed; acronyms defined. |

Weighted: iteration 1 = 0.20×8.5 + 0.15×9.5 + 0.15×9.0 + 0.15×9.0 + 0.10×9.5 + 0.10×9.5 + 0.05×(9.0 + 9.5 + 8.5) = 9.08; iteration 2 = 9.50 (all dimensions 9.5; none < 9.0).

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | §18.14 | Original scenario showed power-brake clocks at ≈ 1,005 MHz (≈ 51 %) yet only a 12 % slowdown — physically inconsistent. | Rewritten as a PSU-driven power-limit cap (SW Power Cap, ≈ 1,670 MHz) with the step-time arithmetic and SM-activity numbers derived; vendor note on platform-specific behaviour. |
| F2 | Major | Whole package | Node/switch names did not follow the new canonical names. | Renamed to orion-n01..n32, orion-be-leaf-r0..r7, orion-be-spine-1..4 in manuscript, lab data, checker, key. |
| F3 | Major | §18.3 table | DCGM clock-reason field named with the deprecated name first. | Uses `DCGM_FI_DEV_CLOCKS_EVENT_REASONS` (formerly …THROTTLE…), `clocks_event_reasons.*`. |
| F4 | Minor | §18.14 | Restart cost used 10 min. | Canonical 15 min (900 s); decision arithmetic recomputed (64 GPU-h; saves ≈ 240 GPU-h). |
| F5 | Major | lab/check.py | Reproducibility check failed when tools/ is stripped for students. | Reports SKIP and still exits 0; README/file map mark generator "instructor copy only". |
| F6 | Minor | manuscript | 10,408 words (> 10,000). | Trimmed to 9,999. |
| F7 | Minor | Figure 18.1 | Mermaid labels used literal `\n`. | Replaced with `<br/>`. |

## Release-gate items outstanding

- External review by a practising GPU-cluster SRE (alert rules, DCGM profiling-field availability on
  current dcgm-exporter releases).
- Verify vendor-native PFC/ECN gNMI paths for at least two switch OSes; verify vLLM metric names at
  publication time.
- L2/L3 extensions not yet executed on hardware.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent score: 9.23 (fail). All findings resolved; labs re-validated (all four columns OK).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | §18.14 compared peers at 1,980 MHz boost | Peers at sustained ≈ 1,830 MHz; capped GPUs ≈ 1,540 MHz → 1.19×, 19.8 s, ratio 0.88; SM-active and 307 GPU-h figures re-derived and consistent |
| R-02 | Major | "Requeued onto a spare node" — ORION has none | Inference node orion-n25 borrowed through a lifecycle transition; `kubectl drain`, `scontrol update … resume`, `scontrol requeue 731842`; drain-does-not-move-job stated |
| R-03 | Major | Completion and availability SLOs unachievable under the canon | Completion SLI redefined as recovery within 30 min (e^(−24/96) = 0.78 shown); availability = ≥ 25 of 32 nodes (P(≤ 7 in repair) = 0.996 vs P(≤ 1) = 0.29) |
| R-04 | Minor | p50_10m lag ignored | Burn-rate page now ≈ 15–17 min after onset; 5-min median alternative; summary updated |
| R-05 | Minor | PSU story vs N+1 PSUs | Platform policy (cap at 450 W on lost redundancy) stated; query uses `power.limit,enforced.power.limit,power.default_limit,clocks_event_reasons.sw_power_cap` |
| R-06 | Minor | Thermal red-herring timeline inconsistent | One timeline (01:40 / 01:44:48 / 01:45 / 01:53 / 02:10) in manuscript, key, and events.jsonl (n07 typo fixed) |
| R-07 | Minor | Lab README cited "18.L2" | Now cites Exercise M1 |
| R-08 | Minor | DCGM series have no job_id | Recording rule uses `* on (Hostname, gpu) group_left(job_id) slurm_gpu_job_info` |
| R-09 | Minor | K3 0.7 h restart unlabeled | Labelled as variation; canonical 0.25 h result added |
| R-10 | Minor | "18 % slower" ambiguous | Defined once: throughput −18 % = step time +22 % |
| R-11 | Minor | Xid latch; burn saturation | `DCGM_FI_DEV_XID_ERRORS` latch/app-Xid note; max burn 1/(1 − SLO) = 20 at 95 % explained |

Author re-score after fixes: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.5 → 9.50.
Manuscript 9,999 words.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score history: 9.23 → 9.50.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Minor | Availability SLO (≥ 25 nodes) used ≈ 85 % of budget on repair alone | ≥ 24 of 32 nodes, P(≤ 8) = 0.9989; arithmetic shown; key M1 updated |
| R2-02 | Minor | Join needs `Hostname` on `slurm_gpu_job_info` | Example label added; prolog-writes-Hostname or relabel `instance` stated |
| R2-03 | Minor | `state=resume` does not change partitions | Node must already be in the training partition (`slurm.conf` / `scontrol update PartitionName=…`) |
