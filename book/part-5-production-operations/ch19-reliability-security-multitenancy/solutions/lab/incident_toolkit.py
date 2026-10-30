"""Chapter 19 lab - ORION-XL incident correlation, containment, recovery, FMEA, and tenant isolation.

REFERENCE SOLUTION (instructors). Same public API as lab/starter/incident_toolkit.py.

Timestamps are timezone-aware pandas Timestamps (UTC). Durations are minutes unless stated;
accelerator time is in GPU-hours.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

XID_RE = re.compile(r"NVRM: Xid \(PCI:([0-9A-Fa-f]{4}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})\): (\d+)")
NETIB_RE = re.compile(r"NET/IB : Got completion from peer ([0-9.]+)<\d+> with status=(\d+).*?hca (mlx5_\d+)")


# --------------------------------------------------------------------------- loading (given)
def load_incident(data_dir: Path) -> dict[str, Any]:
    """Load every file of the incident dataset. Provided complete in the starter."""
    d = Path(data_dir)
    b: dict[str, Any] = {name: pd.read_csv(d / f"{name}.csv") for name in (
        "rank_map", "rank_progress", "gpu_health", "host_nic_snapshot", "switch_port_counters",
        "checkpoints", "restart_history", "spares", "fmea")}
    for name, cols in (("switch_port_counters", ["ts"]), ("checkpoints", ["start_ts", "end_ts"]),
                       ("restart_history", ["start_ts", "end_ts"]), ("rank_progress", ["watchdog_timeout_ts"])):
        for c in cols:
            b[name][c] = pd.to_datetime(b[name][c], utc=True)
    with open(d / "events.jsonl", encoding="utf-8") as fh:
        ev = pd.DataFrame([json.loads(x) for x in fh if x.strip()])
    ev["ts"] = pd.to_datetime(ev["ts"], utc=True)
    b["events"] = ev.sort_values("ts").reset_index(drop=True)
    for name in ("hypotheses", "tenants", "isolation_policy"):
        b[name] = yaml.safe_load((d / f"{name}.yaml").read_text(encoding="utf-8"))
    return b


# --------------------------------------------------------------------------- Task 1: parsing + mapping
def parse_xid(line: str) -> dict[str, Any] | None:
    """Parse an `NVRM: Xid (PCI:dddd:bb:dd): N, ...` kernel line -> {"pci": "dddd:bb:dd", "xid": N}.
    Return None for any other line. PCI address lower-cased."""
    m = XID_RE.search(line)
    return {"pci": m.group(1).lower(), "xid": int(m.group(2))} if m else None


def parse_netib(line: str) -> dict[str, Any] | None:
    """Parse an NCCL `NET/IB : Got completion from peer <ip><port> with status=S ... hca mlx5_N` line
    -> {"peer_ip", "status", "hca"}; None otherwise."""
    m = NETIB_RE.search(line)
    return {"peer_ip": m.group(1), "status": int(m.group(2)), "hca": m.group(3)} if m else None


def rank_to_hardware(rank_map: pd.DataFrame, rank: int) -> dict[str, Any]:
    """Return the full hardware path of a rank as a dict (node, GPU UUID/BDF, NUMA, HCA/BDF, rail,
    leaf, leaf_port, backend_ip, pp_stage, dp_index)."""
    row = rank_map[rank_map["rank"] == rank]
    if row.empty:
        raise KeyError(rank)
    return row.iloc[0].to_dict()


def gpu_bdf_to_rank(rank_map: pd.DataFrame, node: str, pci: str) -> int:
    """Map an Xid's PCI address (dddd:bb:dd) on `node` to the rank using that GPU."""
    m = rank_map[(rank_map.node == node) & (rank_map.gpu_bdf.str.lower().str.startswith(pci.lower()))]
    if m.empty:
        raise KeyError((node, pci))
    return int(m["rank"].iloc[0])


# --------------------------------------------------------------------------- Task 2: localisation
def stuck_ranks(rank_progress: pd.DataFrame) -> list[int]:
    """Ranks whose last completed collective sequence number is the minimum (they are behind)."""
    lo = rank_progress.last_completed_seq.min()
    return sorted(int(r) for r in rank_progress[rank_progress.last_completed_seq == lo]["rank"])


def common_hardware(rank_map: pd.DataFrame, ranks: list[int]) -> dict[str, Any]:
    """Shared hardware attributes of a rank set: sets of rails, pp_stages, leaves; node count."""
    sub = rank_map[rank_map["rank"].isin(ranks)]
    return {"rails": set(int(x) for x in sub.rail), "pp_stages": set(int(x) for x in sub.pp_stage),
            "leaves": set(sub.leaf), "nodes": int(sub.node.nunique())}


