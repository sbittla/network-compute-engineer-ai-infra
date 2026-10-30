"""Capstone B starter: ORION backend telemetry and troubleshooting pipeline.

Pipeline you will build:
    native dumps (3 formats) -> normalized long table -> wrap/reset-aware rates
    -> alert rules (thresholds, persistence, peer comparison, maintenance suppression)
    -> root-cause alerts -> precision/recall against hashed ground truth -> report table

Run ``python check.py`` from starter-kit/ after each step. Functions that still raise
NotImplementedError are reported as TODO. All data in data/ is [SIMULATED].
"""
from __future__ import annotations

import gzip
import hashlib
import json  # noqa: F401  (you will need it)
import re  # noqa: F401  (you will need it)
from pathlib import Path
from typing import Any

import numpy as np  # noqa: F401
import pandas as pd
import yaml

# ----------------------------------------------------------------------------------------------
# Schema (provided). Document it in templates/telemetry-schema.md.
# ----------------------------------------------------------------------------------------------

CANONICAL_COUNTERS = [
    "rx_bytes", "tx_bytes", "rx_discards", "tx_discards", "fcs_errors", "fec_corrected",
    "fec_uncorrectable", "pfc_rx_pause_p3", "pfc_tx_pause_p3", "ecn_marked_p3", "ecn_ce_received_p3", "cnp_sent",
    "cnp_handled", "out_of_sequence", "local_ack_timeout_err",
]
# One row per sample: ts (tz-aware UTC pandas Timestamp), device, interface, counter (canonical name),
# native (the name in the source format), value (int, cumulative), source ('leaf_cli' |
# 'spine_stream' | 'nic_ethtool' — these match the platform keys in device_profiles.yaml).
SCHEMA_COLUMNS = ["ts", "device", "interface", "counter", "native", "value", "source"]

# TODO: fill these native-name -> canonical-name maps. Read the sample of each format in
# starter-kit/README.md §4 and the files in data/. Every native counter in the bundle maps to exactly
# one canonical name; NIC counters not listed in the bundle should be ignored by the parser.
# Direction matters: a switch's ECN counter counts packets it MARKED on egress (ecn_marked_p3); the NIC's
# np_ecn_marked_roce_packets counts CE-marked packets it RECEIVED as notification point (ecn_ce_received_p3).
LEAF_CLI_MAP: dict[str, str] = {}
SPINE_JSON_MAP: dict[str, str] = {}
NIC_ETHTOOL_MAP: dict[str, str] = {}

# Alert-rule parameters (provided starting point; tune them and justify every value in
# templates/alert-rules.md). Rates are per second.
DEFAULT_RULES: dict[str, dict[str, float]] = {
    "pfc_storm": {"rx_pause_per_s": 10_000.0, "persistence": 3},
    # Page on FCS / uncorrectable codewords. Healthy 400G PAM4 links correct ~1e5 codewords/s, so an absolute
    # corrected-codeword threshold pages on healthy links (docs/VERIFIED_FACTS.md); use the corrected-codeword
    # TREND against each port's own baseline as an early warning (role 'early_warning', not paged/scored).
    "link_degradation": {"fcs_per_s": 0.0, "fec_uncorrectable_per_s": 0.0, "persistence": 2},
    "fec_trend": {"ratio_to_own_baseline": 5.0, "baseline_intervals": 5, "persistence": 2},
    "ecn_misconfig": {"ecn_ratio_max": 0.01, "pfc_ratio_min": 3.0, "persistence": 3},
    "ecmp_imbalance": {"cv_threshold": 0.5, "min_mean_bytes_per_s": 1e8, "persistence": 3},
    "link_down": {"rx_floor_bytes_per_s": 1e6, "active_floor_bytes_per_s": 1e9, "persistence": 2},
}


def _read_text(path: Path) -> str:
    """Read a text file that may be gzip-compressed (provided)."""
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


# ----------------------------------------------------------------------------------------------
# 1. Parsers
# ----------------------------------------------------------------------------------------------


def parse_leaf_cli(text: str) -> pd.DataFrame:
    """Parse leaf ``show interfaces counters`` text into SCHEMA_COLUMNS (source 'leaf_cli').

    Format: repeated snapshots, each = prompt line ``<device># show interfaces counters``,
    ``Timestamp: <ISO-8601, UTC 'Z'>``, a header row starting with ``Port`` followed by native
    column names, then one whitespace-separated row per port. Blank lines separate snapshots.

    TODO:
      * Track the current device, timestamp and header as you scan lines.
      * Emit one row per (port, native column) with counter = LEAF_CLI_MAP[native], value = int.
      * Raise ValueError on a data row whose column count differs from the header (do not guess).
    """
    raise NotImplementedError("parse_leaf_cli: parse CLI text snapshots into the long schema")


