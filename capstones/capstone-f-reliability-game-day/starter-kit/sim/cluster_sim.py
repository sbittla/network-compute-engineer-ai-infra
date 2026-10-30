"""ORION game-day simulator — a seeded discrete-event model of a GPU cluster (GIVEN; not a TODO).

What it models
--------------
* 32 HX8 nodes (8 GPUs, 8 backend rails each) in 8 racks: rack-01–rack-06 run the training job ``train``
  (24 nodes, 192 GPUs, W-TRAIN at TP 8 x PP 4 x DP 6, global batch 768), orion-n25 and orion-n26
  run the fine-tune job ``ft`` (16 GPUs), orion-n27 and orion-n28 are idle spares, and rack-08
  (orion-n29..n32) hosts the inference service (4 replicas). Fine-tune, spares and the 4-replica
  inference service are a declared VARIATION of the default 8-node inference partition.
* Synchronous training steps with small seeded jitter; periodic checkpoints with a synchronous
  snapshot stall followed by an asynchronous write; concurrent writes share the storage write
  bandwidth equally, and a write's speed follows storage health. A
  checkpoint becomes *durable* only when its write completes; losing a member node during the
  write aborts it. A trigger while a write is in flight is skipped.
* Collective hang on member-node loss or backend link loss; job failure after the collective
  timeout (or immediately on health-controller detection with ``fast_fail``).
* A health controller that drains nodes whose node/link signal has been bad for ``health_for_s``;
  drains need the scheduler. A scheduler that requeues failed jobs onto healthy nodes (spares
  first), launches them, and reloads the last durable checkpoint at storage read bandwidth.
* A Prometheus-like scrape every ``scrape_s`` and alert rules with ``for`` durations, including an
  ``absent`` operator for series that stop being exported.

What it does NOT capture (state this in every report)
-----------------------------------------------------
Network congestion and partial bandwidth loss, NCCL algorithm behaviour, per-rank stragglers,
storage metadata contention, real exporter staleness semantics, Slurm scheduling policy and
backfill, GPU errors (Xid/ECC), human response time, and anything about real hardware. Every
number it produces is ``[SIMULATED]``.

Metric names are prefixed ``sim_`` on purpose: they are simulator series, not the names of any
real exporter. The capstone README maps each one to its real-world counterpart.
"""
from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any

import numpy as np

FAULT_KINDS = ("link_down", "node_loss", "storage_slow", "scheduler_outage")

DEFAULT_CONFIG: dict[str, Any] = {
    "horizon_s": 21600,
    "scrape_s": 15,
    "seed": 7,
    "nccl_timeout_s": 600,
    "health_for_s": 60,
    "fast_fail": False,
    "launch_s": 280,
    "storage_write_GBps": 80.0,
    "storage_read_GBps": 160.0,
    "jobs": {
        "train": {"nodes": 24, "step_s": 17.4, "ckpt_interval_s": 1800, "ckpt_GB": 980.0, "ckpt_stall_s": 20.0},
        "ft": {"nodes": 2, "step_s": 2.0, "ckpt_interval_s": 600, "ckpt_GB": 28.0, "ckpt_stall_s": 5.0},
    },
}


def node_names() -> list[str]:
    return [f"orion-n{i:02d}" for i in range(1, 33)]


def initial_placement() -> dict[str, list[str]]:
    nodes = node_names()
    return {"train": nodes[:24], "ft": nodes[24:26], "spare": nodes[26:28], "inference": nodes[28:32]}


@dataclass
class Job:
    name: str
    gpus: int
    step_s: float
    ckpt_interval_s: float
    ckpt_GB: float
    ckpt_stall_s: float
    nodes: list[str]
    state: str = "running"          # running | hung | failed | restarting
    step: int = 0
    last_progress_t: float = 0.0
    awaiting_first_step: bool = False
    last_trigger_t: float = 0.0
    durable_step: int = 0
    durable_t: float = 0.0
    write: dict | None = None       # in-flight checkpoint write
    token: int = 0                  # invalidates stale step events


@dataclass
class SimResult:
    events: list[dict]
    alerts: list[dict]
    config: dict
    final: dict = field(default_factory=dict)


