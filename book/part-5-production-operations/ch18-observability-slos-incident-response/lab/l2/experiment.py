"""Ch 18 L2: real GPU telemetry as a Prometheus text exposition, a step-time SLI and its burn rate.

What it teaches (Sections 18.2-18.6; Tasks 1-3 of the lab): the pipeline a real cluster runs. A
training-like loop runs four phases on the GPU: *healthy*; *degraded*, with an injected host-side stall
after every step, the kind of slowdown a slow dataloader causes; *recovered*; and *busy-idle*, a flood of
tiny kernels that does no useful work. Every second a scraper renders the
Prometheus text exposition of what the node exports: ``nvidia-smi`` gauges (the fields dcgm-exporter calls
``DCGM_FI_DEV_GPU_UTIL``, ``..._POWER_USAGE``, ``..._SM_CLOCK``, ``..._GPU_TEMP``, ``..._CLOCKS_EVENT_REASONS``)
and the job's own counters, including a step-time histogram with a bucket at the SLO threshold.

Everything downstream is computed **only from the scraped series**, as Prometheus would:
- the step-time SLI (good steps / all steps, good = step <= 1.1 x baseline), per scrape;
- the burn rate with the lab's ``burn_rate`` function (the reference solution, or the learner's starter),
  using windows of 10 and 2 scrapes in place of 1 h and 5 min (a time-compressed SRE-workbook page);
- detection latency of the regression and the replay of the lab's ``GPUUtilLow`` rule on real data.
  The util rule misses the busy-idle phase, where utilization stays high and useful TFLOP/s collapse. That
  is exercise K1, "the lying utilization metric", measured.

CPU fallback: the same four phases on the CPU. The exported gauges are host metrics (``/proc/stat`` busy,
the main thread's CPU-time rate as the "utilization" analogue), and the job counters are the same. The
exposition, SLI, burn rate and alert replay are identical; GPU-only invariants are skipped.
"""
from __future__ import annotations

import importlib.util
import math
import re
import shutil
import socket
import subprocess
import threading
import time
import warnings
from pathlib import Path

import hwlab

# cuBLAS binds the worker thread to the primary context on first use and says so; that is expected here.
warnings.filterwarnings("ignore", message="Attempting to run cuBLAS, but there was no current CUDA context")

EXPERIMENT = {
    "id": "ch18-l2",
    "title": "Lab 18 L2: Prometheus exposition of real telemetry, step-time SLI and burn rate",
    "evidence": "MEASURED",
    "cpu_fallback": ("same four-phase loop on the CPU; host gauges (/proc/stat, main-thread CPU-time rate) and the job's "
                     "step counters are exposed in Prometheus text format and the SLI/burn rate are computed from the scrapes"),
}

PKG = Path(__file__).resolve().parents[2]
LAB = PKG / "lab"
SLO_RATIO = 1.10            # good step: step_time <= 1.1 x baseline (the lab's training SLI definition)
SLO_TARGET = 0.99           # 99 % of steps good
LONG_W, SHORT_W, FAST_BURN = 10, 2, 14.4   # scrapes; stands in for (1 h, 5 min, 14.4) of the SRE workbook
SAMPLE_FIELDS = ["index", "utilization.gpu", "power.draw", "clocks.sm", "temperature.gpu", "clocks_event_reasons.active",
                 "memory.used"]
SPIN_CODE = ("template <typename T> T spin(T x, int n) { for (int i = 0; i < n; ++i) { x = x * T(0.999999) + T(1e-6); } "
             "return x; }")
NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
SAMPLE_RE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+(\S+)$")


# ----------------------------------------------------------------------------------------------- helpers
def _parse(v: str):
    v = v.strip()
    if not v or v.startswith("[") or v in ("N/A", "Not Supported"):
        return None
    if v.lower().startswith("0x"):
        return int(v, 16)
    try:
        return float(v)
    except ValueError:
        return v


class NvSampler:
    """Background ``nvidia-smi --query-gpu ... -lms`` reader for GPU 0; keeps the latest row."""

    def __init__(self, fields, interval_ms=250):
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
                row = dict(zip(self.fields, map(_parse, vals)))
                if row.get("index") in (0, 0.0, None):
                    row["t"] = time.perf_counter()
                    self.samples.append(row)

    def latest(self):
        return self.samples[-1] if self.samples else None

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        return False