def implicate_links(events: pd.DataFrame, rank_map: pd.DataFrame, job: str | None = None) -> list[tuple[str, str, int]]:
    """Score (node, hca) endpoints named by NET/IB errors: +1 for the reporting endpoint (host + hca in
    the line) and +1 for the peer endpoint (peer IP resolved through rank_map.backend_ip).
    Optionally restrict to one job. Return [(node, hca, score)] sorted by score desc, then node."""
    ip_map = {r.backend_ip: (r.node, r.hca) for r in rank_map[["backend_ip", "node", "hca"]].itertuples()}
    ev = events[events.source == "nccl"]
    if job is not None:
        ev = ev[ev.get("job") == job]
    score: dict[tuple[str, str], int] = {}
    for _, e in ev.iterrows():
        p = parse_netib(e.message)
        if not p:
            continue
        local = (e.host, p["hca"])
        score[local] = score.get(local, 0) + 1
        if p["peer_ip"] in ip_map:
            peer = ip_map[p["peer_ip"]]
            score[peer] = score.get(peer, 0) + 1
    return sorted(((n, h, s) for (n, h), s in score.items()), key=lambda x: (-x[2], x[0]))


def bad_ports(switch_counters: pd.DataFrame, fec_threshold: int = 10_000) -> pd.DataFrame:
    """Ports whose link_down_count increased, or whose fec_uncorrectable_blocks increased by more than
    `fec_threshold`, between the first and last snapshot. Columns: switch, port, peer_node, peer_hca,
    link_downs, fec_delta, rx_power_dbm (last)."""
    g = switch_counters.sort_values("ts").groupby(["switch", "port", "peer_node", "peer_hca"])
    agg = g.agg(ld0=("link_down_count", "first"), ld1=("link_down_count", "last"),
                f0=("fec_uncorrectable_blocks", "first"), f1=("fec_uncorrectable_blocks", "last"),
                rx=("rx_power_dbm_min_lane", "last")).reset_index()
    agg["link_downs"] = agg.ld1 - agg.ld0 + (agg.ld0 > 0) * agg.ld0
    agg["fec_delta"] = agg.f1 - agg.f0
    out = agg[(agg.link_downs > 0) | (agg.fec_delta > fec_threshold)]
    return out[["switch", "port", "peer_node", "peer_hca", "link_downs", "fec_delta", "rx"]].rename(
        columns={"rx": "rx_power_dbm"}).reset_index(drop=True)


def gpu_actions(gpu_health: pd.DataFrame) -> pd.DataFrame:
    """Health decision per GPU that needs one:
    quarantine_rma        remap_failure == Yes or ecc_dbe_volatile > 0
    drain_reset_validate  remap_pending == Yes (remap takes effect only after a GPU reset)
    monitor               rows already remapped (correctable or uncorrectable > 0), nothing pending
    Returns columns node, gpu, gpu_uuid, action (healthy GPUs omitted)."""
    out = []
    for r in gpu_health.itertuples():
        if r.remap_failure == "Yes" or r.ecc_dbe_volatile > 0:
            a = "quarantine_rma"
        elif r.remap_pending == "Yes":
            a = "drain_reset_validate"
        elif r.remapped_rows_correctable > 0 or r.remapped_rows_uncorrectable > 0:
            a = "monitor"
        else:
            continue
        out.append((r.node, int(r.gpu), r.gpu_uuid, a))
    return pd.DataFrame(out, columns=["node", "gpu", "gpu_uuid", "action"])


