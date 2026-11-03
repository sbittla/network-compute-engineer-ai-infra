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

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.5, D5 9.0, D6 9.5, D7 9.5, D8 9.5, D9 9.0 → **9.33** (fail).
Checker at review time: solution 14/14, starter 1/14.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N18-01 | Major | T1: `OOMKilled`/137 is a host-memory cgroup kill, but the key cited `FB_USED` 79.1/79.6 GiB (normal vLLM pre-allocation) as corroboration | Option (a): DEP-44 now also raises `--swap-space` 4 → 8 GiB/GPU (× TP 8 = 64 GiB pinned host memory vs a 64 GiB pod limit); evidence adds `container_memory_working_set_bytes` 63.9/64 GiB and a stalled rollout (1 of 8 updated); `FB_USED` 73–74 GiB on all replicas is kept as a distractor and the key explains why it is normal (≈ 0.92 × 79.6) and that a CUDA OOM exits 1, not 137. exercises.md, folder README (prompt sync), key, answer.md, meta.yaml and marking.json updated |
| N18-02 | Minor | GPU_UTIL_RATIO attributed to DCGM 4.6 | Caption: 4.6 = profiling renames; 4.7 = `GPU_UTIL` (203) → `GPU_UTIL_RATIO` (1613) |
| N18-03 | Minor | Flight recorder used only the legacy env var | `TORCH_FR_BUFFER_SIZE` (legacy `TORCH_NCCL_TRACE_BUFFER_SIZE`), `TORCH_NCCL_DUMP_ON_TIMEOUT=1`, `TORCH_FR_DUMP_TEMP_FILE` |
| N18-04 | Minor | Garbled red-herring sentence in §18.12 Step 8 | Split: CRAH/n08 (clocks never throttled); Grafana CHG-4468 monitoring-only |
| N18-05 | Minor | "≈ 30× larger" at ORION-XL | ≈ 21× (4,096 / 192 GPUs) |
| N18-06 | Minor | Summary "10–17 min" | ≈ 13–17 min |
| N18-07 | Minor | $3/GPU-hour vs book's $2.50 | Canonical $2.50 `[ILLUSTRATIVE]` everywhere: §18.1 92 GPU-h ≈ $230; §18.12 62.4 GPU-h ≈ $156; W2 $5,605 / $604, saving ≈ $5,000 (prompt, key, answer, meta, solve.py re-run). False claim "Chapter 21 derives ORION's figure" replaced |
| N18-08 | Minor | §18.14 hot handover (`kubectl drain` then `scontrol … resume`) | Replaced with an `[ILLUSTRATIVE]` lifecycle-controller pool move; controller drains, validates and issues the Slurm RESUME (Sections 17.5.5, 17.7) |
| N18-09 | Minor | 30-min peak 9.8 vs hand 9.5 | "(request-weighted, from the data; ≈ 9.5 by hand)" |
| D2 advice | — | Telemetry-pipeline failures as first-class alerts | New §18.8 subsection "Alerting on the telemetry pipeline itself": `up`, `absent_over_time`, join-breakage count, `resets()`, gNMI staleness |
| D4 advice | — | Exercise a missing-scrape case | New check "T2 scrape gap": `burn_rate()` must return NaN across a 3-minute gap (contiguity mask), equal values after it; solution/starter updated; checker now 15/15 (solution), 1/15 (starter); L1 lab_checks and golden outputs regenerated |
| D9 advice | — | Very long acronym paragraph | Regrouped into a four-line list by layer |

Validation: `check.py --impl solution` 15/15 exit 0; `--impl starter` 1/15 exit 1 (graceful TODO);
`validate_labs.py ch18` OK (all four columns); package test suite 86 passed; `copyedit_lint.py` 0 findings
for ch18. L2 committed results untouched (the contiguity-masked `burn_rate` gives identical values on
contiguous scrapes).

---

## Independent review r2 (2026-11-01)

Reviewer scores (independent, after the r1 fixes):

| Dim | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|---|
| Score | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.0 | **9.48 (FAIL)** |

