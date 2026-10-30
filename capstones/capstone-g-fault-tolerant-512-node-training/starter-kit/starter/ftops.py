"""Capstone G starter module - fault-tolerant 512-node training operations (ORION-XL).

Implement every function marked TODO. The loaders, regular expressions and parse_utc() are given.
Run ``python check.py`` from starter-kit/ to see which checks pass; read starter-kit/README.md for
the tasks. The dataset is SIMULATED; nothing here touches a real system.
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
    # TODO: iterate the inventory once; it is the LLDP-observed truth, not the DCIM plan
    # TODO: spare nodes have an empty rank: index their devices but give them no ranks
    # TODO: convert gpu, numa, rail, leaf_port and rank to int
    raise NotImplementedError("TODO: implement build_maps()")


def cabling_discrepancies(inventory: pd.DataFrame, plan: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows where the LLDP-observed (leaf, port) differs from the DCIM cabling plan, sorted by node, hca."""
    # TODO: compare every planned (leaf, port) with what LLDP observed for the same (node, hca)
    # TODO: each mismatch is a DCIM correction ticket - and a trap for anyone correlating with the plan
    raise NotImplementedError("TODO: implement cabling_discrepancies()")


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
    # TODO: correct every host timestamp with clock_offsets.csv BEFORE comparing times across hosts
    # TODO: Xid lines print the PCI address without the function (.0); inventory BDFs include it
    # TODO: map switch ports to the attached HCA with the LLDP port map from build_maps()
    # TODO: use the regular expressions defined at the top of the module
    raise NotImplementedError("TODO: implement normalize_events()")


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
    # TODO: implement the scoring table in the docstring exactly; thresholds are part of the policy
    # TODO: correctable ECC below the threshold is trended, not scored
    # TODO: cap each component at 100 and keep the evidence strings - they go into the quarantine ticket
    raise NotImplementedError("TODO: implement health_scores()")


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
    # TODO: find the rank(s) that never enqueued the collective everyone else is waiting in
    # TODO: do NOT rank by timestamps: one host's clock is wrong by minutes
    # TODO: a component is the proven cause only if it is on a first-stalled rank AND has critical evidence
    # TODO: everything else above the quarantine threshold is an independent fault: correlated in time is not causal
    raise NotImplementedError("TODO: implement classify()")


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
    # TODO: quarantine the smallest repair domain (GPU or HCA) but drain the whole node: it is the placement unit
    # TODO: an HCA fault also needs a Fabric ticket for its LLDP peer switch port
    # TODO: watch items get tickets, not drains
    raise NotImplementedError("TODO: implement quarantine_plan()")


# --------------------------------------------------------------------------- T6 checkpoint selection
def select_checkpoint(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the newest checkpoint that is restorable.

    Restorable = metadata committed AND no missing shards AND no checksum failures. Returns
    {"step": int, "rejected": {step: [reasons]}} where rejected lists every NEWER checkpoint and why.
    Raises ValueError if none is restorable.
    """
    # TODO: walk checkpoints newest first; reject uncommitted metadata, missing shards and checksum failures
    # TODO: record why each newer checkpoint was rejected - it is postmortem evidence
    raise NotImplementedError("TODO: implement select_checkpoint()")


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
    # TODO: a spare is eligible only if idle, acceptance passed, and with no OPEN quarantine on any component
    # TODO: pair sorted drained nodes with sorted eligible spares; keep each rank's GPU index so rails stay aligned
    # TODO: raise ValueError rather than placing ranks on an ineligible node
    raise NotImplementedError("TODO: implement restart_plan()")


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
    # TODO: all times are relative to the TRUE fault time from classify()
    # TODO: RPO is measured from the last completed step to the step you restored, not to the newest checkpoint
    raise NotImplementedError("TODO: implement recovery_metrics()")


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
    # TODO: coerce loss and grad_norm to numeric: 'nan' strings must count as NaN
    # TODO: the sample index must match exactly on overlapping steps: weights alone are not the whole state
    # TODO: set the tolerance from replay noise, not from the loss magnitude; check loss AND grad_norm
    # TODO: return every sub-check so the postmortem can show which one failed
    raise NotImplementedError("TODO: implement validate_resume()")