def parse_spine_jsonl(text: str) -> pd.DataFrame:
    """Parse spine streaming-telemetry JSON lines into SCHEMA_COLUMNS (source 'spine_stream').

    Each line: {"timestamp_ns": int, "device": str, "updates": [{"path": str, "values": {native: int}}]}.
    The interface name is inside the path: ``.../interface[name=Ethernet1/7]/...``.

    TODO: decode timestamp_ns as nanoseconds since the Unix epoch in UTC; map native names with
    SPINE_JSON_MAP; ignore values whose native name is not in the map.
    """
    raise NotImplementedError("parse_spine_jsonl: decode ns timestamps and interface paths")


def parse_nic_ethtool(text: str) -> pd.DataFrame:
    """Parse host-agent NIC dumps into SCHEMA_COLUMNS (source 'nic_ethtool').

    Each block starts ``### collected_at=<epoch seconds> host=<h> dev=<mlx5_N> netdev=<if> rail=<r>``
    followed by ``NIC statistics:`` (``ethtool -S`` output) and the RDMA hw_counters section; counter
    lines look like ``     name: value``.

    TODO: device = host, interface = the RDMA device (mlx5_N); keep only names in NIC_ETHTOOL_MAP.
    """
    raise NotImplementedError("parse_nic_ethtool: parse ethtool -S and hw_counters blocks")


def load_all(data_dir: str | Path) -> pd.DataFrame:
    """Parse every file in the bundle; return one DataFrame sorted by device, interface, counter, ts
    (provided glue — it works once your parsers do)."""
    d = Path(data_dir)
    frames = [parse_leaf_cli(_read_text(p)) for p in sorted((d / "leaf_cli").glob("*.txt*"))]
    frames.append(parse_spine_jsonl(_read_text(d / "spine_stream.jsonl.gz")))
    frames += [parse_nic_ethtool(_read_text(p)) for p in sorted((d / "nic").glob("*.txt*"))]
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["device", "interface", "counter", "ts"], kind="mergesort").reset_index(drop=True)


def load_context(data_dir: str | Path) -> dict[str, Any]:
    """Load topology.csv, device_profiles.yaml and maintenance.yaml (provided)."""
    d = Path(data_dir)
    return {"topology": pd.read_csv(d / "topology.csv"),
            "profiles": yaml.safe_load((d / "device_profiles.yaml").read_text(encoding="utf-8")),
            "maintenance": yaml.safe_load((d / "maintenance.yaml").read_text(encoding="utf-8"))["windows"]}


# ----------------------------------------------------------------------------------------------
# 2. Counter arithmetic
# ----------------------------------------------------------------------------------------------


def counter_delta(prev: int, cur: int, width: int, max_delta: float | None = None) -> int | None:
    """Increment of a cumulative counter between two polls.

    TODO:
      * cur >= prev -> cur - prev.
      * cur < prev on a 32-bit counter whose previous value was in the upper half of the range
        (prev >= 2**31) -> wrap: cur + 2**32 - prev.
      * any other decrease -> reset (reboot, driver reload, ``clear counters``): return None.
        The true increment is unknown; never substitute cur or 0.
      * plausibility bound: if the wrap delta exceeds ``max_delta`` (max plausible rate × dt, from
        device_profiles.yaml ``max_plausible_rate_per_s``), it was a clear, not a wrap -> None. In production
        prefer a discontinuity signal (device uptime, boot ID, counter-discontinuity time) over heuristics.
    """
    raise NotImplementedError("counter_delta: distinguish increment, 32-bit wrap and reset")


def compute_rates(df: pd.DataFrame, profiles: dict) -> pd.DataFrame:
    """Per-interval rates for every (device, interface, counter) series.

    Returns columns: ts (end of interval), device, interface, counter, source, dt_s, delta,
    rate (units per second), valid (bool), reason ('' | 'reset' | 'bad_dt'). The first sample of each
    series produces no row. Invalid intervals have NaN rate and delta.

    TODO:
      * Width: profiles['platforms'][source]['counter_width_bits'].get(native, ...['default']).
      * Plausibility: profiles['platforms'][source].get('max_plausible_rate_per_s', {}).get(native) × dt
        bounds a 32-bit wrap (see counter_delta).
      * Use the actual timestamps for dt (polls are jittered, and NICs poll every ~120 s).
      * Apply counter_delta semantics (vectorize for speed: ~267k samples).
    """
    raise NotImplementedError("compute_rates: wrap/reset-aware deltas divided by real dt")


