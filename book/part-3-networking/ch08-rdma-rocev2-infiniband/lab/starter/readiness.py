#!/usr/bin/env python3
"""RDMA deployment-readiness validator (Chapter 8 lab) -- STARTER (complete the TODOs).

Parses per-node command captures (ibv_devinfo, rdma link, show_gids, ethtool, ip, dcb, lsmod and the
site RDMA environment file), compares them with a baseline, and emits a readiness checklist.

Input format: one text file per node; each command's output follows a header line
``### cmd: <command>``. See ``lab/data/inventory/``.

Usage:
    python readiness.py --inventory ../../lab/data/inventory --baseline ../../lab/data/baseline.yaml \
        --out readiness_report.md
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Check identifiers used in findings (stable; the checker relies on them).
CHECK_IDS = ("PORT_STATE", "LINK_LAYER", "LINK_SPEED", "FIRMWARE", "DRIVER", "MTU", "GID_INDEX",
             "QOS_PFC", "QOS_DSCP", "PEERMEM", "ADDRESS_PLAN")

_IB_MTU = {1: 256, 2: 512, 3: 1024, 4: 2048, 5: 4096}


@dataclass(frozen=True)
class Finding:
    """One failed readiness check.

    ``device`` is an RDMA device name (``mlx5_3``) or ``-`` for node-level checks.
    """

    host: str
    device: str
    check_id: str
    message: str

    @property
    def key(self) -> str:
        return f"{self.host}|{self.device}|{self.check_id}"


@dataclass
class NodeInventory:
    host: str
    sections: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- provided helper

def split_sections(text: str) -> NodeInventory:
    """Split a capture file into ``{command: output}``. Provided (not a TODO) in the starter."""
    host = "unknown"
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("### host:"):
            host = line.split(":", 1)[1].strip()
        elif line.startswith("### cmd:"):
            current = line.split(":", 1)[1].strip()
            sections[current] = []
        elif line.startswith("###"):
            continue
        elif current is not None:
            sections[current].append(line)
    return NodeInventory(host, {k: "\n".join(v) + "\n" for k, v in sections.items()})


# --------------------------------------------------------------------------- parsers

def parse_ibv_devinfo(text: str) -> dict[str, dict]:
    """Parse ``ibv_devinfo`` output.

    Returns ``{hca_id: {"fw_ver": str, "state": str, "active_mtu": int, "max_mtu": int,
    "link_layer": str, "node_guid": str}}``. ``state`` is the symbolic name (``PORT_ACTIVE``);
    MTUs are in bytes (the number before the enum in parentheses). Single-port devices assumed.
    """
    # TODO: implement parse_ibv_devinfo (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_ibv_devinfo")


def parse_rdma_link(text: str) -> dict[str, dict]:
    """Parse ``rdma link show``. Returns ``{dev: {"port": int, "state": str, "physical_state": str,
    "netdev": str | None}}``."""
    # TODO: implement parse_rdma_link (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_rdma_link")


def parse_show_gids(text: str) -> list[dict]:
    """Parse ``show_gids``. Returns rows ``{"dev", "port": int, "index": int, "gid", "ipv4": str|None,
    "ver": "v1"|"v2", "netdev"}``. Rows without an IPv4 address have ``ipv4=None``."""
    # TODO: implement parse_show_gids (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_show_gids")


def parse_ethtool_i(text: str) -> dict[str, str]:
    """Parse ``ethtool -i``. Returns ``{"driver", "version", "firmware", "bus_info"}`` where
    ``firmware`` is the version token only (``28.39.1002``, without the PSID in parentheses)."""
    # TODO: implement parse_ethtool_i (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_ethtool_i")


def parse_ethtool_speed(text: str) -> int | None:
    """Return link speed in Mb/s from ``ethtool <if>``, or ``None`` if unknown/no link."""
    # TODO: implement parse_ethtool_speed (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_ethtool_speed")


def parse_ip_link(text: str) -> dict[str, dict]:
    """Parse ``ip -o link show``. Returns ``{ifname: {"mtu": int, "state": str, "flags": [str]}}``."""
    # TODO: implement parse_ip_link (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_ip_link")


def parse_ip_addr(text: str) -> dict[str, list[str]]:
    """Parse ``ip -o -4 addr show``. Returns ``{ifname: ["10.100.0.1/31", ...]}``."""
    # TODO: implement parse_ip_addr (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_ip_addr")


def parse_dcb_pfc(text: str) -> set[int]:
    """Parse ``dcb pfc show dev <if> prio-pfc``. Returns the set of priorities with PFC on."""
    # TODO: implement parse_dcb_pfc (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_dcb_pfc")


def parse_dcb_app_dscp(text: str) -> dict[int, int]:
    """Parse ``dcb app show dev <if> dscp-prio``. Returns ``{dscp: priority}``."""
    # TODO: implement parse_dcb_app_dscp (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_dcb_app_dscp")


def parse_env(text: str) -> dict[str, str]:
    """Parse a ``KEY=VALUE`` env file, ignoring comments and blank lines."""
    # TODO: implement parse_env (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_env")


def loaded_modules(text: str) -> set[str]:
    """Return module names (first column) from ``lsmod`` output."""
    # TODO: implement loaded_modules (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("loaded_modules")


# --------------------------------------------------------------------------- checks

def _section(inv: NodeInventory, prefix: str) -> str:
    for k, v in inv.sections.items():
        if k == prefix or k.startswith(prefix):
            return v
    return ""


def expected_ip(plan: str, rail: int, node_index: int) -> str:
    """Render the address plan for (rail, node) -> e.g. ``10.100.3.9/31``."""
    return plan.format(rail=rail, host=2 * node_index + 1).split()[0]


def check_node(inv: NodeInventory, baseline: dict) -> list[Finding]:
    """Run every readiness check on one node and return the failed checks as findings.

    Per device: PORT_STATE, LINK_LAYER, LINK_SPEED, FIRMWARE, DRIVER, MTU (netdev MTU and RDMA
    active_mtu), GID_INDEX (configured index resolves to a RoCE v2 GID carrying the netdev's IPv4
    address), QOS_PFC (PFC enabled on exactly the expected priorities), QOS_DSCP (expected DSCP to
    priority entries present), ADDRESS_PLAN. Per node (device ``-``): PEERMEM.
    """
    # TODO: implement check_node (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("check_node")


def run_readiness(inventory_dir: Path, baseline_path: Path) -> tuple[list[Finding], dict[str, str]]:
    """Check every ``*.txt`` node capture in ``inventory_dir``.

    Returns ``(findings, verdicts)`` where ``verdicts`` maps host -> ``READY`` | ``NOT_READY``.
    """
    # TODO: implement run_readiness (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("run_readiness")


def render_report(findings: list[Finding], verdicts: dict[str, str]) -> str:
    """Render a Markdown readiness checklist: a per-node verdict table and a findings table."""
    # TODO: implement render_report (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("render_report")


def main() -> None:
    here = Path(__file__).resolve().parent
    default_data = here.parent.parent / "lab" / "data"
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inventory", type=Path, default=default_data / "inventory")
    p.add_argument("--baseline", type=Path, default=default_data / "baseline.yaml")
    p.add_argument("--out", type=Path, default=None, help="write Markdown report here (default: stdout)")
    a = p.parse_args()
    findings, verdicts = run_readiness(a.inventory, a.baseline)
    rep = render_report(findings, verdicts)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
    else:
        print(rep)


if __name__ == "__main__":
    main()
