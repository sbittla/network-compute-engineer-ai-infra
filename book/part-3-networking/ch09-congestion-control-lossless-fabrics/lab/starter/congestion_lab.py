#!/usr/bin/env python3
"""Chapter 9 lab -- congestion telemetry diagnosis and a SIMULATED incast model (STARTER -- implement the TODOs).

Units used throughout:
    * throughput gauges: Gb/s (decimal, 10^9 bit/s)
    * queue depth: KB (10^3 bytes), the per-interval maximum (watermark) of the TC3 egress queue
    * counter rates: events per second (packets/s or pause frames/s)
    * latency: microseconds (us)
    * simulation time: microseconds; simulation volumes: bytes

Run as a script to produce the diagnosis report:
    python congestion_lab.py --out report.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

LABELS = ("incast", "pause_propagation", "pfc_storm", "unclassified")

# Detection thresholds (documented in lab/README.md, Task 3-5).
HOT_QUEUE_KB = 1000.0          # TC3 egress watermark that counts as "congested"
HOT_PFC_RATE = 100.0           # pause frames/s that counts as "PFC active" on a port
STORM_PFC_RX_RATE = 10_000.0   # sustained received pause frames/s that indicate a storm
STORM_MAX_TX_GBPS = 5.0        # ...while the port transmits essentially nothing
LINE_FRACTION = 0.9            # "at line rate" means >= 90 % of the 400 Gb/s port
VICTIM_RATIO = 10.0            # p99 latency inflation vs. baseline that counts as "impacted"
VICTIM_DST_QUEUE_KB = 500.0    # destination port below this is "not itself congested"

SWITCH_COUNTERS = ["ecn_marked_tc3", "pfc_tx_p3", "pfc_rx_p3", "discards_tc3"]
NIC_COUNTERS = ["cnp_sent", "cnp_handled", "ecn_marked_rx", "pfc_tx_p3", "pfc_rx_p3"]


# ---------------------------------------------------------------------------------------------
# Provided helpers (identical in starter and solution)
# ---------------------------------------------------------------------------------------------
def load_dataset(data_dir: Path) -> dict:
    """Load all lab inputs. Returns dict with DataFrames ``switch``, ``nic``, ``probes`` and dicts
    ``topology`` and ``sim``."""
    data_dir = Path(data_dir)
    return {
        "switch": pd.read_csv(data_dir / "switch_ports.csv"),
        "nic": pd.read_csv(data_dir / "nic_counters.csv"),
        "probes": pd.read_csv(data_dir / "flow_probes.csv"),
        "topology": yaml.safe_load((data_dir / "topology.yaml").read_text(encoding="utf-8")),
        "sim": yaml.safe_load((data_dir / "sim_configs.yaml").read_text(encoding="utf-8")),
    }


def port_index(topology: dict) -> pd.DataFrame:
    """Return one row per switch port: switch, port, role ('downlink'|'fabric'), peer, peer_port,
    peer_kind ('nic'|'switch')."""
    rows = []
    for L in topology["links"]:
        rows.append({"switch": L["a_device"], "port": L["a_port"], "role": L["role"],
                     "peer": L["b_device"], "peer_port": L["b_port"], "peer_kind": L["b_kind"]})
        if L["b_kind"] == "switch":
            rows.append({"switch": L["b_device"], "port": L["b_port"], "role": L["role"],
                         "peer": L["a_device"], "peer_port": L["a_port"], "peer_kind": "switch"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------
# Task 1 -- counters to rates
# ---------------------------------------------------------------------------------------------
def counters_to_rates(df: pd.DataFrame, keys: list[str], counters: list[str]) -> pd.DataFrame:
    """Convert cumulative counters into per-second rates.

    For every counter ``c`` add a column ``c_rate`` = (c[t] - c[t_prev]) / (t - t_prev) computed
    within each group defined by ``keys`` after sorting by ``ts_s``. ``t_prev`` is the previous
    *present* sample, so telemetry gaps are divided by the true elapsed time. The first sample of a
    group and any negative delta (counter cleared or wrapped) give NaN -- never a negative or
    fabricated rate. Returns a new DataFrame sorted by keys + ts_s; input is not modified.
    """
    # TODO: Sort by keys + ts_s, group by keys.
    # TODO: Delta of each counter and of ts_s within each group (groupby().diff()).
    # TODO: rate = delta / dt; set NaN where delta < 0 (counter cleared/wrapped).
    raise NotImplementedError("counters_to_rates")


def prepare_ports(ds: dict) -> pd.DataFrame:
    """Switch-port rates joined with port roles (uses counters_to_rates)."""
    rates = counters_to_rates(ds["switch"], ["switch", "port"], SWITCH_COUNTERS)
    return rates.merge(port_index(ds["topology"]), on=["switch", "port"], how="left")


# ---------------------------------------------------------------------------------------------
# Task 2 -- episode detection
# ---------------------------------------------------------------------------------------------
def detect_episodes(ports: pd.DataFrame, merge_gap_s: int = 6) -> list[dict]:
    """Find congestion episodes.

    A port-sample is *hot* if q_tc3_max_kb >= HOT_QUEUE_KB, or pfc_tx_p3_rate >= HOT_PFC_RATE, or
    pfc_rx_p3_rate >= HOT_PFC_RATE (NaN rates are not hot). An episode is a maximal run of hot
    timestamps where consecutive hot timestamps are at most ``merge_gap_s`` apart.

    Returns a list (sorted by start) of dicts: {"start": int s, "end": int s (last hot ts),
    "ports": sorted list of "switch:port" strings that were hot at any time in the episode}.
    """
    # TODO: Build a boolean 'hot' mask (treat NaN rates as not hot).
    # TODO: Walk the sorted unique hot timestamps; start a new episode when the gap exceeds merge_gap_s.
    # TODO: Collect the hot 'switch:port' ids inside each episode window.
    raise NotImplementedError("detect_episodes")


def _episode_stats(ports: pd.DataFrame, episode: dict) -> pd.DataFrame:
    """Median of each metric per port over the episode window."""
    w = ports[(ports["ts_s"] >= episode["start"]) & (ports["ts_s"] <= episode["end"])]
    cols = ["tx_gbps", "rx_gbps", "q_tc3_max_kb", "ecn_marked_tc3_rate", "pfc_tx_p3_rate", "pfc_rx_p3_rate"]
    st = w.groupby(["switch", "port", "role", "peer", "peer_port", "peer_kind"])[cols].median().reset_index()
    st["id"] = st["switch"] + ":" + st["port"]
    return st


# ---------------------------------------------------------------------------------------------
# Task 3 -- classification and congestion-tree roots
# ---------------------------------------------------------------------------------------------
def classify_episode(ports: pd.DataFrame, episode: dict, line_gbps: float = 400.0) -> str:
    """Classify one episode into one of LABELS using per-port medians over the episode.

    Rules, checked in order:
      1. ``pfc_storm``: some port receives >= STORM_PFC_RX_RATE pause frames/s while transmitting
         < STORM_MAX_TX_GBPS (the peer is pausing it continuously and nothing drains).
      2. ``pause_propagation``: PFC is active (tx or rx >= HOT_PFC_RATE) on any switch-to-switch
         ('fabric') port -- the congestion tree has spread beyond the first hop.
      3. ``incast``: some port has a hot queue, transmits >= LINE_FRACTION * line rate, and is not
         itself being paused (pfc_rx < HOT_PFC_RATE).
      4. otherwise ``unclassified``.
    """
    # TODO: Use _episode_stats(ports, episode) to get per-port medians.
    # TODO: Apply the four rules in the documented order; storm first.
    raise NotImplementedError("classify_episode")


def find_roots(ports: pd.DataFrame, episode: dict, line_gbps: float = 400.0) -> list[str]:
    """Return the root(s) of the congestion tree as sorted "switch:port" strings.

    A root is a port whose congestion is *not explained by a downstream pause*: median queue
    >= HOT_QUEUE_KB, median tx >= LINE_FRACTION * line_gbps, and median pfc_rx < HOT_PFC_RATE.
    Ports that are congested because their peer pauses them are branches, not roots.
    """
    # TODO: Filter the per-port medians: hot queue, near line rate, NOT receiving pause.
    raise NotImplementedError("find_roots")


def find_storm_source(ports: pd.DataFrame, nic: pd.DataFrame, topology: dict, episode: dict) -> str | None:
    """Identify the device generating a PFC storm as "node:nic" (or "switch:port" for a switch
    peer), or None if there is no storm. Confirms with the NIC's own pfc_tx_p3 rate when the peer is
    a NIC: the NIC must report >= STORM_PFC_RX_RATE transmitted pause frames/s (median)."""
    # TODO: Find the port receiving a sustained pause storm while transmitting ~nothing.
    # TODO: Map it to its peer via the stats columns peer/peer_port.
    # TODO: If the peer is a NIC, confirm with the NIC's own pfc_tx_p3 rate (counters_to_rates on ds['nic']).
    raise NotImplementedError("find_storm_source")


# ---------------------------------------------------------------------------------------------
# Task 4 -- victim flows (head-of-line blocking)
# ---------------------------------------------------------------------------------------------
def find_victims(probes: pd.DataFrame, ports: pd.DataFrame, episodes: list[dict],
                 baseline_end_s: int = 90) -> list[dict]:
    """Find probes that are *victims*: their p99 latency inflates while their own destination is
    not congested.

    For each probe, baseline = median lat_p99_us over ts_s < baseline_end_s. For each episode
    (dicts carrying at least start, end and "label"), impact ratio = median p99 in the episode /
    baseline. A probe is a victim in that episode if ratio >= VICTIM_RATIO AND the median queue on
    its destination port (dst_switch:dst_port) during the episode is < VICTIM_DST_QUEUE_KB AND the
    destination port is not a root of that episode.

    Returns list of dicts {"probe", "episode_label", "ratio" (float, 1 decimal), "dst_port"}, sorted
    by (probe, episode start).
    """
    # TODO: Baseline p99 per probe from ts_s < baseline_end_s.
    # TODO: Per episode: inflation ratio, destination-port median queue, destination not a root.
    raise NotImplementedError("find_victims")


# ---------------------------------------------------------------------------------------------
# Task 5 -- QoS configuration audit
# ---------------------------------------------------------------------------------------------
def audit_qos(topology: dict) -> list[tuple[str, str]]:
    """Audit each switch's QoS snapshot against fabric intent. Returns sorted (switch, code) tuples.

    Codes:
      ECN_KMIN_HIGH          ecn_kmin_kb > one bandwidth-delay product, where
                             BDP_KB = line_rate_gbps * 1e9 / 8 * base_rtt_us * 1e-6 / 1e3
      PFC_WATCHDOG_DISABLED  pfc_watchdog is false
      PFC_PRIORITY_MISMATCH  lossless_priorities differs (as a set) from fabric intent
      CNP_CLASS_MISMATCH     cnp_dscp or cnp_tc differs from fabric intent
      ROCE_CLASS_MISMATCH    roce_dscp or roce_tc differs from fabric intent
    """
    # TODO: Compute BDP_KB from fabric_intent.
    # TODO: Compare every switch's snapshot with fabric_intent; emit (switch, code) tuples.
    raise NotImplementedError("audit_qos")


# ---------------------------------------------------------------------------------------------
# Task 6 -- SIMULATED discrete-time incast model
# ---------------------------------------------------------------------------------------------
def red_mark_probability(q_kb: float, kmin_kb: float, kmax_kb: float, pmax: float) -> float:
    """RED/ECN marking profile: 0 below kmin; linear from 0 to pmax between kmin and kmax; 1 at or
    above kmax (the common switch behaviour once the queue exceeds Kmax)."""
    # TODO: Implement the three-segment RED/ECN marking profile.
    raise NotImplementedError("red_mark_probability")


def simulate_incast(common: dict, cfg: dict) -> dict:
    """SIMULATED fluid model of an N:1 incast into one 400 Gb/s egress port.

    Model (deliberately simple; see lab/README.md "What the model cannot conclude"):
      * N senders, each with ``burst_bytes`` to send, start together at line rate.
      * One shared egress queue drains at line rate. Time step ``dt_us``.
      * PFC (if enabled) is aggregated: when the queue >= xoff_kb all senders are paused, when it
        falls <= xon_kb they resume; either decision takes effect ``pause_delay_us`` later. Bytes
        that arrive while the queue is above ``buffer_kb`` consume headroom; exceeding
        buffer + headroom drops bytes (headroom overflow).
      * Without PFC, bytes beyond ``buffer_kb`` are dropped and re-offered by their sender after
        ``retx_delay_us`` (an optimistic selective-retransmission assumption).
      * ECN marking follows red_mark_probability on the queue. Each sender accumulates expected
        marked packets (p x its bytes / mtu) as seen ``feedback_delay_us`` ago; when >= 1 and at
        least ``cnp_interval_us`` since its last CNP, it applies a DCQCN-style cut:
        Rt = Rc; Rc = Rc * (1 - alpha/2); alpha = (1 - g) * alpha + g. Without a CNP for
        ``alpha_timer_us``: alpha = (1 - g) * alpha. Every ``increase_timer_us`` without a CNP:
        Rc = (Rc + Rt) / 2 (fast recovery only).

    Returns dict with: completion_us, peak_queue_kb, pause_time_us (time during which senders with
    data were paused), dropped_bytes, delivered_bytes, total_bytes, ecn_marked_bytes, cnps,
    headroom_overflow (bool), lower_bound_us (total_bytes / line rate).
    """
    # TODO: Follow the model description exactly; keep every quantity in bytes and microseconds.
    # TODO: Remember: decisions (pause, ECN feedback) act with a delay -- keep short history buffers.
    # TODO: Return every key listed above; round as you see fit.
    raise NotImplementedError("simulate_incast")


def compare_configs(sim: dict) -> pd.DataFrame:
    """Run simulate_incast for every config in sim['configs']; one row per config (index = name)."""
    rows = {name: simulate_incast(sim["common"], cfg) for name, cfg in sim["configs"].items()}
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------------------------
# Task 7 -- report
# ---------------------------------------------------------------------------------------------
REPORT_SECTIONS = ["## Summary", "## Episodes", "## Root cause and evidence", "## Victim flows",
                   "## Configuration findings", "## Simulation [SIMULATED]",
                   "## What the simulation cannot conclude", "## Mitigation proposal", "## Experiment plan"]


def run_analysis(data_dir: Path) -> dict:
    """Run every task and return a dict consumed by build_report."""
    ds = load_dataset(data_dir)
    ports = prepare_ports(ds)
    episodes = detect_episodes(ports)
    for ep in episodes:
        ep["label"] = classify_episode(ports, ep)
        ep["roots"] = find_roots(ports, ep)
        ep["storm_source"] = find_storm_source(ports, ds["nic"], ds["topology"], ep) if ep["label"] == "pfc_storm" else None
    victims = find_victims(ds["probes"], ports, episodes)
    return {"episodes": episodes, "victims": victims, "qos_findings": audit_qos(ds["topology"]),
            "sim": compare_configs(ds["sim"]), "sim_configs": ds["sim"]["configs"]}


def build_report(a: dict) -> str:
    """Render the diagnosis report (Markdown) containing every heading in REPORT_SECTIONS."""
    # TODO: Emit every heading in REPORT_SECTIONS, in order.
    # TODO: Label the simulation section [SIMULATED] and name the storm source if there is one.
    raise NotImplementedError("build_report")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = build_report(run_analysis(args.data))
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
