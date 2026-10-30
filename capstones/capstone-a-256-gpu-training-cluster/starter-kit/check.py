#!/usr/bin/env python3
"""Capstone A starter-kit checker — ORION-256 cluster design model.

Usage:
    python check.py                    # check your starter/cluster_model.py (default)
    python check.py --impl solution    # check the instructor reference (instructor edition only)

Prints one line per check (PASS / FAIL / TODO). Exits 0 only when every check passes.
Expected values below are derived by hand from the dataset (see starter-kit/README.md, Section 4)
or recomputed independently here; they are [MODELED] numbers, not measurements.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODULE = "cluster_model"


def load(impl: str) -> ModuleType | None:
    if impl == "solution":
        path = HERE.parent / "instructor" / "reference" / f"{MODULE}.py"
    else:
        path = HERE / "starter" / f"{MODULE}.py"
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("The instructor reference is not shipped in the student edition.")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECKS: list[tuple[str, Callable[[ModuleType], str]]] = []
_CACHE: dict[str, object] = {}


def check(name: str):
    def deco(fn: Callable[[ModuleType], str]):
        CHECKS.append((name, fn))
        return fn
    return deco


def close(a: float, b: float, rel: float = 1e-3, abs_: float = 1e-9) -> bool:
    return abs(a - b) <= max(abs_, rel * abs(b))


def inputs(m: ModuleType) -> dict:
    if "inputs" not in _CACHE:
        _CACHE["inputs"] = m.load_inputs(DATA)
    return _CACHE["inputs"]  # type: ignore[return-value]


def opt(m: ModuleType, name: str) -> dict:
    return inputs(m)["design"]["fabric_options"][name]


def media_counts(df) -> dict[tuple[str, str], int]:
    return {k: int(v) for k, v in df.groupby(["link_type", "media"]).size().items()}


# ---- independent reference for the contention check -------------------------------------------

def _indep_contention(style: str, order: list[int], pp: int, dp: int, scheme: str, traffic: str,
                      uplinks: int) -> float:
    def leaf(node: int, rail: int) -> int:
        return rail if style == "rail" else node // 4
    slot = {}
    for s in range(pp):
        for d in range(dp):
            slot[(s, d)] = order[s * dp + d if scheme == "dp_contiguous" else d * pp + s]
    up: dict[int, int] = {}
    down: dict[int, int] = {}
    for r in range(8):
        pairs = []
        if traffic == "dp" and dp > 1:
            pairs = [(slot[(s, d)], slot[(s, (d + 1) % dp)]) for s in range(pp) for d in range(dp)]
        if traffic == "pp":
            pairs = [(slot[(s, d)], slot[(s + 1, d)]) for d in range(dp) for s in range(pp - 1)]
        for a, b in pairs:
            if leaf(a, r) != leaf(b, r):
                up[leaf(a, r)] = up.get(leaf(a, r), 0) + 1
                down[leaf(b, r)] = down.get(leaf(b, r), 0) + 1
    worst = max(max(up.values(), default=0), max(down.values(), default=0))
    return max(1.0, worst / uplinks)


# ---- checks --------------------------------------------------------------------------------------

@check("01 load_inputs")
def _c01(m):
    inp = inputs(m)
    assert set(inp) >= {"design", "facility", "floorplan", "hostfile"}, f"keys {sorted(inp)}"
    assert len(inp["hostfile"]) == 32, f"hostfile has {len(inp['hostfile'])} nodes, expected 32"
    assert len(inp["floorplan"]) == 13, "floorplan should list 13 racks"
    return "dataset loaded (13 racks, 32-node hostfile)"


@check("02 fabric_counts option A")
def _c02(m):
    c = m.fabric_counts(opt(m, "A_rail_1to1"), 32, 8)
    exp = {"n_leaves": 8, "n_spines": 4, "host_links": 256, "leaf_spine_links": 256,
           "uplinks_per_leaf_per_spine": 8, "switch_count": 12, "spine_ports_used": 64}
    bad = {k: (c.get(k), v) for k, v in exp.items() if c.get(k) != v}
    assert not bad, f"(got, expected): {bad}"
    assert close(c["oversubscription"], 1.0), f"oversubscription {c['oversubscription']}"
    assert not c["warnings"], f"unexpected warnings {c['warnings']}"
    return "8 leaves, 4 spines, 256+256 links, 1:1"


@check("03 fabric_counts option B")
def _c03(m):
    c = m.fabric_counts(opt(m, "B_tor_2to1"), 32, 8)
    exp = {"n_leaves": 8, "n_spines": 2, "host_links": 256, "leaf_spine_links": 128,
           "uplinks_per_leaf_per_spine": 8, "switch_count": 10}
    bad = {k: (c.get(k), v) for k, v in exp.items() if c.get(k) != v}
    assert not bad, f"(got, expected): {bad}"
    assert close(c["oversubscription"], 2.0), f"oversubscription {c['oversubscription']}"
    return "8 ToR leaves, 2 spines, 256+128 links, 2:1"


@check("04 vendor quote C is flagged")
def _c04(m):
    c = m.fabric_counts(opt(m, "C_vendor_quote_3to1"), 32, 8)
    assert c["n_leaves"] == 6, f"n_leaves {c['n_leaves']} (expected ceil(256/48) = 6)"
    assert close(c["oversubscription"], 3.0), f"oversubscription {c['oversubscription']}"
    assert len(c["warnings"]) >= 2, ("option C breaks rail alignment and loads leaves unevenly; "
                                     f"expected >= 2 warnings, got {c['warnings']}")
    return f"{len(c['warnings'])} design-rule warnings raised"


@check("05 cable plan option A")
def _c05(m):
    df = m.cable_plan(inputs(m), "A_rail_1to1")
    _CACHE["cables_A"] = df
    got = media_counts(df)
    exp = {("host", "mm"): 224, ("host", "sm"): 32, ("fabric", "dac"): 128, ("fabric", "mm"): 128}
    assert got == exp, f"media by link type {got}, expected {exp}"
    assert int(df["transceivers"].sum()) == 768, f"transceivers {df['transceivers'].sum()} != 768"
    g08 = df[(df["rack_a"] == "rack-08") | (df["rack_b"] == "rack-08")]
    assert (g08["media"] == "sm").all(), "every rack-08 link exceeds the 50 m MM reach and needs SM optics"
    return "224 MM + 32 SM host links; 128 DAC + 128 MM fabric links; 768 optics"


@check("06 cable plan option B")
def _c06(m):
    df = m.cable_plan(inputs(m), "B_tor_2to1")
    _CACHE["cables_B"] = df
    got = media_counts(df)
    exp = {("host", "dac"): 256, ("fabric", "mm"): 112, ("fabric", "sm"): 16}
    assert got == exp, f"media by link type {got}, expected {exp}"
    assert int(df["transceivers"].sum()) == 256, f"transceivers {df['transceivers'].sum()} != 256"
    return "256 in-rack DAC; 112 MM + 16 SM uplinks; 256 optics"


@check("07 feed usable kW (units trap)")
def _c07(m):
    pf, der = 0.95, 0.80
    for amps in (80, 63, 32):
        exp = math.sqrt(3) * 415 * amps / 1000 * pf * der
        got = m.feed_usable_kw({"phases": 3, "voltage_v": 415, "breaker_a": amps}, pf, der)
        assert close(got, exp, 1e-3), f"{amps} A feed: {got:.2f} kW, expected {exp:.2f} kW (sqrt(3)*V*I*PF*derate)"
    return "415 V 3-phase: 80 A -> 43.70 kW, 63 A -> 34.42 kW usable"


def _cables(m, name: str):
    key = f"cables_{name[0]}"
    if key not in _CACHE:
        _CACHE[key] = m.cable_plan(inputs(m), name)
    return _CACHE[key]


def _power(m, name: str):
    key = f"power_{name}"
    if key not in _CACHE:
        cables = _cables(m, name)
        _CACHE[key] = m.rack_power(inputs(m), name, cables)
    return _CACHE[key]


@check("08 rack power + 2N, option A")
def _c08(m):
    p = _power(m, "A_rail_1to1").set_index("rack")
    assert close(p.at["rack-01", "max_kw"], 40.8), f"rack-01 max {p.at['rack-01', 'max_kw']} kW, expected 4 x 10.2 = 40.8"
    assert close(p.at["rack-01", "sustained_kw"], 34.0), f"rack-01 sustained {p.at['rack-01', 'sustained_kw']}"
    assert close(p.at["net-01", "max_kw"], 8.336, 2e-3), (
        f"net-01 {p.at['net-01', 'max_kw']} kW; expected 4 leaves x 1.44 + 2 spines x 1.288 = 8.336 kW "
        "(switch base + switch-side optics)")
    viol = sorted(p.index[~p["ok_2n_max"].astype(bool)])
    assert viol == ["rack-05"], f"2N violations at max load {viol}, expected ['rack-05'] (63 A feeds)"
    assert p["ok_2n_sustained"].astype(bool).all(), "no rack should violate 2N at sustained load in option A"
    return "rack-05 violates 2N at max (40.8 > 34.42 kW) but fits at sustained"


@check("09 rack power + 2N, option B")
def _c09(m):
    p = _power(m, "B_tor_2to1").set_index("rack")
    assert close(p.at["rack-01", "max_kw"], 41.944, 2e-3), f"rack-01 max {p.at['rack-01', 'max_kw']} (nodes + ToR leaf + 16 MM optics)"
    viol_max = sorted(p.index[~p["ok_2n_max"].astype(bool)])
    viol_sus = sorted(p.index[~p["ok_2n_sustained"].astype(bool)])
    assert viol_max == ["rack-05"] and viol_sus == ["rack-05"], f"violations max {viol_max} sustained {viol_sus}"
    return "ToR leaf pushes rack-05 over its feed even at sustained load"


@check("10 cooling N+1 per row")
def _c10(m):
    for name in ("A_rail_1to1", "B_tor_2to1"):
        c = m.cooling_check(inputs(m), _power(m, name)).set_index("row")
        failing = sorted(c.index[~c["ok"].astype(bool)])
        assert failing == ["D"], f"{name}: failing rows {failing}, expected ['D'] (1 x 30 kW usable vs ~41 kW)"
        assert close(c.at["D", "usable_kw"], 30.0), f"row D usable {c.at['D', 'usable_kw']} (N+1 = (2-1) x 30)"
    return "row D (rack-08 overflow position) cannot cool a 41 kW rack with N+1"


@check("11 communication bytes")
def _c11(m):
    d = inputs(m)["design"]
    order = list(range(32))
    b = m.comm_step_model(d, "baseline_3d", "A_rail_1to1", order, "dp_contiguous")
    f = m.comm_step_model(d, "fsdp_dp32", "A_rail_1to1", order, "dp_contiguous")
    exp_dp = 2 * 7 / 8 * 70e9 / 32 * 2
    exp_pp = 4096 * 1024 / 8 * 8192 * 2 / 8
    exp_f = 3 * 31 / 32 * 70e9 / 8 * 2
    assert close(b["dp_bytes_per_gpu"], exp_dp), f"baseline DP bytes {b['dp_bytes_per_gpu']:.4g}, expected {exp_dp:.4g}"
    assert close(b["pp_bytes_per_gpu"], exp_pp), f"PP bytes {b['pp_bytes_per_gpu']:.4g}, expected {exp_pp:.4g}"
    assert close(f["dp_bytes_per_gpu"], exp_f), f"FSDP bytes {f['dp_bytes_per_gpu']:.4g}, expected {exp_f:.4g}"
    assert close(b["compute_time_s"], 17.39, 2e-3), f"compute time {b['compute_time_s']:.3f} s, expected ~17.39 s"
    return "DP 7.66 GB, PP 1.07 GB, FSDP 50.9 GB per GPU per step"


@check("12 oversubscription vs rank layout")
def _c12(m):
    d = inputs(m)["design"]
    hf = m.hostfile_order(inputs(m)["hostfile"])
    cases = [("A_rail_1to1", "rail", 32, "baseline_3d", list(range(32)), "pp_contiguous"),
             ("A_rail_1to1", "rail", 32, "fsdp_dp32", hf, "dp_contiguous"),
             ("B_tor_2to1", "tor", 16, "baseline_3d", list(range(32)), "dp_contiguous"),
             ("B_tor_2to1", "tor", 16, "baseline_3d", list(range(32)), "pp_contiguous"),
             ("B_tor_2to1", "tor", 16, "fsdp_dp32", list(range(32)), "dp_contiguous"),
             ("B_tor_2to1", "tor", 16, "fsdp_dp32", hf, "dp_contiguous")]
    for name, style, upl, sc, order, scheme in cases:
        s = d["workload"]["scenarios"][sc]
        r = m.comm_step_model(d, sc, name, order, scheme)
        for traffic, key in (("dp", "dp_contention"), ("pp", "pp_contention")):
            exp = _indep_contention(style, order, s["pp"], s["dp"], scheme, traffic, upl)
            assert close(r[key], exp), f"{name}/{sc}/{scheme}/{'hostfile' if order is hf else 'sorted'}: {key} {r[key]} != {exp}"
    return "rail-optimized always 1.0; ToR 1.0 or 2.0 depending on rank order"


@check("13 step-time model")
def _c13(m):
    d = inputs(m)["design"]
    hf = m.hostfile_order(inputs(m)["hostfile"])
    a = m.comm_step_model(d, "baseline_3d", "A_rail_1to1", list(range(32)), "dp_contiguous")
    b = m.comm_step_model(d, "fsdp_dp32", "B_tor_2to1", hf, "dp_contiguous")
    bh = m.comm_step_model(d, "baseline_3d", "B_tor_2to1", hf, "dp_contiguous")
    assert close(a["exposed_comm_s"], 0.1914 - 0.07, 2e-3), (
        f"A baseline exposed {a['exposed_comm_s']:.4f} s; expected max(0, 0.1914 - 0.07) = 0.1214 s "
        "(only the last micro-batch's backward hides DP when PP > 1)")
    assert close(bh["exposed_comm_s"], 0.3828 - 0.07, 2e-3), f"B hostfile baseline exposed {bh['exposed_comm_s']:.4f} s, expected 0.3128 s"
    assert close(a["step_time_s"], 17.516, 1e-3), f"A baseline step {a['step_time_s']:.3f} s, expected 17.516"
    assert close(b["step_time_s"], 18.157, 1e-3), f"B FSDP hostfile step {b['step_time_s']:.3f} s, expected 18.157"
    return "A baseline 17.52 s (0.12 s exposed); B baseline hostfile 0.31 s exposed; B FSDP hostfile 18.16 s"


@check("14 bill of materials")
def _c14(m):
    for name, exp in (("A_rail_1to1", 12_616_976.0), ("B_tor_2to1", 12_077_152.0)):
        cables = _cables(m, name)
        b = m.bom(inputs(m), name, cables)
        tot = float(b["ext_usd"].sum())
        assert close(tot, exp, 1e-3), f"{name} BOM total ${tot:,.0f}, expected ${exp:,.0f}"
        non_fiber = b[~b["item"].astype(str).str.startswith("fiber")]
        assert ((non_fiber["qty"] * non_fiber["unit_usd"] - non_fiber["ext_usd"]).abs() < 0.01).all(), \
            "ext_usd must equal qty x unit_usd"
    return "A $12.62 M vs B $12.08 M [ILLUSTRATIVE prices]"


@check("15 acceptance campaign size")
def _c15(m):
    cables = _cables(m, "A_rail_1to1")
    a = m.acceptance_counts(cables, 32, 8)
    exp = {"links_total": 512, "optical_links": 384, "dac_links": 128, "transceivers": 768,
           "nodes": 32, "rail_neighbor_pairs": 256}
    bad = {k: (a.get(k), v) for k, v in exp.items() if a.get(k) != v}
    assert not bad, f"(got, expected): {bad}"
    return "512 links / 768 optics / 256 rail-pair tests to certify (option A)"


@check("16 cost per million tokens")
def _c16(m):
    d = inputs(m)["design"]
    r = m.comm_step_model(d, "baseline_3d", "A_rail_1to1", list(range(32)), "dp_contiguous")
    sus_kw = float(_power(m, "A_rail_1to1")["sustained_kw"].sum())
    assert close(sus_kw, 310.122, 2e-3), f"option A sustained IT {sus_kw:.2f} kW, expected 8 x 34.0 + 2 x 8.336 + 16 + 5.45 = 310.12 kW"
    c = m.cost_per_million_tokens(d, 12_616_976.0, sus_kw, 1.30, r["step_time_s"], r["tokens_per_step"])
    exp_h = 12_616_976.0 / (4 * 8760) + sus_kw * 1.30 * 0.10
    assert close(c["usd_per_hour"], exp_h), f"usd/hour {c['usd_per_hour']:.2f}, expected {exp_h:.2f}"
    exp_m = exp_h / (r["tokens_per_step"] * 3600 / r["step_time_s"]) * 1e6
    assert close(c["usd_per_million_tokens"], exp_m), f"usd/M tokens {c['usd_per_million_tokens']:.4f}"
    return f"${c['usd_per_hour']:.0f}/h -> ${c['usd_per_million_tokens']:.3f} per M training tokens [MODELED]"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    try:
        mod = load(args.impl)
    except Exception as e:  # syntax error etc. in learner code
        print(f"FAIL import  {type(e).__name__}: {e}")
        return 1
    if mod is None:
        return 2
    counts = {"PASS": 0, "FAIL": 0, "TODO": 0}
    for name, fn in CHECKS:
        try:
            msg = fn(mod)
            status = "PASS"
        except NotImplementedError as e:
            status, msg = "TODO", str(e) or "not implemented yet"
        except AssertionError as e:
            status, msg = "FAIL", str(e) or "assertion failed"
        except Exception as e:  # noqa: BLE001 - report, never crash
            status, msg = "FAIL", f"{type(e).__name__}: {e}"
        counts[status] += 1
        print(f"{status:4} {name:<34} {msg}")
    total = len(CHECKS)
    print(f"\n{counts['PASS']}/{total} checks pass ({counts['TODO']} TODO, {counts['FAIL']} FAIL) [impl={args.impl}]")
    return 0 if counts["PASS"] == total else 1


if __name__ == "__main__":
    sys.exit(main())
