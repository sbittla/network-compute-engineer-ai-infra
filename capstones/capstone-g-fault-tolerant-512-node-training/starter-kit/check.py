#!/usr/bin/env python3
"""Checker for the Capstone G starter kit (fault-tolerant 512-node training operations).

Usage:
    python check.py                    # check your starter/ftops.py (default)
    python check.py --impl solution    # instructor: check ../instructor/reference/ftops.py

Contract (docs/LAB_STANDARDS.md §4): one line per check (PASS/FAIL/TODO), never a traceback,
exit 0 only when every check passes. SIMULATED dataset, no network, no hardware, < 60 s.
"""
from __future__ import annotations

import argparse
import copy
import filecmp
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
MODULE = "ftops"
DATA = HERE / "data"
FAULT_GPU = "gpu:orionxl-n377:5"
FLAKY_HCA = "hca:orionxl-n213:mlx5_3"



class Skip(Exception):
    """A check that cannot run in this copy (e.g. the instructor-only generator is absent)."""


def load(impl: str) -> ModuleType | None:
    path = (HERE / "starter" / f"{MODULE}.py") if impl == "starter" else (
        HERE.parent / "instructor" / "reference" / f"{MODULE}.py")
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("(The instructor/ folder is removed from student releases; use --impl starter.)")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  import -- {type(exc).__name__}: {exc}")
        return None
    return mod


class Ctx:
    """Lazily computed pipeline so one unimplemented stage reports TODO instead of cascading noise."""

    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.d = m.load_dataset(DATA)
        self._c: dict = {}

    def get(self, key: str):
        if key not in self._c:
            m, d = self.m, self.d
            if key == "maps":
                v = m.build_maps(d["inventory"])
            elif key == "norm":
                v = m.normalize_events(d["events"], d["offsets"], self.get("maps"))
            elif key == "scores":
                v = m.health_scores(self.get("norm"))
            elif key == "cls":
                v = m.classify(self.get("norm"), self.get("scores"), d["progress"], self.get("maps"),
                               d["config"]["scoring"])
            elif key == "plan":
                v = m.quarantine_plan(self.get("cls"), self.get("maps"))
            elif key == "ckpt":
                v = m.select_checkpoint(d["checkpoints"])
            else:
                raise KeyError(key)
            self._c[key] = v
        return self._c[key]


def c_data(_: Ctx) -> str:
    if not (HERE / "tools" / "generate_data.py").exists():
        raise Skip("generator is instructor copy only (tools/ absent); data/ used as shipped")
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", tmp],
                              capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, f"generator failed: {proc.stderr.strip()[-200:]}"
        files = sorted(p.name for p in DATA.iterdir() if p.is_file())
        _, mismatch, errors = filecmp.cmpfiles(DATA, tmp, files, shallow=False)
        assert not mismatch and not errors, f"regenerated files differ: {mismatch + errors}"
        size = sum(p.stat().st_size for p in DATA.iterdir())
        assert size < 2_000_000, f"data/ is {size} B (limit 2 MB)"
    return f"{len(files)} files byte-identical, {size / 1e6:.2f} MB"


def c_maps(c: Ctx) -> str:
    m = c.get("maps")
    assert len(m["rank"]) == 3840, f"expected 3,840 job ranks, got {len(m['rank'])}"
    r = m["rank"][3013]
    assert (r["node"], r["gpu"], r["gpu_bdf"], r["numa"], r["hca"], r["rail"]) == \
        ("orionxl-n377", 5, "0000:ab:00.0", 1, "mlx5_5", 5), f"rank 3013 -> {r}"
    assert m["port"][("orionxl-be-leaf-p06-r3", 22)] == ("orionxl-n213", "mlx5_3"), \
        "port map must come from the LLDP-observed inventory"
    assert m["node_ranks"].get("orionxl-n483") == [], "spare nodes carry no ranks"
    return "3,840 ranks; rank 3013 -> orionxl-n377 GPU5 (0000:ab:00.0, NUMA 1, mlx5_5, rail 5)"


def c_cabling(c: Ctx) -> str:
    diffs = c.m.cabling_discrepancies(c.d["inventory"], c.d["cabling_plan"])
    nodes = sorted(x["node"] for x in diffs)
    assert nodes == ["orionxl-n213", "orionxl-n214"], f"discrepancies: {diffs}"
    return "2 DCIM-vs-LLDP mismatches on orionxl-be-leaf-p06-r3 ports 21/22"


