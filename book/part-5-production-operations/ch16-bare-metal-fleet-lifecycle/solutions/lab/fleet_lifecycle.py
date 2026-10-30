"""Chapter 16 lab -- bare-metal fleet lifecycle (REFERENCE SOLUTION, instructor only).

Four pieces of fleet automation that every GPU fleet team writes in some form:

1. ``check_compat``        -- is a node's firmware/driver stack a *validated bundle*?
2. ``evaluate_node``       -- turn raw acceptance results into PASS / WARN / FAIL with reason codes.
3. ``apply_event``/``replay`` -- a guarded node lifecycle state machine with an append-only audit log.
4. ``plan_upgrade_waves``  -- a canary + wave plan that respects blast-radius limits.

All functions are pure apart from the explicit ``nodes``/``audit`` arguments they are documented
to mutate. No hardware access; inputs are the JSON/YAML files in ``lab/data``.
"""
from __future__ import annotations

import copy
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
# Data loading helpers (provided to learners, identical in starter)
# --------------------------------------------------------------------------------------------
def load_json(path: str | Path) -> Any:
    """Load a JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str | Path) -> Any:
    """Load a YAML file with the safe loader."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------
# 1. Compatibility matrix
# --------------------------------------------------------------------------------------------
def _values(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple, set)):
        return sorted({str(x) for x in v})
    return [str(v)]


