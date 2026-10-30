#!/usr/bin/env python3
"""RDMA deployment-readiness validator (Chapter 8 lab) -- REFERENCE SOLUTION.

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
    devs: dict[str, dict] = {}
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        if key == "hca_id":
            cur = {}
            devs[val] = cur
        elif cur is None:
            continue
        elif key == "fw_ver":
            cur["fw_ver"] = val
        elif key == "node_guid":
            cur["node_guid"] = val
        elif key == "state":
            cur["state"] = val.split()[0]
        elif key in ("active_mtu", "max_mtu"):
            cur[key] = int(val.split()[0])
        elif key == "link_layer":
            cur["link_layer"] = val
    return devs


def parse_rdma_link(text: str) -> dict[str, dict]:
    """Parse ``rdma link show``. Returns ``{dev: {"port": int, "state": str, "physical_state": str,
    "netdev": str | None}}``."""
    out: dict[str, dict] = {}
    for line in text.splitlines():
        m = re.match(r"link (\S+)/(\d+) state (\S+) physical_state (\S+)(?: netdev (\S+))?", line.strip())
        if m:
            out[m.group(1)] = {"port": int(m.group(2)), "state": m.group(3),
                               "physical_state": m.group(4), "netdev": m.group(5)}
    return out


def parse_show_gids(text: str) -> list[dict]:
    """Parse ``show_gids``. Returns rows ``{"dev", "port": int, "index": int, "gid", "ipv4": str|None,
    "ver": "v1"|"v2", "netdev"}``. Rows without an IPv4 address have ``ipv4=None``."""
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 6 or not parts[1].isdigit():
            continue
        if len(parts) == 7:
            dev, port, idx, gid, ipv4, ver, nd = parts
        else:
            dev, port, idx, gid, ver, nd = parts
            ipv4 = None
        rows.append({"dev": dev, "port": int(port), "index": int(idx), "gid": gid,
                     "ipv4": ipv4, "ver": ver, "netdev": nd})
    return rows


def parse_ethtool_i(text: str) -> dict[str, str]:
    """Parse ``ethtool -i``. Returns ``{"driver", "version", "firmware", "bus_info"}`` where
    ``firmware`` is the version token only (``28.39.1002``, without the PSID in parentheses)."""
    kv = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            kv[k.strip()] = v.strip()
    return {"driver": kv.get("driver", ""), "version": kv.get("version", ""),
            "firmware": kv.get("firmware-version", "").split()[0] if kv.get("firmware-version") else "",
            "bus_info": kv.get("bus-info", "")}


def parse_ethtool_speed(text: str) -> int | None:
    """Return link speed in Mb/s from ``ethtool <if>``, or ``None`` if unknown/no link."""
    m = re.search(r"Speed:\s*(\d+)Mb/s", text)
    return int(m.group(1)) if m else None


def parse_ip_link(text: str) -> dict[str, dict]:
    """Parse ``ip -o link show``. Returns ``{ifname: {"mtu": int, "state": str, "flags": [str]}}``."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"\d+:\s+(\S+?):\s+<([^>]*)>\s+mtu\s+(\d+).*?\sstate\s+(\S+)", line)
        if m:
            out[m.group(1)] = {"flags": m.group(2).split(","), "mtu": int(m.group(3)), "state": m.group(4)}
    return out


def parse_ip_addr(text: str) -> dict[str, list[str]]:
    """Parse ``ip -o -4 addr show``. Returns ``{ifname: ["10.100.0.1/31", ...]}``."""
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        m = re.match(r"\d+:\s+(\S+)\s+inet\s+(\S+)", line)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return out


def parse_dcb_pfc(text: str) -> set[int]:
    """Parse ``dcb pfc show dev <if> prio-pfc``. Returns the set of priorities with PFC on."""
    return {int(p) for p, s in re.findall(r"(\d):(on|off)", text) if s == "on"}


def parse_dcb_app_dscp(text: str) -> dict[int, int]:
    """Parse ``dcb app show dev <if> dscp-prio``. Returns ``{dscp: priority}``."""
    return {int(d): int(p) for d, p in re.findall(r"(\d+):(\d+)", text)}


