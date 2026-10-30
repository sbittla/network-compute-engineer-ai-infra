#!/usr/bin/env python3
"""Checker for the Chapter 18 lab (telemetry bundle -> SLIs, alerts, root cause, postmortem).

Usage:
    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python, no hardware, no network, < 60 s.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DATA_FILES = ("job_steps.csv", "node_metrics.csv", "switch_metrics.csv", "inference_slo.csv",
              "events.jsonl", "alert_rules.yaml", "postmortem_template.md")
JOBS = {"trn-70b": 128, "ft-13b": 64}
JOB_NODES = {"trn-70b": [f"orion-n{i:02d}" for i in range(1, 17)], "ft-13b": [f"orion-n{i:02d}" for i in range(17, 25)]}


def T(hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"2026-10-12T{hhmm}Z")


BASE_WIN = (T("00:00"), T("02:00"))


def load_impl(impl: str) -> ModuleType:
    """Import telemetry_analysis.py from starter/ or ../solutions/lab/ by path."""
    path = HERE / "starter" / "telemetry_analysis.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "telemetry_analysis.py"
    spec = importlib.util.spec_from_file_location(f"telemetry_analysis_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def close(a: float, b: float, rel: float = 0.01) -> bool:
    return math.isclose(a, b, rel_tol=rel, abs_tol=1e-9)


class Ctx:
    """Lazily computed shared values so later checks do not re-implement earlier tasks."""

    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.b = m.load_bundle(DATA)
        self._base: dict[str, float] = {}

    def base(self, job: str) -> float:
        if job not in self._base:
            self._base[job] = self.m.baseline_step_time(self.b["job_steps"], job, *BASE_WIN)
        return self._base[job]


# ------------------------------------------------------------------ checks
def check_reproducible(c: Ctx) -> tuple[bool | None, str]:
    if not (HERE / "tools" / "generate_data.py").exists():
        return None, "generator not shipped (instructor copy only); data integrity not re-checked"
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", td],
                       check=True, capture_output=True)
        for name in DATA_FILES:
            a = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            b = hashlib.sha256((Path(td) / name).read_bytes()).hexdigest()
            if a != b:
                return False, f"{name} differs from regenerated copy (did you edit data/ by hand?)"
    size = sum((DATA / n).stat().st_size for n in DATA_FILES)
    return size < 2_000_000, f"generator reproduces committed data byte-for-byte ({size/1e6:.2f} MB)"


def check_baselines(c: Ctx) -> tuple[bool, str]:
    t, f = c.base("trn-70b"), c.base("ft-13b")
    ok = 17.2 < t < 17.6 and 5.9 < f < 6.1
    return ok, f"baseline step time trn-70b={t:.3f} s (expect ~17.4), ft-13b={f:.3f} s (expect ~6.0)"


def check_checkpoint_excluded(c: Ctx) -> tuple[bool, str]:
    ser = c.m.step_time_per_minute(c.b["job_steps"], "trn-70b")
    mx = float(ser[(ser.index >= T("00:00")) & (ser.index < T("02:00"))].max())
    return mx < 18.5, f"per-minute series excludes checkpoint stalls (baseline-window max {mx:.2f} s < 18.5 s)"


def check_onsets(c: Ctx) -> tuple[bool, str]:
    msgs, ok = [], True
    for job in JOBS:
        on = c.m.detect_onset(c.b["job_steps"], job, c.base(job))
        rec = c.m.detect_recovery(c.b["job_steps"], job, c.base(job), on)
        ok &= T("02:06") <= on <= T("02:16") and T("04:02") <= rec <= T("04:15")
        msgs.append(f"{job} onset {on:%H:%M} recovery {rec:%H:%M}")
    return ok, "; ".join(msgs) + " (expect onset 02:06-02:16, recovery 04:02-04:15)"


def check_training_sli_and_loss(c: Ctx) -> tuple[bool, str]:
    js = c.b["job_steps"]
    sli = c.m.training_sli(js, "trn-70b", c.base("trn-70b"))
    total = 0.0
    for job, gpus in JOBS.items():
        on = c.m.detect_onset(js, job, c.base(job))
        rec = c.m.detect_recovery(js, job, c.base(job), on)
        total += c.m.lost_gpu_hours(js, job, c.base(job), gpus, on, rec)
    ok = 0.66 < sli < 0.70 and 59.0 < total < 66.0
    return ok, f"trn-70b SLI={sli:.3f} (expect ~0.68); lost GPU-hours onset->recovery={total:.1f} (expect ~62)"


def check_burn_rates(c: Ctx) -> tuple[bool, str]:
    inf = c.b["inference_slo"]
    b5 = c.m.burn_rate(inf, "errors_5xx", 0.999, 5)
    b60 = c.m.burn_rate(inf, "errors_5xx", 0.999, 60)
    at = T("05:16")
    v5, v60 = float(b5.loc[at]), float(b60.loc[at])
    nan_ok = bool(pd.isna(c.m.burn_rate(inf, "errors_5xx", 0.999, 60).loc[T("00:30")]))
    ok = 35 < v5 < 45 and 4.0 < v60 < 6.0 and nan_ok
    return ok, f"availability burn at 05:16: 5m={v5:.1f} (expect ~40), 1h={v60:.2f} (expect ~5); partial windows NaN={nan_ok}"


def check_multiwindow(c: Ctx) -> tuple[bool, str]:
    inf = c.b["inference_slo"]
    a = int(c.m.multiwindow_fast_burn(inf, "errors_5xx", 0.999).sum())
    # synthetic sustained outage must page
    syn = inf.copy()
    syn.loc[(syn.ts >= T("01:00")) & (syn.ts < T("01:40")), "errors_5xx"] = (syn.requests * 0.03).astype(int)
    s = c.m.multiwindow_fast_burn(syn, "errors_5xx", 0.999)
    fired = s[s].index
    ok = a == 0 and len(fired) > 0 and fired[0] <= T("01:30")
    first = f"{fired[0]:%H:%M}" if len(fired) else "never"
    return ok, f"7-min deploy blip does not page ({a} minutes); synthetic 3% outage pages at {first}"


def check_rule_eval(c: Ctx) -> tuple[bool, str]:
    rules = {r["name"]: r for r in c.b["rules"]}
    temp = c.m.evaluate_rule(rules["GPUTempHigh"], c.b)
    disc = c.m.evaluate_rule(rules["FabricOutDiscards"], c.b)
    ok = len(temp) == 1 and temp[0]["entity"] == "orion-n08" and T("01:50") <= temp[0]["start"] <= T("01:56") \
        and len(disc) == 0
    desc = f"{temp[0]['entity']}@{temp[0]['start']:%H:%M}" if temp else "none"
    return ok, f"GPUTempHigh fires once ({desc}, expect orion-n08 ~01:53); FabricOutDiscards silent ({len(disc)})"


def check_noisy_and_missing(c: Ctx) -> tuple[bool, str]:
    res = c.m.classify_alerts(c.b, (T("02:08"), T("04:10")))
    noisy = {k for k, v in res.items() if v["verdict"] == "noisy"}
    pages_during = [k for k, v in res.items() if v["severity"] == "page" and v["during_incident"] > 0
                    and v["verdict"] != "noisy"]
    ok = noisy == {"GPUUtilLow"} and pages_during == []
    return ok, f"noisy={sorted(noisy)} (expect ['GPUUtilLow']); actionable pages during incident={pages_during} (expect none -> missing alert)"


def check_goodput_alert(c: Ctx) -> tuple[bool, str]:
    js = c.b["job_steps"]
    msgs, ok = [], True
    for job in JOBS:
        fires = c.m.goodput_alert(js, job, c.base(job))
        in_inc = [f for f in fires if T("02:08") <= f["start"] <= T("02:25")]
        false = [f for f in fires if f["start"] < T("02:08") or f["start"] > T("04:15")]
        ok &= len(in_inc) >= 1 and not false
        msgs.append(f"{job}: {len(fires)} firing(s), first {fires[0]['start']:%H:%M}" if fires else f"{job}: none")
    return ok, "; ".join(msgs) + " (must fire by 02:25 with no firing outside the incident)"


def check_root_cause(c: Ctx) -> tuple[bool, str]:
    js = c.b["job_steps"]
    on = {j: c.m.detect_onset(js, j, c.base(j)) for j in JOBS}
    rc = c.m.correlate_root_cause(c.b, on, JOB_NODES)
    rej = {r["id"] for r in rc["rejected"]}
    fs = c.m.fabric_shift(c.b["switch_metrics"], (T("01:00"), T("02:00")), (T("02:30"), T("03:30")))
    leaf_pfc = float(fs.loc[[f"orion-be-leaf-r{r}" for r in range(8)], "pfc_tx_ratio"].min())
    leaf_ecn = float(fs.loc[[f"orion-be-leaf-r{r}" for r in range(8)], "ecn_ratio"].max())
    ok = rc["trigger"] == "CHG-4471" and "FAC-0912" in rej and leaf_pfc > 20 and leaf_ecn < 0.1
    return ok, (f"trigger={rc['trigger']} (expect CHG-4471), rejected={sorted(rej)}; "
                f"leaf PFC TX x{leaf_pfc:.0f}, ECN x{leaf_ecn:.2f}")


def check_timeline(c: Ctx) -> tuple[bool, str]:
    js = c.b["job_steps"]
    on = min(c.m.detect_onset(js, j, c.base(j)) for j in JOBS)
    t = c.m.build_timeline(c.b, on)
    ok = (t["detected"] == T("02:58") and t["declared"] == T("03:12") and t["resolved"] == T("04:30")
          and T("04:08") <= t["mitigated"] <= T("04:09") and 44 <= t["ttd_min"] <= 52 and 114 <= t["ttm_min"] <= 122)
    return ok, f"TTD={t['ttd_min']} min, TTM={t['ttm_min']} min, TTR={t['ttr_min']} min (expect ~48 / ~118 / ~140)"


def check_postmortem(c: Ctx) -> tuple[bool, str]:
    keys = ["incident_id", "title", "severity", "owner", "summary", "affected_jobs", "impact_minutes",
            "lost_gpu_hours", "training_sli", "inference_impact", "timeline", "ttd_min", "how_detected",
            "missing_alert", "noisy_alert", "root_cause", "rejected_hypotheses", "went_well", "action_items"]
    facts = {k: f"<{k}>" for k in keys}
    out = c.m.render_postmortem(c.b["template"], facts)
    complete = "{{" not in out and "<lost_gpu_hours>" in out
    try:
        c.m.render_postmortem(c.b["template"], {k: "x" for k in keys[:-1]})
        raises = False
    except KeyError:
        raises = True
    return complete and raises, f"all placeholders filled={complete}; missing fact raises KeyError={raises}"


def check_dashboard(c: Ctx) -> tuple[bool, str]:
    spec = c.m.dashboard_spec()
    levels = spec["levels"]
    names = [lv["name"] for lv in levels]
    ok = names[:4] == ["fleet", "node", "device", "workload"]
    for i, lv in enumerate(levels):
        ok &= len(lv["panels"]) >= 3 and all({"title", "query", "unit"} <= set(p) for p in lv["panels"])
        nxt = levels[i + 1]["name"] if i + 1 < len(levels) else None
        ok &= lv.get("drilldown") == nxt
    queries = " ".join(p["query"] for lv in levels for p in lv["panels"])
    ok &= "DCGM_FI_PROF_" in queries and "burn" in " ".join(p["title"].lower() for p in levels[0]["panels"])
    return ok, f"levels={names}; drilldowns chain; fleet has a burn-rate panel; uses DCGM profiling metrics"


CHECKS: list[tuple[str, Callable[[Ctx], tuple[bool | None, str]]]] = [
    ("dataset reproducible", check_reproducible),
    ("T1 baseline step times", check_baselines),
    ("T1 checkpoint steps excluded", check_checkpoint_excluded),
    ("T1 regression onset/recovery", check_onsets),
    ("T2 training SLI + lost GPU-hours", check_training_sli_and_loss),
    ("T2 burn rates", check_burn_rates),
    ("T2 multiwindow page logic", check_multiwindow),
    ("T3 rule evaluation", check_rule_eval),
    ("T3 noisy + missing alert", check_noisy_and_missing),
    ("T3 goodput alert design", check_goodput_alert),
    ("T4 root-cause correlation", check_root_cause),
    ("T5 incident timeline", check_timeline),
    ("T5 postmortem rendering", check_postmortem),
    ("T6 dashboard hierarchy", check_dashboard),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    ap.add_argument("-v", "--verbose", action="store_true", help="print tracebacks for failures")
    args = ap.parse_args()
    try:
        ctx = Ctx(load_impl(args.impl))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import/load: {exc!r}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            if ok is None:
                print(f"SKIP {name}: {msg}")
                passed += 1
                continue
            print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
            passed += bool(ok)
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc.args[0] if exc.args else 'function'}()")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            if args.verbose:
                print(traceback.format_exc())
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
