#!/usr/bin/env python3
"""Chapter 7 lab -- fabric design and validation tool (STARTER).

Implement the five TODO functions. Run ``python ../check.py`` (or ``python check.py`` from
``lab/``) to see your progress. All bandwidth values are in Gb/s (bits). Everything you compute
here is [MODELED]: no packets are sent, no switch is touched.

Conventions (also in lab/README.md, "Intent conventions"):
  * Leaves are ``orion-be-leaf-r0`` .. ``orion-be-leaf-r7`` (rail r), spines ``orion-be-spine-1`` .. ``orion-be-spine-4``, hosts ``orion-n01`` .. ``orion-n32``.
  * Host link, rail r, node n (1..32): leaf ``Ethernet<n>`` = 10.100.r.(2n)/31, host ``nic<r>`` = 10.100.r.(2n+1)/31.
  * Fabric link, leaf r, spine s (1-based), parallel link k (0..7), idx = r*8 + k:
    spine ``Ethernet<1+idx>`` = 10.101.s.(2*idx)/31 (even), leaf ``Ethernet<33+(s-1)*8+k>`` = 10.101.s.(2*idx+1)/31 (odd).
  * ASNs: all spines 65100 (shared on purpose, RFC 7938); orion-be-leaf-r<r> = 65101 + r.
  * MTU: switch ports 9216 on both ends of every fabric link; host links are switch 9216 / host 9000.
  * A leaf owns exactly two prefixes: its rail aggregate 10.100.r.0/24 and its loopback /32.
"""
from __future__ import annotations

import argparse
import csv
import ipaddress  # noqa: F401  (you will want it)
import itertools  # noqa: F401  (you will want it)
import math  # noqa: F401  (you will want it)
from collections import defaultdict  # noqa: F401  (you will want it)
from pathlib import Path

SPINE_ASN = 65100
LEAF_ASN_BASE = 65101
SWITCH_MTU = 9216
HOST_MTU = 9000


# --------------------------------------------------------------------------------------------
# Provided helpers (do not change)
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
    """Size a two-tier leaf-spine (folded Clos) fabric. Port counts are per leaf at the stated speeds.

    Args:
        endpoints:   number of host-facing ports needed (e.g. 256 backend NICs for ORION-256).
        leaf_ports:  usable ports per leaf at ``link_gbps``.
        spine_ports: usable ports per spine at ``link_gbps``.
        oversub:     downlink:uplink ratio (1.0 = non-blocking, 3.0 = 3:1).
        link_gbps:   uplink (and, by default, downlink) port speed in Gb/s.
        min_spines:  never build fewer spines than this (redundancy floor).
        down_gbps:   host-facing port speed if different from link_gbps (e.g. 200 on a frontend leaf
                     with 400G uplinks); None means "same as link_gbps".

    Returns a dict with these keys:
        down_per_leaf          = round(leaf_ports * oversub / (1 + oversub))
        up_per_leaf            = leaf_ports - down_per_leaf
        oversubscription       = down_per_leaf / up_per_leaf (float) -- the PORT-COUNT ratio
        bandwidth_oversubscription = (down_per_leaf * down_gbps) / (up_per_leaf * link_gbps) -- the ratio
                                 that matters for traffic; differs from the port ratio when speeds differ
        leaves                 = ceil(endpoints / down_per_leaf)
        max_endpoints_two_tier = spine_ports * down_per_leaf
        feasible               = endpoints <= max_endpoints_two_tier (and a spine count exists)
        spines                 = smallest s >= max(min_spines, ceil(leaves*up/spine_ports)) with up % s == 0
                                 (None if infeasible)
        links_per_leaf_spine   = up_per_leaf // spines (None if infeasible)
        host_cables            = endpoints
        fabric_cables          = leaves * up_per_leaf (None if infeasible)
        total_cables           = host_cables + fabric_cables (None if infeasible)
        transceivers           = 2 * total_cables, i.e. every cable optical (None if infeasible)
        leaf_uplink_gbps       = up_per_leaf * link_gbps
    """
    # TODO: implement the arithmetic above. Check ORION: 256 endpoints, 64/64 ports, 1:1
    #       -> 8 leaves, 4 spines, 8 links per leaf-spine pair, 512 cables.
    raise NotImplementedError("size_two_tier")