def _proc_stat():
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


def stats(vals):
    vals = [v for v in vals if isinstance(v, (int, float)) and not math.isnan(v)]
    return {k: round(v, 4) for k, v in hwlab.summarize(vals).items()} if vals else None


# ----------------------------------------------------------------------------------------------- the job
class Job:
    """Training-like loop with Prometheus-style instrumentation (counters only ever increase)."""

    def __init__(self, ctx, buckets: list[float]):
        torch = ctx.torch
        self.ctx = ctx
        dev = "cuda" if ctx.is_gpu else "cpu"
        n = 4096 if ctx.is_gpu else 768
        dt = torch.float16 if ctx.is_gpu else torch.float32
        self.a, self.b = torch.randn(n, n, device=dev, dtype=dt), torch.randn(n, n, device=dev, dtype=dt)
        self.c = torch.empty(n, n, device=dev, dtype=dt)
        self.tiny = torch.zeros(1, device=dev)
        self.gemms = 4 if ctx.is_gpu else 2
        self.flop_per_step = self.gemms * 2.0 * n ** 3
        self.buckets = buckets
        self.lock = threading.Lock()
        self.steps = 0
        self.flop = 0.0
        self.step_sum = 0.0
        self.bucket_counts = [0] * len(buckets)
        self.busy_thread_s = 0.0   # CPU fallback: main-thread CPU time (the utilization analogue)
        self.phase = "warmup"
        self.stall_s = 0.0
        self.spin, self.spin_iters, self.busy_idle_kind = None, 0, "tiny-op flood"
        if ctx.is_gpu:
            try:   # one thread, one block, a long dependent FMA chain: a kernel is resident, 1 of SMs x 1536 threads works
                self.spin = torch.cuda.jiterator._create_jit_fn(SPIN_CODE, n=0)
                self.spin(self.tiny, n=1000)
                torch.cuda.synchronize()
                self.busy_idle_kind = "single-thread spin kernel"
            except Exception:  # noqa: BLE001 - NVRTC missing: fall back to a launch flood
                self.spin = None

    def calibrate_spin(self, target_s: float):
        """Pick the spin length so one busy-idle step lasts about one healthy step."""
        if self.spin is None:
            return
        t0 = time.perf_counter()
        self.spin(self.tiny, n=1_000_000)
        self.ctx.sync()
        per_iter = (time.perf_counter() - t0) / 1_000_000
        self.spin_iters = max(10_000, int(target_s / per_iter))

    def compute_step(self):
        for _ in range(self.gemms):
            self.ctx.torch.matmul(self.a, self.b, out=self.c)

    def busy_idle_step(self):
        """Keeps the device (or the thread) busy for about one healthy step with no useful FLOPs."""
        if self.spin is not None:
            self.tiny.copy_(self.spin(self.tiny, n=self.spin_iters))
            return
        for _ in range(400):
            self.tiny.add_(1.0)

    def step(self):
        t0, c0 = time.perf_counter(), time.thread_time()
        useful = 0.0
        if self.phase == "busy_idle":
            self.busy_idle_step()
        else:
            self.compute_step()
            useful = self.flop_per_step
        self.ctx.sync()
        if self.stall_s:
            time.sleep(self.stall_s)      # host-side stall after the step (a slow dataloader), injected on purpose
        dt = time.perf_counter() - t0
        with self.lock:
            self.steps += 1
            self.flop += useful
            self.step_sum += dt
            self.busy_thread_s += time.thread_time() - c0
            for i, le in enumerate(self.buckets):
                if dt <= le:
                    self.bucket_counts[i] += 1
        return dt