class _Sim:
    def __init__(self, faults: list[dict], rules: list[dict], config: dict) -> None:
        self.cfg = config
        self.rng = np.random.default_rng(config["seed"])
        self.q: list = []
        self.seq = itertools.count()
        self.events: list[dict] = []
        self.rules = rules
        self.alert_state: dict[tuple, dict] = {}
        self.alerts: list[dict] = []
        place = initial_placement()
        self.spares = list(place["spare"])
        self.inference_nodes = list(place["inference"])
        self.node_up = {n: True for n in node_names()}
        self.link_up = {(n, r): True for n in node_names() for r in range(8)}
        self.bad_since: dict[str, float] = {}
        self.drained: set[str] = set()
        self.pending_drain: set[str] = set()
        self.sched_up = True
        self.storage_factor = 1.0
        self.bw_each = config["storage_write_GBps"]
        self.queue: list[str] = []
        self.blocked_logged: set[str] = set()
        self.jobs: dict[str, Job] = {}
        for name, jc in config["jobs"].items():
            self.jobs[name] = Job(name=name, gpus=8 * jc["nodes"], step_s=jc["step_s"],
                                  ckpt_interval_s=jc["ckpt_interval_s"], ckpt_GB=jc["ckpt_GB"],
                                  ckpt_stall_s=jc["ckpt_stall_s"], nodes=list(place[name]))
        for f in faults:
            self._push(f["start_s"], "fault_start", f)
            if f.get("duration_s"):
                self._push(f["start_s"] + f["duration_s"], "fault_end", f)
        for j in self.jobs.values():
            self._schedule_step(j, 0.0)
        t = 0.0
        while t <= config["horizon_s"]:
            self._push(t, "scrape", None)
            t += config["scrape_s"]

    # ------------------------------------------------------------------ plumbing
    def _push(self, t: float, kind: str, payload: Any) -> None:
        heapq.heappush(self.q, (round(t, 3), next(self.seq), kind, payload))

    def _log(self, t: float, kind: str, **kw: Any) -> None:
        self.events.append({"t": round(t, 3), "kind": kind, **kw})

    def _storage_w(self) -> float:
        return self.cfg["storage_write_GBps"] * self.storage_factor

    def _storage_r(self) -> float:
        return self.cfg["storage_read_GBps"] * self.storage_factor

    def _node_healthy(self, n: str) -> bool:
        return self.node_up[n] and all(self.link_up[(n, r)] for r in range(8))

    # ------------------------------------------------------------------ job mechanics
    def _schedule_step(self, j: Job, t: float, extra: float = 0.0) -> None:
        j.token += 1
        dur = j.step_s * (1.0 + float(self.rng.normal(0.0, 0.01))) + extra
        self._push(t + dur, "step", (j.name, j.token))

    def _on_step(self, t: float, name: str, token: int) -> None:
        j = self.jobs[name]
        if token != j.token or j.state != "running":
            return
        j.step += 1
        first_after_restart = j.awaiting_first_step
        j.awaiting_first_step = False
        j.last_progress_t = t
        if first_after_restart:
            self._log(t, "job_resumed", job=name, step=j.step)
        stall = 0.0
        if t - j.last_trigger_t >= j.ckpt_interval_s:
            j.last_trigger_t = t
            if j.write is not None:
                self._log(t, "ckpt_skipped", job=name, step=j.step, reason="previous write in flight")
            else:
                stall = j.ckpt_stall_s
                self._log(t, "ckpt_started", job=name, step=j.step)
                j.write = {"step": j.step, "remaining_GB": j.ckpt_GB, "since": t + stall, "token": 0}
                self._push(t + stall, "write_start", None)
        self._schedule_step(j, t, extra=stall)

    def _advance_writes(self, t: float) -> None:
        for j in self.jobs.values():
            w = j.write
            if w is not None and t > w["since"]:
                w["remaining_GB"] = max(0.0, w["remaining_GB"] - (t - w["since"]) * self.bw_each)
                w["since"] = t

    def _rebalance(self, t: float) -> None:
        """Share storage write bandwidth equally among the writes in progress and reschedule them."""
        self._advance_writes(t)
        active = [j for j in self.jobs.values() if j.write is not None and j.write["since"] <= t]
        self.bw_each = self._storage_w() / max(1, len(active))
        for j in active:
            w = j.write
            w["token"] += 1
            self._push(t + w["remaining_GB"] / self.bw_each, "ckpt_done", (j.name, w["token"]))

    def _on_ckpt_done(self, t: float, name: str, token: int) -> None:
        j = self.jobs[name]
        w = j.write
        if w is None or token != w["token"]:
            return
        self._advance_writes(t)
        j.durable_step, j.durable_t, j.write = w["step"], t, None
        self._log(t, "ckpt_durable", job=name, step=w["step"])
        self._rebalance(t)

    def _hang(self, t: float, j: Job, cause: str) -> None:
        if j.state != "running":
            return
        j.state = "hung"
        j.token += 1
        self._log(t, "job_hung", job=j.name, step=j.step, cause=cause, last_progress_t=round(j.last_progress_t, 3))
        self._push(t + self.cfg["nccl_timeout_s"], "nccl_timeout", (j.name, j.token))

    def _fail(self, t: float, j: Job, reason: str) -> None:
        if j.state not in ("hung", "running"):
            return
        j.state = "failed"
        j.token += 1
        self._log(t, "job_failed", job=j.name, step=j.step, reason=reason)
        if j.write is not None:
            self._log(t, "ckpt_aborted", job=j.name, step=j.write["step"], reason="job failed during write")
            self._advance_writes(t)
            j.write = None
            self._rebalance(t)
        self.queue.append(j.name)
        self._try_requeue(t)

    def _try_requeue(self, t: float) -> None:
        if not self.sched_up:
            return
        for name in list(self.queue):
            j = self.jobs[name]
            keep = [n for n in j.nodes if n not in self.drained and self.node_up[n]]
            need = len(j.nodes) - len(keep)
            avail = [n for n in self.spares if n not in self.drained and self.node_up[n]]
            if need > len(avail):
                if name not in self.blocked_logged:
                    self._log(t, "requeue_blocked", job=name, need=need, available=len(avail))
                    self.blocked_logged.add(name)
                continue
            self.blocked_logged.discard(name)
            use = avail[:need]
            for n in use:
                self.spares.remove(n)
            for n in j.nodes:
                if n not in keep:
                    self.spares.append(n)  # returned to pool (drained/down nodes stay excluded)
            j.nodes = keep + use
            self.queue.remove(name)
            j.state = "restarting"
            load = j.ckpt_GB / self._storage_r()
            self._log(t, "job_requeued", job=name, replaced=need, nodes_added=use)
            self._push(t + self.cfg["launch_s"] + load, "restart_done", name)

    def _on_restart_done(self, t: float, name: str) -> None:
        j = self.jobs[name]
        if j.state != "restarting":
            return
        if not all(self._node_healthy(n) for n in j.nodes):
            j.state = "running"   # last_progress_t is NOT reset: no step has completed
            self._hang(t, j, cause="unhealthy node at restart")
            return
        j.state = "running"
        lost = j.step - j.durable_step
        self._log(t, "job_restarted", job=name, from_step=j.durable_step, steps_lost=lost)
        j.step = j.durable_step
        j.awaiting_first_step = True   # progress age keeps counting until a step completes
        j.last_trigger_t = t
        self._schedule_step(j, t)

    # ------------------------------------------------------------------ faults
    def _on_fault(self, t: float, f: dict, start: bool) -> None:
        kind = f["kind"]
        self._log(t, "fault_start" if start else "fault_end", fault_id=f["id"], fault=kind,
                  target=f.get("target"), rail=f.get("rail"))
        self._advance_writes(t)
        if kind == "storage_slow":
            self.storage_factor = f.get("factor", 0.1) if start else 1.0
            self._rebalance(t)
            return
        if kind == "scheduler_outage":
            self.sched_up = not start
            if not start:
                for n in sorted(self.pending_drain):
                    self._drain(t, n)
                self.pending_drain.clear()
                self._try_requeue(t)
            return
        node = f["target"]
        if kind == "node_loss":
            self.node_up[node] = not start
        elif kind == "link_down":
            self.link_up[(node, int(f["rail"]))] = not start
        if start:
            for j in self.jobs.values():
                if node in j.nodes:
                    if kind == "node_loss" and j.write is not None:
                        self._log(t, "ckpt_aborted", job=j.name, step=j.write["step"],
                                  reason=f"writer on {node} lost")
                        self._advance_writes(t)
                        j.write = None
                        self._rebalance(t)
                    self._hang(t, j, cause=f"{kind} {node}")

    def _drain(self, t: float, node: str) -> None:
        if node in self.drained:
            return
        if not self.sched_up:
            if node not in self.pending_drain:
                self.pending_drain.add(node)
                self._log(t, "drain_pending", node=node, reason="scheduler unavailable")
            return
        self.drained.add(node)
        self._log(t, "node_drained", node=node)
        self._try_requeue(t)

    # ------------------------------------------------------------------ scrape + alerts
    def _sample(self, t: float) -> dict[tuple, float]:
        s: dict[tuple, float] = {}
        for n in node_names():
            s[("sim_node_up", (("node", n),))] = 1.0 if self.node_up[n] else 0.0
            if self.node_up[n]:
                for r in range(8):
                    s[("sim_nic_link_up", (("node", n), ("rail", str(r))))] = 1.0 if self.link_up[(n, r)] else 0.0
        for j in self.jobs.values():
            age = t - j.last_progress_t
            s[("sim_job_progress_age_seconds", (("job", j.name),))] = round(age, 1)
            s[("sim_job_running", (("job", j.name),))] = 1.0 if j.state == "running" else 0.0
            s[("sim_checkpoint_age_seconds", (("job", j.name),))] = round(t - j.durable_t, 1)
        s[("sim_storage_write_GBps", ())] = round(self._storage_w(), 2)
        if self.sched_up:
            s[("sim_scheduler_heartbeat", ())] = 1.0
        s[("sim_inference_ready_replicas", ())] = float(sum(1 for n in self.inference_nodes if self._node_healthy(n)))
        return s

    def _health_controller(self, t: float) -> None:
        for n in node_names():
            if self._node_healthy(n):
                self.bad_since.pop(n, None)
                continue
            since = self.bad_since.setdefault(n, t)
            if t - since >= self.cfg["health_for_s"] and n not in self.drained:
                # Drain first so a fast-failed job is never requeued onto the node that caused it.
                self._drain(t, n)
                if self.cfg["fast_fail"]:
                    for j in self.jobs.values():
                        if n in j.nodes and j.state == "hung":
                            self._fail(t, j, reason=f"fast-fail: health controller saw {n} unhealthy")

    def _eval_rules(self, t: float, sample: dict[tuple, float]) -> None:
        for rule in self.rules:
            m, op, thr = rule["metric"], rule["op"], rule.get("threshold", 0.0)
            if op == "absent":
                present = any(k[0] == m for k in sample)
                cands = {(): (not present)}
            else:
                cands = {}
                for (metric, labels), v in sample.items():
                    if metric != m:
                        continue
                    cands[labels] = {"<": v < thr, ">": v > thr, "==": v == thr, "!=": v != thr}[op]
            for labels, cond in cands.items():
                key = (rule["name"], labels)
                st = self.alert_state.get(key)
                if cond:
                    if st is None:
                        st = {"pending_since": t, "alert": None}
                        self.alert_state[key] = st
                    if st["alert"] is None and t - st["pending_since"] >= rule.get("for_s", 0):
                        a = {"rule": rule["name"], "labels": dict(labels), "severity": rule.get("severity", "warning"),
                             "detects": list(rule.get("detects", [])), "t_fire": t, "t_resolve": None}
                        st["alert"] = a
                        self.alerts.append(a)
                        self._log(t, "alert_firing", rule=rule["name"], labels=dict(labels))
                elif st is not None:
                    if st["alert"] is not None:
                        st["alert"]["t_resolve"] = t
                        self._log(t, "alert_resolved", rule=rule["name"], labels=dict(labels))
                    del self.alert_state[key]

    # ------------------------------------------------------------------ main loop
    def run(self) -> SimResult:
        horizon = self.cfg["horizon_s"]
        while self.q:
            t, _, kind, p = heapq.heappop(self.q)
            if t > horizon:
                break
            if kind == "scrape":
                self._advance_writes(t)
                self._health_controller(t)
                self._eval_rules(t, self._sample(t))
            elif kind == "step":
                self._on_step(t, *p)
            elif kind == "write_start":
                self._rebalance(t)
            elif kind == "ckpt_done":
                self._on_ckpt_done(t, *p)
            elif kind == "nccl_timeout":
                j = self.jobs[p[0]]
                if p[1] == j.token and j.state == "hung":
                    self._fail(t, j, reason="collective timeout")
            elif kind == "restart_done":
                self._on_restart_done(t, p)
            elif kind == "fault_start":
                self._on_fault(t, p, True)
            elif kind == "fault_end":
                self._on_fault(t, p, False)
        final = {name: {"state": j.state, "step": j.step, "durable_step": j.durable_step, "nodes": list(j.nodes)}
                 for name, j in self.jobs.items()}
        final["drained"] = sorted(self.drained)
        return SimResult(events=self.events, alerts=self.alerts, config=self.cfg, final=final)


