#!/usr/bin/env python3
"""Check a Chapter 21 hands-on evidence bundle: complete, internally consistent and physically sensible.

    python check.py results/<run-id>

Prints one PASS / FAIL / SKIP line per check and exits 0 only if no check fails. Standard library only;
it re-integrates energy from the raw telemetry rather than trusting summary.json.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ch21_telemetry import energy_j, read_csv, window  # noqa: E402

FILES = ["environment.json", "ch21_telemetry.csv", "jobs.json", "steps.csv", "controls.txt", "field_availability.json",
         "model.json", "cost_inputs.json", "summary.json", "report.md"]


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

    Jf = lambda f: json.loads((run / f).read_text())  # noqa: E731
    S, jobs, env = Jf("summary.json"), Jf("jobs.json"), Jf("environment.json")
    tel = read_csv(run / "ch21_telemetry.csv")
    J = S["jobs"]
    work = {n: x for n, x in J.items() if n.startswith(("intensity_", "duty_"))}

    def c_env():
        assert env.get("captured_at") and env.get("gpu"), "environment.json lacks captured_at or gpu"
        return f"{env['gpu']}; kernel {env.get('kernel')}"
    check("environment", c_env)

    def c_tel():
        med = statistics.median(b["t"] - a["t"] for a, b in zip(tel, tel[1:]))
        assert med <= 0.5, f"median sample interval {med * 1e3:.0f} ms; expected about 100 ms (<= 500 ms)"
        thin = [n for n, j in jobs.items() if len(window(tel, j["t0"], j["t1"])) < 5]
        assert not thin, f"jobs with fewer than 5 power samples (energy would be a guess): {thin}"
        return f"{len(tel)} samples, median interval {med * 1e3:.0f} ms; every job has >= 5 samples"
    check("telemetry", c_tel)

    def c_energy():
        worst = 0.0
        for n, x in J.items():
            e = energy_j(tel, jobs[n]["t0"], jobs[n]["t1"])
            assert abs(e / x["energy_j"] - 1) < 0.01, f"{n}: energy in summary.json does not match the raw telemetry"
            if x.get("avg_power_from_average_field_w"):
                dev = abs(x["avg_power_w"] / x["avg_power_from_average_field_w"] - 1)
                worst = max(worst, dev)
                assert dev < 0.15, (f"{n}: integrated instant power ({x['avg_power_w']:.1f} W) and the driver's 1 s average "
                                    f"({x['avg_power_from_average_field_w']:.1f} W) disagree by {dev:.0%}")
        return f"energy re-integrated for {len(J)} jobs; instant vs averaged power agree within {worst:.0%}"
    check("energy_integral", c_energy)

    def c_fixed():
        toks = {x["tokens"] for x in work.values()}
        assert len(toks) == 1, f"jobs did different amounts of work: {sorted(toks)} tokens; energy per job is not comparable"
        return f"every job trained the same {toks.pop():,} tokens"
    check("fixed_work", c_fixed)

    def c_phys():
        p_idle = S["idle_power_w"]
        for n, x in J.items():
            lim = x.get("enforced_limit_w") or 1e9
            assert x["avg_power_w"] <= 1.1 * lim, f"{n}: average {x['avg_power_w']:.1f} W above the {lim} W limit"
            assert x["avg_power_w"] >= 0.5 * p_idle, f"{n}: average {x['avg_power_w']:.1f} W below half of idle {p_idle:.1f} W"
            assert x["busy_s"] <= x["wall_s"] * 1.001, f"{n}: busy time exceeds wall time"
        return f"idle {p_idle:.1f} W; job averages {min(x['avg_power_w'] for x in J.values()):.1f}-{max(x['avg_power_w'] for x in J.values()):.1f} W"
    check("power_physical", c_phys)

    def c_int():
        b = sorted((x["batch"], x) for n, x in J.items() if n.startswith("intensity_"))
        tps = [x["tokens_per_s_wall"] for _, x in b]
        assert tps == sorted(tps), f"throughput does not rise with batch size: {[round(t) for t in tps]}"
        lo, hi = b[0][1], b[-1][1]
        assert hi["tokens_per_j"] > lo["tokens_per_j"], (f"batch {b[-1][0]} is not more energy-efficient than batch {b[0][0]} "
                                                         f"({hi['tokens_per_j']:.0f} vs {lo['tokens_per_j']:.0f} tokens/J)")
        return (f"tokens/J {lo['tokens_per_j']:.0f} (B{b[0][0]}) -> {hi['tokens_per_j']:.0f} (B{b[-1][0]}) "
                f"while power rose {lo['avg_power_w']:.0f} -> {hi['avg_power_w']:.0f} W")
    check("intensity_efficiency", c_int)

    def c_duty():
        seq = [J["intensity_b16"]] + [J[n] for n in sorted((n for n in J if n.startswith("duty_")), reverse=True)]
        for x, n in zip(seq[1:], sorted((n for n in J if n.startswith("duty_")), reverse=True)):
            tgt = jobs[n]["target_busy_fraction"]
            assert abs(x["busy_fraction"] - tgt) < 0.1, f"{n}: busy fraction {x['busy_fraction']:.2f}, target {tgt}"
        jpt = [x["j_per_token"] for x in seq]
        assert all(b > a for a, b in zip(jpt, jpt[1:])), f"energy per token does not rise as busy fraction falls: {jpt}"
        return f"J/token rises {jpt[0] * 1e3:.2f} -> {jpt[-1] * 1e3:.2f} mJ as busy fraction falls {seq[0]['busy_fraction']:.2f} -> {seq[-1]['busy_fraction']:.2f}"
    check("idle_costs_energy", c_duty)

    def c_cost():
        o, C = S["cost_orion"], S["inputs"]["orion"]
        exp = C["usd_per_nominal_gpu_hour"] / (C["usable_fraction"] * C["allocated_fraction"] * C["goodput"])
        assert abs(o["usd_per_useful_gpu_hour"] - exp) < 0.005, "ORION $/useful GPU-h does not follow from the ladder"
        assert abs(o["usd_per_useful_gpu_hour"] - 4.72) < 0.01, f"ORION $/useful GPU-h {o['usd_per_useful_gpu_hour']:.3f}; the book says $4.72"
        ys = S["cost_yours"]
        for n, c in ys.items():
            assert c["usd_per_useful_gpu_hour"] >= c["usd_per_nominal_gpu_hour"], f"{n}: useful hour cheaper than a nominal one"
        order = sorted(ys.values(), key=lambda c: -c["goodput_measured"])
        u = [c["usd_per_useful_gpu_hour"] for c in order]
        assert u == sorted(u), "cost per useful GPU-hour must rise as goodput falls"
        return (f"ORION $3.00 -> ${o['usd_per_useful_gpu_hour']:.2f}/useful GPU-h; yours "
                f"${order[0]['usd_per_nominal_gpu_hour']:.3f} -> ${order[0]['usd_per_useful_gpu_hour']:.3f} at goodput {order[0]['goodput_measured']:.2f}")
    check("cost_ladder", c_cost)

    def c_controls():
        ctl = (run / "controls.txt").read_text()
        assert "$ nvidia-smi -pl" in ctl, "controls.txt does not record whether the power limit can be changed"
        caps = [n for n in J if n.startswith("cap_")]
        if not S["power_limit_change_permitted"]:
            assert not caps, "power-cap jobs present although changing the limit was refused"
            return "power limit change refused on this platform; no cap sweep run (expected on WSL2)"
        if not caps:
            return "SKIP: power limit change permitted but the opt-in cap sweep (CH21_ALLOW_POWER_CAP=1) was not run"
        assert not (run.parent / ".ch21_power_limit_changed").exists(), "the cap sweep did not restore the power limit"
        return f"cap sweep run: {', '.join(caps)}; limit restored"
    check("power_controls", c_controls)

    def c_report():
        txt = (run / "report.md").read_text(encoding="utf-8")
        assert txt.count("[MEASURED]") >= 4, "report.md must label measured numbers [MEASURED]"
        assert "ORION" in txt and "$/useful GPU-h" in txt, "report.md must put your cost beside ORION's"
        return f"{txt.count('[MEASURED]')} [MEASURED] labels; ORION comparison present"
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
