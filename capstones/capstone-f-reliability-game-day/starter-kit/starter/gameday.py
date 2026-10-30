"""Capstone F starter module — AI infrastructure reliability game day.

Implement every function marked TODO. The loaders, constants and the simulator (sim/cluster_sim.py)
are given. Run ``python check.py`` from starter-kit/ to see which checks pass; read
starter-kit/README.md for tasks and acceptance criteria.

Everything here runs against a SIMULATED cluster. Nothing in this module may touch real systems.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from sim import cluster_sim
from sim.cluster_sim import SimResult

NODE_FAULTS = ("link_down", "node_loss")
TIMELINE_KINDS = {
    "fault_start": "game-day", "fault_end": "game-day",
    "alert_firing": "alerting", "alert_resolved": "alerting",
    "node_drained": "health-controller", "drain_pending": "health-controller",
    "job_hung": "job", "job_failed": "job", "job_restarted": "job", "job_resumed": "job",
    "job_requeued": "scheduler", "requeue_blocked": "scheduler",
    "ckpt_aborted": "checkpoint", "ckpt_skipped": "checkpoint",
}


# --------------------------------------------------------------------------- loaders (given)
def load_inputs(data_dir: Path) -> dict[str, Any]:
    """Load the dataset (given; not a TODO)."""
    d = Path(data_dir)
    with open(d / "default_alert_rules.yaml", encoding="utf-8") as fh:
        rules = yaml.safe_load(fh)
    with open(d / "gameday_constraints.yaml", encoding="utf-8") as fh:
        constraints = yaml.safe_load(fh)
    with open(d / "gameday1_plan.yaml", encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)
    with open(d / "backlog_candidates.csv", encoding="utf-8") as fh:
        backlog = list(csv.DictReader(fh))
    return {"default_rules": rules, "constraints": constraints, "gameday1_plan": plan,
            "gameday1": cluster_sim.load_result(d, "gameday1"), "backlog": backlog}


# --------------------------------------------------------------------------- T1 fault-injection plan
def fault_plan() -> list[dict[str, Any]]:
    """Return your game-day fault-injection plan: a list of scenarios.

    Each scenario: ``id``, ``title``, ``faults`` (simulator fault dicts with unique ``id``),
    ``hypothesis`` (what you expect and why), ``expected`` ({fault_id: {detect_within_s,
    max_lost_gpu_h, expect_recovered}}), ``abort_conditions`` (list of str), ``blast_radius`` (str),
    ``rollback`` (str). Constraints come from data/gameday_constraints.yaml: cover all four fault
    kinds, include at least one scenario with two overlapping faults, never target protected nodes,
    start after the warm-up, at most ``max_concurrent_faults`` overlapping faults.
    """
    # TODO: write at least five scenarios; cover link_down, node_loss, storage_slow and scheduler_outage
    # TODO: include at least one scenario with two OVERLAPPING faults - single faults rarely reveal the interesting failures
    # TODO: write the hypothesis and expected numbers BEFORE you run the scenario (derive them from the simulator docstring and ORION numbers)
    # TODO: respect data/gameday_constraints.yaml: warm-up, protected nodes, max concurrent faults
    # TODO: every scenario needs abort conditions, a blast radius and a rollback
    raise NotImplementedError("TODO: implement fault_plan()")


# --------------------------------------------------------------------------- T2 alert rules
def alert_rules() -> list[dict[str, Any]]:
    """Return your alert rules (simulator rule dicts).

    Each rule: ``name``, ``metric``, ``op`` (one of <, >, ==, !=, absent), ``threshold`` (not used by
    absent), ``for_s``, ``severity``, ``detects`` (fault kinds this rule is evidence for). Goals:
    zero alerts on a fault-free 6 h run; every fault kind detected within its target in
    data/gameday_constraints.yaml.
    """
    # TODO: start from data/default_alert_rules.yaml and run cluster_sim.run([], rules) - count the false positives
    # TODO: a checkpoint stalls training for ckpt_stall_s; a stall threshold must sit above step time + stall
    # TODO: think about how you detect a component that stops reporting altogether (op: absent)
    # TODO: a symptom alert (checkpoint age) is slow; is there a cause alert for storage?
    raise NotImplementedError("TODO: implement alert_rules()")


# --------------------------------------------------------------------------- T3 detection
# Scoring window per fault kind: 2 x the detection target in data/gameday_constraints.yaml.
DETECTION_TOLERANCE_S = {"node_loss": 240, "link_down": 240, "scheduler_outage": 240, "storage_slow": 600}


def detection_time(result: SimResult, fault: dict[str, Any],
                   tolerance_s: dict[str, float] | None = None) -> float | None:
    """Seconds from ``fault['start_s']`` to the first alert that detects it, or None.

    Only alerts that fire inside [onset, onset + tolerance] count (``tolerance_s`` per fault kind,
    default DETECTION_TOLERANCE_S = 2 x the detection target). A later alert is not a detection of
    this fault; an alert that fired before onset is a false positive, not a detection.

    An alert detects a fault when the fault's kind is in the alert's ``detects`` list, it fired at or
    after the fault start, and its labels tie it to the fault: a ``node`` label must equal the
    fault's target; a ``job`` label (for a fault with a target) must name a job that this fault
    hung (``job_hung`` with cause "<kind> <target>"). Unlabelled alerts (storage, scheduler) count
    for any fault of a kind they detect. Alerts already firing before the fault do not count.
    """
    # TODO: count only alerts firing inside [onset, onset + tolerance] (default: DETECTION_TOLERANCE_S)
    # TODO: filter by fault kind in detects, and tie labels to the fault: node must match; job must be one this fault hung
    # TODO: return None when nothing detected the fault in the window - that is a finding, not an error
    raise NotImplementedError("TODO: implement detection_time()")


# --------------------------------------------------------------------------- T4 recovery metrics
def recovery_metrics(result: SimResult, fault: dict[str, Any]) -> dict[str, Any]:
    """Compute detection, mitigation, recovery and lost GPU-hours for one injected fault.

    Returns dict with keys:
      detect_s     detection_time()
      mitigate_s   node/link faults: first ``node_drained`` of the target at/after start; global
                   faults (storage_slow, scheduler_outage): ``fault_end`` time (injection rolled back);
                   minus start. None if never.
      recover_s    if the fault interrupted jobs (``job_hung`` whose cause is "<kind> <target>"):
                   latest ``job_resumed`` among them minus start (None if any job never resumed);
                   otherwise equal to mitigate_s.
      recovered    bool
      lost_work_gpu_h  Σ GPUs × steps_lost × step_s / 3600, where steps_lost = step at hang − step
                   restored (``job_restarted.from_step``; if never restarted, the last durable step
                   before the hang) — i.e. work since the last *durable* checkpoint, not the last started one
      idle_gpu_h   Σ GPUs × (resume time, or horizon if never) − last_progress_t) / 3600
      lost_gpu_h   lost_work_gpu_h + idle_gpu_h (rounded to 0.1)
    """
    # TODO: attribute job interruptions to the fault through the job_hung cause string
    # TODO: the restore point is the last DURABLE checkpoint (job_restarted.from_step), not the last one started
    # TODO: a job that never resumes before the horizon is unrecovered: count idle time up to the horizon
    # TODO: use GPUs = 8 x nodes and step_s from result.config['jobs']
    raise NotImplementedError("TODO: implement recovery_metrics()")


# --------------------------------------------------------------------------- T5 timeline
def _offset(s: float) -> str:
    s = int(round(s))
    return f"T+{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def build_timeline(result: SimResult, t0_utc: str, start_s: float = 0.0,
                   end_s: float | None = None) -> list[dict[str, Any]]:
    """Merge events into an incident timeline, sorted by time (stable).

    Include only the kinds in TIMELINE_KINDS (routine ``ckpt_started``/``ckpt_durable`` and
    non-incident noise are excluded) within [start_s, end_s]. Each row: ``t_s``, ``utc``
    (ISO-8601 ``YYYY-MM-DDTHH:MM:SSZ``, seconds truncated), ``offset`` (``T+HH:MM:SS`` from start of
    simulation), ``source`` (TIMELINE_KINDS value), ``event`` (kind) and ``detail`` (short text).
    """
    # TODO: keep only kinds in TIMELINE_KINDS, inside [start_s, end_s]
    # TODO: format utc from t0_utc + int(t) seconds and offset with _offset()
    # TODO: sort by t_s (stable)
    raise NotImplementedError("TODO: implement build_timeline()")


# --------------------------------------------------------------------------- T6 hypotheses
def evaluate_hypotheses(scenario: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compare each fault's expected behaviour with observed metrics.

    Returns {fault_id: {detect_ok, lost_ok, recovered_ok, verdict}} where verdict is "held" when all
    three are True, else "failed". A missing detection (None) is never ok.
    """
    # TODO: compare observed metrics with scenario['expected'] for every fault id
    # TODO: an undetected fault (detect_s is None) never satisfies a detection target
    raise NotImplementedError("TODO: implement evaluate_hypotheses()")


# --------------------------------------------------------------------------- T7 backlog
def prioritize_backlog(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Rank reliability backlog items.

    score = annual_events × gpu_h_per_event × expected_reduction / effort_weeks (GPU-hours avoided per
    engineer-week). Order: safety_critical == "true" first, then score descending, then id. Returns
    new dicts with a numeric ``score`` (rounded to 0.1) added.
    """
    # TODO: compute the score from the CSV columns (they are strings)
    # TODO: safety-critical items first, then score descending, then id
    # TODO: then argue in your report what this formula ignores (cost of spare capacity, toil, risk)
    raise NotImplementedError("TODO: implement prioritize_backlog()")
