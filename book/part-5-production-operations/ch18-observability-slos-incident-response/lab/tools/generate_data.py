#!/usr/bin/env python3
"""Generate the Chapter 18 telemetry bundle (ORION-256, cluster-wide throughput regression).

The bundle is synthetic [SIMULATED] and modeled on ORION-256 (docs/REFERENCE_CLUSTER.md). It
covers a 6-hour window (2026-10-12 00:00Z to 06:00Z) at 1-minute resolution:

  job_steps.csv          per-step records for two Slurm training jobs
  node_metrics.csv       per-node, per-minute host/GPU summary (DCGM-exporter-style fields)
  switch_metrics.csv     per-switch, per-minute backend-fabric summary (gNMI-style fields)
  inference_slo.csv      per-minute request / bad-request counts for the inference service
  events.jsonl           change records, syslog/kernel lines, chat reports, incident updates
  alert_rules.yaml       the alert rules that were deployed during the incident
  postmortem_template.md the blameless postmortem template with {{placeholders}}

Usage:
    python generate_data.py                 # writes into ../data
    python generate_data.py --out /tmp/x    # writes elsewhere (used by check.py)

Deterministic: fixed seed; regenerating produces byte-identical files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 18
T0 = pd.Timestamp("2026-10-12T00:00:00Z")
MINUTES = 360
TRN_NODES = [f"orion-n{i:02d}" for i in range(1, 17)]      # trn-70b: 16 nodes, 128 GPUs
FT_NODES = [f"orion-n{i:02d}" for i in range(17, 25)]      # ft-13b: 8 nodes, 64 GPUs
INF_NODES = [f"orion-n{i:02d}" for i in range(25, 33)]     # Kubernetes inference pool
LEAVES = [f"orion-be-leaf-r{r}" for r in range(8)]
SPINES = [f"orion-be-spine-{s}" for s in range(1, 5)]

# Change CHG-4471 rolls across the 8 rail leaves 02:08-02:12; rollback 04:02-04:08.
PUSH_START, PUSH_END = 128.0, 132.0           # minutes from T0
ROLLBACK_START, ROLLBACK_END = 242.0, 248.0


def iso(minute: float) -> str:
    """Return an ISO-8601 UTC timestamp `minute` minutes after T0 (second resolution)."""
    return (T0 + pd.Timedelta(seconds=round(minute * 60))).strftime("%Y-%m-%dT%H:%M:%SZ")


def degradation(minute: float) -> float:
    """Fraction (0..1) of the fabric regression in effect at `minute`."""
    if minute < PUSH_START or minute >= ROLLBACK_END:
        return 0.0
    if minute < PUSH_END:
        return (minute - PUSH_START) / (PUSH_END - PUSH_START)
    if minute < ROLLBACK_START:
        return 1.0
    return 1.0 - (minute - ROLLBACK_START) / (ROLLBACK_END - ROLLBACK_START)


def gen_job_steps(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    jobs = [
        # job_id, slurm id, baseline step s, regressed factor, ckpt period min, ckpt stall s, tokens/step
        ("trn-70b", 731842, 17.4, 1.225, 30, 9.0, 2_097_152),
        ("ft-13b", 731907, 6.0, 1.183, 20, 4.0, 1_048_576),
    ]
    for job_id, slurm_id, base, factor, ck_period, ck_stall, tokens in jobs:
        t = 0.0  # seconds since T0
        step = 50_000 if job_id == "trn-70b" else 12_000
        next_ck = ck_period * 60.0
        while True:
            d = degradation(t / 60.0)
            mean = base * (1.0 + (factor - 1.0) * d)
            sd = base * (0.012 + 0.025 * d)
            st = max(base * 0.95, rng.normal(mean, sd))
            ck = 0
            if t + st >= next_ck:
                st += ck_stall
                ck = 1
                next_ck += ck_period * 60.0
            t += st
            if t >= MINUTES * 60:
                break
            step += 1
            rows.append((job_id, slurm_id, step, iso(t / 60.0), round(st, 3), tokens, ck))
    return pd.DataFrame(rows, columns=["job_id", "slurm_job_id", "step", "end_ts", "step_time_s",
                                       "tokens", "checkpoint"])


def gen_node_metrics(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for m in range(MINUTES):
        d = degradation(m + 0.5)
        night = 0.5 + 0.5 * np.sin(np.pi * (m / MINUTES))  # inference load shape over the window
        for node in TRN_NODES + FT_NODES + INF_NODES:
            if node in INF_NODES:
                role, job = "inference", "k8s:chat-70b"
                util = float(np.clip(rng.normal(40 + 30 * night, 6), 15, 92))
                sm = util / 100 * rng.uniform(0.40, 0.55)
                power = 250 + 3.0 * util + rng.normal(0, 10)
                temp = 52 + 0.18 * util + rng.normal(0, 1.0)
                nic = rng.uniform(1.0, 6.0)
            else:
                role = "training"
                job = "trn-70b" if node in TRN_NODES else "ft-13b"
                factor = 1.225 if job == "trn-70b" else 1.183
                slow = 1.0 + (factor - 1.0) * d
                # DCGM GPU_UTIL counts any kernel resident, incl. NCCL kernels spinning on the
                # network, so it barely moves; SM activity and power fall with the stall fraction.
                util = float(np.clip(rng.normal(97.0, 0.8), 90, 100))
                sm_base = 0.62 if job == "trn-70b" else 0.55
                sm = sm_base / slow + rng.normal(0, 0.01)
                power = 615 - 360 * (1 - 1 / slow) + rng.normal(0, 8)
                temp = 71 + 9 * (power - 450) / 200 + rng.normal(0, 0.8)
                nic_base = 1150.0 if job == "trn-70b" else 900.0
                nic = nic_base / slow + rng.normal(0, 15)
                # Checkpoint minutes: brief dip in utilization (trn every 30 min, ft every 20 min)
                period = 30 if job == "trn-70b" else 20
                if m > 0 and m % period == 0:
                    util -= rng.uniform(8, 14)
                    sm *= 0.8
                    nic *= 0.75
                # Red herring: orion-n08 runs hot 01:45-02:40 (row-B CRAH maintenance), clocks normal
                if node == "orion-n08" and 105 <= m < 160:
                    ramp = min(1.0, (m - 105) / 6.0) if m < 154 else (160 - m) / 6.0
                    temp = 80.5 + 7.0 * ramp + rng.normal(0, 0.4)
            rows.append((iso(m), node, role, job, round(util, 1), round(float(sm), 3), round(float(power), 1),
                         round(float(temp), 1), round(float(nic), 1), 0))
    return pd.DataFrame(rows, columns=["ts", "node", "role", "job", "gpu_util_pct", "sm_active",
                                       "power_w", "gpu_temp_c_max", "nic_tx_gbps", "xid_count"])


def gen_switch_metrics(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for m in range(MINUTES):
        for sw in LEAVES + SPINES:
            if "-leaf-" in sw:
                r = int(sw[-1])
                # rolling push: leaf r flips at 02:08 + r*0.5 min; rollback 04:02 + r*0.75 min
                flipped = (PUSH_START + r * 0.5) <= m < (ROLLBACK_START + r * 0.75)
                util = rng.normal(31.0, 1.5) * (0.82 if flipped else 1.0)
                ecn = rng.normal(11500, 900) if not flipped else rng.normal(320, 60)
                pfc_tx = rng.normal(45, 10) if not flipped else rng.normal(4200, 350)
                pfc_rx = rng.normal(20, 6)
            else:
                d = degradation(m + 0.5)
                util = rng.normal(31.0, 1.2) * (1 - 0.18 * d)
                ecn = rng.normal(2100, 200) * (1 - 0.9 * d)
                pfc_tx = rng.normal(15, 5) * (1 + 3 * d)
                pfc_rx = rng.normal(30, 8) + 3100 * d + rng.normal(0, 150) * d
            rows.append((iso(m), sw, "leaf" if "-leaf-" in sw else "spine",
                         round(max(util, 0), 1), int(max(ecn, 0)), int(max(pfc_tx, 0)), int(max(pfc_rx, 0)), 0))
    return pd.DataFrame(rows, columns=["ts", "switch", "role", "tx_util_pct", "ecn_marked_pps",
                                       "pfc_pause_tx_pps", "pfc_pause_rx_pps", "out_discards_pps"])


def gen_inference(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for m in range(MINUTES):
        night = 0.5 + 0.5 * np.sin(np.pi * (m / MINUTES))
        req = int(rng.normal(2000 + 1800 * night, 80))
        bad_frac = rng.normal(0.015, 0.003)
        err_frac = max(rng.normal(0.0002, 0.00008), 0)
        if 310 <= m < 317:  # 05:10-05:16 bad deploy of the serving config, auto-rolled back
            bad_frac, err_frac = 0.12, 0.04
        rows.append((iso(m), req, int(round(req * max(bad_frac, 0))), int(round(req * err_frac))))
    return pd.DataFrame(rows, columns=["ts", "requests", "ttft_over_800ms", "errors_5xx"])


def gen_events() -> list[dict]:
    ev: list[dict] = []

    def add(minute: float, source: str, etype: str, host: str, scope: list[str], msg: str, **kw: str) -> None:
        e = {"ts": iso(minute), "source": source, "type": etype, "host": host, "scope": scope, "message": msg}
        e.update(kw)
        ev.append(e)

    add(90.0, "change-mgmt", "change", "grafana-01", ["monitoring"],
        "CHG-4468 completed: Grafana 11.x minor upgrade on grafana-01 (dashboards only)", change_id="CHG-4468")
    add(100.0, "facilities", "facilities", "row-B", ["row-B", "orion-n05", "orion-n06", "orion-n07", "orion-n08"],
        "FAC-0912 started: CRAH-3 fan module replacement in row B; inlet temps may rise 2-4 C for ~60 min")
    add(104.8, "bmc", "syslog", "orion-n08", ["orion-n08"],
        "Redfish event: Inlet Temp warning (assert) reading 31 C threshold 30 C")
    add(128.2, "change-mgmt", "change", "netauto-01", ["backend-fabric"] + LEAVES,
        "CHG-4471 started: rolling apply of buffer-profile v2 (ECN/WRED min/max thresholds) to backend "
        "rail leaves orion-be-leaf-r0..orion-be-leaf-r7 via gNMI Set", change_id="CHG-4471")
    for r in range(8):
        add(PUSH_START + r * 0.5 + 0.05, "switch-syslog", "syslog", f"orion-be-leaf-r{r}", [f"orion-be-leaf-r{r}"],
            f"config commit by svc-netauto (CHG-4471): qos profile roce-lossless tc3 ecn min/max thresholds "
            f"updated; commit id 9f2c{r:02d}")
    add(132.4, "change-mgmt", "change", "netauto-01", ["backend-fabric"] + LEAVES,
        "CHG-4471 completed: 8/8 leaves applied, post-checks PASS (interfaces up, BGP established, "
        "no discards)", change_id="CHG-4471")
    add(160.0, "facilities", "facilities", "row-B", ["row-B"], "FAC-0912 completed: CRAH-3 back in service")
    add(178.0, "chat", "report", "#training-help", ["trn-70b"],
        "researcher: trn-70b tokens/s looks ~18% lower than yesterday since roughly 02:15 - anything going on?")
    add(181.0, "chat", "report", "#training-help", ["ft-13b"],
        "researcher: ft-13b is slow too, step time 7.1 s vs 6.0 s")
    add(185.0, "pager", "incident", "sre-oncall", ["cluster"], "SRE on-call acknowledged chat report; investigating")
    add(192.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "INC-2291 declared SEV2: cluster-wide training throughput regression; IC=sre-oncall, "
        "Ops lead=fabric-oncall, Comms=training-infra")
    add(200.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Comms update 1: both training jobs ~15-20% slower since ~02:12; inference unaffected; next update 03:50")
    add(208.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Hypothesis: orion-n08 thermal (row B) -> rejected: ft-13b does not include orion-n08 and orion-n08 clocks normal")
    add(215.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Hypothesis: backend fabric; leaf PFC pause TX up ~90x, ECN marks down ~97% since 02:08-02:12")
    add(228.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Correlated to CHG-4471 (buffer-profile v2). Decision: roll back CHG-4471 leaf by leaf")
    add(230.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Comms update 2: probable cause identified (fabric config change); rollback starting 04:02")
    add(242.0, "change-mgmt", "change", "netauto-01", ["backend-fabric"] + LEAVES,
        "CHG-4471-RB started: rollback to buffer-profile v1", change_id="CHG-4471-RB")
    add(248.2, "change-mgmt", "change", "netauto-01", ["backend-fabric"] + LEAVES,
        "CHG-4471-RB completed: 8/8 leaves rolled back", change_id="CHG-4471-RB")
    add(260.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "Validation: step times back to baseline for 10+ min on both jobs; PFC/ECN back to baseline")
    add(270.0, "incident-bot", "incident", "INC-2291", ["cluster"],
        "INC-2291 resolved. Postmortem owner: fabric-oncall; due 2026-10-19")
    add(310.0, "k8s", "change", "chat-70b", ["inference"],
        "Deployment chat-70b rollout started: serving config rev 41 (max-num-seqs raised)", change_id="DEP-41")
    add(317.0, "k8s", "change", "chat-70b", ["inference"],
        "Deployment chat-70b auto-rollback to rev 40 after canary error-rate check failed", change_id="DEP-41-RB")
    ev.sort(key=lambda e: e["ts"])
    return ev


ALERT_RULES = """\
# Alert rules deployed on ORION during INC-2291 (2026-10-12).
# `promql` is what ran in Prometheus; `eval` is a simplified spec the lab evaluates offline
# against the bundle (minute resolution). Metric names in `promql` follow DCGM-exporter / custom
# recording-rule conventions [VENDOR-SPEC, 2026-10 - verify against your exporter version].
rules:
  - name: GPUUtilLow
    severity: page
    promql: 'avg by (Hostname) (DCGM_FI_DEV_GPU_UTIL) < 80'
    for: 2m
    eval: {type: threshold, source: node_metrics, entity: node, metric: gpu_util_pct, op: "<", threshold: 80, for_min: 2}
  - name: GPUTempHigh
    severity: ticket
    promql: 'max by (Hostname) (DCGM_FI_DEV_GPU_TEMP) > 85'
    for: 5m
    eval: {type: threshold, source: node_metrics, entity: node, metric: gpu_temp_c_max, op: ">", threshold: 85, for_min: 5}
  - name: GPUXidCritical
    severity: page
    promql: 'max by (Hostname) (DCGM_FI_DEV_XID_ERRORS) > 0'
    for: 0m
    eval: {type: threshold, source: node_metrics, entity: node, metric: xid_count, op: ">", threshold: 0, for_min: 1}
  - name: FabricOutDiscards
    severity: page
    promql: 'sum by (switch) (rate(switch_interface_out_discards_total[5m])) > 0'
    for: 5m
    eval: {type: threshold, source: switch_metrics, entity: switch, metric: out_discards_pps, op: ">", threshold: 0, for_min: 5}
  - name: InferenceAvailabilityBurn
    severity: page
    promql: '(slo:errors:ratio_rate1h > 14.4*0.001 and slo:errors:ratio_rate5m > 14.4*0.001) or (slo:errors:ratio_rate6h > 6*0.001 and slo:errors:ratio_rate30m > 6*0.001)'
    for: 2m
    eval: {type: burn_rate, source: inference_slo, bad: errors_5xx, slo: 0.999}
  - name: InferenceTTFTBurn
    severity: page
    promql: '(slo:ttft_bad:ratio_rate1h > 14.4*0.05 and slo:ttft_bad:ratio_rate5m > 14.4*0.05) or (slo:ttft_bad:ratio_rate6h > 6*0.05 and slo:ttft_bad:ratio_rate30m > 6*0.05)'
    for: 2m
    eval: {type: burn_rate, source: inference_slo, bad: ttft_over_800ms, slo: 0.95}