def c_normalize(c: Ctx) -> str:
    n = c.get("norm")
    assert len(n) == len(c.d["events"]), "one normalised row per event"
    assert list(n["utc"]) == sorted(n["utc"]), "rows must be sorted by true time"
    x = n[(n["kind"] == "xid") & (n["xid"] == 94)]
    assert len(x) == 1 and x.iloc[0]["component"] == FAULT_GPU, f"Xid 94 row: {x.to_dict('records')}"
    sk = n[(n["host"] == "orionxl-n042") & (n["kind"] == "nccl_timeout")]
    first_timeout = n[n["kind"] == "nccl_timeout"]["utc"].min()
    assert len(sk) and sk["utc"].min() > first_timeout, \
        "orionxl-n042 still reports the earliest timeout: apply clock_offsets (its clock is 180 s behind)"
    sw = n[n["kind"] == "switch_counter"]
    assert set(sw["component"]) == {FLAKY_HCA}, f"switch counters mapped to {set(sw['component'])}"
    return "true-time ordering; Xid 94 -> GPU5 via BDF; skew corrected; switch port -> LLDP peer"


def c_scores(c: Ctx) -> str:
    s = c.get("scores")
    got = {k: v["score"] for k, v in s.items()}
    exp = {FAULT_GPU: 100, FLAKY_HCA: 100, "gpu:orionxl-n101:2": 20, "gpu:orionxl-n099:2": 10}
    assert got == exp, f"scores {got}; expected {exp}"
    return "4 non-zero components; background correctable ECC scored 0; orionxl-n214 untouched"


def c_classify(c: Ctx) -> str:
    cl = c.get("cls")
    assert cl["first_stalled_ranks"] == [3013], f"first stalled {cl['first_stalled_ranks']}"
    assert cl["proven_cause"] == FAULT_GPU, f"proven cause {cl['proven_cause']}"
    assert cl["independent_faults"] == [FLAKY_HCA], f"independent {cl['independent_faults']}"
    assert cl["watch"] == ["gpu:orionxl-n099:2", "gpu:orionxl-n101:2"], f"watch {cl['watch']}"
    assert str(cl["fault_utc"]).startswith("2026-11-12 03:14:07"), f"fault_utc {cl['fault_utc']}"
    return "cause GPU5 on orionxl-n377 (rank 3013); flaky HCA correlated but not causal"


def c_quarantine(c: Ctx) -> str:
    plan = c.get("plan")
    drains = sorted({a["drain_node"] for a in plan if a["drain_node"]})
    assert drains == ["orionxl-n213", "orionxl-n377"], f"drained {drains}"
    q = sorted(a["component"] for a in plan if a["action"] == "quarantine")
    assert q == [FAULT_GPU, FLAKY_HCA], f"quarantined {q} (smallest repair domain: GPU / HCA)"
    ft = [a["component"] for a in plan if a["action"] == "fabric_ticket"]
    assert ft == ["switchport:orionxl-be-leaf-p06-r3:22"], f"fabric tickets {ft}"
    assert not any("orionxl-n214" in a["component"] or "orionxl-n042" in a["component"] for a in plan), \
        "red herrings (stale cabling plan, skewed clock) must not be actioned"
    return "quarantine GPU + HCA, drain 2 nodes, Fabric ticket on port 22, watch 2"


def c_checkpoint(c: Ctx) -> str:
    ck = c.get("ckpt")
    assert ck["step"] == 51474, f"selected {ck['step']}"
    assert set(ck["rejected"]) == {51750, 51612}, f"rejected {ck['rejected']}"
    bad = copy.deepcopy(c.d["checkpoints"])
    for x in bad:
        x["metadata_committed"] = False
    try:
        c.m.select_checkpoint(bad)
    except ValueError:
        return "51,474 selected; 51,750 (uncommitted, missing shards) and 51,612 (checksum) rejected"
    raise AssertionError("must raise ValueError when nothing is restorable")


