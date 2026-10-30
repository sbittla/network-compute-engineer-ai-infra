"""Capstone A starter: ORION-256 cluster design model.

Implement each function marked TODO. Run ``python check.py`` from starter-kit/ after each one; the
checker reports TODO for functions that still raise NotImplementedError.

Everything this module produces is [MODELED] from the [ILLUSTRATIVE] inputs in data/. Label it that
way in your design pack. Nothing here is a measurement of real hardware.
"""
from __future__ import annotations

import math  # noqa: F401  (you will need it)
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# ----------------------------------------------------------------------------------------------
# Loading (provided)
# ----------------------------------------------------------------------------------------------


def load_inputs(data_dir: str | Path) -> dict[str, Any]:
    """Load the design dataset (provided — do not change the return shape).

    Returns a dict with keys ``design`` (design_inputs.yaml), ``facility`` (facility.yaml),
    ``floorplan`` (DataFrame from floorplan.csv) and ``hostfile`` (node names in launcher order).
    """
    d = Path(data_dir)
    design = yaml.safe_load((d / "design_inputs.yaml").read_text(encoding="utf-8"))
    facility = yaml.safe_load((d / "facility.yaml").read_text(encoding="utf-8"))
    floorplan = pd.read_csv(d / "floorplan.csv")
    hostfile = [ln.strip() for ln in (d / "hostfile_job4471.txt").read_text(encoding="utf-8").splitlines()
                if ln.strip()]
    return {"design": design, "facility": facility, "floorplan": floorplan, "hostfile": hostfile}


def hostfile_order(hostfile: list[str]) -> list[int]:
    """Convert node names ``orion-nNN`` (1-based) to 0-based node indices, preserving order (provided)."""
    return [int(h.rsplit("-n", 1)[1]) - 1 for h in hostfile]


# ----------------------------------------------------------------------------------------------
# 1. Fabric topology counts
# ----------------------------------------------------------------------------------------------


def fabric_counts(option: dict, n_nodes: int, nics_per_node: int) -> dict[str, Any]:
    """Count switches, links and oversubscription for a two-tier leaf-spine backend option.

    Args:
        option: one entry of ``design['fabric_options']`` with keys style ('rail' | 'tor'),
            leaf_radix, downlinks_per_leaf, uplinks_per_leaf, spine_radix.
        n_nodes: GPU nodes on the backend fabric (32 for ORION-256).
        nics_per_node: backend NICs (= rails) per node (8).

    Returns a dict with:
        n_leaves, n_spines, host_links, leaf_spine_links, uplinks_per_leaf_per_spine,
        oversubscription (downlinks/uplinks as float; 1.0 = non-blocking), switch_count,
        spine_ports_used, warnings (list[str] of design-rule violations; empty if clean).

    TODO:
      1. host_links = n_nodes × nics_per_node; n_leaves = ceil(host_links / downlinks_per_leaf).
      2. leaf_spine_links = n_leaves × uplinks_per_leaf; n_spines = ceil(leaf_spine_links / spine_radix).
      3. uplinks_per_leaf_per_spine = uplinks_per_leaf // n_spines.
      4. Raise *warnings* (do not throw) for at least: host links not dividing evenly into leaves;
         a 'rail' design whose leaf count is not a multiple of nics_per_node (rails would share or
         split leaves); uplinks that cannot be striped evenly over spines; port counts exceeding radix.
    """
    raise NotImplementedError("fabric_counts: count leaves/spines/links and raise design-rule warnings")


def leaf_of(option: dict, counts: dict, n_nodes: int, nics_per_node: int, node: int, rail: int) -> int:
    """Return the leaf index that NIC ``rail`` of 0-based node ``node`` attaches to.

    TODO:
      * 'rail' style: leaves_per_rail = n_leaves // nics_per_node (≥ 1); nodes are split evenly over
        a rail's leaves; leaf = rail × leaves_per_rail + node // ceil(n_nodes / leaves_per_rail).
      * 'tor' style: nodes_per_leaf = downlinks_per_leaf // nics_per_node; leaf = node // nodes_per_leaf
        (every rail of a node lands on the same ToR leaf).
    """
    raise NotImplementedError("leaf_of: map (node, rail) to a leaf for rail and ToR styles")


# ----------------------------------------------------------------------------------------------
# 2. Physical placement and cable plan
# ----------------------------------------------------------------------------------------------


def switch_racks(option: dict, counts: dict, floorplan: pd.DataFrame) -> dict[str, str]:
    """Map switch ids (``leaf0``…, ``spine0``…) to rack ids (provided — this is the placement policy).

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

    TODO:
      * Same rack → path = cabling['in_rack_m'].
      * Different racks → path = (|Δx| + |Δy| + 2 × tray_drop_m) × (1 + slack_fraction), using the
        x_m / y_m columns of the floorplan (overhead tray, Manhattan routing).
      * Purchased length = smallest value in cabling['standard_lengths_m'] that is ≥ path.
    """
    raise NotImplementedError("cable_length_m: Manhattan tray routing + slack, round up to stock length")


