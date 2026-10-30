#!/usr/bin/env python3
"""Generate the Chapter 9 synthetic congestion-telemetry dataset (Progressive Lab 3).

INSTRUCTOR MATERIAL: this generator and the planted-fault specification it reads
(``solutions/lab/planted_faults.yaml``) are removed from the student release.

The dataset models a slice of the ORION-256 backend fabric (docs/REFERENCE_CLUSTER.md):
rail leaves ``orion-be-leaf-r3`` (hosts orion-n01..n16, NIC ``mlx5_3``) and ``orion-be-leaf-r4``
(hosts orion-n01..n08, NIC ``mlx5_4``), each with one representative uplink to
``orion-be-spine-1`` and ``orion-be-spine-2``.

Outputs (in ``../data``): switch_ports.csv, nic_counters.csv, flow_probes.csv, topology.yaml,
sim_configs.yaml. All values are SYNTHETIC / ILLUSTRATIVE. Same seed -> byte-identical files.

ECN consistency rule used throughout: a port only accumulates ECN marks when its TC3 egress watermark
exceeds that switch's configured Kmin; above Kmax every ECT packet is marked (~6 M packets/s at
~200 Gb/s with 4 KB packets).

Usage:
    python generate_telemetry.py [--spec ../../solutions/lab/planted_faults.yaml] [--out ../data]
"""
from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_SPEC = HERE.parent.parent / "solutions" / "lab" / "planted_faults.yaml"
L3, L4, S1, S2 = "orion-be-leaf-r3", "orion-be-leaf-r4", "orion-be-spine-1", "orion-be-spine-2"


def host(i: int) -> str:
    """0-based index -> canonical ORION host name (orion-n01 ...)."""
    return f"orion-n{i + 1:02d}"


