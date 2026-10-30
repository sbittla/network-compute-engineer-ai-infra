#!/usr/bin/env python3
"""Chapter 9 lab -- congestion telemetry diagnosis and a SIMULATED incast model (REFERENCE SOLUTION).

Units used throughout:
    * throughput gauges: Gb/s (decimal, 10^9 bit/s)
    * queue depth: KB (10^3 bytes), the per-interval maximum (watermark) of the TC3 egress queue
    * counter rates: events per second (packets/s or pause frames/s)
    * latency: microseconds (us)
    * simulation time: microseconds; simulation volumes: bytes

Run as a script to produce the diagnosis report:
    python congestion_lab.py --data ../../lab/data --out report.md
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
    out = df.sort_values(keys + ["ts_s"]).reset_index(drop=True).copy()
    g = out.groupby(keys, sort=False)
    dt = g["ts_s"].diff()
    for c in counters:
        delta = g[c].diff()
        rate = delta / dt
        rate[delta < 0] = np.nan
        out[f"{c}_rate"] = rate
    return out


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
    hot = (ports["q_tc3_max_kb"] >= HOT_QUEUE_KB) | (ports["pfc_tx_p3_rate"] >= HOT_PFC_RATE) | (
        ports["pfc_rx_p3_rate"] >= HOT_PFC_RATE)
    h = ports[hot.fillna(False)]
    times = sorted(h["ts_s"].unique())
    episodes: list[dict] = []
    for t in times:
        if episodes and t - episodes[-1]["end"] <= merge_gap_s:
            episodes[-1]["end"] = int(t)
        else:
            episodes.append({"start": int(t), "end": int(t)})
    for ep in episodes:
        sel = h[(h["ts_s"] >= ep["start"]) & (h["ts_s"] <= ep["end"])]
        ep["ports"] = sorted(set(sel["switch"] + ":" + sel["port"]))
    return episodes


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
    st = _episode_stats(ports, episode)
    if ((st["pfc_rx_p3_rate"] >= STORM_PFC_RX_RATE) & (st["tx_gbps"] < STORM_MAX_TX_GBPS)).any():
        return "pfc_storm"
    fab = st[st["role"] == "fabric"]
    if ((fab["pfc_tx_p3_rate"] >= HOT_PFC_RATE) | (fab["pfc_rx_p3_rate"] >= HOT_PFC_RATE)).any():
        return "pause_propagation"
    if find_roots(ports, episode, line_gbps):
        return "incast"
    return "unclassified"


def find_roots(ports: pd.DataFrame, episode: dict, line_gbps: float = 400.0) -> list[str]:
    """Return the root(s) of the congestion tree as sorted "switch:port" strings.

    A root is a port whose congestion is *not explained by a downstream pause*: median queue
    >= HOT_QUEUE_KB, median tx >= LINE_FRACTION * line_gbps, and median pfc_rx < HOT_PFC_RATE.
    Ports that are congested because their peer pauses them are branches, not roots.
    """
    st = _episode_stats(ports, episode)
    r = st[(st["q_tc3_max_kb"] >= HOT_QUEUE_KB) & (st["tx_gbps"] >= LINE_FRACTION * line_gbps)
           & (st["pfc_rx_p3_rate"] < HOT_PFC_RATE)]
    return sorted(r["id"].tolist())


def find_storm_source(ports: pd.DataFrame, nic: pd.DataFrame, topology: dict, episode: dict) -> str | None:
    """Identify the device generating a PFC storm as "node:nic" (or "switch:port" for a switch
    peer), or None if there is no storm. Confirms with the NIC's own pfc_tx_p3 rate when the peer is
    a NIC: the NIC must report >= STORM_PFC_RX_RATE transmitted pause frames/s (median)."""
    st = _episode_stats(ports, episode)
    s = st[(st["pfc_rx_p3_rate"] >= STORM_PFC_RX_RATE) & (st["tx_gbps"] < STORM_MAX_TX_GBPS)]
    if s.empty:
        return None
    row = s.sort_values("pfc_rx_p3_rate", ascending=False).iloc[0]
    if row["peer_kind"] != "nic":
        return f"{row['peer']}:{row['peer_port']}"
    nr = counters_to_rates(nic, ["node", "nic"], ["pfc_tx_p3"])
    w = nr[(nr["node"] == row["peer"]) & (nr["nic"] == row["peer_port"])
           & (nr["ts_s"] >= episode["start"]) & (nr["ts_s"] <= episode["end"])]
    if w["pfc_tx_p3_rate"].median() >= STORM_PFC_RX_RATE:
        return f"{row['peer']}:{row['peer_port']}"
    return None


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
    out = []
    for pid, g in probes.groupby("probe"):
        base = g[g["ts_s"] < baseline_end_s]["lat_p99_us"].median()
        dst = f"{g['dst_switch'].iloc[0]}:{g['dst_port'].iloc[0]}"
        for ep in episodes:
            w = g[(g["ts_s"] >= ep["start"]) & (g["ts_s"] <= ep["end"])]
            ratio = w["lat_p99_us"].median() / base
            if ratio < VICTIM_RATIO:
                continue
            st = _episode_stats(ports, ep)
            dq = st.loc[st["id"] == dst, "q_tc3_max_kb"]
            dst_q = float(dq.iloc[0]) if len(dq) else 0.0
            roots = ep.get("roots") if ep.get("roots") is not None else find_roots(ports, ep)
            if dst_q < VICTIM_DST_QUEUE_KB and dst not in roots:
                out.append({"probe": pid, "episode_label": ep["label"], "ratio": round(float(ratio), 1),
                            "dst_port": dst, "_start": ep["start"]})
    out.sort(key=lambda d: (d["probe"], d["_start"]))
    for d in out:
        d.pop("_start")
    return out


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
    intent = topology["fabric_intent"]
    bdp_kb = intent["line_rate_gbps"] * 1e9 / 8 * intent["base_rtt_us"] * 1e-6 / 1e3
    findings = []
    for sw, q in topology["qos"].items():
        if q["ecn_kmin_kb"] > bdp_kb:
            findings.append((sw, "ECN_KMIN_HIGH"))
        if not q["pfc_watchdog"]:
            findings.append((sw, "PFC_WATCHDOG_DISABLED"))
        if set(q["lossless_priorities"]) != set(intent["lossless_priorities"]):
            findings.append((sw, "PFC_PRIORITY_MISMATCH"))
        if q["cnp_dscp"] != intent["cnp_dscp"] or q["cnp_tc"] != intent["cnp_tc"]:
            findings.append((sw, "CNP_CLASS_MISMATCH"))
        if q["roce_dscp"] != intent["roce_dscp"] or q["roce_tc"] != intent["roce_tc"]:
            findings.append((sw, "ROCE_CLASS_MISMATCH"))
    return sorted(findings)


# ---------------------------------------------------------------------------------------------
# Task 6 -- SIMULATED discrete-time incast model
# ---------------------------------------------------------------------------------------------
def red_mark_probability(q_kb: float, kmin_kb: float, kmax_kb: float, pmax: float) -> float:
    """RED/ECN marking profile: 0 below kmin; linear from 0 to pmax between kmin and kmax; 1 at or
    above kmax (the common switch behaviour once the queue exceeds Kmax)."""
    if q_kb <= kmin_kb:
        return 0.0
    if q_kb >= kmax_kb:
        return 1.0
    return pmax * (q_kb - kmin_kb) / (kmax_kb - kmin_kb)


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
    c = {**common, **cfg}
    n = int(c["n_senders"])
    dt = float(c["dt_us"])
    line_Bpus = c["line_gbps"] * 1e9 / 8 / 1e6           # bytes per microsecond
    buf = c["buffer_kb"] * 1e3
    head = c["headroom_kb"] * 1e3
    xoff, xon = c["xoff_kb"] * 1e3, c["xon_kb"] * 1e3
    fb_steps = max(1, int(round(c["feedback_delay_us"] / dt)))
    pd_steps = max(1, int(round(c["pause_delay_us"] / dt)))
    rx_steps = max(1, int(round(c["retx_delay_us"] / dt)))
    max_steps = int(c["max_time_us"] / dt)

    remaining = np.full(n, float(c["burst_bytes"]))
    total = float(remaining.sum())
    rate = np.full(n, line_Bpus)          # current rate Rc, bytes/us
    target = rate.copy()                   # Rt
    alpha = np.ones(n)
    acc = np.zeros(n)
    last_cnp = np.full(n, -1e9)
    last_alpha = np.zeros(n)
    last_inc = np.zeros(n)
    q = 0.0
    peak = 0.0
    paused_hist = [False] * (pd_steps + 1)
    q_hist = [0.0] * (fb_steps + 1)
    paused_state = False
    pending: dict[int, np.ndarray] = {}
    dropped = delivered = marked = 0.0
    pause_time = 0.0
    cnps = 0
    overflow = False
    step = 0
    while step < max_steps:
        t = step * dt
        if step in pending:
            remaining += pending.pop(step)
        paused_eff = c["pfc_enabled"] and paused_hist[-pd_steps - 1]
        active = remaining > 0
        if paused_eff and active.any():
            pause_time += dt
        send = np.zeros(n) if paused_eff else np.minimum(rate * dt, remaining)
        remaining -= send
        arrivals = float(send.sum())
        q += arrivals
        limit = buf + head if c["pfc_enabled"] else buf
        if q > limit:
            drop = q - limit
            q = limit
            dropped += drop
            if c["pfc_enabled"]:
                overflow = True
            share = send / arrivals if arrivals > 0 else np.full(n, 1.0 / n)
            pending[step + rx_steps] = pending.get(step + rx_steps, np.zeros(n)) + drop * share
        peak = max(peak, q)
        dep = min(q, line_Bpus * dt)
        q -= dep
        delivered += dep
        p_now = red_mark_probability(q / 1e3, c["ecn_kmin_kb"], c["ecn_kmax_kb"], c["ecn_pmax"])
        marked += p_now * dep
        # PFC decision on the current queue
        if q >= xoff:
            paused_state = True
        elif q <= xon:
            paused_state = False
        paused_hist.append(paused_state)
        paused_hist = paused_hist[-(pd_steps + 1):]
        q_hist.append(q)
        q_hist = q_hist[-(fb_steps + 1):]
        # ECN feedback as seen feedback_delay ago
        p_fb = red_mark_probability(q_hist[0] / 1e3, c["ecn_kmin_kb"], c["ecn_kmax_kb"], c["ecn_pmax"])
        acc += p_fb * send / c["mtu_bytes"]
        cut = (acc >= 1.0) & (t - last_cnp >= c["cnp_interval_us"])
        if cut.any():
            cnps += int(cut.sum())
            target[cut] = rate[cut]
            rate[cut] = rate[cut] * (1 - alpha[cut] / 2)
            alpha[cut] = (1 - c["g"]) * alpha[cut] + c["g"]
            last_cnp[cut] = t
            last_alpha[cut] = t
            last_inc[cut] = t
            acc[cut] = 0.0
        dec = (~cut) & (t - last_alpha >= c["alpha_timer_us"])
        alpha[dec] *= (1 - c["g"])
        last_alpha[dec] = t
        inc = (~cut) & (t - last_inc >= c["increase_timer_us"])
        rate[inc] = (rate[inc] + target[inc]) / 2
        last_inc[inc] = t
        step += 1
        if remaining.sum() <= 0 and q <= 1e-6 and not pending:
            break
    return {
        "completion_us": round(step * dt, 1),
        "peak_queue_kb": round(peak / 1e3, 1),
        "pause_time_us": round(pause_time, 1),
        "dropped_bytes": round(dropped),
        "delivered_bytes": round(delivered),
        "total_bytes": round(total),
        "ecn_marked_bytes": round(marked),
        "cnps": cnps,
        "headroom_overflow": overflow,
        "lower_bound_us": round(total / line_Bpus, 1),
    }


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
    L = ["# Congestion diagnosis -- ORION backend slice (SYNTHETIC dataset)", ""]
    L += ["## Summary", ""]
    for ep in a["episodes"]:
        extra = f"; storm source {ep['storm_source']}" if ep.get("storm_source") else ""
        L.append(f"- {ep['start']}-{ep['end']} s: **{ep['label']}**; roots {', '.join(ep['roots']) or 'none'}{extra}.")
    L += ["", "## Episodes", "", "| Start (s) | End (s) | Label | Hot ports |", "|---|---|---|---|"]
    for ep in a["episodes"]:
        L.append(f"| {ep['start']} | {ep['end']} | {ep['label']} | {len(ep['ports'])}: {', '.join(ep['ports'][:6])}"
                 f"{' ...' if len(ep['ports']) > 6 else ''} |")
    L += ["", "## Root cause and evidence", ""]
    for ep in a["episodes"]:
        if ep["label"] == "incast":
            L.append(f"- Incast ({ep['start']}-{ep['end']} s): egress {', '.join(ep['roots'])} at line rate with a "
                     "deep TC3 queue and ECN marks; PFC pauses only on the senders' ingress ports (first hop).")
        elif ep["label"] == "pause_propagation":
            L.append(f"- Pause propagation ({ep['start']}-{ep['end']} s): root {', '.join(ep['roots'])} is the only "
                     "congested port not itself receiving pause; spine and orion-be-leaf-r4 uplink queues are branches "
                     "(they receive PFC from downstream). Cross-rail traffic suggests a rank-to-rail mapping error.")
        elif ep["label"] == "pfc_storm":
            L.append(f"- PFC storm ({ep['start']}-{ep['end']} s): {ep['storm_source']} transmits pause frames "
                     "continuously while receiving nothing; its switch port has a full queue, zero ECN marks and "
                     "~0 Gb/s egress. A PFC watchdog would have isolated the queue.")
        else:
            L.append(f"- {ep['start']}-{ep['end']} s: unclassified -- collect more evidence.")
    L += ["", "## Victim flows", "", "| Probe | Episode | p99 inflation | Destination port |", "|---|---|---|---|"]
    for v in a["victims"]:
        L.append(f"| {v['probe']} | {v['episode_label']} | {v['ratio']}x | {v['dst_port']} |")
    L += ["", "Victims have uncongested destinations: their delay comes from PFC pausing a shared ingress "
          "port or upstream link (head-of-line blocking), not from their own path's egress.", ""]
    L += ["## Configuration findings", ""]
    for sw, code in a["qos_findings"]:
        L.append(f"- {sw}: {code}")
    L += ["", "## Simulation [SIMULATED]", "", "Configurations:", ""]
    for name, cfg in a["sim_configs"].items():
        L.append(f"- `{name}`: {cfg['description']}")
    L += ["", "| Config | Completion (us) | Lower bound (us) | Peak queue (KB) | Pause time (us) | Dropped (B) | CNPs |",
          "|---|---|---|---|---|---|---|"]
    for name, r in a["sim"].iterrows():
        L.append(f"| {name} | {r['completion_us']} | {r['lower_bound_us']} | {r['peak_queue_kb']} | {r['pause_time_us']} "
                 f"| {r['dropped_bytes']} | {r['cnps']} |")
    L += ["", "## What the simulation cannot conclude", "",
          "- It is a single-queue fluid model: no ASIC shared-buffer dynamics, no per-ingress-port PFC, no "
          "multi-hop pause propagation, no ECMP or other traffic classes.",
          "- The DCQCN reaction is simplified (no byte counter, no additive/hyper increase, no NIC "
          "implementation quirks); absolute numbers are not predictions of real hardware.",
          "- It cannot show victim-flow HOL blocking, deadlock, or PFC storm behaviour.",
          "- Lossy-mode recovery assumes best-case selective retransmission after 20 us; go-back-N resends "
          "the whole in-flight window, and a lost tail packet waits for the ACK timeout (~4.3 s at "
          "timeout 20 [VENDOR-SPEC]).",
          "- Only the *direction* of differences between configurations is meaningful, and only as a "
          "hypothesis to test on an L3 lab fabric.", ""]
    L += ["## Mitigation proposal", "",
          "1. orion-be-leaf-r3: restore template ECN thresholds (Kmin 150 KB / Kmax 1500 KB) through the change "
          "pipeline; canary one leaf first; validate ECN-marked vs pause ratio.",
          "2. Enable the PFC watchdog on orion-be-leaf-r3; confirm detection/restore timers against vendor guidance.",
          "3. Drain and investigate the storm NIC (firmware, driver, host hang) before return to service.",
          "4. orion-be-spine-2: remove priority 4 from the lossless set; orion-be-leaf-r4: map CNPs to TC 6.",
          "5. Fix the job's rank-to-rail mapping that produced cross-rail incast (Chapters 5, 13).", ""]
    L += ["## Experiment plan", "",
          "Controlled A/B on a dedicated L3 lab fabric (never production): same incast generator "
          "(N senders, fixed message size), one variable changed (ECN thresholds), >= 5 repetitions per "
          "config with warm-up, record pause frames tx/rx, ECN-marked, CNPs, queue watermarks, "
          "completion time p50/p99, and an environment manifest.", ""]
    return "\n".join(L)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent.parent.parent / "lab" / "data")
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
