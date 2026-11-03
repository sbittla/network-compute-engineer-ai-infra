"""Ch 21 L2: power draw vs throughput across workload intensities, perf/W, and the power-cap question.

What it teaches (Sections 21.5, 21.7 and 21.8): throughput per watt is measured, not assumed, and it depends
on *how* power is reduced. The run sweeps workload intensity on one GPU: a compute-bound FP16 GEMM duty-cycled
at 0 (idle), 25, 50, 75 and 100 % in 200 ms periods, plus a memory-bound copy at 100 %. Per level it records
achieved TFLOP/s (or GB/s), board power sampled every 100 ms (mean, p5/p95, swing within the period), SM clock,
temperature, and the share of samples with ``SW_POWER_CAP`` asserted. It then derives energy per TFLOP, perf/W,
and a linear power model ``P = P_static + k x throughput``.

Two comparisons carry the lesson:
- **Duty-cycling is not capping.** Lowering intensity at fixed voltage/frequency *raises* energy per unit of
  work, because static power is paid all the time. A power cap lowers V/f, and the lab's curve
  (``power_cap_curve.csv``, run through the lab's ``power_cap_tradeoff``) shows the opposite: perf/W improves as
  the cap goes down. The run puts both side by side.
- **The GPU is already capped.** At 100 % GEMM this laptop GPU sits at its enforced limit with ``SW_POWER_CAP``
  asserted and the SM clock below its memory-bound-copy clock: one real point on a cap curve, set by firmware.

Not runnable here: setting power limits (``nvidia-smi -pl`` needs root on a bare-metal Linux host; under WSL2
the Windows driver owns the limit). Limits are *read* and recorded. The cap sweep itself is recorded as
not runnable, and the lab's modeled curve stands in for it. Rack PDU telemetry (L3) is absent too.

CPU fallback: the same duty-cycle sweep with a CPU GEMM and a host-memory copy, measuring throughput and CPU busy
time. Host power is not readable (no RAPL in the container), so perf/W is recorded as not runnable and the L1
power-cap analysis runs on the lab's curve.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import threading
import time
from pathlib import Path

import hwlab

EXPERIMENT = {
    "id": "ch21-l2",
    "title": "Lab 21 L2: power draw vs throughput across workload intensities, and perf/W",
    "evidence": "MEASURED",
    "cpu_fallback": ("duty-cycle sweep of a CPU GEMM and a host-memory copy (throughput and CPU busy); host power is not "
                     "readable, so perf/W is not runnable and the lab's power-cap model runs on its own curve"),
}

PKG = Path(__file__).resolve().parents[2]
LAB = PKG / "lab"
PERIOD_S = 0.2
DUTIES = [0, 25, 50, 75, 100]
SAMPLE_FIELDS = ["index", "power.draw.instant", "power.draw.average", "clocks.sm", "temperature.gpu",
                 "utilization.gpu", "clocks_event_reasons.active", "memory.used"]
POWER_FIELDS = ["power.default_limit", "power.min_limit", "power.max_limit", "enforced.power.limit", "clocks.max.sm"]
FP16_FLOP_PER_CLK_SM = 1024   # dense FP16 tensor ceiling per SM per clock (Ada/Hopper whitepapers): an upper bound


def _num(v):
    v = (v or "").strip()
    if not v or v.startswith("[") or v in ("N/A", "Not Supported"):
        return None
    if v.lower().startswith("0x"):
        return int(v, 16)
    try:
        return float(v)
    except ValueError:
        return v


class NvSampler:
    def __init__(self, fields, interval_ms=100):
        self.fields, self.interval_ms, self.samples, self.proc = fields, interval_ms, [], None

    def __enter__(self):
        if shutil.which("nvidia-smi"):
            self.proc = subprocess.Popen(
                ["nvidia-smi", f"--query-gpu={','.join(self.fields)}", "--format=csv,noheader,nounits",
                 f"-lms={self.interval_ms}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
            threading.Thread(target=self._read, daemon=True).start()
            time.sleep(0.6)
        return self

    def _read(self):
        for line in self.proc.stdout:
            vals = line.split(",")
            if len(vals) == len(self.fields):
                row = dict(zip(self.fields, map(_num, vals)))
                if row.get("index") in (0, 0.0, None):
                    row["t"] = time.perf_counter()
                    self.samples.append(row)

    def window(self, t0, t1):
        return [s for s in self.samples if t0 <= s["t"] <= t1]

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        return False


def proc_stat():
    try:
        f = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
        return f[3] + f[4], sum(f)
    except (OSError, ValueError, IndexError):
        return None


def load_lab_model(name: str):
    """The lab's L1 model: the reference solution when the instructor tree is present, else the learner's starter."""
    for path in (PKG / "solutions" / "lab" / f"{name}.py", LAB / "starter" / f"{name}.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, path.relative_to(PKG).as_posix()
    return None, None


def pct(vals, q):
    s = sorted(v for v in vals if isinstance(v, (int, float)))
    return s[min(len(s) - 1, round(q * (len(s) - 1)))] if s else None


def fit_line(xs, ys):
    """Least squares y = a + b x; returns (a, b, r2)."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    a = my - b * mx
    ss_res = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, (1 - ss_res / ss_tot) if ss_tot else 1.0