def parse_env(text: str) -> dict[str, str]:
    """Parse a ``KEY=VALUE`` env file, ignoring comments and blank lines."""
    env = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def loaded_modules(text: str) -> set[str]:
    """Return module names (first column) from ``lsmod`` output."""
    return {ln.split()[0] for ln in text.splitlines() if ln.strip() and not ln.startswith("Module")}


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
    exp = baseline["expected"]
    host = inv.host
    node_index = int(re.search(r"(\d+)$", host).group(1))
    findings: list[Finding] = []

    def add(dev: str, cid: str, msg: str) -> None:
        findings.append(Finding(host, dev, cid, msg))

    devinfo = parse_ibv_devinfo(_section(inv, "ibv_devinfo"))
    links = parse_rdma_link(_section(inv, "rdma link"))
    gids = parse_show_gids(_section(inv, "show_gids"))
    iplink = parse_ip_link(_section(inv, "ip -o link"))
    ipaddr = parse_ip_addr(_section(inv, "ip -o -4 addr"))
    env = parse_env(_section(inv, "cat /etc/halcyon/rdma.env"))
    mods = loaded_modules(_section(inv, "lsmod"))
    gid_var = exp["gid_index_variable"]
    gid_index = int(env[gid_var]) if gid_var in env else None

    for dev, meta in baseline["rails"].items():
        rail, nd = meta["rail"], meta["netdev"]
        di = devinfo.get(dev)
        if di is None:
            add(dev, "PORT_STATE", "device missing from ibv_devinfo")
            continue
        lk = links.get(dev, {})
        if di.get("state") != exp["port_state"] or lk.get("state") != "ACTIVE":
            add(dev, "PORT_STATE", f"state={di.get('state')} rdma={lk.get('state')}/{lk.get('physical_state')}")
        if di.get("link_layer") != exp["link_layer"]:
            add(dev, "LINK_LAYER", f"link_layer={di.get('link_layer')}")
        speed = parse_ethtool_speed(_section(inv, f"ethtool {nd}"))
        if speed != exp["speed_mbps"]:
            add(dev, "LINK_SPEED", f"speed={speed} Mb/s expected {exp['speed_mbps']}")
        eti = parse_ethtool_i(_section(inv, f"ethtool -i {nd}"))
        if di.get("fw_ver") != str(exp["firmware"]) or eti["firmware"] != str(exp["firmware"]):
            add(dev, "FIRMWARE", f"fw={di.get('fw_ver')} expected {exp['firmware']}")
        if eti["driver"] != exp["driver"] or eti["version"] != str(exp["driver_version"]):
            add(dev, "DRIVER", f"driver={eti['driver']} {eti['version']}")
        mtu = iplink.get(nd, {}).get("mtu")
        if mtu != exp["netdev_mtu"] or di.get("active_mtu") != exp["rdma_active_mtu"]:
            add(dev, "MTU", f"netdev mtu={mtu} active_mtu={di.get('active_mtu')}")
        addrs = ipaddr.get(nd, [])
        ip = addrs[0].split("/")[0] if addrs else None
        row = next((g for g in gids if g["dev"] == dev and g["index"] == gid_index), None)
        if row is None or row["ver"] != exp["roce_version"] or row["ipv4"] != ip:
            desc = "absent" if row is None else f"{row['ver']} ipv4={row['ipv4']}"
            add(dev, "GID_INDEX", f"{gid_var}={gid_index} -> {desc}; netdev IPv4={ip}")
        pfc = parse_dcb_pfc(_section(inv, f"dcb pfc show dev {nd}"))
        if pfc != set(exp["pfc_enabled_priorities"]):
            add(dev, "QOS_PFC", f"PFC on {sorted(pfc)} expected {exp['pfc_enabled_priorities']}")
        dscp = parse_dcb_app_dscp(_section(inv, f"dcb app show dev {nd}"))
        want = {int(k): int(v) for k, v in exp["dscp_to_priority"].items()}
        if any(dscp.get(k) != v for k, v in want.items()):
            add(dev, "QOS_DSCP", f"dscp-prio={dscp}")
        want_ip = expected_ip(exp["address_plan"], rail, node_index)
        if want_ip not in addrs:
            add(dev, "ADDRESS_PLAN", f"{nd} has {addrs} expected {want_ip}")

    if exp["peer_memory_module"] not in mods:
        add("-", "PEERMEM", f"{exp['peer_memory_module']} not loaded")
    return findings


def run_readiness(inventory_dir: Path, baseline_path: Path) -> tuple[list[Finding], dict[str, str]]:
    """Check every ``*.txt`` node capture in ``inventory_dir``.

    Returns ``(findings, verdicts)`` where ``verdicts`` maps host -> ``READY`` | ``NOT_READY``.
    """
    baseline = yaml.safe_load(Path(baseline_path).read_text(encoding="utf-8"))
    findings: list[Finding] = []
    verdicts: dict[str, str] = {}
    for f in sorted(Path(inventory_dir).glob("*.txt")):
        inv = split_sections(f.read_text(encoding="utf-8"))
        fs = check_node(inv, baseline)
        findings += fs
        verdicts[inv.host] = "NOT_READY" if fs else "READY"
    return findings, verdicts


def render_report(findings: list[Finding], verdicts: dict[str, str]) -> str:
    """Render a Markdown readiness checklist: a per-node verdict table and a findings table."""
    lines = ["# RDMA deployment-readiness report", "",
             f"Nodes checked: {len(verdicts)}; ready: {sum(v == 'READY' for v in verdicts.values())}; "
             f"findings: {len(findings)}", "", "| Host | Verdict | Failed checks |", "|---|---|---|"]
    for host, v in verdicts.items():
        ids = sorted({f.check_id for f in findings if f.host == host})
        lines.append(f"| {host} | {v} | {', '.join(ids) or '-'} |")
    lines += ["", "| Host | Device | Check | Evidence |", "|---|---|---|---|"]
    for f in sorted(findings, key=lambda x: x.key):
        lines.append(f"| {f.host} | {f.device} | {f.check_id} | {f.message} |")
    return "\n".join(lines) + "\n"


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
