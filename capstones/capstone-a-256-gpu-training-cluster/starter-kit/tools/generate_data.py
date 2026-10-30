#!/usr/bin/env python3
"""Generate the Capstone A design-input dataset for ORION-256.

Writes (deterministically; re-running produces byte-identical files):
  design_inputs.yaml   component catalog, fabric options, workload scenarios, economics
  facility.yaml        rack positions with power feeds, cooling per row, PUE
  floorplan.csv        rack placement (row, position, x/y in metres) and contents
  hostfile_job4471.txt node order handed to the launcher by the inventory API (seeded shuffle)

All prices, power figures and facility values are [ILLUSTRATIVE] teaching values modeled on
docs/REFERENCE_CLUSTER.md. They are not quotes and not vendor specifications.

Usage:
    python tools/generate_data.py [--out ../data] [--seed 2026]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yaml

RACK_PITCH_M = 0.8   # GPU-rack width incl. side panels [ILLUSTRATIVE]
ROW_PITCH_M = 3.6    # row-to-row pitch (rack depth + hot/cold aisle) [ILLUSTRATIVE]


def design_inputs() -> dict:
    return {
        "provenance": "ILLUSTRATIVE teaching values for ORION-256 (Halcyon AI). Not quotes.",
        "cluster": {"n_nodes": 32, "gpus_per_node": 8, "nics_per_node": 8, "nic_gbps": 400,
                    "nodes_per_gpu_rack": 4},
        "catalog": {
            # key: {usd, watts, reach_m (media only), note}
            "node_hx8": {"usd": 300000, "watts_max": 10200, "watts_sustained": 8500,
                         "note": "8x H100-class SXM, 8x 400G NIC, 2x 200G FE NIC; host-side optics counted in node power"},
            "switch_64x400g": {"usd": 90000, "watts": 1000,
                               "note": "64 x 400G OSFP ports = 25.6 Tb/s in use; base power excludes switch-side transceivers"},
            "xcvr_400g_mm": {"usd": 700, "watts": 9, "reach_m": 50,
                             "note": "400G multimode optic; 50 m is an ILLUSTRATIVE site policy for the installed MM plant (module reach on OM4 is typically ~70-100 m; verify per datasheet)"},
            "xcvr_400g_sm": {"usd": 1100, "watts": 11, "reach_m": 500,
                             "note": "400G single-mode optic"},
            "dac_400g": {"usd": 250, "watts": 0, "reach_m": 3,
                         "note": "400G passive copper DAC; price includes both ends"},
            "fiber_mm": {"usd_base": 60, "usd_per_m": 2.0, "note": "MM fiber jumper/trunk per link"},
            "fiber_sm": {"usd_base": 50, "usd_per_m": 1.5, "note": "SM fiber jumper/trunk per link"},
        },
        "fixed_items": [
            {"item": "storage_server", "qty": 8, "usd": 120000, "watts": 2000,
             "note": "parallel FS servers (~160 GB/s read aggregate per REFERENCE_CLUSTER)"},
            {"item": "frontend_switch_64x200g", "qty": 4, "usd": 40000, "watts": 800,
             "note": "2 frontend leaves + 2 frontend spines; 3:1 by ports, 1.5:1 by bandwidth (200G hosts, 400G uplinks)"},
            {"item": "oob_switch_48x1g", "qty": 3, "usd": 5000, "watts": 150, "note": "BMC network"},
            {"item": "mgmt_server", "qty": 3, "usd": 15000, "watts": 600,
             "note": "Slurm controller, provisioning, monitoring"},
            {"item": "rack_pdu_kit", "qty": 13, "usd": 10000, "watts": 0,
             "note": "rack, 2 x PDUs, containment per rack position"},
        ],
        "fabric_options": {
            "A_rail_1to1": {
                "description": "Rail-optimized leaf-spine, one leaf per rail, non-blocking (ORION baseline)",
                "style": "rail", "leaf_radix": 64, "downlinks_per_leaf": 32, "uplinks_per_leaf": 32,
                "spine_radix": 64, "leaf_location": "network_racks", "spine_location": "network_racks"},
            "B_tor_2to1": {
                "description": "Top-of-rack leaf per GPU rack (all 8 rails of 4 nodes), 2:1 oversubscribed",
                "style": "tor", "leaf_radix": 64, "downlinks_per_leaf": 32, "uplinks_per_leaf": 16,
                "spine_radix": 64, "leaf_location": "gpu_racks", "spine_location": "network_racks"},
            "C_vendor_quote_3to1": {
                "description": "Vendor quote: 48 down / 16 up per leaf to save one leaf",
                "style": "rail", "leaf_radix": 64, "downlinks_per_leaf": 48, "uplinks_per_leaf": 16,
                "spine_radix": 64, "leaf_location": "network_racks", "spine_location": "network_racks"},
        },
        "workload": {
            "name": "W-TRAIN",
            "params": 70.0e9, "hidden": 8192, "layers": 80, "seq_len": 4096, "global_batch_seqs": 1024,
            "bytes_per_grad": 2, "bytes_per_param_bf16": 2, "bytes_per_activation": 2,
            "gpu_peak_flops": 989.0e12, "mfu": 0.40,
            "busbw_efficiency": 0.80,
            "dp_overlap_window_s": 0.07,
            "exposed_comm_fraction_fsdp": 0.30,
            "scenarios": {
                "baseline_3d": {"tp": 8, "pp": 4, "dp": 8, "sharding": "dp_allreduce",
                                "note": "REFERENCE_CLUSTER baseline: TP inside NVLink, PP=4, DP=8"},
                "fsdp_dp32": {"tp": 8, "pp": 1, "dp": 32, "sharding": "zero3",
                              "note": "TP=8 + fully sharded data parallel across 32 nodes"},
            },
        },
        "economics": {"amortization_years": 4, "usd_per_kwh": 0.10, "hours_per_year": 8760},
    }


def facility() -> dict:
    gpu_ok = {"phases": 3, "voltage_v": 415, "breaker_a": 80}
    gpu_g05 = {"phases": 3, "voltage_v": 415, "breaker_a": 63}
    net = {"phases": 3, "voltage_v": 415, "breaker_a": 32}
    positions = {}
    for name in ["A01", "A02", "A03", "A04", "A07", "A08", "A09", "D10"]:
        positions[name] = dict(gpu_ok)
    positions["A07"] = dict(gpu_g05)       # legacy 63 A feeds at this position
    positions["A05"] = dict(net)
    positions["A06"] = dict(net)
    for name in ["B01", "B02", "B03", "B04", "B05"]:
        positions[name] = dict(net)
    return {
        "provenance": "ILLUSTRATIVE facility envelope for the ORION hall.",
        "power_redundancy": "2N",            # A and B feeds; either feed must carry the full rack
        "power_factor": 0.95,
        "continuous_load_derate": 0.80,      # site rule: continuous load <= 80 % of breaker rating
        "pue": 1.30,
        "positions": positions,
        "cooling_rows": {
            "A": {"units": 6, "unit_kw": 70, "redundancy": "N+1"},
            "B": {"units": 3, "unit_kw": 40, "redundancy": "N+1"},
            "D": {"units": 2, "unit_kw": 30, "redundancy": "N+1",
                  "note": "legacy air-cooled row at the far end of the hall"},
        },
        "cabling": {"tray_drop_m": 2.0, "slack_fraction": 0.10, "in_rack_m": 2.0,
                    "standard_lengths_m": [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100]},
    }


def floorplan() -> list[dict]:
    rows = []
    layout = [  # (rack_id, position, kind)
        ("rack-01", "A01", "gpu"), ("rack-02", "A02", "gpu"), ("rack-03", "A03", "gpu"), ("rack-04", "A04", "gpu"),
        ("net-01", "A05", "network"), ("net-02", "A06", "network"),
        ("rack-05", "A07", "gpu"), ("rack-06", "A08", "gpu"), ("rack-07", "A09", "gpu"),
        ("stor-01", "B01", "storage"), ("stor-02", "B02", "storage"), ("mgmt-01", "B03", "mgmt"),
        ("rack-08", "D10", "gpu"),
    ]
    row_y = {"A": 0.0, "B": 1 * ROW_PITCH_M, "D": 3 * ROW_PITCH_M}
    for rack, pos, kind in layout:
        row, idx = pos[0], int(pos[1:])
        x = (idx - 1) * RACK_PITCH_M
        if row == "D":
            x = 39.2  # far end of the hall (overflow position)
        rows.append({"rack": rack, "position": pos, "row": row, "x_m": round(x, 2),
                     "y_m": round(row_y[row], 2), "kind": kind})
    return rows


def write_floorplan(path: Path, rows: list[dict]) -> None:
    cols = ["rack", "position", "row", "x_m", "y_m", "kind"]
    lines = [",".join(cols)] + [",".join(str(r[c]) for c in cols) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def hostfile(seed: int) -> list[str]:
    rng = np.random.default_rng(seed)
    names = [f"orion-n{i:02d}" for i in range(1, 33)]
    order = rng.permutation(len(names))
    return [names[i] for i in order]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj: dict) -> None:
        text = yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100)
        (out / name).write_text(text, encoding="utf-8", newline="\n")

    dump("design_inputs.yaml", design_inputs())
    dump("facility.yaml", facility())
    write_floorplan(out / "floorplan.csv", floorplan())
    (out / "hostfile_job4471.txt").write_text("\n".join(hostfile(args.seed)) + "\n",
                                               encoding="utf-8", newline="\n")
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