# ----------------------------------------------------------------------------------------------- workloads
def make_work(ctx, kind: str):
    """Returns (fn, units_per_call, unit). One call is a short burst (~10-20 ms on the GPU)."""
    torch = ctx.torch
    dev = "cuda" if ctx.is_gpu else "cpu"
    if kind == "gemm":
        n = 4096 if ctx.is_gpu else 1024
        dt = torch.float16 if ctx.is_gpu else torch.float32
        a, b = torch.randn(n, n, device=dev, dtype=dt), torch.randn(n, n, device=dev, dtype=dt)
        c = torch.empty(n, n, device=dev, dtype=dt)
        k = 2 if ctx.is_gpu else 1

        def fn():
            for _ in range(k):
                torch.matmul(a, b, out=c)
            ctx.sync()
        return fn, k * 2.0 * n ** 3 / 1e12, "TFLOP"
    mib = 256 if ctx.is_gpu else 64
    src = torch.empty(mib * 2 ** 20, dtype=torch.uint8, device=dev)
    dst = torch.empty_like(src)

    def fn():
        dst.copy_(src)
        ctx.sync()
    return fn, 2 * mib * 2 ** 20 / 1e9, "GB"          # read + write bytes


def duty_cycle(fn, duty: int, seconds: float) -> tuple[int, float, float]:
    """Run bursts for duty % of every PERIOD_S, sleep the rest. Returns (calls, wall_s, busy_s)."""
    calls, busy, t_start = 0, 0.0, time.perf_counter()
    while time.perf_counter() - t_start < seconds:
        p0 = time.perf_counter()
        if duty > 0:
            while time.perf_counter() - p0 < PERIOD_S * duty / 100:
                b0 = time.perf_counter()
                fn()
                busy += time.perf_counter() - b0
                calls += 1
        rest = PERIOD_S - (time.perf_counter() - p0)
        if rest > 0:
            time.sleep(rest)
    return calls, time.perf_counter() - t_start, busy