def exposition(job: Job, gpu_row: dict | None, host: dict, labels: str) -> str:
    """Prometheus text format 0.0.4 for one scrape."""
    out = []

    def fam(name, typ, help_, samples):
        out.append(f"# HELP {name} {help_}")
        out.append(f"# TYPE {name} {typ}")
        for lab, val in samples:
            out.append(f"{name}{{{lab}}} {val:.9g}" if lab else f"{name} {val:.9g}")

    if gpu_row is not None:
        g = gpu_row
        fam("nvsmi_gpu_utilization_percent", "gauge", "Percent of the sample period a kernel was running (DCGM_FI_DEV_GPU_UTIL).",
            [(labels, g.get("utilization.gpu") or 0)])
        fam("nvsmi_power_draw_watts", "gauge", "Board power draw (DCGM_FI_DEV_POWER_USAGE).", [(labels, g.get("power.draw") or 0)])
        fam("nvsmi_sm_clock_hertz", "gauge", "SM clock (DCGM_FI_DEV_SM_CLOCK, which is in MHz).",
            [(labels, (g.get("clocks.sm") or 0) * 1e6)])
        fam("nvsmi_temperature_celsius", "gauge", "GPU temperature (DCGM_FI_DEV_GPU_TEMP).", [(labels, g.get("temperature.gpu") or 0)])
        fam("nvsmi_clocks_event_reasons", "gauge", "Active clock-event-reason bitmask (DCGM_FI_DEV_CLOCKS_EVENT_REASONS).",
            [(labels, g.get("clocks_event_reasons.active") or 0)])
        fam("nvsmi_memory_used_bytes", "gauge", "Framebuffer memory used (DCGM_FI_DEV_FB_USED, which is in MiB).",
            [(labels, (g.get("memory.used") or 0) * 1024 ** 2)])
    fam("node_cpu_busy_ratio", "gauge", "Host CPU busy fraction since the previous scrape (/proc/stat).",
        [(f'host="{socket.gethostname()}"', host.get("cpu_busy", 0.0))])
    with job.lock:
        steps, flop, ssum, counts, busy = job.steps, job.flop, job.step_sum, list(job.bucket_counts), job.busy_thread_s
        phase = job.phase
    fam("lab_phase_info", "gauge", "Phase of the experiment (1 for the active phase).",
        [(f'job="l2",phase="{p}"', 1.0 if p == phase else 0.0) for p in ("warmup", "healthy", "degraded", "recovered", "busy_idle")])
    fam("train_steps_total", "counter", "Completed training steps.", [('job="l2"', steps)])
    fam("train_useful_flop_total", "counter", "FLOPs of useful (GEMM) work completed.", [('job="l2"', flop)])
    fam("train_main_thread_cpu_seconds_total", "counter", "CPU time of the training thread.", [('job="l2"', busy)])
    out.append("# HELP train_step_seconds Wall time of one training step.")
    out.append("# TYPE train_step_seconds histogram")
    for le, cnt in zip(job.buckets, counts):
        out.append(f'train_step_seconds_bucket{{job="l2",le="{le:.6g}"}} {cnt}')
    out.append(f'train_step_seconds_bucket{{job="l2",le="+Inf"}} {steps}')
    out.append(f'train_step_seconds_sum{{job="l2"}} {ssum:.9g}')
    out.append(f'train_step_seconds_count{{job="l2"}} {steps}')
    return "\n".join(out) + "\n"


def parse_exposition(text: str) -> tuple[dict, list[str]]:
    """Minimal text-format parser: {(name, labels): value} plus format errors."""
    types, series, errors = {}, {}, []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("# TYPE "):
            _, _, name, typ = line.split(" ", 3)
            types[name] = typ
            continue
        if line.startswith("#"):
            continue
        m = SAMPLE_RE.match(line)
        if not m:
            errors.append(f"unparseable sample line: {line!r}")
            continue
        name, labels, val = m.group(1), m.group(2) or "", m.group(3)
        base = re.sub(r"_(bucket|sum|count)$", "", name)
        if name not in types and base not in types:
            errors.append(f"sample {name} has no # TYPE")
        if types.get(name) == "counter" and not name.endswith("_total"):
            errors.append(f"counter {name} does not end in _total")
        try:
            series[(name, labels)] = float(val)
        except ValueError:
            errors.append(f"non-numeric value in {line!r}")
    return series, errors


def get(series: dict, name: str, contains: str = "") -> float | None:
    for (n, lab), v in series.items():
        if n == name and contains in lab:
            return v
    return None


