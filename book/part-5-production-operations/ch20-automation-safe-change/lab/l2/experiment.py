"""Ch 20 L2: a real canary gate. Inject a regression on this GPU and let the lab's rollout controller catch it.

The chapter's L2 extension turns ``SimFleet`` into a ``LinuxHost`` adapter that reads and sets a real
NIC's MTU (or a soft-RoCE device's), runs the reconciler twice and proves the second plan is empty.
That needs a lab VM with an RDMA NIC or ``rdma_rxe``, root and a real netdev. The harness runs each lab
unprivileged with ``--network none`` (only ``lo``), so the mutating part is probed and recorded as not
runnable. A read-only ``LinuxHost`` adapter still runs: it reads the real state, the lab's
``compute_plan`` classifies this host, and ``apply_plan`` proves a dry run writes nothing.

What genuinely runs on one GPU (Section 20.6, canaries and abort conditions): the decision half of the
L3 canary, ``evaluate_wave`` / ``run_rollout``, fed with *measured* samples instead of the lab's JSON.
The node is this GPU and the metric is GEMM throughput, the stand-in for per-rail busbw. Abort
condition AC1 is the lab's own (median more than 5 % below the node's baseline median), and so is
the bake rule (>= 12 post-change samples). Three changes are measured, baseline and post samples
interleaved so drift (thermals, other tenants) hits both alike:

* **control**: a no-op change. The gate must say *proceed* (no false abort from noise).
* **regression**: the change adds extra element-wise passes over the GEMM output each step (the shape
  of a library or driver change that quietly adds work), sized to about 20 % of the GEMM time and then
  measured. The gate must say *abort* and name AC1.
* **short bake**: the same regression with too few post samples. The gate must say *hold*.

The experiment also reports the run-to-run noise (coefficient of variation) next to the 5 % threshold:
an abort threshold below the noise floor aborts healthy changes.

CPU fallback: the same three changes on a CPU GEMM; the gate logic and invariants are identical.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch20-l2",
    "title": "Lab 20 L2: a measured canary gate (no-op, injected regression, short bake) through the lab's controller",
    "evidence": "MEASURED",
    "cpu_fallback": "the same control / regression / short-bake changes measured on a CPU GEMM and judged by the same gate",
}

PKG = Path(__file__).resolve().parents[2]
NODE = "l2-this-host"
METRIC = "gemm_tflops"


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip("\n")
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def read(path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def load_l1(name: str):
    """The L1 module: the reference solution if present, else the learner's starter (student release)."""
    for d in (PKG / "solutions" / "lab", PKG / "lab" / "starter"):
        p = d / f"{name}.py"
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            try:
                spec.loader.exec_module(mod)
                return mod, p.relative_to(PKG).as_posix()
            except Exception:  # noqa: BLE001
                continue
    return None, None


# --------------------------------------------------------------------------------------------- Part A: read-only host
class LinuxHostReadOnly:
    """The L2 ``LinuxHost`` adapter with ``get`` only: real state from sysfs. ``set`` is refused (no CAP_NET_ADMIN here)."""

    BACKEND_NETDEVS = ("eth1", "ens1np0")  # the names the lab's runbook and baseline use for the backend NIC

    def __init__(self):
        self.writes = 0
        self.netdevs = sorted(p.name for p in Path("/sys/class/net").iterdir()) if Path("/sys/class/net").is_dir() else []

    def targets(self) -> list[str]:
        return [NODE]

    def get(self, target: str) -> dict | None:
        nd = next((n for n in self.BACKEND_NETDEVS if n in self.netdevs), None)
        if nd is None:
            return None  # no backend NIC: unreachable for the reconciler, exactly as SimFleet models it
        return {"host_mtu": int(read(f"/sys/class/net/{nd}/mtu") or 0)}

    def set(self, target: str, key: str, value) -> None:
        raise PermissionError("LinuxHostReadOnly never writes; the mutating adapter needs root on a lab VM")