# --------------------------------------------------------------------------------------------
# Task 2 -- addressing plan
# --------------------------------------------------------------------------------------------
def build_addressing_plan(nodes: int = 32, rails: int = 8, spines: int = 4,
                          links_per_pair: int = 8) -> list[dict]:
    """Return one row per point-to-point link: all host links, then all fabric links.

    Each row has keys: link_id, link_type ('host'|'fabric'), a_device, a_port, a_ip,
    b_device, b_port, b_ip, subnet. ``a_*`` is always the leaf. IPs carry their prefix length
    (e.g. '10.100.3.10/31'); ``subnet`` is the /31 network ('10.100.3.10/31').
    Link ids: host 'H-r<r>-n<nn>' (nn = node number 01..32, zero-padded), fabric 'F-r<r>-s<s>-k<k>'.
    Follow the conventions in the module docstring exactly.
    """
    # TODO: two nested loops (rails x nodes 1..32) for host links, three (rails x spines x k) for fabric.
    raise NotImplementedError("build_addressing_plan")


# --------------------------------------------------------------------------------------------
# Task 3 -- BGP neighbor table
# --------------------------------------------------------------------------------------------
def build_bgp_neighbors(plan: list[dict], spine_asn: int = SPINE_ASN,
                        leaf_asn_base: int = LEAF_ASN_BASE) -> list[dict]:
    """Return one row per eBGP session -- one per *fabric* link in ``plan`` -- seen from the leaf.

    Keys: leaf, leaf_asn, leaf_ip (no prefix length), spine, spine_asn, spine_ip, link_id.
    leaf_asn = leaf_asn_base + rail, where rail is parsed from 'orion-be-leaf-r<rail>'.
    """
    # TODO: filter fabric rows and map them to session rows.
    raise NotImplementedError("build_bgp_neighbors")


# --------------------------------------------------------------------------------------------
# Task 4 -- intent validation
# --------------------------------------------------------------------------------------------
def validate_intent(intent: dict[str, list[dict]]) -> list[dict]:
    """Validate a fabric intent (as returned by ``load_intent``) and return a list of findings.

    Each finding is a dict: {"code", "subject", "severity", "detail"}. Implement these rules
    and use EXACTLY these codes and subject formats (the checker compares (code, subject) pairs):

      DUP_P2P        a /31 network used by more than one link.        subject: '10.101.x.y/31'
      P2P_MISMATCH   a link whose two ends are not in the same /31,
                     or that uses the same IP on both ends.           subject: link_id
      ASN_COLLISION  two non-spine devices share an ASN, or a
                     non-spine device uses a spine ASN. Spines
                     sharing one ASN is CORRECT (RFC 7938).           subject: the ASN as a string
      MTU_MISMATCH   fabric link: ends differ or != 9216;
                     host link: switch != 9216 or host != 9000.       subject: link_id
      ECMP_MAXPATHS  leaf: ecmp_max_paths < number of its fabric
                     links; spine: < its largest bundle to one leaf.  subject: device name
      BAD_ORIGIN     a device advertises a prefix it does not own
                     (report once per device+prefix).                 subject: '<device> <prefix>'
      ASYM_ADVERT    a leaf's owned prefix is not advertised to
                     exactly the set of spines it has links to.       subject: '<device> <prefix>'

    Severity: 'blocker' or 'major' (your judgement; explain it in your design note).
    A correct implementation reports the planted errors and NOTHING else -- false positives fail.
    """
    # TODO: build lookups (devices by name, links by subnet, uplinks per leaf, advertisements
    #       per (device, prefix)) and apply each rule.
    raise NotImplementedError("validate_intent")


# --------------------------------------------------------------------------------------------
# Task 5 -- capacity after failure
# --------------------------------------------------------------------------------------------
def fabric_capacity(link_counts: list[list[int]], link_gbps: float,
                    advertised: list[list[bool]] | None = None) -> dict:
    """Compute three capacity views of a two-tier fabric (Gb/s, one direction).

    Args:
        link_counts: c[leaf][spine] healthy parallel links (see ``link_matrix``).
        link_gbps:   per-link speed.
        advertised:  a[leaf][spine] True if the leaf's prefix is advertised to that spine
                     (default: all True).

    Returns:
        uplink_gbps:       list, per leaf: sum of healthy uplinks * link_gbps.
        ecmp_ingress_gbps: list, per leaf j: let U = spines with c[j][s] > 0 and a[j][s].
                           Remote senders spread traffic EQUALLY across U (ECMP is unweighted),
                           so the narrowest bundle caps it: len(U) * min(c[j][s] for s in U) * link_gbps
                           (0 if U is empty).
        bisection_gbps:    worst case over every split of the leaves into two halves of size
                           n//2 of sum over spines of min(links from half A, links from half B),
                           times link_gbps. (Brute force is fine for n <= 16.)
    """
    # TODO: ORION baseline must give 12800 / 12800 / 51200.
    raise NotImplementedError("fabric_capacity")


# --------------------------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    print(size_two_tier(256, 64, 64, 1.0))
    for f in validate_intent(load_intent(args.data)):
        print(f)
    print(fabric_capacity(link_matrix(8, 4, 8), 400))


if __name__ == "__main__":
    main()
