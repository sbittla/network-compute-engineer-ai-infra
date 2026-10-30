#!/usr/bin/env python3
"""Chapter 7 lab -- fabric design and validation tool (REFERENCE SOLUTION, instructor only).

Five jobs, mirroring what a fabric engineer does before and after a build:

1. ``size_two_tier``        -- leaf/spine counts, oversubscription and cabling from port assumptions
2. ``build_addressing_plan`` -- /31 plan for every host and fabric link of ORION-256's backend
3. ``build_bgp_neighbors``   -- RFC 7938-style eBGP neighbor table (one session per fabric link)
4. ``validate_intent``       -- catch errors in a supplied (flawed) fabric intent dataset
5. ``fabric_capacity``       -- uplink, ECMP-aware ingress and bisection capacity after failures

All bandwidth values are in Gb/s (bits). Everything is [MODELED]: no packets are sent.
"""
from __future__ import annotations

import argparse
import csv
import ipaddress
import itertools
import math
from collections import defaultdict
from pathlib import Path

SPINE_ASN = 65100
LEAF_ASN_BASE = 65101
SWITCH_MTU = 9216
HOST_MTU = 9000


# --------------------------------------------------------------------------------------------
# Provided helpers (identical in starter and solution)
# --------------------------------------------------------------------------------------------
def load_intent(data_dir: Path) -> dict[str, list[dict]]:
    """Load devices.csv, links.csv and advertisements.csv into lists of dicts with typed fields."""
    data_dir = Path(data_dir)
    out: dict[str, list[dict]] = {}
    for name in ("devices", "links", "advertisements"):
        with (data_dir / f"{name}.csv").open(newline="", encoding="utf-8") as fh:
            out[name] = list(csv.DictReader(fh))
    for d in out["devices"]:
        d["asn"] = int(d["asn"])
        d["ecmp_max_paths"] = int(d["ecmp_max_paths"])
        d["rail"] = int(d["rail"]) if d["rail"] != "" else None
    for link in out["links"]:
        link["a_mtu"] = int(link["a_mtu"])
        link["b_mtu"] = int(link["b_mtu"])
        link["speed_gbps"] = int(link["speed_gbps"])
    return out


def link_matrix(n_leaves: int, n_spines: int, links_per_pair: int,
                failed_links: tuple[tuple[int, int], ...] = (),
                failed_spines: tuple[int, ...] = (),
                failed_leaves: tuple[int, ...] = ()) -> list[list[int]]:
    """Return c[leaf][spine] = number of healthy parallel links (0-based leaf and spine indices).

    ``failed_links`` lists (leaf, spine) pairs; each entry removes ONE link from that pair.
    """
    c = [[links_per_pair] * n_spines for _ in range(n_leaves)]
    for leaf, spine in failed_links:
        c[leaf][spine] = max(0, c[leaf][spine] - 1)
    for spine in failed_spines:
        for leaf in range(n_leaves):
            c[leaf][spine] = 0
    for leaf in failed_leaves:
        c[leaf] = [0] * n_spines
    return c


