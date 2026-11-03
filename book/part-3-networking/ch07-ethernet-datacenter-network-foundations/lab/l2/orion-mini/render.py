#!/usr/bin/env python3
"""Render the ORION-mini containerlab fabric (L2 extension of Lab 7).

A scaled-down ORION backend that keeps the chapter's conventions (Section 7.3, Table 7.2):

* 4 rail leaves ``leaf-r0``..``leaf-r3`` (AS 65101 + r, loopback 10.255.0.(11 + r)),
  2 spines ``spine-1``/``spine-2`` (shared AS 65100, loopback 10.255.0.s), one link per leaf-spine pair
  (k = 0), so idx = 8r + k = 8r; spine side ``10.101.s.(2 idx)/31``, leaf side ``10.101.s.(2 idx + 1)/31``.
* 2 hosts ``n01``/``n02`` with one NIC per rail: leaf ``10.100.r.(2n)/31``, host ``10.100.r.(2n + 1)/31``,
  per-rail policy routing on the host (one rule and one table per rail).
* eBGP with BFD, ``timers 3 9``, ``maximum-paths 64``; each leaf advertises its loopback and
  ``10.100.r.0/24`` (summary-only), as in Listing 7.1.

Container interfaces: leaf ``eth1``/``eth2`` = hosts n01/n02, ``eth3``/``eth4`` = spine-1/spine-2;
spine ``eth(r + 1)`` = leaf-r<r>; host ``eth(r + 1)`` = rail r.

Writes ``orion-mini.clab.yml`` and ``configs/`` next to this file (deterministic; the committed copies are
its output). Untested in the course harness, which cannot run containerlab (no root, ``--network none``).

Usage:
    python render.py            # (re)write the topology and FRR configs
    python render.py --check    # exit 1 if the committed files differ from a fresh render
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAILS = 4
SPINES = (1, 2)
HOSTS = (1, 2)
FRR_IMAGE = "quay.io/frrouting/frr:9.1.0"
HOST_IMAGE = "alpine:3.19"

DAEMONS = """\
# FRR daemons for ORION-mini (zebra always runs)
bgpd=yes
bfdd=yes
vtysh_enable=yes
zebra_options="  -A 127.0.0.1 -s 90000000"
bgpd_options="   -A 127.0.0.1"
bfdd_options="   -A 127.0.0.1"
"""


def fabric_ips(rail: int, spine: int) -> tuple[str, str]:
    """Return (spine_ip, leaf_ip) of the rail-``rail`` leaf's single uplink to ``spine`` (k = 0)."""
    idx = 8 * rail
    return f"10.101.{spine}.{2 * idx}", f"10.101.{spine}.{2 * idx + 1}"


def leaf_conf(rail: int) -> str:
    asn, lo = 65101 + rail, f"10.255.0.{11 + rail}"
    lines = ["frr defaults traditional", f"hostname leaf-r{rail}", "!", "interface lo",
             f" ip address {lo}/32", "!"]
    for n in HOSTS:
        lines += [f"interface eth{n}", f" description orion-n{n:02d} nic{rail}",
                  f" ip address 10.100.{rail}.{2 * n}/31", "!"]
    for s in SPINES:
        _, leaf_ip = fabric_ips(rail, s)
        lines += [f"interface eth{2 + s}", f" description spine-{s}", f" ip address {leaf_ip}/31", "!"]
    lines += [f"ip prefix-list HOST-LINKS seq 10 permit 10.100.{rail}.0/24 le 31",
              "route-map HOST-LINKS permit 10", " match ip address prefix-list HOST-LINKS", "!",
              f"router bgp {asn}", f" bgp router-id {lo}", " no bgp ebgp-requires-policy",
              " neighbor SPINES peer-group", " neighbor SPINES remote-as 65100", " neighbor SPINES bfd",
              " neighbor SPINES timers 3 9", " neighbor SPINES advertisement-interval 0"]
    for s in SPINES:
        spine_ip, _ = fabric_ips(rail, s)
        lines.append(f" neighbor {spine_ip} peer-group SPINES")
    lines += [" address-family ipv4 unicast", f"  network {lo}/32",
              f"  aggregate-address 10.100.{rail}.0/24 summary-only",
              "  redistribute connected route-map HOST-LINKS", "  maximum-paths 64",
              " exit-address-family", "!"]
    return "\n".join(lines) + "\n"


