#!/usr/bin/env python3
"""Checker for the Chapter 5 lab (GPU/NIC topology mapping and aligned vs misaligned all-reduce model).

Usage:
    python check.py                    # check starter/topo_mapper.py
    python check.py --impl solution    # instructor reference (not in the student release)

Prints one PASS / FAIL / TODO line per check; exit 0 only if every check passes. Expected values are
independent facts about the supplied captures or are computed here from first principles; the checker
never calls the reference solution.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import re
import sys
from pathlib import Path
from typing import Callable

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
HOSTS = DATA / "hosts"
MODULE = "topo_mapper.py"


def load_impl(impl: str):
    path = (HERE / "starter" / MODULE) if impl == "starter" else (HERE.parent / "solutions" / "lab" / MODULE)
    if not path.exists():
        print(f"Implementation not found: {path}\n(The solutions folder is removed from the student release.)")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(f"ch05_{impl}_topo_mapper", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        assert spec.loader is not None
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import — could not import {path.name}: {type(exc).__name__}: {exc}")
        sys.exit(1)
    return mod


def text(host: str, name: str) -> str:
    return (HOSTS / host / name).read_text(encoding="utf-8")


def raw_topo(host: str) -> dict:
    """Minimal independent read of the topo matrix: {(row, col): label}."""
    lines = text(host, "nvidia-smi_topo_m.txt").splitlines()
    cols = [c.strip() for c in lines[0].split("\t")[1:19]]
    out = {}
    for ln in lines[1:19]:
        p = ln.split("\t")
        for c, v in zip(cols, p[1:19]):
            out[(p[0].strip(), c)] = v.strip()
    return out


# ---- checks ---------------------------------------------------------------------------
def c_bdf(m):
    cases = {"00000000:1A:00.0": "0000:1a:00.0", "0000:19:00.0": "0000:19:00.0", "c2:00.0": "0000:c2:00.0",
             " 00000001:05:00.1 ": "0001:05:00.1"}
    for k, v in cases.items():
        assert m.normalize_bdf(k) == v, f"normalize_bdf({k!r}) -> {m.normalize_bdf(k)!r}, expected {v!r}"
    return "nvidia-smi, lspci and lstopo address forms normalized"


def c_topo(m):
    t = m.parse_topo_matrix(text("orion-n17", "nvidia-smi_topo_m.txt"))
    assert len(t["devices"]) == 18, f"expected 18 devices (8 GPU + 10 NIC), got {len(t['devices'])}"
    exp = raw_topo("orion-n17")
    bad = [k for k, v in exp.items() if t["rel"].get(k) != v]
    assert not bad, f"{len(bad)} relations differ, e.g. {bad[0]}: {t['rel'].get(bad[0])} vs {exp[bad[0]]}"
    assert t["rel"][("GPU3", "NIC4")] == "SYS" and t["rel"][("GPU0", "NIC1")] == "PIX"
    assert t["nic_names"]["NIC4"] == "mlx5_3" and len(t["nic_names"]) == 10, "NIC legend not parsed"
    assert t["numa_affinity"]["GPU4"] == 1 and t["cpu_affinity"]["GPU0"] == "0-55,112-167", "affinity columns wrong"
    return "324 relations, NIC legend and CPU/NUMA affinity parsed"


def c_lstopo(m):
    d = m.parse_lstopo(text("orion-n01", "lstopo.txt"))
    kinds = pd.Series([v["kind"] for v in d.values()]).value_counts().to_dict()
    assert kinds.get("GPU") == 8 and kinds.get("NIC") == 10, f"device kinds {kinds}"
    r = d["0000:19:00.0"]
    assert r["name"] == "mlx5_0" and r["netdev"] == "enp25s0np0" and r["package"] == 0, f"bad record {r}"
    g = d["0000:18:00.0"]
    assert g["name"] == "nvml0" and len(g["ancestors"]) == 6 and g["ancestors"][0].startswith("HB"), f"bad GPU record {g}"
    assert g["ancestors"][:5] == r["ancestors"][:5] and g["ancestors"][5] != r["ancestors"][5], \
        "GPU0 and its NIC must share the leaf switch but sit under different downstream ports"
    assert d["0000:0d:00.0"]["ancestors"][0] == g["ancestors"][0], "FE NIC and GPU0 share a host bridge"
    return "8 GPUs, 10 NICs, ancestors and names recovered"


def c_classify(m):
    for host in ("orion-n01", "orion-n17"):
        d = m.parse_lstopo(text(host, "lstopo.txt"))
        exp = raw_topo(host)
        legend = dict(re.findall(r"^\s*(NIC\d+):\s*(\S+)", text(host, "nvidia-smi_topo_m.txt"), re.M))
        by_name = {v["name"]: v for v in d.values() if v["name"]}
        for gi in range(8):
            for nic, hca in legend.items():
                got = m.classify_path(by_name[f"nvml{gi}"], by_name[hca])
                assert got == exp[(f"GPU{gi}", nic)], f"{host} GPU{gi}-{nic}: lstopo says {got}, nvidia-smi {exp[(f'GPU{gi}', nic)]}"
    return "lstopo-derived relations match nvidia-smi on all 160 GPU-NIC pairs"


def c_small_parsers(m):
    inv = m.parse_gpu_inventory(text("orion-n17", "gpu_inventory.csv"))
    assert list(inv.columns[:3]) == ["index", "uuid", "bdf"] and len(inv) == 8 and inv.loc[3, "bdf"] == "0000:42:00.0"
    v = m.parse_lspci_vmm(text("orion-n17", "lspci_vmm.txt"))
    assert v["0000:86:00.0"]["slot"] == 11 and v["0000:86:00.0"]["numa"] == 1, "misplaced NIC slot/NUMA not parsed"
    nd = m.parse_ibdev2netdev(text("orion-n01", "ibdev2netdev.txt"))
    assert nd["mlx5_8"] == "enp13s0np0" and len(nd) == 10
    ll = m.parse_lldp(text("orion-n23", "lldp.txt"))
    assert ll["enp153s0np0"]["chassis"] == "orion-be-leaf-r5" and ll["enp153s0np0"]["port"] == "Ethernet23"
    assert m.rail_from_chassis("orion-be-leaf-r7") == 7 and m.rail_from_chassis("orion-fe-leaf-01") is None
    return "inventory, lspci -vmm, ibdev2netdev, LLDP parsed"


def c_gdr(m):
    a = m.parse_gdr(text("orion-n01", "gdr_prereqs.txt"))
    assert a["peermem"] and a["iommu_passthrough"] and not a["acs_redirect_ports"], f"n01 should be clean: {a}"
    b = m.parse_gdr(text("orion-n02", "gdr_prereqs.txt"))
    assert len(b["acs_redirect_ports"]) == 16 and not b["iommu_passthrough"] and b["iommu_enabled"], f"n02: {b}"
    c = m.parse_gdr(text("orion-n23", "gdr_prereqs.txt"))
    assert not c["peermem"] and c["driver"] == "550.127.05", f"n23: {c}"
    return "peer-memory module, IOMMU mode, ACS and driver version extracted"


REQUIRED = ["host", "gpu_index", "gpu_uuid", "gpu_bdf", "gpu_numa", "rail", "rail_nic", "rail_nic_bdf",
            "rail_nic_numa", "rail_nic_slot", "rail_relation", "nearest_nic", "nearest_relation",
            "nearest_nic_rail", "relation_crosscheck_ok", "aligned"]


def c_mapping(m):
    a = m.build_mapping(HOSTS / "orion-n01")
    missing = [c for c in REQUIRED if c not in a.columns]
    assert not missing, f"missing columns {missing}"
    assert len(a) == 8 and a["aligned"].all() and (a["rail_relation"] == "PIX").all(), "n01 must be fully aligned"
    inv = pd.read_csv(HOSTS / "orion-n01" / "gpu_inventory.csv", skipinitialspace=True)
    assert list(a.sort_values("gpu_index")["gpu_uuid"]) == list(inv["uuid"]), "UUIDs must come from the inventory"
    assert a["relation_crosscheck_ok"].all()
    b = m.build_mapping(HOSTS / "orion-n17").set_index("gpu_index")
    g3 = b.loc[3]
    assert (g3["rail_nic"], g3["rail_relation"], int(g3["rail_nic_slot"]), int(g3["rail_nic_numa"])) == ("mlx5_3", "SYS", 11, 1), \
        f"n17 GPU3 rail NIC wrong: {g3[['rail_nic', 'rail_relation', 'rail_nic_slot', 'rail_nic_numa']].to_dict()}"
    assert g3["nearest_nic"] == "mlx5_2" and not g3["aligned"], "n17 GPU3 nearest should be mlx5_2 and not aligned"
    c = m.build_mapping(HOSTS / "orion-n23").set_index("gpu_index")
    assert c.loc[4, "rail_nic"] == "mlx5_5" and c.loc[4, "nearest_nic"] == "mlx5_4" and int(c.loc[4, "nearest_nic_rail"]) == 5
    assert int(a["aligned"].sum()) + int(b["aligned"].sum()) + int(c["aligned"].sum()) == 8 + 7 + 6
    return "mapping columns complete; n17 GPU3 and n23 GPU4/5 misalignment captured"


EXPECTED = {
    "orion-n01": [],
    "orion-n02": ["ACS_REDIRECT", "IOMMU_NOT_PASSTHROUGH"],
    "orion-n17": ["NIC_NOT_LOCAL", "NIC_SHARED"],
    "orion-n23": ["DRIVER_DRIFT", "GDR_PEERMEM_MISSING", "RAIL_MISMATCH", "RAIL_MISMATCH"],
}


def c_issues(m):
    for host, exp in EXPECTED.items():
        got = m.detect_issues(m.load_host(HOSTS / host))
        codes = sorted(i["code"] for i in got)
        assert codes == sorted(exp), f"{host}: expected {sorted(exp)}, got {codes}"
        for i in got:
            assert i["severity"] in ("blocker", "major", "minor") and i["detail"], f"{host} finding incomplete: {i}"
    sev = {i["code"]: i["severity"] for i in m.detect_issues(m.load_host(HOSTS / "orion-n23"))}
    assert sev["RAIL_MISMATCH"] == "blocker", "a cabling rail mismatch must block node acceptance"
    return "every planted fault found, no false positives on the clean host"


def c_rankmap(m):
    n01 = m.load_host(HOSTS / "orion-n01")
    a = m.make_rank_map([n01, n01], "aligned")
    assert len(a) == 16 and list(a["rank"]) == list(range(16)), "ranks must be 0..15 in node order"
    assert (a["relation"] == "PIX").all() and (a["sharers"] == 1).all()
    x = m.make_rank_map([n01], "cross_socket")
    assert (x["relation"] == "SYS").all(), "cross_socket map must cross the inter-socket link"
    n17 = m.load_host(HOSTS / "orion-n17")
    nn = m.make_rank_map([n17], "nearest").set_index("local_rank")
    assert nn.loc[2, "nic"] == nn.loc[3, "nic"] == "mlx5_2" and nn.loc[3, "sharers"] == 2
    al = m.make_rank_map([n17], "aligned").set_index("local_rank")
    assert al.loc[3, "nic"] == "mlx5_3" and al.loc[3, "relation"] == "SYS"
    px = m.make_rank_map([n17], "pxn").set_index("local_rank")
    assert px.loc[3, "nic"] == "mlx5_2" and px.loc[3, "relation"] == "PXB" and px.loc[3, "sharers"] == 2, \
        "PXN needs a peer GPU at <= PXB from mlx5_3; none exists on n17 (best is PHB), so GPU3 falls back to its nearest NIC"
    hp = m.make_rank_map([n01], "pxn")
    assert (hp["relation"] == "PIX").all() and list(hp["nic"]) == list(a[a["node"] == 0]["nic"]), "healthy node: PXN == aligned"
    return "aligned, nearest, cross-socket and PXN policies produce the expected NIC choices"


def c_model(m):
    params = yaml.safe_load((DATA / "path_model.yaml").read_text(encoding="utf-8"))
    mp, cv = m.path_params({"relation": "PIX", "acs": True, "host_staged": True, "sharers": 2}, params)
    assert abs(mp - 9.0) < 1e-9 and abs(cv - 0.18) < 1e-9, f"path_params -> ({mp}, {cv}), expected (9.0, 0.18)"
    gated = m.path_params({"relation": "SYS", "acs": False, "host_staged": False, "sharers": 1}, params)
    assert abs(gated[0] - 18.0) < 1e-9, "a SYS pair is beyond the PXB GDR gate and must be host-staged (18 GB/s cap)"
    flat = copy.deepcopy(params)
    for c in flat["classes"].values():
        c["cv"] = 0.0
    for mod in flat["modifiers"].values():
        if "cv_add" in mod:
            mod["cv_add"] = 0.0
    rows = []
    for node in range(4):
        for lr in range(8):
            rel = "SYS" if (node, lr) == (2, 5) else "PIX"
            rows.append({"rank": node * 8 + lr, "node": node, "host": f"h{node}", "local_rank": lr, "ring": lr,
                         "nic": f"mlx5_{lr}", "relation": rel, "acs": False, "host_staged": False, "sharers": 1})
    rm = pd.DataFrame(rows)
    size = 1 << 30
    r = m.model_allreduce(rm, flat, size, iters=20, seed=1)
    n = 32
    t = 2 * (n - 1) / n * (size / 8) / (18.0e9) + flat["alpha_ms"] / 1e3   # rail 5: SYS -> host-staged by the GDR gate
    assert abs(r["median_ms"] - t * 1e3) < 1e-6, f"median {r['median_ms']:.4f} ms, expected {t * 1e3:.4f} ms"
    exp_bus = 2 * (n - 1) / n * size / t / 1e9
    assert abs(r["busbw_median_GBps"] - exp_bus) < 1e-6 and r["cv"] < 1e-12
    return f"deterministic case: {t * 1e3:.3f} ms, busbw {exp_bus:.1f} GB/s; modifiers applied in order"


def c_scenarios(m):
    s = m.analyze(DATA)["scenarios"]
    s1, s2, s3, s4, s5, s4s = (s[k] for k in ("S1_aligned_healthy", "S2_cross_socket_healthy", "S3_scheduled_nearest",
                                              "S4_scheduled_aligned", "S5_scheduled_pxn", "S4_gdr_level_sys"))
    assert s1["n_ranks"] == 128, "the worked-example job is 16 nodes x 8 GPUs"
    assert 330 < s1["busbw_median_GBps"] < 380, f"S1 busbw {s1['busbw_median_GBps']:.1f} outside the plausible range"
    assert s2["median_ms"] > 3 * s1["median_ms"] and s2["cv"] > 10 * s1["cv"], "cross-socket map (host-staged) should be far slower and noisier"
    assert s3["busbw_median_GBps"] < 0.6 * s1["busbw_median_GBps"], "two flawed nodes should drag the whole job"
    assert s4["busbw_median_GBps"] < s3["busbw_median_GBps"] and s4["p99_ms"] > s3["p99_ms"], \
        "with the default GDR gate, forcing the SYS NIC is worse than sharing the PXB NIC"
    assert abs(s5["median_ms"] - s3["median_ms"]) < 1e-9, "PXN is not eligible on n17, so S5 must equal S3"
    assert s4s["busbw_median_GBps"] > s4["busbw_median_GBps"], "NCCL_NET_GDR_LEVEL=SYS would keep GDR on the SYS path"
    return (f"S1 {s1['busbw_median_GBps']:.0f} GB/s, S2 {s2['busbw_median_GBps']:.0f}, S3 {s3['busbw_median_GBps']:.0f}, "
            f"S4 {s4['busbw_median_GBps']:.0f}, S5 {s5['busbw_median_GBps']:.0f}, S4@SYS {s4s['busbw_median_GBps']:.0f} [MODELED]")


CHECKS: list[tuple[str, Callable]] = [
    ("normalize_bdf", c_bdf), ("parse_topo_matrix", c_topo), ("parse_lstopo", c_lstopo),
    ("classify_path", c_classify), ("small_parsers", c_small_parsers), ("parse_gdr", c_gdr),
    ("build_mapping", c_mapping), ("detect_issues", c_issues), ("make_rank_map", c_rankmap),
    ("model_allreduce", c_model), ("scenarios", c_scenarios),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mod = load_impl(args.impl)
    passed = 0
    for name, fn in CHECKS:
        try:
            msg = fn(mod)
            print(f"PASS {name} — {msg}")
            passed += 1
        except NotImplementedError:
            print(f"TODO {name} — not implemented yet")
        except AssertionError as exc:
            print(f"FAIL {name} — {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name} — {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
