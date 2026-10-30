#!/usr/bin/env python3
"""Checker for the Chapter 2 lab (ORION capacity / BOM / power / failure-domain model).

Usage:
    python check.py                    # check your starter/ implementation
    python check.py --impl solution    # check the reference solution (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
No hardware, network, or root access is used.
"""
from __future__ import annotations

import argparse
import filecmp
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

sys.dont_write_bytecode = True  # keep starter/, solutions/, tools/ free of __pycache__
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

EXPECTED_FINDINGS = {
    ("DUPLICATE_RACK", "rack-05"), ("POWER_BASIS", "rack-03"), ("CIRCUIT_OVERLOAD", "rack-07"),
    ("FLOOR_LOAD", "rack-08"), ("PORT_OVERCOMMIT", "orion-be-spine-2"), ("OVERSUBSCRIBED_LEAF", "orion-be-leaf-r5"),
    ("UPLINK_MISMATCH", "fabric"), ("UNIT_MISMATCH", "storage.aggregate_read"), ("PSU_FEED_LOSS", "HX8"),
}
EXPECTED_SPOFS = {"busway-A", "cdu-1", "mds-1", "oob-sw-1", "pdu-net-A", "slurmctld-1", "ups-A"} | {
    f"orion-be-leaf-r{r}" for r in range(8)}


class CheckFailure(Exception):
    """Raised by a check with a short human-readable reason."""


class CheckSkip(Exception):
    """Raised by a check that cannot run in this edition (generator stripped from the student release)."""