def spine_conf(spine: int) -> str:
    lo = f"10.255.0.{spine}"
    lines = ["frr defaults traditional", f"hostname spine-{spine}", "!", "interface lo",
             f" ip address {lo}/32", "!"]
    for r in range(RAILS):
        spine_ip, _ = fabric_ips(r, spine)
        lines += [f"interface eth{r + 1}", f" description leaf-r{r}", f" ip address {spine_ip}/31", "!"]
    lines += ["router bgp 65100", f" bgp router-id {lo}", " no bgp ebgp-requires-policy"]
    for r in range(RAILS):
        _, leaf_ip = fabric_ips(r, spine)
        lines += [f" neighbor {leaf_ip} remote-as {65101 + r}", f" neighbor {leaf_ip} bfd",
                  f" neighbor {leaf_ip} timers 3 9", f" neighbor {leaf_ip} advertisement-interval 0"]
    lines += [" address-family ipv4 unicast", f"  network {lo}/32", "  maximum-paths 64",
              " exit-address-family", "!"]
    return "\n".join(lines) + "\n"


def host_exec(n: int) -> list[str]:
    cmds = []
    for r in range(RAILS):
        host_ip, gw = f"10.100.{r}.{2 * n + 1}", f"10.100.{r}.{2 * n}"
        cmds += [f"ip link set eth{r + 1} mtu 9000",
                 f"ip addr add {host_ip}/31 dev eth{r + 1}",
                 f"ip rule add from {host_ip} table {100 + r}",
                 f"ip route add 10.100.0.0/16 via {gw} dev eth{r + 1} table {100 + r}"]
    cmds.append(f"ip route add 10.100.0.0/16 via 10.100.0.{2 * n} dev eth1")   # unsourced traffic: rail 0
    return cmds


def topology() -> str:
    out = ["# ORION-mini: 2 spines x 4 rail leaves x 2 hosts, eBGP + BFD (Lab 7, L2 extension).",
           "# Generated by render.py; isolated lab use only. Untested in the course harness.",
           "name: orion-mini", "topology:", "  nodes:"]
    for s in SPINES:
        out += [f"    spine-{s}:", "      kind: linux", f"      image: {FRR_IMAGE}", "      binds:",
                f"        - configs/spine-{s}/frr.conf:/etc/frr/frr.conf",
                "        - configs/daemons:/etc/frr/daemons"]
    for r in range(RAILS):
        out += [f"    leaf-r{r}:", "      kind: linux", f"      image: {FRR_IMAGE}", "      binds:",
                f"        - configs/leaf-r{r}/frr.conf:/etc/frr/frr.conf",
                "        - configs/daemons:/etc/frr/daemons"]
    for n in HOSTS:
        out += [f"    n{n:02d}:", "      kind: linux", f"      image: {HOST_IMAGE}", "      exec:"]
        out += [f'        - "{c}"' for c in host_exec(n)]
    out += ["  links:"]
    for r in range(RAILS):
        for n in HOSTS:
            out.append(f'    - endpoints: ["leaf-r{r}:eth{n}", "n{n:02d}:eth{r + 1}"]')
        for s in SPINES:
            out.append(f'    - endpoints: ["leaf-r{r}:eth{2 + s}", "spine-{s}:eth{r + 1}"]')
    return "\n".join(out) + "\n"


def render() -> dict[str, str]:
    files = {"orion-mini.clab.yml": topology(), "configs/daemons": DAEMONS}
    for s in SPINES:
        files[f"configs/spine-{s}/frr.conf"] = spine_conf(s)
    for r in range(RAILS):
        files[f"configs/leaf-r{r}/frr.conf"] = leaf_conf(r)
    return files


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="compare with the committed files instead of writing")
    a = p.parse_args()
    stale = []
    for rel, text in render().items():
        path = HERE / rel
        if a.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("stale: " + ", ".join(stale))
        return 1
    print("ok" if a.check else f"wrote {len(render())} files under {HERE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
