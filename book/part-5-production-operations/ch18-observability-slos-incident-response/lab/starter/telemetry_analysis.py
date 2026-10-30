"""Chapter 18 lab - telemetry-bundle analysis for a cluster-wide throughput regression.

STARTER: implement every function that raises NotImplementedError. `load_bundle` and `_runs` are
given. Run `python ../check.py` from lab/starter (or `python check.py` from lab/) to see progress.

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
    # TODO: Filter job_id, checkpoint == 0 and the [start, end) window on end_ts; return the median.
    raise NotImplementedError("baseline_step_time")


def step_time_per_minute(job_steps: pd.DataFrame, job_id: str) -> pd.Series:
    """Per-minute median step time (s) of non-checkpoint steps, indexed by minute start.

    Minutes with no completed step are forward-filled from the previous minute.
    """
    # TODO: Filter non-checkpoint steps, set_index('end_ts'), resample('1min').median(), then ffill().
    raise NotImplementedError("step_time_per_minute")


def detect_onset(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10,
                 sustain_min: int = 5) -> pd.Timestamp:
    """First minute m such that the per-minute step time exceeds ratio*baseline for the
    `sustain_min` consecutive minutes starting at m. Raises ValueError if none."""
    # TODO: Build a 0/1 series (step time > ratio*baseline); a rolling(sustain_min).sum() == sustain_min marks the END of a qualifying run.
    raise NotImplementedError("detect_onset")


def detect_recovery(job_steps: pd.DataFrame, job_id: str, baseline: float, after: pd.Timestamp,
                    ratio: float = 1.05, sustain_min: int = 10) -> pd.Timestamp:
    """First minute m > `after` from which the per-minute step time stays <= ratio*baseline
    for `sustain_min` consecutive minutes."""
    # TODO: Mirror detect_onset on the slice after `after`, with <= ratio*baseline.
    raise NotImplementedError("detect_recovery")


# --------------------------------------------------------------------------- Task 2: SLIs / burn
def training_sli(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10) -> float:
    """Fraction of minutes in the bundle whose per-minute step time is <= ratio*baseline."""
    # TODO: Use step_time_per_minute(); the SLI is the mean of the boolean 'good minute' series.
    raise NotImplementedError("training_sli")


def lost_gpu_hours(job_steps: pd.DataFrame, job_id: str, baseline: float, gpus: int,
                   start: pd.Timestamp, end: pd.Timestamp) -> float:
    """GPU-hours lost to slow steps: sum over non-checkpoint steps ending in [start, end) of
    max(0, step_time - baseline) * gpus / 3600."""
    # TODO: Only time ABOVE baseline is lost: clip(lower=0) before summing, then x gpus / 3600.
    raise NotImplementedError("lost_gpu_hours")


def burn_rate(inference: pd.DataFrame, bad_col: str, slo: float, window_min: int) -> pd.Series:
    """Rolling burn rate = (sum bad / sum requests over the trailing window) / (1 - slo).

    Indexed by ts; NaN until a full window is available (min_periods = window_min).
    """
    # TODO: Rolling sums of the bad column and of requests with min_periods=window_min; divide, then divide by (1 - slo).
    raise NotImplementedError("burn_rate")


def multiwindow_fast_burn(inference: pd.DataFrame, bad_col: str, slo: float) -> pd.Series:
    """Boolean series: True where the SRE-workbook page condition holds:
    (1h > 14.4 and 5m > 14.4) or (6h > 6 and 30m > 6)."""
    # TODO: Combine the two (long, short, threshold) pairs in FAST_BURN with & inside a pair and | across pairs; fillna(False).
    raise NotImplementedError("multiwindow_fast_burn")


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
    # TODO: threshold rules: groupby entity, compare metric with op/threshold, then _runs(mask, for_min). burn_rate rules: multiwindow_fast_burn + _runs(mask, 2), entity 'service'.
    raise NotImplementedError("evaluate_rule")


def classify_alerts(bundle: dict[str, Any], incident: tuple[pd.Timestamp, pd.Timestamp]) -> dict[str, dict]:
    """For each rule: number of firings, firings overlapping the incident window, and a verdict.

    verdict = "noisy"   if severity == page and >= 5 firings start outside the incident window
              "silent"  if severity == page and it never fired during the incident window
              "ok"      otherwise.
    """
    # TODO: Call evaluate_rule for each bundle['rules'] entry; a firing overlaps the incident if start <= i1 and end >= i0.
    raise NotImplementedError("classify_alerts")


def goodput_alert(job_steps: pd.DataFrame, job_id: str, baseline: float, ratio: float = 1.10,
                  window_min: int = 10, for_min: int = 5) -> list[dict]:
    """The missing symptom-based alert: fire when the rolling `window_min` median of the
    per-minute step time exceeds ratio*baseline for `for_min` consecutive minutes."""
    # TODO: rolling(window_min).median() of step_time_per_minute, compare with ratio*baseline, then _runs(mask, for_min).
    raise NotImplementedError("goodput_alert")


# --------------------------------------------------------------------------- Task 4: correlation
def fabric_shift(switch_metrics: pd.DataFrame, before: tuple[pd.Timestamp, pd.Timestamp],
                 after: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Per switch: ratio of mean pfc_pause_tx_pps and ecn_marked_pps (after / before)."""
    # TODO: Mean per switch in each window; ratio after/before. Guard the denominator with clip(lower=1).
    raise NotImplementedError("fabric_shift")