def load_impl(impl: str) -> ModuleType:
    path = HERE / "starter" / "capacity_model.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "capacity_model.py"
    if not path.exists():
        raise SystemExit(f"implementation not found: {path}")
    spec = importlib.util.spec_from_file_location(f"capacity_model_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def close(name: str, got: Any, want: float, rel: float = 0.01) -> None:
    if got is None:
        raise CheckFailure(f"missing key {name}")
    if abs(float(got) - want) > rel * abs(want) + 1e-9:
        raise CheckFailure(f"{name}={got!r}, expected about {want}")


def equal(name: str, got: Any, want: Any) -> None:
    if got != want:
        raise CheckFailure(f"{name}={got!r}, expected {want!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = parser.parse_args()
    m = load_impl(args.impl)
    inputs = m.load_inputs(DATA)
    cache: dict[str, Any] = {}

    def get(key: str, fn: Callable[[], Any]) -> Any:
        if key not in cache:
            cache[key] = fn()
        return cache[key]

    def findings() -> set[tuple[str, str]]:
        return {(f["code"], f["item"]) for f in get("f", lambda: m.validate_inputs(inputs))}

    def bom() -> dict:
        return get("b", lambda: m.compute_bom(inputs["intent"]))

    def pc() -> dict:
        return get("p", lambda: m.compute_power_cooling(inputs["intent"], inputs["facility"]))

    def cap() -> dict:
        return get("c", lambda: m.compute_capacity(inputs["intent"], inputs["storage"]))

    def spofs() -> list:
        return get("s", lambda: m.find_spofs(inputs["design"]))

    # ------------------------------------------------------------------ checks
    def c_regen() -> str:
        if not (HERE / "tools" / "generate_inputs.py").exists():
            raise CheckSkip("generator not shipped in this edition (instructor material)")
        sys.path.insert(0, str(HERE / "tools"))
        try:
            import generate_inputs  # type: ignore
        finally:
            sys.path.pop(0)
        with tempfile.TemporaryDirectory() as tmp:
            generate_inputs.generate(Path(tmp))
            names = sorted(p.name for p in DATA.iterdir() if p.is_file())
            _, mismatch, errors = filecmp.cmpfiles(DATA, tmp, names, shallow=False)
            if mismatch or errors:
                raise CheckFailure(f"regenerated data differs: {mismatch + errors}")
        return f"{len(names)} files byte-identical"

    def c_rack_findings() -> str:
        want = {f for f in EXPECTED_FINDINGS if f[0] in {"DUPLICATE_RACK", "POWER_BASIS", "CIRCUIT_OVERLOAD", "FLOOR_LOAD"}}
        missing = want - findings()
        if missing:
            raise CheckFailure(f"{len(missing)} rack-plan flaw(s) not detected")
        return f"{len(want)} rack-plan flaws detected"

    def c_fabric_findings() -> str:
        want = {f for f in EXPECTED_FINDINGS if f[0] in {"PORT_OVERCOMMIT", "OVERSUBSCRIBED_LEAF", "UPLINK_MISMATCH"}}
        missing = want - findings()
        if missing:
            raise CheckFailure(f"{len(missing)} fabric-plan flaw(s) not detected")
        return f"{len(want)} fabric-plan flaws detected"

    def c_other_findings() -> str:
        want = {f for f in EXPECTED_FINDINGS if f[0] in {"UNIT_MISMATCH", "PSU_FEED_LOSS"}}
        missing = want - findings()
        if missing:
            raise CheckFailure(f"{len(missing)} storage/node flaw(s) not detected")
        return "storage unit and PSU feed-loss flaws detected"

    def c_no_false_positives() -> str:
        extra = findings() - EXPECTED_FINDINGS
        if extra:
            raise CheckFailure(f"{len(extra)} false positive(s), e.g. {sorted(extra)[0]}")
        return "no false positives"

    def c_bom() -> str:
        b = bom()
        for k, v in {"gpus": 256, "gpu_racks": 8, "gpu_node_rack_units": 256, "rack_units_per_gpu_rack": 32,
                     "backend_switches": 12, "host_backend_links": 256, "leaf_spine_links": 256,
                     "backend_links_total": 512, "backend_switch_ports": 768, "total_racks": 13}.items():
            equal(k, b.get(k), v)
        return "servers, RUs, switches, ports and links correct"

    def c_bom_optics() -> str:
        b = bom()
        equal("transceivers_single_port", b.get("transceivers_single_port"), 1024)
        equal("switch_side_twin_port_modules", b.get("switch_side_twin_port_modules"), 384)
        equal("frontend_node_ports", b.get("frontend_node_ports"), 64)
        equal("oob_ports", b.get("oob_ports"), 86)
        return "optics, frontend and OOB counts correct"

    def c_rack_power() -> str:
        p = pc()
        close("rack_it_max_kw", p.get("rack_it_max_kw"), 41.0)
        close("rack_design_kw", p.get("rack_design_kw"), 45.1)
        close("usable_per_side_kw", p.get("usable_per_side_kw"), 65.55)
        close("headroom_per_side_kw", p.get("headroom_per_side_kw"), 20.45, rel=0.02)
        return "rack max 41.0 kW, design 45.1 kW, 65.6 kW usable per side"

    def c_cooling() -> str:
        p = pc()
        close("rack_liquid_kw", p.get("rack_liquid_kw"), 30.75)
        close("coolant_flow_lpm", p.get("coolant_flow_lpm"), 46.38)
        close("rack_air_cfm", p.get("rack_air_cfm"), 1199.4)
        close("all_air_rack_cfm", p.get("all_air_rack_cfm"), 4797.6)
        close("cdu_utilization", p.get("cdu_utilization"), 0.82)
        return "coolant 46.4 L/min, residual air ~1,200 CFM, CDU 82 % loaded"

    def c_cluster_energy() -> str:
        p = pc()
        close("cluster_it_max_kw", p.get("cluster_it_max_kw"), 382.0)
        close("facility_max_kw", p.get("facility_max_kw"), 477.5)
        close("annual_energy_mwh", p.get("annual_energy_mwh"), 3587.2)
        close("annual_energy_cost_usd", p.get("annual_energy_cost_usd"), 286978)
        return "cluster 382 kW IT max, ~3,587 MWh/yr"

    def c_capacity() -> str:
        c = cap()
        close("total_hbm_gb", c.get("total_hbm_gb"), 20480)
        close("training_state_per_gpu_gb", c.get("training_state_per_gpu_gb"), 35.0)
        close("injection_tbps", c.get("injection_tbps"), 102.4)
        close("bisection_tbps_per_direction", c.get("bisection_tbps_per_direction"), 51.2)
        return "HBM, per-GPU training state and bisection correct"

    def c_storage_util() -> str:
        c = cap()
        close("storage_read_gbytes_s", c.get("storage_read_gbytes_s"), 160.0)
        close("storage_read_per_gpu_gbytes_s", c.get("storage_read_per_gpu_gbytes_s"), 0.625)
        close("checkpoint_write_s", c.get("checkpoint_write_s"), 12.25)
        close("allocated_gpu_hours_per_year", c.get("allocated_gpu_hours_per_year"), 1906176)
        return "storage per GPU, checkpoint lower bound and GPU-hours correct"

    def c_spofs() -> str:
        got = {d["component"] for d in spofs()}
        missing, extra = EXPECTED_SPOFS - got, got - EXPECTED_SPOFS
        if missing or extra:
            raise CheckFailure(f"{len(missing)} SPOF(s) missed, {len(extra)} wrongly flagged")
        return f"{len(got)} SPOFs found (incl. hidden power-path SPOFs)"

    def c_spof_impact() -> str:
        by = {d["component"]: d["services_lost"] for d in spofs()}
        equal("cdu-1 services_lost", by.get("cdu-1"), ["svc-inference", "svc-training"])
        equal("oob-sw-1 services_lost", by.get("oob-sw-1"), ["svc-management"])
        equal("mds-1 services_lost", by.get("mds-1"), ["svc-training"])
        return "service impact per SPOF correct"

    checks: list[tuple[str, Callable[[], str]]] = [
        ("data_regenerates_identically", c_regen),
        ("validate_rack_plan", c_rack_findings),
        ("validate_fabric_plan", c_fabric_findings),
        ("validate_storage_and_node", c_other_findings),
        ("validate_no_false_positives", c_no_false_positives),
        ("bom_counts", c_bom),
        ("bom_optics_frontend_oob", c_bom_optics),
        ("rack_power_budget", c_rack_power),
        ("rack_cooling_budget", c_cooling),
        ("cluster_power_energy", c_cluster_energy),
        ("capacity_compute_fabric", c_capacity),
        ("capacity_storage_utilization", c_storage_util),
        ("spof_set", c_spofs),
        ("spof_service_impact", c_spof_impact),
    ]
    passed = skipped = 0
    for name, fn in checks:
        try:
            msg = fn()
            print(f"PASS {name}: {msg}")
            passed += 1
        except CheckSkip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc.args[0] if exc.args else 'function'}()")
        except CheckFailure as exc:
            print(f"FAIL {name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - learner code may raise anything
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(checks) - skipped} checks passed, {skipped} skipped ({args.impl})")
    return 0 if passed == len(checks) - skipped else 1


if __name__ == "__main__":
    sys.exit(main())