# ----------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    secs = 3.0 if ctx.quick else 15.0
    notes = [f"Duty cycle in {PERIOD_S * 1e3:.0f} ms periods; each level runs {secs:.0f} s after a 0.5 s settle (dropped). "
             "Power is power.draw.instant sampled every 100 ms; energy = mean sampled power x wall time.",
             "Levels run from 0 % to 100 %, so the GPU warms through the sweep; temperature is recorded per level.",
             "The 0 % level follows the warm-up, so the GPU idles in a high performance state (SM clock still up). Deep idle "
             "(P8, about 2 W on this laptop) takes seconds to reach: the fitted static term is the price of being ready to work."]
    limits = {}
    not_runnable = []
    if ctx.is_gpu:
        limits = {k: _num(v) for k, v in hwlab.nvidia_smi_query(POWER_FIELDS)[0].items()}
    can_set = hasattr(os, "geteuid") and os.geteuid() == 0 and "microsoft" not in platform.release().lower()
    not_runnable.append({
        "part": "power-cap sweep (nvidia-smi -i 0 -pl <W> at each cap, >= 5 runs per cap)",
        "probe": f"euid={os.geteuid() if hasattr(os, 'geteuid') else '?'}, WSL2={'microsoft' in platform.release().lower()}; "
                 f"limits read-only: {limits or 'no GPU'}",
        "needs": ["root on a bare-metal Linux GPU host (dedicated lab system)", "restore the default limit afterwards"],
        "fallback": "duty-cycle sweep at the default limit + the lab's modeled cap curve"})
    if can_set:
        notes.append("This host could set power limits, but the experiment never changes system configuration; "
                     "run the README's cap sweep by hand on a dedicated lab host.")
    rapl = Path("/sys/class/powercap/intel-rapl")
    if not ctx.is_gpu:
        not_runnable.append({"part": "host power (RAPL) for CPU perf/W", "probe": f"{rapl} present: {rapl.is_dir()}",
                             "needs": ["bare-metal Linux with intel-rapl powercap readable"],
                             "fallback": "throughput and CPU busy only"})
    not_runnable.append({"part": "rack PDU power (L3: peak, p99, compute/communication swing)", "probe": "no PDU on a laptop",
                         "needs": ["read-only access to rack PDU and facility telemetry"], "fallback": "per-period GPU power swing"})

    levels = [("gemm", d) for d in DUTIES] + [("copy", 100)]
    rows = []
    sampler = NvSampler(SAMPLE_FIELDS, 100) if ctx.is_gpu else None
    if sampler:
        sampler.__enter__()
    try:
        work = {k: make_work(ctx, k) for k in ("gemm", "copy")}
        for fn, _, _ in work.values():          # warm-up: 3 calls each (cuBLAS heuristics, allocator)
            for _ in range(3):
                fn()
        for kind, duty in levels:
            fn, units, unit = work[kind]
            # settle into the new level; the idle level gets longer so board power decays from the warm-up to true idle
            duty_cycle(fn, duty, (1.0 if ctx.quick else 3.0) if duty == 0 else 0.5)
            s0 = proc_stat()
            t0 = time.perf_counter()
            calls, wall, busy = duty_cycle(fn, duty, secs)
            t1 = time.perf_counter()
            s1 = proc_stat()
            r = {"workload": kind, "duty_pct": duty, "calls": calls, "wall_s": round(wall, 3),
                 "throughput": calls * units / wall, "unit": f"{unit}/s", "busy_fraction": round(busy / wall, 3)}
            if sampler:
                w = sampler.window(t0, t1)
                p = [s["power.draw.instant"] for s in w if s.get("power.draw.instant") is not None]
                mask_cap = [1 if int(s.get("clocks_event_reasons.active") or 0) & 0x4 else 0 for s in w]
                r.update({"samples": len(w), "power_mean_w": round(sum(p) / len(p), 2) if p else None,
                          "power_p5_w": pct(p, 0.05), "power_p95_w": pct(p, 0.95),
                          "power_avg_field_w": pct([s["power.draw.average"] for s in w], 0.5),
                          "sm_mhz_median": pct([s["clocks.sm"] for s in w], 0.5),
                          "temp_c_max": max([s["temperature.gpu"] for s in w if s.get("temperature.gpu") is not None] or [None]),
                          "util_median": pct([s["utilization.gpu"] for s in w], 0.5),
                          "mem_used_min_mib": min([s["memory.used"] for s in w if s.get("memory.used") is not None] or [0]),
                          "mem_used_max_mib": max([s["memory.used"] for s in w if s.get("memory.used") is not None] or [0]),
                          "sw_power_cap_share": round(sum(mask_cap) / max(1, len(mask_cap)), 3)})
                if r["power_mean_w"]:
                    r["perf_per_w"] = r["throughput"] / r["power_mean_w"]            # TFLOP/J or GB/J
                    r["energy_per_unit_j"] = r["power_mean_w"] / r["throughput"] if r["throughput"] else None
                    r["swing_w"] = round(r["power_p95_w"] - r["power_p5_w"], 2)
            elif s0 and s1:
                r["cpu_busy"] = round(1 - (s1[0] - s0[0]) / max(1, s1[1] - s0[1]), 3)
            rows.append(r)
            ctx.log(f"{kind:5} {duty:3d}%  {r['throughput']:.3f} {r['unit']}"
                    + (f"  {r['power_mean_w']} W (p5 {r['power_p5_w']}, p95 {r['power_p95_w']})  SM {r['sm_mhz_median']} MHz  "
                       f"cap {r['sw_power_cap_share']}" if sampler else f"  cpu_busy {r.get('cpu_busy')}"))
        del work
        if ctx.is_gpu:
            torch.cuda.empty_cache()
    finally:
        if sampler:
            sampler.__exit__(None, None, None)

    gemm = [r for r in rows if r["workload"] == "gemm"]
    full = next(r for r in gemm if r["duty_pct"] == 100)
    for r in rows:
        r["rel_throughput"] = round(r["throughput"] / full["throughput"], 4) if r["workload"] == "gemm" else None
    metrics = {"gemm_tflops_100": round(full["throughput"], 3)}
    model = None
    if ctx.is_gpu:
        busy = [r for r in gemm if r["power_mean_w"]]
        a, b, r2 = fit_line([r["throughput"] for r in busy], [r["power_mean_w"] for r in busy])
        idle = next(r for r in gemm if r["duty_pct"] == 0)
        copy_r = next(r for r in rows if r["workload"] == "copy")
        p = torch.cuda.get_device_properties(0)
        mem_lo = min(r["mem_used_min_mib"] for r in rows)
        mem_hi = max(r["mem_used_max_mib"] for r in rows)
        metrics.update({
            "foreign_mem_swing_mib": round(mem_hi - mem_lo, 1), "idle_level_util_pct": idle["util_median"],
            "power_idle_w": idle["power_mean_w"], "power_gemm_100_w": full["power_mean_w"],
            "power_copy_100_w": copy_r["power_mean_w"], "copy_gbs_100": round(copy_r["throughput"], 1),
            "tflops_per_w_100": round(full["perf_per_w"], 4),
            "tflops_per_w_25": round(next(r for r in gemm if r["duty_pct"] == 25)["perf_per_w"], 4),
            "j_per_tflop_100": round(full["energy_per_unit_j"], 3),
            "sm_mhz_gemm_100": full["sm_mhz_median"], "sm_mhz_copy_100": copy_r["sm_mhz_median"],
            "sw_power_cap_share_gemm_100": full["sw_power_cap_share"],
            "power_model_static_w": round(a, 2), "power_model_w_per_tflops": round(b, 3), "power_model_r2": round(r2, 4),
            "max_period_swing_w": max(r["swing_w"] for r in busy),
            "enforced_power_limit_w": limits.get("enforced.power.limit"), "default_power_limit_w": limits.get("power.default_limit"),
            "max_power_limit_w": limits.get("power.max_limit"), "min_power_limit_w": limits.get("power.min_limit"),
            "gemm_ceiling_tflops": round(FP16_FLOP_PER_CLK_SM * p.multi_processor_count * (limits.get("clocks.max.sm") or 0) / 1e6, 1),
        })
    else:
        metrics["cpu_busy_100"] = full.get("cpu_busy")

    # -------- L1 model: the lab's cap curve through power_cap_tradeoff (what the cap sweep would replace)
    mod, model_path = load_lab_model("capacity_model")
    if mod:
        try:
            import pandas as pd
            import yaml
            curve = pd.read_csv(LAB / "data" / "power_cap_curve.csv")
            case = yaml.safe_load((LAB / "data" / "power_cap_case.yaml").read_text(encoding="utf-8"))
            tab = mod.power_cap_tradeoff(curve, case)
            curve = curve.assign(perf_per_w_rel=lambda d: (d.rel_throughput / d.gpu_power_cap_w) /
                                 (d.rel_throughput / d.gpu_power_cap_w).iloc[-1])
            model = {"model": model_path, "best_cap_w": mod.best_cap(tab), "table": tab.to_dict("records"),
                     "curve": curve.round(4).to_dict("records")}
            metrics["l1_best_cap_w"] = model["best_cap_w"]
            ctx.log(f"lab power_cap_tradeoff ({model_path}): best cap {model['best_cap_w']} W")
        except NotImplementedError as exc:
            notes.append(f"power_cap_tradeoff is not implemented yet in {model_path} ({exc}); the L1 comparison was skipped.")
    if ctx.is_gpu:
        dv = dvfs_downclocked(sorted((r for r in rows if r["workload"] == "gemm"), key=lambda r: r["duty_pct"]))
        metrics["dvfs_downclocked_duties"] = dv
        if dv:
            notes.append(f"DVFS: at {dv} % duty the median SM clock fell below 80 % of the full-load clock (the GPU idled down "
                         "between bursts), so those levels ran at a different V/f point. The fixed-V/f invariants (power rises "
                         "with duty; perf/W at 100 % >= 25 %) were not applied to them. Lock clocks (nvidia-smi -lgc, native "
                         "Linux, root) to test them; the experiment itself never changes system configuration.")
    for r in rows:
        r["throughput"] = round(r["throughput"], 4)
        if r.get("perf_per_w") is not None:
            r["perf_per_w"] = round(r["perf_per_w"], 5)
            r["energy_per_unit_j"] = round(r["energy_per_unit_j"], 4) if r["energy_per_unit_j"] else None
    return {"metrics": metrics, "tables": {"levels": rows, "limits": limits, "l1_power_cap": model},
            "not_runnable_parts": not_runnable, "notes": notes}


