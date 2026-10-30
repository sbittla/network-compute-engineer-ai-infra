#!/usr/bin/env python3
"""Generate the Chapter 10 link-health dataset for ORION rail-3 backend leaf.

Produces (deterministically, seed 10):
  data/snapshot_t0.csv       per-port counters + DOM at T0
  data/snapshot_t1.csv       per-port counters + DOM at T1 = T0 + 600 s
  data/cabling_schedule.csv  intended cabling (source of truth for neighbours and optics)
  data/thresholds.yaml       ILLUSTRATIVE fleet thresholds used by the analyzer
  data/fabrics.yaml          fabric specs for the port/cable/spares estimation task

All values are [SIMULATED]/[ILLUSTRATIVE]; they are modeled on ORION (docs/REFERENCE_CLUSTER.md)
and on the counter semantics described in Chapter 10. Regenerating must be byte-identical.

Usage:
    python tools/generate_data.py [--out DIR]
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import random
from pathlib import Path

SEED = 10
DT_S = 600
UPTIME_S = 2_592_000  # 30 days of counter accumulation before T0
LINE_RATE_BPS = 425e9  # 400GBASE-R after 256b/257b transcoding and RS(544,514) FEC
LEAF = "orion-be-leaf-r3"
RAIL = 3
T0 = "2026-10-12T09:00:00+00:00"
T1 = "2026-10-12T09:10:00+00:00"
FIXED_LENGTHS_M = {14: 43, 21: 38, 40: 12}  # lengths quoted in the manuscript (Sections 10.6, 10.10)

COLUMNS = [
    "ts", "port", "admin_status", "oper_status", "mtu", "speed_gbps", "optic_type", "optic_serial",
    "lldp_neighbor", "link_down_events", "rx_frames", "tx_frames", "rx_fcs_errors",
    "rx_oversize_frames", "out_discards", "ecn_marked_pkts", "pfc_rx_pause", "pfc_tx_pause",
    "fec_corrected_cw", "fec_uncorrectable_cw", "pre_fec_ber", "module_temp_c",
    "tx_bias_ma_l0", "tx_bias_ma_l1", "tx_bias_ma_l2", "tx_bias_ma_l3",
    "tx_power_dbm_l0", "tx_power_dbm_l1", "tx_power_dbm_l2", "tx_power_dbm_l3",
    "rx_power_dbm_l0", "rx_power_dbm_l1", "rx_power_dbm_l2", "rx_power_dbm_l3",
]

THRESHOLDS_YAML = """\
# ILLUSTRATIVE fleet thresholds for the Chapter 10 lab. Not a vendor specification.
# rx_power_low_warn/crit are OPERATIONAL POLICY: warn with ~2 dB left above the receiver minimum,
# critical at the receiver minimum (400GBASE-DR4: -5.9 dBm average per lane, IEEE 802.3bs; verify).
# module_rx_low_warn/alarm are what a typical module programs in its CMIS memory map; they sit BELOW
# the receiver minimum, so they are informational only and must not drive alerting.
interval_expected_s: 600
optics:
  400G-DR4:
    lanes: 4
    media: "SMF, parallel, MPO-12, 1310 nm, 500 m"
    rx_power_low_warn_dbm: -4.0
    rx_power_low_crit_dbm: -5.9
    module_rx_low_warn_dbm: -6.0
    module_rx_low_alarm_dbm: -9.0
    rx_power_high_warn_dbm: 4.0
    temp_high_warn_c: 70.0
  400G-FR4:
    lanes: 4
    media: "SMF, duplex LC, CWDM4 1271-1331 nm, 2 km"
    rx_power_low_warn_dbm: -5.0
    rx_power_low_crit_dbm: -7.0
    rx_power_high_warn_dbm: 3.5
    temp_high_warn_c: 70.0
  400G-SR8:
    lanes: 8
    media: "MMF OM4, MPO-16, 850 nm, 100 m"
    rx_power_low_warn_dbm: -6.5
    rx_power_low_crit_dbm: -8.5
    rx_power_high_warn_dbm: 4.0
    temp_high_warn_c: 70.0