0 blocker, 0 major, 7 minor. Checker at review time: solution 15/15, starter 1/15.

| ID | Finding | Resolution |
|---|---|---|
| Price (coordinator) | Canonical price corrected to ≈ $3.00/GPU-h | Every $2.50 is now $3.00 `[ILLUSTRATIVE]`, cited as rounded from Chapter 21's owned-cluster TCO of $3.02 per nominal GPU-hour `[MODELED]`. Recomputed: §18.1 92 GPU-h ≈ $276; §18.12 62.4 GPU-h ≈ $187; W2 2,242 GPU-h ≈ $6,726 and 241 GPU-h ≈ $724, saving ≈ $6,000. Updated in the manuscript, exercises.md, the W2 folder README, key, answer.md, meta.yaml and solve.py; outputs regenerated. |
| R18-01 | Per-token "TPOT" SLI conflated with ITL | Table 18.4 now counts requests whose TPOT (per-request mean) ≤ 50 ms over successful requests, with ITL p99 tracked beside it. The M1 answer is updated to match. |
| R18-02 | §18.14 said n25 is defined in `train`, contradicting Ch17 | Replaced with the REFERENCE_CLUSTER model: 24 training (n01–n24) + 8 inference (n25–n32). Lending a node, like the full W-TRAIN run, is a lifecycle transition, and joining `train` is part of it (Section 17.7). The text no longer claims a particular partition definition. |
| R18-03 | Epigraph said 128 GPUs, §18.1 computes 256 | Epigraph now reads "A 256-GPU training job". |
| R18-04 | Runbook SEV2 criterion differed from Table 18.8 | Runbook now declares SEV2 on the Table 18.8 criteria and quotes them. |
| R18-05 | CRAH, LLDP, PSU, WRED, XOFF undefined | Added to the acronym block. |
| R18-06 | L2 degraded phase lowers GPU_UTIL, apparently contradicting §18.3 | Lab README now explains it: a host-side stall leaves no kernel resident, so GPU_UTIL falls (64 % in the committed run); an NCCL wait keeps one resident, and the busy-idle phase reproduces that case. Measured results are untouched. |
| R18-07 | `--swap-space` is a V0 concept | T1 evidence (exercises.md and folder README) now states a V0-engine release. Key and answer.md explain that the lesson is version-neutral, because any host-memory increase gives the same OOMKilled/137 signature. |
| D2 advice | Profiling multiplexing and profiler conflicts | New paragraph after Table 18.10: counter multiplexing, the Nsight conflict (`dcgmi profile --pause`/`--resume`), and 1 s collection bounded to the job's nodes and a window. |
| D3 advice | Time-series sketch of INC-2291 | New Figure 18.3: an event timeline with step time, leaf PFC, changes and alerts. CHG-4468 at 01:30 and FAC-0912 at 01:40 are checked against `events.jsonl`. |
| D5 advice | R1–R4 point allocations | Five-point marking added to each. |
| D6 advice | Sources for the power split and the 1.2 % noise | The power split is labelled as teaching values for the bundle. The 1.2 % is labelled `[SIMULATED]`, a bundle property; recomputed from `job_steps.csv` as 1.27 % for trn-70b and 1.20 % for ft-13b. |

Tests: `check.py --impl solution` 15/15 (exit 0); `--impl starter` 1/15 (exit 1); `validate_labs.py ch18` OK; package test suite 86 passed; `copyedit_lint.py` reports 0 findings in ch18. Manuscript is 1,079 lines (was 1,050). Awaiting independent re-review.

### r2 re-score fixes (2026-11-03)

| ID | Finding | Resolution |
|---|---|---|
| R18-08 | The $3.00/GPU-hour price was labelled `[ILLUSTRATIVE]` although it is the Chapter 21 TCO | Relabelled `[MODELED]` (Chapter 21 owned-cluster TCO $3.02, rounded) in the manuscript, exercises.md and folder prompts, key, answers, meta.yaml and solve.py comments; outputs regenerated. Tests: check.py solution/starter as before, `validate_labs.py` OK, package tests pass, `copyedit_lint.py` 0 findings. |
