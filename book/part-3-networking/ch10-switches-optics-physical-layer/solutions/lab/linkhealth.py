"""Link-health analyzer and physical-layer planning tools (Chapter 10) -- REFERENCE SOLUTION.

Units: optical power in dBm, loss in dB, bias in mA, temperature in degrees C, rates per second,
link speeds in Gb/s, fibre attenuation in dB/km.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

# Cumulative counters that must be differenced between snapshots.
COUNTERS = [
    "link_down_events", "rx_frames", "tx_frames", "rx_fcs_errors", "rx_oversize_frames",
    "out_discards", "ecn_marked_pkts", "pfc_rx_pause", "pfc_tx_pause",
    "fec_corrected_cw", "fec_uncorrectable_cw",
]

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


# ------------------------------------------------------------------------------- task 1
def counter_delta(v0: int, v1: int) -> int:
    """Difference of a cumulative counter between two snapshots.

    If v1 < v0 the counter was cleared (or the agent restarted) between samples; the best
    available estimate of the in-window increase is then v1 itself. Never returns a negative.
    """
    v0, v1 = int(v0), int(v1)
    return v1 - v0 if v1 >= v0 else v1


def pcs_fec_line_rate_gbps(mac_rate_gbps: float) -> float:
    """Serial line rate after 256b/257b transcoding and RS(544,514) FEC, in Gb/s."""
    return mac_rate_gbps * (257 / 256) * (544 / 514)


def fec_margin_decades(pre_fec_ber: float, threshold: float = 2.4e-4) -> float:
    """Orders of magnitude between the measured pre-FEC BER and the FEC threshold.

    margin = log10(threshold / ber). 2.0 means the link runs 100x below the threshold.
    """
    if pre_fec_ber is None or (isinstance(pre_fec_ber, float) and math.isnan(pre_fec_ber)) \
            or pre_fec_ber <= 0:
        return float("inf")
    return math.log10(threshold / pre_fec_ber)


# ------------------------------------------------------------------------------- task 2
def compute_deltas(t0: pd.DataFrame, t1: pd.DataFrame) -> pd.DataFrame:
    """Join two snapshots per port.

    Returns a DataFrame indexed by ``port`` containing every T1 column unchanged, plus
    ``pre_fec_ber_t0``, ``dt_s`` (seconds between snapshots) and ``d_<counter>`` for each
    entry in COUNTERS (non-negative, reset-aware).
    """
    a = t0.set_index("port")
    b = t1.set_index("port")
    out = b.copy()
    out["pre_fec_ber_t0"] = a["pre_fec_ber"].reindex(b.index)
    dt = [(datetime.fromisoformat(tb) - datetime.fromisoformat(ta)).total_seconds()
          for ta, tb in zip(a["ts"].reindex(b.index), b["ts"])]
    out["dt_s"] = dt
    for c in COUNTERS:
        out[f"d_{c}"] = [counter_delta(x0, x1) for x0, x1 in zip(a[c].reindex(b.index), b[c])]
    return out


# ------------------------------------------------------------------------------- task 3
def classify_port(row: dict, sched: dict | None, thr: dict) -> dict:
    """Classify one port from its delta row (see compute_deltas), schedule row and thresholds.

    Returns {"findings": [codes in PRIORITY order], "primary": code or "HEALTHY",
             "layer": "physical" | "higher_layer" | "healthy", "severity": ..., "action": str}.
    """
    found: set[str] = set()
    installed = row["optic_type"]
    if sched is not None and installed != sched["expected_optic_a"]:
        found.add("OPTIC_MISMATCH")
    up = row["oper_status"] == "up"
    if not up:
        found.add("LINK_DOWN")
    else:
        if sched is not None and row["lldp_neighbor"] != f"{sched['b_device']}:{sched['b_port']}":
            found.add("MISCABLED")
        if row["d_link_down_events"] >= thr["link"]["flap_events_warn"]:
            found.add("LINK_FLAP")
        if row["d_rx_fcs_errors"] > 0:
            found.add("CRC_ERRORS")
        if row["d_fec_uncorrectable_cw"] > 0:
            found.add("FEC_UNCORRECTABLE")
        spec = thr["optics"].get(installed, {})
        lanes = [row[f"rx_power_dbm_l{i}"] for i in range(4)]
        if spec:
            if min(lanes) < spec["rx_power_low_warn_dbm"]:
                found.add("RX_POWER_LOW")
            if max(lanes) > spec["rx_power_high_warn_dbm"]:
                found.add("RX_POWER_HIGH")
            if row["module_temp_c"] >= spec["temp_high_warn_c"]:
                found.add("TEMP_HIGH")
        if max(lanes) - min(lanes) > thr["link"]["lane_imbalance_db"]:
            found.add("LANE_IMBALANCE")
        fec = thr["fec"]
        ber1, ber0 = row["pre_fec_ber"], row["pre_fec_ber_t0"]
        if pd.notna(ber1):
            if ber1 >= fec["pre_fec_ber_warn"]:
                found.add("PRE_FEC_BER_HIGH")
            if pd.notna(ber0) and ber0 > 0 and ber1 >= fec["pre_fec_ber_rising_factor"] * ber0 \
                    and ber1 >= fec["pre_fec_ber_rising_floor"]:
                found.add("PRE_FEC_BER_RISING")
        if row["d_rx_oversize_frames"] > 0:
            found.add("OVERSIZE_FRAMES")
        pfc_rate = (row["d_pfc_rx_pause"] + row["d_pfc_tx_pause"]) / row["dt_s"]
        if row["d_out_discards"] > 0 or pfc_rate > thr["higher_layer"]["pfc_pause_rate_warn_per_s"]:
            found.add("CONGESTION")

    findings = [c for c in PRIORITY if c in found]
    primary = findings[0] if findings else "HEALTHY"
    if any(c in PHYSICAL_CODES for c in findings):
        layer = "physical"
    elif findings:
        layer = "higher_layer"
    else:
        layer = "healthy"
    if layer == "healthy":
        severity = "ok"
    elif layer == "higher_layer":
        severity = "refer"
    elif primary in CRITICAL_CODES:
        severity = "critical"
    elif primary == "RX_POWER_LOW" and min(row[f"rx_power_dbm_l{i}"] for i in range(4)) < \
            thr["optics"][installed]["rx_power_low_crit_dbm"]:
        severity = "critical"
    elif primary in ("PRE_FEC_BER_HIGH", "PRE_FEC_BER_RISING") and pd.notna(row["pre_fec_ber"]) and \
            row["pre_fec_ber"] >= thr["fec"]["pre_fec_ber_crit"]:
        severity = "critical"
    else:
        severity = "warning"
    return {"findings": findings, "primary": primary, "layer": layer, "severity": severity,
            "action": ACTIONS[primary]}


def analyze(t0: pd.DataFrame, t1: pd.DataFrame, schedule: pd.DataFrame, thr: dict) -> pd.DataFrame:
    """Run compute_deltas + classify_port for every port.

    Returns columns: port, layer, primary, severity, findings (';'-joined), action,
    sorted by port number.
    """
    deltas = compute_deltas(t0, t1)
    sched = schedule.set_index("a_port")
    rows = []
    for port, r in deltas.iterrows():
        s = sched.loc[port].to_dict() if port in sched.index else None
        res = classify_port(r.to_dict(), s, thr)
        rows.append({"port": port, "layer": res["layer"], "primary": res["primary"],
                     "severity": res["severity"], "findings": ";".join(res["findings"]),
                     "action": res["action"]})
    out = pd.DataFrame(rows)
    out["_n"] = out["port"].map(port_number)
    return out.sort_values("_n").drop(columns="_n").reset_index(drop=True)


def classification_digest(results: pd.DataFrame) -> str:
    """SHA-256 over 'port:primary:layer' lines in port order (used by check.py)."""
    lines = [f"{r.port}:{r.primary}:{r.layer}" for r in results.itertuples()]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


# ------------------------------------------------------------------------------- task 4
def commissioning_report(results: pd.DataFrame, leaf: str) -> dict:
    """Summarise analyzer output as a commissioning (acceptance) report.

    A port is *accepted* when it has no physical-layer finding. Higher-layer findings do not
    block physical acceptance but are referred to the owning team. Overall = PASS only if every
    port is accepted.
    Returns keys: leaf, ports_total, ports_accepted, physical_failures (list of ports, port order),
    higher_layer_referrals (list), overall ("PASS"/"FAIL"), markdown (str).
    """
    phys = results[results["layer"] == "physical"]
    refer = results[results["layer"] == "higher_layer"]
    total = len(results)
    accepted = total - len(phys)
    overall = "PASS" if phys.empty else "FAIL"
    md = [f"# Physical-layer commissioning report: {leaf}", "",
          f"Ports: {total} | accepted: {accepted} | physical failures: {len(phys)} | "
          f"referred (higher-layer): {len(refer)} | **Overall: {overall}**", "",
          "## Physical-layer failures (block acceptance)", "",
          "| Port | Severity | Primary | All findings | Action |", "|---|---|---|---|---|"]
    for r in phys.itertuples():
        md.append(f"| {r.port} | {r.severity} | {r.primary} | {r.findings} | {r.action} |")
    md += ["", "## Referred to other teams (not physical)", "",
           "| Port | Primary | Findings | Action |", "|---|---|---|---|"]
    for r in refer.itertuples():
        md.append(f"| {r.port} | {r.primary} | {r.findings} | {r.action} |")
    md += ["", "Evidence class: SIMULATED (Level-1 dataset). Re-run on hardware before sign-off.", ""]
    return {"leaf": leaf, "ports_total": total, "ports_accepted": accepted,
            "physical_failures": list(phys["port"]), "higher_layer_referrals": list(refer["port"]),
            "overall": overall, "markdown": "\n".join(md)}


# ------------------------------------------------------------------------------- task 5
def link_budget(tx_dbm: float, rx_sensitivity_dbm: float, length_km: float,
                fiber_db_per_km: float, n_connectors: int, connector_db: float,
                n_splices: int = 0, splice_db: float = 0.0, penalties_db: float = 0.0) -> dict:
    """Simple power budget. Returns {"loss_db", "rx_dbm", "margin_db"} (rounded to 2 dp).

    loss = length*attenuation + connectors*connector_loss + splices*splice_loss + penalties
    rx = tx - loss;  margin = rx - sensitivity
    """
    loss = length_km * fiber_db_per_km + n_connectors * connector_db + n_splices * splice_db \
        + penalties_db
    rx = tx_dbm - loss
    return {"loss_db": round(loss, 2), "rx_dbm": round(rx, 2),
            "margin_db": round(rx - rx_sensitivity_dbm, 2)}


# ------------------------------------------------------------------------------- task 6
def estimate_fabric_bom(spec: dict, policy: dict) -> dict:
    """Port, cable, optic and spares estimate for a rail-optimized 2-tier leaf-spine fabric.

    spec: nodes, rails, switch_radix, oversubscription (down:up), host_optic, fabric_optic.
    policy: optic_rate, cable_rate, min_per_type, spare_switches_per_model.
    One NIC port per rail per node; each link has an optic at both ends and one cable.
    """
    nodes, rails, radix = spec["nodes"], spec["rails"], spec["switch_radix"]
    osub = spec["oversubscription"]
    down_max = int(radix * osub / (1 + osub))
    leaves_per_rail = math.ceil(nodes / down_max)
    leaves = rails * leaves_per_rail
    host_links = nodes * rails
    down_per_leaf = math.ceil(nodes / leaves_per_rail)
    up_per_leaf = math.ceil(down_per_leaf / osub)
    if down_per_leaf + up_per_leaf > radix:
        raise ValueError("leaf radix exceeded")
    fabric_links = leaves * up_per_leaf
    spines = math.ceil(fabric_links / radix)
    while up_per_leaf % spines:
        spines += 1
    optics: dict[str, int] = {}
    for typ, n in ((spec["host_optic"], 2 * host_links), (spec["fabric_optic"], 2 * fabric_links)):
        optics[typ] = optics.get(typ, 0) + n
    cables = host_links + fabric_links
    spare_optics = {t: max(math.ceil(n * policy["optic_rate"]), policy["min_per_type"])
                    for t, n in optics.items()}
    return {
        "leaves": leaves, "spines": spines,
        "down_ports_per_leaf": down_per_leaf, "up_ports_per_leaf": up_per_leaf,
        "uplinks_per_leaf_per_spine": up_per_leaf // spines,
        "host_links": host_links, "fabric_links": fabric_links,
        "total_links": host_links + fabric_links,
        "optics": optics, "cables": cables,
        "leaf_ports_used": leaves * (down_per_leaf + up_per_leaf),
        "spine_ports_used": fabric_links,
        "free_leaf_ports": leaves * radix - leaves * (down_per_leaf + up_per_leaf),
        "free_spine_ports": spines * radix - fabric_links,
        "spare_optics": spare_optics,
        "spare_cables": max(math.ceil(cables * policy["cable_rate"]), policy["min_per_type"]),
        "spare_switches": policy["spare_switches_per_model"],
        "oversubscription_actual": down_per_leaf / up_per_leaf,
    }


def generate_cabling_schedule(spec: dict) -> list[dict]:
    """Cabling schedule rows for the fabric in ``spec`` (uses spec['prefix'] for names).

    Leaf ``{prefix}-leaf-r{r}`` (r = rail index, or ``r{r}-{i}`` if a rail needs >1 leaf):
    down ports Ethernet1..N to ``{prefix}-n{nn}:nic{r}`` (nn = 01..N); up ports start at
    Ethernet{down_max+1} and are spread round-robin-by-block across spines. Spine
    ``{prefix}-spine-{s}`` port numbers are allocated contiguously per leaf.
    Each row: cable_id, a_device, a_port, b_device, b_port, optic, label_a, label_b.
    """
    bom = estimate_fabric_bom(spec, {"optic_rate": 0, "cable_rate": 0, "min_per_type": 0,
                                     "spare_switches_per_model": 0})
    pre = spec["prefix"]
    radix, osub = spec["switch_radix"], spec["oversubscription"]
    down_max = int(radix * osub / (1 + osub))
    lpr = bom["leaves"] // spec["rails"]
    per_spine = bom["uplinks_per_leaf_per_spine"]
    rows: list[dict] = []

    def add(cid: str, ad: str, ap: str, bd: str, bp: str, optic: str) -> None:
        rows.append({"cable_id": cid, "a_device": ad, "a_port": ap, "b_device": bd, "b_port": bp,
                     "optic": optic, "label_a": f"{cid} | {ad}:{ap} -> {bd}:{bp}",
                     "label_b": f"{cid} | {bd}:{bp} -> {ad}:{ap}"})

    leaf_index = 0
    for r in range(spec["rails"]):
        for i in range(lpr):
            leaf = f"{pre}-leaf-r{r}" if lpr == 1 else f"{pre}-leaf-r{r}-{i}"
            first = i * bom["down_ports_per_leaf"]
            for j, n in enumerate(range(first, min(first + bom["down_ports_per_leaf"], spec["nodes"]))):
                add(f"H-r{r}-n{n + 1:02d}", leaf, f"Ethernet{j + 1}", f"{pre}-n{n + 1:02d}", f"nic{r}",
                    spec["host_optic"])
            for s in range(bom["spines"]):
                for k in range(per_spine):
                    up_port = down_max + 1 + s * per_spine + k
                    sp_port = leaf_index * per_spine + k + 1
                    add(f"F-r{r}-{i}-s{s + 1}-{k + 1}", leaf, f"Ethernet{up_port}",
                        f"{pre}-spine-{s + 1}", f"Ethernet{sp_port}", spec["fabric_optic"])
            leaf_index += 1
    return rows
