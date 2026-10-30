# Lab 18 — Telemetry Bundle Forensics: SLIs, Burn Rates, Alerts, and a Blameless Postmortem

**Progressive Lab 8 (Observability and incident).** Tier **L1** (laptop). Evidence class: `[SIMULATED]`.

## 1. Goal and the real-world task it mirrors

At 02:58 UTC a researcher posts in `#training-help`: *"trn-70b tokens/s looks ~18 % lower than
yesterday."* Nothing paged. You are the SRE who picks up the incident afterwards with a telemetry
bundle exported from ORION's Prometheus, the switch telemetry collector, the change-management
system, and the incident bot. Your job is the work every SRE does after a quiet, expensive
regression:

1. establish baselines and find exactly when the regression started and ended;
2. compute the SLIs and error-budget burn rates that *should* have described it;
3. replay the deployed alert rules against the data — find the **noisy** rule and the **missing** one —
   and design the symptom-based alert that would have paged;
4. correlate the regression to its trigger and reject the red herrings with evidence;
5. build the incident timeline (TTD, TTM, TTR), compute lost GPU-hours, and render a blameless
   postmortem from the team template;
6. specify the dashboard hierarchy (fleet → node → device → workload) that would have made the
   diagnosis a five-minute job.

## 2. Tier and realism boundary

L1: everything runs on supplied synthetic data in < 5 s. The bundle is shaped like real exports
(DCGM-exporter fields, gNMI-style switch counters, Slurm step records, change records) but it is
**simulated**: per-node GPU fields are node averages, switch counters are pre-aggregated per switch,
and the fabric's response to the ECN-threshold change is a scripted effect, not a queueing
simulation. The lab cannot show you real scrape jitter, counter resets, missing series, cardinality
limits, or the cost of high-resolution telemetry — see the manuscript's "Realism boundaries" section.

## 3. Setup

```bash
cd book/part-5-production-operations/ch18-observability-slos-incident-response/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                           # progress on starter/telemetry_analysis.py
```

Python ≥ 3.10. No GPU, no network, no root.

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Telemetry layers and what each metric family can and cannot tell you | 18.2–18.5 |
| PromQL, recording rules, `for:` semantics | 18.6 |
| SLIs/SLOs, error budgets, multiwindow burn-rate alerts | 18.7–18.8 |
| Dashboard hierarchy | 18.9 |
| Incident command, timelines, postmortems | 18.10–18.11 |
| Worked example (same arithmetic as Tasks 1–2) | 18.12 |

## 5. Data

| File | Contents |
|---|---|
| `data/job_steps.csv` | One row per training step: `job_id`, `slurm_job_id`, `step`, `end_ts`, `step_time_s`, `tokens`, `checkpoint` (1 = step included a checkpoint stall) |
| `data/node_metrics.csv` | Per node per minute: `gpu_util_pct` (DCGM_FI_DEV_GPU_UTIL-like), `sm_active` (DCGM_FI_PROF_SM_ACTIVE-like), `power_w` (mean per GPU), `gpu_temp_c_max`, `nic_tx_gbps` (sum of 8 backend NICs), `xid_count` |
| `data/switch_metrics.csv` | Per switch per minute: `tx_util_pct`, `ecn_marked_pps`, `pfc_pause_tx_pps`, `pfc_pause_rx_pps`, `out_discards_pps` |
| `data/inference_slo.csv` | Per minute: `requests`, `ttft_over_800ms`, `errors_5xx` for the `chat-70b` service |
| `data/events.jsonl` | Change records, switch syslog, BMC/Redfish events, facilities work, chat reports, incident-bot updates |
| `data/alert_rules.yaml` | The rules that were live, with the PromQL that ran and an `eval` spec you replay offline |
| `data/postmortem_template.md` | Team template with `{{placeholders}}` |

Jobs: `trn-70b` (W-TRAIN variant, 128 GPUs on `orion-n01..n16`, TP = 8, PP = 4, DP = 4, 512 × 4,096 tokens
per step) and `ft-13b` (64 GPUs on `orion-n17..n24`). Inference pool: `orion-n25..n32` (Kubernetes).

## 6. Tasks

Implement the functions in `starter/telemetry_analysis.py` (each raises `NotImplementedError`).
Baseline window for all tasks: **00:00–02:00 UTC**.

| # | Task | Functions | Acceptance criterion (checked) |
|---|---|---|---|
| 1 | Baselines, onset, recovery | `baseline_step_time`, `step_time_per_minute`, `detect_onset`, `detect_recovery` | Baselines ≈ 17.4 s and ≈ 6.0 s; checkpoint stalls excluded; onset and recovery found for both jobs |
| 2 | SLIs and burn rates | `training_sli`, `lost_gpu_hours`, `burn_rate`, `multiwindow_fast_burn` | Training SLI ≈ 0.68; lost GPU-hours ≈ 62; 5 m / 1 h burn at 05:16 ≈ 40 / ≈ 5; the 7-minute deploy blip does **not** page; a sustained 3 % outage **does** |
| 3 | Alert replay | `evaluate_rule`, `classify_alerts`, `goodput_alert` | `GPUTempHigh` fires once on `orion-n08`; exactly one rule is classified noisy; no actionable page fired during the incident; your goodput alert fires by 02:25 and never outside the incident |
| 4 | Root cause | `fabric_shift`, `correlate_root_cause` | Trigger identified; red herrings rejected with a reason; leaf PFC/ECN shift quantified |
| 5 | Timeline and postmortem | `build_timeline`, `render_postmortem` | TTD/TTM/TTR computed; template rendered with no holes; missing facts raise |
| 6 | Dashboard spec | `dashboard_spec` | Four-level hierarchy with chained drill-downs, a burn-rate panel at fleet level, and DCGM profiling metrics at device level |