def host_probe() -> dict:
    status = read("/proc/self/status") or ""
    cap_eff = next((int(ln.split()[1], 16) for ln in status.splitlines() if ln.startswith("CapEff:")), 0)
    return {"netdevs": LinuxHostReadOnly().netdevs, "cap_net_admin": bool(cap_eff & (1 << 12)), "euid": os.geteuid(),
            "rdma_rxe_module": "rdma_rxe" in (read("/proc/modules") or ""),
            "sys_class_infiniband": Path("/sys/class/infiniband").is_dir(),
            "tools": {t: bool(shutil.which(t)) for t in ("ip", "rdma", "ibv_devinfo")}}


def reconcile_this_host(mod) -> dict:
    desired = json.loads((PKG / "lab" / "data" / "desired_state.json").read_text(encoding="utf-8"))
    desired = copy.deepcopy(desired)
    desired["targets"]["node"] = [NODE]
    desired["targets"]["leaf"] = [t for t in desired["targets"].get("leaf", [])]
    desired["overrides"] = {}
    host = LinuxHostReadOnly()
    actual = {NODE: host.get(NODE)}
    for leaf in desired["targets"]["leaf"]:
        actual[leaf] = None  # no switch API from here
    viol = mod.validate_desired(desired)
    plan = mod.compute_plan(desired, actual, viol)
    res = mod.apply_plan(host, plan, dry_run=True, change_id=desired.get("change_id", "L2"))
    plan2 = mod.compute_plan(desired, actual, viol)
    return {"actual": actual[NODE], "unreachable": plan["unreachable"], "blocked": plan["blocked"],
            "actions": len(plan["actions"]), "second_plan_actions": len(plan2["actions"]),
            "writes": host.writes, "audit_records": len(res["audit"])}


# --------------------------------------------------------------------------------------------- Part B: measured canary
def make_step(ctx, target: float = 0.20):
    """Baseline step = one GEMM; the regressed step adds k element-wise passes over the output, with k calibrated
    so the extra work is ~``target`` of the GEMM time (the injected regression is sized, then *measured*)."""
    torch = ctx.torch
    if ctx.is_gpu:
        n, dt, dev = 4096, torch.float16, "cuda"
    else:
        n, dt, dev = 768, torch.float32, "cpu"
        torch.set_num_threads(1)  # one pinned thread: far less exposed to other tenants' CPU load than a full pool
        try:
            os.sched_setaffinity(0, {sorted(os.sched_getaffinity(0))[-1]})
        except OSError:
            pass
    a, b = torch.randn(n, n, device=dev, dtype=dt), torch.randn(n, n, device=dev, dtype=dt)
    c = torch.empty(n, n, device=dev, dtype=dt)
    passes = {"k": 1}

    def base():
        torch.matmul(a, b, out=c)

    def one_pass():
        c.mul_(1.0)

    def regressed():
        torch.matmul(a, b, out=c)
        for _ in range(passes["k"]):  # the injected regression: extra passes over the output
            c.mul_(1.0)

    t_gemm = ctx.bench(base, warmup=3, reps=5)["median"]
    t_pass = ctx.bench(one_pass, warmup=3, reps=5)["median"]
    passes["k"] = max(1, min(64, round(target * t_gemm / max(t_pass, 1e-9))))
    return base, regressed, 2 * n ** 3, n, passes["k"]


def sample(ctx, fn, flop: float, window_s: float) -> float:
    """One throughput sample (TFLOP/s). GPU: one ~window_s window. CPU: the best of 3 sub-windows, which filters
    out bursts of interference from other processes sharing the host's cores."""
    if not ctx.is_gpu:
        return max(_window(ctx, fn, flop, window_s / 3) for _ in range(3))
    return _window(ctx, fn, flop, window_s)


def _window(ctx, fn, flop: float, window_s: float) -> float:
    it, t0 = 0, time.perf_counter()
    while True:
        for _ in range(4):
            fn()
        ctx.sync()
        it += 4
        el = time.perf_counter() - t0
        if el >= window_s:
            return flop * it / el / 1e12


