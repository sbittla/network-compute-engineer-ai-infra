#!/usr/bin/env python3
"""Checker for the Chapter 8 lab (RDMA readiness validator + perftest analyzer).

Usage:
    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check: PASS / FAIL / TODO + name + reason. Exit 0 only if every check passes.
Expected findings are stored as salted hashes so the checker does not reveal the answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

EXPECTED_FINDINGS = {
    "1e2a691e2c8d888b", "17f625d9bcde6efd", "2a5e4657a6aeb845", "48f7486dc2dc65d6",
    "5c2dec0f23a85dae", "874ed4c866150163", "add6e0513c74152b", "b2b5e8a4c02995e1",
    "b83498b078cb65e6", "c6b9312a62b89764", "c8b8fad11066ab4d", "cbbdd4ea057a8bc5",
    "ccd960b3c02076e3", "ce9c3884114ad04f", "e0e5292dcfc765f1", "ef5fc30920b1bc3d",
}
EXPECTED_VERDICTS = {
    "0aec59feee2dae5e", "0e02b124cc9f1659", "3e34f161b6ee4999", "7583985d410ed6bf",
    "88539c691f68f430", "805a828ef25b47c4", "423991a64f35c8b1", "e69646c96f61a657",
}
EXPECTED_BW_FLAGS = {"47ba22f362cbf30c"}
EXPECTED_TAIL_FLAGS = {"80898910b51f164b"}


def h(s: str) -> str:
    return hashlib.sha256(("ch08:" + s).encode()).hexdigest()[:16]


SNIP_DEVINFO = """hca_id:\tmlx5_9
\ttransport:\t\t\tInfiniBand (0)
\tfw_ver:\t\t\t\t28.39.1002
\tnode_guid:\t\t\tb83f:d203:0047:0929
\tphys_port_cnt:\t\t\t1
\t\tport:\t1
\t\t\tstate:\t\t\tPORT_INIT (2)
\t\t\tmax_mtu:\t\t4096 (5)
\t\t\tactive_mtu:\t\t2048 (4)
\t\t\tlink_layer:\t\tInfiniBand
"""
SNIP_RDMA_LINK = ("link mlx5_0/1 state ACTIVE physical_state LINK_UP netdev ens1np0\n"
                  "link mlx5_1/1 state DOWN physical_state DISABLED netdev ens2np0\n")
SNIP_GIDS = ("DEV\tPORT\tINDEX\tGID\t\t\t\t\tIPv4  \t\tVER\tDEV\n"
             "---\t----\t-----\t---\t\t\t\t\t------------  \t---\t---\n"
             "mlx5_0\t1\t1\tfe80:0000:0000:0000:ba3f:d2ff:fe47:0020\t\t\tv2\tens1np0\n"
             "mlx5_0\t1\t3\t0000:0000:0000:0000:0000:ffff:0a64:0001\t10.100.0.1  \tv2\tens1np0\n"
             "n_gids_found=2\n")
SNIP_ETHTOOL_I = ("driver: mlx5_core\nversion: 24.04-0.6.6\nfirmware-version: 28.36.2024 (MT_0000000838)\n"
                  "expansion-rom-version: \nbus-info: 0000:9b:00.0\n")
SNIP_IP_LINK = ("6: ens3np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP mode DEFAULT group "
                "default qlen 1000\\    link/ether b8:3f:d2:47:00:22 brd ff:ff:ff:ff:ff:ff\n")
SNIP_IP_ADDR = "6: ens3np0    inet 10.100.2.1/31 scope global ens3np0\\       valid_lft forever preferred_lft forever\n"


class Skip(Exception):
    """Raised by a check that cannot run here (e.g. generator stripped from the student release)."""


def load(impl: str) -> tuple[ModuleType, ModuleType]:
    base = HERE / "starter" if impl == "starter" else HERE.parent / "solutions" / "lab"
    mods = []
    for name in ("readiness", "perftest_analysis"):
        spec = importlib.util.spec_from_file_location(f"ch08_{impl}_{name}", base / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = mod          # dataclasses need the module registered
        spec.loader.exec_module(mod)
        mods.append(mod)
    return mods[0], mods[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    try:
        R, P = load(args.impl)
    except Exception as exc:  # noqa: BLE001 - report import errors without a traceback
        print(f"FAIL import: could not import {args.impl} modules: {exc!r}")
        return 1

    cache: dict[str, object] = {}

    def readiness():
        if "r" not in cache:
            cache["r"] = R.run_readiness(DATA / "inventory", DATA / "baseline.yaml")
        return cache["r"]

    def summary():
        if "s" not in cache:
            cache["s"] = P.summarize(DATA / "perftest")
        return cache["s"]

    def c_devinfo():
        d = R.parse_ibv_devinfo(SNIP_DEVINFO)["mlx5_9"]
        assert d["fw_ver"] == "28.39.1002", f"fw_ver={d.get('fw_ver')}"
        assert d["state"] == "PORT_INIT", f"state={d.get('state')} (want symbolic name only)"
        assert d["active_mtu"] == 2048 and d["max_mtu"] == 4096, "MTUs must be bytes as int"
        assert d["link_layer"] == "InfiniBand", f"link_layer={d.get('link_layer')}"
        return "fields parsed"

    def c_rdma_link():
        d = R.parse_rdma_link(SNIP_RDMA_LINK)
        assert d["mlx5_1"]["state"] == "DOWN" and d["mlx5_1"]["physical_state"] == "DISABLED"
        assert d["mlx5_0"]["netdev"] == "ens1np0" and d["mlx5_0"]["port"] == 1
        return "state/physical_state/netdev parsed"

    def c_gids():
        rows = R.parse_show_gids(SNIP_GIDS)
        assert len(rows) == 2, f"expected 2 GID rows, got {len(rows)}"
        r3 = [r for r in rows if r["index"] == 3][0]
        assert r3["ipv4"] == "10.100.0.1" and r3["ver"] == "v2" and r3["netdev"] == "ens1np0"
        r1 = [r for r in rows if r["index"] == 1][0]
        assert r1["ipv4"] is None, "rows without IPv4 must have ipv4=None"
        return "v1/v2 and IPv4 columns parsed"

    def c_ethtool():
        e = R.parse_ethtool_i(SNIP_ETHTOOL_I)
        assert e["firmware"] == "28.36.2024", f"firmware={e['firmware']!r} (strip the PSID)"
        assert e["driver"] == "mlx5_core" and e["version"] == "24.04-0.6.6" and e["bus_info"] == "0000:9b:00.0"
        assert R.parse_ethtool_speed("\tSpeed: 400000Mb/s\n") == 400000
        assert R.parse_ethtool_speed("\tSpeed: Unknown!\n") is None
        return "driver/firmware/speed parsed"

    def c_ip():
        lk = R.parse_ip_link(SNIP_IP_LINK)
        assert lk["ens3np0"]["mtu"] == 9000 and lk["ens3np0"]["state"] == "UP"
        ad = R.parse_ip_addr(SNIP_IP_ADDR)
        assert ad["ens3np0"] == ["10.100.2.1/31"], f"got {ad}"
        return "MTU/state/addresses parsed"

    def c_qos_env():
        assert R.parse_dcb_pfc("prio-pfc 0:off 1:off 2:off 3:on 4:off 5:off 6:off 7:off\n") == {3}
        assert R.parse_dcb_app_dscp("dscp-prio 26:3 48:6\n") == {26: 3, 48: 6}
        env = R.parse_env("# c\nNCCL_IB_GID_INDEX=3\n\nNCCL_IB_TC=106\n")
        assert env == {"NCCL_IB_GID_INDEX": "3", "NCCL_IB_TC": "106"}, f"got {env}"
        assert "nvidia_peermem" in R.loaded_modules("nvidia_peermem         16384  0\nmlx5_ib 1 0\n")
        return "dcb, env file and lsmod parsed"

    def c_clean_node():
        import yaml
        base = yaml.safe_load((DATA / "baseline.yaml").read_text(encoding="utf-8"))
        inv = R.split_sections((DATA / "inventory" / "orion-n01.txt").read_text(encoding="utf-8"))
        fs = R.check_node(inv, base)
        assert not fs, f"clean node produced {len(fs)} finding(s), e.g. {fs[0]}"
        return "orion-n01 passes every check (no false positives)"

    def c_findings():
        findings, _ = readiness()
        got = {h(f.key) for f in findings}
        hit = len(got & EXPECTED_FINDINGS)
        extra = len(got - EXPECTED_FINDINGS)
        assert hit == len(EXPECTED_FINDINGS) and extra == 0, (
            f"matched {hit}/{len(EXPECTED_FINDINGS)} expected findings, {extra} unexpected")
        return f"all {hit} planted-fault findings detected, no extras"

    def c_verdicts():
        _, verdicts = readiness()
        got = {h(f"{k}|{v}") for k, v in verdicts.items()}
        assert got == EXPECTED_VERDICTS, f"{len(got & EXPECTED_VERDICTS)}/{len(EXPECTED_VERDICTS)} verdicts correct"
        return "per-node READY/NOT_READY verdicts correct"

    def c_report():
        findings, verdicts = readiness()
        rep = R.render_report(findings, verdicts)
        assert all(host in rep for host in verdicts), "every host must appear in the report"
        assert "NOT_READY" in rep and "READY" in rep
        return f"report rendered ({len(rep.splitlines())} lines)"

    def c_parse_perf():
        bw = P.parse_bw((DATA / "perftest" / "bw_n01-n02_rail0.txt").read_text(encoding="utf-8"))
        assert len(bw) == 23 and int(bw["bytes"].iloc[-1]) == 8388608, f"bw rows={len(bw)}"
        assert 380 < float(bw["bw_avg_gbps"].iloc[-1]) < 395
        lat = P.parse_lat((DATA / "perftest" / "lat_n01-n02_rail0.txt").read_text(encoding="utf-8"))
        assert len(lat) == 16 and {"p99_us", "p999_us", "t_typical_us"} <= set(lat.columns)
        assert P.half_bw_bytes(bw) == 8192, f"n1/2={P.half_bw_bytes(bw)}"
        return "bw/lat tables parsed; plateau and n1/2 computed"

    def c_summary():
        df = summary()
        assert len(df) == 32, f"expected 32 pair/rail rows, got {len(df)}"
        med = float(df["plateau_gbps"].median())
        assert 380 < med < 395, f"fleet median plateau {med:.1f} Gb/s out of range"
        return f"32 rows, fleet median plateau {med:.1f} Gb/s"

    def c_flags():
        df = summary()
        bw = {h(f"{r.pair}|{r.rail}|BW") for r in df.itertuples() if r.bw_flag}
        tail = {h(f"{r.pair}|{r.rail}|TAIL") for r in df.itertuples() if r.tail_flag}
        assert bw == EXPECTED_BW_FLAGS, f"bandwidth flags wrong ({len(bw)} flagged)"
        assert tail == EXPECTED_TAIL_FLAGS, f"tail-latency flags wrong ({len(tail)} flagged)"
        return "underperforming pair and tail-latency pair flagged"

    def c_pcie():
        pc = P.pcie_downgrades(DATA / "perftest" / "pcie_link.csv")
        assert len(pc) == 1, f"expected 1 downgraded link, got {len(pc)}"
        return "PCIe downgrade correlated"

    def c_regenerate():
        gen = HERE / "tools" / "generate_data.py"
        if not gen.exists():
            raise Skip("lab/tools/ not present (student release); regeneration check is instructor-only")
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([sys.executable, str(gen), "--out", td], check=True, capture_output=True)
            diffs = [str(f.relative_to(DATA)) for f in sorted(DATA.rglob("*")) if f.is_file()
                     and (Path(td) / f.relative_to(DATA)).read_bytes() != f.read_bytes()]
        assert not diffs, f"regenerated data differs from committed data: {diffs[:3]}"
        return "generator reproduces data/ byte-for-byte"

    checks: list[tuple[str, Callable[[], str]]] = [
        ("parse_ibv_devinfo", c_devinfo), ("parse_rdma_link", c_rdma_link), ("parse_show_gids", c_gids),
        ("parse_ethtool", c_ethtool), ("parse_ip", c_ip), ("parse_qos_env_lsmod", c_qos_env),
        ("no_false_positive_clean_node", c_clean_node), ("readiness_findings", c_findings),
        ("node_verdicts", c_verdicts), ("render_report", c_report), ("parse_perftest", c_parse_perf),
        ("perftest_summary", c_summary), ("perftest_flags", c_flags), ("pcie_correlation", c_pcie),
        ("data_regenerates_identically", c_regenerate),
    ]
    passed = skipped = 0
    for name, fn in checks:
        try:
            msg = fn()
            print(f"PASS {name}: {msg}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except NotImplementedError as exc:
            print(f"TODO {name}: not implemented ({exc})")
        except AssertionError as exc:
            print(f"FAIL {name}: {exc or 'assertion failed'}")
        except Exception as exc:  # noqa: BLE001 - learners get a reason, not a traceback
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(checks) - skipped} checks passed, {skipped} skipped ({args.impl})")
    return 0 if passed == len(checks) - skipped else 1


if __name__ == "__main__":
    sys.exit(main())