Then write the deliverables (Section 8) by hand — the checker verifies your numbers, not your
judgement.

## 7. Running the checker

```bash
python check.py                    # your starter implementation; TODO lines show what is left
python check.py --impl solution    # instructors: the reference implementation
python check.py -v                 # tracebacks for FAIL lines
```

Each line prints `PASS`, `FAIL`, or `TODO` with the value it saw and the value it expected.

## 8. Deliverable and grading rubric (100 points)

Submit: `telemetry_analysis.py`, `postmortem.md` (rendered from the template, then edited into
prose), `dashboard_spec.json` (the output of `dashboard_spec()` plus one sentence per panel on the
question it answers), and `slo_spec.md` (the SLO specification of Exercise M1).

| Item | Points |
|---|---|
| Tasks 1–2 correct (checker) and a one-paragraph explanation of why checkpoint steps are excluded | 20 |
| Task 3 correct, plus a written redesign of the noisy rule and a PromQL version of your goodput alert with `for:` justified | 20 |
| Task 4 correct, plus a "proven vs correlated" table for every hypothesis in `events.jsonl` | 15 |
| Task 5 postmortem: blameless language, accurate timeline, impact with evidence labels, ≥ 5 action items with owner/priority/type (detect / mitigate / prevent) | 25 |
| Task 6 dashboard spec: each level answers one question; panels justified; drill-down keys (job → node → GPU UUID / NIC / switch port) stated | 15 |
| Reproducibility: manifest filled, commands to regenerate outputs recorded | 5 |

## 9. Extensions (L2 / L3)

> **Safety:** run extensions only on a lab host or a cluster you are authorised to instrument. Do
> not change switch configuration or alert routing on shared production systems.

**L2 — one GPU host.** Stand up the same pipeline for real and re-run Tasks 1–3 on your own data.

```bash
nvidia-smi --query-gpu=index,uuid,pci.bus_id,utilization.gpu,power.draw,temperature.gpu --format=csv
dcgmi discovery -l                                   # GPUs DCGM can see
dcgmi dmon -e 1001,1002,1004,1005 -d 1000            # GR engine, SM active, tensor active, DRAM active (1 s)
docker run -d --gpus all --cap-add SYS_ADMIN -p 9400:9400 nvcr.io/nvidia/k8s/dcgm-exporter:<tag>
curl -s localhost:9400/metrics | grep -E '^DCGM_FI_(DEV_GPU_UTIL|PROF_SM_ACTIVE|DEV_POWER_USAGE)'
promtool check rules rules.yml                       # validate your recording/alert rules
promtool test rules rules_test.yml                   # unit-test alerts against synthetic series
```

Run a GPU workload that alternates compute and synchronisation (for example a PyTorch loop with
periodic `torch.cuda.synchronize()` and sleeps) and show that `DCGM_FI_DEV_GPU_UTIL` and
`DCGM_FI_PROF_SM_ACTIVE` diverge. Pick the `dcgm-exporter` tag from NVIDIA's catalogue for your
driver; field IDs and metric names are `[VENDOR-SPEC, 2026-10]` — verify them.

**L3 — multi-node with RDMA and switch access (read-only).**

```bash
gnmic -a orion-be-leaf-r0:<port> -u <user> -p <pass> --skip-verify subscribe \
      --path /interfaces/interface/state/counters --mode stream --stream-mode sample --sample-interval 10s
rdma statistic show link mlx5_0/1                    # RDMA hw counters (CNPs, retransmits, out-of-buffer)
ethtool -S <backend-if> | grep -E 'prio3_pause|discard'
mpirun -np 16 -H nodeA:8,nodeB:8 ./build/all_reduce_perf -b 1M -e 4G -f 2 -g 1
```

Record step-time or `all_reduce_perf` bus bandwidth together with the switch and NIC counters at the
same timestamps, then repeat the correlation of Task 4 on real data. Record in `manifest.yaml`:
NIC firmware, RDMA stack version, switch OS version, gNMI paths and sample interval, NCCL version,
topology, job size, number of runs, warm-up policy, and the alert-rule versions you evaluated.
Vendor-native gNMI paths for PFC and ECN counters differ by switch OS — use your vendor's YANG
models; OpenConfig covers interface counters and queues generically.

## 10. Intentionally flawed inputs

The bundle contains planted traps (a red-herring thermal event, a noisy rule, a deploy blip, a
monitoring change, checkpoint stalls). They are documented for instructors in
`../solutions/exercises-key.md` (section "Lab 18 — planted anomalies"). Learners: find them.
