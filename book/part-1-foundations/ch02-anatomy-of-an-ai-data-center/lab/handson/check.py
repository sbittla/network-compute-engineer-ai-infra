#!/usr/bin/env python3
"""Check a Chapter 2 hands-on evidence bundle: complete, internally consistent and physically sensible.

    python check.py results/<run-id>

Prints one PASS / FAIL / SKIP line per check and exits 0 only if no check fails. Standard library only;
it re-derives key numbers from the raw telemetry rather than trusting summary.json.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the lab directory free of __pycache__
sys.path.insert(0, str(HERE))
from ch02_telemetry import read_csv, window  # noqa: E402

FILES = ["environment.json", "ch02_telemetry.csv", "phases.json", "counters.json", "field_availability.json",
         "power_controls.txt", "nvidia_smi_q_before.txt", "nvidia_smi_q_after.txt", "summary.json", "report.md"]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    results: list[tuple[str, str, str]] = []

    def check(name: str, fn) -> None:
        try:
            msg = fn()
            results.append(("SKIP" if msg.startswith("SKIP:") else "PASS", name, msg.removeprefix("SKIP: ")))
        except AssertionError as e:
            results.append(("FAIL", name, str(e)))
        except Exception as e:  # noqa: BLE001
            results.append(("FAIL", name, f"{type(e).__name__}: {e}"))

    missing = [f for f in FILES if not (run / f).is_file()]
    if missing:
        results.append(("FAIL", "bundle_complete", f"missing {', '.join(missing)} in {run}"))
        return report(results)
    results.append(("PASS", "bundle_complete", f"all {len(FILES)} files present"))

    J = lambda f: json.loads((run / f).read_text())  # noqa: E731
    S, ph, env = J("summary.json"), J("phases.json"), J("environment.json")
    tel = read_csv(run / "ch02_telemetry.csv")
    P = S["power_field"]
    F = S["phases"]
    lim = S["enforced_power_limit_w"]

    def c_env():
        assert env.get("captured_at") and env.get("gpu"), "environment.json lacks captured_at or gpu"
        return f"{env['gpu']}; kernel {env.get('kernel')}"
    check("environment", c_env)

    def c_tel():
        assert len(tel) >= 100, f"only {len(tel)} samples; the sampler did not cover the run"
        med = statistics.median(b["t"] - a["t"] for a, b in zip(tel, tel[1:]))
        assert med <= 0.5, f"median sample interval {med * 1e3:.0f} ms; expected about 100 ms (<= 500 ms)"
        thin = [k for k, (t0, t1) in ph.items() if len(window(tel, t0, t1)) < 2]
        assert not thin, f"phases with fewer than 2 samples: {thin}"
        return f"{len(tel)} samples, median interval {med * 1e3:.0f} ms; every phase sampled"
    check("telemetry", c_tel)

    def c_recompute():
        for name in ("idle", "memory", "compute"):
            t0, t1 = ph[name]
            v = statistics.median(r[P] for r in window(tel, t0 + 0.2 * (t1 - t0), t1))
            assert abs(v - F[name]["power_w"]["median"]) < 0.5, f"{name}: summary median power does not match the raw telemetry"
        return "per-phase median power re-derived from ch02_telemetry.csv"
    check("summary_matches_raw", c_recompute)

    def c_order():
        i, m, c = (F[n]["power_w"]["median"] for n in ("idle", "memory", "compute"))
        assert m > i + 5, f"memory phase {m:.1f} W is not above idle {i:.1f} W: the copy loop did not load the GPU"
        assert c > m, f"compute phase {c:.1f} W is not above memory phase {m:.1f} W: unexpected for Tensor-Core GEMMs"
        assert i < 0.5 * c, f"idle {i:.1f} W is more than half of compute {c:.1f} W: was another job on the GPU?"
        return f"idle {i:.1f} W < memory {m:.1f} W < compute {c:.1f} W"
    check("phase_power_order", c_order)

    def c_limit():
        assert lim, "no enforced power limit recorded"
        c = F["compute"]
        p95 = c["power_w"]["p95"]
        assert p95 <= 1.15 * lim, f"compute p95 {p95:.1f} W exceeds the {lim} W limit by > 15 %: wrong field or limit"
        cap = c["frac_sw_power_cap"] or 0
        if cap >= 0.5:
            assert c["power_w"]["median"] >= 0.85 * lim, (f"SW Power Cap asserted in {cap:.0%} of samples but power is only "
                                                         f"{c['power_w']['median']:.1f} W of {lim} W: inconsistent")
        binds = S["findings"]["power_limit_binds_in_compute"]
        return (f"compute {c['power_w']['median']:.1f} W of {lim} W limit, SW Power Cap {cap:.0%}: limit "
                f"{'binds' if binds else 'does not bind'}")
    check("power_limit", c_limit)

    def c_clock():
        f = S["findings"]
        if not (f["power_limit_binds_in_compute"] and not f["power_limit_binds_in_memory"]):
            return "SKIP: the limit did not bind in compute only, so there is no clock contrast to test"
        assert f["compute_sm_clock_mhz"] < f["memory_sm_clock_mhz"], (
            f"compute is power-capped yet its SM clock {f['compute_sm_clock_mhz']:.0f} MHz is not below the uncapped "
            f"memory phase's {f['memory_sm_clock_mhz']:.0f} MHz")
        return f"capped compute SM clock {f['compute_sm_clock_mhz']:.0f} MHz < uncapped memory phase {f['memory_sm_clock_mhz']:.0f} MHz"
    check("cap_costs_clock", c_clock)

    def c_ramp():
        r = S["ramp"]
        assert len(r) >= 3, "fewer than 3 ramp levels"
        pw = [x["power_w"] for x in r]
        assert all(b >= a - 3 for a, b in zip(pw, pw[1:])), f"power does not rise with duty cycle: {[round(p, 1) for p in pw]}"
        assert pw[-1] > pw[0] + 5, "the ramp did not change power"
        return f"power {' -> '.join(f'{p:.0f}' for p in pw)} W; limit binds from {S['power_limit_binds_from_duty_pct']} % duty"
    check("ramp", c_ramp)

    def c_square():
        sq = S["square"]
        assert sq["cycles"] >= 3, f"only {sq['cycles']} square-wave cycles analysed"
        span = F["compute"]["power_w"]["median"] - F["idle"]["power_w"]["median"]
        assert sq["swing_w"] >= 0.3 * span, f"swing {sq['swing_w']:.1f} W is under 30 % of the idle-to-compute span {span:.1f} W"
        return f"{sq['cycles']} cycles, {sq['low_w']:.1f} -> {sq['high_w']:.1f} W, swing {sq['swing_w']:.1f} W"
    check("square_swing", c_square)

    def c_counters():
        d = F["compute"].get("counter_delta_us")
        if not d:
            return "SKIP: violation counters not reported on this platform"
        neg = {k: v for n in F.values() for k, v in n.get("counter_delta_us", {}).items() if v < 0}
        assert not neg, f"cumulative counters went backwards: {neg}"
        return (f"compute phase: power-cap counter +{d.get('sw_power_cap', 0) / 1e6:.2f} s over "
                f"{F['compute']['duration_s']:.0f} s; flag in {F['compute']['frac_sw_power_cap'] or 0:.0%} of samples")
    check("violation_counters", c_counters)

    def c_report():
        txt = (run / "report.md").read_text(encoding="utf-8")
        assert txt.count("[MEASURED]") >= 5, "report.md must label measured numbers [MEASURED]"
        assert "does not report" in txt, "report.md must list the fields this platform lacks"
        return f"{txt.count('[MEASURED]')} [MEASURED] labels"
    check("report", c_report)

    def c_answers():
        p = run / "answers.md"
        if not p.is_file():
            return "SKIP: no answers.md (write your answers to the README questions there)"
        n = sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
        assert n >= 5, "answers.md is nearly empty"
        return f"answers.md has {n} non-empty lines"
    check("answers", c_answers)
    return report(results)


def report(results) -> int:
    w = max(len(n) for _, n, _ in results)
    for st, name, msg in results:
        print(f"{st} {name:<{w}}  {msg}")
    fails = sum(1 for st, _, _ in results if st == "FAIL")
    skips = sum(1 for st, _, _ in results if st == "SKIP")
    print(f"\n{len(results) - fails - skips}/{len(results)} checks passed, {skips} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