# ----------------------------------------------------------------------------------------------
# 3. Detection
# ----------------------------------------------------------------------------------------------


def in_maintenance(device: str, ts: pd.Timestamp, windows: list[dict]) -> bool:
    """True if ``device`` has a change window with start <= ts < end (ISO strings in the windows)."""
    raise NotImplementedError("in_maintenance: start-inclusive, end-exclusive per-device windows")


def detect(rates: pd.DataFrame, topology: pd.DataFrame, maintenance: list[dict],
           rules: dict | None = None, persistence: int | None = None) -> pd.DataFrame:
    """Run the alert rules; return columns device, interface, fault_class, role ('root' | 'symptom' |
    'early_warning'), first_ts (first interval of the episode), fired_ts (the interval at which persistence
    is satisfied — when the page goes out; scoring uses this), last_ts, evidence (one sentence with numbers).

    Fault classes: pfc_storm, link_degradation, ecn_misconfig, ecmp_imbalance, link_down.
    Root-cause granularity (what the scorer compares):
      * pfc_storm        -> the device/interface that is *sending* the pause (find it via topology.csv)
      * link_degradation -> the device/interface whose receive side counts the errors
      * ecn_misconfig, ecmp_imbalance -> the leaf, with interface '*'
      * link_down        -> the switch port that stopped receiving

    ``persistence`` (if given) overrides every rule's persistence; check.py uses persistence=1 to
    show what happens without it.

    TODO (suggested approach — see starter-kit/README.md §6):
      1. Pivot rates to one row per (device, interface, ts) with a column per canonical counter.
      2. Per port: evaluate each per-interval condition; mask intervals inside a maintenance window of
         the device OR of its link peer; alert on runs of >= persistence consecutive True intervals.
      3. Per leaf: compare host-port ECN and PFC sums with the median of the other leaves at the same
         minute (peer comparison); compute the coefficient of variation of uplink tx_bytes.
      4. Episodes: OPEN an episode only on `persistence` consecutive True intervals (fired_ts = the
         last of those, never a False interval). Once open, bridge gaps of fewer than 3 consecutive
         False intervals (hysteresis), and CLOSE after 3 consecutive False intervals. Never fill gaps
         before checking persistence: two isolated glitches must not page.
      5. Emit symptom / early_warning alerts if you like; only role == 'root' is scored.
    """
    raise NotImplementedError("detect: rules with persistence, peer comparison and suppression")


# ----------------------------------------------------------------------------------------------
# 4. Reporting and scoring
# ----------------------------------------------------------------------------------------------


def leaf_health_table(rates: pd.DataFrame, topology: pd.DataFrame) -> pd.DataFrame:
    """One row per leaf for the report/dashboard.

    Columns: device, host_rx_gbps (mean rx rate per host-facing port, in Gb/s — bits!),
    pfc_per_s (mean rx+tx pause per host port), ecn_per_s (mean marks per host port),
    fcs_errors (sum of valid increments over the capture, all ports), uplink_cv (median over intervals
    of std/mean of uplink tx_bytes rates).
    """
    raise NotImplementedError("leaf_health_table: per-leaf summary for the report")


def truth_key(device: str, interface: str, fault_class: str) -> str:
    """SHA-256 hex digest of '<device>:<interface>|<fault_class>' (provided)."""
    return hashlib.sha256(f"{device}:{interface}|{fault_class}".encode()).hexdigest()


def score(alerts: pd.DataFrame, truth: list[dict]) -> dict[str, object]:
    """Time-aware precision/recall of ROOT pages against hashed ground truth (see load_truth).

    TODO: process root alerts in fired_ts order. A page is a TP if truth_key(...) matches a fault, it FIRES
    within [onset, onset + tolerance_s], and that fault is not yet matched. A later page for an already
    matched fault is a duplicate (count it separately). Everything else (wrong key, fired before onset,
    after the window) is a false positive. Return tp, fp, fn, duplicates, precision, recall, f1 and
    latency_s (dict hash -> seconds from onset to the matching page).
    """
    raise NotImplementedError("score: time-aware matching of pages to fault windows")


def load_truth(data_dir: str | Path) -> list[dict]:
    """Read ground_truth.sha256 (provided): '<hash> <onset ISO> <tolerance_s>' per line -> list of
    {'hash', 'onset' (tz-aware Timestamp), 'tolerance_s'}."""
    out = []
    for ln in (Path(data_dir) / "ground_truth.sha256").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            h, onset, tol = ln.split()
            out.append({"hash": h, "onset": pd.Timestamp(onset), "tolerance_s": float(tol)})
    return out
