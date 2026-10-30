"""Link-health analyzer and physical-layer planning tools (Chapter 10) -- STARTER.

Implement every function that raises NotImplementedError. Run ``python ../check.py`` (or
``python check.py`` from lab/) to see which checks pass.

Units: optical power in dBm, loss in dB, bias in mA, temperature in degrees C, rates per second,
link speeds in Gb/s, fibre attenuation in dB/km.
"""
from __future__ import annotations

import hashlib
import math  # noqa: F401  (you will need it)
from datetime import datetime  # noqa: F401  (you will need it)
from pathlib import Path

import pandas as pd
import yaml

# Cumulative counters that must be differenced between snapshots.
COUNTERS = [
    "link_down_events", "rx_frames", "tx_frames", "rx_fcs_errors", "rx_oversize_frames",
    "out_discards", "ecn_marked_pkts", "pfc_rx_pause", "pfc_tx_pause",
    "fec_corrected_cw", "fec_uncorrectable_cw",
]

# Finding codes. PRIORITY order decides the *primary* finding of a port: the first code in this
# list that is present wins. Physical codes come first on purpose (fix the wire before the queue).
PHYSICAL_CODES = [
    "OPTIC_MISMATCH", "LINK_DOWN", "MISCABLED", "LINK_FLAP", "CRC_ERRORS", "FEC_UNCORRECTABLE",
    "RX_POWER_LOW", "RX_POWER_HIGH", "PRE_FEC_BER_HIGH", "PRE_FEC_BER_RISING", "LANE_IMBALANCE",
    "TEMP_HIGH",
]
HIGHER_LAYER_CODES = ["OVERSIZE_FRAMES", "CONGESTION"]
PRIORITY = PHYSICAL_CODES + HIGHER_LAYER_CODES
CRITICAL_CODES = {"OPTIC_MISMATCH", "LINK_DOWN", "MISCABLED", "LINK_FLAP", "CRC_ERRORS",
                  "FEC_UNCORRECTABLE"}

ACTIONS = {
    "OPTIC_MISMATCH": "Replace module with the BOM part from the cabling schedule; re-read DOM; re-test.",
    "LINK_DOWN": "Check admin state, optic seating, LOS/LOL per lane, far-end port; inspect fibre.",
    "MISCABLED": "Trace both ends against the cabling schedule; correct patching; re-verify LLDP.",
    "LINK_FLAP": "Drain the link; reseat optic; check DOM history, firmware, far end; replace optic if repeat.",
    "CRC_ERRORS": "Drain the link; inspect/clean both ends; swap cable, then optic; soak before return.",
    "FEC_UNCORRECTABLE": "Drain the link; inspect/clean; check FEC histogram tail; swap cable then optic.",
    "RX_POWER_LOW": "Inspect and clean both end-faces (MPO); re-measure Rx; replace jumper if no recovery.",
    "RX_POWER_HIGH": "Check optic type vs reach; add attenuation only if the vendor specifies it.",
    "PRE_FEC_BER_HIGH": "Schedule drain; inspect/clean; compare far-end Tx/bias; replace optic before KP4 limit.",
    "PRE_FEC_BER_RISING": "Increase sampling; watch trend; prepare a maintenance window.",
    "LANE_IMBALANCE": "Inspect MPO end-face (single-fibre contamination/damage); clean; re-measure.",
    "TEMP_HIGH": "Check airflow, blanking panels, fan tray, adjacent high-power modules.",
    "OVERSIZE_FRAMES": "Not physical: port/host MTU mismatch. Refer to Fabric config (Chapter 7).",
    "CONGESTION": "Not physical: discards/PFC/ECN from congestion. Refer to Chapter 9 workflow.",
    "HEALTHY": "None.",
}


# ----------------------------------------------------------------------------------- loaders
# (provided -- do not change)
def load_snapshot(path: Path) -> pd.DataFrame:
    """Load one counter/DOM snapshot CSV (one row per port)."""
    return pd.read_csv(path, keep_default_na=True, dtype={"lldp_neighbor": str}).fillna(
        {"lldp_neighbor": ""})


def load_schedule(path: Path) -> pd.DataFrame:
    """Load the cabling schedule CSV (one row per cable)."""
    return pd.read_csv(path)


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def port_number(port: str) -> int:
    return int(port.replace("Ethernet", ""))


def classification_digest(results: pd.DataFrame) -> str:
    """SHA-256 over 'port:primary:layer' lines in port order (used by check.py)."""
    lines = [f"{r.port}:{r.primary}:{r.layer}" for r in results.itertuples()]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