def correlate_root_cause(bundle: dict[str, Any], onsets: dict[str, pd.Timestamp],
                         job_nodes: dict[str, list[str]], lookback_min: int = 45) -> dict[str, Any]:
    """Rank candidate trigger events (types change/facilities) that started within `lookback_min`
    minutes before the earliest onset. A candidate *explains* a job if its scope contains
    "backend-fabric" (shared by every training job) or any of the job's nodes.

    Returns {"trigger": <change_id or host>, "explains": {...}, "rejected": [ {id, reason} ...]}.
    The trigger is the candidate that explains ALL affected jobs; ties go to the latest start.
    """
    # TODO: Candidates: events of type change/facilities in [first_onset - lookback, first_onset]. Use change_id if present, else the first word of the message (e.g. FAC-0912).
    raise NotImplementedError("correlate_root_cause")


# --------------------------------------------------------------------------- Task 5: timeline
def build_timeline(bundle: dict[str, Any], onset: pd.Timestamp) -> dict[str, Any]:
    """Key incident timestamps and durations (minutes).

    detected  = first event of type "report" at/after onset
    declared  = first "incident" event whose message contains "declared"
    mitigated = first "change" event whose message contains "RB completed" (rollback complete)
    resolved  = first "incident" event whose message contains "resolved"
    """
    # TODO: Search bundle['events'] at/after onset with the rules in the docstring; durations in minutes rounded to 0.1.
    raise NotImplementedError("build_timeline")


def render_postmortem(template: str, facts: dict[str, Any]) -> str:
    """Replace every {{key}} in the template with str(facts[key]). Raise KeyError if any
    placeholder has no fact (a postmortem with holes is not done)."""
    # TODO: re.findall(r'\{\{(\w+)\}\}', template) gives the placeholder names.
    raise NotImplementedError("render_postmortem")


# --------------------------------------------------------------------------- Task 6: dashboard
def dashboard_spec() -> dict[str, Any]:
    """Dashboard hierarchy fleet -> node -> device (GPU/NIC/switch) -> workload.

    Each level: {"name", "question", "panels": [{"title", "query", "unit"}], "drilldown": <next level|None>}.
    Queries use DCGM-exporter / node-exporter / kube-state-metrics names and recording rules
    defined in the chapter (verify names against your exporter versions).
    """
    # TODO: Return >= 4 levels named fleet, node, device, workload, each with >= 3 panels {title, query, unit} and a drilldown to the next level (None for the last). Use real exporter metric names (DCGM_FI_*, node_*, kube_*) or recording rules you define.
    raise NotImplementedError("dashboard_spec")