# --------------------------------------------------------------------------------------------
# Task 1 -- sizing
# --------------------------------------------------------------------------------------------
def size_two_tier(endpoints: int, leaf_ports: int, spine_ports: int, oversub: float = 1.0,
                  link_gbps: int = 400, min_spines: int = 2, down_gbps: int | None = None) -> dict:
    """Size a two-tier leaf-spine (folded Clos) fabric. See the starter docstring for the contract."""
    down = int(round(leaf_ports * oversub / (1.0 + oversub)))
    up = leaf_ports - down
    down_gbps = link_gbps if down_gbps is None else down_gbps
    max_endpoints = spine_ports * down  # each leaf: one link to each of `up` spines
    leaves = math.ceil(endpoints / down)
    result = {
        "down_per_leaf": down, "up_per_leaf": up, "oversubscription": down / up,
        "bandwidth_oversubscription": (down * down_gbps) / (up * link_gbps),
        "leaves": leaves, "max_endpoints_two_tier": max_endpoints,
        "feasible": endpoints <= max_endpoints,
        "spines": None, "links_per_leaf_spine": None,
        "host_cables": endpoints, "fabric_cables": None, "total_cables": None,
        "transceivers": None, "leaf_uplink_gbps": up * link_gbps,
    }
    if not result["feasible"]:
        return result
    total_up = leaves * up
    spines = max(min_spines, math.ceil(total_up / spine_ports))
    while spines <= up and up % spines != 0:
        spines += 1
    if spines > up or leaves * (up // spines) > spine_ports:
        result["feasible"] = False
        return result
    result.update({
        "spines": spines, "links_per_leaf_spine": up // spines,
        "fabric_cables": total_up, "total_cables": endpoints + total_up,
        "transceivers": 2 * (endpoints + total_up),
    })
    return result


# --------------------------------------------------------------------------------------------
# Task 2 -- addressing plan
# --------------------------------------------------------------------------------------------
def build_addressing_plan(nodes: int = 32, rails: int = 8, spines: int = 4,
                          links_per_pair: int = 8) -> list[dict]:
    """Return one row per point-to-point link (host links first, then fabric links)."""
    rows: list[dict] = []
    for r in range(rails):
        for n in range(1, nodes + 1):
            rows.append({
                "link_id": f"H-r{r}-n{n:02d}", "link_type": "host",
                "a_device": f"orion-be-leaf-r{r}", "a_port": f"Ethernet{n}", "a_ip": f"10.100.{r}.{2 * n}/31",
                "b_device": f"orion-n{n:02d}", "b_port": f"nic{r}", "b_ip": f"10.100.{r}.{2 * n + 1}/31",
                "subnet": f"10.100.{r}.{2 * n}/31",
            })
    for r in range(rails):
        for s in range(1, spines + 1):
            for k in range(links_per_pair):
                idx = r * links_per_pair + k
                rows.append({
                    "link_id": f"F-r{r}-s{s}-k{k}", "link_type": "fabric",
                    "a_device": f"orion-be-leaf-r{r}", "a_port": f"Ethernet{33 + (s - 1) * links_per_pair + k}",
                    "a_ip": f"10.101.{s}.{2 * idx + 1}/31",
                    "b_device": f"orion-be-spine-{s}", "b_port": f"Ethernet{1 + idx}",
                    "b_ip": f"10.101.{s}.{2 * idx}/31",
                    "subnet": f"10.101.{s}.{2 * idx}/31",
                })
    return rows


# --------------------------------------------------------------------------------------------
# Task 3 -- BGP neighbor table
# --------------------------------------------------------------------------------------------
def build_bgp_neighbors(plan: list[dict], spine_asn: int = SPINE_ASN,
                        leaf_asn_base: int = LEAF_ASN_BASE) -> list[dict]:
    """One row per eBGP session (one per fabric link), seen from the leaf."""
    rows = []
    for link in plan:
        if link["link_type"] != "fabric":
            continue
        rail = int(link["a_device"].removeprefix("orion-be-leaf-r"))
        rows.append({
            "leaf": link["a_device"], "leaf_asn": leaf_asn_base + rail,
            "leaf_ip": link["a_ip"].split("/")[0],
            "spine": link["b_device"], "spine_asn": spine_asn,
            "spine_ip": link["b_ip"].split("/")[0], "link_id": link["link_id"],
        })
    return rows


# --------------------------------------------------------------------------------------------
# Task 4 -- intent validation
# --------------------------------------------------------------------------------------------
def _owned_prefixes(dev: dict) -> set[str]:
    owned = {dev["loopback"]}
    if dev["role"] == "leaf" and dev["rail"] is not None:
        owned.add(f"10.100.{dev['rail']}.0/24")
    return owned


def validate_intent(intent: dict[str, list[dict]]) -> list[dict]:
    """Return findings: dicts with keys code, subject, severity, detail."""
    findings: list[dict] = []
    devices = {d["device"]: d for d in intent["devices"]}
    links = intent["links"]
    adverts = intent["advertisements"]

    def add(code: str, subject: str, severity: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "severity": severity, "detail": detail})

    # DUP_P2P -- the same /31 used on more than one link
    by_subnet: dict[str, list[str]] = defaultdict(list)
    for link in links:
        for side in ("a_ip", "b_ip"):
            net = str(ipaddress.ip_interface(link[side]).network)
            if link["link_id"] not in by_subnet[net]:
                by_subnet[net].append(link["link_id"])
    for net, ids in sorted(by_subnet.items()):
        if len(ids) > 1:
            add("DUP_P2P", net, "blocker", f"/31 used on {len(ids)} links: {', '.join(sorted(ids))}")
    # P2P sanity -- both ends in the same /31 and not identical
    for link in links:
        a, b = ipaddress.ip_interface(link["a_ip"]), ipaddress.ip_interface(link["b_ip"])
        if a.network != b.network or a.ip == b.ip:
            add("P2P_MISMATCH", link["link_id"], "blocker", f"{a} vs {b}")

    # ASN_COLLISION -- spines may share one ASN (RFC 7938); nothing else may share
    spine_asns = {d["asn"] for d in devices.values() if d["role"] == "spine"}
    by_asn: dict[int, list[str]] = defaultdict(list)
    for d in devices.values():
        if d["role"] != "spine":
            by_asn[d["asn"]].append(d["device"])
    for asn, devs in sorted(by_asn.items()):
        if len(devs) > 1 or asn in spine_asns:
            add("ASN_COLLISION", str(asn), "blocker", f"ASN shared by {', '.join(sorted(devs))}")

    # MTU -- fabric links 9216 on both ends; host links switch 9216 / host 9000
    for link in links:
        if link["link_type"] == "fabric":
            if link["a_mtu"] != link["b_mtu"] or link["a_mtu"] != SWITCH_MTU:
                add("MTU_MISMATCH", link["link_id"], "blocker",
                    f"{link['a_device']} {link['a_mtu']} vs {link['b_device']} {link['b_mtu']}")
        elif link["a_mtu"] != SWITCH_MTU or link["b_mtu"] != HOST_MTU:
            add("MTU_MISMATCH", link["link_id"], "major",
                f"host link expects switch {SWITCH_MTU}/host {HOST_MTU}, got {link['a_mtu']}/{link['b_mtu']}")

    # ECMP_MAXPATHS -- leaf needs >= its uplinks; spine needs >= its widest bundle to one leaf
    uplinks: dict[str, int] = defaultdict(int)
    pair_links: dict[tuple[str, str], int] = defaultdict(int)
    for link in links:
        if link["link_type"] == "fabric":
            uplinks[link["a_device"]] += 1
            pair_links[(link["b_device"], link["a_device"])] += 1
    for name, d in sorted(devices.items()):
        if d["role"] == "leaf":
            need = uplinks[name]
        else:
            need = max((n for (sp, _), n in pair_links.items() if sp == name), default=0)
        if d["ecmp_max_paths"] < need:
            add("ECMP_MAXPATHS", name, "major", f"max-paths {d['ecmp_max_paths']} < {need} equal-cost paths")

    # ASYM_ADVERT / BAD_ORIGIN -- every owned prefix to every connected spine; nothing else
    linked_spines: dict[str, set[str]] = defaultdict(set)
    for link in links:
        if link["link_type"] == "fabric":
            linked_spines[link["a_device"]].add(link["b_device"])
    sent: dict[tuple[str, str], set[str]] = defaultdict(set)
    for adv in adverts:
        sent[(adv["device"], adv["prefix"])].add(adv["neighbor"])
    bad_origin_seen: set[tuple[str, str]] = set()
    for adv in adverts:
        owned = _owned_prefixes(devices[adv["device"]])
        key = (adv["device"], adv["prefix"])
        if adv["prefix"] not in owned and key not in bad_origin_seen:
            bad_origin_seen.add(key)
            owner = [n for n, d in devices.items() if adv["prefix"] in _owned_prefixes(d)]
            add("BAD_ORIGIN", f"{adv['device']} {adv['prefix']}", "blocker",
                f"prefix owned by {owner[0] if owner else 'nobody'}")
    for name, d in sorted(devices.items()):
        if d["role"] != "leaf":
            continue
        for prefix in sorted(_owned_prefixes(d)):
            got = sent.get((name, prefix), set())
            if got != linked_spines[name]:
                missing = sorted(linked_spines[name] - got)
                add("ASYM_ADVERT", f"{name} {prefix}", "major", f"not advertised to {', '.join(missing)}")
    return findings