# ----------------------------------------------------------------------------------------------- check
def dvfs_downclocked(gemm: list[dict]) -> list[int]:
    """Busy duty levels whose median SM clock fell below 80 % of the 100 % level's: the GPU changed V/f point."""
    full = gemm[-1].get("sm_mhz_median") or 0
    return [r["duty_pct"] for r in gemm[1:-1] if full and (r.get("sm_mhz_median") or full) < 0.8 * full]


def invariant_scope(result: dict, env: dict) -> str:
    """Which invariants were not applied, for the report headline (empty when all applied)."""
    if env.get("device") != "cuda":
        return "GPU-only invariants skipped: CPU fallback"
    gemm = sorted((r for r in result["tables"]["levels"] if r["workload"] == "gemm"), key=lambda r: r["duty_pct"])
    dv = dvfs_downclocked(gemm)
    if not dv:
        return ""
    return (f"fixed-V/f checks skipped at {', '.join(str(d) for d in dv)} % duty: DVFS-shifted, SM clock below 80 % "
            "of the full-load clock")


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    gemm = sorted((r for r in t["levels"] if r["workload"] == "gemm"), key=lambda r: r["duty_pct"])
    fails = []
    tp = [r["throughput"] for r in gemm]
    if tp[0] != 0:
        fails.append("idle level reported work")
    for lo, hi in zip(gemm[1:], gemm[2:]):
        if hi["throughput"] < 0.9 * lo["throughput"]:
            fails.append(f"throughput fell from {lo['duty_pct']} % to {hi['duty_pct']} % duty: another job on the device, or "
                         "the duty-cycle timer is wrong")
    if gemm[-1]["throughput"] <= gemm[1]["throughput"]:
        fails.append("100 % duty is not faster than 25 % duty")
    if t.get("l1_power_cap") and t["l1_power_cap"]["best_cap_w"] != 650:
        fails.append(f"lab power_cap_tradeoff picks {t['l1_power_cap']['best_cap_w']} W; Table 21.7 says 650 W: check the model")
    if env["device"] == "cuda":
        if m["foreign_mem_swing_mib"] > 256 or (m["idle_level_util_pct"] or 0) > 10:
            fails.append(f"another process used the GPU during the sweep (memory.used moved by {m['foreign_mem_swing_mib']} MiB, "
                         f"util {m['idle_level_util_pct']} % at 0 % duty): power is board-level, so rerun with the GPU to yourself")
        lim, mx = m["enforced_power_limit_w"], m["max_power_limit_w"]
        for r in t["levels"]:
            if r["samples"] < 0.5 * r["wall_s"] * 10:
                fails.append(f"{r['workload']} {r['duty_pct']} %: only {r['samples']} power samples: check nvidia-smi -lms 100")
            if lim and r["power_mean_w"] and r["power_mean_w"] > 1.05 * lim:
                fails.append(f"{r['workload']} {r['duty_pct']} %: mean power {r['power_mean_w']} W above 1.05 x the {lim} W "
                             "enforced limit (nvidia-smi enforced.power.limit): check power.draw units/field")
            if mx and r["power_p95_w"] and r["power_p95_w"] > 1.15 * mx:
                fails.append(f"{r['workload']} {r['duty_pct']} %: p95 power above the {mx} W maximum limit")
        # The next two invariants assume a fixed V/f point. Without locked clocks (not settable under WSL2 or without
        # root), a laptop GPU drops to an idle P-state between short bursts, so light duty runs at a fraction of the
        # clock and draws less power per unit time than idle-after-load. Hold only clock-matched levels to them.
        dvfs = dvfs_downclocked(gemm)
        pw = [r["power_mean_w"] for r in gemm]
        for (d0, p0), (d1, p1) in zip(zip(DUTIES, pw), zip(DUTIES[1:], pw[1:])):
            if d0 in dvfs or d1 in dvfs:
                continue
            if p1 < p0 - max(3.0, 0.1 * p0):
                fails.append(f"power fell from {p0} W at {d0} % to {p1} W at {d1} %: power must rise with work at fixed V/f")
        if m["gemm_tflops_100"] > m["gemm_ceiling_tflops"]:
            fails.append(f"{m['gemm_tflops_100']} TFLOP/s above the {m['gemm_ceiling_tflops']} TFLOP/s FP16 tensor ceiling: check timing")
        if 25 not in dvfs and m["tflops_per_w_100"] < m["tflops_per_w_25"]:
            fails.append("perf/W at 100 % duty below 25 % duty: static power should make light duty cycles less efficient")
        if not m["power_idle_w"] < m["power_gemm_100_w"]:
            fails.append("idle power not below full-load power: check the sampler")
        if not m["power_copy_100_w"] < m["power_gemm_100_w"]:
            fails.append("memory-bound copy drew as much power as a compute-bound GEMM: check the workloads")
        if m["power_model_static_w"] <= 0:
            fails.append("fitted static power <= 0 W: the power/throughput fit is unphysical; check the levels")
    else:
        busy = [r.get("cpu_busy") for r in gemm]
        if None not in busy and busy[-1] <= busy[0]:
            fails.append("CPU busy at 100 % duty not above idle: check /proc/stat sampling")
    return fails


