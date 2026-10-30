#!/usr/bin/env python3
"""Generate the Chapter 16 lab datasets (ORION-256 fleet lifecycle).

Outputs (all deterministic for a given seed; re-running produces byte-identical files):

* ``data/acceptance_policy.yaml``   -- acceptance thresholds for an HX8 node
* ``data/compat_matrix.yaml``       -- validated firmware/driver bundles + blocked versions
* ``data/acceptance_results.json``  -- per-node acceptance results for the 32 ORION nodes
* ``data/inventory.json``           -- fleet inventory / CMDB snapshot at the start of the ops week
* ``data/lifecycle_events.json``    -- ordered lifecycle events to replay through the state machine

All values are [ILLUSTRATIVE] and modelled on the HX8 node in docs/REFERENCE_CLUSTER.md.
Firmware/driver version strings are invented for teaching; they are not a statement about any
vendor's real compatibility matrix.

Usage:
    python tools/generate_data.py            # writes into ../data
    python tools/generate_data.py --seed 16 --out ../data
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import yaml

N_NODES = 32
NODES_PER_RACK = 4
GPU_BDFS = ["0000:18:00.0", "0000:2a:00.0", "0000:3a:00.0", "0000:5d:00.0",
            "0000:9a:00.0", "0000:ab:00.0", "0000:ba:00.0", "0000:db:00.0"]
NIC_BDFS = ["0000:17:00.0", "0000:29:00.0", "0000:39:00.0", "0000:5c:00.0",
            "0000:99:00.0", "0000:aa:00.0", "0000:b9:00.0", "0000:da:00.0"]

BUNDLES = [
    {
        "id": "B-2025.11",
        "status": "deprecated",
        "notes": "Previous baseline. Still bootable; no longer accepted for new nodes.",
        "versions": {
            "bios": "2.2.4", "bmc_fw": "1.10.3", "kernel": "5.15.0-119-generic",
            "gpu_driver": "535.183.06", "gpu_vbios": "96.00.89.00.01",
            "nic_fw": "28.39.1002", "rdma_stack": "24.01",
        },
    },
    {
        "id": "B-2026.04",
        "status": "production",
        "notes": "Current fleet baseline (build-out acceptance ran on this bundle).",
        "versions": {
            "bios": "2.4.1", "bmc_fw": "1.12.0", "kernel": "6.8.0-45-generic",
            "gpu_driver": "550.127.08", "gpu_vbios": "96.00.99.00.01",
            "nic_fw": "28.41.1000", "rdma_stack": "24.07",
        },
    },
    {
        "id": "B-2026.10",
        "status": "production",
        "notes": "Upgrade target. Qualified on 2 pilot nodes for 14 days.",
        "versions": {
            "bios": "2.6.0", "bmc_fw": "1.14.2", "kernel": "6.8.0-60-generic",
            "gpu_driver": "570.86.15", "gpu_vbios": "96.00.A5.00.01",
            "nic_fw": "28.43.1014", "rdma_stack": "24.10",
        },
    },
]

BLOCKED = [
    {"component": "nic_fw", "version": "28.42.1000",
     "reason": "Intermittent 400G link renegotiation under load (internal defect FAB-1187). Do not deploy."},
    {"component": "gpu_driver", "version": "570.40.02",
     "reason": "Pre-release driver; not qualified."},
]

POLICY = {
    "policy_version": "acc-2026.10",
    "node_type": "HX8",
    "expected": {
        "gpu_count": 8,
        "gpu_product": "H100-SXM-80GB",
        "gpu_hbm_total_mib_min": 81000,
        "gpu_pcie": {"gen": 5, "width": 16},
        "nvlink_links_per_gpu": 18,
        "compute_nic": {"count": 8, "speed_mbps": 400000, "pcie_gen": 5, "pcie_width": 16,
                        "mtu": 9000, "active_mtu": 4096},
        "frontend_nic": {"count": 2, "speed_mbps": 200000, "mtu": 9000},
        "nvme_count": 8,
    },
    "thresholds": {
        "dcgm_diag_min_level": 3,
        "ecc_dbe_volatile_max": 0,
        "ecc_sbe_volatile_warn": 10,
        "max_gpu_temp_c": 87,
        "throttle_reasons_fail": ["HW_THERMAL_SLOWDOWN", "SW_THERMAL_SLOWDOWN", "HW_POWER_BRAKE_SLOWDOWN"],
        "throttle_reasons_ignore": ["SW_POWER_CAP", "GPU_IDLE"],
        "rdma_pair_bw_min_gbps": 360.0,
        # Single-node all_reduce_perf busbw floor at 8 GiB, keyed by the NCCL algorithm actually used
        # (from NCCL_DEBUG=INFO). NVLS = NVLink SHARP in-switch reduction; Ring = NVLS disabled or
        # unavailable. Baseline each separately on known-good nodes [ILLUSTRATIVE values].
        "nccl_allreduce_busbw_min_gbs": {"NVLS": 400.0, "Ring": 330.0},
        "fio_seq_read_min_gbs": 40.0,
        "nvme_media_errors_max": 0,
    },
}

# Planted acceptance anomalies (documented for instructors in solutions/lab/PLANTED_FAULTS.md).
MISSING_GPU_NODE, MISSING_GPU_INDEX = 4, 5
PCIE_X8_NODE, PCIE_X8_GPU = 11, 3
NIC_200G_NODE, NIC_200G_IDX = 19, 5
FW_OFF_NODE, FW_OFF_NIC = 23, 7
THERMAL_NODE, THERMAL_GPU = 27, 6
ROWREMAP_NODE, ROWREMAP_GPU = 30, 2
SBE_WARN_NODE, SBE_WARN_GPU = 7, 1
RING_NODE = 15  # distractor: Ring-algorithm NCCL run at a healthy Ring busbw must PASS


def node_name(n: int) -> str:
    return f"orion-n{n:02d}"


def rack_of(n: int) -> str:
    return f"rack-{(n - 1) // NODES_PER_RACK + 1:02d}"


def fake_uuid(rng: random.Random) -> str:
    h = "".join(rng.choice("0123456789abcdef") for _ in range(32))
    return f"GPU-{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def acceptance_for(n: int, rng: random.Random) -> dict:
    fw = dict(BUNDLES[1]["versions"])
    gpus = []
    for i in range(8):
        reasons = ["SW_POWER_CAP"] if rng.random() < 0.6 else []
        g = {
            "index": i,
            "uuid": fake_uuid(rng),
            "bdf": GPU_BDFS[i],
            "product": "H100-SXM-80GB",
            "hbm_total_mib": 81559,
            "pcie": {"gen": 5, "width": 16, "gen_idle": 1 if rng.random() < 0.5 else 5},
            "nvlink_links_up": 18,
            "ecc": {"sbe_volatile": rng.choice([0, 0, 0, 0, 1, 2]), "dbe_volatile": 0, "dbe_aggregate": 0},
            "row_remap": {"correctable": 0, "uncorrectable": 0, "pending": False, "failure": False},
            "burn_in": {"duration_h": 24, "max_temp_c": rng.randint(62, 79), "throttle_reasons": reasons},
        }
        gpus.append(g)
    xids: list[dict] = []

    if n == MISSING_GPU_NODE:
        gpus = [g for g in gpus if g["index"] != MISSING_GPU_INDEX]
        xids.append({"xid": 79, "bdf": GPU_BDFS[MISSING_GPU_INDEX],
                     "message": "GPU has fallen off the bus."})
    if n == PCIE_X8_NODE:
        gpus[PCIE_X8_GPU]["pcie"]["width"] = 8
    if n == THERMAL_NODE:
        gpus[THERMAL_GPU]["burn_in"]["max_temp_c"] = 89
        gpus[THERMAL_GPU]["burn_in"]["throttle_reasons"] = ["SW_POWER_CAP", "SW_THERMAL_SLOWDOWN"]
    if n == ROWREMAP_NODE:
        gpus[ROWREMAP_GPU]["ecc"]["dbe_aggregate"] = 1
        gpus[ROWREMAP_GPU]["row_remap"]["pending"] = True
    if n == SBE_WARN_NODE:
        gpus[SBE_WARN_GPU]["ecc"]["sbe_volatile"] = 14

    nics = []
    for r in range(8):
        nic = {
            "name": f"rdma{r}",
            "role": "compute",
            "rail": r,
            "bdf": NIC_BDFS[r],
            "link_state": "up",
            "speed_mbps": 400000,
            "mtu": 9000,
            "active_mtu": 4096,
            "pcie": {"gen": 5, "width": 16},
            "fw": fw["nic_fw"],
            "rdma_pair_bw_gbps": round(rng.uniform(386.0, 394.5), 1),
        }
        nics.append(nic)
    if n == NIC_200G_NODE:
        nics[NIC_200G_IDX]["speed_mbps"] = 200000
        nics[NIC_200G_IDX]["rdma_pair_bw_gbps"] = round(rng.uniform(191.0, 196.0), 1)
    if n == FW_OFF_NODE:
        nics[FW_OFF_NIC]["fw"] = "28.42.1000"
    for s in range(2):
        nics.append({"name": f"fe{s}", "role": "frontend", "rail": None, "link_state": "up",
                     "speed_mbps": 200000, "mtu": 9000, "pcie": {"gen": 5, "width": 16}})

    nvme = [{"slot": s, "capacity_tb": 3.84, "media_errors": 0, "critical_warning": 0,
             "percentage_used": rng.choice([0, 0, 1])} for s in range(8)]

    n_gpus = len(gpus)
    nccl = {"test": "all_reduce_perf", "gpus": n_gpus, "max_bytes": 8589934592,
            "nccl_version": "2.21.5", "algorithm": "NVLS",
            "busbw_gbs": round(rng.uniform(452.0, 478.0), 1)}
    if n == RING_NODE:  # NVLS unavailable on this node's run (NCCL_ALGO=Ring): healthy Ring baseline
        nccl.update(algorithm="Ring", busbw_gbs=round(rng.uniform(366.0, 374.0), 1))
    return {
        "node": node_name(n),
        "rack": rack_of(n),
        "serial": f"SN-HX8-2409{n:03d}",
        "collected_at": f"2026-09-{8 + (n - 1) // 8:02d}T{6 + (n % 8):02d}:15:00Z",
        "acceptance_policy": POLICY["policy_version"],
        "firmware": {k: v for k, v in fw.items() if k != "nic_fw"},
        "gpus": gpus,
        "dcgm_diag": {"level": 3, "result": "Pass", "gpus_tested": n_gpus},
        "nics": nics,
        "storage": {"nvme": nvme, "fio_seq_read_gbs": round(rng.uniform(46.0, 52.0), 1)},
        "nccl_single_node": nccl,
        "xid_events": xids,
    }


def inventory(rng: random.Random) -> list[dict]:
    base = BUNDLES[1]["versions"]
    target = BUNDLES[2]["versions"]
    special = {
        5: {"state": "draining", "drain": {"reason": "Xid 79 on GPU4 (fell off bus)", "category": "fault"}},
        9: {"state": "drained", "drain": {"reason": "planned fw wave pilot", "category": "maintenance"}},
        14: {"state": "repair", "ticket": {"id": "FLT-4411", "status": "open"}},
        21: {"state": "repair", "ticket": {"id": "FLT-4420", "status": "closed"}},
        26: {"state": "discovered"},
        29: {"state": "validated"},
        31: {"state": "imaged"},
        32: {"state": "draining", "drain": {"reason": "PDU-B maintenance window", "category": "maintenance"}},
    }
    out = []
    for n in range(1, N_NODES + 1):
        fw = dict(target if n in (2, 18) else base)
        if n == 29:
            fw["nic_fw"] = "28.42.1000"
        rec = {
            "node": node_name(n),
            "rack": rack_of(n),
            "serial": f"SN-HX8-2409{n:03d}",
            "asset_tag": f"HAL-{n:04d}",
            "bmc_mac": "02:00:5e:%02x:%02x:%02x" % (16, n, rng.randint(0, 255)),
            "bmc_ip": f"172.16.1.{10 + n}",
            "state": "schedulable",
            "firmware": fw,
            "drain": None,
            "ticket": None,
        }
        rec.update(special.get(n, {}))
        if n == 26:
            rec["serial"] = "SN-HX8-2410126"
            rec["asset_tag"] = None
        out.append(rec)
    return out


def events() -> list[dict]:
    target = dict(BUNDLES[2]["versions"])
    base_fixed = dict(BUNDLES[1]["versions"])
    ev = [
        ("orion-n05", "drain_complete", "fleet-bot", {"running_jobs": 1}),
        ("orion-n05", "drain_complete", "fleet-bot", {"running_jobs": 0}),
        ("orion-n05", "send_to_repair", "oncall-amara", {"ticket": "FLT-4431"}),
        ("orion-n32", "cancel_drain", "oncall-amara", {}),
        ("orion-n09", "reimage", "fleet-bot", {"firmware": target, "change": "CHG-7720"}),
        ("orion-n09", "pass_acceptance", "acceptance-bot", {"acceptance_verdict": "PASS"}),
        ("orion-n09", "enable", "fleet-bot", {}),
        ("orion-n14", "reimage", "fleet-bot", {"ticket_status": "open"}),
        ("orion-n21", "reimage", "fleet-bot", {"ticket_status": "closed"}),
        ("orion-n21", "enable", "oncall-jun", {}),
        ("orion-n21", "pass_acceptance", "acceptance-bot", {"acceptance_verdict": "WARN"}),
        ("orion-n21", "pass_acceptance", "acceptance-bot", {"acceptance_verdict": "WARN", "waiver": "WVR-0192"}),
        ("orion-n21", "enable", "fleet-bot", {}),
        ("orion-n26", "image", "fleet-bot", {}),
        ("orion-n26", "inventory_update", "dc-tech-olu", {"asset_tag": "HAL-0026B"}),
        ("orion-n26", "image", "fleet-bot", {}),
        ("orion-n26", "fail_acceptance", "acceptance-bot", {"acceptance_verdict": "FAIL", "ticket": "FLT-4437"}),
        ("orion-n29", "enable", "oncall-jun", {}),
        ("orion-n29", "reimage", "fleet-bot", {"firmware": base_fixed, "change": "CHG-7725"}),
        ("orion-n29", "pass_acceptance", "acceptance-bot", {"acceptance_verdict": "PASS"}),
        ("orion-n29", "enable", "fleet-bot", {}),
        ("orion-n31", "pass_acceptance", "acceptance-bot", {"acceptance_verdict": "PASS"}),
        ("orion-n12", "send_to_repair", "oncall-jun", {"ticket": "FLT-4440"}),
        ("orion-n12", "drain", "health-bot", {"reason": "Xid 48 (DBE) on GPU3", "category": "fault"}),
        ("orion-n12", "cancel_drain", "oncall-jun", {}),
        ("orion-n12", "drain_complete", "fleet-bot", {"running_jobs": 0}),
        ("orion-n12", "send_to_repair", "oncall-jun", {}),
        ("orion-n12", "send_to_repair", "oncall-jun", {"ticket": "FLT-4440"}),
        ("orion-n14", "retire", "fleet-mgr-li", {}),
        ("orion-n14", "retire", "fleet-mgr-li", {"sanitization_cert": "SAN-2026-0091"}),
        ("orion-n14", "reimage", "fleet-bot", {"ticket_status": "closed"}),
        ("orion-n32", "drain", "oncall-amara", {"category": "maintenance"}),
        ("orion-n40", "drain", "oncall-amara", {"reason": "typo in hostname", "category": "maintenance"}),
        ("orion-n03", "drain", "upgrade-ctl", {"reason": "fw wave canary B-2026.10", "category": "maintenance"}),
        ("orion-n03", "drain_complete", "upgrade-ctl", {"running_jobs": 0}),
        ("orion-n31", "enable", "fleet-bot", {}),
    ]
    out = []
    for i, (node, event, actor, evidence) in enumerate(ev, start=1):
        out.append({"seq": i, "ts": f"2026-10-12T{8 + i // 6:02d}:{(i * 7) % 60:02d}:00Z",
                    "node": node, "event": event, "actor": actor, "evidence": evidence})
    return out


def dump_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=16)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    with open(args.out / "acceptance_policy.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# HX8 node acceptance policy [ILLUSTRATIVE thresholds; tune per platform]\n")
        yaml.safe_dump(POLICY, f, sort_keys=False)
    with open(args.out / "compat_matrix.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# ORION firmware/driver compatibility matrix [ILLUSTRATIVE version strings]\n")
        yaml.safe_dump({"matrix_version": "2026-10-01",
                        "components": list(BUNDLES[0]["versions"].keys()),
                        "bundles": BUNDLES, "blocked": BLOCKED}, f, sort_keys=False)
    dump_json(args.out / "acceptance_results.json",
              [acceptance_for(n, rng) for n in range(1, N_NODES + 1)])
    dump_json(args.out / "inventory.json", inventory(rng))
    dump_json(args.out / "lifecycle_events.json", events())
    print(f"wrote 5 files to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