def c_restart(c: Ctx) -> str:
    drains = sorted({a["drain_node"] for a in c.get("plan") if a["drain_node"]})
    rp = c.m.restart_plan(c.get("maps"), drains, c.d["spares"], c.d["quarantine_db"])
    assert rp["replacements"] == {"orionxl-n213": "orionxl-n483", "orionxl-n377": "orionxl-n484"}, \
        f"replacements {rp['replacements']}"
    for n in ("orionxl-n481", "orionxl-n482"):
        assert n in rp["excluded_spares"], f"{n} must be excluded (see spares.csv and quarantine_db.csv)"
    assert len(rp["rank_map"]) == 16 and all(v["gpu"] == c.get("maps")["rank"][k]["gpu"]
                                             for k, v in rp["rank_map"].items()), "16 ranks, GPU index preserved"
    used = set(rp["replacements"].values())
    assert not used & set(drains), "never reschedule onto a drained node"
    try:
        c.m.restart_plan(c.get("maps"), drains + [f"orionxl-n{i:03d}" for i in range(1, 40)],
                         c.d["spares"], c.d["quarantine_db"])
    except ValueError:
        return "orionxl-n213->n483, n377->n484; n481 (acceptance pending), n482 (open quarantine) excluded"
    raise AssertionError("must raise ValueError when spares run out")


def c_metrics(c: Ctx) -> str:
    cl = c.get("cls")
    met = c.m.recovery_metrics(c.d["ops_log"], cl["fault_utc"], 51797, c.get("ckpt")["step"], c.d["config"])
    exp = {"detect_s": 38.0, "isolate_s": 242.0, "rto_s": 912.0, "rpo_steps": 323, "rpo_s": 1405.0, "lost_gpu_h": 2471.5}
    wrong = {k: (met[k], v) for k, v in exp.items() if abs(met[k] - v) > 0.15}
    assert not wrong, f"(got, expected) {wrong}"
    assert met["meets"] == {"detect": True, "isolate": True, "rto": True, "rpo": False}, f"meets {met['meets']}"
    return "detect 38 s, isolate 242 s, RTO 912 s, RPO 323 steps (target missed), 2,471.5 GPU-h"


def c_validate(c: Ctx) -> str:
    good = c.m.validate_resume(c.d["loss_pre"], c.d["resume_validated"], 51474)
    bad = c.m.validate_resume(c.d["loss_pre"], c.d["resume_unvalidated"], 51612)
    assert good["ok"] and good["max_rel_dev"] < 1e-3, f"validated resume: {good}"
    assert not bad["ok"] and not bad["no_nan"] and not bad["continuity_ok"], f"unvalidated resume: {bad}"
    dl = c.m.validate_resume(c.d["loss_pre"], c.d["resume_dataloader_not_restored"], 51474)
    assert not dl["ok"] and not dl["sample_idx_ok"] and not dl["continuity_ok"],         f"data-loader state not restored must fail (sample index and a 1e-3 tolerance): {dl}"
    wrong_ckpt = c.m.validate_resume(c.d["loss_pre"], c.d["resume_validated"], 51612)
    assert not wrong_ckpt["first_step_ok"], "first step must equal restored step + 1"
    return (f"validated resume ok (max dev {good['max_rel_dev']:.5f}); corrupt-checkpoint restore and "
            f"data-loader-not-restored resume (max dev {dl['max_rel_dev']:.4f}) both fail")


CHECKS: list[tuple[str, Callable[[Ctx], str]]] = [
    ("dataset deterministic", c_data),
    ("T1 rank-to-device inventory", c_maps),
    ("T1 cabling plan vs LLDP", c_cabling),
    ("T2 telemetry normalisation and correlation", c_normalize),
    ("T3 health scoring", c_scores),
    ("T4 failure classification", c_classify),
    ("T5 quarantine policy", c_quarantine),
    ("T6 checkpoint selection", c_checkpoint),
    ("T7 restart orchestration", c_restart),
    ("T8 RTO/RPO and lost GPU-hours", c_metrics),
    ("T9 post-incident validation", c_validate),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    mod = load(args.impl)
    if mod is None:
        return 2
    try:
        ctx = Ctx(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  load_dataset -- {type(exc).__name__}: {exc}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            detail = fn(ctx)
            print(f"PASS  {name} -- {detail}")
            passed += 1
        except Skip as exc:
            print(f"SKIP  {name} -- {exc}")
            passed += 1
        except NotImplementedError as exc:
            print(f"TODO  {name} -- not implemented: {exc}")
        except AssertionError as exc:
            print(f"FAIL  {name} -- {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {name} -- {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
