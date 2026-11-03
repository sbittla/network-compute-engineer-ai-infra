"""Run one package's L2 experiment and write its evidence bundle.

    python /opt/hwlab/run.py --pkg /work/pkg --out /work/pkg/lab/l2/results [--device auto|cuda|cpu] [--quick]

Writes ``<out>/<label>/{environment.json, results.json, report.md}`` where label is ``gpu-<model>``
or ``cpu-fallback``. Exit code 0 only if the experiment ran and every invariant in ``check()`` held
(or it is recorded as not-runnable on this hardware, which is reported, not hidden).
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hwlab  # noqa: E402


def load_experiment(pkg: Path):
    lab = pkg / ("starter-kit" if (pkg / "starter-kit").is_dir() else "lab")
    path = lab / "l2" / "experiment.py"
    spec = importlib.util.spec_from_file_location("experiment", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


def pick_device(requested: str) -> str:
    gpu = hwlab.torch is not None and hwlab.torch.cuda.is_available()
    if requested == "cuda" and not gpu:
        sys.exit("--device cuda requested but no CUDA GPU is visible (did you pass --gpus all?)")
    return "cuda" if (requested == "auto" and gpu) or requested == "cuda" else "cpu"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", default="/work/pkg")
    ap.add_argument("--out", default=None)
    ap.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    ap.add_argument("--quick", action="store_true", help="small sizes, 5 repetitions (CI / smoke test)")
    args = ap.parse_args()

    pkg = Path(args.pkg)
    exp = load_experiment(pkg)
    device = pick_device(args.device)
    env = hwlab.environment(device)
    env["quick"] = args.quick
    env["run_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ctx = hwlab.Context(device=device, quick=args.quick)
    print(f"== {exp.EXPERIMENT['id']}: {exp.EXPERIMENT['title']}  [device={device}{', quick' if args.quick else ''}]")
    if device == "cpu":
        print(f"   no GPU in use -> CPU fallback: {exp.EXPERIMENT.get('cpu_fallback', 'same experiment on CPU')}")

    t0 = time.perf_counter()
    try:
        result = exp.run(ctx)
        result.setdefault("status", "ran")
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:  # noqa: B036 - torch DCP's CheckpointException derives from BaseException; record any crash
        result = {"status": "error", "error": traceback.format_exc(), "metrics": {}, "tables": {}, "notes": []}
    result["runtime_s"] = round(time.perf_counter() - t0, 2)
    result["experiment"] = exp.EXPERIMENT
    result["log"] = ctx.log_lines

    failures: list[str] = []
    if result["status"] == "ran":
        failures = list(exp.check(result, env))
    elif result["status"] == "error":
        failures = ["experiment raised an exception"]
    result["invariants"] = {"passed": not failures, "failures": failures}
    if result["status"] == "ran" and hasattr(exp, "invariant_scope"):
        scope = exp.invariant_scope(result, env)   # optional: which invariants were not applicable, and why
        if scope:
            result["invariants"]["scope"] = scope

    out = Path(args.out) if args.out else pkg / ("starter-kit" if (pkg / "starter-kit").is_dir() else "lab") / "l2" / "results"
    folder = out / (hwlab.label_for(env) + ("-quick" if args.quick else ""))
    hwlab.dump(folder / "environment.json", env)
    hwlab.dump(folder / "results.json", result)
    body = exp.report(result, env) if hasattr(exp, "report") and result["status"] == "ran" else ""
    (folder / "report.md").write_text(render(exp.EXPERIMENT, env, result, body), encoding="utf-8", newline="\n")

    status = result["status"].upper()
    print(f"-> {status}; invariants {'PASS' if not failures else 'FAIL'}; {folder}")
    for f in failures:
        print(f"   FAIL {f}")
    if result["status"] == "error":
        print(result["error"])
    return 0 if result["status"] in ("ran", "not-runnable") and not failures else 1


def render(meta: dict, env: dict, result: dict, body: str) -> str:
    gpu = env.get("gpu0", {}).get("name", "none")
    lines = [
        f"# {meta['title']}",
        "",
        f"`[{meta.get('evidence', 'MEASURED')}]` on **{gpu if env['device'] == 'cuda' else 'CPU fallback: ' + str(env['cpu_model'])}**,"
        f" {env['run_utc']}{' (quick mode)' if env.get('quick') else ''}.",
        "",
        "| Environment | Value |",
        "|---|---|",
    ]
    for key in ("device", "cpu_model", "cpu_count", "mem_total_gib", "os", "torch", "cuda_runtime"):
        lines.append(f"| {key} | {env.get(key)} |")
    for gpu_row in env.get("gpus", [])[:1]:
        for key in ("driver_version", "pcie.link.gen.max", "pcie.link.width.max", "clocks.max.sm", "power.limit"):
            lines.append(f"| {key} | {gpu_row.get(key)} |")
    lines += ["", f"**Status:** {result['status']}"]
    if result["status"] == "not-runnable":
        lines += [f"**Why:** {result['reason']}", f"**Needs:** {', '.join(result['needs'])}",
                  f"**Fallback used instead:** {result['fallback']}"]
    inv = result.get("invariants", {})
    scope = f" ({inv['scope']})" if inv.get("scope") else ""
    lines += [f"**Invariants:** {'all passed' if inv.get('passed') else 'FAILED: ' + '; '.join(inv.get('failures', []))}{scope}", ""]
    if body:
        lines += [body.strip(), ""]
    for note in result.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    sys.exit(main())