# ----------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    phases = ([("healthy", 5), ("degraded", 5), ("recovered", 3), ("busy_idle", 3)] if ctx.quick else
              [("healthy", 15), ("degraded", 15), ("recovered", 10), ("busy_idle", 8)])
    notes = [
        "Scrape interval 1 s; nvidia-smi samples every 250 ms and the scrape exports the newest row (staleness recorded).",
        f"Burn-rate windows are {LONG_W} and {SHORT_W} scrapes in place of 1 h and 5 min; the threshold 14.4 is the SRE-workbook "
        "fast-burn page. The arithmetic is the lab's; only the time base is compressed.",
        "The degraded phase is an injected host-side sleep after each step (stall = 50 % of the baseline step), i.e. a "
        "real slowdown of a real loop, not a synthetic series.",
        "The baseline is calibrated after a fixed-time clock warm-up (3 s); without it a laptop GPU calibrates at idle "
        "clocks and the baseline comes out ~2x the healthy step.",
    ]
    # Calibrate the baseline step with the normal benchmark discipline, then put a histogram bucket at the SLO threshold.
    probe = Job(ctx, [1.0])
    # A count of warm-ups is not enough here: a laptop GPU needs seconds of load to leave its idle clocks,
    # and a baseline taken at idle clocks is ~2x the healthy step, which hides the injected stall below the
    # SLO bucket. Run the step for a fixed wall time first, then apply the usual warm-up + timed reps.
    warm_end = time.perf_counter() + (1.0 if ctx.quick else 3.0)
    while time.perf_counter() < warm_end:
        probe.compute_step()
        ctx.sync()
    base = ctx.bench(probe.compute_step, warmup=3, reps=ctx.reps(10))
    baseline = base["median"]
    buckets = sorted({round(baseline * f, 6) for f in (0.5, 0.8, 1.0, SLO_RATIO, 1.25, 1.5, 2.0, 4.0)})
    slo_le = round(baseline * SLO_RATIO, 6)
    job = Job(ctx, buckets)
    del probe
    job.calibrate_spin(baseline)
    ctx.log(f"baseline step {baseline * 1e3:.2f} ms (median of {base['n']}); SLO bucket le={slo_le * 1e3:.2f} ms")

    stop = threading.Event()

    def worker():
        if ctx.is_gpu:
            torch.cuda.set_device(0)   # bind the worker thread to the device's primary context
        while not stop.is_set():
            job.step()

    labels = 'gpu="0",Hostname="%s"' % socket.gethostname()
    scrapes = []
    sampler = NvSampler(SAMPLE_FIELDS, 250) if ctx.is_gpu else None
    if sampler:
        sampler.__enter__()
    try:
        th = threading.Thread(target=worker, daemon=True)
        job.phase = "warmup"
        th.start()
        time.sleep(1.0)
        prev_stat = _proc_stat()
        t_start = time.perf_counter()
        phase_start = {}
        next_scrape = t_start
        for name, secs in phases:
            job.phase = name
            job.stall_s = 0.5 * baseline if name == "degraded" else 0.0
            phase_start[name] = time.perf_counter() - t_start
            end = time.perf_counter() + secs
            while time.perf_counter() < end:
                next_scrape += 1.0
                time.sleep(max(0.0, next_scrape - time.perf_counter()))
                cur = _proc_stat()
                busy = (1 - (cur[0] - prev_stat[0]) / max(1, cur[1] - prev_stat[1])) if (cur and prev_stat) else 0.0
                prev_stat = cur
                row = sampler.latest() if sampler else None
                ts = time.perf_counter()
                text = exposition(job, row, {"cpu_busy": busy}, labels)
                scrapes.append({"t": ts - t_start, "phase": name, "text": text,
                                "staleness_s": (ts - row["t"]) if row else None})
        stop.set()
        th.join(timeout=10)
    finally:
        if sampler:
            sampler.__exit__(None, None, None)

    # ---------------- everything below uses only the scraped text
    parsed, fmt_errors = [], []
    for s in scrapes:
        ser, errs = parse_exposition(s["text"])
        fmt_errors += errs
        parsed.append(ser)
    rows, counter_regressions, hist_errors = [], 0, []
    for i in range(1, len(parsed)):
        a, b, dt = parsed[i - 1], parsed[i], scrapes[i]["t"] - scrapes[i - 1]["t"]
        for (n, lab), v in b.items():
            if (n.endswith("_total") or n.endswith("_count") or n.endswith("_bucket") or n.endswith("_sum")) and v < a.get((n, lab), 0):
                counter_regressions += 1
        cum = [get(b, "train_step_seconds_bucket", f'le="{le:.6g}"') for le in buckets] + \
              [get(b, "train_step_seconds_bucket", 'le="+Inf"')]
        if any(x > y for x, y in zip(cum, cum[1:])) or cum[-1] != get(b, "train_step_seconds_count"):
            hist_errors.append(f"scrape {i}: buckets not cumulative or +Inf != _count")
        d_count = get(b, "train_step_seconds_count") - get(a, "train_step_seconds_count")
        d_sum = get(b, "train_step_seconds_sum") - get(a, "train_step_seconds_sum")
        d_good = get(b, "train_step_seconds_bucket", f'le="{slo_le:.6g}"') - get(a, "train_step_seconds_bucket", f'le="{slo_le:.6g}"')
        d_flop = get(b, "train_useful_flop_total") - get(a, "train_useful_flop_total")
        d_busy = get(b, "train_main_thread_cpu_seconds_total") - get(a, "train_main_thread_cpu_seconds_total")
        rows.append({
            "scrape": i, "t_s": round(scrapes[i]["t"], 3), "dt_s": round(dt, 4), "phase": scrapes[i]["phase"],
            "steps": d_count, "good": d_good, "bad": d_count - d_good,
            "mean_step_ms": round(1e3 * d_sum / d_count, 3) if d_count else None,
            "useful_tflops": round(d_flop / dt / 1e12, 4),
            "util_pct": get(b, "nvsmi_gpu_utilization_percent") if ctx.is_gpu else round(100 * d_busy / dt, 1),
            "power_w": get(b, "nvsmi_power_draw_watts"), "sm_mhz": (get(b, "nvsmi_sm_clock_hertz") or 0) / 1e6 or None,
            "temp_c": get(b, "nvsmi_temperature_celsius"), "reasons_mask": get(b, "nvsmi_clocks_event_reasons"),
            "node_cpu_busy": round(get(b, "node_cpu_busy_ratio"), 3),
        })

    # SLI per phase (training job phases only) and burn rate with the lab's function
    import pandas as pd
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["t_s"], unit="s", utc=True)
    train = df[df.phase != "busy_idle"].copy()
    mod, model_path = load_lab_model("telemetry_analysis")
    burn_source = "embedded (lab model unavailable)"
    inference_like = train.rename(columns={"steps": "requests"})[["ts", "requests", "bad"]]
    burn_long = burn_short = None
    if mod:
        try:
            burn_long = mod.burn_rate(inference_like, "bad", SLO_TARGET, LONG_W)
            burn_short = mod.burn_rate(inference_like, "bad", SLO_TARGET, SHORT_W)
            burn_source = model_path
        except NotImplementedError as exc:
            notes.append(f"burn_rate is not implemented yet in {model_path} ({exc}); used the embedded formula. "
                         "Implement it in lab/starter/telemetry_analysis.py and rerun.")
    if burn_long is None:
        x = inference_like.set_index("ts")
        burn_long = (x.bad.rolling(LONG_W, min_periods=LONG_W).sum() / x.requests.rolling(LONG_W, min_periods=LONG_W).sum()) / (1 - SLO_TARGET)
        burn_short = (x.bad.rolling(SHORT_W, min_periods=SHORT_W).sum() / x.requests.rolling(SHORT_W, min_periods=SHORT_W).sum()) / (1 - SLO_TARGET)
    train["burn_long"] = burn_long.to_numpy()
    train["burn_short"] = burn_short.to_numpy()
    train["page"] = (train.burn_long > FAST_BURN) & (train.burn_short > FAST_BURN)
    deg_start = phase_start["degraded"]
    pages = train[train.page]
    first_page = float(pages.t_s.iloc[0]) if len(pages) else None
    # Onset from the scraped mean step time: first of 2 consecutive scrapes above 1.1 x baseline
    slow = (train.mean_step_ms > SLO_RATIO * baseline * 1e3).astype(int).to_numpy()
    onset = next((float(train.t_s.iloc[i]) for i in range(1, len(slow)) if slow[i] and slow[i - 1]), None)
    # Replay the lab's GPUUtilLow rule (util < 80 for 2 scrapes) on the real series
    util_low = (df.util_pct < 80).astype(int).to_numpy()
    util_fires = {p: bool(any(util_low[i] and util_low[i - 1] and df.phase.iloc[i] == p and df.phase.iloc[i - 1] == p
                              for i in range(1, len(df)))) for p in ("healthy", "degraded", "recovered", "busy_idle")}

    per_phase = []
    for p, _ in phases:
        d = df[df.phase == p]
        tot = d.steps.sum()
        per_phase.append({
            "phase": p, "scrapes": int(len(d)), "steps": int(tot),
            "sli_good_ratio": round(float(d.good.sum() / tot), 4) if tot else None,
            "mean_step_ms_median": round(float(d.mean_step_ms.median()), 3) if d.mean_step_ms.notna().any() else None,
            "useful_tflops_median": round(float(d.useful_tflops.median()), 4),
            "util_pct_median": round(float(d.util_pct.median()), 1) if d.util_pct.notna().any() else None,
            "power_w_median": round(float(d.power_w.median()), 1) if ctx.is_gpu and d.power_w.notna().any() else None,
            "sm_mhz_median": round(float(d.sm_mhz.median()), 0) if ctx.is_gpu and d.sm_mhz.notna().any() else None,
            "burn_long_max": round(float(train[train.phase == p].burn_long.max()), 2)
            if p != "busy_idle" and train[train.phase == p].burn_long.notna().any() else None,
            "util_low_alert_fires": util_fires[p],
        })
    tot = train.steps.sum()
    sli_total = float(train.good.sum() / tot) if tot else None
    intervals = [r["dt_s"] for r in rows]
    stale = [s["staleness_s"] for s in scrapes if s["staleness_s"] is not None]
    ph = {r["phase"]: r for r in per_phase}
    ctx.log("phase      steps  SLI    step ms  useful TFLOP/s  util %  power W")
    for r in per_phase:
        ctx.log(f"{r['phase']:10} {r['steps']:5}  {r['sli_good_ratio'] if r['sli_good_ratio'] is not None else '-':<6} "
                f"{r['mean_step_ms_median']}  {r['useful_tflops_median']}  {r['util_pct_median']}  {r['power_w_median']}")
    ctx.log(f"SLI over the training phases {sli_total:.3f}; first page at t={first_page}; onset {onset}; degraded start {deg_start:.1f}")
    metrics = {
        "baseline_step_ms": round(baseline * 1e3, 3), "slo_threshold_ms": round(slo_le * 1e3, 3),
        "scrapes": len(scrapes), "series_per_scrape": len(parsed[-1]) if parsed else 0,
        "exposition_bytes": len(scrapes[-1]["text"].encode()) if scrapes else 0,
        "format_errors": len(fmt_errors) + len(hist_errors), "counter_regressions": counter_regressions,
        "scrape_interval_p95_s": stats(intervals)["p95"] if intervals else None,
        "scrape_interval_median_s": stats(intervals)["median"] if intervals else None,
        "sample_staleness_p95_s": stats(stale)["p95"] if stale else None,
        "sli_training_phases": round(sli_total, 4) if sli_total is not None else None,
        "degraded_start_s": round(deg_start, 2), "onset_detected_s": onset, "first_page_s": first_page,
        "detection_delay_s": round(onset - deg_start, 2) if onset is not None else None,
        "page_delay_s": round(first_page - deg_start, 2) if first_page is not None else None,
        "burn_rate_model": burn_source, "busy_idle_kind": job.busy_idle_kind, "spin_iters": job.spin_iters,
    }
    return {"metrics": metrics,
            "tables": {"per_phase": per_phase, "scrapes": rows, "buckets_s": buckets,
                       "last_exposition": scrapes[-1]["text"] if scrapes else "",
                       "format_errors": (fmt_errors + hist_errors)[:20],
                       "burn": train[["scrape", "t_s", "phase", "burn_long", "burn_short", "page"]].round(3).to_dict("records")},
            "notes": notes}