# ----------------------------------------------------------------------------------------------- report
def t_max(t: dict):
    return max((r.get("temp_c_max") or 0) for r in t["levels"])


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    L = ["## Intensity sweep (medians over the level" + ("; power sampled every 100 ms)" if gpu else ")"), ""]
    if gpu:
        L += ["| Workload | Duty % | Throughput | rel. | Mean W | p5-p95 W | SM MHz | Max C | SW_POWER_CAP share | Perf/W | J per unit |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in t["levels"]:
            L.append(f"| {r['workload']} | {r['duty_pct']} | {r['throughput']:.3f} {r['unit']} | {r['rel_throughput'] if r['rel_throughput'] is not None else '-'} | "
                     f"{r['power_mean_w']} | {r['power_p5_w']}-{r['power_p95_w']} | {r['sm_mhz_median']} | {r['temp_c_max']} | "
                     f"{r['sw_power_cap_share']} | {r.get('perf_per_w') or '-'} | {r.get('energy_per_unit_j') or '-'} |")
        L += ["", f"Power limits (read-only): default {m['default_power_limit_w']} W, enforced {m['enforced_power_limit_w']} W, "
              f"range {m['min_power_limit_w']}-{m['max_power_limit_w']} W. Linear fit over the GEMM levels: "
              f"P = {m['power_model_static_w']} W + {m['power_model_w_per_tflops']} W per TFLOP/s (R² {m['power_model_r2']}) `[MODELED]` "
              "from `[MEASURED]` points."]
    else:
        L += ["| Workload | Duty % | Throughput | rel. | CPU busy |", "|---|---|---|---|---|"]
        for r in t["levels"]:
            L.append(f"| {r['workload']} | {r['duty_pct']} | {r['throughput']:.4f} {r['unit']} | {r['rel_throughput'] if r['rel_throughput'] is not None else '-'} | {r.get('cpu_busy')} |")
    l1 = t.get("l1_power_cap")
    if l1:
        L += ["", f"## The lab's power-cap curve (`{l1['model']}`, `[ILLUSTRATIVE]` H100-class curve)", "",
              "| Cap W | rel. throughput | perf/W relative to 700 W | Nodes per rack | Cluster throughput |", "|---|---|---|---|---|"]
        tab = {r["cap_w"]: r for r in l1["table"]}
        for c in l1["curve"]:
            row = tab.get(int(c["gpu_power_cap_w"]), {})
            L.append(f"| {int(c['gpu_power_cap_w'])} | {c['rel_throughput']} | {c['perf_per_w_rel']} | {row.get('nodes_per_rack')} | "
                     f"{row.get('cluster_throughput')} |")
        L += ["", f"Best cap for the legacy-hall case: **{l1['best_cap_w']} W** (manuscript Table 21.7)."]
    L += ["", "## What to conclude", ""]
    if gpu:
        # Conclusions are emitted only when the invariant behind them holds (same V/f point, perf/W ordering).
        gemm = sorted((r for r in t["levels"] if r["workload"] == "gemm"), key=lambda r: r["duty_pct"])
        dvfs = dvfs_downclocked(gemm)
        matched = [r for r in gemm[1:] if r["duty_pct"] not in dvfs and r.get("perf_per_w")]
        if 25 not in dvfs and m["tflops_per_w_100"] >= m["tflops_per_w_25"]:
            duty_bullet = (f"- **Duty-cycling wastes energy; capping saves it.** At 25 % duty the GPU delivers {m['tflops_per_w_25']} "
                           f"TFLOP/J against {m['tflops_per_w_100']} at 100 %: about {m['power_model_static_w']} W of static and idle-clock "
                           "power is paid whether or not work runs. A power cap lowers voltage and frequency instead, and the lab's curve "
                           "shows perf/W *rising* as the cap falls. \"Use less power\" and \"do less work\" are different levers.")
        else:
            duty_bullet = ("- **Inconclusive at light duty.** The fixed-V/f comparison could not be made: at "
                           f"{', '.join(str(d) for d in (dvfs or [25]))} % duty the GPU ran at a different clock (DVFS idled it down between bursts), so those levels "
                           "do not test duty-cycling at a fixed V/f point. Clock-matched levels: "
                           + ", ".join(f"{r['duty_pct']} % -> {r['perf_per_w']} TFLOP/J" for r in matched)
                           + ". Lock clocks on a dedicated native-Linux lab host to test the light-duty levels.")
        L += [duty_bullet,
              (f"- **This GPU is already capped.** At 100 % GEMM it draws {m['power_gemm_100_w']} W against an enforced "
               f"{m['enforced_power_limit_w']} W, with `SW_POWER_CAP` in {100 * m['sw_power_cap_share_gemm_100']:.0f} % of samples"
               if m["sw_power_cap_share_gemm_100"] >= 0.5 else
               f"- **The limit that binds is not always the power cap.** At 100 % GEMM it draws {m['power_gemm_100_w']} W, below the "
               f"enforced {m['enforced_power_limit_w']} W, with `SW_POWER_CAP` in only {100 * m['sw_power_cap_share_gemm_100']:.0f} % of "
               f"samples at {t_max(t)} C: the boost clock is being reduced for temperature")
              + f", and the SM clock is {m['sm_mhz_gemm_100']} MHz versus {m['sm_mhz_copy_100']} MHz in the memory-bound copy at "
              f"{m['power_copy_100_w']} W. Compute-bound work hits the limits that memory-bound work does not (Section 21.8: the curve is "
              "workload-dependent; Section 21.7: thermal-performance coupling).",
              f"- **Transients are real at small scale.** Within one 200 ms duty period power swings by up to {m['max_period_swing_w']} W, "
              "which is the per-GPU version of the synchronized swing that drives the transient margin in Section 21.7.",
              "- This is a **laptop Ada GPU** with an 80 W-class limit, not a 700 W H100. Do not put these watts into the lab's rack model. "
              "Replace `power_cap_curve.csv` only with a cap sweep measured on your own data-center GPU (not runnable here)."]
    else:
        L += ["- _CPU fallback: no GPU was visible and host power is not readable, so perf/W could not be measured. The sweep shows "
              "throughput and CPU busy time rising with duty. The lab's modeled cap curve stands in for the cap sweep. GPU-only "
              "invariants (power bounds, perf/W ordering, the tensor ceiling) were skipped._"]
    L += ["", "## Not runnable on this host", "", "| Part | Probe | Needs | Instead |", "|---|---|---|---|"]
    L += [f"| {p['part']} | {p['probe']} | {', '.join(p['needs'])} | {p['fallback']} |" for p in result.get("not_runnable_parts", [])]
    return "\n".join(L)
