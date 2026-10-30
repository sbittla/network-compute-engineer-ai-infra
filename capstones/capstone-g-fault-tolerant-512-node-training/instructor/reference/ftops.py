"""Reference implementation — Capstone G fault-tolerant 512-node training operations (INSTRUCTOR ONLY).

Same public API as starter-kit/starter/ftops.py. Pure functions over the SIMULATED incident dataset.
"""
from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

CRITICAL_XIDS = {48, 79, 94, 95}
XID_RE = re.compile(r"NVRM: Xid \(PCI:([0-9a-fA-F:]+)\): (\d+)")
AER_RE = re.compile(r"AER: Corrected error received: ([0-9a-fA-F:.]+)")
LINK_RE = re.compile(r"mlx5_core ([0-9a-fA-F:.]+) \S+: Link (down|up)")
RANK_RE = re.compile(r"^\[rank (\d+)\]")


# --------------------------------------------------------------------------- loaders (given)
def load_dataset(data_dir: Path) -> dict[str, Any]:
    """Load every file in data/ (given; not a TODO)."""
    d = Path(data_dir)
    with open(d / "events.jsonl", encoding="utf-8") as fh:
        events = [json.loads(x) for x in fh if x.strip()]
    with open(d / "ops_log.jsonl", encoding="utf-8") as fh:
        ops = [json.loads(x) for x in fh if x.strip()]
    with open(d / "checkpoints.json", encoding="utf-8") as fh:
        ckpts = json.load(fh)
    with open(d / "config.yaml", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    rd = lambda f: pd.read_csv(d / f, dtype=str, keep_default_na=False)  # noqa: E731
    offsets = {r["host"]: float(r["offset_s"]) for r in csv.DictReader(open(d / "clock_offsets.csv", encoding="utf-8"))}
    return {"inventory": rd("inventory.csv"), "cabling_plan": rd("cabling_plan.csv"), "offsets": offsets,
            "events": events, "progress": pd.read_csv(d / "progress.csv"), "checkpoints": ckpts,
            "quarantine_db": rd("quarantine_db.csv"), "spares": rd("spares.csv"), "ops_log": ops,
            "loss_pre": pd.read_csv(d / "loss_pre.csv"), "resume_validated": pd.read_csv(d / "resume_validated.csv"),
            "resume_unvalidated": pd.read_csv(d / "resume_unvalidated.csv"),
            "resume_dataloader_not_restored": pd.read_csv(d / "resume_dataloader_not_restored.csv"), "config": config,
            "step_times": pd.read_csv(d / "step_times.csv")}


def parse_utc(s: str) -> datetime:
    """Parse ``YYYY-MM-DDTHH:MM:SS.mmmZ`` (or without millis) to an aware UTC datetime (given)."""
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in s else "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)


# --------------------------------------------------------------------------- T1 topology inventory
def build_maps(inventory: pd.DataFrame) -> dict[str, dict]:
    """Build lookup tables from the LLDP-observed rank-to-device inventory.

    Returns dict with:
      ``rank``      {rank:int -> {node, gpu:int, gpu_uuid, gpu_bdf, numa:int, hca, nic_bdf, rail:int, leaf, leaf_port:int}}
      ``gpu_bdf``   {(node, gpu_bdf) -> gpu index}
      ``nic_bdf``   {(node, nic_bdf) -> hca name}
      ``uuid``      {gpu_uuid -> (node, gpu index)}
      ``port``      {(leaf, port:int) -> (node, hca)}   from the INVENTORY (LLDP), not the cabling plan
      ``node_ranks`` {node -> sorted list of ranks}     (spare nodes have none)
    """
    m: dict[str, dict] = {"rank": {}, "gpu_bdf": {}, "nic_bdf": {}, "uuid": {}, "port": {}, "node_ranks": {}}
    for r in inventory.to_dict("records"):
        g = int(r["gpu"])
        m["gpu_bdf"][(r["node"], r["gpu_bdf"])] = g
        m["nic_bdf"][(r["node"], r["nic_bdf"])] = r["hca"]
        m["uuid"][r["gpu_uuid"]] = (r["node"], g)
        m["port"][(r["leaf"], int(r["leaf_port"]))] = (r["node"], r["hca"])
        m["node_ranks"].setdefault(r["node"], [])
        if r["rank"] != "":
            rk = int(r["rank"])
            m["rank"][rk] = {"node": r["node"], "gpu": g, "gpu_uuid": r["gpu_uuid"], "gpu_bdf": r["gpu_bdf"],
                             "numa": int(r["numa"]), "hca": r["hca"], "nic_bdf": r["nic_bdf"],
                             "rail": int(r["rail"]), "leaf": r["leaf"], "leaf_port": int(r["leaf_port"])}
            m["node_ranks"][r["node"]].append(rk)
    for v in m["node_ranks"].values():
        v.sort()
    return m


def cabling_discrepancies(inventory: pd.DataFrame, plan: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows where the LLDP-observed (leaf, port) differs from the DCIM cabling plan, sorted by node, hca."""
    obs = {(r["node"], r["hca"]): (r["leaf"], int(r["leaf_port"])) for r in inventory.to_dict("records")}
    out = []
    for r in plan.to_dict("records"):
        o = obs[(r["node"], r["hca"])]
        if o != (r["leaf"], int(r["port"])):
            out.append({"node": r["node"], "hca": r["hca"], "planned": f"{r['leaf']}:{r['port']}",
                        "observed": f"{o[0]}:{o[1]}"})
    return sorted(out, key=lambda x: (x["node"], x["hca"]))


# --------------------------------------------------------------------------- T2 correlation
def normalize_events(events: list[dict[str, Any]], offsets: dict[str, float], maps: dict[str, dict]) -> pd.DataFrame:
    """Normalise raw events to one table on TRUE time.

    true_utc = host_ts − offset_s(host) (offset = host clock − true time). Columns: utc (datetime),
    host, source, kind, component (e.g. ``gpu:orionxl-n377:5``, ``hca:orionxl-n213:mlx5_3`` or ``""``), xid (int
    or -1), rank (int or -1), field, value (float or NaN). Kinds: xid, aer_corrected, link_down,
    link_up, dcgm, nic_counter, switch_counter, cuda_error, nccl_timeout, scheduler, other.
    GPU components come from the PCI address (Xid prints it without the ``.0`` function), the DCGM
    GPU UUID, or the rank; HCA components from the NIC BDF or, for switch counters, from the LLDP
    port map. Sorted by utc then host.
    """
    rows = []
    for e in events:
        host = e["host"]
        utc = pd.Timestamp(parse_utc(e["host_ts"])) - pd.Timedelta(seconds=offsets.get(host, 0.0))
        kind, comp, xid, rank, field, value = "other", "", -1, -1, "", math.nan
        src, msg = e["source"], e.get("msg", "")
        if src == "kernel":
            if (mm := XID_RE.search(msg)):
                bdf = mm.group(1).lower() + ".0"
                kind, xid = "xid", int(mm.group(2))
                g = maps["gpu_bdf"].get((host, bdf))
                comp = f"gpu:{host}:{g}" if g is not None else ""
            elif (mm := AER_RE.search(msg)):
                kind = "aer_corrected"
                g = maps["gpu_bdf"].get((host, mm.group(1).lower()))
                comp = f"gpu:{host}:{g}" if g is not None else ""
            elif (mm := LINK_RE.search(msg)):
                kind = "link_" + mm.group(2)
                h = maps["nic_bdf"].get((host, mm.group(1).lower()))
                comp = f"hca:{host}:{h}" if h else ""
        elif src == "dcgm":
            kind, field, value = "dcgm", e["field"], float(e["value"])
            node, g = maps["uuid"][e["gpu_uuid"]]
            comp = f"gpu:{node}:{g}"
        elif src == "nic":
            kind, field, value = "nic_counter", e["counter"], float(e["value"])
            comp = f"hca:{host}:{e['hca']}"
        elif src == "switch":
            kind, field, value = "switch_counter", e["counter"], float(e["value"])
            peer = maps["port"].get((host, int(e["port"])))
            comp = f"hca:{peer[0]}:{peer[1]}" if peer else ""
        elif src == "job":
            mm = RANK_RE.search(msg)
            rank = int(mm.group(1)) if mm else -1
            kind = "nccl_timeout" if "Watchdog caught collective operation timeout" in msg else (
                "cuda_error" if "CUDA error" in msg else "other")
            if rank >= 0 and rank in maps["rank"]:
                info = maps["rank"][rank]
                comp = f"gpu:{info['node']}:{info['gpu']}"
        elif src == "scheduler":
            kind = "scheduler"
        rows.append({"utc": utc, "host": host, "source": src, "kind": kind, "component": comp, "xid": xid,
                     "rank": rank, "field": field, "value": value})
    return pd.DataFrame(rows).sort_values(["utc", "host"], kind="stable").reset_index(drop=True)


# --------------------------------------------------------------------------- T3 health scoring
def health_scores(norm: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Score every component with evidence (0–100, capped). Only components scoring > 0 are returned.

    GPU:  critical Xid (48, 79, 94, 95) → 100; DCGM_FI_DEV_ECC_DBE_VOL_TOTAL > 0 → 100;
          DCGM_FI_DEV_ROW_REMAP_PENDING > 0 → 60; Xid 63 → 30;
          max DCGM_FI_DEV_ECC_SBE_VOL_TOTAL ≥ 1,000 → 20 (below: 0 — trended, not scored);
          ≥ 10 corrected AER events → 10.
    HCA:  ≥ 3 ``link_down`` events within any 60-min window → 70; max rx_crc_errors_phy ≥ 1,000 → 20;
          any switch-port counter (via LLDP peer) with value > 0 → 20.
    Returns {component: {"score": int, "evidence": [str]}} with rules summed then capped at 100.
    """
    out: dict[str, dict[str, Any]] = {}

    def add(comp: str, pts: int, why: str) -> None:
        if not comp:
            return
        rec = out.setdefault(comp, {"score": 0, "evidence": []})
        rec["score"] = min(100, rec["score"] + pts)
        rec["evidence"].append(why)

    for comp, g in norm[norm["component"] != ""].groupby("component"):
        if comp.startswith("gpu:"):
            xids = set(g.loc[g["kind"] == "xid", "xid"])
            if xids & CRITICAL_XIDS:
                add(comp, 100, f"critical Xid {sorted(xids & CRITICAL_XIDS)}")
            dc = g[g["kind"] == "dcgm"]
            if (dc.loc[dc["field"] == "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL", "value"] > 0).any():
                add(comp, 100, "uncorrectable (DBE) ECC")
            if (dc.loc[dc["field"] == "DCGM_FI_DEV_ROW_REMAP_PENDING", "value"] > 0).any():
                add(comp, 60, "row remap pending")
            if 63 in xids:
                add(comp, 30, "Xid 63 row-remap event")
            sbe = dc.loc[dc["field"] == "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL", "value"]
            if len(sbe) and sbe.max() >= 1000:
                add(comp, 20, f"high correctable ECC ({int(sbe.max())})")
            n_aer = int((g["kind"] == "aer_corrected").sum())
            if n_aer >= 10:
                add(comp, 10, f"{n_aer} corrected AER events")
        elif comp.startswith("hca:"):
            downs = g.loc[g["kind"] == "link_down", "utc"].sort_values().tolist()
            if any(sum(1 for x in downs if t <= x < t + pd.Timedelta(minutes=60)) >= 3 for t in downs):
                add(comp, 70, f"{len(downs)} link flaps")
            crc = g.loc[(g["kind"] == "nic_counter") & (g["field"] == "rx_crc_errors_phy"), "value"]
            if len(crc) and crc.max() >= 1000:
                add(comp, 20, f"rx_crc_errors_phy {int(crc.max())}")
            sw = g[(g["kind"] == "switch_counter") & (g["value"] > 0)]
            if len(sw):
                add(comp, 20, "switch-port errors on LLDP peer port")
    return out


# --------------------------------------------------------------------------- T4 classification
def classify(norm: pd.DataFrame, scores: dict[str, dict[str, Any]], progress: pd.DataFrame,
             maps: dict[str, dict], scoring: dict[str, int]) -> dict[str, Any]:
    """Classify the incident: proven cause vs correlated/independent faults vs watch items.

    * first_stalled_ranks: ranks with the LOWEST ``last_collective_seq`` (they never enqueued the
      collective everyone else is waiting in). Timestamps are not used: host clocks can be skewed.
    * proven_cause: the GPU component of a first-stalled rank whose score ≥ quarantine_at and that
      has a critical event (critical Xid or DBE) — its earliest such event (true time) is fault_utc.
      None if no such component.
    * independent_faults: other components with score ≥ quarantine_at (sorted).
    * watch: components with watch_at ≤ score < quarantine_at (sorted).
    Returns {first_stalled_ranks, proven_cause, fault_utc (pd.Timestamp or None), independent_faults, watch}.
    """
    low = progress["last_collective_seq"].min()
    first = sorted(int(r) for r in progress.loc[progress["last_collective_seq"] == low, "rank"])
    q, w = scoring["quarantine_at"], scoring["watch_at"]
    proven, fault_utc = None, None
    for r in first:
        info = maps["rank"][r]
        comp = f"gpu:{info['node']}:{info['gpu']}"
        if scores.get(comp, {"score": 0})["score"] >= q:
            crit = norm[(norm["component"] == comp) & (
                (norm["xid"].isin(CRITICAL_XIDS)) |
                ((norm["field"] == "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL") & (norm["value"] > 0)))]
            if len(crit):
                proven, fault_utc = comp, crit["utc"].min()
                break
    indep = sorted(c for c, s in scores.items() if s["score"] >= q and c != proven)
    watch = sorted(c for c, s in scores.items() if w <= s["score"] < q)
    return {"first_stalled_ranks": first, "proven_cause": proven, "fault_utc": fault_utc,
            "independent_faults": indep, "watch": watch}


# --------------------------------------------------------------------------- T5 quarantine
def quarantine_plan(classification: dict[str, Any], maps: dict[str, dict]) -> list[dict[str, Any]]:
    """Turn the classification into actions, sorted by (action, component).

    * proven cause and independent faults → ``quarantine`` the component (smallest repair domain:
      the GPU or the HCA/link), with ``drain_node`` = its node (the job's placement unit is a whole
      node: TP = 8 needs all 8 GPUs; rail alignment needs all 8 HCAs).
    * each quarantined HCA → also ``fabric_ticket`` for its LLDP peer ``switchport:<leaf>:<port>``.
    * watch items → ``watch`` (ticket only, no drain).
    Each action: {component, action, drain_node (str or ""), reason}.
    """
    acts = []
    bad = ([classification["proven_cause"]] if classification["proven_cause"] else []) + \
        list(classification["independent_faults"])
    peer = {v: k for k, v in maps["port"].items()}
    for c in bad:
        _, node, dev = c.split(":")
        reason = "proven cause of the hang" if c == classification["proven_cause"] else "independent fault"
        acts.append({"component": c, "action": "quarantine", "drain_node": node, "reason": reason})
        if c.startswith("hca:"):
            leaf, port = peer[(node, dev)]
            acts.append({"component": f"switchport:{leaf}:{port}", "action": "fabric_ticket", "drain_node": "",
                         "reason": f"peer of {c}: inspect optic/cable"})
    for c in classification["watch"]:
        acts.append({"component": c, "action": "watch", "drain_node": "", "reason": "below quarantine threshold"})
    return sorted(acts, key=lambda a: (a["action"], a["component"]))


# --------------------------------------------------------------------------- T6 checkpoint selection
def select_checkpoint(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the newest checkpoint that is restorable.

    Restorable = metadata committed AND no missing shards AND no checksum failures. Returns
    {"step": int, "rejected": {step: [reasons]}} where rejected lists every NEWER checkpoint and why.
    Raises ValueError if none is restorable.
    """
    rejected: dict[int, list[str]] = {}
    for c in sorted(catalog, key=lambda x: -x["step"]):
        why = []
        if not c["metadata_committed"]:
            why.append("metadata not committed")
        if c["missing_shards"]:
            why.append(f"{len(c['missing_shards'])} missing shards")
        if c["checksum_failures"]:
            why.append(f"checksum failure on shards {c['checksum_failures']}")
        if not why:
            return {"step": c["step"], "rejected": rejected}
        rejected[c["step"]] = why
    raise ValueError("no restorable checkpoint")


# --------------------------------------------------------------------------- T7 restart orchestration
def restart_plan(maps: dict[str, dict], drain_nodes: list[str], spares: pd.DataFrame,
                 quarantine_db: pd.DataFrame) -> dict[str, Any]:
    """Replace drained nodes with eligible spares and remap their ranks.

    Eligible spare: sched_state ``idle``, acceptance ``passed``, no OPEN quarantine record on any of
    its components, and not itself being drained. Drained nodes (sorted) are paired with eligible
    spares (sorted). Each rank keeps its GPU index (so rail = GPU index is preserved).
    Returns {"replacements": {old: new}, "rank_map": {rank: {"node": new, "gpu": idx}},
             "excluded_spares": {node: reason}}. Raises ValueError if there are not enough spares.
    """
    open_nodes = {c.split(":")[1] for c in quarantine_db.loc[quarantine_db["state"] == "open", "component"]}
    excluded, eligible = {}, []
    for r in spares.sort_values("node").to_dict("records"):
        n = r["node"]
        if r["sched_state"] != "idle":
            excluded[n] = f"sched_state {r['sched_state']}"
        elif r["acceptance"] != "passed":
            excluded[n] = f"acceptance {r['acceptance']}"
        elif n in open_nodes:
            excluded[n] = "open quarantine record"
        elif n in drain_nodes:
            excluded[n] = "being drained"
        else:
            eligible.append(n)
    olds = sorted(drain_nodes)
    if len(eligible) < len(olds):
        raise ValueError("not enough eligible spares")
    repl = dict(zip(olds, eligible))
    rank_map = {}
    for old, new in repl.items():
        for rk in maps["node_ranks"].get(old, []):
            rank_map[rk] = {"node": new, "gpu": maps["rank"][rk]["gpu"]}
    return {"replacements": repl, "rank_map": rank_map,
            "excluded_spares": excluded}


# --------------------------------------------------------------------------- T8 recovery metrics
def recovery_metrics(ops_log: list[dict[str, Any]], fault_utc: pd.Timestamp, last_completed_step: int,
                     restored_step: int, config: dict[str, Any]) -> dict[str, Any]:
    """Detection, isolation, RTO, RPO and lost GPU-hours against the targets in config.

    detect_s  = first ``alert`` − fault;  isolate_s = last ``quarantine``/``drain`` − fault;
    rto_s     = ``first_step`` − fault;   rpo_steps = last_completed_step − restored_step;
    rpo_s     = rpo_steps × step_s;       lost_gpu_h = gpus × (rpo_s + rto_s) / 3600.
    ``meets`` = {detect, isolate, rto, rpo} booleans vs config['targets'] (rpo compares steps).
    Times in seconds rounded to 0.1; lost_gpu_h rounded to 0.1.
    """
    def t(a: str) -> list[float]:
        return [(pd.Timestamp(parse_utc(o["utc"])) - fault_utc).total_seconds() for o in ops_log if o["action"] == a]

    job, tg = config["job"], config["targets"]
    detect = min(t("alert"))
    isolate = max(t("quarantine") + t("drain"))
    rto = min(t("first_step"))
    rpo_steps = last_completed_step - restored_step
    rpo_s = rpo_steps * job["step_s"]
    lost = job["gpus"] * (rpo_s + rto) / 3600
    return {"detect_s": round(detect, 1), "isolate_s": round(isolate, 1), "rto_s": round(rto, 1),
            "rpo_steps": rpo_steps, "rpo_s": round(rpo_s, 1), "lost_gpu_h": round(lost, 1),
            "meets": {"detect": detect <= tg["detect_s"], "isolate": isolate <= tg["isolate_s"],
                      "rto": rto <= tg["rto_s"], "rpo": rpo_steps <= tg["rpo_steps"]}}


# --------------------------------------------------------------------------- T9 post-incident validation
def validate_resume(pre: pd.DataFrame, resumed: pd.DataFrame, restored_step: int, tol: float = 1e-3) -> dict[str, Any]:
    """Prove the job resumed correctly from ``restored_step``.

    first_step_ok   first resumed step == restored_step + 1 and steps strictly increase.
    no_nan          no NaN/inf in resumed loss or grad_norm.
    sample_idx_ok   on every overlapping step the data-loader sample index is IDENTICAL (data order
                    and RNG state were restored, not just the weights).
    continuity_ok   on every overlapping step |resumed − pre| / pre ≤ tol for loss AND grad_norm.
    progressed      the resumed log goes past the last pre-fault step.

    ``tol`` comes from replay noise, not from the size of the loss: a correct restore replays the same
    samples in the same order, so the only differences come from non-deterministic reductions. In
    this dataset that noise has σ ≈ 2e-4 (relative), and the validated resume's worst step over 323
    replayed steps deviates 6.5e-4 — 65 % of the 1e-3 tolerance, a 35 % margin. The data-loader bug
    deviates 2.4e-3 (2.4× the tolerance) and also fails the exact sample-index check. The loss changes
    by ≈ 8e-4 on average between consecutive steps, so a 1 % tolerance could not even detect a
    one-step offset. On real hardware, measure the replay noise first (restore the same checkpoint
    twice) and set the tolerance a few σ above the observed maximum.
    Returns those booleans, ``max_rel_dev`` (loss) and ``ok`` (all true).
    """
    res = resumed.copy()
    for col in ("loss", "grad_norm"):
        res[col] = pd.to_numeric(res[col], errors="coerce")
    first_ok = int(res["step"].iloc[0]) == restored_step + 1 and bool(res["step"].diff().dropna().gt(0).all())
    vals = res[["loss", "grad_norm"]]
    no_nan = bool(vals.notna().all().all() and (vals.abs() != float("inf")).all().all())
    m = pre.merge(res, on="step", suffixes=("_pre", "_res"))
    dev = ((m["loss_res"] - m["loss_pre"]).abs() / m["loss_pre"]).fillna(float("inf"))
    gdev = ((m["grad_norm_res"] - m["grad_norm_pre"]).abs() / m["grad_norm_pre"]).fillna(float("inf"))
    max_dev = float(dev.max()) if len(dev) else float("inf")
    cont = len(m) > 0 and max_dev <= tol and float(gdev.max()) <= tol
    samp = len(m) > 0 and bool((m["sample_idx_res"] == m["sample_idx_pre"]).all())
    prog = int(res["step"].max()) > int(pre["step"].max())
    return {"first_step_ok": first_ok, "no_nan": no_nan, "sample_idx_ok": samp, "continuity_ok": cont,
            "progressed": prog, "max_rel_dev": max_dev, "ok": first_ok and no_nan and samp and cont and prog}
