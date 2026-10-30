"""Capstone B reference implementation: ORION backend telemetry pipeline.

INSTRUCTOR EDITION. Same public API as starter-kit/starter/telemetry.py, fully implemented.

Pipeline: parse three native formats -> one normalized long table -> wrap/reset-aware rates ->
rule-based detection with persistence, peer comparison and maintenance suppression -> scoring.
All data is [SIMULATED]; see starter-kit/README.md for what the generator does not model.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# ----------------------------------------------------------------------------------------------
# Schema
# ----------------------------------------------------------------------------------------------

CANONICAL_COUNTERS = [
    "rx_bytes", "tx_bytes", "rx_discards", "tx_discards", "fcs_errors", "fec_corrected",
    "fec_uncorrectable", "pfc_rx_pause_p3", "pfc_tx_pause_p3", "ecn_marked_p3", "ecn_ce_received_p3", "cnp_sent",
    "cnp_handled", "out_of_sequence", "local_ack_timeout_err",
]
SCHEMA_COLUMNS = ["ts", "device", "interface", "counter", "native", "value", "source"]

LEAF_CLI_MAP = {
    "InOctets": "rx_bytes", "OutOctets": "tx_bytes", "InDiscards": "rx_discards",
    "OutDiscards": "tx_discards", "FCSErrors": "fcs_errors", "FECCorrected": "fec_corrected",
    "FECUncorr": "fec_uncorrectable", "RxPause3": "pfc_rx_pause_p3", "TxPause3": "pfc_tx_pause_p3",
    "EcnMarked3": "ecn_marked_p3",
}
SPINE_JSON_MAP = {
    "in-octets": "rx_bytes", "out-octets": "tx_bytes", "in-discards": "rx_discards",
    "out-discards": "tx_discards", "in-fcs-errors": "fcs_errors", "rx-pause-3": "pfc_rx_pause_p3",
    "tx-pause-3": "pfc_tx_pause_p3", "ecn-marked-3": "ecn_marked_p3",
}
NIC_ETHTOOL_MAP = {
    "rx_vport_rdma_unicast_bytes": "rx_bytes", "tx_vport_rdma_unicast_bytes": "tx_bytes",
    "rx_prio3_pause": "pfc_rx_pause_p3", "tx_prio3_pause": "pfc_tx_pause_p3",
    "rx_discards_phy": "rx_discards", "rx_crc_errors_phy": "fcs_errors", "np_cnp_sent": "cnp_sent",
    "rp_cnp_handled": "cnp_handled", "np_ecn_marked_roce_packets": "ecn_ce_received_p3",
    "out_of_sequence": "out_of_sequence", "local_ack_timeout_err": "local_ack_timeout_err",
}

DEFAULT_RULES: dict[str, dict[str, float]] = {
    "pfc_storm": {"rx_pause_per_s": 10_000.0, "persistence": 3},
    "link_degradation": {"fcs_per_s": 0.0, "fec_uncorrectable_per_s": 0.0, "persistence": 2},
    "fec_trend": {"ratio_to_own_baseline": 5.0, "baseline_intervals": 5, "persistence": 2},
    "ecn_misconfig": {"ecn_ratio_max": 0.01, "pfc_ratio_min": 3.0, "persistence": 3},
    "ecmp_imbalance": {"cv_threshold": 0.5, "min_mean_bytes_per_s": 1e8, "persistence": 3},
    "link_down": {"rx_floor_bytes_per_s": 1e6, "active_floor_bytes_per_s": 1e9, "persistence": 2},
}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


# ----------------------------------------------------------------------------------------------
# 1. Parsers
# ----------------------------------------------------------------------------------------------


def parse_leaf_cli(text: str) -> pd.DataFrame:
    """Parse leaf `show interfaces counters` text into the normalized long schema.

    Each snapshot: a prompt line ``<device># show interfaces counters``, a ``Timestamp: <ISO-8601 Z>``
    line, a header row of native column names, then one row per port. Returns SCHEMA_COLUMNS with
    ts as a tz-aware UTC pandas Timestamp, value as int, source 'leaf_cli'.
    """
    rows: list[tuple] = []
    device = ts = None
    header: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(\S+)# show interfaces counters", line)
        if m:
            device, header = m.group(1), []
            continue
        if line.startswith("Timestamp:"):
            ts = pd.Timestamp(line.split(":", 1)[1].strip())
            continue
        parts = line.split()
        if parts[0] == "Port":
            header = parts[1:]
            continue
        if device is None or ts is None or not header:
            raise ValueError(f"row before header/timestamp: {line[:40]}")
        port, vals = parts[0], parts[1:]
        if len(vals) != len(header):
            raise ValueError(f"column count mismatch on {device} {port}")
        for native, v in zip(header, vals):
            rows.append((ts, device, port, LEAF_CLI_MAP[native], native, int(v), "leaf_cli"))
    return pd.DataFrame(rows, columns=SCHEMA_COLUMNS)


def parse_spine_jsonl(text: str) -> pd.DataFrame:
    """Parse spine JSON-lines telemetry into the normalized schema.

    Each line: {"timestamp_ns": int, "device": str, "updates": [{"path": ".../interface[name=X]/...",
    "values": {native: int}}]}. Timestamps are integer nanoseconds since the Unix epoch (UTC).
    """
    rows: list[tuple] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        ts = pd.Timestamp(rec["timestamp_ns"], unit="ns", tz="UTC")
        for up in rec["updates"]:
            m = re.search(r"interface\[name=([^\]]+)\]", up["path"])
            if not m:
                continue
            for native, v in up["values"].items():
                if native in SPINE_JSON_MAP:
                    rows.append((ts, rec["device"], m.group(1), SPINE_JSON_MAP[native], native, int(v),
                                 "spine_stream"))
    return pd.DataFrame(rows, columns=SCHEMA_COLUMNS)


def parse_nic_ethtool(text: str) -> pd.DataFrame:
    """Parse host-agent NIC dumps (`ethtool -S` + RDMA hw_counters) into the normalized schema.

    Each block starts ``### collected_at=<epoch s> host=<h> dev=<mlx5_N> netdev=<if> rail=<r>``;
    counter lines are ``     name: value``. The device is the host; the interface is the RDMA device.
    Unknown counters are ignored.
    """
    rows: list[tuple] = []
    ts = host = dev = None
    for line in text.splitlines():
        if line.startswith("###"):
            kv = dict(tok.split("=", 1) for tok in line[3:].split())
            ts = pd.Timestamp(int(kv["collected_at"]), unit="s", tz="UTC")
            host, dev = kv["host"], kv["dev"]
            continue
        m = re.match(r"^\s+([A-Za-z0-9_]+):\s+(\d+)\s*$", line)
        if m and ts is not None and m.group(1) in NIC_ETHTOOL_MAP:
            rows.append((ts, host, dev, NIC_ETHTOOL_MAP[m.group(1)], m.group(1), int(m.group(2)),
                         "nic_ethtool"))
    return pd.DataFrame(rows, columns=SCHEMA_COLUMNS)


def load_all(data_dir: str | Path) -> pd.DataFrame:
    """Parse every file in the bundle and return one normalized DataFrame sorted by
    (device, interface, counter, ts)."""
    d = Path(data_dir)
    frames = [parse_leaf_cli(_read_text(p)) for p in sorted((d / "leaf_cli").glob("*.txt*"))]
    frames.append(parse_spine_jsonl(_read_text(d / "spine_stream.jsonl.gz")))
    frames += [parse_nic_ethtool(_read_text(p)) for p in sorted((d / "nic").glob("*.txt*"))]
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["device", "interface", "counter", "ts"], kind="mergesort").reset_index(drop=True)


def load_context(data_dir: str | Path) -> dict[str, Any]:
    """Load topology.csv, device_profiles.yaml and maintenance.yaml."""
    d = Path(data_dir)
    return {"topology": pd.read_csv(d / "topology.csv"),
            "profiles": yaml.safe_load((d / "device_profiles.yaml").read_text(encoding="utf-8")),
            "maintenance": yaml.safe_load((d / "maintenance.yaml").read_text(encoding="utf-8"))["windows"]}


# ----------------------------------------------------------------------------------------------
# 2. Counter arithmetic
# ----------------------------------------------------------------------------------------------


def counter_delta(prev: int, cur: int, width: int, max_delta: float | None = None) -> int | None:
    """Increment of a cumulative counter between two polls.

    * cur ≥ prev: cur − prev.
    * cur < prev on a 32-bit counter whose previous value was in the upper half of its range:
      a wrap, delta = cur + 2**32 − prev.
    * any other decrease: a reset (reboot, driver reload, `clear counters`): return None, because the
      true increment is unknown. Do not guess.
    * plausibility bound: a candidate wrap whose delta exceeds ``max_delta`` (max plausible rate × dt) is
      a clear, not a wrap. Without a discontinuity signal (device uptime, boot ID, or a counter-
      discontinuity timestamp) the heuristic alone can misread a clear as a wrap.
    """
    if cur >= prev:
        return cur - prev
    if width == 32 and prev >= 2**31:
        d = cur + 2**32 - prev
        if max_delta is None or d <= max_delta:
            return d
    return None


def compute_rates(df: pd.DataFrame, profiles: dict) -> pd.DataFrame:
    """Per-interval rates for every (device, interface, counter) series.

    Returns columns ts (end of interval), device, interface, counter, source, dt_s, delta, rate (units/s),
    valid (bool) and reason ('' | 'reset' | 'bad_dt'). Width comes from
    profiles['platforms'][source]['counter_width_bits'] keyed by native name, else 'default'.
    Invalid intervals have NaN rate.
    """
    widths = {src: p["counter_width_bits"] for src, p in profiles["platforms"].items()}
    maxr = {src: p.get("max_plausible_rate_per_s", {}) for src, p in profiles["platforms"].items()}
    df = df.sort_values(["device", "interface", "counter", "ts"], kind="mergesort").reset_index(drop=True)
    key = df["device"] + "\x00" + df["interface"] + "\x00" + df["counter"]
    same = key.eq(key.shift(1))
    prev = df["value"].shift(1)
    width = np.array([widths[s].get(n, widths[s]["default"]) for s, n in zip(df["source"], df["native"])])
    max_rate = np.array([maxr[s].get(n, np.inf) for s, n in zip(df["source"], df["native"])], dtype=float)
    cur = df["value"].astype("float64").to_numpy()
    pv = prev.astype("float64").to_numpy()
    delta = cur - pv
    neg = delta < 0
    dt = (df["ts"] - df["ts"].shift(1)).dt.total_seconds().to_numpy()
    wrap = neg & (width == 32) & (pv >= 2**31)
    finite = np.isfinite(max_rate)
    bound = np.where(finite, np.where(finite, max_rate, 0.0) * np.where(dt > 0, dt, 0.0), np.inf)
    wrap &= (delta + 2**32) <= bound                                  # plausibility bound
    delta = np.where(wrap, delta + 2**32, delta)
    reset = neg & ~wrap
    bad_dt = ~(dt > 0)
    valid = ~reset & ~bad_dt
    out = pd.DataFrame({
        "ts": df["ts"], "device": df["device"], "interface": df["interface"], "counter": df["counter"],
        "source": df["source"], "dt_s": dt, "delta": np.where(valid, delta, np.nan),
        "rate": np.where(valid, delta / np.where(dt > 0, dt, 1.0), np.nan), "valid": valid,
        "reason": np.where(reset, "reset", np.where(bad_dt, "bad_dt", "")),
    })
    return out[same.to_numpy()].reset_index(drop=True)


# ----------------------------------------------------------------------------------------------
# 3. Detection
# ----------------------------------------------------------------------------------------------


def in_maintenance(device: str, ts: pd.Timestamp, windows: list[dict]) -> bool:
    """True if ``device`` has a change window covering ``ts`` (start inclusive, end exclusive)."""
    for w in windows:
        if w["device"] == device and pd.Timestamp(w["start"]) <= ts < pd.Timestamp(w["end"]):
            return True
    return False


def _peer_map(topology: pd.DataFrame) -> dict[tuple[str, str], tuple[str, str, str]]:
    peers: dict[tuple[str, str], tuple[str, str, str]] = {}
    for r in topology.itertuples(index=False):
        peers[(r.a_device, r.a_interface)] = (r.b_device, r.b_interface, r.link_role)
        peers[(r.b_device, r.b_interface)] = (r.a_device, r.a_interface, r.link_role)
    return peers


def _runs(flags: pd.Series, need: int, clear_after: int = 3) -> list[tuple[int, int]]:
    """Index ranges [start, end] of alert episodes (a small state machine).

    * An episode OPENS only on ``need`` consecutive True intervals; ``start`` is the first of them, so the
      page fires at index start + need − 1 (always a True interval).
    * Once open, it stays open across gaps of fewer than ``clear_after`` consecutive False intervals
      (hysteresis), so one ongoing fault produces one page.
    * It CLOSES after ``clear_after`` consecutive False intervals; ``end`` is the last True interval.
    Isolated True intervals never open an episode, so two separated glitches do not page.
    """
    vals = flags.to_numpy().astype(bool)
    out: list[tuple[int, int]] = []
    run = gap = 0
    start = last = -1
    is_open = False
    for i, v in enumerate(vals):
        if not is_open:
            run = run + 1 if v else 0
            if run >= need:
                is_open, start, last, gap = True, i - need + 1, i, 0
        elif v:
            last, gap = i, 0
        else:
            gap += 1
            if gap >= clear_after:
                out.append((start, last))
                is_open, run = False, 0
    if is_open:
        out.append((start, last))
    return out


def detect(rates: pd.DataFrame, topology: pd.DataFrame, maintenance: list[dict],
           rules: dict | None = None, persistence: int | None = None) -> pd.DataFrame:
    """Run the alert rules. Returns one row per alert with columns device, interface, fault_class,
    role ('root' | 'symptom' | 'early_warning'), first_ts (first interval of the run), fired_ts (the interval
    at which persistence is satisfied, i.e. when the page goes out), last_ts, evidence.

    ``persistence`` overrides every rule's persistence (used for the false-positive analysis).
    Intervals inside a maintenance window of the device or of its link peer are masked out.
    """
    rules = rules or DEFAULT_RULES
    peers = _peer_map(topology)

    def need(rule: str) -> int:
        return int(persistence if persistence is not None else rules[rule]["persistence"])

    def masked(dev: str, intf: str, ts: pd.Series) -> np.ndarray:
        peer = peers.get((dev, intf))
        return np.array([in_maintenance(dev, t, maintenance) or
                         (peer is not None and in_maintenance(peer[0], t, maintenance)) for t in ts])

    wide = rates.pivot_table(index=["device", "interface", "ts"], columns="counter", values="rate",
                             aggfunc="first").reset_index()
    for c in CANONICAL_COUNTERS:          # tolerate sources that lack some counters
        if c not in wide.columns:
            wide[c] = np.nan
    alerts: list[dict] = []

    # --- per-port rules -------------------------------------------------------------------------
    for (dev, intf), g in wide.groupby(["device", "interface"], sort=True):
        g = g.sort_values("ts").reset_index(drop=True)
        mask = masked(dev, intf, g["ts"])
        peer = peers.get((dev, intf))
        # pfc_storm: a leaf host port receiving sustained pause -> the host NIC is the source
        if dev.startswith("orion-be-leaf") and peer is not None and peer[2] == "host" and "pfc_rx_pause_p3" in g:
            flag = (g["pfc_rx_pause_p3"] > rules["pfc_storm"]["rx_pause_per_s"]) & ~mask
            need_now = need("pfc_storm")
            for s, e in _runs(flag, need_now):
                peak = g["pfc_rx_pause_p3"].iloc[s:e + 1].max()
                ev = (f"{dev} {intf} pfc_rx_pause_p3 > {rules['pfc_storm']['rx_pause_per_s']:.0f}/s for "
                      f"{e - s + 1} intervals (peak {peak:,.0f}/s); source is peer {peer[0]} {peer[1]}")
                alerts.append({"device": peer[0], "interface": peer[1], "fault_class": "pfc_storm",
                               "role": "root", "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e], "evidence": ev})
                alerts.append({"device": dev, "interface": intf, "fault_class": "pfc_storm",
                               "role": "symptom", "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e], "evidence": ev})
        # link_degradation: errors counted on the receiving port
        rl = rules["link_degradation"]
        cond = pd.Series(False, index=g.index)
        if "fcs_errors" in g:
            cond |= g["fcs_errors"] > rl["fcs_per_s"]
        if "fec_uncorrectable" in g:
            cond |= g["fec_uncorrectable"] > rl["fec_uncorrectable_per_s"]
        flag = cond & ~mask
        if "fec_corrected" in g and g["fec_corrected"].notna().sum() > rules["fec_trend"]["baseline_intervals"]:
            rt = rules["fec_trend"]
            base = g["fec_corrected"].dropna().iloc[: int(rt["baseline_intervals"])].median()
            tflag = (g["fec_corrected"] > rt["ratio_to_own_baseline"] * base) & ~mask
            need_now = need("fec_trend")
            for s, e in _runs(tflag, need_now):
                alerts.append({"device": dev, "interface": intf, "fault_class": "link_degradation",
                               "role": "early_warning", "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e],
                               "evidence": f"{dev} {intf}: corrected codewords > {rt['ratio_to_own_baseline']:.0f}x own baseline "
                                           f"({base:,.0f}/s) and rising; check pre-FEC BER and symbol-error bins"})
        need_now = need("link_degradation")
        for s, e in _runs(flag, need_now):
            seg = g.iloc[s:e + 1]
            parts = [f"{c} max {seg[c].max():,.2f}/s" for c in ("fcs_errors", "fec_uncorrectable", "fec_corrected")
                     if c in seg and seg[c].notna().any()]
            ev = f"{dev} {intf}: " + ", ".join(parts) + f" over {e - s + 1} intervals"
            alerts.append({"device": dev, "interface": intf, "fault_class": "link_degradation", "role": "root",
                           "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e], "evidence": ev})
        # link_down: a busy switch port that stops receiving
        if not dev.startswith("orion-n") and "rx_bytes" in g:
            rd = rules["link_down"]
            hist = g["rx_bytes"].where(g["rx_bytes"].notna()).expanding().median().shift(1)
            flag = (g["rx_bytes"] < rd["rx_floor_bytes_per_s"]) & (hist > rd["active_floor_bytes_per_s"]) & ~mask
            need_now = need("link_down")
            for s, e in _runs(flag, need_now):
                alerts.append({"device": dev, "interface": intf, "fault_class": "link_down", "role": "root",
                               "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e],
                               "evidence": f"{dev} {intf} rx below {rd['rx_floor_bytes_per_s']:.0e} B/s for {e - s + 1} intervals"})

    # --- per-leaf rules (peer comparison across rails) ----------------------------------------------
    topo = topology
    host_ports = topo[topo["link_role"] == "host"][["a_device", "a_interface"]]
    up_ports = topo[topo["link_role"] == "fabric"][["a_device", "a_interface"]]
    hp = wide.merge(host_ports, left_on=["device", "interface"], right_on=["a_device", "a_interface"])
    hp["pfc"] = hp["pfc_rx_pause_p3"] + hp["pfc_tx_pause_p3"]
    hp["minute"] = hp["ts"].dt.floor("min")
    per_leaf = hp.groupby(["device", "minute"]).agg(ecn=("ecn_marked_p3", "sum"), pfc=("pfc", "sum"),
                                                    ts=("ts", "max")).reset_index()
    re_ = rules["ecn_misconfig"]
    for dev, g in per_leaf.groupby("device"):
        g = g.sort_values("minute").reset_index(drop=True)
        others = per_leaf[per_leaf["device"] != dev].groupby("minute")[["ecn", "pfc"]].median()
        o = others.reindex(g["minute"]).reset_index(drop=True)
        mask = np.array([in_maintenance(dev, t, maintenance) for t in g["ts"]])
        flag = ((g["ecn"] <= re_["ecn_ratio_max"] * o["ecn"]) & (g["pfc"] >= re_["pfc_ratio_min"] * o["pfc"])
                & ~mask)
        need_now = need("ecn_misconfig")
        for s, e in _runs(flag, need_now):
            alerts.append({"device": dev, "interface": "*", "fault_class": "ecn_misconfig", "role": "root",
                           "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e],
                           "evidence": (f"{dev}: ECN marks {g['ecn'][s]:.0f}/s vs peer median {o['ecn'][s]:.0f}/s; "
                                        f"PFC {g['pfc'][s]:.0f}/s vs peer median {o['pfc'][s]:.0f}/s")})
    up = wide.merge(up_ports, left_on=["device", "interface"], right_on=["a_device", "a_interface"])
    rc = rules["ecmp_imbalance"]
    stats = up.groupby(["device", "ts"])["tx_bytes"].agg(["mean", "std"]).reset_index()
    stats["cv"] = stats["std"] / stats["mean"]
    for dev, g in stats.groupby("device"):
        g = g.sort_values("ts").reset_index(drop=True)
        mask = np.array([in_maintenance(dev, t, maintenance) for t in g["ts"]])
        flag = (g["cv"] > rc["cv_threshold"]) & (g["mean"] > rc["min_mean_bytes_per_s"]) & ~mask
        need_now = need("ecmp_imbalance")
        for s, e in _runs(flag, need_now):
            alerts.append({"device": dev, "interface": "*", "fault_class": "ecmp_imbalance", "role": "root",
                           "first_ts": g["ts"][s], "fired_ts": g["ts"][s + need_now - 1], "last_ts": g["ts"][e],
                           "evidence": f"{dev}: uplink tx CV {g['cv'][s]:.2f} (> {rc['cv_threshold']}) for {e - s + 1} intervals"})
    cols = ["device", "interface", "fault_class", "role", "first_ts", "fired_ts", "last_ts", "evidence"]
    return pd.DataFrame(alerts, columns=cols)


# ----------------------------------------------------------------------------------------------
# 4. Reporting and scoring
# ----------------------------------------------------------------------------------------------


def leaf_health_table(rates: pd.DataFrame, topology: pd.DataFrame) -> pd.DataFrame:
    """One row per leaf for the report/dashboard: host_rx_gbps (mean per host port, Gb/s),
    pfc_per_s (mean rx+tx pause per host port), ecn_per_s (mean marks per host port),
    fcs_errors (sum of increments over the capture, all ports), uplink_cv (median over intervals)."""
    leaves = rates[rates["device"].str.startswith("orion-be-leaf")]
    host = topology[topology["link_role"] == "host"][["a_device", "a_interface"]]
    upl = topology[topology["link_role"] == "fabric"][["a_device", "a_interface"]]
    h = leaves.merge(host, left_on=["device", "interface"], right_on=["a_device", "a_interface"])
    u = leaves.merge(upl, left_on=["device", "interface"], right_on=["a_device", "a_interface"])
    rows = []
    for dev in sorted(leaves["device"].unique()):
        hd = h[h["device"] == dev]
        ud = u[(u["device"] == dev) & (u["counter"] == "tx_bytes")]
        cv = ud.groupby("ts")["rate"].agg(lambda s: s.std() / s.mean() if s.mean() > 0 else np.nan).median()
        rows.append({
            "device": dev,
            "host_rx_gbps": hd.loc[hd["counter"] == "rx_bytes", "rate"].mean() * 8 / 1e9,
            "pfc_per_s": (hd.loc[hd["counter"] == "pfc_rx_pause_p3", "rate"].mean()
                          + hd.loc[hd["counter"] == "pfc_tx_pause_p3", "rate"].mean()),
            "ecn_per_s": hd.loc[hd["counter"] == "ecn_marked_p3", "rate"].mean(),
            "fcs_errors": float(leaves.loc[(leaves["device"] == dev) & (leaves["counter"] == "fcs_errors"), "delta"].sum()),
            "uplink_cv": float(cv),
        })
    return pd.DataFrame(rows)


def truth_key(device: str, interface: str, fault_class: str) -> str:
    """SHA-256 hex digest of '<device>:<interface>|<fault_class>' (interface '*' for device-level)."""
    return hashlib.sha256(f"{device}:{interface}|{fault_class}".encode()).hexdigest()


def score(alerts: pd.DataFrame, truth: list[dict]) -> dict[str, object]:
    """Time-aware precision/recall of ROOT alerts against hashed ground truth.

    ``truth`` is a list of {"hash", "onset" (tz-aware Timestamp), "tolerance_s"}. Each root alert row is
    one page. A page is a true positive if its key hash matches a fault AND it fires (``fired_ts``) within
    [onset, onset + tolerance] AND that fault has not already been matched. Repeat pages for a fault that was
    already matched are duplicates (neither TP nor FP; report them as on-call noise). Every other page — wrong key, fired
    before onset, or after the window — is a false positive. Returns tp, fp, fn, duplicates, precision,
    recall, f1 and latency_s (dict hash -> seconds from onset to the matching page).
    """
    by_hash = {t["hash"]: t for t in truth}
    roots = alerts[alerts["role"] == "root"].sort_values("fired_ts")
    matched: dict[str, float] = {}
    fp = dup = 0
    for r in roots.itertuples(index=False):
        h = truth_key(r.device, r.interface, r.fault_class)
        t = by_hash.get(h)
        fired = pd.Timestamp(r.fired_ts)
        in_window = t is not None and t["onset"] <= fired <= t["onset"] + pd.Timedelta(seconds=t["tolerance_s"])
        if in_window and h not in matched:
            matched[h] = (fired - t["onset"]).total_seconds()
        elif t is not None and h in matched and fired > t["onset"]:
            dup += 1        # re-page of a fault already detected: noise, but not a false positive
        else:
            fp += 1
    tp, fn = len(matched), len(truth) - len(matched)
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not truth else 0.0)
    recall = tp / len(truth) if truth else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "duplicates": dup, "precision": precision, "recall": recall,
            "f1": f1, "latency_s": matched}


def load_truth(data_dir: str | Path) -> list[dict]:
    """Read ground_truth.sha256: '<hash> <onset ISO> <tolerance_s>' per line ('#' lines are comments)."""
    out = []
    for ln in (Path(data_dir) / "ground_truth.sha256").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            h, onset, tol = ln.split()
            out.append({"hash": h, "onset": pd.Timestamp(onset), "tolerance_s": float(tol)})
    return out