# ----------------------------------------------------------------------------------------------- check
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    ph = {r["phase"]: r for r in t["per_phase"]}
    fails = []
    if m["format_errors"]:
        fails.append(f"{m['format_errors']} exposition format errors, e.g. {t['format_errors'][:2]}: check the text format "
                     "(# TYPE before samples, counters end in _total, cumulative buckets, +Inf == _count)")
    if m["counter_regressions"]:
        fails.append(f"{m['counter_regressions']} counter decreases between scrapes without a restart: counters must be monotonic")
    if m["scrape_interval_p95_s"] is None or m["scrape_interval_p95_s"] > 1.5:
        fails.append(f"scrape interval p95 {m['scrape_interval_p95_s']} s for a 1 s target: the scraper fell behind")
    if not (ph["healthy"]["sli_good_ratio"] or 0) >= 0.8:
        fails.append(f"healthy-phase SLI {ph['healthy']['sli_good_ratio']} < 0.8: the baseline is unstable (another GPU job?)")
    if not (ph["degraded"]["sli_good_ratio"] if ph["degraded"]["sli_good_ratio"] is not None else 1) <= 0.2:
        fails.append(f"degraded-phase SLI {ph['degraded']['sli_good_ratio']} > 0.2 although every step had a stall of 50 % "
                     "of the baseline: check the SLO bucket")
    if not (ph["degraded"]["mean_step_ms_median"] or 0) >= 1.3 * m["baseline_step_ms"]:
        fails.append("degraded mean step < 1.3 x baseline: the injected stall did not show up in the scraped histogram")
    if m["first_page_s"] is None:
        fails.append("the fast-burn page never fired during a sustained regression: check burn_rate and the windows")
    elif not m["degraded_start_s"] <= m["first_page_s"] <= m["degraded_start_s"] + LONG_W + 2:
        fails.append(f"page at {m['first_page_s']} s, degraded from {m['degraded_start_s']} s: it must follow the onset within "
                     f"the long window ({LONG_W} scrapes)")
    if m["detection_delay_s"] is None or not -0.5 <= m["detection_delay_s"] <= 3.5:
        fails.append(f"onset detected {m['detection_delay_s']} s after the injection: expected within 3 scrapes")
    if ph["busy_idle"]["useful_tflops_median"] > 0.05 * max(1e-12, ph["healthy"]["useful_tflops_median"]):
        fails.append("busy-idle phase reported useful FLOPs: the useful-work counter is wrong")
    if env["device"] == "cuda":
        if (ph["healthy"]["util_pct_median"] or 0) < 70:
            fails.append(f"GPU utilization {ph['healthy']['util_pct_median']} % during back-to-back GEMMs: check the sampler")
        if (ph["busy_idle"]["util_pct_median"] or 0) < 50:
            fails.append(f"busy-idle utilization {ph['busy_idle']['util_pct_median']} %: the tiny-kernel flood did not keep a "
                         "kernel resident; increase launches per step")
        if (ph["busy_idle"]["power_w_median"] or 0) >= (ph["healthy"]["power_w_median"] or 0):
            fails.append("busy-idle power >= GEMM power: power should track useful work even when utilization does not")
        if m["sample_staleness_p95_s"] is None or m["sample_staleness_p95_s"] > 1.0:
            fails.append(f"nvidia-smi sample staleness p95 {m['sample_staleness_p95_s']} s: check nvidia-smi -lms")
    return fails