# --------------------------------------------------------------------------- Task 3: cause vs correlation
def classify_hypotheses(b: dict[str, Any]) -> dict[str, str]:
    """Classify each hypothesis in b["hypotheses"] as proven_cause, real_fault_not_cause,
    correlation_only, or refuted, using:
      * the stuck rank set and its hardware (stuck_ranks / common_hardware),
      * the top implicated link for the failing job (implicate_links, job 900211),
      * link-down events on that endpoint immediately preceding the first NET/IB error,
      * gpu_actions for GPU hypotheses, bad_ports for switch hypotheses,
      * event timing relative to the first NET/IB error for fabric-consequence hypotheses."""
    rm, ev = b["rank_map"], b["events"]
    stuck = set(stuck_ranks(b["rank_progress"]))
    stuck_nodes = set(rm[rm["rank"].isin(stuck)].node)
    hw = common_hardware(rm, sorted(stuck))
    top = implicate_links(ev, rm, job="900211")[0]
    netib = ev[(ev.source == "nccl") & (ev.get("job") == "900211")]
    first_err = netib.ts.min()
    actions = gpu_actions(b["gpu_health"])
    bp = bad_ports(b["switch_port_counters"])
    res: dict[str, str] = {}
    for h in b["hypotheses"]["hypotheses"]:
        k = h["kind"]
        if k == "link":
            node_rank = rm[(rm.node == h["node"]) & (rm.hca == h["hca"])]["rank"].iloc[0]
            downs = ev[(ev.host == h["node"]) & ev.message.str.contains("Link down")
                       & (ev.ts <= first_err) & (ev.ts >= first_err - pd.Timedelta(seconds=30))]
            ok = (h["node"], h["hca"]) == (top[0], top[1]) and int(node_rank) in stuck and not downs.empty
            res[h["id"]] = "proven_cause" if ok else "correlation_only"
        elif k == "gpu":
            a = actions[(actions.node == h["node"]) & (actions.gpu == h["gpu"])]
            ranks = set(rm[(rm.node == h["node"]) & (rm.local_rank == h["gpu"])]["rank"])
            if not a.empty and a.action.iloc[0] != "monitor":
                res[h["id"]] = "real_fault_not_cause" if not (ranks & stuck) else "correlation_only"
            else:
                res[h["id"]] = "correlation_only"
        elif k in ("first_reporter", "aer"):
            in_stuck = h["node"] in stuck_nodes and (k == "first_reporter" or int(h["hca"][-1]) in hw["rails"])
            res[h["id"]] = "correlation_only" if not in_stuck else "proven_cause"
        elif k == "fabric_pfc":
            e = ev[ev.host == h["switch"]]
            res[h["id"]] = "correlation_only" if (not e.empty and e.ts.min() > first_err) else "refuted"
        elif k == "switch":
            n_bad = int((bp.switch == h["switch"]).sum())
            res[h["id"]] = "refuted" if n_bad <= 1 else "proven_cause"
    return res


# --------------------------------------------------------------------------- Task 4: containment + recovery
def select_checkpoint(checkpoints: pd.DataFrame, failure_ts: pd.Timestamp) -> str:
    """Latest checkpoint that is restorable: status complete, shards_written == shards_expected,
    metadata_committed true, and end_ts <= failure_ts. Returns ckpt_id."""
    c = checkpoints[(checkpoints.status == "complete") & (checkpoints.shards_written == checkpoints.shards_expected)
                    & (checkpoints.metadata_committed.astype(str).str.lower() == "true")
                    & (checkpoints.end_ts <= failure_ts)]
    return str(c.sort_values("start_ts").ckpt_id.iloc[-1])


def recovery_metrics(failure_ts: pd.Timestamp, ckpt_ts: pd.Timestamp, resume_ts: pd.Timestamp,
                     gpus: int) -> dict[str, float]:
    """RPO = failure - checkpoint state time; RTO = resume - failure (minutes);
    lost GPU-hours = gpus * (resume - checkpoint state time) in hours."""
    rpo = (failure_ts - ckpt_ts).total_seconds() / 60
    rto = (resume_ts - failure_ts).total_seconds() / 60
    lost = gpus * (resume_ts - ckpt_ts).total_seconds() / 3600
    return {"rpo_min": round(rpo, 2), "rto_min": round(rto, 2), "lost_gpu_hours": round(lost, 1)}


def repeat_offenders(events: pd.DataFrame, rank_map: pd.DataFrame) -> set[str]:
    """Nodes that are the top implicated endpoint for NET/IB failures in two or more distinct jobs."""
    jobs = [j for j in events[events.source == "nccl"].get("job").dropna().unique()]
    hits: dict[str, int] = {}
    for j in jobs:
        top = implicate_links(events, rank_map, job=j)
        if top:
            hits[top[0][0]] = hits.get(top[0][0], 0) + 1
    return {n for n, c in hits.items() if c >= 2}


def auto_restart_allowed(restart_history: pd.DataFrame, now: pd.Timestamp, offenders: set[str],
                         max_auto_per_6h: int = 2) -> dict[str, Any]:
    """Retry-loop policy: automatic restart is allowed only if (a) fewer than `max_auto_per_6h`
    automatic restarts happened in the 6 h before `now`, and (b) no repeat-offender node is still in
    the allocation (offenders must be excluded first). Returns {"allowed": bool, "reasons": [...]}."""
    recent = restart_history[(restart_history.auto_restarted.astype(str).str.lower() == "true")
                             & (restart_history.end_ts >= now - pd.Timedelta(hours=6))]
    reasons = []
    if len(recent) >= max_auto_per_6h:
        reasons.append(f"{len(recent)} automatic restarts in 6 h")
    if offenders:
        reasons.append(f"repeat offender(s) {sorted(offenders)} must be excluded before restart")
    return {"allowed": not reasons, "reasons": reasons}