# --------------------------------------------------------------------------------------------
# Task 5 -- capacity after failure
# --------------------------------------------------------------------------------------------
def fabric_capacity(link_counts: list[list[int]], link_gbps: float,
                    advertised: list[list[bool]] | None = None) -> dict:
    """Uplink, ECMP-aware ingress and worst-case bisection capacity (Gb/s, one direction)."""
    n_leaves, n_spines = len(link_counts), len(link_counts[0])
    if advertised is None:
        advertised = [[True] * n_spines for _ in range(n_leaves)]
    uplink = [sum(row) * link_gbps for row in link_counts]
    ingress = []
    for j in range(n_leaves):
        usable = [link_counts[j][s] for s in range(n_spines) if link_counts[j][s] > 0 and advertised[j][s]]
        ingress.append(len(usable) * min(usable) * link_gbps if usable else 0.0)
    best = math.inf
    for group in itertools.combinations(range(n_leaves), n_leaves // 2):
        a = set(group)
        cut = 0
        for s in range(n_spines):
            sa = sum(link_counts[i][s] for i in a)
            sb = sum(link_counts[i][s] for i in range(n_leaves) if i not in a)
            cut += min(sa, sb)
        best = min(best, cut)
    return {"uplink_gbps": uplink, "ecmp_ingress_gbps": ingress, "bisection_gbps": best * link_gbps}


# --------------------------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    args = parser.parse_args()
    print("== Sizing (ORION-256 backend) ==")
    for k, v in size_two_tier(256, 64, 64, 1.0).items():
        print(f"  {k:24s} {v}")
    plan = build_addressing_plan()
    print(f"== Addressing plan: {len(plan)} /31 links; BGP sessions: {len(build_bgp_neighbors(plan))} ==")
    print("== Intent validation ==")
    for f in validate_intent(load_intent(args.data)):
        print(f"  [{f['severity']:7s}] {f['code']:14s} {f['subject']:28s} {f['detail']}")
    print("== Capacity (Gb/s, one direction) ==")
    for label, c in (("baseline", link_matrix(8, 4, 8)),
                     ("orion-be-leaf-r0/orion-be-spine-1 one link down", link_matrix(8, 4, 8, failed_links=((0, 0),))),
                     ("orion-be-spine-2 down", link_matrix(8, 4, 8, failed_spines=(1,)))):
        cap = fabric_capacity(c, 400)
        print(f"  {label:32s} orion-be-leaf-r0 uplink {cap['uplink_gbps'][0]:>7.0f}  "
              f"orion-be-leaf-r0 ECMP ingress {cap['ecmp_ingress_gbps'][0]:>7.0f}  bisection {cap['bisection_gbps']:>7.0f}")


if __name__ == "__main__":
    main()