def build_links() -> list[dict]:
    """Return link records. Each end is (kind, device, port_or_nic)."""
    links = []
    for i in range(16):
        links.append({"a": ("sw", L3, f"eth1/{i + 1}"), "b": ("nic", host(i), "mlx5_3"), "role": "downlink"})
    for i in range(8):
        links.append({"a": ("sw", L4, f"eth1/{i + 1}"), "b": ("nic", host(i), "mlx5_4"), "role": "downlink"})
    links.append({"a": ("sw", L3, "eth1/33"), "b": ("sw", S1, "eth1/25"), "role": "fabric"})
    links.append({"a": ("sw", L3, "eth1/41"), "b": ("sw", S2, "eth1/25"), "role": "fabric"})
    links.append({"a": ("sw", L4, "eth1/33"), "b": ("sw", S1, "eth1/33"), "role": "fabric"})
    links.append({"a": ("sw", L4, "eth1/41"), "b": ("sw", S2, "eth1/33"), "role": "fabric"})
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--out", type=Path, default=HERE.parent / "data")
    args = parser.parse_args()
    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    rng = np.random.default_rng(spec["seed"])
    interval = spec["interval_s"]
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    ts = np.arange(0, spec["duration_s"], interval)
    T = len(ts)
    ep = spec["episodes"]

    def mask(name: str) -> np.ndarray:
        w = ep[name]["window"]
        return (ts >= w[0]) & (ts < w[1])

    def U(lo: float, hi: float, m: np.ndarray | None = None) -> np.ndarray:
        n = int(m.sum()) if m is not None else T
        return rng.uniform(lo, hi, n)

    links = build_links()
    for L in links:
        L["g"], L["q"], L["ecn"], L["p"] = {}, {}, {}, {}
        for end in ("a", "b"):
            lo, hi = (120, 200) if L["role"] == "downlink" else (60, 120)
            L["g"][end] = U(lo, hi)
            # baseline watermark stays below every switch's Kmin (>= 150 KB), so no ECN marks
            L["q"][end] = np.minimum(rng.exponential(15.0, T), 120.0) if L[end][0] == "sw" else np.zeros(T)
            L["ecn"][end] = np.zeros(T)
            L["p"][end] = np.zeros(T)

    def link(dev: str, port: str) -> dict:
        for L in links:
            for end in ("a", "b"):
                if L[end][1] == dev and L[end][2] == port:
                    return L
        raise KeyError((dev, port))

    nic_extra: dict[tuple[str, str], dict[str, np.ndarray]] = {}
    for L in links:
        if L["b"][0] == "nic":
            nic_extra[(L["b"][1], L["b"][2])] = {"cnp_sent": U(0, 50), "cnp_handled": U(0, 50)}

    # --- incast at a leaf egress (Kmin 1500 KB on leaf-r3: watermark 2.6-3.6 MB -> p ~ 0.05-0.09)
    e = ep["incast"]
    m = mask("incast")
    L = link(e["leaf"], f"eth1/{e['dst_index'] + 1}")
    L["g"]["a"][m] = U(390, 398, m)
    L["q"]["a"][m] = U(2600, 3600, m)
    L["ecn"]["a"][m] = U(0.5e6, 1.0e6, m)
    nic_extra[(host(e["dst_index"]), "mlx5_3")]["cnp_sent"][m] = U(3.5e5, 4.5e5, m)
    for i in e["sender_indices"]:
        L = link(e["leaf"], f"eth1/{i + 1}")
        L["g"]["b"][m] = U(70, 110, m)
        L["p"]["a"][m] = U(2500, 6000, m)
        nic_extra[(host(i), "mlx5_3")]["cnp_handled"][m] = U(2.0e4, 3.0e4, m)

    # --- cross-rail incast with pause propagation
    e = ep["pause_propagation"]
    m = mask("pause_propagation")
    L = link(e["root_leaf"], f"eth1/{e['dst_index'] + 1}")
    L["g"]["a"][m] = U(390, 398, m)
    L["q"]["a"][m] = U(2800, 3800, m)
    L["ecn"]["a"][m] = U(0.6e6, 1.1e6, m)
    nic_extra[(host(e["dst_index"]), "mlx5_3")]["cnp_sent"][m] = U(2.5e5, 3.5e5, m)
    for port in ("eth1/33", "eth1/41"):        # root leaf pauses the spines; spine egress > Kmax
        L = link(e["root_leaf"], port)
        L["g"]["b"][m] = U(180, 210, m)
        L["q"]["b"][m] = U(1800, 3000, m)
        L["ecn"]["b"][m] = U(5.5e6, 6.4e6, m)
        L["p"]["a"][m] = U(6000, 10000, m)
    for port in ("eth1/33", "eth1/41"):        # spines pause the sender leaf; its uplink egress > Kmax
        L = link(e["sender_leaf"], port)
        L["g"]["a"][m] = U(180, 210, m)
        L["q"]["a"][m] = U(1600, 2200, m)
        L["ecn"]["a"][m] = U(5.5e6, 6.4e6, m)
        L["p"]["b"][m] = U(3000, 7000, m)
    for i in e["sender_indices"]:              # sender leaf pauses its NICs
        L = link(e["sender_leaf"], f"eth1/{i + 1}")
        L["g"]["b"][m] = U(40, 60, m)
        L["p"]["a"][m] = U(1500, 4000, m)
        nic_extra[(host(i), "mlx5_4")]["cnp_handled"][m] = U(2.5e4, 3.5e4, m)

    # --- PFC storm from one NIC (nothing dequeues toward it, so no ECN marks)
    e = ep["pfc_storm"]
    m = mask("pfc_storm")
    L = link(e["leaf"], f"eth1/{e['storm_index'] + 1}")
    L["g"]["a"][m] = U(0.0, 0.05, m)
    L["g"]["b"][m] = U(0.0, 0.05, m)
    L["q"]["a"][m] = U(3990, 4000, m)
    L["p"]["b"][m] = U(23500, 24000, m)
    nic_extra[(host(e["storm_index"]), "mlx5_3")]["cnp_sent"][m] = 0.0
    nic_extra[(host(e["storm_index"]), "mlx5_3")]["cnp_handled"][m] = 0.0
    for i in e["peer_indices"]:
        L = link(e["leaf"], f"eth1/{i + 1}")
        L["g"]["b"][m] = U(30, 50, m)
        L["p"]["a"][m] = U(5000, 7000, m)

    # --- benign busy port (leaf-r4 Kmin 150 KB). Marks > 0 only make sense with a watermark above
    # Kmin, so the watermark is floored at Kmin: 155-250 KB -> light marking only.
    e = ep["benign_busy"]
    m = mask("benign_busy")
    L = link(e["leaf"], f"eth1/{e['dst_index'] + 1}")
    L["g"]["a"][m] = U(375, 392, m)
    L["q"]["a"][m] = U(155, 250, m)
    L["ecn"]["a"][m] = U(2.0e4, 8.0e4, m)
    nic_extra[(host(e["dst_index"]), "mlx5_4")]["cnp_sent"][m] = U(5.0e3, 2.0e4, m)

    # --- emit switch_ports.csv and nic_counters.csv
    def cumulate(rate_per_s: np.ndarray, start: int) -> np.ndarray:
        return start + np.cumsum(np.rint(rate_per_s * interval).astype(np.int64))

    reset = spec["data_anomalies"]["counter_reset"]
    gap = spec["data_anomalies"]["telemetry_gap"]
    sw_rows, nic_rows = [], []
    for L in links:
        for end, other in (("a", "b"), ("b", "a")):
            kind, dev, port = L[end]
            tx, rx = L["g"][end], L["g"][other]
            if kind == "sw":
                ecn_c = cumulate(L["ecn"][end], int(rng.integers(1e6, 5e8)))
                ptx_c = cumulate(L["p"][end], int(rng.integers(0, 2e5)))
                prx_c = cumulate(L["p"][other], int(rng.integers(0, 2e5)))
                disc_c = np.full(T, int(rng.integers(0, 50)), dtype=np.int64)
                if (dev, port) == (reset["switch"], reset["port"]):
                    i0 = int(np.searchsorted(ts, reset["ts_s"]))
                    for arr, rate in ((ecn_c, L["ecn"][end]), (ptx_c, L["p"][end]), (prx_c, L["p"][other])):
                        arr[i0:] = np.cumsum(np.rint(rate * interval).astype(np.int64)[i0:])
                    disc_c[i0:] = 0
                for i in range(T):
                    if dev == gap["switch"] and gap["from_s"] <= ts[i] <= gap["to_s"]:
                        continue
                    sw_rows.append([int(ts[i]), dev, port, f"{tx[i]:.2f}", f"{rx[i]:.2f}", f"{L['q'][end][i]:.1f}",
                                    int(ecn_c[i]), int(ptx_c[i]), int(prx_c[i]), int(disc_c[i])])
            else:
                sw_dev, sw_port = L[other][1], L[other][2]
                ex = nic_extra[(dev, port)]
                cnp_s = cumulate(ex["cnp_sent"], int(rng.integers(1e5, 1e7)))
                cnp_h = cumulate(ex["cnp_handled"], int(rng.integers(1e5, 1e7)))
                ecn_rx = cumulate(L["ecn"][other], int(rng.integers(1e6, 5e8)))
                ptx_c = cumulate(L["p"][end], int(rng.integers(0, 2e5)))
                prx_c = cumulate(L["p"][other], int(rng.integers(0, 2e5)))
                for i in range(T):
                    nic_rows.append([int(ts[i]), dev, port, sw_dev, sw_port, f"{tx[i]:.2f}", f"{rx[i]:.2f}",
                                     int(cnp_s[i]), int(cnp_h[i]), int(ecn_rx[i]), int(ptx_c[i]), int(prx_c[i])])

    sw_rows.sort(key=lambda r: (r[0], r[1], int(r[2].split("/")[1])))
    nic_rows.sort(key=lambda r: (r[0], r[1], r[2]))
    with open(out / "switch_ports.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ts_s", "switch", "port", "tx_gbps", "rx_gbps", "q_tc3_max_kb", "ecn_marked_tc3",
                    "pfc_tx_p3", "pfc_rx_p3", "discards_tc3"])
        w.writerows(sw_rows)
    with open(out / "nic_counters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ts_s", "node", "nic", "switch", "port", "tx_gbps", "rx_gbps", "cnp_sent", "cnp_handled",
                    "ecn_marked_rx", "pfc_tx_p3", "pfc_rx_p3"])
        w.writerows(nic_rows)

    # --- emit flow_probes.csv
    nic_of = {L3: "mlx5_3", L4: "mlx5_4"}
    inflation = {  # probe -> list of (episode, p50 range, p99 range)
        "P1": [("incast", (40, 90), (150, 350)), ("pfc_storm", (600, 1200), (3000, 6000))],
        "P3": [("incast", (60, 90), (150, 400))],
        "P4": [("pause_propagation", (80, 150), (400, 900))],
    }
    pr_rows = []
    for p in spec["probes"]:
        (ssw, si), (dsw, di) = p["src"], p["dst"]
        cross = ssw != dsw
        p50 = U(7.0, 9.0) if cross else U(4.5, 6.0)
        p99 = U(14, 20) if cross else U(9, 14)
        for name, r50, r99 in inflation.get(p["id"], []):
            m = mask(name)
            p50[m] = U(*r50, m)
            p99[m] = U(*r99, m)
        for i in range(T):
            pr_rows.append([int(ts[i]), p["id"], host(si), nic_of[ssw], host(di), nic_of[dsw], ssw, f"eth1/{si + 1}",
                            dsw, f"eth1/{di + 1}", f"{p50[i]:.1f}", f"{p99[i]:.1f}"])
    pr_rows.sort(key=lambda r: (r[0], r[1]))
    with open(out / "flow_probes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ts_s", "probe", "src_node", "src_nic", "dst_node", "dst_nic", "src_switch", "src_port",
                    "dst_switch", "dst_port", "lat_p50_us", "lat_p99_us"])
        w.writerows(pr_rows)

    # --- emit topology.yaml (the QoS faults listed in the spec are encoded here)
    topo_links = [{"a_device": L["a"][1], "a_port": L["a"][2], "b_device": L["b"][1], "b_port": L["b"][2],
                   "b_kind": "nic" if L["b"][0] == "nic" else "switch", "role": L["role"]} for L in links]
    template = {"lossless_priorities": [3], "roce_dscp": 26, "roce_tc": 3, "cnp_dscp": 48, "cnp_tc": 6,
                "ecn_kmin_kb": 150, "ecn_kmax_kb": 1500, "ecn_pmax": 0.2, "pfc_watchdog": True}
    qos = {
        L3: {**copy.deepcopy(template), "ecn_kmin_kb": 1500, "ecn_kmax_kb": 6000, "pfc_watchdog": False},
        L4: {**copy.deepcopy(template), "cnp_tc": 3},
        S1: copy.deepcopy(template),
        S2: {**copy.deepcopy(template), "lossless_priorities": [3, 4]},
    }
    topology = {
        "description": "SYNTHETIC slice of ORION-256 backend fabric (rail 3 and rail 4 leaves, two spines).",
        "fabric_intent": {"line_rate_gbps": 400, "base_rtt_us": 4.0, "mtu_bytes": 4096, **copy.deepcopy(template)},
        "sample_interval_s": interval,
        "links": topo_links,
        "qos": qos,
    }
    with open(out / "topology.yaml", "w", newline="\n", encoding="utf-8") as f:
        yaml.safe_dump(topology, f, sort_keys=False)

    sim = {
        "common": {"n_senders": 12, "burst_bytes": 4_000_000, "line_gbps": 400, "dt_us": 0.2,
                   "feedback_delay_us": 4.0, "pause_delay_us": 1.0, "buffer_kb": 4000,
                   "headroom_kb": 1128,
                   "headroom_basis": "12 ingress ports x 93,496 B (Section 9.4 formula, 50 m) = 1,121,952 B "
                                     "~ 1,122 KB, rounded up to 12 x 94 KB = 1,128 KB",
                   "xoff_kb": 1000, "xon_kb": 800, "mtu_bytes": 4096, "cnp_interval_us": 50.0,
                   "alpha_timer_us": 55.0, "increase_timer_us": 55.0, "g": 1.0 / 256, "retx_delay_us": 20.0,
                   "max_time_us": 20000.0},
        "configs": {
            "A_as_found": {"description": "leaf-r3 as found: PFC on, ECN Kmin 1500 KB / Kmax 6000 KB / Pmax 0.2",
                           "pfc_enabled": True, "ecn_kmin_kb": 1500, "ecn_kmax_kb": 6000, "ecn_pmax": 0.2},
            "B_template": {"description": "fabric template: PFC on, ECN Kmin 150 KB / Kmax 1500 KB / Pmax 0.2",
                           "pfc_enabled": True, "ecn_kmin_kb": 150, "ecn_kmax_kb": 1500, "ecn_pmax": 0.2},
            "C_lossy": {"description": "lossy RoCE: PFC off, template ECN, dropped bytes re-offered after 20 us "
                                      "(best case: selective repeat, no go-back-N window, no tail-loss timeout)",
                        "pfc_enabled": False, "ecn_kmin_kb": 150, "ecn_kmax_kb": 1500, "ecn_pmax": 0.2},
        },
    }
    with open(out / "sim_configs.yaml", "w", newline="\n", encoding="utf-8") as f:
        yaml.safe_dump(sim, f, sort_keys=False)

    print(f"wrote {len(sw_rows)} switch rows, {len(nic_rows)} NIC rows, {len(pr_rows)} probe rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
