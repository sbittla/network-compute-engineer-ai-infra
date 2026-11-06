#!/usr/bin/env python3
"""Check a Chapter 1 hands-on evidence bundle: complete, internally consistent and physically sensible.

    python check.py results/<run-id>

Prints one PASS / FAIL / SKIP line per check and exits 0 only if no check fails. Standard library only;
it re-derives the headline numbers from the raw outputs rather than trusting summary.json.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the lab directory free of __pycache__
sys.path.insert(0, str(HERE))
from ch01_telemetry import read_csv, window  # noqa: E402

FILES = ["environment.json", "gpu_inventory.json", "ch01_telemetry.csv", "segments.json", "ceiling_gemm.json",
         "ceiling_copy.json", "gemv_sweep.csv", "train_steps.csv", "train_model.json", "summary.json", "report.md"]


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
    check("bundle_complete", lambda: (_ for _ in ()).throw(AssertionError(f"missing {', '.join(missing)} in {run}"))
          if missing else f"all {len(FILES)} files present")
    if missing:
        return report(results)

    J = lambda f: json.loads((run / f).read_text())  # noqa: E731
    S, seg, inv = J("summary.json"), J("segments.json"), J("gpu_inventory.json")
    gemm, copy, model, env = J("ceiling_gemm.json"), J("ceiling_copy.json"), J("train_model.json"), J("environment.json")
    tel = read_csv(run / "ch01_telemetry.csv")
    gemv = list(csv.DictReader(open(run / "gemv_sweep.csv")))
    steps = list(csv.DictReader(open(run / "train_steps.csv")))

    def c_env():
        assert env.get("captured_at") and env.get("gpu"), "environment.json lacks captured_at or gpu"
        assert inv.get("sm_count", 0) > 0, "gpu_inventory.json has no SM count"
        return f"{env['gpu']}; kernel {env.get('kernel')}"
    check("environment", c_env)

    def c_tel():
        assert len(tel) >= 50, f"only {len(tel)} telemetry samples; the sampler did not run for the whole lab"
        dts = [b["t"] - a["t"] for a, b in zip(tel, tel[1:])]
        med = statistics.median(dts)
        assert med <= 0.5, f"median sample interval {med * 1e3:.0f} ms; expected about 100 ms (<= 500 ms)"
        short = [k for k, (t0, t1) in seg.items() if k.startswith(("gemm", "copy", "train")) and len(window(tel, t0, t1)) < 3]
        assert not short, f"segments with fewer than 3 telemetry samples: {short}"
        return f"{len(tel)} samples, median interval {med * 1e3:.0f} ms, every measured segment covered"
    check("telemetry", c_tel)

    def c_gemm():
        ach = gemm["flop_per_iter"] * gemm["iterations"] / gemm["elapsed_s"]
        assert abs(ach / gemm["achieved_flops"] - 1) < 0.01, "achieved FLOP/s does not follow from iterations / elapsed"
        f = S["gemm"]["fraction_of_clock_adjusted_peak"]
        assert f <= 1.05, f"GEMM at {f:.2f} of the clock-adjusted peak is impossible: wrong peak constant or clock"
        assert f >= 0.3, f"GEMM at {f:.2f} of peak: the GPU was shared, throttled hard, or the peak constant is wrong"
        return f"{ach / 1e12:.1f} TFLOP/s = {f:.2f} of clock-adjusted peak ({S['gemm']['fraction_of_max_clock_peak']:.2f} of max-clock peak)"
    check("gemm_ceiling", c_gemm)

    def c_copy():
        ach = copy["bytes_moved_per_iter"] * copy["iterations"] / copy["elapsed_s"]
        assert abs(ach / copy["achieved_bytes_per_s"] - 1) < 0.01, "achieved bytes/s does not follow from iterations / elapsed"
        f = S["copy"]["fraction_of_theoretical"]
        assert 0.3 <= f <= 1.02, f"copy at {f:.2f} of theoretical bandwidth is not physical (expect 0.3-1.0)"
        return f"{ach / 1e9:.0f} GB/s = {f:.2f} of theoretical"
    check("copy_ceiling", c_copy)

    def c_power():
        idle = statistics.median(r["power.draw.instant"] for r in window(tel, *seg["idle"]))
        load = statistics.median(r["power.draw.instant"] for r in window(tel, *seg["gemm"]))
        assert load > idle + 5, f"GEMM power {load:.1f} W is not above idle {idle:.1f} W: the GPU was not loaded"
        return f"idle {idle:.1f} W -> GEMM {load:.1f} W"
    check("power_under_load", c_power)

    def c_gemv():
        sw = S["gemv_sweep"]
        assert sw[0]["dominant"] == "memory", f"B={sw[0]['batch']} classified {sw[0]['dominant']}; a GEMV is memory-bound"
        assert sw[-1]["dominant"] == "compute", f"B={sw[-1]['batch']} classified {sw[-1]['dominant']}; a large GEMM is compute-bound"
        bad = [s["batch"] for s in sw if s["ceiling_fraction"] > 1.05]
        assert not bad, f"ceiling fraction > 1.05 (faster than the hardware allows) at B = {bad}"
        for r, s in zip(gemv, sw):
            obs = float(r["elapsed_s"]) / int(r["iterations"])
            assert abs(obs / s["observed_s"] - 1) < 0.01, f"B={r['batch']}: observed time does not follow from the raw sweep"
        cross = next(s["batch"] for s in sw if s["dominant"] == "compute")
        return f"memory-bound at B={sw[0]['batch']}, compute-bound from B={cross}; machine balance {S['machine_balance_measured_clock']:.0f} FLOP/B"
    check("gemv_crossover", c_gemv)

    def c_train():
        assert model.get("loss_is_finite"), "training loss is not finite"
        out = []
        for x in S["train"]:
            ts = [float(r["step_s"]) for r in steps if int(r["batch"]) == x["batch"]]
            assert len(ts) >= 10, f"batch {x['batch']}: only {len(ts)} timed steps"
            tps = x["tokens_per_step"] / statistics.median(ts)
            assert abs(tps / x["tokens_per_s"] - 1) < 0.01, f"batch {x['batch']}: tokens/s in summary does not match train_steps.csv"
            out.append(f"B{x['batch']} {tps:,.0f} tok/s")
        tp = [x["tokens_per_s"] for x in S["train"]]
        assert tp == sorted(tp), f"tokens/s does not rise with batch size: {tp}"
        return "; ".join(out)
    check("train_throughput", c_train)

    def c_mfu():
        g = S["gemm"]["fraction_of_clock_adjusted_peak"]
        for x in S["train"]:
            m = x["mfu_clock_adjusted"]
            assert 0 < m <= 1.0, f"batch {x['batch']}: MFU {m:.2f} outside (0, 1]"
            assert m <= g + 0.05, f"batch {x['batch']}: MFU {m:.2f} beats the GEMM ceiling {g:.2f}; check the FLOP count"
            assert x["mfu_at_max_clock"] <= m + 1e-9, "MFU against the max-clock peak must not exceed the clock-adjusted MFU"
        best = S["train"][-1]
        return f"best MFU {best['mfu_clock_adjusted']:.2f} (clock-adjusted), {best['mfu_at_max_clock']:.2f} (max clock); GEMM ceiling {g:.2f}"
    check("mfu_physical", c_mfu)

    def c_class():
        v, sc = S["verdict"], S["scaling"]
        assert v["class"] in ("compute", "memory", "overhead"), f"unknown class {v['class']}"
        if v["class"] == "compute":
            assert sc["scales_with_flops"], (f"classified compute-bound but time per token changed by "
                                             f"x{sc['time_per_token_ratio_largest_vs_next']:.2f} when tokens grew: evidence disagrees")
        return f"batch {v['batch']}: {v['class']}-bound, ceiling fraction {v['ceiling_fraction']:.2f}; time/token ratio {sc['time_per_token_ratio_largest_vs_next']:.2f}"
    check("classification", c_class)

    def c_report():
        txt = (run / "report.md").read_text(encoding="utf-8")
        assert txt.count("[MEASURED]") >= 5, "report.md must label measured numbers [MEASURED]"
        for sec in ("Step 2", "Step 3", "Step 4", "Verdict"):
            assert sec in txt, f"report.md lacks the '{sec}' section"
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