def validate_faults(faults: list[dict], horizon_s: float) -> None:
    """Raise ValueError for malformed fault specs (unknown kind, bad target, outside horizon)."""
    nodes = set(node_names())
    for f in faults:
        if f.get("kind") not in FAULT_KINDS:
            raise ValueError(f"{f.get('id')}: unknown fault kind {f.get('kind')!r}")
        if f["kind"] in ("link_down", "node_loss") and f.get("target") not in nodes:
            raise ValueError(f"{f.get('id')}: target {f.get('target')!r} is not an ORION node")
        if f["kind"] == "link_down" and int(f.get("rail", -1)) not in range(8):
            raise ValueError(f"{f.get('id')}: rail must be 0..7")
        if not 0 <= f["start_s"] < horizon_s:
            raise ValueError(f"{f.get('id')}: start_s outside the horizon")


def run(faults: list[dict], rules: list[dict], config: dict | None = None) -> SimResult:
    """Run one simulated game day. ``faults`` and ``rules`` are plain dicts (see the README).

    Deterministic: the same faults, rules and config always produce the same result.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    cfg["jobs"] = {**DEFAULT_CONFIG["jobs"], **(config or {}).get("jobs", {})}
    validate_faults(faults, cfg["horizon_s"])
    return _Sim(faults, rules, cfg).run()


def save_result(result: SimResult, out_dir: Any, prefix: str) -> None:
    """Write ``<prefix>_events.jsonl``, ``<prefix>_alerts.jsonl`` and ``<prefix>_final.json``."""
    import json
    from pathlib import Path

    out = Path(out_dir)
    with open(out / f"{prefix}_events.jsonl", "w", newline="\n", encoding="utf-8") as fh:
        fh.writelines(json.dumps(e, sort_keys=True) + "\n" for e in result.events)
    with open(out / f"{prefix}_alerts.jsonl", "w", newline="\n", encoding="utf-8") as fh:
        fh.writelines(json.dumps(a, sort_keys=True) + "\n" for a in result.alerts)
    cfg = {k: v for k, v in result.config.items()}
    with open(out / f"{prefix}_final.json", "w", newline="\n", encoding="utf-8") as fh:
        fh.write(json.dumps({"final": result.final, "config": cfg}, sort_keys=True, indent=1) + "\n")


def load_result(data_dir: Any, prefix: str) -> SimResult:
    """Load a recorded run written by :func:`save_result`."""
    import json
    from pathlib import Path

    d = Path(data_dir)
    with open(d / f"{prefix}_events.jsonl", encoding="utf-8") as fh:
        events = [json.loads(x) for x in fh if x.strip()]
    with open(d / f"{prefix}_alerts.jsonl", encoding="utf-8") as fh:
        alerts = [json.loads(x) for x in fh if x.strip()]
    with open(d / f"{prefix}_final.json", encoding="utf-8") as fh:
        meta = json.load(fh)
    return SimResult(events=events, alerts=alerts, config=meta["config"], final=meta["final"])
