"""Chapter 18 lab - telemetry-bundle analysis for a cluster-wide throughput regression.

REFERENCE SOLUTION (instructors). Same public API as lab/starter/telemetry_analysis.py.

All timestamps are timezone-aware pandas Timestamps (UTC). Step times are in seconds, GPU-hours
in GPU x hours, burn rates are dimensionless multiples of the sustainable error-budget rate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

FAST_BURN = ((60, 5, 14.4), (360, 30, 6.0))   # (long window min, short window min, threshold)


# --------------------------------------------------------------------------- loading (given)
def load_bundle(data_dir: Path) -> dict[str, Any]:
    """Load every file of the telemetry bundle. Provided complete in the starter."""
    data_dir = Path(data_dir)
    b: dict[str, Any] = {}
    for name, tcol in (("job_steps", "end_ts"), ("node_metrics", "ts"), ("switch_metrics", "ts"),
                       ("inference_slo", "ts")):
        df = pd.read_csv(data_dir / f"{name}.csv")
        df[tcol] = pd.to_datetime(df[tcol], utc=True)
        b[name] = df
    with open(data_dir / "events.jsonl", encoding="utf-8") as fh:
        ev = pd.DataFrame([json.loads(line) for line in fh if line.strip()])
    ev["ts"] = pd.to_datetime(ev["ts"], utc=True)
    b["events"] = ev.sort_values("ts").reset_index(drop=True)
    b["rules"] = yaml.safe_load((data_dir / "alert_rules.yaml").read_text(encoding="utf-8"))["rules"]
    b["template"] = (data_dir / "postmortem_template.md").read_text(encoding="utf-8")
    return b


# --------------------------------------------------------------------------- Task 1: baselines
def baseline_step_time(job_steps: pd.DataFrame, job_id: str, start: pd.Timestamp,
                       end: pd.Timestamp) -> float:
    """Median step time (s) of NON-checkpoint steps of `job_id` whose end_ts is in [start, end)."""
    s = job_steps[(job_steps.job_id == job_id) & (job_steps.checkpoint == 0)
                  & (job_steps.end_ts >= start) & (job_steps.end_ts < end)]
    return float(s.step_time_s.median())


def step_time_per_minute(job_steps: pd.DataFrame, job_id: str) -> pd.Series:
    """Per-minute median step time (s) of non-checkpoint steps, indexed by minute start.

    Minutes with no completed step are forward-filled from the previous minute.
    """
    s = job_steps[(job_steps.job_id == job_id) & (job_steps.checkpoint == 0)]
    ser = s.set_index("end_ts").step_time_s.resample("1min").median()
    return ser.ffill()


def detect_onset(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10,
                 sustain_min: int = 5) -> pd.Timestamp:
    """First minute m such that the per-minute step time exceeds ratio*baseline for the
    `sustain_min` consecutive minutes starting at m. Raises ValueError if none."""
    ser = step_time_per_minute(job_steps, job_id)
    bad = (ser > ratio * baseline).astype(int)
    run = bad.rolling(sustain_min).sum()
    hits = run[run >= sustain_min]
    if hits.empty:
        raise ValueError("no sustained regression")
    return hits.index[0] - pd.Timedelta(minutes=sustain_min - 1)


def detect_recovery(job_steps: pd.DataFrame, job_id: str, baseline: float, after: pd.Timestamp,
                    ratio: float = 1.05, sustain_min: int = 10) -> pd.Timestamp:
    """First minute m > `after` from which the per-minute step time stays <= ratio*baseline
    for `sustain_min` consecutive minutes."""
    ser = step_time_per_minute(job_steps, job_id)
    ser = ser[ser.index > after]
    good = (ser <= ratio * baseline).astype(int)
    run = good.rolling(sustain_min).sum()
    hits = run[run >= sustain_min]
    if hits.empty:
        raise ValueError("no recovery")
    return hits.index[0] - pd.Timedelta(minutes=sustain_min - 1)


# --------------------------------------------------------------------------- Task 2: SLIs / burn
def training_sli(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10) -> float:
    """Fraction of minutes in the bundle whose per-minute step time is <= ratio*baseline."""
    ser = step_time_per_minute(job_steps, job_id).dropna()
    return float((ser <= ratio * baseline).mean())


def lost_gpu_hours(job_steps: pd.DataFrame, job_id: str, baseline: float, gpus: int,
                   start: pd.Timestamp, end: pd.Timestamp) -> float:
    """GPU-hours lost to slow steps: sum over non-checkpoint steps ending in [start, end) of
    max(0, step_time - baseline) * gpus / 3600."""
    s = job_steps[(job_steps.job_id == job_id) & (job_steps.checkpoint == 0)
                  & (job_steps.end_ts >= start) & (job_steps.end_ts < end)]
    return float((s.step_time_s - baseline).clip(lower=0).sum() * gpus / 3600.0)


def burn_rate(inference: pd.DataFrame, bad_col: str, slo: float, window_min: int) -> pd.Series:
    """Rolling burn rate = (sum bad / sum requests over the trailing window) / (1 - slo).

    Indexed by ts; NaN until a full window is available (min_periods = window_min).
    """
    df = inference.set_index("ts")
    bad = df[bad_col].rolling(window_min, min_periods=window_min).sum()
    req = df["requests"].rolling(window_min, min_periods=window_min).sum()
    return (bad / req) / (1.0 - slo)


def multiwindow_fast_burn(inference: pd.DataFrame, bad_col: str, slo: float) -> pd.Series:
    """Boolean series: True where the SRE-workbook page condition holds:
    (1h > 14.4 and 5m > 14.4) or (6h > 6 and 30m > 6)."""
    cond = None
    for long_w, short_w, thr in FAST_BURN:
        c = (burn_rate(inference, bad_col, slo, long_w) > thr) & (burn_rate(inference, bad_col, slo, short_w) > thr)
        cond = c if cond is None else (cond | c)
    return cond.fillna(False)


# --------------------------------------------------------------------------- Task 3: alerts
def _runs(mask: pd.Series, for_min: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Firing intervals for a boolean per-minute series with a `for` duration (minutes)."""
    out = []
    start = None
    count = 0
    last = None
    for ts, v in mask.items():
        if v:
            count += 1
            if count == for_min:
                start = ts
            last = ts
        else:
            if start is not None:
                out.append((start, last))
            start, count = None, 0
    if start is not None:
        out.append((start, last))
    return out


