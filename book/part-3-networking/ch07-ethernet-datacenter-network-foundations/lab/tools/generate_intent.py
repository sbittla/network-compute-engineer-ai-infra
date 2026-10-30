#!/usr/bin/env python3
"""Generate the ORION-256 backend fabric *intent* dataset used by the Chapter 7 lab.

The dataset describes the rail-optimized backend fabric of ORION-256
(docs/REFERENCE_CLUSTER.md): 8 rail leaves (orion-be-leaf-r0 .. orion-be-leaf-r7), 4 spines
(orion-be-spine-1 .. orion-be-spine-4), 8 parallel 400 Gb/s links between every leaf and every
spine, and 32 HX8 nodes with one 400 Gb/s NIC per rail.

It writes three CSV files into ``lab/data/``:

* ``devices.csv``         -- one row per switch: role, rail, ASN, loopback, ECMP max-paths
* ``links.csv``           -- one row per point-to-point link (host and fabric) with /31s and MTUs
* ``advertisements.csv``  -- one row per (leaf, spine, prefix) BGP advertisement

The intent is deliberately *flawed*: an instructor-only list of planted errors lives in
``solutions/exercises-key.md``. Row order is shuffled with a fixed seed so that learners cannot
rely on ordering. Regenerating with the same seed produces byte-identical files.

Usage:
    python tools/generate_intent.py            # writes ../data/*.csv
    python tools/generate_intent.py --seed 7 --out ../data
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

NODES = 32
RAILS = 8
SPINES = 4
LINKS_PER_PAIR = 8
LINK_GBPS = 400
SPINE_ASN = 65100
LEAF_ASN_BASE = 65101
SWITCH_MTU = 9216
HOST_MTU = 9000


def leaf_name(r: int) -> str:
    return f"orion-be-leaf-r{r}"


def spine_name(s: int) -> str:
    return f"orion-be-spine-{s}"


def host_name(n: int) -> str:
    return f"orion-n{n:02d}"


def build_devices() -> list[dict]:
    rows = []
    for s in range(1, SPINES + 1):
        rows.append({"device": spine_name(s), "role": "spine", "rail": "", "asn": SPINE_ASN,
                     "loopback": f"10.255.0.{s}/32", "ecmp_max_paths": 64})
    for r in range(RAILS):
        asn = LEAF_ASN_BASE + r
        max_paths = 64
        if r == 7:
            asn = 65107  # PLANTED: ASN collision with orion-be-leaf-r6 (should be 65108)
        if r == 2:
            max_paths = 4  # PLANTED: ECMP max-paths too small for 32 uplinks
        rows.append({"device": leaf_name(r), "role": "leaf", "rail": r, "asn": asn,
                     "loopback": f"10.255.0.{11 + r}/32", "ecmp_max_paths": max_paths})
    return rows


def build_links() -> list[dict]:
    rows = []
    # Host links (n = 1..32): orion-be-leaf-r<r> Ethernet<n>  <->  orion-n<nn> nic<r>; leaf side even, host side odd.
    for r in range(RAILS):
        for n in range(1, NODES + 1):
            rows.append({
                "link_id": f"H-r{r}-n{n:02d}", "link_type": "host",
                "a_device": leaf_name(r), "a_port": f"Ethernet{n}",
                "a_ip": f"10.100.{r}.{2 * n}/31", "a_mtu": SWITCH_MTU,
                "b_device": host_name(n), "b_port": f"nic{r}",
                "b_ip": f"10.100.{r}.{2 * n + 1}/31", "b_mtu": HOST_MTU,
                "speed_gbps": LINK_GBPS,
            })
    # Fabric links: orion-be-leaf-r<r> Ethernet<33+(s-1)*8+k>  <->  orion-be-spine-<s> Ethernet<1+r*8+k>
    # Subnet 10.101.<s>.<2*(r*8+k)>/31; spine side even, leaf side odd.
    for r in range(RAILS):
        for s in range(1, SPINES + 1):
            for k in range(LINKS_PER_PAIR):
                idx = r * LINKS_PER_PAIR + k
                spine_ip = f"10.101.{s}.{2 * idx}/31"
                leaf_ip = f"10.101.{s}.{2 * idx + 1}/31"
                b_mtu = SWITCH_MTU
                if (r, s, k) == (4, 3, 5):
                    # PLANTED: copy-paste duplicate of the k=4 subnet (10.101.3.72/31)
                    spine_ip, leaf_ip = "10.101.3.72/31", "10.101.3.73/31"
                if (r, s, k) == (3, 2, 6):
                    b_mtu = 1500  # PLANTED: spine port left at factory-default MTU after RMA
                rows.append({
                    "link_id": f"F-r{r}-s{s}-k{k}", "link_type": "fabric",
                    "a_device": leaf_name(r), "a_port": f"Ethernet{33 + (s - 1) * LINKS_PER_PAIR + k}",
                    "a_ip": leaf_ip, "a_mtu": SWITCH_MTU,
                    "b_device": spine_name(s), "b_port": f"Ethernet{1 + idx}",
                    "b_ip": spine_ip, "b_mtu": b_mtu,
                    "speed_gbps": LINK_GBPS,
                })
    return rows


def build_advertisements() -> list[dict]:
    rows = []
    for r in range(RAILS):
        for s in range(1, SPINES + 1):
            prefixes = [f"10.100.{r}.0/24", f"10.255.0.{11 + r}/32"]
            if r == 5 and s == 4:
                prefixes = [f"10.255.0.{11 + r}/32"]  # PLANTED: rail /24 not sent to orion-be-spine-4
            if r == 1:
                prefixes.append("10.100.6.0/24")  # PLANTED: orion-be-leaf-r1 originates rail 6's prefix
            for p in prefixes:
                rows.append({"device": leaf_name(r), "neighbor": spine_name(s), "prefix": p})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("devices.csv", build_devices()), ("links.csv", build_links()),
                       ("advertisements.csv", build_advertisements())):
        rng.shuffle(rows)
        write_csv(args.out / name, rows)
        print(f"wrote {args.out / name} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
