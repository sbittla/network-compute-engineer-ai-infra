"""Chapter 16 lab -- bare-metal fleet lifecycle (STARTER: complete the TODOs).

Four pieces of fleet automation that every GPU fleet team writes in some form:

1. ``check_compat``          -- is a node's firmware/driver stack a *validated bundle*?   (Task 1)
2. ``evaluate_node``         -- raw acceptance results -> PASS / WARN / FAIL + reason codes. (Task 2)
3. ``transition_table`` / ``apply_event`` / ``replay``
                             -- a guarded node lifecycle state machine with an audit log. (Task 3)
4. ``plan_upgrade_waves``    -- a canary + wave plan that respects blast-radius limits.   (Task 4)

Run ``python ../check.py`` (from this folder) or ``python check.py`` (from lab/) to see progress.
Every function documents its exact contract; the checker tests the contract, not your style.
"""
from __future__ import annotations

import copy  # noqa: F401  (you will want deepcopy in replay)
import json
import math
from pathlib import Path
from typing import Any

import yaml

STATES: tuple[str, ...] = ("discovered", "imaged", "validated", "schedulable",
                           "draining", "drained", "repair", "retired")

# Reason codes used in the audit log for rejected events.
REJECT_CODES: tuple[str, ...] = (
    "UNKNOWN_NODE", "ILLEGAL_TRANSITION", "INVENTORY_INCOMPLETE", "ACCEPTANCE_NOT_PASSED",
    "MISSING_TICKET", "FW_OFF_MATRIX", "MISSING_REASON", "FAULT_DRAIN_REQUIRES_REPAIR",
    "JOBS_STILL_RUNNING", "TICKET_OPEN", "SANITIZATION_MISSING",
)

REQUIRED_INVENTORY_FIELDS: tuple[str, ...] = ("serial", "asset_tag", "rack", "bmc_mac", "bmc_ip")


# --------------------------------------------------------------------------------------------
# Data loading helpers (provided)
# --------------------------------------------------------------------------------------------
def load_json(path: str | Path) -> Any:
    """Load a JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str | Path) -> Any:
    """Load a YAML file with the safe loader."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------
