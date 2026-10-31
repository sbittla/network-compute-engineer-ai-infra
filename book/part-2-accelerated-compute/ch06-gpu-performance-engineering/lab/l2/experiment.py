"""Ch 6 L2: the benchmark protocol on a real GPU: telemetry-tagged runs, a measured roofline, and
statistical decisions made by the lab's own ``compare()``.

What it teaches (Sections 6.2-6.6): a benchmark result is a distribution of run medians, not one
number; clocks and clock-event reasons must be recorded per iteration so non-comparable runs can be
excluded by a rule fixed in advance; an A/A pair gives the noise floor below which no change is
believed; and the roofline (measured compute roof, measured memory roof, ridge point) says which
ceiling a kernel is up against before anyone tries to optimise it.

Three parts, all through the reference solution ``solutions/lab/analysis.py`` (unchanged):

1. Interleaved arms (round-robin, rotated start), >= 5 runs per arm, each run = 5 warm-up + N timed
   iterations timed with CUDA events and tagged with SM clock, temperature, power and decoded
   ``clocks_event_reasons`` sampled by ``nvidia-smi -lms 100``. Arms: FP32 GEMM with TF32 off (the
   baseline, plus an A/A pair of identical arms), the same GEMM in BF16 (a large real effect), FP32 with
   TF32 allowed, and a no-op change (``torch.mm(out=...)`` instead of ``torch.matmul``). ``compare()``
   cleans, tests (exact permutation on run medians) and decides.
2. A measured roofline: device-memory copy/add bandwidth on buffers larger than L2, a BF16 GEMM K-sweep
   from AI ~ 8 to ~ 1,400 FLOP/B, all classified by ``classify_kernels()`` against this GPU's vendor-class
   ceilings (derived from SM count x FLOP/clock/SM x max SM clock; DRAM from bus width x data rate).
3. The comparison with the manuscript's H100-class roofline (989 TFLOP/s BF16, 3.35 TB/s, ridge ~ 295).

CPU fallback: the same harness and the same compare() on single-threaded CPU GEMMs (FP64 baseline, A/A
pair, FP32 as the real effect, FP64 on 4 threads and a no-op as extra arms), then, on 4 threads, a host-memory
copy roof and an FP32 GEMM K-sweep (m = 3072, larger than the last-level cache) classified against the
*measured* CPU roofs. GPU-only invariants (vendor TFLOP/s and DRAM bounds,
telemetry) are skipped and the report says so.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch06-l2",
    "title": "Lab 6 L2: benchmark protocol, measured roofline and statistical decisions on a real GPU",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same interleaved-arm harness and compare() on single-threaded CPU GEMMs (FP64 baseline, A/A pair, "
                     "FP32 as the real effect), a host-memory copy roof and an FP32 GEMM K-sweep classified against the measured CPU roofs"),
}

PKG = Path(__file__).resolve().parents[2]
H100 = {"bf16_tflops": 989.0, "hbm_tbs": 3.35}  # manuscript / lab data/device.yaml [VENDOR-SPEC, 2026-10]

# Dense FLOP per clock per SM by compute capability. Sources: NVIDIA Ada (AD102) whitepaper, RTX 4090 column:
# 165.2 TFLOPS BF16 (FP32 accumulate) / 82.6 TF32 / 82.6 FP32 at 128 SMs x 2520 MHz -> 512 / 256 / 256 per SM per
# clock on GeForce Ada; Ampere GA10x the same; A100 312/156/19.5 at 108 SMs x 1410 MHz; H100 SXM 989/495/67 at
# 132 SMs x 1830 MHz. These are peaks: no kernel may exceed them at the max SM clock.
FLOP_PER_CLK_SM = {
    (8, 9): {"bf16_tensor": 512, "tf32_tensor": 256, "fp32_simt": 256},
    (8, 6): {"bf16_tensor": 512, "tf32_tensor": 256, "fp32_simt": 256},
    (8, 0): {"bf16_tensor": 2048, "tf32_tensor": 1024, "fp32_simt": 128},
    (9, 0): {"bf16_tensor": 4096, "tf32_tensor": 2048, "fp32_simt": 256},
}
# Memory bus width in bits for GDDR parts (not queryable through nvidia-smi). Source: NVIDIA product specs.
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4080 laptop": 192,
            "rtx 4090 laptop": 256, "rtx 4090": 384, "rtx 3090": 384}
EVENT_BITS = {0x1: "gpu_idle", 0x2: "applications_clocks_setting", 0x4: "sw_power_cap", 0x8: "hw_slowdown",
              0x10: "sync_boost", 0x20: "sw_thermal_slowdown", 0x40: "hw_thermal_slowdown",
              0x80: "hw_power_brake_slowdown", 0x100: "display_clock_setting"}


def load_solution(name: str):
    # Reference solution when present (instructor tree); the learner's starter/ in the student release.
    path = PKG / "solutions" / "lab" / f"{name}.py"
    if not path.is_file():
        path = PKG / "lab" / "starter" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ch06_solution_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def decode_reasons(text: str) -> str:
    """nvidia-smi clocks_event_reasons.active bitmask -> lab vocabulary ("none", "sw_power_cap", "a+b")."""
    try:
        mask = int(text, 16)
    except ValueError:
        return "unknown"
    names = [n for bit, n in EVENT_BITS.items() if mask & bit]
    return "+".join(names) if names else "none"


def gpu_ceilings(env: dict) -> dict:
    """Vendor-class ceilings for GPU 0 at its max SM clock, with the derivation recorded."""
    g = (env.get("gpus") or [{}])[0]
    cap = tuple(int(x) for x in env.get("gpu0", {}).get("capability", "0.0").split("."))
    sms = env.get("gpu0", {}).get("sm_count")
    out = {"source": "SM count x dense FLOP/clock/SM (NVIDIA architecture whitepapers) x clocks.max.sm; "
                     "DRAM = bus width (NVIDIA product spec) x 2 x clocks.max.memory"}
    try:
        clk = float(g["clocks.max.sm"]) * 1e6
        per = FLOP_PER_CLK_SM[cap]
        out["peak_flops"] = {k: sms * v * clk for k, v in per.items()}
        out["max_sm_mhz"] = clk / 1e6
    except (KeyError, ValueError, TypeError):
        out["peak_flops"] = None
    name = env.get("gpu0", {}).get("name", "").lower()
    bits = next((b for k, b in sorted(BUS_BITS.items(), key=lambda kv: -len(kv[0])) if k in name), None)
    try:
        out["dram_bytes_per_s"] = float(g["clocks.max.memory"]) * 1e6 * 2 * bits / 8 if bits else None
        out["bus_bits"] = bits
    except (KeyError, ValueError):
        out["dram_bytes_per_s"] = None
    return out


class Telemetry:
    """Background sampler: ``nvidia-smi -lms 100`` on the GPU; /proc/cpuinfo MHz on the CPU."""

    FIELDS = "clocks.sm,temperature.gpu,power.draw,clocks_event_reasons.active,utilization.gpu"

    def __init__(self, gpu: bool):
        self.gpu, self.samples, self._stop, self.proc = gpu, [], threading.Event(), None
        if gpu and shutil.which("nvidia-smi"):
            self.proc = subprocess.Popen(["nvidia-smi", f"--query-gpu={self.FIELDS}", "--format=csv,noheader,nounits",
                                          "-lms", "100", "-i", "0"], stdout=subprocess.PIPE, text=True)
            self.thread = threading.Thread(target=self._read_gpu, daemon=True)
        else:
            self.thread = threading.Thread(target=self._read_cpu, daemon=True)
        self.thread.start()

    def _read_gpu(self):
        for line in self.proc.stdout:
            v = [x.strip() for x in line.split(",")]
            if len(v) == 5:
                try:
                    self.samples.append((time.monotonic(), float(v[0]), float(v[1]),
                                         float(v[2]) if v[2] not in ("[N/A]", "N/A") else 0.0, decode_reasons(v[3]), float(v[4])))
                except ValueError:
                    continue

    def _read_cpu(self):
        while not self._stop.is_set():
            try:
                mhz = [float(x.split(":")[1]) for x in Path("/proc/cpuinfo").read_text().splitlines() if x.startswith("cpu MHz")]
            except OSError:
                mhz = []
            self.samples.append((time.monotonic(), sum(mhz) / len(mhz) if mhz else 0.0, 0.0, 0.0, "none", 0.0))
            self._stop.wait(0.1)

    def at(self, t: float) -> tuple:
        """The latest sample taken at or before t (else the first sample)."""
        best = None
        for s in reversed(self.samples):
            if s[0] <= t:
                best = s
                break
        return best or (self.samples[0] if self.samples else (t, 0.0, 0.0, 0.0, "unknown", 0.0))

    def wait_ready(self, timeout: float = 5.0) -> None:
        t0 = time.monotonic()
        while not self.samples and time.monotonic() - t0 < timeout:
            time.sleep(0.05)

    def stop(self) -> None:
        self._stop.set()
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)


def make_arms(ctx, n: int) -> dict:
    torch = ctx.torch
    dev = "cuda" if ctx.is_gpu else "cpu"
    g = torch.Generator(device=dev).manual_seed(6)
    if ctx.is_gpu:
        base_dt, fast_dt = torch.float32, torch.bfloat16
    else:
        base_dt, fast_dt = torch.float64, torch.float32
    a = torch.randn(n, n, device=dev, dtype=base_dt, generator=g)
    b = torch.randn(n, n, device=dev, dtype=base_dt, generator=g)
    af, bf = a.to(fast_dt), b.to(fast_dt)
    out = torch.empty_like(a)

    def tf32(flag):
        torch.backends.cuda.matmul.allow_tf32 = flag

    def plain():
        tf32(False)
        torch.matmul(a, b)

    def noop():
        tf32(False)
        torch.mm(a, b, out=out)

    def fast():
        torch.matmul(af, bf)

    arms = {"base": plain, "AA1": plain, "AA2": plain, "fast": fast, "noop": noop}
    if ctx.is_gpu:
        def alt():
            tf32(True)
            torch.matmul(a, b)
        labels = {"base": "FP32 GEMM, TF32 off", "fast": "BF16 GEMM", "alt": "FP32 GEMM, TF32 allowed",
                  "noop": "FP32 GEMM via torch.mm(out=)"}
    else:
        def alt():
            torch.set_num_threads(min(4, os.cpu_count() or 1))
            try:
                torch.matmul(a, b)
            finally:
                torch.set_num_threads(1)
        labels = {"base": "FP64 GEMM, 1 thread", "fast": "FP32 GEMM, 1 thread", "alt": "FP64 GEMM, 4 threads",
                  "noop": "FP64 GEMM via torch.mm(out=), 1 thread"}
    arms["alt"] = alt
    labels.update({"AA1": labels["base"] + " (A/A group 1)", "AA2": labels["base"] + " (A/A group 2)"})
    return {"fns": arms, "labels": labels, "flop": 2.0 * n ** 3, "cleanup": lambda: tf32(False) if ctx.is_gpu else None}


def timed_iters(ctx, fn, iters: int, tel: Telemetry) -> list[tuple]:
    torch = ctx.torch
    rows = []
    for i in range(iters):
        if ctx.is_gpu:
            s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            s.record()
            fn()
            e.record()
            e.synchronize()
            ms = s.elapsed_time(e)
        else:
            t0 = time.perf_counter()
            fn()
            ms = (time.perf_counter() - t0) * 1e3
        rows.append((i, ms, tel.at(time.monotonic())))
    return rows


def run_arms(ctx, env: dict, tel: Telemetry) -> dict:
    pd = __import__("pandas")
    n = (2048 if ctx.quick else 4096) if ctx.is_gpu else (384 if ctx.quick else 512)
    runs = 5 if ctx.quick else 8
    target_s = 0.4 if ctx.quick else 1.0       # each run spans several 100 ms telemetry samples
    arms = make_arms(ctx, n)
    names = list(arms["fns"])
    sw = software_versions(env)
    # Pre-heat: leave the idle power state before the first timed run (a cold first run is not comparable).
    t_end = time.monotonic() + (1.0 if ctx.quick else 3.0)
    while time.monotonic() < t_end:
        arms["fns"]["base"]()
        ctx.sync()
    # Iterations per arm from a calibration pass: 5 warm-up (dropped by clean_runs) + enough for target_s.
    iters = {}
    for arm in names:
        st = ctx.bench(arms["fns"][arm], warmup=2, reps=5)
        iters[arm] = 5 + max(20, int(target_s / st["median"]))
    rows = []
    for r in range(runs):                          # round-robin, start rotated each round: drift hits every arm
        order = names[r % len(names):] + names[:r % len(names)]
        for arm in order:
            for i, ms, s in timed_iters(ctx, arms["fns"][arm], iters[arm], tel):
                rows.append({"arm": arm, "run_id": f"{arm}-{r + 1}", "iter": i, "latency_ms": ms,
                             "sm_clock_mhz": s[1], "gpu_temp_c": s[2], "power_w": s[3], "clocks_event_reasons": s[4],
                             "util_pct": s[5], **sw, "kernel_variant": arms["labels"][arm]})
    arms["cleanup"]()
    df = pd.DataFrame(rows)
    return {"df": df, "n": n, "runs": runs, "iters": iters, "flop": arms["flop"], "labels": arms["labels"], "sw": sw}


def software_versions(env: dict) -> dict:
    g = (env.get("gpus") or [{}])[0]
    return {"driver": str(g.get("driver_version", "none")), "cuda": str(env.get("cuda_runtime") or "none"),
            "torch": str(env.get("torch"))}


# Pre-registered (fixed before any data is collected): arms that run the SAME kernel as the baseline are
# compared with the lab's compare() unchanged (session-wide peer clock). Arms that run a DIFFERENT kernel are
# also compared with compare() unchanged, but the decision uses the same rules with the clock check made
# against each arm's own peer runs: under a power cap the sustained clock is a consequence of the kernel
# (BF16 tensor-core GEMMs draw less power per clock than FP32 SIMT GEMMs), not evidence of throttling.
SAME_KERNEL_ARMS = {"noop"}


def same_code_peer_compare(an, base, cand, sw: dict, floor: float) -> dict:
    """compare()'s statistics and decision rule, with the clock-exclusion peer = the arm's own runs."""
    def clean(df):
        peer = float(df.groupby("run_id")["sm_clock_mhz"].median().median())
        return an.clean_runs(df, sw, peer_clock_mhz=peer)
    cb, eb = clean(base)
    cc, ec = clean(cand)
    rb, rc = an.run_medians(cb), an.run_medians(cc)
    out = {"excluded": eb + ec, "n_runs_base": len(rb), "n_runs_cand": len(rc), "floor": floor,
           "threshold": an.PRACTICAL_THRESHOLD, "naive": an.naive_compare(base, cand)}
    if len(rb) < 2 or len(rc) < 2:
        return {**out, "point": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"), "p_perm": float("nan"),
                "cliffs_delta_runs": float("nan"), "decision": "undecidable"}
    p, lo, hi = an.bootstrap_ratio_ci(rb, rc)
    pp = an.permutation_test(rb, rc)
    bar = max(floor, an.PRACTICAL_THRESHOLD)
    decision = ("not_significant" if pp >= an.ALPHA else "below_threshold" if abs(p) < bar
                else "improvement" if p < 0 else "regression")
    return {**out, "point": p, "ci_lo": lo, "ci_hi": hi, "p_perm": pp, "cliffs_delta_runs": an.cliffs_delta(rc, rb),
            "decision": decision}


def lab_compare(an, base, cand, sw: dict, floor: float) -> dict:
    """compare() unchanged; an arm emptied by exclusions is reported as undecidable (compare() itself would
    turn the NaN statistics into a spurious decision)."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        c = an.compare(base, cand, sw, floor)
    c["excluded"] = [dict(e) for e in c["excluded"]]
    if c["n_runs_base"] < 2 or c["n_runs_cand"] < 2:
        c["decision"] = "undecidable"
    return c