# ------------------------------------------------------------------------------- task 1
def counter_delta(v0: int, v1: int) -> int:
    """Difference of a cumulative counter between two snapshots.

    TODO:
      * normal case: v1 - v0
      * if v1 < v0 the counter was cleared (or the collection agent restarted) between samples;
        return v1 (the best available estimate of the in-window increase)
      * never return a negative number
    """
    raise NotImplementedError("counter_delta")


def pcs_fec_line_rate_gbps(mac_rate_gbps: float) -> float:
    """Serial line rate after 256b/257b transcoding and RS(544,514) FEC, in Gb/s.

    TODO: apply both overhead ratios (Section 10.4). 400 -> 425.0.
    """
    raise NotImplementedError("pcs_fec_line_rate_gbps")


def fec_margin_decades(pre_fec_ber: float, threshold: float = 2.4e-4) -> float:
    """Orders of magnitude between measured pre-FEC BER and the FEC threshold.

    TODO: margin = log10(threshold / ber). Return float('inf') for None, NaN, or ber <= 0
    (no errors measured / no signal: margin is not defined).
    """
    raise NotImplementedError("fec_margin_decades")


# ------------------------------------------------------------------------------- task 2
def compute_deltas(t0: pd.DataFrame, t1: pd.DataFrame) -> pd.DataFrame:
    """Join two snapshots per port.

    TODO: return a DataFrame indexed by ``port`` containing
      * every T1 column unchanged (DOM, status, optic, lldp_neighbor, pre_fec_ber, ...)
      * ``pre_fec_ber_t0``: the T0 pre-FEC BER for the same port
      * ``dt_s``: seconds between the two ``ts`` values (ISO-8601 with offset)
      * ``d_<name>`` for each name in COUNTERS, using counter_delta()
    """
    raise NotImplementedError("compute_deltas")


# ------------------------------------------------------------------------------- task 3
def classify_port(row: dict, sched: dict | None, thr: dict) -> dict:
    """Classify one port.

    Inputs: ``row`` is one compute_deltas() row as a dict (it includes the T1 columns, the d_*
    deltas, pre_fec_ber_t0, dt_s); ``sched`` is the cabling-schedule row whose a_port is this port
    (or None); ``thr`` is data/thresholds.yaml.

    TODO -- add a finding code when its rule holds:
      OPTIC_MISMATCH      installed optic_type != sched['expected_optic_a']
      LINK_DOWN           oper_status != 'up'  (if down, evaluate no further rules below)
      MISCABLED           lldp_neighbor != f"{b_device}:{b_port}" from the schedule
      LINK_FLAP           d_link_down_events >= thr.link.flap_events_warn
      CRC_ERRORS          d_rx_fcs_errors > 0
      FEC_UNCORRECTABLE   d_fec_uncorrectable_cw > 0
      RX_POWER_LOW        min lane Rx power (l0..l3) <  optics[installed].rx_power_low_warn_dbm
      RX_POWER_HIGH       max lane Rx power          >  optics[installed].rx_power_high_warn_dbm
      TEMP_HIGH           module_temp_c >= optics[installed].temp_high_warn_c
      LANE_IMBALANCE      (max - min) lane Rx power > thr.link.lane_imbalance_db
      PRE_FEC_BER_HIGH    pre_fec_ber >= thr.fec.pre_fec_ber_warn
      PRE_FEC_BER_RISING  pre_fec_ber >= rising_factor * pre_fec_ber_t0 AND >= rising_floor
      OVERSIZE_FRAMES     d_rx_oversize_frames > 0
      CONGESTION          d_out_discards > 0 OR (d_pfc_rx_pause + d_pfc_tx_pause)/dt_s >
                          thr.higher_layer.pfc_pause_rate_warn_per_s
    Then:
      findings  = codes sorted in PRIORITY order
      primary   = findings[0] or "HEALTHY"
      layer     = "physical" if any physical code, elif findings "higher_layer", else "healthy"
      severity  = "ok" (healthy) | "refer" (higher_layer) | "critical" (primary in CRITICAL_CODES,
                  or RX_POWER_LOW with a lane below rx_power_low_crit_dbm,
                  or a PRE_FEC_BER_* primary with pre_fec_ber >= thr.fec.pre_fec_ber_crit) | "warning"
      action    = ACTIONS[primary]
    Return {"findings", "primary", "layer", "severity", "action"}.
    """
    raise NotImplementedError("classify_port")