# Task 1. Compatibility matrix
# --------------------------------------------------------------------------------------------
def check_compat(firmware: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    """Classify a node's firmware/driver stack against the compatibility matrix.

    ``matrix`` is ``data/compat_matrix.yaml``: ``components`` (list of component names),
    ``bundles`` (list of ``{id, status, versions}``; status "production" or "deprecated"), and
    ``blocked`` (list of ``{component, version, reason}``).

    A component value in ``firmware`` may be a string or a list of strings (e.g. the NIC firmware
    of all 8 compute NICs). A list matches a bundle only if *every* element equals the bundle's
    version. A missing/empty component never matches.

    Returns a dict with keys:
      ``status``     -- "BLOCKED" if any value is on the blocked list (takes precedence); else
                        "OK" for an exact match to a production bundle; "DEPRECATED" for an exact
                        match to a deprecated bundle; otherwise "OFF_MATRIX".
      ``bundle``     -- id of the exactly matching bundle, else None.
      ``closest``    -- id of the bundle with the fewest mismatching components
                        (ties: first in matrix order).
      ``mismatches`` -- sorted component names that differ from ``closest``.
      ``blocked``    -- sorted list of "component=version" strings found on the blocked list.

    TODO:
      1. Normalise each component value to a sorted list of strings.
      2. For each bundle, compute the list of mismatching components.
      3. Track the exact match (zero mismatches) and the closest bundle.
      4. Collect blocked hits, then decide ``status`` with the precedence above.
    """
    raise NotImplementedError("check_compat")


# --------------------------------------------------------------------------------------------
# Task 2. Acceptance evaluator
# --------------------------------------------------------------------------------------------
def evaluate_node(result: dict[str, Any], policy: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one node's acceptance results against the policy and the compatibility matrix.

    ``result`` is one element of ``data/acceptance_results.json``; ``policy`` is
    ``data/acceptance_policy.yaml``. Returns::

        {"node": str, "verdict": "PASS"|"WARN"|"FAIL", "codes": [...], "warnings": [...],
         "details": [human-readable strings]}

    ``codes`` and ``warnings`` are sorted, de-duplicated. Verdict: FAIL if any code, else WARN if
    any warning, else PASS.

    FAIL codes and their rules (``exp`` = policy["expected"], ``thr`` = policy["thresholds"]):
      GPU_COUNT             len(gpus) != exp.gpu_count
      GPU_PRODUCT           a GPU's product != exp.gpu_product
      HBM_CAPACITY          a GPU's hbm_total_mib < exp.gpu_hbm_total_mib_min
      PCIE_DEGRADED         a GPU's *under-load* pcie gen/width != exp.gpu_pcie, or a compute NIC's
                            pcie gen/width != exp.compute_nic (ignore ``gen_idle``: idle GPUs
                            legitimately down-train the link speed to save power)
      NVLINK_DOWN           nvlink_links_up < exp.nvlink_links_per_gpu
      ECC_DBE               ecc.dbe_volatile > thr.ecc_dbe_volatile_max
      HBM_ROW_REMAP_PENDING row_remap.pending is true
      HBM_ROW_REMAP_FAILURE row_remap.failure is true
      THERMAL_THROTTLE      burn_in.throttle_reasons intersects thr.throttle_reasons_fail, or
                            burn_in.max_temp_c >= thr.max_gpu_temp_c (SW_POWER_CAP is normal)
      DCGM_DIAG_FAIL        dcgm_diag.result != "Pass" or level < thr.dcgm_diag_min_level
      NIC_COUNT             compute or frontend NIC count differs from expected
      NIC_LINK_DOWN         a NIC's link_state != "up"
      NIC_SPEED             an up NIC's speed_mbps != expected *for its role* (frontend NICs are
                            200000 Mb/s by design)
      NIC_MTU               a NIC's mtu != expected mtu for its role, or a compute NIC's
                            active_mtu (RDMA path MTU) != exp.compute_nic.active_mtu
      RDMA_PAIR_BW_LOW      a compute NIC's rdma_pair_bw_gbps missing or < thr.rdma_pair_bw_min_gbps
      NVME_COUNT            len(storage.nvme) != exp.nvme_count
      NVME_MEDIA_ERRORS     any media_errors > thr.nvme_media_errors_max or critical_warning != 0
      STORAGE_THROUGHPUT_LOW storage.fio_seq_read_gbs < thr.fio_seq_read_min_gbs
      NCCL_ALGO_UNRECORDED  nccl_single_node.algorithm missing, or not a key of
                            thr.nccl_allreduce_busbw_min_gbs (never assume NVLS)
      NCCL_BUSBW_LOW        otherwise, busbw_gbs < thr.nccl_allreduce_busbw_min_gbs[algorithm]
      XID_PRESENT           xid_events is non-empty
      FW_OFF_MATRIX         check_compat(...) status is OFF_MATRIX or BLOCKED, where the firmware
                            dict is result["firmware"] plus "nic_fw" = list of every compute NIC's fw
    WARN codes:
      ECC_SBE_ELEVATED      ecc.sbe_volatile > thr.ecc_sbe_volatile_warn
      FW_DEPRECATED         check_compat(...) status is DEPRECATED

    TODO: implement each rule; keep the code table-driven by the policy (no hard-coded numbers).
    """
    raise NotImplementedError("evaluate_node")


def evaluate_fleet(results: list[dict[str, Any]], policy: dict[str, Any],
                   matrix: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate every node; return the per-node verdicts in input order (provided)."""
    return [evaluate_node(r, policy, matrix) for r in results]


# --------------------------------------------------------------------------------------------
# Task 3. Lifecycle state machine
# --------------------------------------------------------------------------------------------
def transition_table() -> dict[tuple[str, str], str]:
    """Return the allowed ``(from_state, event) -> to_state`` transitions.

    Required transitions (13):
      discovered --image--> imaged
      imaged --pass_acceptance--> validated        imaged --fail_acceptance--> repair
      validated --enable--> schedulable            validated --reimage--> imaged
      schedulable --drain--> draining
      draining --cancel_drain--> schedulable       draining --drain_complete--> drained
      drained --send_to_repair--> repair           drained --reimage--> imaged
      drained --retire--> retired
      repair --reimage--> imaged                   repair --retire--> retired
    ``retired`` is terminal. ``inventory_update`` is NOT in this table (see apply_event).

    TODO: return the dict.
    """
    raise NotImplementedError("transition_table")


def apply_event(nodes: dict[str, dict[str, Any]], event: dict[str, Any], audit: list[dict[str, Any]],
                matrix: dict[str, Any]) -> bool:
    """Apply one lifecycle event; append exactly one audit record; return True if applied.

    ``nodes`` maps node name -> inventory record (``data/inventory.json`` element) and is mutated
    in place only when the event is applied. A rejected event never changes ``nodes``.
    ``event`` is one element of ``data/lifecycle_events.json``: ``{seq, ts, node, event, actor,
    evidence}``.

    Audit record keys (all required): seq, ts, node, event, actor, from_state (None for an unknown
    node), to_state (None if rejected), result ("applied" | "rejected"), reason_code (None if
    applied; one of REJECT_CODES if rejected).

    Check order: UNKNOWN_NODE -> ILLEGAL_TRANSITION (pair not in transition_table) -> guard.
    Guards (evidence = event["evidence"]):
      image            every REQUIRED_INVENTORY_FIELDS value truthy on the node, else INVENTORY_INCOMPLETE
      pass_acceptance  verdict "PASS", or "WARN" with a non-empty ``waiver``; else ACCEPTANCE_NOT_PASSED
      fail_acceptance, send_to_repair   non-empty ``ticket``; else MISSING_TICKET
      enable           check_compat(node["firmware"], matrix)["status"] == "OK"; else FW_OFF_MATRIX
      drain            non-empty ``reason`` and ``category`` in {"fault","maintenance"}; else MISSING_REASON
      cancel_drain     node["drain"]["category"] == "maintenance"; else FAULT_DRAIN_REQUIRES_REPAIR
      drain_complete   evidence ``running_jobs`` == 0 (missing counts as not drained); else JOBS_STILL_RUNNING
      reimage (from repair only)  evidence ``ticket_status`` == "closed"; else TICKET_OPEN
      retire           non-empty ``sanitization_cert``; else SANITIZATION_MISSING
    Side effects when applied:
      drain -> node["drain"] = {"reason", "category"};  cancel_drain -> node["drain"] = None
      fail_acceptance/send_to_repair -> node["ticket"] = {"id": ticket, "status": "open"}
      reimage -> if evidence has "firmware", replace node["firmware"]; mark ticket closed; drain None
      retire -> node["sanitization_cert"] = cert
    ``inventory_update`` (any state except retired, else ILLEGAL_TRANSITION): copy evidence keys
    that are in REQUIRED_INVENTORY_FIELDS onto the node; state unchanged; to_state = from_state.

    TODO: implement; keep guards in one place so they are easy to audit.
    """
    raise NotImplementedError("apply_event")


def replay(inventory: list[dict[str, Any]], events: list[dict[str, Any]],
           matrix: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Replay events (sorted by ``seq``) over a *deep copy* of the inventory.

    Returns ``(nodes_by_name, audit_log)``. The input inventory must not be modified.

    TODO: build the dict with copy.deepcopy, sort events by seq, call apply_event for each.
    """
    raise NotImplementedError("replay")


# --------------------------------------------------------------------------------------------
# Task 4. Staged upgrade planner
# --------------------------------------------------------------------------------------------
def plan_upgrade_waves(inventory: list[dict[str, Any]], matrix: dict[str, Any], target_bundle: str,
                       canary_size: int = 2, max_per_wave: int = 4,
                       max_per_rack_per_wave: int = 1) -> dict[str, Any]:
    """Build a canary + wave upgrade plan to ``target_bundle``.

    Eligible nodes: state == "schedulable" and ``check_compat(firmware)["bundle"] != target_bundle``.
    Excluded nodes are reported as ``{node: reason}`` with reason "state:<state>" or
    "already_on_target".

    Rules the checker enforces:
      * canary: exactly ``canary_size`` nodes, all in different racks.
      * waves: each wave has <= ``max_per_wave`` nodes and <= ``max_per_rack_per_wave`` per rack.
      * every eligible node appears exactly once across canary + waves.
      * number of waves == wave_lower_bound(...) of what remains after the canary.
      * deterministic: same input -> same plan.
    Hint: a greedy "take from the rack with the most remaining nodes first" achieves the bound.

    Returns ``{"target": str, "canary": [names], "waves": [[names], ...], "excluded": {name: reason}}``.

    TODO: implement.
    """
    raise NotImplementedError("plan_upgrade_waves")


def wave_lower_bound(remaining_per_rack: dict[str, int], max_per_wave: int, max_per_rack_per_wave: int) -> int:
    """Minimum number of waves for the given per-rack node counts (provided)."""
    total = sum(remaining_per_rack.values())
    if total == 0:
        return 0
    return max(math.ceil(total / max_per_wave),
               math.ceil(max(remaining_per_rack.values()) / max_per_rack_per_wave))