def paired_samples(ctx, base, post, flop, n_base: int, n_post: int, window_s: float) -> tuple[list[float], list[float]]:
    """ABBA-interleaved samples: alternating the order each round cancels a linear drift between the two arms."""
    b, p = [], []
    for i in range(max(n_base, n_post)):
        order = (("b", base), ("p", post)) if i % 2 == 0 else (("p", post), ("b", base))
        for arm, fn in order:
            if arm == "b" and i < n_base:
                b.append(sample(ctx, fn, flop, window_s))
            elif arm == "p" and i < n_post:
                p.append(sample(ctx, fn, flop, window_s))
    return b, p


def gpu_health() -> str:
    rc, out = sh(["nvidia-smi", "--query-gpu=temperature.gpu,clocks_event_reasons.hw_slowdown", "--format=csv,noheader,nounits"])
    if rc != 0:
        return "ok"  # CPU fallback: nothing to check beyond the process running
    try:
        temp, hw = [v.strip() for v in out.splitlines()[0].split(",")]
        return "ok" if float(temp) < 87 and hw != "Active" else "degraded"
    except ValueError:
        return "unknown"


def run(ctx) -> dict:
    mod, src = load_l1("safe_change")
    conditions = json.loads((PKG / "lab" / "data" / "abort_conditions.json").read_text(encoding="utf-8"))
    ac1 = next(c for c in conditions["conditions"] if c["id"] == "AC1")
    gate = {"precheck": conditions["precheck"], "bake": conditions["bake"],
            "conditions": [{**ac1, "metric": METRIC, "rationale": ac1["rationale"].replace("busbw", "GEMM throughput")}]}
    need = gate["bake"]["min_post_samples"]
    window = (0.25 if ctx.quick else 0.5) if ctx.is_gpu else 0.5
    base, regressed, flop, n, k_passes = make_step(ctx)
    for _ in range(5):  # warm-up
        base()
        regressed()
    ctx.sync()
    health = gpu_health() if ctx.is_gpu else "ok"
    scenarios = {}
    t0 = time.perf_counter()
    for name, post_fn, n_post in (("control", base, need), ("regression", regressed, need), ("short_bake", regressed, need // 2)):
        b, p = paired_samples(ctx, base, post_fn, flop, need, n_post, window)
        scenarios[name] = {"baseline": b, "post": p}
        ctx.log(f"{name:10s} baseline median {statistics.median(b):.3f}  post median {statistics.median(p):.3f} TFLOP/s "
                f"({(statistics.median(b) - statistics.median(p)) / statistics.median(b) * 100:+.1f} % drop)")
    measure_s = time.perf_counter() - t0

    def wave(i, name):
        return {"wave": i, "nodes": [{"node": f"{NODE}-{name}", "precheck": {"drained": True, "health": health},
                                      "baseline": {METRIC: scenarios[name]["baseline"]}, "post": {METRIC: scenarios[name]["post"]}}]}

    decisions, rollout, recon, err = {}, None, None, None
    if mod is not None:
        try:
            for i, name in enumerate(scenarios):
                decisions[name] = mod.evaluate_wave(wave(i, name), gate)
            rollout = mod.run_rollout({"waves": [wave(0, "control"), wave(1, "regression")], "rollback_scope": "all_changed"},
                                      gate)
            recon = reconcile_this_host(mod)
        except Exception as exc:  # noqa: BLE001 - starter TODOs
            err = f"{type(exc).__name__}: {exc}"
    rows = []
    for name, s in scenarios.items():
        bm, pm = statistics.median(s["baseline"]), statistics.median(s["post"])
        cv = statistics.pstdev(s["baseline"]) / statistics.fmean(s["baseline"])
        rows.append({"change": name, "baseline_n": len(s["baseline"]), "post_n": len(s["post"]), "baseline_median": bm,
                     "post_median": pm, "drop": (bm - pm) / bm, "baseline_cv": cv,
                     "baseline_p95": sorted(s["baseline"])[min(len(s["baseline"]) - 1, round(0.95 * (len(s["baseline"]) - 1)))],
                     "decision": decisions.get(name, {}).get("decision"), "reasons": decisions.get(name, {}).get("reasons", [])})
    by = {r["change"]: r for r in rows}
    metrics = {
        "threshold_drop": ac1["threshold"], "min_post_samples": need, "node_health": health,
        "control_drop": round(by["control"]["drop"], 4), "regression_drop": round(by["regression"]["drop"], 4),
        "baseline_cv_median": round(statistics.median(r["baseline_cv"] for r in rows), 4),
        "baseline_tflops_median": round(by["control"]["baseline_median"], 3),
        "decision_control": by["control"]["decision"], "decision_regression": by["regression"]["decision"],
        "decision_short_bake": by["short_bake"]["decision"],
        "rollout_outcome": rollout["outcome"] if rollout else None,
        "rollout_rollback_nodes": rollout["rollback_nodes"] if rollout else None,
        "measure_seconds": round(measure_s, 1), "injected_extra_passes": k_passes,
    }
    if recon:
        metrics.update({"reconcile_unreachable": recon["unreachable"], "reconcile_actions": recon["actions"],
                        "reconcile_second_plan_actions": recon["second_plan_actions"], "reconcile_writes": recon["writes"]})
    probe = host_probe()
    not_runnable = [
        {"part": "LinuxHost adapter set(): ip link set dev <if> mtu 9000, then a second run planning zero actions",
         "needs": ["a lab VM with an RDMA NIC or a soft-RoCE rxe device", "root / CAP_NET_ADMIN", "a real netdev "
                   "(the harness runs with --network none)"], "probe": probe},
        {"part": "L3 canary on >= 2 GPU nodes with RoCEv2 NICs: all_reduce_perf busbw per rail, CNP/PFC counters, Xid events",
         "needs": [">= 2 multi-GPU nodes with RoCEv2 NICs", "a lab leaf switch with API access", "nccl-tests"],
         "probe": "single host"},
    ]
    notes = [
        f"Samples: one sample = back-to-back steps for {window} s ({'4096^3 FP16 GEMM' if ctx.is_gpu else '768^3 FP32 GEMM on one pinned thread'}); "
        f"baseline and post samples interleaved in ABBA order (CPU: best of 3 sub-windows per sample); {need} baseline samples per change; 5 warm-up steps of each variant first.",
        f"Injected regression: {k_passes} extra in-place multiply pass(es) over the GEMM output per step, sized from a "
        "timed GEMM and a timed pass to cost ~20 % of the step.",
        "AC1, the bake rule and the precheck rule are read from lab/data/abort_conditions.json; only the metric name changes "
        "(GEMM TFLOP/s instead of busbw).",
        "Node health for the precheck comes from nvidia-smi (temperature, HW slowdown) on the GPU; drained is true because "
        "nothing else is scheduled on this node by the lab.",
    ]
    if err:
        notes.append(f"Gate not evaluated: {err} (implement lab/starter/safe_change.py).")
    return {"metrics": metrics, "tables": {"changes": rows, "samples": scenarios, "rollout": [rollout] if rollout else [],
                                           "reconcile": [recon] if recon else []},
            "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m = result["metrics"]
    fails = []
    thr = m["threshold_drop"]
    if m["regression_drop"] <= thr:
        fails.append(f"the injected regression only cost {m['regression_drop'] * 100:.1f} % (threshold {thr * 100:.0f} %): the "
                     "injection is too small for this device; increase the extra passes")
    if abs(m["control_drop"]) >= thr:
        fails.append(f"the no-op change moved the median by {m['control_drop'] * 100:+.1f} %: the measurement is noisier than the "
                     "abort threshold (another job on the device?), so the gate cannot be trusted; rerun on an idle device")
    if m["decision_control"] is not None:
        if m["decision_control"] != "proceed":
            fails.append(f"the gate said {m['decision_control']} for a no-op change: false abort")
        if m["decision_regression"] != "abort":
            fails.append(f"the gate said {m['decision_regression']} for a {m['regression_drop'] * 100:.0f} % regression: missed abort")
        if m["decision_short_bake"] != "hold":
            fails.append(f"the gate said {m['decision_short_bake']} with fewer than {m['min_post_samples']} post samples: "
                         "must hold")
        if m["rollout_outcome"] != "aborted" or sorted(m["rollout_rollback_nodes"] or []) !=                 [f"{NODE}-control", f"{NODE}-regression"]:
            fails.append("run_rollout must abort at the regression wave and roll back every changed node (all_changed)")
        reasons = next(r["reasons"] for r in result["tables"]["changes"] if r["change"] == "regression")
        if not any(r.startswith("AC1") and f"{NODE}-regression" in r for r in reasons):
            fails.append("abort reasons must start with the condition ID and name the node")
    if m.get("reconcile_writes", 0) != 0:
        fails.append("a dry run wrote to the host")
    if m.get("reconcile_actions") not in (None, 0) and m.get("reconcile_unreachable"):
        fails.append("an unreachable target must get no actions")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    unit = "TFLOP/s" if env["device"] == "cuda" else "TFLOP/s (CPU)"
    lines = ["## Canary gate on measured samples", "",
             f"Abort condition AC1: post-change median more than **{m['threshold_drop'] * 100:.0f} %** below baseline; bake needs "
             f">= {m['min_post_samples']} post samples. Node health at precheck: {m['node_health']}.", "",
             f"| Change | Baseline median ({unit}) | Post median | Drop | Baseline CV | Samples (base/post) | Gate decision |",
             "|---|---|---|---|---|---|---|"]
    for r in t["changes"]:
        lines.append(f"| {r['change']} | {r['baseline_median']:.3f} | {r['post_median']:.3f} | {r['drop'] * 100:+.1f} % | "
                     f"{r['baseline_cv'] * 100:.1f} % | {r['baseline_n']}/{r['post_n']} | **{r['decision'] or 'n/a'}** |")
    for r in t["changes"]:
        for reason in r["reasons"]:
            lines.append(f"- `{r['change']}`: {reason}")
    if t["rollout"]:
        ro = t["rollout"][0]
        lines += ["", f"`run_rollout` over [control, regression]: **{ro['outcome']}**, roll back {ro['rollback_nodes']}, "
                  f"not started {ro['not_started_waves']}."]
    if t["reconcile"]:
        rc = t["reconcile"][0]
        lines += ["", "## Read-only LinuxHost adapter", "",
                  f"Real state read: {rc['actual']} (no backend NIC netdev); `compute_plan`: unreachable {rc['unreachable']}, "
                  f"{rc['actions']} actions; second plan {rc['second_plan_actions']} actions; dry-run writes {rc['writes']}."]
    lines += ["", "What to conclude:", "",
              f"- The gate is only as good as the noise under it: the baseline varied by ~{m['baseline_cv_median'] * 100:.1f} % (CV) and "
              f"the no-op change moved the median {m['control_drop'] * 100:+.1f} %, comfortably inside the "
              f"{m['threshold_drop'] * 100:.0f} % threshold, so a real {m['regression_drop'] * 100:.0f} % regression stands out and "
              "a healthy change is not aborted. Measure the noise before you set the threshold.",
              "- Interleave baseline and post samples when you can; drift (thermals, a neighbour on the device) otherwise reads "
              "as a regression or hides one.",
              "- The controller refuses to decide on thin evidence: with half the bake samples it holds, neither proceeding "
              "nor rolling back.",
              "- This is one laptop Ada GPU with GEMM throughput standing in for per-rail busbw; the decision logic is the "
              "chapter's, the signal of a real fabric change needs the L3 two-node canary."]
    if env["device"] != "cuda":
        lines += ["", "_CPU fallback: the samples are CPU GEMM throughput; GPU health (temperature, HW slowdown) was not "
                  "checked._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