def choose_media(length_m: float, catalog: dict) -> str:
    """Return the cheapest medium whose reach covers the purchased length: 'dac', 'mm' or 'sm'.

    TODO: compare against catalog['dac_400g']['reach_m'], ['xcvr_400g_mm']['reach_m'],
    ['xcvr_400g_sm']['reach_m'] in that order; raise ValueError if nothing reaches.
    """
    raise NotImplementedError("choose_media: DAC if within copper reach, else MM, else SM")


def cable_plan(inputs: dict, option_name: str) -> pd.DataFrame:
    """Enumerate every backend link of a fabric option with its length and medium.

    Returns one row per link with columns: link_type ('host' | 'fabric'), end_a, rack_a, end_b,
    rack_b, path_m, length_m, media ('dac' | 'mm' | 'sm'), transceivers (0 for DAC, 2 for an optical
    link), switch_ends (1 for host links, 2 for leaf–spine links).

    TODO:
      1. counts = fabric_counts(...); racks = switch_racks(...).
      2. Node n (0-based) lives in GPU rack sorted(gpu racks)[n // nodes_per_gpu_rack].
      3. Host links: for every node n and rail r, link 'node{n}.nic{r}' → f'leaf{leaf_of(...)}'.
      4. Fabric links: for every leaf i, spine j, repeat uplinks_per_leaf_per_spine times.
      5. Length via cable_length_m, medium via choose_media.
    """
    raise NotImplementedError("cable_plan: enumerate host and fabric links with length and medium")


# ----------------------------------------------------------------------------------------------
# 3. Power and cooling
# ----------------------------------------------------------------------------------------------


def feed_usable_kw(feed: dict, power_factor: float, derate: float) -> float:
    """Usable continuous kW of ONE feed.

    feed has phases (1 or 3), voltage_v (line-to-line for 3-phase) and breaker_a.
    TODO: kVA = √3 × V × I / 1000 for 3-phase (V × I / 1000 for 1-phase); kW = kVA × PF × derate.
    Beware: the facility sheet gives amps and volts, not kW. kVA is not kW.
    """
    raise NotImplementedError("feed_usable_kw: sqrt(3)*V*I*PF*derate for 3-phase feeds")


def rack_power(inputs: dict, option_name: str, cables: pd.DataFrame) -> pd.DataFrame:
    """Per-rack IT power (kW) and 2N feed check.

    Returns columns: rack, position, row, kind, max_kw, sustained_kw, feed_usable_kw, ok_2n_max,
    ok_2n_sustained.

    TODO:
      1. GPU racks: nodes_per_gpu_rack × node watts_max (and watts_sustained).
      2. Every switch: catalog switch base watts + the watts of each transceiver plugged into it
         (one per optical link end that terminates on that switch; DACs draw ~0 W). Host-side optics
         are already inside node power. Add each switch to the rack switch_racks() puts it in.
      3. fixed_items: storage_* items split evenly over storage racks; everything else in the mgmt rack.
      4. 2N: facility['power_redundancy'] is '2N' — EITHER feed alone must carry the whole rack, so
         compare rack kW to feed_usable_kw(one feed), not to two feeds.
    """
    raise NotImplementedError("rack_power: sum node, switch and optic power per rack; check 2N")


def cooling_check(inputs: dict, power: pd.DataFrame) -> pd.DataFrame:
    """Per-row heat load against cooling capacity with N+1 redundancy.

    Returns columns: row, heat_kw (sum of max_kw in the row), usable_kw ((units − 1) × unit_kw for
    'N+1'), headroom_kw, ok.

    TODO: treat all IT power as heat; design to max_kw, not sustained.
    """
    raise NotImplementedError("cooling_check: row heat vs (units-1) x unit_kw")


# ----------------------------------------------------------------------------------------------
# 4. Workload / communication model
# ----------------------------------------------------------------------------------------------


def rank_layout(node_order: list[int], pp: int, dp: int, scheme: str) -> dict[tuple[int, int], int]:
    """Map (pipeline stage s, data-parallel index d) → node index. One node = one TP=8 group.

    TODO: logical slot k = s·dp + d for 'dp_contiguous', k = d·pp + s for 'pp_contiguous';
    the node in slot k is node_order[k].
    """
    raise NotImplementedError("rank_layout: place (stage, dp-index) pairs onto the launcher's node order")