def evaluate_rule(rule: dict, bundle: dict[str, Any]) -> list[dict]:
    """Evaluate one rule's `eval` spec at minute resolution.

    Returns a list of firing intervals: {"entity", "start", "end"} where `start` is the first
    minute at which the condition has held for `for_min` consecutive minutes and `end` is the
    last minute it held. Burn-rate rules use entity "service" and the multiwindow condition.
    """
    e = rule["eval"]
    out: list[dict] = []
    if e["type"] == "burn_rate":
        mask = multiwindow_fast_burn(bundle[e["source"]], e["bad"], e["slo"])
        for s, t in _runs(mask, 2):
            out.append({"entity": "service", "start": s, "end": t})
        return out
    df = bundle[e["source"]]
    ops = {"<": lambda a, b: a < b, ">": lambda a, b: a > b}
    for ent, g in df.groupby(e["entity"]):
        g = g.set_index("ts").sort_index()
        mask = ops[e["op"]](g[e["metric"]], e["threshold"])
        for s, t in _runs(mask, int(e["for_min"])):
            out.append({"entity": ent, "start": s, "end": t})
    return out


def classify_alerts(bundle: dict[str, Any], incident: tuple[pd.Timestamp, pd.Timestamp]) -> dict[str, dict]:
    """For each rule: number of firings, firings overlapping the incident window, and a verdict.

    verdict = "noisy"   if severity == page and >= 5 firings start outside the incident window
              "silent"  if severity == page and it never fired during the incident window
              "ok"      otherwise.
    """
    res: dict[str, dict] = {}
    i0, i1 = incident
    for rule in bundle["rules"]:
        fires = evaluate_rule(rule, bundle)
        during = [f for f in fires if f["start"] <= i1 and f["end"] >= i0]
        outside = [f for f in fires if not (i0 <= f["start"] <= i1)]
        if rule["severity"] == "page" and len(outside) >= 5:
            verdict = "noisy"
        elif rule["severity"] == "page" and not during:
            verdict = "silent"
        else:
            verdict = "ok"
        res[rule["name"]] = {"severity": rule["severity"], "fires": len(fires), "during_incident": len(during),
                             "outside_incident": len(outside), "verdict": verdict}
    return res