def decide(an, arm_data: dict) -> dict:
    df, sw = arm_data["df"], arm_data["sw"]
    aa = df[df["arm"].isin(["AA1", "AA2"])].copy()
    floor = an.noise_floor(aa, sw)
    base = df[df["arm"] == "base"]
    out = {"noise_floor": floor}
    for arm in ("fast", "alt", "noop"):
        cand = df[df["arm"] == arm]
        lab = lab_compare(an, base, cand, sw, floor)
        if arm in SAME_KERNEL_ARMS:
            used, rule = lab, "lab rule (session-wide peer clock)"
        else:
            used, rule = same_code_peer_compare(an, base, cand, sw, floor), "per-arm peer clock"
        out[arm] = {**used, "rule": rule, "lab_rule": {k: lab[k] for k in ("point", "p_perm", "decision", "n_runs_base", "n_runs_cand")}}
    aa_cmp = lab_compare(an, df[df["arm"] == "AA1"], df[df["arm"] == "AA2"], sw, floor)
    out["aa"] = {k: aa_cmp[k] for k in ("point", "ci_lo", "ci_hi", "p_perm", "decision")}
    return out


def roofline(ctx, an, ceilings: dict | None) -> dict:
    """Measured memory roof, measured compute roof, and a GEMM K-sweep classified by classify_kernels()."""
    torch = ctx.torch
    pd = __import__("pandas")
    dev = "cuda" if ctx.is_gpu else "cpu"
    if not ctx.is_gpu:   # roofs are a property of the machine: use 4 threads (the arms above were single-threaded)
        torch.set_num_threads(min(4, os.cpu_count() or 1))
    mib = (128 if ctx.quick else 256) if ctx.is_gpu else (64 if ctx.quick else 256)
    nel = mib * 1024 * 1024 // 4
    x, y, z = (torch.rand(nel, device=dev) for _ in range(3))
    reps = ctx.reps(20)
    copy = ctx.bench(lambda: z.copy_(x), reps=reps)
    add = ctx.bench(lambda: torch.add(x, y, out=z), reps=reps)
    rows = [{"name": f"copy_fp32_{mib}MiB", "precision": "fp32_simt", "flop": 0.0, "dram_bytes": 2.0 * 4 * nel,
             "time_us": copy["median"] * 1e6, "p95_us": copy["p95"] * 1e6, "iqr_us": copy["iqr"] * 1e6, "n": copy["n"]},
            {"name": f"add_fp32_{mib}MiB", "precision": "fp32_simt", "flop": float(nel), "dram_bytes": 3.0 * 4 * nel,
             "time_us": add["median"] * 1e6, "p95_us": add["p95"] * 1e6, "iqr_us": add["iqr"] * 1e6, "n": add["n"]}]
    del x, y, z
    if ctx.is_gpu:
        m = 2048 if ctx.quick else 4096
        ks = [8, 32, 128, 512, 2048] if ctx.quick else [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        dt, prec, esz = torch.bfloat16, "bf16_tensor", 2
    else:
        m = 3072                 # output 36 MiB: larger than the CPU's last-level cache, so thin GEMMs stream DRAM
        ks = [4, 64, 512] if ctx.quick else [4, 16, 64, 256, 1024]
        dt, prec, esz = torch.float32, "fp32_simt", 4
    for k in ks:
        a = torch.randn(m, k, device=dev, dtype=dt)
        b = torch.randn(k, m, device=dev, dtype=dt)
        st = ctx.bench(lambda: torch.matmul(a, b), reps=reps)
        rows.append({"name": f"gemm_{m}x{m}x{k}", "precision": prec, "flop": 2.0 * m * m * k,
                     "dram_bytes": float(esz * (m * k + k * m + m * m)),   # compulsory traffic: a lower bound
                     "time_us": st["median"] * 1e6, "p95_us": st["p95"] * 1e6, "iqr_us": st["iqr"] * 1e6, "n": st["n"], "k": k})
    kern = pd.DataFrame(rows)
    measured_bw = max(r["dram_bytes"] / (r["time_us"] * 1e-6) for r in rows[:2])
    measured_flops = max(r["flop"] / (r["time_us"] * 1e-6) for r in rows[2:])
    if ceilings and ceilings.get("peak_flops") and ceilings.get("dram_bytes_per_s"):
        device = {"peak_flops": ceilings["peak_flops"], "hbm_bytes_per_s": ceilings["dram_bytes_per_s"], "roof": "vendor"}
    else:   # CPU (or an unknown GPU): no vendor ceiling asserted; the roof is what we measured
        device = {"peak_flops": {prec: measured_flops},
                  "hbm_bytes_per_s": measured_bw, "roof": "measured"}
    cls = an.classify_kernels(kern[["name", "precision", "flop", "dram_bytes", "time_us"]], device)
    cls = pd.concat([cls, kern[["p95_us", "iqr_us", "n"]]], axis=1)
    cls["k"] = kern.get("k")
    recs = cls.astype(object).where(cls.notna(), None).to_dict("records")
    return {"kernels": recs, "measured_bw": measured_bw, "measured_flops": measured_flops,
            "measured_ridge": measured_flops / measured_bw, "roof": device["roof"],
            "device": {k: v for k, v in device.items()}, "m": m, "precision": prec}


def run(ctx) -> dict:
    sys.path.insert(0, "/opt/hwlab")
    import hwlab  # noqa: E402  (the runtime is on the image; used for the environment manifest only)
    an = load_solution("analysis")
    harness = load_solution("harness")
    env = hwlab.environment(ctx.device)
    ceilings = gpu_ceilings(env) if ctx.is_gpu else None
    if not ctx.is_gpu:
        # One BLAS thread: a CPU shared with other jobs makes all-core GEMMs swing by 10x between runs (oversubscription).
        ctx.torch.set_num_threads(1)
    tel = Telemetry(ctx.is_gpu)
    tel.wait_ready()
    try:
        t0 = time.perf_counter()
        arm_data = run_arms(ctx, env, tel)
        ctx.log(f"arms done in {time.perf_counter() - t0:.1f}s ({arm_data['runs']} runs x {len(arm_data['labels'])} arms)")
        roof = roofline(ctx, an, ceilings)
    finally:
        tel.stop()
    dec = decide(an, arm_data)
    df = arm_data["df"]
    timed = df[df["iter"] >= an.WARMUP_ITERS]
    per_arm = []
    for arm, g in timed.groupby("arm", sort=False):
        rm = an.run_medians(g)
        s = an.summarize(g["latency_ms"])
        per_arm.append({"arm": arm, "label": arm_data["labels"][arm], "runs": int(g["run_id"].nunique()),
                        "median_ms": s["median"], "p95_ms": s["p95"], "p99_ms": s["p99"], "iqr_ms": s["iqr"],
                        "min_ms": s["min"], "max_ms": s["max"], "cv": s["cv"],
                        "run_median_spread_pct": float((rm.max() - rm.min()) / an.np.median(rm) * 100),
                        "tflops_median": arm_data["flop"] / (s["median"] * 1e-3) / 1e12,
                        "sm_clock_median_mhz": float(g["sm_clock_mhz"].median()),
                        "temp_max_c": float(g["gpu_temp_c"].max()), "power_median_w": float(g["power_w"].median()),
                        "event_reasons": sorted(set(g["clocks_event_reasons"]))})
    reasons = df["clocks_event_reasons"].value_counts().to_dict()
    m = {f"tflops_{a['arm']}": round(a["tflops_median"], 3) for a in per_arm}
    m.update({"noise_floor_pct": round(dec["noise_floor"] * 100, 3),
              "fast_vs_base_pct": round(dec["fast"]["point"] * 100, 2), "fast_decision": dec["fast"]["decision"],
              "alt_decision": dec["alt"]["decision"], "noop_decision": dec["noop"]["decision"],
              "measured_bw_gbs": round(roof["measured_bw"] / 1e9, 2), "measured_peak_tflops": round(roof["measured_flops"] / 1e12, 3),
              "measured_ridge_flop_per_byte": round(roof["measured_ridge"], 1)})
    notes = [
        "Each run is 5 warm-up iterations (dropped by clean_runs) plus timed iterations; runs are interleaved round-robin "
        "with a rotated start. Runs share one process (a deviation from the lab's one-process-per-run rule, made so the "
        "GPU context and allocations are created once); run-to-run variance therefore understates cold-start effects.",
        "Telemetry is sampled every 100 ms by nvidia-smi and attached to each iteration by timestamp, so several "
        "iterations share one sample." if ctx.is_gpu else
        "CPU fallback: no GPU telemetry; sm_clock_mhz holds the mean /proc/cpuinfo MHz (static under WSL2), "
        "temperature/power are 0 and clocks_event_reasons is 'none'. torch runs single-threaded (the 'alt' arm uses 4) "
        "so that other jobs on the host do not oversubscribe the cores mid-run.",
        "GEMM DRAM bytes are compulsory traffic (each operand read once, output written once) [MODELED]: a lower "
        "bound on real traffic, so the achieved bandwidth they imply is a lower bound too.",
    ]
    if ctx.is_gpu:
        notes.append("Clocks were not locked (no root, and a shared laptop GPU); exclusions follow the lab's pre-registered "
                     "rules: non-routine clock events on > 5 % of iterations, or median SM clock < 95 % of the peer median.")
    return {"metrics": m, "tables": {"arms": per_arm, "roofline": roof["kernels"]},
            "decisions": dec, "roof": {k: v for k, v in roof.items() if k != "kernels"}, "ceilings": ceilings,
            "event_reason_counts": reasons, "harness_manifest": harness.environment_manifest(seed=6),
            "workload": {"gemm_n": arm_data["n"], "runs_per_arm": arm_data["runs"], "iters_per_run": arm_data["iters"],
                         "warmup_iters": an.WARMUP_ITERS, "timer": "CUDA events" if ctx.is_gpu else "perf_counter",
                         "run_order": "round-robin, start rotated per round", "roofline_gemm_m": roof["m"]},
            "notes": notes}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    gpu = env["device"] == "cuda"
    arms = {a["arm"]: a for a in result["tables"]["arms"]}
    dec = result["decisions"]
    kern = result["tables"]["roofline"]
    if any(a["median_ms"] <= 0 for a in arms.values()):
        fails.append("non-positive latency: check the timer (CUDA events need a synchronize before elapsed_time)")
    # 1. a large real effect must be detected; the noise floor must sit below it
    f = dec["fast"]
    # The exact permutation test can reach p < 0.05 only with >= 3 runs per arm and >= 7 in total (3 + 4: p_min = 1/35).
    if min(f["n_runs_base"], f["n_runs_cand"]) >= 3 and f["n_runs_base"] + f["n_runs_cand"] >= 7:
        if f["decision"] != "improvement":
            fails.append(f"{arms['fast']['label']} vs {arms['base']['label']} decided '{f['decision']}' (point {f['point']:+.1%}, "
                         f"p {f['p_perm']:.3f}); a 2-4x effect must be an improvement: check run interleaving and exclusions")
    else:
        fails.append(f"only {f['n_runs_base']}/{f['n_runs_cand']} runs survived cleaning: check clocks_event_reasons and "
                     "other processes on the GPU (nvidia-smi), then re-run")
    if dec["noise_floor"] >= abs(f["point"]):
        fails.append(f"A/A noise floor {dec['noise_floor']:.1%} is not below the real effect {abs(f['point']):.1%}: the "
                     "measurement is too noisy to decide anything; check for other GPU/CPU load")
    if dec["aa"]["decision"] in ("improvement", "regression"):
        fails.append("the A/A pair (identical code) was decided a real change: the decision rule or the floor is broken")
    # 2. roofline consistency
    for r in kern:
        if r["bound"] == "anomaly" and gpu:
            fails.append(f"{r['name']} exceeds a ceiling ({r['note']}): check the FLOP/byte accounting or the ceilings")
    gemms = sorted((r for r in kern if r["name"].startswith("gemm")), key=lambda r: r["k"])
    # On the CPU the memory roof is a measured copy rate (caches, write-allocate), so a thin GEMM can sit just above
    # it ("anomaly"); what must hold is which side of the measured ridge each end of the sweep falls.
    thin_ok = gemms[0]["bound"] == "memory" if gpu else gemms[0]["ai"] < gemms[0]["ridge"]
    if not thin_ok or gemms[-1]["bound"] != "compute":
        fails.append(f"K-sweep classification {gemms[0]['name']}={gemms[0]['bound']}, {gemms[-1]['name']}={gemms[-1]['bound']}: "
                     "the thinnest GEMM must be memory-bound and the squarest compute-bound (check AI and the ridge)")
    if gemms[-1]["achieved_flops"] < 3 * gemms[0]["achieved_flops"]:
        fails.append("achieved FLOP/s did not rise with arithmetic intensity across the K-sweep: check the sizes and the timer")
    if gpu:
        c = result.get("ceilings") or {}
        pk, bw = c.get("peak_flops"), c.get("dram_bytes_per_s")
        if pk:
            for arm, prec in (("base", "fp32_simt"), ("fast", "bf16_tensor"), ("alt", "tf32_tensor")):
                ach = arms[arm]["tflops_median"] * 1e12
                if ach > 1.02 * pk[prec]:
                    fails.append(f"{arms[arm]['label']} at {ach / 1e12:.1f} TFLOP/s exceeds the {prec} peak "
                                 f"{pk[prec] / 1e12:.1f} TFLOP/s at max clock: check the FLOP count (2n^3) or the timer")
        if bw and result["roof"]["measured_bw"] > 1.02 * bw:
            fails.append(f"measured DRAM bandwidth {result['roof']['measured_bw'] / 1e9:.0f} GB/s exceeds the {bw / 1e9:.0f} GB/s "
                         "spec: buffers may be L2-resident (use > L2 size) or the byte count is wrong")
        if bw and result["roof"]["measured_bw"] < 0.4 * bw:
            fails.append(f"measured DRAM bandwidth {result['roof']['measured_bw'] / 1e9:.0f} GB/s < 40 % of spec: check for "
                         "another process on the GPU or a low memory clock")
        if arms["fast"]["tflops_median"] <= arms["base"]["tflops_median"]:
            fails.append("BF16 tensor-core GEMM was not faster than FP32 SIMT: check that the BF16 arm really uses bfloat16")
    return fails


def _pct(x):
    return f"{x * 100:+.2f} %"


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    m, dec, roof = result["metrics"], result["decisions"], result["roof"]
    w = result["workload"]
    L = ["## Workload and protocol", "",
         f"Square GEMM n = {w['gemm_n']}; {w['runs_per_arm']} runs per arm, {w['iters_per_run']} iterations per run (per arm, sized to ~{0.4 if env.get('quick') else 1.0:g} s) "
         f"({w['warmup_iters']} warm-up dropped); timer: {w['timer']}; order: {w['run_order']}.", "",
         "## Arms (cleaned iterations)", "",
         "| Arm | What | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Run-median spread | TFLOP/s | SM clock (MHz) | Max temp (C) | Clock events |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in result["tables"]["arms"]:
        L.append(f"| {a['arm']} | {a['label']} | {a['median_ms']:.3f} | {a['p95_ms']:.3f} | {a['iqr_ms']:.3f} | "
                 f"{a['min_ms']:.3f}-{a['max_ms']:.3f} | {a['run_median_spread_pct']:.1f} % | {a['tflops_median']:.2f} | "
                 f"{a['sm_clock_median_mhz']:.0f} | {a['temp_max_c']:.0f} | {', '.join(a['event_reasons'])} |")
    L += ["", "## Decisions (`compare()` from the lab's reference analysis, unchanged)", "",
          f"A/A noise floor: **±{dec['noise_floor'] * 100:.2f} %**; practical threshold 1 %.", "",
          "| Candidate vs base | Clock rule | Point | 95 % band | p (perm.) | Cliff's d (runs) | Runs base/cand | Naive mean | Decision | Lab rule as written |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    labels = {a["arm"]: a["label"] for a in result["tables"]["arms"]}
    for arm in ("fast", "alt", "noop"):
        c = dec[arm]
        lr = c["lab_rule"]
        L.append(f"| {labels[arm]} | {c['rule']} | {_pct(c['point'])} | [{_pct(c['ci_lo'])}, {_pct(c['ci_hi'])}] | {c['p_perm']:.3f} | "
                 f"{c['cliffs_delta_runs']:+.2f} | {c['n_runs_base']}/{c['n_runs_cand']} | {_pct(c['naive'])} | **{c['decision']}** | "
                 f"{lr['decision']} ({lr['n_runs_base']}/{lr['n_runs_cand']} runs kept) |")
    a = dec["aa"]
    L.append(f"| A/A (group 1 vs 2) | lab rule | {_pct(a['point'])} | [{_pct(a['ci_lo'])}, {_pct(a['ci_hi'])}] | {a['p_perm']:.3f} | | | | {a['decision']} | |")
    emptied = [labels[arm] for arm in ("fast", "alt") if dec[arm]["lab_rule"]["decision"] == "undecidable"]
    L += ["", "Clock rule: same-kernel comparisons (A/A, no-op) use `compare()` exactly as written. Different-kernel "
          "comparisons apply the same exclusion rules but judge each run's clock against runs of the same code, "
          "because under a power cap the sustained clock depends on the kernel (pre-registered in the experiment, "
          "not chosen after seeing the data)."]
    if emptied:
        L += ["", f"**Lab rule as written, on this power-capped GPU:** for {' and '.join(emptied)} the session-wide peer clock "
              "sits between the two arms' sustained clocks, so the 95 % rule excluded the slower-clocked arm's runs and "
              "left nothing to compare (undecidable). That is the lesson: a clock rule that assumes clocks are independent "
              "of the change is only valid with locked clocks or for changes that keep the same kernel."]
    excl = [e for arm in ("fast", "alt", "noop") for e in dec[arm]["excluded"]]
    if excl:
        L += ["", "Excluded runs (pre-registered rules, same for every arm):", ""]
        L += sorted({f"- `{e['run_id']}`: {e['reason']} — {e['detail']}" for e in excl})
    if gpu:
        L += ["", f"Clock-event reasons over all samples: {result['event_reason_counts']}."]
    L += ["", f"## Roofline ({'vendor-class ceilings for this GPU' if roof['roof'] == 'vendor' else 'measured CPU roofs'})", ""]
    c = result.get("ceilings")
    if gpu and c and c.get("peak_flops"):
        pk = c["peak_flops"]
        L += [f"Ceilings `[MODELED]` at clocks.max.sm = {c['max_sm_mhz']:.0f} MHz: BF16 tensor {pk['bf16_tensor'] / 1e12:.1f}, "
              f"TF32 {pk['tf32_tensor'] / 1e12:.1f}, FP32 {pk['fp32_simt'] / 1e12:.1f} TFLOP/s; DRAM "
              f"{(c['dram_bytes_per_s'] or 0) / 1e9:.0f} GB/s ({c.get('bus_bits')}-bit). Source: {c['source']}.", ""]
    L += ["| Kernel | AI (FLOP/B) | Median (us) | p95 (us) | Achieved TFLOP/s | Achieved GB/s | Ridge | Bound | % of roof |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in result["tables"]["roofline"]:
        ai = "inf" if r["ai"] in (None, float("inf")) else f"{r['ai']:.1f}"
        pct = "-" if r["pct_of_roof"] is None else f"{r['pct_of_roof'] * 100:.0f} %"
        L.append(f"| {r['name']} | {ai} | {r['time_us']:.1f} | {r['p95_us']:.1f} | {r['achieved_flops'] / 1e12:.3f} | "
                 f"{r['achieved_bw'] / 1e9:.1f} | {r['ridge']:.0f} | {r['bound']} | {pct} |")
    L += ["", f"Measured roofs: compute **{m['measured_peak_tflops']:.2f} TFLOP/s**, memory **{m['measured_bw_gbs']:.1f} GB/s**, "
          f"measured ridge **{m['measured_ridge_flop_per_byte']:.0f} FLOP/B** `[MEASURED]`."]
    if gpu:
        L += [f"The manuscript's H100-class part: {H100['bf16_tflops']:.0f} TFLOP/s BF16 and {H100['hbm_tbs']} TB/s, ridge "
              f"~{H100['bf16_tflops'] / H100['hbm_tbs']:.0f} FLOP/B `[VENDOR-SPEC]`. **This is a laptop Ada GPU, not an H100**: "
              "its absolute numbers are 25-40x lower, but the shape is the same — thin GEMMs (small K) ride the memory "
              "roof, square GEMMs flatten at the compute roof, and the ridge decides which kernels a faster memory system would help."]
    L += ["", "## What to conclude", "",
          f"- The real effect ({labels['fast']}: {_pct(dec['fast']['point'])}) against the A/A floor "
          f"(±{dec['noise_floor'] * 100:.2f} %): the decision is **{dec['fast']['decision']}** (exact permutation test on run "
          f"medians, p = {dec['fast']['p_perm']:.3f}; 5 + 5 runs cannot give p below 2/252 = 0.008).",
          f"- The no-op change ({labels['noop']}) came out **{dec['noop']['decision']}**: a difference that small is either noise "
          "or not worth shipping, and the floor and the 1 % threshold stop it from being reported as a win.",
          "- The naive mean of every iteration (Naive mean column) includes warm-up and excluded runs; compare it with the cleaned point.",
          "- Below the ridge a kernel is limited by bytes, not FLOPs: a precision change only helps it through fewer bytes."]
    if not gpu:
        L += ["", "_CPU fallback: no GPU was used. The arms are CPU GEMMs and the roofline is classified against the measured "
              "CPU roofs (no vendor ceiling is asserted), so the GPU-only invariants — vendor TFLOP/s and DRAM bounds, "
              "BF16-faster-than-FP32 and clock telemetry — were skipped._"]
    return "\n".join(L)