def contention(option: dict, counts: dict, n_nodes: int, nics_per_node: int,
               layout: dict, pp: int, dp: int, traffic: str) -> dict[str, float]:
    """Leaf-uplink contention for one traffic class ('dp' or 'pp').

    Model (state it in your assumptions register): every flow wants the full NIC rate.
      * 'dp': for each stage s and rail r, a ring over d = 0..dp−1 sends one flow
        layout[(s, d)] → layout[(s, (d+1) % dp)] on rail r (no flows if dp == 1).
      * 'pp': for each d and rail r, forward activations layout[(s, d)] → layout[(s+1, d)].
    A flow whose endpoints are on different leaves (use leaf_of with that rail) adds 1 to the
    source leaf's up-count and 1 to the destination leaf's down-count. Assume perfect ECMP.

    Returns max_up_flows, max_down_flows, uplinks_per_leaf,
    contention_factor = max(1, max(max_up, max_down) / uplinks_per_leaf).
    """
    raise NotImplementedError("contention: count cross-leaf flows per leaf and compare with uplinks")


def comm_step_model(design: dict, scenario_name: str, option_name: str, node_order: list[int],
                    scheme: str) -> dict[str, float]:
    """W-TRAIN step-time model for one scenario × fabric option × rank layout. All outputs [MODELED].

    Returns dp_bytes_per_gpu, pp_bytes_per_gpu, dp_contention, pp_contention, dp_time_s, pp_time_s,
    compute_time_s, exposed_comm_s, step_time_s, tokens_per_step.

    TODO (bytes per GPU per step):
      * S = params / (tp × pp) parameters held per GPU.
      * 'dp_allreduce': ring all-reduce of BF16 grads → 2(n−1)/n × S × bytes_per_grad.
      * 'zero3': all-gather (fwd) + all-gather (bwd) + reduce-scatter (grads) → 3(n−1)/n × S × 2 B.
      * PP (pp > 1): tokens_per_replica × hidden × bytes_per_activation / tp per boundary per direction
        (Megatron-style scatter/gather across the TP group); tokens_per_replica = seq_len ×
        global_batch_seqs / dp.
      * time = bytes / (nic_gbps/8 GB/s × busbw_efficiency / contention_factor).
      * compute = 6 × params × tokens_per_step / (n_gpus × gpu_peak_flops × mfu).
      * exposure: if pp > 1, exposed = max(0, dp_time − dp_overlap_window_s) — only the last micro-batch's
        backward can hide the DP collective (≈ 70 ms on W-TRAIN, docs/VERIFIED_FACTS.md); PP send/recv is
        assumed hidden in the 1F1B schedule. If pp == 1 (FSDP variation), exposed =
        exposed_comm_fraction_fsdp × dp_time.
      * step = compute + exposed.
    """
    raise NotImplementedError("comm_step_model: bytes, contention, comm time and step time")


# ----------------------------------------------------------------------------------------------
# 5. Bill of materials, acceptance counts, cost/performance
# ----------------------------------------------------------------------------------------------


def bom(inputs: dict, option_name: str, cables: pd.DataFrame) -> pd.DataFrame:
    """Bill of materials: columns item, qty, unit_usd, ext_usd ([ILLUSTRATIVE] USD).

    TODO lines: node_hx8; switch_64x400g (switch_count); xcvr_400g_mm and xcvr_400g_sm (count
    transceivers, i.e. 2 per optical link); dac_400g (one per DAC link); fiber_mm and fiber_sm priced
    per link as usd_base + usd_per_m × length_m (unit_usd = mean); every entry in fixed_items.
    """
    raise NotImplementedError("bom: compute line items from counts, cable plan and catalog")


def acceptance_counts(cables: pd.DataFrame, n_nodes: int, nics_per_node: int) -> dict[str, int]:
    """Size the physical/fabric acceptance campaign.

    TODO: return links_total, optical_links, dac_links, transceivers, nodes, and rail_neighbor_pairs
    (one RDMA bandwidth test per ring-neighbour pair per rail = n_nodes × nics_per_node).
    """
    raise NotImplementedError("acceptance_counts: count links, optics and pairwise tests")


def cost_per_million_tokens(design: dict, capex_usd: float, it_kw_sustained: float, pue: float,
                            step_time_s: float, tokens_per_step: float) -> dict[str, float]:
    """Training cost per million tokens [MODELED].

    TODO: usd_per_hour_capex = capex / (amortization_years × hours_per_year);
    usd_per_hour_power = it_kw_sustained × pue × usd_per_kwh; tokens_per_hour = tokens_per_step ×
    3600 / step_time_s; usd_per_million_tokens = usd_per_hour / tokens_per_hour × 1e6.
    Return capex_usd, usd_per_hour_capex, usd_per_hour_power, usd_per_hour, tokens_per_hour,
    usd_per_million_tokens.
    """
    raise NotImplementedError("cost_per_million_tokens: amortized capex + energy over token throughput")