fec:
  code: "RS(544,514) KP4"
  pre_fec_ber_threshold: 2.4e-4
  pre_fec_ber_warn: 1.0e-5
  pre_fec_ber_crit: 1.0e-4
  pre_fec_ber_rising_factor: 10.0
  pre_fec_ber_rising_floor: 1.0e-6
link:
  flap_events_warn: 2
  lane_imbalance_db: 3.0
higher_layer:
  pfc_pause_rate_warn_per_s: 100.0
"""

FABRICS_YAML = """\
# Fabric specs for the port / cable / spares estimation task. [ILLUSTRATIVE]
# One NIC port per GPU, one rail per NIC index, rail-optimized leaves, 2-tier leaf-spine.
fabrics:
  small:
    nodes: 16
    rails: 8
    switch_radix: 64
    oversubscription: 1.0
    host_optic: 400G-DR4
    fabric_optic: 400G-DR4
    prefix: lab
  orion:
    nodes: 32
    rails: 8
    switch_radix: 64
    oversubscription: 1.0
    host_optic: 400G-DR4
    fabric_optic: 400G-DR4
    prefix: orion-be
spares_policy:
  optic_rate: 0.03
  cable_rate: 0.02
  min_per_type: 2
  spare_switches_per_model: 1
"""


def expected_neighbor(port_num: int) -> tuple[str, str, str]:
    """Return (device, port, cable_id) intended for leaf port ``port_num`` (1-based)."""
    if port_num <= 32:  # canonical: orion-nNN (01-32) lands on leaf port EthernetNN
        return f"orion-n{port_num:02d}", f"nic{RAIL}", f"BE-R{RAIL}-H-{port_num:02d}"
    k = port_num - 33
    spine = k // 8 + 1
    spine_port = RAIL * 8 + (k % 8) + 1
    return f"orion-be-spine-{spine}", f"Ethernet{spine_port}", f"BE-R{RAIL}-S{spine}-{k % 8 + 1}"


def fmt(v: float, nd: int = 2) -> str:
    return f"{v:.{nd}f}"


def fmt_ber(v: float | None) -> str:
    return "" if v is None else f"{v:.3e}"


def build() -> dict[str, str]:
    rng = random.Random(SEED)
    rows0: list[dict] = []
    rows1: list[dict] = []
    sched: list[dict] = []

    for p in range(1, 65):
        port = f"Ethernet{p}"
        dev, dport, cable = expected_neighbor(p)
        host_link = p <= 32
        length = rng.randint(28, 46) if host_link else rng.randint(8, 16)
        length = FIXED_LENGTHS_M.get(p, length)
        sched.append({
            "cable_id": cable, "a_device": LEAF, "a_port": port, "b_device": dev, "b_port": dport,
            "expected_optic_a": "400G-DR4", "expected_optic_b": "400G-DR4",
            "media": "SMF MPO-12 (8f used)", "length_m": length,
            "label_a": f"{cable} | {LEAF}:{port} -> {dev}:{dport}",
            "label_b": f"{cable} | {dev}:{dport} -> {LEAF}:{port}",
        })

        # ---- healthy baseline -------------------------------------------------------------
        rx_fps = rng.uniform(2.0e6, 6.0e6)
        tx_fps = rng.uniform(2.0e6, 6.0e6)
        ber0 = 10 ** rng.uniform(-9.0, math.log10(3e-7))
        ber1 = ber0 * rng.uniform(0.8, 1.3)
        ecn_rate = rng.uniform(0.0, 50.0)
        pfc_rx_rate = rng.uniform(0.0, 30.0)
        pfc_tx_rate = rng.uniform(0.0, 30.0)
        temp = rng.uniform(38.0, 56.0)
        bias = [rng.uniform(6.0, 9.0) for _ in range(4)]
        txp = [rng.uniform(-1.0, 1.5) for _ in range(4)]
        rx_base = rng.uniform(-2.5, 0.0)
        rxp = [rx_base + rng.uniform(-0.6, 0.6) for _ in range(4)]
        events0 = rng.randint(0, 2)
        serial = f"OPX{rng.randint(10_000_000, 99_999_999)}"
        jit = [rng.uniform(-0.08, 0.08) for _ in range(13)]

        s0 = {
            "admin_status": "up", "oper_status": "up", "mtu": 9216, "speed_gbps": 400,
            "optic_type": "400G-DR4", "optic_serial": serial, "lldp_neighbor": f"{dev}:{dport}",
            "link_down_events": events0,
            "rx_frames": int(rx_fps * UPTIME_S), "tx_frames": int(tx_fps * UPTIME_S),
            "rx_fcs_errors": 0, "rx_oversize_frames": 0, "out_discards": 0,
            "ecn_marked_pkts": int(ecn_rate * UPTIME_S),
            "pfc_rx_pause": int(pfc_rx_rate * UPTIME_S), "pfc_tx_pause": int(pfc_tx_rate * UPTIME_S),
            "fec_corrected_cw": int(ber0 * LINE_RATE_BPS * UPTIME_S), "fec_uncorrectable_cw": 0,
            "pre_fec_ber": ber0, "module_temp_c": temp, "tx_bias": bias, "tx_power": txp, "rx_power": rxp,
        }
        d = {  # deltas over the 600 s window
            "link_down_events": 0, "rx_frames": int(rx_fps * DT_S), "tx_frames": int(tx_fps * DT_S),
            "rx_fcs_errors": 0, "rx_oversize_frames": 0, "out_discards": 0,
            "ecn_marked_pkts": int(ecn_rate * DT_S), "pfc_rx_pause": int(pfc_rx_rate * DT_S),
            "pfc_tx_pause": int(pfc_tx_rate * DT_S),
            "fec_corrected_cw": int((ber0 + ber1) / 2 * LINE_RATE_BPS * DT_S), "fec_uncorrectable_cw": 0,
        }
        s1_over: dict = {
            "pre_fec_ber": ber1, "module_temp_c": temp + jit[0],
            "tx_bias": [b + j for b, j in zip(bias, jit[1:5])],
            "tx_power": [t + j for t, j in zip(txp, jit[5:9])],
            "rx_power": [r + j for r, j in zip(rxp, jit[9:13])],
        }
        reset_at_t1 = False

        # ---- planted conditions (documented only in solutions/) ---------------------------
        if p == 2:  # counters cleared 240 s before T1 (decoy: healthy)
            s0["link_down_events"] = 1
            reset_at_t1 = True
        elif p == 7:  # dirty MPO end-face: one lane low
            s0["rx_power"] = [-1.5, -1.6, -7.6, -1.3]
            s1_over["rx_power"] = [-1.4, -1.7, -7.8, -1.2]
            s0["pre_fec_ber"], s1_over["pre_fec_ber"] = 2.4e-6, 2.6e-6
            s0["fec_corrected_cw"] = int(2.0e-6 * LINE_RATE_BPS * UPTIME_S)
            d["fec_corrected_cw"] = int(2.5e-6 * LINE_RATE_BPS * DT_S)
        elif p == 12:  # congestion: looks bad, but not physical
            s0["out_discards"] = 1200
            d["out_discards"] = 18342
            d["ecn_marked_pkts"] = 16000 * DT_S
            d["pfc_tx_pause"] = 3500 * DT_S
            d["pfc_rx_pause"] = 200 * DT_S
        elif p == 18:  # decoy: busy, many corrected codewords, but within policy
            s0["pre_fec_ber"], s1_over["pre_fec_ber"] = 5.0e-7, 6.5e-7
            s0["fec_corrected_cw"] = int(4.0e-7 * LINE_RATE_BPS * UPTIME_S)
            d["fec_corrected_cw"] = int(5.75e-7 * LINE_RATE_BPS * DT_S)
            d["ecn_marked_pkts"] = 400 * DT_S
            d["pfc_tx_pause"] = 60 * DT_S
        elif p == 21:  # pre-FEC BER rising toward the KP4 limit
            s0["pre_fec_ber"], s1_over["pre_fec_ber"] = 4.0e-6, 1.6e-4
            s0["rx_power"] = [-3.2, -3.5, -3.3, -3.4]
            s1_over["rx_power"] = [-3.3, -3.6, -3.4, -3.5]
            s0["fec_corrected_cw"] = int(3.0e-6 * LINE_RATE_BPS * UPTIME_S)
            d["fec_corrected_cw"] = int(8.2e-5 * LINE_RATE_BPS * DT_S)
        elif p == 27:  # port MTU left at 1500: giants from 9000-byte host frames
            s0["mtu"] = 1500
            s0["rx_oversize_frames"] = 0
            d["rx_oversize_frames"] = 45210
        elif p in (35, 36):  # two jumpers swapped at the patch panel
            other = 36 if p == 35 else 35
            odev, oport, _ = expected_neighbor(other)
            s0["lldp_neighbor"] = f"{odev}:{oport}"
        elif p == 40:  # damaged/defective cable: bursty errors, uncorrectables, CRC
            s0["pre_fec_ber"], s1_over["pre_fec_ber"] = 3.1e-5, 3.4e-5
            s0["fec_corrected_cw"] = int(2.9e-5 * LINE_RATE_BPS * UPTIME_S)
            d["fec_corrected_cw"] = int(3.25e-5 * LINE_RATE_BPS * DT_S)
            s0["fec_uncorrectable_cw"] = 52_310
            d["fec_uncorrectable_cw"] = 1180
            s0["rx_fcs_errors"] = 49_874
            d["rx_fcs_errors"] = 1104
        elif p == 45:  # wrong optic type installed: link never came up
            s0["optic_type"] = "400G-SR8"
            s0["oper_status"] = "down"
            s0["lldp_neighbor"] = ""
            for key in ("rx_frames", "tx_frames", "ecn_marked_pkts", "pfc_rx_pause", "pfc_tx_pause",
                        "fec_corrected_cw"):
                s0[key] = 0
                d[key] = 0
            s0["pre_fec_ber"], s1_over["pre_fec_ber"] = None, None
            s0["rx_power"] = [-40.0] * 4
            s1_over["rx_power"] = [-40.0] * 4
        elif p == 50:  # flapping link
            s0["link_down_events"] = 3
            d["link_down_events"] = 6
            d["fec_uncorrectable_cw"] = 40
            d["rx_fcs_errors"] = 31

        s1 = dict(s0)
        s1.update(s1_over)
        for k, v in d.items():
            s1[k] = s0[k] + v
        if reset_at_t1:
            frac = 240 / DT_S
            for k in d:
                s1[k] = int(d[k] * frac)

        rows0.append(to_row(T0, port, s0))
        rows1.append(to_row(T1, port, s1))

    return {
        "snapshot_t0.csv": to_csv(rows0, COLUMNS),
        "snapshot_t1.csv": to_csv(rows1, COLUMNS),
        "cabling_schedule.csv": to_csv(sched, list(sched[0].keys())),
        "thresholds.yaml": THRESHOLDS_YAML,
        "fabrics.yaml": FABRICS_YAML,
    }


def to_row(ts: str, port: str, s: dict) -> dict:
    row = {"ts": ts, "port": port}
    for k in ("admin_status", "oper_status", "mtu", "speed_gbps", "optic_type", "optic_serial",
              "lldp_neighbor", "link_down_events", "rx_frames", "tx_frames", "rx_fcs_errors",
              "rx_oversize_frames", "out_discards", "ecn_marked_pkts", "pfc_rx_pause", "pfc_tx_pause",
              "fec_corrected_cw", "fec_uncorrectable_cw"):
        row[k] = s[k]
    row["pre_fec_ber"] = fmt_ber(s["pre_fec_ber"])
    row["module_temp_c"] = fmt(s["module_temp_c"], 1)
    for i in range(4):
        row[f"tx_bias_ma_l{i}"] = fmt(s["tx_bias"][i])
        row[f"tx_power_dbm_l{i}"] = fmt(s["tx_power"][i])
        row[f"rx_power_dbm_l{i}"] = fmt(s["rx_power"][i])
    return row


def to_csv(rows: list[dict], cols: list[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def write_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, text in build().items():
        (out / name).write_bytes(text.encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    write_all(args.out)
    print(f"wrote dataset to {args.out}")


if __name__ == "__main__":
    main()