# ----------------------------------------------------------------------------------------------- report
def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    util_name = "GPU util % (`nvsmi_gpu_utilization_percent`)" if gpu else "main-thread CPU-time rate %"
    L = ["## Per-phase SLI and telemetry (computed from the scraped exposition)", "",
         f"Baseline step **{m['baseline_step_ms']:.2f} ms** (median of ≥ 5 timed reps, after a 3 s clock warm-up and 3 warm-ups); SLO: step ≤ "
         f"{SLO_RATIO} x baseline = {m['slo_threshold_ms']:.2f} ms (a histogram bucket sits exactly there), target {SLO_TARGET}.", "",
         f"| Phase | Scrapes | Steps | SLI (good/all) | Mean step ms (median) | Useful TFLOP/s | {util_name} | Power W | SM MHz | Max burn ({LONG_W}-scrape) | `GPUUtilLow` fires |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in t["per_phase"]:
        L.append(f"| {r['phase']} | {r['scrapes']} | {r['steps']} | {r['sli_good_ratio']} | {r['mean_step_ms_median']} | "
                 f"{r['useful_tflops_median']} | {r['util_pct_median']} | {r['power_w_median'] or '-'} | {r['sm_mhz_median'] or '-'} | "
                 f"{r['burn_long_max'] if r['burn_long_max'] is not None else '-'} | {'yes' if r['util_low_alert_fires'] else 'no'} |")
    L += ["", "## Alerting from the scrapes", "",
          f"- SLI over the three training phases: **{m['sli_training_phases']}** against a {SLO_TARGET} target.",
          f"- Regression injected at t = {m['degraded_start_s']} s; detected from the scraped mean step time at t = "
          f"{m['onset_detected_s']} s (delay {m['detection_delay_s']} s); multi-window fast-burn page "
          f"(long {LONG_W} and short {SHORT_W} scrapes > {FAST_BURN}) first true at t = {m['first_page_s']} s "
          f"(delay {m['page_delay_s']} s). Burn rate from `{m['burn_rate_model']}`.",
          f"- Scrape interval median {m['scrape_interval_median_s']} s, p95 {m['scrape_interval_p95_s']} s; "
          + (f"nvidia-smi sample age at scrape p95 {m['sample_staleness_p95_s']} s; " if gpu else "")
          + f"{m['series_per_scrape']} series and {m['exposition_bytes']} bytes per scrape; {m['format_errors']} format errors, "
          f"{m['counter_regressions']} counter decreases.",
          "", "## Exposition (last scrape, excerpt)", "", "```text"]
    lines = t["last_exposition"].splitlines()
    L += lines[:60] + (["..."] if len(lines) > 60 else []) + ["```", "", "## What to conclude", ""]
    bi, he = (next(r for r in t["per_phase"] if r["phase"] == p) for p in ("busy_idle", "healthy"))
    if gpu:
        L += [f"- **Utilization is not efficiency.** In the busy-idle phase GPU utilization stayed at {bi['util_pct_median']} % "
              f"(the `GPUUtilLow` rule did {'not ' if not bi['util_low_alert_fires'] else ''}fire) while useful work fell from "
              f"{he['useful_tflops_median']} to {bi['useful_tflops_median']} TFLOP/s and power fell from {he['power_w_median']} to "
              f"{bi['power_w_median']} W. `utilization.gpu` only says that *a* kernel was resident. DCGM's `PROF_SM_ACTIVE` "
              "(not available on this GeForce laptop) or a job-level goodput SLI is what catches it.",
              "- **The symptom-based SLI catches the injected stall within a scrape or two**, and the multi-window burn rate pages "
              "inside the long window, which is the lab's Task 3 design measured on a real loop.",
              "- This is a **laptop Ada GPU** behind WSL2 with `nvidia-smi` as the exporter, not an H100 node with dcgm-exporter: "
              "metric names here are `nvsmi_*`, and the DCGM field each one stands for is in its `# HELP`. Absolute numbers do not "
              "transfer; the alert logic does."]
    else:
        L += ["- _CPU fallback: no GPU was visible. The exposition carries host gauges and the job's counters; the SLI, burn rate "
              "and alert replay are computed exactly as on a GPU. GPU-only invariants (utilization, power, sample staleness) were "
              "skipped. The \"utilization\" column is the training thread's CPU-time rate, which stays high in the busy-idle phase "
              "while useful GFLOP/s collapse: the same lesson as `utilization.gpu`._"]
    return "\n".join(L)