def restart_plan(b: dict[str, Any], exclude: list[str], ckpt_id: str) -> dict[str, Any]:
    """Safe restart plan: replace each excluded node with the next `ready` spare (in spares.csv order)
    that has no GPU action in gpu_health; remap the excluded node's ranks to the spare preserving
    local_rank (so TP/PP/DP coordinates are unchanged). Returns
    {"checkpoint", "node_map": {bad: spare}, "remapped_ranks": {rank: spare}, "excluded": [...]}."""
    acts = gpu_actions(b["gpu_health"])
    bad_spares = set(acts[acts.action != "monitor"].node)
    pool = [s for s in b["spares"][b["spares"].state == "ready"].node if s not in bad_spares]
    if len(pool) < len(exclude):
        raise RuntimeError("not enough healthy spares")
    node_map = dict(zip(exclude, pool))
    rm = b["rank_map"]
    remap = {int(r): node_map[n] for r, n in zip(rm["rank"], rm.node) if n in node_map}
    return {"checkpoint": ckpt_id, "node_map": node_map, "remapped_ranks": remap, "excluded": list(exclude)}


# --------------------------------------------------------------------------- Task 5: FMEA
def fmea_score(fmea: pd.DataFrame, rpn_threshold: int = 200, severity_override: int = 9) -> pd.DataFrame:
    """Add columns: issue (OUT_OF_RANGE if any S/O/D outside 1..10; DETECTION_INCONSISTENT if
    detection < 5 while detection_control is 'none'; else ''), rpn = S*O*D computed on CORRECTED
    scores (detection -> 10 when control is 'none'; out-of-range rows get rpn 0 until re-scored),
    action_required (rpn >= rpn_threshold or severity >= severity_override). Sorted by rpn desc,
    then severity desc."""
    df = fmea.copy()
    issues, rpns = [], []
    for r in df.itertuples():
        s, o, d = int(r.severity), int(r.occurrence), int(r.detection)
        issue = ""
        if not all(1 <= v <= 10 for v in (s, o, d)):
            issue = "OUT_OF_RANGE"
        elif str(r.detection_control).strip().lower() == "none" and d < 5:
            issue = "DETECTION_INCONSISTENT"
            d = 10
        issues.append(issue)
        rpns.append(0 if issue == "OUT_OF_RANGE" else s * o * d)
    df["issue"] = issues
    df["rpn"] = rpns
    df["action_required"] = (df.rpn >= rpn_threshold) | (df.severity >= severity_override)
    return df.sort_values(["rpn", "severity"], ascending=[False, False]).reset_index(drop=True)


# --------------------------------------------------------------------------- Task 6: tenant isolation
def _overlaps(a: str, b: str) -> bool:
    pa, pb = a.rstrip("/").split("/"), b.rstrip("/").split("/")
    n = min(len(pa), len(pb))
    return pa[:n] == pb[:n]


def check_isolation(tenants: dict[str, Any], policy: dict[str, Any]) -> set[tuple[str, str]]:
    """Return the set of (tenant, code) violations. Codes:
    RBAC_FORBIDDEN_ROLE, SHARED_VRF / SHARED_VNI / SHARED_IB_PKEY / SHARED_FRONTEND_VLAN (both tenants),
    STORAGE_OVERLAP (the tenant whose export contains or equals another tenant's export),
    GPU_SHARING_NOT_MIG, NO_SCRUB, SECRETS_SCOPE, AUDIT_RETENTION."""
    ts = tenants["tenants"]
    out: set[tuple[str, str]] = set()
    for t in ts:
        for rb in t["rbac_bindings"]:
            if rb["role"] in policy["forbidden_roles_for_tenant_subjects"]:
                out.add((t["name"], "RBAC_FORBIDDEN_ROLE"))
        if t["gpu"]["shared_with"] and t["gpu"]["allocation_mode"] != policy["gpu_cross_tenant_sharing_requires"]:
            out.add((t["name"], "GPU_SHARING_NOT_MIG"))
        if policy["scrub_on_release_required"] and not t["gpu"]["scrub_on_release"]:
            out.add((t["name"], "NO_SCRUB"))
        if policy["secrets_prefix_must_end_with_tenant_name"] and \
                not t["secrets"]["path_prefix"].rstrip("/").endswith(t["name"]):
            out.add((t["name"], "SECRETS_SCOPE"))
        if t["audit"]["retention_days"] < policy["min_audit_retention_days"]:
            out.add((t["name"], "AUDIT_RETENTION"))
    for field in policy["unique_per_tenant"]:
        seen: dict[str, list[str]] = {}
        for t in ts:
            seen.setdefault(str(t["network"][field]), []).append(t["name"])
        for names in seen.values():
            if len(names) > 1:
                out.update((n, f"SHARED_{field.upper()}") for n in names)
    if policy["storage_exports_must_not_overlap_other_tenants"]:
        for t in ts:
            for u in ts:
                if t["name"] == u["name"]:
                    continue
                for e in t["storage"]["exports"]:
                    for f in u["storage"]["exports"]:
                        if _overlaps(e["path"], f["path"]) and len(e["path"].rstrip("/")) <= len(f["path"].rstrip("/")):
                            out.add((t["name"], "STORAGE_OVERLAP"))
    return out