def check_compat(firmware: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    """Classify a node's firmware/driver stack against the compatibility matrix.

    A component value may be a string or a list of strings (e.g. the set of NIC firmware
    versions seen across 8 NICs); a list matches a bundle only if *every* element equals the
    bundle's version.

    Returns a dict with keys:
      ``status``     -- "OK" (exact match to a production bundle), "DEPRECATED" (exact match to a
                        deprecated bundle), "BLOCKED" (any value is on the blocked list), or
                        "OFF_MATRIX" (no exact match).  BLOCKED takes precedence.
      ``bundle``     -- id of the exactly matching bundle, else None.
      ``closest``    -- id of the bundle with the fewest mismatching components (ties: first in
                        matrix order).
      ``mismatches`` -- sorted component names that differ from ``closest``.
      ``blocked``    -- sorted list of "component=version" strings found on the blocked list.
    """
    components = matrix["components"]
    blocked = sorted(f"{b['component']}={v}"
                     for b in matrix.get("blocked", [])
                     for v in _values(firmware.get(b["component"]))
                     if v == str(b["version"]))
    best_id, best_mm = None, None
    exact = None
    for bundle in matrix["bundles"]:
        mm = [c for c in components
              if not _values(firmware.get(c))
              or any(v != str(bundle["versions"][c]) for v in _values(firmware.get(c)))]
        if best_mm is None or len(mm) < len(best_mm):
            best_id, best_mm = bundle["id"], mm
        if not mm and exact is None:
            exact = bundle
    if blocked:
        status = "BLOCKED"
    elif exact is None:
        status = "OFF_MATRIX"
    elif exact["status"] == "production":
        status = "OK"
    else:
        status = "DEPRECATED"
    return {"status": status, "bundle": exact["id"] if exact else None, "closest": best_id,
            "mismatches": sorted(best_mm or []), "blocked": blocked}


# --------------------------------------------------------------------------------------------
# 2. Acceptance evaluator
# --------------------------------------------------------------------------------------------
def evaluate_node(result: dict[str, Any], policy: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one node's acceptance results against the policy and the compatibility matrix.

    Returns ``{"node", "verdict", "codes", "warnings", "details"}`` where ``codes`` (FAIL reasons)
    and ``warnings`` are sorted, de-duplicated lists of reason codes, ``verdict`` is "FAIL" if any
    code, else "WARN" if any warning, else "PASS"; ``details`` is a list of human-readable strings.

    FAIL codes: GPU_COUNT, GPU_PRODUCT, HBM_CAPACITY, PCIE_DEGRADED, NVLINK_DOWN, ECC_DBE,
    HBM_ROW_REMAP_PENDING, HBM_ROW_REMAP_FAILURE, THERMAL_THROTTLE, DCGM_DIAG_FAIL, NIC_COUNT,
    NIC_LINK_DOWN, NIC_SPEED, NIC_MTU, RDMA_PAIR_BW_LOW, NVME_COUNT, NVME_MEDIA_ERRORS,
    STORAGE_THROUGHPUT_LOW, NCCL_BUSBW_LOW, NCCL_ALGO_UNRECORDED, FW_OFF_MATRIX, XID_PRESENT.
    WARN codes: ECC_SBE_ELEVATED, FW_DEPRECATED.

    Units: speeds in Mb/s (as ``ethtool`` reports), RDMA bandwidth in Gb/s, NCCL bus bandwidth
    and fio throughput in GB/s, temperatures in degrees C.
    """
    exp, thr = policy["expected"], policy["thresholds"]
    codes: set[str] = set()
    warns: set[str] = set()
    details: list[str] = []

    def fail(code: str, msg: str) -> None:
        codes.add(code)
        details.append(f"{code}: {msg}")

    gpus = result.get("gpus", [])
    if len(gpus) != exp["gpu_count"]:
        fail("GPU_COUNT", f"{len(gpus)} GPUs visible, expected {exp['gpu_count']}")
    fail_reasons = set(thr["throttle_reasons_fail"])
    for g in gpus:
        tag = f"GPU{g['index']} {g.get('bdf', '')}".strip()
        if g.get("product") != exp["gpu_product"]:
            fail("GPU_PRODUCT", f"{tag} product {g.get('product')}")
        if g.get("hbm_total_mib", 0) < exp["gpu_hbm_total_mib_min"]:
            fail("HBM_CAPACITY", f"{tag} {g.get('hbm_total_mib')} MiB")
        pcie = g.get("pcie", {})
        if pcie.get("gen") != exp["gpu_pcie"]["gen"] or pcie.get("width") != exp["gpu_pcie"]["width"]:
            fail("PCIE_DEGRADED", f"{tag} Gen{pcie.get('gen')} x{pcie.get('width')} under load")
        if g.get("nvlink_links_up", 0) < exp["nvlink_links_per_gpu"]:
            fail("NVLINK_DOWN", f"{tag} {g.get('nvlink_links_up')}/{exp['nvlink_links_per_gpu']} links")
        ecc = g.get("ecc", {})
        if ecc.get("dbe_volatile", 0) > thr["ecc_dbe_volatile_max"]:
            fail("ECC_DBE", f"{tag} {ecc['dbe_volatile']} uncorrectable (volatile)")
        if ecc.get("sbe_volatile", 0) > thr["ecc_sbe_volatile_warn"]:
            warns.add("ECC_SBE_ELEVATED")
            details.append(f"ECC_SBE_ELEVATED: {tag} {ecc['sbe_volatile']} correctable during burn-in")
        rr = g.get("row_remap", {})
        if rr.get("pending"):
            fail("HBM_ROW_REMAP_PENDING", f"{tag} row remap pending (GPU reset required)")
        if rr.get("failure"):
            fail("HBM_ROW_REMAP_FAILURE", f"{tag} row remapping failure")
        bi = g.get("burn_in", {})
        bad = sorted(set(bi.get("throttle_reasons", [])) & fail_reasons)
        if bad or bi.get("max_temp_c", 0) >= thr["max_gpu_temp_c"]:
            fail("THERMAL_THROTTLE", f"{tag} max {bi.get('max_temp_c')} C, reasons {bad}")

    diag = result.get("dcgm_diag") or {}
    if (diag.get("result") != "Pass" or diag.get("level", 0) < thr["dcgm_diag_min_level"]):
        fail("DCGM_DIAG_FAIL", f"level {diag.get('level')} result {diag.get('result')}")

    nics = result.get("nics", [])
    compute = [n for n in nics if n.get("role") == "compute"]
    frontend = [n for n in nics if n.get("role") == "frontend"]
    cexp, fexp = exp["compute_nic"], exp["frontend_nic"]
    if len(compute) != cexp["count"] or len(frontend) != fexp["count"]:
        fail("NIC_COUNT", f"{len(compute)} compute / {len(frontend)} frontend NICs")
    for n in compute + frontend:
        want = cexp["speed_mbps"] if n["role"] == "compute" else fexp["speed_mbps"]
        if n.get("link_state") != "up":
            fail("NIC_LINK_DOWN", f"{n['name']} link {n.get('link_state')}")
            continue
        if n.get("speed_mbps") != want:
            fail("NIC_SPEED", f"{n['name']} {n.get('speed_mbps')} Mb/s, expected {want}")
    for n in compute + frontend:
        exp_n = cexp if n["role"] == "compute" else fexp
        if n.get("mtu") != exp_n["mtu"] or (n["role"] == "compute" and n.get("active_mtu") != cexp["active_mtu"]):
            fail("NIC_MTU", f"{n['name']} mtu {n.get('mtu')} active_mtu {n.get('active_mtu')}")
    for n in compute:
        p = n.get("pcie", {})
        if p.get("gen") != cexp["pcie_gen"] or p.get("width") != cexp["pcie_width"]:
            fail("PCIE_DEGRADED", f"{n['name']} Gen{p.get('gen')} x{p.get('width')}")
        bw = n.get("rdma_pair_bw_gbps")
        if bw is None or bw < thr["rdma_pair_bw_min_gbps"]:
            fail("RDMA_PAIR_BW_LOW", f"{n['name']} {bw} Gb/s < {thr['rdma_pair_bw_min_gbps']}")

    st = result.get("storage", {})
    nvme = st.get("nvme", [])
    if len(nvme) != exp["nvme_count"]:
        fail("NVME_COUNT", f"{len(nvme)} NVMe devices, expected {exp['nvme_count']}")
    if any(d.get("media_errors", 0) > thr["nvme_media_errors_max"] or d.get("critical_warning", 0) for d in nvme):
        fail("NVME_MEDIA_ERRORS", "media errors or critical warning on NVMe")
    if st.get("fio_seq_read_gbs", 0.0) < thr["fio_seq_read_min_gbs"]:
        fail("STORAGE_THROUGHPUT_LOW", f"{st.get('fio_seq_read_gbs')} GB/s")

    nccl = result.get("nccl_single_node") or {}
    floors = thr["nccl_allreduce_busbw_min_gbs"]
    algo = nccl.get("algorithm")
    if algo not in floors:
        fail("NCCL_ALGO_UNRECORDED", f"NCCL algorithm {algo!r} not recorded or has no baseline")
    elif nccl.get("busbw_gbs", 0.0) < floors[algo]:
        fail("NCCL_BUSBW_LOW", f"{nccl.get('busbw_gbs')} GB/s < {floors[algo]} ({algo})")

    if result.get("xid_events"):
        fail("XID_PRESENT", ", ".join(f"Xid {x['xid']} @ {x.get('bdf')}" for x in result["xid_events"]))

    fw = dict(result.get("firmware", {}))
    fw["nic_fw"] = [n.get("fw") for n in compute if n.get("fw") is not None]
    comp = check_compat(fw, matrix)
    if comp["status"] in ("OFF_MATRIX", "BLOCKED"):
        fail("FW_OFF_MATRIX", f"{comp['status']} closest={comp['closest']} mismatches={comp['mismatches']} "
                              f"blocked={comp['blocked']}")
    elif comp["status"] == "DEPRECATED":
        warns.add("FW_DEPRECATED")
        details.append(f"FW_DEPRECATED: matches deprecated bundle {comp['bundle']}")

    verdict = "FAIL" if codes else ("WARN" if warns else "PASS")
    return {"node": result.get("node"), "verdict": verdict, "codes": sorted(codes),
            "warnings": sorted(warns), "details": details}


def evaluate_fleet(results: list[dict[str, Any]], policy: dict[str, Any],
                   matrix: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate every node; return the per-node verdicts in input order."""
    return [evaluate_node(r, policy, matrix) for r in results]


# --------------------------------------------------------------------------------------------
# 3. Lifecycle state machine
# --------------------------------------------------------------------------------------------
def transition_table() -> dict[tuple[str, str], str]:
    """Return the allowed ``(from_state, event) -> to_state`` transitions.

    ``inventory_update`` is handled separately (a self-transition allowed in every state except
    ``retired``) and is not part of this table.
    """
    return {
        ("discovered", "image"): "imaged",
        ("imaged", "pass_acceptance"): "validated",
        ("imaged", "fail_acceptance"): "repair",
        ("validated", "enable"): "schedulable",
        ("validated", "reimage"): "imaged",
        ("schedulable", "drain"): "draining",
        ("draining", "cancel_drain"): "schedulable",
        ("draining", "drain_complete"): "drained",
        ("drained", "send_to_repair"): "repair",
        ("drained", "reimage"): "imaged",
        ("drained", "retire"): "retired",
        ("repair", "reimage"): "imaged",
        ("repair", "retire"): "retired",
    }


def _guard(node: dict[str, Any], event: str, ev: dict[str, Any], matrix: dict[str, Any]) -> str | None:
    """Return a reject code if the guard for this (state, event) fails, else None."""
    state = node["state"]
    if event == "image":
        if any(not node.get(f) for f in REQUIRED_INVENTORY_FIELDS):
            return "INVENTORY_INCOMPLETE"
    elif event == "pass_acceptance":
        verdict = ev.get("acceptance_verdict")
        if not (verdict == "PASS" or (verdict == "WARN" and ev.get("waiver"))):
            return "ACCEPTANCE_NOT_PASSED"
    elif event in ("fail_acceptance", "send_to_repair"):
        if not ev.get("ticket"):
            return "MISSING_TICKET"
    elif event == "enable":
        if check_compat(node["firmware"], matrix)["status"] != "OK":
            return "FW_OFF_MATRIX"
    elif event == "drain":
        if not ev.get("reason") or ev.get("category") not in ("fault", "maintenance"):
            return "MISSING_REASON"
    elif event == "cancel_drain":
        if (node.get("drain") or {}).get("category") != "maintenance":
            return "FAULT_DRAIN_REQUIRES_REPAIR"
    elif event == "drain_complete":
        if ev.get("running_jobs", 1) != 0:
            return "JOBS_STILL_RUNNING"
    elif event == "reimage" and state == "repair":
        if ev.get("ticket_status") != "closed":
            return "TICKET_OPEN"
    elif event == "retire":
        if not ev.get("sanitization_cert"):
            return "SANITIZATION_MISSING"
    return None


def _side_effects(node: dict[str, Any], event: str, ev: dict[str, Any]) -> None:
    if event == "drain":
        node["drain"] = {"reason": ev["reason"], "category": ev["category"]}
    elif event == "cancel_drain":
        node["drain"] = None
    elif event in ("fail_acceptance", "send_to_repair"):
        node["ticket"] = {"id": ev["ticket"], "status": "open"}
    elif event == "reimage":
        if "firmware" in ev:
            node["firmware"] = dict(ev["firmware"])
        if node.get("ticket"):
            node["ticket"] = dict(node["ticket"], status="closed")
        node["drain"] = None
    elif event == "retire":
        node["sanitization_cert"] = ev["sanitization_cert"]


def apply_event(nodes: dict[str, dict[str, Any]], event: dict[str, Any], audit: list[dict[str, Any]],
                matrix: dict[str, Any]) -> bool:
    """Apply one lifecycle event; append exactly one audit record; return True if applied.

    ``nodes`` maps node name -> inventory record and is mutated in place on success (state and
    side-effect fields only). A rejected event never changes ``nodes``.

    Audit record keys: seq, ts, node, event, actor, from_state, to_state (None if rejected),
    result ("applied" | "rejected"), reason_code (None if applied).

    Check order: UNKNOWN_NODE -> ILLEGAL_TRANSITION -> event-specific guard.
    """
    name, ename, ev = event["node"], event["event"], event.get("evidence", {}) or {}
    rec = {"seq": event["seq"], "ts": event["ts"], "node": name, "event": ename,
           "actor": event.get("actor"), "from_state": None, "to_state": None,
           "result": "rejected", "reason_code": None}
    node = nodes.get(name)
    if node is None:
        rec["reason_code"] = "UNKNOWN_NODE"
        audit.append(rec)
        return False
    rec["from_state"] = node["state"]
    if ename == "inventory_update":
        if node["state"] == "retired":
            rec["reason_code"] = "ILLEGAL_TRANSITION"
            audit.append(rec)
            return False
        for k, v in ev.items():
            if k in REQUIRED_INVENTORY_FIELDS:
                node[k] = v
        rec.update(to_state=node["state"], result="applied")
        audit.append(rec)
        return True
    target = transition_table().get((node["state"], ename))
    if target is None:
        rec["reason_code"] = "ILLEGAL_TRANSITION"
        audit.append(rec)
        return False
    code = _guard(node, ename, ev, matrix)
    if code:
        rec["reason_code"] = code
        audit.append(rec)
        return False
    _side_effects(node, ename, ev)
    node["state"] = target
    rec.update(to_state=target, result="applied")
    audit.append(rec)
    return True


def replay(inventory: list[dict[str, Any]], events: list[dict[str, Any]],
           matrix: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Replay events (sorted by ``seq``) over a deep copy of the inventory.

    Returns ``(nodes_by_name, audit_log)``. The input inventory is not modified.
    """
    nodes = {r["node"]: copy.deepcopy(r) for r in inventory}
    audit: list[dict[str, Any]] = []
    for ev in sorted(events, key=lambda e: e["seq"]):
        apply_event(nodes, ev, audit, matrix)
    return nodes, audit


# --------------------------------------------------------------------------------------------
# 4. Staged upgrade planner
# --------------------------------------------------------------------------------------------
def plan_upgrade_waves(inventory: list[dict[str, Any]], matrix: dict[str, Any], target_bundle: str,
                       canary_size: int = 2, max_per_wave: int = 4,
                       max_per_rack_per_wave: int = 1) -> dict[str, Any]:
    """Build a canary + wave upgrade plan to ``target_bundle``.

    Eligible nodes: state == "schedulable" and not already exactly on ``target_bundle``.
    Excluded nodes are reported as ``{node: reason}`` with reason "state:<state>" or
    "already_on_target".

    Rules:
      * canary: ``canary_size`` nodes, all in different racks; chosen as the alphabetically first
        eligible node of each rack, racks taken in alphabetical order of their first node.
      * waves: each wave has <= ``max_per_wave`` nodes and <= ``max_per_rack_per_wave`` nodes per
        rack; every remaining eligible node appears exactly once; the number of waves equals the
        lower bound max(ceil(remaining / max_per_wave), ceil(max_rack_remaining / max_per_rack_per_wave)).
        Greedy "largest remaining rack first" (ties by rack name), nodes within a rack by name,
        achieves the bound.

    Returns ``{"target", "canary": [...], "waves": [[...], ...], "excluded": {node: reason}}``.
    """
    excluded: dict[str, str] = {}
    by_rack: dict[str, list[str]] = {}
    for r in sorted(inventory, key=lambda x: x["node"]):
        if r["state"] != "schedulable":
            excluded[r["node"]] = f"state:{r['state']}"
            continue
        if check_compat(r["firmware"], matrix)["bundle"] == target_bundle:
            excluded[r["node"]] = "already_on_target"
            continue
        by_rack.setdefault(r["rack"], []).append(r["node"])

    canary: list[str] = []
    for rack in sorted(by_rack, key=lambda k: by_rack[k][0]):
        if len(canary) >= canary_size:
            break
        canary.append(by_rack[rack].pop(0))
    by_rack = {k: v for k, v in by_rack.items() if v}

    waves: list[list[str]] = []
    while by_rack:
        order = sorted(by_rack, key=lambda k: (-len(by_rack[k]), k))
        wave: list[str] = []
        for rack in order:
            take = min(max_per_rack_per_wave, len(by_rack[rack]), max_per_wave - len(wave))
            wave.extend(by_rack[rack][:take])
            by_rack[rack] = by_rack[rack][take:]
            if len(wave) >= max_per_wave:
                break
        by_rack = {k: v for k, v in by_rack.items() if v}
        waves.append(sorted(wave))
    return {"target": target_bundle, "canary": canary, "waves": waves, "excluded": excluded}


def wave_lower_bound(remaining_per_rack: dict[str, int], max_per_wave: int, max_per_rack_per_wave: int) -> int:
    """Minimum number of waves for the given per-rack counts (helper used in the text)."""
    total = sum(remaining_per_rack.values())
    if total == 0:
        return 0
    return max(math.ceil(total / max_per_wave),
               math.ceil(max(remaining_per_rack.values()) / max_per_rack_per_wave))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run the Chapter 16 fleet lifecycle tools on lab data.")
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    args = ap.parse_args()
    pol = load_yaml(args.data / "acceptance_policy.yaml")
    mat = load_yaml(args.data / "compat_matrix.yaml")
    for v in evaluate_fleet(load_json(args.data / "acceptance_results.json"), pol, mat):
        if v["verdict"] != "PASS":
            print(f"{v['node']}: {v['verdict']} {v['codes']} {v['warnings']}")
    inv = load_json(args.data / "inventory.json")
    final, log = replay(inv, load_json(args.data / "lifecycle_events.json"), mat)
    for a in log:
        if a["result"] == "rejected":
            print(f"seq {a['seq']:>2} {a['node']} {a['event']}: REJECTED {a['reason_code']}")
    print(json.dumps(plan_upgrade_waves(inv, mat, "B-2026.10"), indent=1))