def analyze(t0: pd.DataFrame, t1: pd.DataFrame, schedule: pd.DataFrame, thr: dict) -> pd.DataFrame:
    """Run compute_deltas + classify_port for every port.

    TODO: return columns port, layer, primary, severity, findings (';'-joined), action,
    sorted by port number (Ethernet1, Ethernet2, ..., Ethernet64), index reset.
    The schedule row for a port is the one whose ``a_port`` equals the port.
    """
    raise NotImplementedError("analyze")


# ------------------------------------------------------------------------------- task 4
def commissioning_report(results: pd.DataFrame, leaf: str) -> dict:
    """Summarise analyzer output as a commissioning (acceptance) report.

    TODO: a port is *accepted* when it has no physical-layer finding. Higher-layer findings do
    not block physical acceptance but are referred to the owning team.
    Return keys: leaf, ports_total, ports_accepted, physical_failures (list of ports in port
    order), higher_layer_referrals (list), overall ("PASS" only if no physical failures, else
    "FAIL"), markdown (a Markdown report that names every failing and referred port with its
    primary finding and action).
    """
    raise NotImplementedError("commissioning_report")


# ------------------------------------------------------------------------------- task 5
def link_budget(tx_dbm: float, rx_sensitivity_dbm: float, length_km: float,
                fiber_db_per_km: float, n_connectors: int, connector_db: float,
                n_splices: int = 0, splice_db: float = 0.0, penalties_db: float = 0.0) -> dict:
    """Simple optical power budget.

    TODO: loss = length*attenuation + connectors*connector_loss + splices*splice_loss + penalties
          rx = tx - loss;  margin = rx - sensitivity
    Return {"loss_db", "rx_dbm", "margin_db"}, each rounded to 2 decimal places.
    """
    raise NotImplementedError("link_budget")


# ------------------------------------------------------------------------------- task 6
def estimate_fabric_bom(spec: dict, policy: dict) -> dict:
    """Port, cable, optic and spares estimate for a rail-optimized 2-tier leaf-spine fabric.

    spec: nodes, rails, switch_radix, oversubscription (down:up ratio, 1.0 = non-blocking),
          host_optic, fabric_optic.  policy: optic_rate, cable_rate, min_per_type,
          spare_switches_per_model.  (data/fabrics.yaml)

    TODO (one NIC port per rail per node; every link = 1 cable + 1 optic at each end):
      down_max            = int(radix * osub / (1 + osub))          # down ports a leaf can offer
      leaves_per_rail     = ceil(nodes / down_max);  leaves = rails * leaves_per_rail
      down_ports_per_leaf = ceil(nodes / leaves_per_rail)
      up_ports_per_leaf   = ceil(down_ports_per_leaf / osub)
      host_links = nodes * rails;  fabric_links = leaves * up_ports_per_leaf
      spines = ceil(fabric_links / radix), then increase until up_ports_per_leaf % spines == 0
      optics = {type: count} with 2 per link (types may coincide -> sum them)
      cables = host_links + fabric_links
      spare_optics[type] = max(ceil(count * optic_rate), min_per_type)
      spare_cables       = max(ceil(cables * cable_rate), min_per_type)
    Return keys: leaves, spines, down_ports_per_leaf, up_ports_per_leaf,
      uplinks_per_leaf_per_spine, host_links, fabric_links, total_links, optics, cables,
      leaf_ports_used, spine_ports_used, free_leaf_ports, free_spine_ports, spare_optics,
      spare_cables, spare_switches, oversubscription_actual.
    """
    raise NotImplementedError("estimate_fabric_bom")


def generate_cabling_schedule(spec: dict) -> list[dict]:
    """Cabling schedule rows for the fabric in ``spec`` (uses spec['prefix'] for names).

    TODO: one row per link with keys cable_id, a_device, a_port, b_device, b_port, optic,
    label_a, label_b. Requirements checked:
      * row count == total_links from estimate_fabric_bom
      * cable_id unique; every (device, port) endpoint used at most once
      * every leaf has exactly uplinks_per_leaf_per_spine links to every spine
      * labels name the cable ID and both endpoints
    Suggested naming: leaf ``{prefix}-leaf-r{r}``, host ``{prefix}-n{nn}`` (nn = 01..nodes) port ``nic{r}``,
    spine ``{prefix}-spine-{s}``; leaf up ports start at Ethernet{down_max + 1}.
    """
    raise NotImplementedError("generate_cabling_schedule")