"""

POSTMORTEM_TEMPLATE = """\
# Postmortem {{incident_id}} - {{title}}

Status: draft | Severity: {{severity}} | Blameless: yes | Owner: {{owner}}

## Summary
{{summary}}

## Impact
- Affected workloads: {{affected_jobs}}
- Duration of user-visible impact (onset to mitigation): {{impact_minutes}} min
- Lost accelerator time [MODELED from step records]: {{lost_gpu_hours}} GPU-hours
- Training throughput SLI during the 6-hour window: {{training_sli}}
- Inference SLOs: {{inference_impact}}

## Timeline (UTC)
{{timeline}}

## Detection
- Time to detect (onset to first human/alert signal): {{ttd_min}} min
- How detected: {{how_detected}}
- Alerting gap (missing alert): {{missing_alert}}
- Noisy alert that should be redesigned: {{noisy_alert}}

## Root cause and trigger
{{root_cause}}

## Rejected hypotheses (and the evidence that rejected them)
{{rejected_hypotheses}}

## What went well / what went poorly / where we got lucky
{{went_well}}

## Action items (owner, priority, due)
{{action_items}}
"""


def write_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    gen_job_steps(rng).to_csv(out / "job_steps.csv", index=False, lineterminator="\n")
    gen_node_metrics(rng).to_csv(out / "node_metrics.csv", index=False, lineterminator="\n")
    gen_switch_metrics(rng).to_csv(out / "switch_metrics.csv", index=False, lineterminator="\n")
    gen_inference(rng).to_csv(out / "inference_slo.csv", index=False, lineterminator="\n")
    with open(out / "events.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for e in gen_events():
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    (out / "alert_rules.yaml").write_text(ALERT_RULES, encoding="utf-8", newline="\n")
    (out / "postmortem_template.md").write_text(POSTMORTEM_TEMPLATE, encoding="utf-8", newline="\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = p.parse_args()
    write_all(args.out)
    print(f"wrote bundle to {args.out}")


if __name__ == "__main__":
    main()
