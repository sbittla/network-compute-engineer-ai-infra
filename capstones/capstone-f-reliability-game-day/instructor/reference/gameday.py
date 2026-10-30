"""Reference implementation — Capstone F reliability game day (INSTRUCTOR ONLY).

Same public API as starter-kit/starter/gameday.py. The simulator (``sim.cluster_sim``) is given
and imported from starter-kit/ (check.py puts it on ``sys.path``).
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
    common_abort = ["simulator raises or produces events after horizon",
                    "any fault would touch a protected node (rack-08 inference partition)"]
    return [
        {"id": "S1", "title": "Single node loss in the training job",
         "faults": [{"id": "S1-F1", "kind": "node_loss", "target": "orion-n09", "start_s": 3000}],
         "hypothesis": "NodeDown fires within ~75 s; health controller drains at +60 s; job fails at the "
                       "600 s collective timeout, requeues onto a spare and resumes from the last durable "
                       "checkpoint ~900 s (the canonical ~15-min restart overhead) after the fault; lost <= 120 GPU-h.",
         "expected": {"S1-F1": {"detect_within_s": 120, "max_lost_gpu_h": 120, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "one training node (8 of 192 job GPUs)",
         "rollback": "end of simulation; in a lab: power the node back on and re-run acceptance"},
        {"id": "S2", "title": "Single backend rail link down",
         "faults": [{"id": "S2-F1", "kind": "link_down", "target": "orion-n06", "rail": 3,
                     "start_s": 3000, "duration_s": 600}],
         "hypothesis": "NicLinkDown fires within ~45 s; the job still waits for the collective timeout "
                       "because a dead rail is fatal to the in-flight collective; recovery as S1.",
         "expected": {"S2-F1": {"detect_within_s": 120, "max_lost_gpu_h": 120, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "one rail on one node",
         "rollback": "link restored after 600 s (lab: ip link set dev <if> up)"},
        {"id": "S3", "title": "Storage write throughput collapse",
         "faults": [{"id": "S3-F1", "kind": "storage_slow", "factor": 0.05, "start_s": 3000, "duration_s": 2400}],
         "hypothesis": "StorageWriteDegraded fires within ~75 s; no job interruption; checkpoint "
                       "completion stretches from ~12 s to ~245 s; RPO widens but no GPU-hours are lost.",
         "expected": {"S3-F1": {"detect_within_s": 300, "max_lost_gpu_h": 0, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "all checkpoint writers (shared storage)",
         "rollback": "throughput restored after 2,400 s (lab: tc qdisc del dev <if> root)"},
        {"id": "S4", "title": "Scheduler controller outage",
         "faults": [{"id": "S4-F1", "kind": "scheduler_outage", "start_s": 3000, "duration_s": 900}],
         "hypothesis": "SchedulerHeartbeatAbsent fires within ~75 s; running jobs are unaffected; no GPU-hours lost.",
         "expected": {"S4-F1": {"detect_within_s": 120, "max_lost_gpu_h": 0, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "control plane only",
         "rollback": "controller restarted after 900 s (lab: systemctl start slurmctld)"},
        {"id": "S5", "title": "Node loss while storage is slow (checkpoint in flight)",
         "faults": [{"id": "S5-F1", "kind": "storage_slow", "factor": 0.02, "start_s": 5300, "duration_s": 3000},
                    {"id": "S5-F2", "kind": "node_loss", "target": "orion-n18", "start_s": 5800}],
         "hypothesis": "The checkpoint started at ~5,400 s is still writing at 5,800 s and is aborted; "
                       "the job restores from the previous durable checkpoint, so lost work roughly doubles "
                       "versus S1; restart is slower because checkpoint load is at degraded read bandwidth.",
         "expected": {"S5-F1": {"detect_within_s": 300, "max_lost_gpu_h": 0, "expect_recovered": True},
                      "S5-F2": {"detect_within_s": 120, "max_lost_gpu_h": 150, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "shared storage + one training node",
         "rollback": "storage restored at 8,300 s; node stays lost (lab: power on, re-accept)"},
        {"id": "S6", "title": "Link down during scheduler outage",
         "faults": [{"id": "S6-F1", "kind": "scheduler_outage", "start_s": 3000, "duration_s": 1200},
                    {"id": "S6-F2", "kind": "link_down", "target": "orion-n13", "rail": 0,
                     "start_s": 3300, "duration_s": 600}],
         "hypothesis": "Drain is queued until the scheduler returns; the failed job cannot requeue until "
                       "4,200 s; recovery is bounded by the outage, not by the link.",
         "expected": {"S6-F1": {"detect_within_s": 120, "max_lost_gpu_h": 0, "expect_recovered": True},
                      "S6-F2": {"detect_within_s": 120, "max_lost_gpu_h": 120, "expect_recovered": True}},
         "abort_conditions": common_abort, "blast_radius": "control plane + one rail",
         "rollback": "scheduler restored at 4,200 s; link restored at 3,900 s"},
    ]


# --------------------------------------------------------------------------- T2 alert rules
def alert_rules() -> list[dict[str, Any]]:
    """Return your alert rules (simulator rule dicts).

    Each rule: ``name``, ``metric``, ``op`` (one of <, >, ==, !=, absent), ``threshold`` (not used by
    absent), ``for_s``, ``severity``, ``detects`` (fault kinds this rule is evidence for). Goals:
    zero alerts on a fault-free 6 h run; every fault kind detected within its target in
    data/gameday_constraints.yaml.
    """
    return [
        {"name": "NodeDown", "metric": "sim_node_up", "op": "==", "threshold": 0, "for_s": 60,
         "severity": "critical", "detects": ["node_loss"]},
        {"name": "NicLinkDown", "metric": "sim_nic_link_up", "op": "==", "threshold": 0, "for_s": 30,
         "severity": "critical", "detects": ["link_down"]},
        # Above the checkpoint stall (step ~17.4 s + 20 s snapshot), held for a minute: no flapping.
        {"name": "JobStalled", "metric": "sim_job_progress_age_seconds", "op": ">", "threshold": 120,
         "for_s": 60, "severity": "critical", "detects": ["link_down", "node_loss"]},
        {"name": "StorageWriteDegraded", "metric": "sim_storage_write_GBps", "op": "<", "threshold": 40,
         "for_s": 60, "severity": "warning", "detects": ["storage_slow"]},
        {"name": "CheckpointStale", "metric": "sim_checkpoint_age_seconds", "op": ">", "threshold": 3600,
         "for_s": 300, "severity": "warning", "detects": ["storage_slow"]},
        {"name": "SchedulerHeartbeatAbsent", "metric": "sim_scheduler_heartbeat", "op": "absent",
         "for_s": 60, "severity": "critical", "detects": ["scheduler_outage"]},
    ]


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
    t0, target = fault["start_s"], fault.get("target")
    window = (tolerance_s or DETECTION_TOLERANCE_S)[fault["kind"]]
    hung = {e["job"] for e in result.events
            if e["kind"] == "job_hung" and e["t"] >= t0 and e.get("cause") == f"{fault['kind']} {target}"}

    def tied(labels: dict[str, str]) -> bool:
        if target and "node" in labels:
            return labels["node"] == target
        if target and "job" in labels:
            return labels["job"] in hung
        return True

    hits = [a["t_fire"] for a in result.alerts
            if fault["kind"] in a.get("detects", []) and t0 <= a["t_fire"] <= t0 + window
            and tied(a.get("labels", {}))]
    return round(min(hits) - t0, 3) if hits else None


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
    t0, kind, target = fault["start_s"], fault["kind"], fault.get("target")
    ev = result.events
    horizon = result.config["horizon_s"]
    end = next((e["t"] for e in ev if e["kind"] == "fault_end" and e.get("fault_id") == fault["id"]), None)
    if kind in NODE_FAULTS:
        mit = next((e["t"] for e in ev if e["kind"] == "node_drained" and e["node"] == target and e["t"] >= t0), None)
    else:
        mit = end
    mitigate_s = None if mit is None else round(mit - t0, 3)

    cause = f"{kind} {target}"
    hangs = [e for e in ev if e["kind"] == "job_hung" and e["t"] >= t0 and e.get("cause") == cause]
    lost_work = idle = 0.0
    resumes: list[float | None] = []
    for h in hangs:
        job = h["job"]
        jc = result.config["jobs"][job]
        gpus = 8 * jc["nodes"]
        restart = next((e for e in ev if e["kind"] == "job_restarted" and e["job"] == job and e["t"] > h["t"]), None)
        if restart is not None:
            restored = restart["from_step"]
        else:
            durable = [e["step"] for e in ev if e["kind"] == "ckpt_durable" and e["job"] == job and e["t"] <= h["t"]]
            restored = durable[-1] if durable else 0
        resumed = next((e["t"] for e in ev if e["kind"] == "job_resumed" and e["job"] == job and e["t"] > h["t"]), None)
        lost_work += gpus * (h["step"] - restored) * jc["step_s"] / 3600
        idle += gpus * ((resumed if resumed is not None else horizon) - h["last_progress_t"]) / 3600
        resumes.append(resumed)
    if hangs:
        recover_s = None if any(r is None for r in resumes) else round(max(resumes) - t0, 3)  # type: ignore[type-var]
    else:
        recover_s = mitigate_s
    return {"detect_s": detection_time(result, fault), "mitigate_s": mitigate_s, "recover_s": recover_s,
            "recovered": recover_s is not None, "lost_work_gpu_h": round(lost_work, 1),
            "idle_gpu_h": round(idle, 1), "lost_gpu_h": round(lost_work + idle, 1)}


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
    base = datetime.strptime(t0_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    end = result.config["horizon_s"] if end_s is None else end_s
    rows = []
    for e in result.events:
        k = e["kind"]
        if k not in TIMELINE_KINDS or not (start_s <= e["t"] <= end):
            continue
        detail = ", ".join(f"{key}={val}" for key, val in sorted(e.items()) if key not in ("t", "kind"))
        rows.append({"t_s": e["t"], "utc": (base + timedelta(seconds=int(e["t"]))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "offset": _offset(e["t"]), "source": TIMELINE_KINDS[k], "event": k, "detail": detail})
    rows.sort(key=lambda r: r["t_s"])
    return rows


# --------------------------------------------------------------------------- T6 hypotheses
def evaluate_hypotheses(scenario: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compare each fault's expected behaviour with observed metrics.

    Returns {fault_id: {detect_ok, lost_ok, recovered_ok, verdict}} where verdict is "held" when all
    three are True, else "failed". A missing detection (None) is never ok.
    """
    out = {}
    for fid, exp in scenario["expected"].items():
        m = metrics[fid]
        d_ok = m["detect_s"] is not None and m["detect_s"] <= exp["detect_within_s"]
        l_ok = m["lost_gpu_h"] <= exp["max_lost_gpu_h"]
        r_ok = m["recovered"] == exp["expect_recovered"]
        out[fid] = {"detect_ok": d_ok, "lost_ok": l_ok, "recovered_ok": r_ok,
                    "verdict": "held" if d_ok and l_ok and r_ok else "failed"}
    return out


# --------------------------------------------------------------------------- T7 backlog
def prioritize_backlog(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Rank reliability backlog items.

    score = annual_events × gpu_h_per_event × expected_reduction / effort_weeks (GPU-hours avoided per
    engineer-week). Order: safety_critical == "true" first, then score descending, then id. Returns
    new dicts with a numeric ``score`` (rounded to 0.1) added.
    """
    ranked = []
    for it in items:
        score = float(it["annual_events"]) * float(it["gpu_h_per_event"]) * float(it["expected_reduction"]) \
            / float(it["effort_weeks"])
        ranked.append({**it, "score": round(score, 1)})
    ranked.sort(key=lambda r: (r["safety_critical"].lower() != "true", -r["score"], r["id"]))
    return ranked