def goodput_alert(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10,
                  window_min: int = 10, for_min: int = 5) -> list[dict]:
    """The missing symptom-based alert: fire when the rolling `window_min` median of the
    per-minute step time exceeds ratio*baseline for `for_min` consecutive minutes."""
    ser = step_time_per_minute(job_steps, job_id)
    med = ser.rolling(window_min, min_periods=window_min).median()
    mask = (med > ratio * baseline).fillna(False)
    return [{"entity": job_id, "start": s, "end": t} for s, t in _runs(mask, for_min)]


# --------------------------------------------------------------------------- Task 4: correlation
def fabric_shift(switch_metrics: pd.DataFrame, before: tuple[pd.Timestamp, pd.Timestamp],
                 after: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Per switch: ratio of mean pfc_pause_tx_pps and ecn_marked_pps (after / before)."""
    def window(w: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
        m = switch_metrics[(switch_metrics.ts >= w[0]) & (switch_metrics.ts < w[1])]
        return m.groupby("switch")[["pfc_pause_tx_pps", "ecn_marked_pps", "pfc_pause_rx_pps"]].mean()
    b, a = window(before), window(after)
    return pd.DataFrame({"pfc_tx_ratio": a.pfc_pause_tx_pps / b.pfc_pause_tx_pps.clip(lower=1),
                         "ecn_ratio": a.ecn_marked_pps / b.ecn_marked_pps.clip(lower=1),
                         "pfc_rx_ratio": a.pfc_pause_rx_pps / b.pfc_pause_rx_pps.clip(lower=1)})


def correlate_root_cause(bundle: dict[str, Any], onsets: dict[str, pd.Timestamp],
                         job_nodes: dict[str, list[str]], lookback_min: int = 45) -> dict[str, Any]:
    """Rank candidate trigger events (types change/facilities) that started within `lookback_min`
    minutes before the earliest onset. A candidate *explains* a job if its scope contains
    "backend-fabric" (shared by every training job) or any of the job's nodes.

    Returns {"trigger": <change_id or host>, "explains": {...}, "rejected": [ {id, reason} ...]}.
    The trigger is the candidate that explains ALL affected jobs; ties go to the latest start.
    """
    first = min(onsets.values())
    ev = bundle["events"]
    cands = ev[(ev.type.isin(["change", "facilities"])) & (ev.ts <= first)
               & (ev.ts >= first - pd.Timedelta(minutes=lookback_min))]
    best, rejected, explains_all = None, [], {}
    for _, e in cands.iterrows():
        cid = e.get("change_id") if isinstance(e.get("change_id"), str) else e["message"].split(" ")[0]
        scope = set(e["scope"])
        exp = {j: ("backend-fabric" in scope) or bool(scope & set(nodes)) for j, nodes in job_nodes.items()}
        explains_all[cid] = exp
        if all(exp.values()):
            if best is None or e.ts >= best[1]:
                best = (cid, e.ts)
        else:
            missing = [j for j, ok in exp.items() if not ok]
            rejected.append({"id": cid, "reason": f"scope does not include affected job(s) {missing}"})
    return {"trigger": best[0] if best else None, "explains": explains_all, "rejected": rejected}


# --------------------------------------------------------------------------- Task 5: timeline
def build_timeline(bundle: dict[str, Any], onset: pd.Timestamp) -> dict[str, Any]:
    """Key incident timestamps and durations (minutes).

    detected  = first event of type "report" at/after onset
    declared  = first "incident" event whose message contains "declared"
    mitigated = first "change" event whose message contains "RB completed" (rollback complete)
    resolved  = first "incident" event whose message contains "resolved"
    """
    ev = bundle["events"]
    after = ev[ev.ts >= onset]

    def first(mask: pd.Series) -> pd.Timestamp:
        return after[mask].ts.iloc[0]

    t = {
        "onset": onset,
        "detected": first(after.type == "report"),
        "declared": first((after.type == "incident") & after.message.str.contains("declared")),
        "mitigated": first((after.type == "change") & after.message.str.contains("RB completed")),
        "resolved": first((after.type == "incident") & after.message.str.contains("resolved")),
    }
    mins = lambda a, b: round((t[b] - t[a]).total_seconds() / 60.0, 1)  # noqa: E731
    t["ttd_min"] = mins("onset", "detected")
    t["ttm_min"] = mins("onset", "mitigated")
    t["ttr_min"] = mins("onset", "resolved")
    t["detect_to_declare_min"] = mins("detected", "declared")
    return t


def render_postmortem(template: str, facts: dict[str, Any]) -> str:
    """Replace every {{key}} in the template with str(facts[key]). Raise KeyError if any
    placeholder has no fact (a postmortem with holes is not done)."""
    import re
    keys = set(re.findall(r"\{\{(\w+)\}\}", template))
    missing = keys - set(facts)
    if missing:
        raise KeyError(f"missing facts: {sorted(missing)}")
    out = template
    for k in keys:
        out = out.replace("{{" + k + "}}", str(facts[k]))
    return out


# --------------------------------------------------------------------------- Task 6: dashboard
def dashboard_spec() -> dict[str, Any]:
    """Dashboard hierarchy fleet -> node -> device (GPU/NIC/switch) -> workload.

    Each level: {"name", "question", "panels": [{"title", "query", "unit"}], "drilldown": <next level|None>}.
    Queries use DCGM-exporter / node-exporter / kube-state-metrics names and recording rules
    defined in the chapter (verify names against your exporter versions).
    """
    return {"levels": [
        {"name": "fleet", "question": "Are users getting what they were promised, and where is it breaking?",
         "drilldown": "node",
         "panels": [
             {"title": "Training goodput vs baseline (per job)", "unit": "ratio",
              "query": "job:step_time_seconds:baseline / job:step_time_seconds:median10m"},
             {"title": "Inference availability burn rate 1h / 5m", "unit": "x budget",
              "query": "slo:errors:ratio_rate1h / 0.001"},
             {"title": "Inference TTFT p95", "unit": "s",
              "query": "histogram_quantile(0.95, sum by (le) (rate(vllm:time_to_first_token_seconds_bucket[5m])))"},
             {"title": "Schedulable GPUs vs allocated GPUs", "unit": "GPUs",
              "query": "sum(kube_node_status_allocatable{resource=\"nvidia_com_gpu\"})"},
             {"title": "Fabric PFC pause TX by leaf (top 5)", "unit": "frames/s",
              "query": "topk(5, sum by (switch) (rate(switch_pfc_pause_tx_frames_total[5m])))"},
         ]},
        {"name": "node", "question": "Which nodes deviate from their peers in the same job?",
         "drilldown": "device",
         "panels": [
             {"title": "SM active by node (job peers)", "unit": "ratio",
              "query": "avg by (Hostname) (DCGM_FI_PROF_SM_ACTIVE)"},
             {"title": "GPU power by node", "unit": "W", "query": "sum by (Hostname) (DCGM_FI_DEV_POWER_USAGE)"},
             {"title": "Backend NIC TX by node", "unit": "Gb/s",
              "query": "8 * sum by (instance) (rate(node_infiniband_port_data_transmitted_bytes_total[1m])) / 1e9"},
             {"title": "Node conditions / drained", "unit": "count",
              "query": "kube_node_spec_unschedulable"},
         ]},
        {"name": "device", "question": "Which GPU, NIC port, or switch port is the outlier, and why?",
         "drilldown": "workload",
         "panels": [
             {"title": "GPU tensor-pipe active", "unit": "ratio", "query": "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"},
             {"title": "GPU temperature and clock-event reasons", "unit": "C",
              "query": "DCGM_FI_DEV_GPU_TEMP"},
             {"title": "Xid errors", "unit": "code", "query": "DCGM_FI_DEV_XID_ERRORS"},
             {"title": "NIC link downed / symbol errors", "unit": "count/5m",
              "query": "increase(node_infiniband_link_downed_total[5m])"},
             {"title": "Switch port ECN marks and PFC pauses", "unit": "pkts/s",
              "query": "rate(switch_ecn_marked_packets_total[1m])"},
         ]},
        {"name": "workload", "question": "What did the job experience, step by step?",
         "drilldown": None,
         "panels": [
             {"title": "Step time p50/p95 per job", "unit": "s",
              "query": "histogram_quantile(0.95, sum by (le, job_id) (rate(train_step_seconds_bucket[5m])))"},
             {"title": "Tokens/s per job", "unit": "tokens/s", "query": "sum by (job_id) (rate(train_tokens_total[5m]))"},
             {"title": "Checkpoint duration", "unit": "s", "query": "train_checkpoint_duration_seconds"},
             {"title": "Change and incident annotations", "unit": "event",
              "query": "annotations: change-mgmt + incident-bot"},
         ]},
    ]}
