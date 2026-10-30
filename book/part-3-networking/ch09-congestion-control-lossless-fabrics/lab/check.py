#!/usr/bin/env python3
"""Checker for the Chapter 9 lab (Progressive Lab 3 -- congestion telemetry).

Usage:
    python check.py                    # checks lab/starter/congestion_lab.py (your work)
    python check.py --impl solution    # checks the instructor reference (not in student release)

Prints one PASS / FAIL / TODO / SKIP line per check. Exit code 0 only if every check passes or is
skipped. SKIP is used only for the instructor data-determinism check when lab/tools/ (stripped from
the student release) is absent.
Expected diagnostic answers are stored as truncated SHA-256 digests so the checker does not reveal
them; failure messages give a hint instead.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "congestion_lab.py",
    "solution": HERE.parent / "solutions" / "lab" / "congestion_lab.py",
}

EXPECT = {
    "labels": "4b8fb99030191f8f",
    "roots": "aef889be6592b1d6",
    "storm": "5d7bd725c2b4d7ee",
    "victims": "0441d101616e24e0",
    "qos": "94ab45ea8eb70585",
}


def digest(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def load(impl: str):
    path = IMPLS[impl]
    if not path.exists():
        print(f"FAIL import  {path} not found (the solution is not shipped in the student release)")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(f"congestion_lab_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    """Lazily computed shared state so that later checks reuse earlier results."""

    def __init__(self, mod):
        self.mod = mod
        self.ds = mod.load_dataset(DATA)
        self._ports = None
        self._episodes = None
        self._sim = None

    @property
    def ports(self) -> pd.DataFrame:
        if self._ports is None:
            self._ports = self.mod.prepare_ports(self.ds)
        return self._ports

    @property
    def episodes(self) -> list[dict]:
        if self._episodes is None:
            eps = self.mod.detect_episodes(self.ports)
            for ep in eps:
                ep["label"] = self.mod.classify_episode(self.ports, ep)
            self._episodes = eps
        return self._episodes

    def label_at(self, t: int) -> str:
        for ep in self.episodes:
            if ep["start"] <= t <= ep["end"]:
                return ep["label"]
        return "none"

    @property
    def sim(self) -> dict:
        if self._sim is None:
            s = self.ds["sim"]
            self._sim = {k: self.mod.simulate_incast(s["common"], v) for k, v in s["configs"].items()}
        return self._sim


# ---------------------------------------------------------------------------------------------
class Skip(Exception):
    """Raised by a check that cannot run in this environment (reported as SKIP, not FAIL)."""


GENERATOR = HERE / "tools" / "generate_telemetry.py"
SPEC = HERE.parent / "solutions" / "lab" / "planted_faults.yaml"


def c_data_determinism(ctx: Ctx):
    """Instructor check: regenerating the dataset must be byte-identical. The student release strips
    lab/tools/ (and solutions/), so this check SKIPs when the generator or its spec is absent."""
    if not GENERATOR.exists() or not SPEC.exists():
        raise Skip("generator not shipped in this release (instructor-only check)")
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run([sys.executable, str(GENERATOR), "--spec", str(SPEC), "--out", tmp],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return False, "generator failed: " + proc.stderr.strip()[-200:]
        diffs = [f.name for f in sorted(DATA.iterdir()) if f.is_file()
                 and (Path(tmp) / f.name).read_bytes() != f.read_bytes()]
    return not diffs, "regenerated data is byte-identical" if not diffs else f"differs: {diffs}"


def c_rates_unit(ctx: Ctx):
    df = pd.DataFrame({"ts_s": [0, 2, 4, 10, 12, 0, 2],
                       "dev": ["a", "a", "a", "a", "a", "b", "b"],
                       "ctr": [100, 300, 700, 1300, 5, 0, 50]})
    out = ctx.mod.counters_to_rates(df, ["dev"], ["ctr"])
    a = out[out["dev"] == "a"].sort_values("ts_s")["ctr_rate"].tolist()
    b = out[out["dev"] == "b"].sort_values("ts_s")["ctr_rate"].tolist()
    ok = (math.isnan(a[0]) and a[1] == 100 and a[2] == 200 and a[3] == 100 and math.isnan(a[4])
          and math.isnan(b[0]) and b[1] == 25)
    return ok, "first sample NaN, gap divided by true elapsed time, reset -> NaN" if ok else \
        f"got a={a}, b={b}; expected [nan, 100, 200, 100, nan] and [nan, 25]"


def c_rates_dataset(ctx: Ctx):
    p = ctx.ports
    rate_cols = [c for c in p.columns if c.endswith("_rate")]
    neg = int((p[rate_cols] < 0).sum().sum())
    ok = neg == 0 and len(rate_cols) >= 4 and "role" in p.columns
    return ok, f"{neg} negative rates; a counter that goes backwards is a reset -- did you handle it?" \
        if not ok else f"no negative rates across {len(p)} samples"


def c_labels(ctx: Ctx):
    key = "|".join(f"{t}:{ctx.label_at(t)}" for t in (50, 130, 290, 440, 540))
    ok = digest(key) == EXPECT["labels"]
    return ok, f"{len(ctx.episodes)} episodes, labels at probe times match" if ok else \
        f"labels at t=50/130/290/440/540 s were {key!r}; one or more is wrong (a busy-but-healthy port is not an episode)"


def c_episode_count(ctx: Ctx):
    n = len(ctx.episodes)
    ok = n == 3
    return ok, f"{n} episodes" + ("" if ok else " (expected a small number of distinct episodes; check merge gap and NaN handling)")


def c_roots(ctx: Ctx):
    parts = []
    for ep in ctx.episodes:
        if ep["label"] in ("incast", "pause_propagation"):
            parts.append(f"{ep['label']}={','.join(ctx.mod.find_roots(ctx.ports, ep))}")
    key = "|".join(sorted(parts))
    ok = digest(key) == EXPECT["roots"]
    return ok, "congestion-tree roots correct" if ok else \
        f"roots {key!r} -- a root is congested at line rate but NOT itself receiving pause"


def c_storm(ctx: Ctx):
    src = None
    for ep in ctx.episodes:
        if ep["label"] == "pfc_storm":
            src = ctx.mod.find_storm_source(ctx.ports, ctx.ds["nic"], ctx.ds["topology"], ep)
    ok = src is not None and digest(src) == EXPECT["storm"]
    return ok, f"storm source {src}" if ok else f"storm source {src!r} is wrong; follow the paused port to its peer and confirm with the NIC counters"


def c_victims(ctx: Ctx):
    v = ctx.mod.find_victims(ctx.ds["probes"], ctx.ports, ctx.episodes)
    key = "|".join(sorted(f"{d['probe']}:{d['episode_label']}" for d in v))
    ok = digest(key) == EXPECT["victims"]
    return ok, f"{len(v)} victim (probe, episode) pairs" if ok else \
        f"victims {key!r}; a probe whose own destination is congested is not a victim"


def c_qos(ctx: Ctx):
    f = ctx.mod.audit_qos(ctx.ds["topology"])
    key = "|".join(f"{s}:{c}" for s, c in sorted(f))
    ok = digest(key) == EXPECT["qos"]
    return ok, f"{len(f)} configuration findings" if ok else f"findings {key!r} are incomplete or include false positives"


def c_red(ctx: Ctx):
    m = ctx.mod.red_mark_probability
    vals = [m(100, 150, 1500, 0.2), m(825, 150, 1500, 0.2), m(1500, 150, 1500, 0.2), m(2000, 150, 1500, 0.2)]
    ok = vals[0] == 0 and abs(vals[1] - 0.1) < 1e-9 and vals[2] == 1.0 and vals[3] == 1.0
    return ok, "RED/ECN profile correct" if ok else f"got {vals}, expected [0, 0.1, 1.0, 1.0]"


def c_sim_conservation(ctx: Ctx):
    msgs, ok = [], True
    for name, r in ctx.sim.items():
        if abs(r["delivered_bytes"] - r["total_bytes"]) > 1:
            ok = False
            msgs.append(f"{name}: delivered {r['delivered_bytes']} != total {r['total_bytes']}")
        if r["completion_us"] + 1e-6 < r["lower_bound_us"]:
            ok = False
            msgs.append(f"{name}: completion {r['completion_us']} us beats the line-rate bound {r['lower_bound_us']} us")
    return ok, "bytes conserved; no config beats the line-rate lower bound" if ok else "; ".join(msgs)


def c_sim_lossless(ctx: Ctx):
    a, b = ctx.sim["A_as_found"], ctx.sim["B_template"]
    ok = a["dropped_bytes"] == 0 and b["dropped_bytes"] == 0 and not a["headroom_overflow"] and not b["headroom_overflow"]
    return ok, "PFC configs lose nothing and stay within headroom" if ok else f"A={a}, B={b}"


def c_sim_compare(ctx: Ctx):
    a, b = ctx.sim["A_as_found"], ctx.sim["B_template"]
    ok = b["pause_time_us"] < 0.5 * a["pause_time_us"] and b["cnps"] > a["cnps"]
    return ok, (f"template ECN cuts pause exposure {a['pause_time_us']} -> {b['pause_time_us']} us "
                f"(CNPs {a['cnps']} -> {b['cnps']})") if ok else \
        f"expected early ECN marking to reduce pause time: A={a['pause_time_us']} us, B={b['pause_time_us']} us"


def c_sim_lossy(ctx: Ctx):
    c, b = ctx.sim["C_lossy"], ctx.sim["B_template"]
    ok = c["dropped_bytes"] > 0 and c["pause_time_us"] == 0 and c["completion_us"] > b["completion_us"]
    return ok, f"lossy config drops {c['dropped_bytes']} B and finishes later" if ok else f"C={c}"


def c_report(ctx: Ctx):
    a = {"episodes": ctx.episodes, "victims": ctx.mod.find_victims(ctx.ds["probes"], ctx.ports, ctx.episodes),
         "qos_findings": ctx.mod.audit_qos(ctx.ds["topology"]),
         "sim": pd.DataFrame(ctx.sim).T, "sim_configs": ctx.ds["sim"]["configs"]}
    for ep in a["episodes"]:
        ep["roots"] = ctx.mod.find_roots(ctx.ports, ep)
        ep["storm_source"] = (ctx.mod.find_storm_source(ctx.ports, ctx.ds["nic"], ctx.ds["topology"], ep)
                              if ep["label"] == "pfc_storm" else None)
    rep = ctx.mod.build_report(a)
    missing = [s for s in ctx.mod.REPORT_SECTIONS if s not in rep]
    storm = next((ep["storm_source"] for ep in a["episodes"] if ep.get("storm_source")), None)
    ok = not missing and "SIMULATED" in rep and (storm is None or storm in rep)
    return ok, f"report has all {len(ctx.mod.REPORT_SECTIONS)} sections" if ok else f"missing sections {missing} or labels"


CHECKS = [
    ("data_determinism", c_data_determinism),
    ("rates_unit", c_rates_unit),
    ("rates_dataset", c_rates_dataset),
    ("episode_count", c_episode_count),
    ("episode_labels", c_labels),
    ("congestion_roots", c_roots),
    ("storm_source", c_storm),
    ("victim_flows", c_victims),
    ("qos_audit", c_qos),
    ("red_profile", c_red),
    ("sim_conservation", c_sim_conservation),
    ("sim_lossless_configs", c_sim_lossless),
    ("sim_compare_A_vs_B", c_sim_compare),
    ("sim_lossy_config", c_sim_lossy),
    ("report_sections", c_report),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = parser.parse_args()
    t0 = time.perf_counter()
    ctx = Ctx(load(args.impl))
    passed = skipped = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            status = "PASS" if ok else "FAIL"
        except Skip as e:
            status, msg = "SKIP", str(e)
        except NotImplementedError as e:
            status, msg = "TODO", f"not implemented: {e}"
        except Exception as e:  # noqa: BLE001 -- report learner bugs without a traceback
            status, msg = "FAIL", f"{type(e).__name__}: {e}"
        passed += status == "PASS"
        skipped += status == "SKIP"
        print(f"{status:4} {name:22} {msg}")
    dt = time.perf_counter() - t0
    print(f"\n{passed}/{len(CHECKS) - skipped} checks passed, {skipped} skipped, in {dt:.1f} s ({args.impl})")
    return 0 if passed + skipped == len(CHECKS) and dt < 60 else 1


if __name__ == "__main__":
    sys.exit(main())
