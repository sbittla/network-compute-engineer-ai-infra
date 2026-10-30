"""Capstone A reference implementation: ORION-256 cluster design model.

INSTRUCTOR EDITION. Same public API as starter-kit/starter/cluster_model.py, fully implemented.

Every value this module produces is [MODELED] from the inputs in starter-kit/data/ (which are
[ILLUSTRATIVE]). Nothing here is a measurement.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# ----------------------------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------------------------


def load_inputs(data_dir: str | Path) -> dict[str, Any]:
    """Load the design dataset.

    Returns a dict with keys ``design`` (design_inputs.yaml), ``facility`` (facility.yaml),
    ``floorplan`` (DataFrame from floorplan.csv) and ``hostfile`` (list of node names in launcher
    order).
    """
    d = Path(data_dir)
    design = yaml.safe_load((d / "design_inputs.yaml").read_text(encoding="utf-8"))
    facility = yaml.safe_load((d / "facility.yaml").read_text(encoding="utf-8"))
    floorplan = pd.read_csv(d / "floorplan.csv")
    hostfile = [ln.strip() for ln in (d / "hostfile_job4471.txt").read_text(encoding="utf-8").splitlines()
                if ln.strip()]
    return {"design": design, "facility": facility, "floorplan": floorplan, "hostfile": hostfile}


# ----------------------------------------------------------------------------------------------
# 1. Fabric topology counts
# ----------------------------------------------------------------------------------------------


def fabric_counts(option: dict, n_nodes: int, nics_per_node: int) -> dict[str, Any]:
    """Count switches, links and oversubscription for a two-tier leaf-spine backend option.

    Args:
        option: one entry of ``design['fabric_options']`` (style, radixes, downlinks/uplinks per leaf).
        n_nodes: GPU nodes attached to the backend fabric.
        nics_per_node: backend NICs (rails) per node.

    Returns:
        dict with n_leaves, n_spines, host_links, leaf_spine_links, uplinks_per_leaf_per_spine,
        oversubscription (downlink:uplink ratio as a float, 1.0 = non-blocking), switch_count,
        spine_ports_used, warnings (list of human-readable design-rule violations).
    """
    warnings: list[str] = []
    down, up = int(option["downlinks_per_leaf"]), int(option["uplinks_per_leaf"])
    leaf_radix, spine_radix = int(option["leaf_radix"]), int(option["spine_radix"])
    host_links = n_nodes * nics_per_node
    if down + up > leaf_radix:
        warnings.append(f"leaf uses {down + up} ports but radix is {leaf_radix}")
    n_leaves = math.ceil(host_links / down)
    if host_links % down:
        warnings.append(f"{host_links} host links do not divide evenly into {down} downlinks per leaf "
                        f"({host_links / down:.2f} leaves): leaves are unevenly loaded")
    if option["style"] == "rail":
        if n_leaves % nics_per_node:
            warnings.append(f"rail-optimized design needs a multiple of {nics_per_node} leaves "
                            f"(one or more per rail); got {n_leaves}: rails would share or split leaves")
        if down % n_nodes and n_nodes % down:
            warnings.append(f"{down} downlinks per leaf does not map whole rails ({n_nodes} nodes per rail)")
    elif option["style"] == "tor":
        if down % nics_per_node:
            warnings.append(f"ToR leaf with {down} downlinks cannot host whole {nics_per_node}-NIC nodes")
    leaf_spine_links = n_leaves * up
    n_spines = math.ceil(leaf_spine_links / spine_radix)
    if up % n_spines:
        warnings.append(f"{up} uplinks per leaf cannot be striped evenly over {n_spines} spines")
    per_spine = up // n_spines if n_spines else 0
    spine_ports_used = n_leaves * per_spine
    if spine_ports_used > spine_radix:
        warnings.append(f"spine needs {spine_ports_used} ports, radix {spine_radix}")
    return {
        "n_leaves": n_leaves,
        "n_spines": n_spines,
        "host_links": host_links,
        "leaf_spine_links": leaf_spine_links,
        "uplinks_per_leaf_per_spine": per_spine,
        "oversubscription": down / up,
        "switch_count": n_leaves + n_spines,
        "spine_ports_used": spine_ports_used,
        "warnings": warnings,
    }


def leaf_of(option: dict, counts: dict, n_nodes: int, nics_per_node: int, node: int, rail: int) -> int:
    """Return the leaf index that NIC ``rail`` of node index ``node`` (0-based) attaches to."""
    if option["style"] == "rail":
        leaves_per_rail = max(1, counts["n_leaves"] // nics_per_node)
        nodes_per_leaf = math.ceil(n_nodes / leaves_per_rail)
        return rail * leaves_per_rail + node // nodes_per_leaf
    nodes_per_leaf = int(option["downlinks_per_leaf"]) // nics_per_node
    return node // nodes_per_leaf


# ----------------------------------------------------------------------------------------------
# 2. Physical placement and cable plan
# ----------------------------------------------------------------------------------------------


def switch_racks(option: dict, counts: dict, floorplan: pd.DataFrame) -> dict[str, str]:
    """Map switch ids (``leaf0``…, ``spine0``…) to rack ids using the option's location policy.

    network_racks: switches are split evenly, in index order, across network racks (net-01, net-02 …).
    gpu_racks (ToR): leaf i sits in the i-th GPU rack (rack-01, rack-02 …).
    """
    net = sorted(floorplan.loc[floorplan["kind"] == "network", "rack"])
    gpu = sorted(floorplan.loc[floorplan["kind"] == "gpu", "rack"])
    out: dict[str, str] = {}
    for kind, n, loc in (("leaf", counts["n_leaves"], option["leaf_location"]),
                         ("spine", counts["n_spines"], option["spine_location"])):
        for i in range(n):
            if loc == "gpu_racks":
                out[f"{kind}{i}"] = gpu[i]
            else:
                per = math.ceil(n / len(net))
                out[f"{kind}{i}"] = net[i // per]
    return out


def cable_length_m(rack_a: str, rack_b: str, floorplan: pd.DataFrame, cabling: dict) -> tuple[float, int]:
    """Return (routed path in metres, purchased standard length in metres) between two racks.

    Same rack: ``in_rack_m``. Otherwise Manhattan distance between rack positions plus a tray drop
    at each end, plus ``slack_fraction``; then rounded *up* to the next standard length.
    """
    if rack_a == rack_b:
        path = float(cabling["in_rack_m"])
    else:
        fp = floorplan.set_index("rack")
        dx = abs(fp.at[rack_a, "x_m"] - fp.at[rack_b, "x_m"])
        dy = abs(fp.at[rack_a, "y_m"] - fp.at[rack_b, "y_m"])
        path = (dx + dy + 2 * cabling["tray_drop_m"]) * (1 + cabling["slack_fraction"])
    for std in cabling["standard_lengths_m"]:
        if std >= path - 1e-9:
            return path, int(std)
    raise ValueError(f"no standard length covers {path:.1f} m")


def choose_media(length_m: float, catalog: dict) -> str:
    """Cheapest medium whose reach covers the purchased length: 'dac', 'mm' or 'sm'."""
    if length_m <= catalog["dac_400g"]["reach_m"]:
        return "dac"
    if length_m <= catalog["xcvr_400g_mm"]["reach_m"]:
        return "mm"
    if length_m <= catalog["xcvr_400g_sm"]["reach_m"]:
        return "sm"
    raise ValueError(f"{length_m} m exceeds every medium in the catalog")


def cable_plan(inputs: dict, option_name: str) -> pd.DataFrame:
    """Enumerate every backend link of a fabric option with its length and medium.

    Returns a DataFrame with one row per link and columns:
    link_type ('host' or 'fabric'), end_a, rack_a, end_b, rack_b, path_m, length_m, media
    ('dac'|'mm'|'sm'), transceivers (0 for DAC, 2 for optics), switch_ends (number of link ends
    that terminate on a switch: 1 for host links, 2 for fabric links).
    """
    design, fac, fp = inputs["design"], inputs["facility"], inputs["floorplan"]
    cl, cat = design["cluster"], design["catalog"]
    opt = design["fabric_options"][option_name]
    counts = fabric_counts(opt, cl["n_nodes"], cl["nics_per_node"])
    racks = switch_racks(opt, counts, fp)
    gpu_racks = sorted(fp.loc[fp["kind"] == "gpu", "rack"])
    rows = []

    def add(link_type: str, a: str, ra: str, b: str, rb: str, ends: int) -> None:
        path, length = cable_length_m(ra, rb, fp, fac["cabling"])
        media = choose_media(length, cat)
        rows.append({"link_type": link_type, "end_a": a, "rack_a": ra, "end_b": b, "rack_b": rb,
                     "path_m": round(path, 2), "length_m": length, "media": media,
                     "transceivers": 0 if media == "dac" else 2, "switch_ends": ends})

    for n in range(cl["n_nodes"]):
        node_rack = gpu_racks[n // cl["nodes_per_gpu_rack"]]
        for r in range(cl["nics_per_node"]):
            leaf = leaf_of(opt, counts, cl["n_nodes"], cl["nics_per_node"], n, r)
            add("host", f"node{n}.nic{r}", node_rack, f"leaf{leaf}", racks[f"leaf{leaf}"], 1)
    for i in range(counts["n_leaves"]):
        for j in range(counts["n_spines"]):
            for _ in range(counts["uplinks_per_leaf_per_spine"]):
                add("fabric", f"leaf{i}", racks[f"leaf{i}"], f"spine{j}", racks[f"spine{j}"], 2)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# 3. Power and cooling
# ----------------------------------------------------------------------------------------------


def feed_usable_kw(feed: dict, power_factor: float, derate: float) -> float:
    """Usable continuous kW of one feed: sqrt(3)·V·I (3-phase) or V·I (1-phase) × PF × derate."""
    kva = (math.sqrt(3) if int(feed["phases"]) == 3 else 1.0) * feed["voltage_v"] * feed["breaker_a"] / 1000.0
    return kva * power_factor * derate


def rack_power(inputs: dict, option_name: str, cables: pd.DataFrame) -> pd.DataFrame:
    """Per-rack IT power (max and sustained, kW) and 2N feed check.

    Switch power = base watts + switch-side transceiver watts (host-side optics are inside node power).
    Returns columns: rack, position, row, kind, max_kw, sustained_kw, feed_usable_kw, ok_2n_max,
    ok_2n_sustained.
    """
    design, fac, fp = inputs["design"], inputs["facility"], inputs["floorplan"]
    cl, cat = design["cluster"], design["catalog"]
    opt = design["fabric_options"][option_name]
    counts = fabric_counts(opt, cl["n_nodes"], cl["nics_per_node"])
    sw_rack = switch_racks(opt, counts, fp)
    xw = {"dac": 0.0, "mm": cat["xcvr_400g_mm"]["watts"], "sm": cat["xcvr_400g_sm"]["watts"]}
    sw_watts = {s: float(cat["switch_64x400g"]["watts"]) for s in sw_rack}
    for _, c in cables.iterrows():
        for end in ("end_a", "end_b"):
            if c[end] in sw_watts:
                sw_watts[c[end]] += xw[c["media"]]
    max_w = {r: 0.0 for r in fp["rack"]}
    sus_w = dict(max_w)
    for r in fp.loc[fp["kind"] == "gpu", "rack"]:
        max_w[r] += cl["nodes_per_gpu_rack"] * cat["node_hx8"]["watts_max"]
        sus_w[r] += cl["nodes_per_gpu_rack"] * cat["node_hx8"]["watts_sustained"]
    for s, w in sw_watts.items():
        max_w[sw_rack[s]] += w
        sus_w[sw_rack[s]] += w
    # fixed items: storage in storage racks, everything else in the mgmt rack
    stor = sorted(fp.loc[fp["kind"] == "storage", "rack"])
    mgmt = sorted(fp.loc[fp["kind"] == "mgmt", "rack"])
    for it in design["fixed_items"]:
        w = it["qty"] * it["watts"]
        if not w:
            continue
        targets = stor if it["item"].startswith("storage") else mgmt
        for t in targets:
            max_w[t] += w / len(targets)
            sus_w[t] += w / len(targets)
    rows = []
    for _, f in fp.iterrows():
        feed = feed_usable_kw(fac["positions"][f["position"]], fac["power_factor"], fac["continuous_load_derate"])
        mk, sk = max_w[f["rack"]] / 1000, sus_w[f["rack"]] / 1000
        rows.append({"rack": f["rack"], "position": f["position"], "row": f["row"], "kind": f["kind"],
                     "max_kw": round(mk, 3), "sustained_kw": round(sk, 3), "feed_usable_kw": round(feed, 2),
                     "ok_2n_max": mk <= feed, "ok_2n_sustained": sk <= feed})
    return pd.DataFrame(rows)


def cooling_check(inputs: dict, power: pd.DataFrame) -> pd.DataFrame:
    """Per-row heat load (max kW, all IT power becomes heat) against N+1 cooling capacity.

    Returns columns: row, heat_kw, usable_kw (= (units − 1) × unit_kw for N+1), headroom_kw, ok.
    """
    rows = []
    for row, spec in inputs["facility"]["cooling_rows"].items():
        heat = float(power.loc[power["row"] == row, "max_kw"].sum())
        spare = 1 if spec.get("redundancy", "N+1") == "N+1" else 0
        usable = (spec["units"] - spare) * spec["unit_kw"]
        rows.append({"row": row, "heat_kw": round(heat, 3), "usable_kw": float(usable),
                     "headroom_kw": round(usable - heat, 3), "ok": heat <= usable})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# 4. Workload / communication model
# ----------------------------------------------------------------------------------------------


def rank_layout(node_order: list[int], pp: int, dp: int, scheme: str) -> dict[tuple[int, int], int]:
    """Map (pipeline stage s, data-parallel index d) → node index. One node = one TP=8 group.

    ``node_order`` is the launcher's node order (node indices). Logical slot k is filled by
    node_order[k] where k = s·dp + d for 'dp_contiguous' and k = d·pp + s for 'pp_contiguous'.
    """
    if len(node_order) < pp * dp:
        raise ValueError("not enough nodes for pp × dp")
    out = {}
    for s in range(pp):
        for d in range(dp):
            k = s * dp + d if scheme == "dp_contiguous" else d * pp + s
            out[(s, d)] = node_order[k]
    return out


def _flows(layout: dict, pp: int, dp: int, nics: int, traffic: str) -> list[tuple[int, int, int]]:
    flows = []
    for r in range(nics):
        if traffic == "dp" and dp > 1:
            for s in range(pp):
                for d in range(dp):
                    flows.append((layout[(s, d)], layout[(s, (d + 1) % dp)], r))
        elif traffic == "pp":
            for d in range(dp):
                for s in range(pp - 1):
                    flows.append((layout[(s, d)], layout[(s + 1, d)], r))
    return flows


def contention(option: dict, counts: dict, n_nodes: int, nics_per_node: int,
               layout: dict, pp: int, dp: int, traffic: str) -> dict[str, float]:
    """Leaf-uplink contention for one traffic class.

    Model: every flow wants the full NIC rate; a ring (DP) sends one flow per (stage, rail) hop;
    PP sends forward activations stage s → s+1 on each rail. A flow whose endpoints sit on
    different leaves consumes one NIC-rate unit on the source leaf's uplinks and on the destination
    leaf's downlinks-from-spine. ECMP is assumed to spread perfectly (optimistic).

    Returns max_up_flows, max_down_flows, uplinks_per_leaf, contention_factor
    (= max(1, max(max_up, max_down) / uplinks_per_leaf)).
    """
    up: dict[int, int] = {}
    down: dict[int, int] = {}
    for a, b, r in _flows(layout, pp, dp, nics_per_node, traffic):
        la = leaf_of(option, counts, n_nodes, nics_per_node, a, r)
        lb = leaf_of(option, counts, n_nodes, nics_per_node, b, r)
        if la != lb:
            up[la] = up.get(la, 0) + 1
            down[lb] = down.get(lb, 0) + 1
    mu, md = max(up.values(), default=0), max(down.values(), default=0)
    upl = int(option["uplinks_per_leaf"])
    return {"max_up_flows": mu, "max_down_flows": md, "uplinks_per_leaf": upl,
            "contention_factor": max(1.0, max(mu, md) / upl)}


def comm_step_model(design: dict, scenario_name: str, option_name: str, node_order: list[int],
                    scheme: str) -> dict[str, float]:
    """W-TRAIN step-time model for one scenario × fabric option × rank layout.

    DP bytes per GPU per step: 'dp_allreduce' ring = 2(n−1)/n × S_grad;
    'zero3' = 3(n−1)/n × S_param (all-gather fwd + all-gather bwd + reduce-scatter grads),
    where S = params/(tp·pp) × bytes. PP bytes per GPU per boundary per direction =
    tokens_per_replica × hidden × bytes / tp (scatter/gather across TP ranks).
    Comm time = bytes / (NIC GB/s × busbw_efficiency / contention).
    Compute time = 6·N·tokens / (GPUs × peak × MFU). Exposure (docs/VERIFIED_FACTS.md): with PP > 1 only
    the last micro-batch's backward hides the DP collective, so exposed = max(0, dp_time − dp_overlap_window_s)
    (≈ 70 ms on W-TRAIN); PP send/recv is assumed hidden inside the 1F1B schedule (already inside MFU).
    With PP = 1 (FSDP variation) exposed = exposed_comm_fraction_fsdp × dp_time. Step = compute + exposed.
    All outputs [MODELED].
    """
    cl, wl = design["cluster"], design["workload"]
    sc = wl["scenarios"][scenario_name]
    opt = design["fabric_options"][option_name]
    counts = fabric_counts(opt, cl["n_nodes"], cl["nics_per_node"])
    tp, pp, dp = sc["tp"], sc["pp"], sc["dp"]
    n_gpus = cl["n_nodes"] * cl["gpus_per_node"]
    layout = rank_layout(node_order, pp, dp, scheme)
    nic_GBps = cl["nic_gbps"] / 8.0
    eff_GBps = nic_GBps * wl["busbw_efficiency"]
    shard_params = wl["params"] / (tp * pp)
    if sc["sharding"] == "zero3":
        dp_bytes = 3 * (dp - 1) / dp * shard_params * wl["bytes_per_param_bf16"]
    else:
        dp_bytes = 2 * (dp - 1) / dp * shard_params * wl["bytes_per_grad"]
    tokens = wl["seq_len"] * wl["global_batch_seqs"]
    pp_bytes = 0.0 if pp == 1 else tokens / dp * wl["hidden"] * wl["bytes_per_activation"] / tp
    c_dp = contention(opt, counts, cl["n_nodes"], cl["nics_per_node"], layout, pp, dp, "dp")["contention_factor"]
    c_pp = contention(opt, counts, cl["n_nodes"], cl["nics_per_node"], layout, pp, dp, "pp")["contention_factor"]
    dp_time = dp_bytes / 1e9 / (eff_GBps / c_dp)
    pp_time = pp_bytes / 1e9 / (eff_GBps / c_pp)
    compute = 6 * wl["params"] * tokens / (n_gpus * wl["gpu_peak_flops"] * wl["mfu"])
    if pp > 1:
        exposed = max(0.0, dp_time - wl["dp_overlap_window_s"])
    else:  # FSDP variation: per-layer prefetch overlaps most traffic; fraction is an ILLUSTRATIVE assumption
        exposed = wl["exposed_comm_fraction_fsdp"] * dp_time
    return {"dp_bytes_per_gpu": dp_bytes, "pp_bytes_per_gpu": pp_bytes, "dp_contention": c_dp,
            "pp_contention": c_pp, "dp_time_s": dp_time, "pp_time_s": pp_time, "compute_time_s": compute,
            "exposed_comm_s": exposed, "step_time_s": compute + exposed, "tokens_per_step": float(tokens)}


def hostfile_order(hostfile: list[str]) -> list[int]:
    """Convert node names ``orion-nNN`` (1-based) to 0-based node indices, preserving order."""
    return [int(h.rsplit("-n", 1)[1]) - 1 for h in hostfile]


# ----------------------------------------------------------------------------------------------
# 5. Bill of materials, acceptance counts, cost/performance
# ----------------------------------------------------------------------------------------------


def bom(inputs: dict, option_name: str, cables: pd.DataFrame) -> pd.DataFrame:
    """Bill of materials with columns item, qty, unit_usd, ext_usd (USD, [ILLUSTRATIVE] prices).

    Fiber lines are priced per link (base + per-metre × purchased length); their unit_usd is the mean.
    """
    design = inputs["design"]
    cl, cat = design["cluster"], design["catalog"]
    counts = fabric_counts(design["fabric_options"][option_name], cl["n_nodes"], cl["nics_per_node"])
    rows = [("node_hx8", cl["n_nodes"], cat["node_hx8"]["usd"]),
            ("switch_64x400g", counts["switch_count"], cat["switch_64x400g"]["usd"])]
    for media, key in (("mm", "xcvr_400g_mm"), ("sm", "xcvr_400g_sm")):
        n = int(cables.loc[cables["media"] == media, "transceivers"].sum())
        rows.append((key, n, cat[key]["usd"]))
    rows.append(("dac_400g", int((cables["media"] == "dac").sum()), cat["dac_400g"]["usd"]))
    out = [{"item": i, "qty": q, "unit_usd": float(u), "ext_usd": float(q * u)} for i, q, u in rows]
    for media, key in (("mm", "fiber_mm"), ("sm", "fiber_sm")):
        sel = cables.loc[cables["media"] == media, "length_m"]
        ext = float((cat[key]["usd_base"] + cat[key]["usd_per_m"] * sel).sum())
        out.append({"item": key, "qty": int(len(sel)), "unit_usd": ext / len(sel) if len(sel) else 0.0,
                    "ext_usd": ext})
    for it in design["fixed_items"]:
        out.append({"item": it["item"], "qty": it["qty"], "unit_usd": float(it["usd"]),
                    "ext_usd": float(it["qty"] * it["usd"])})
    return pd.DataFrame(out)


def acceptance_counts(cables: pd.DataFrame, n_nodes: int, nics_per_node: int) -> dict[str, int]:
    """Size the physical/fabric acceptance campaign.

    Returns links_total, optical_links, dac_links, transceivers, nodes, rail_neighbor_pairs
    (pairwise RDMA bandwidth tests between ring neighbours on every rail = n_nodes × nics_per_node).
    """
    return {"links_total": int(len(cables)),
            "optical_links": int((cables["media"] != "dac").sum()),
            "dac_links": int((cables["media"] == "dac").sum()),
            "transceivers": int(cables["transceivers"].sum()),
            "nodes": n_nodes,
            "rail_neighbor_pairs": n_nodes * nics_per_node}


def cost_per_million_tokens(design: dict, capex_usd: float, it_kw_sustained: float, pue: float,
                            step_time_s: float, tokens_per_step: float) -> dict[str, float]:
    """Training cost per million tokens [MODELED].

    usd_per_hour = capex / (years × 8760) + IT kW × PUE × $/kWh; tokens/hour = tokens_per_step ×
    3600 / step_time; usd_per_million_tokens = usd_per_hour / tokens_per_hour × 1e6.
    """
    ec = design["economics"]
    capex_h = capex_usd / (ec["amortization_years"] * ec["hours_per_year"])
    power_h = it_kw_sustained * pue * ec["usd_per_kwh"]
    tph = tokens_per_step * 3600.0 / step_time_s
    return {"capex_usd": capex_usd, "usd_per_hour_capex": capex_h, "usd_per_hour_power": power_h,
            "usd_per_hour": capex_h + power_h, "tokens_per_hour": tph,
            "usd_per_million_tokens": (capex_h + power_h) / tph * 1e6}
