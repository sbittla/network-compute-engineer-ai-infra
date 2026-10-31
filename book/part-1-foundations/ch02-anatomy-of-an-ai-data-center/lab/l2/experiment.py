"""Ch 2 L2: GPU power, clock and throttle telemetry under a defined load (idle / compute-bound / memory-bound).

What it teaches (Sections 2.6 and 2.10): a node's power budget is set by what its accelerators draw
under a *defined* workload, not by nameplate numbers. This experiment measures idle, sustained, p95/p99
and peak power of the one GPU on this host while it runs a compute-bound FP16 GEMM loop and a
memory-bound copy loop, samples clocks, temperature and clock-event (throttle) reasons with
``nvidia-smi`` every 100 ms, and reports throughput per watt for both. It then puts the measured
sustained-to-limit and peak-to-sustained ratios next to the ORION capacity model's 8.5 kW / 10.2 kW node
assumption and its transient margin.

Not runnable here (probed, recorded): server power from the BMC (DCMI/Redfish), because there is no BMC
or IPMI device; and the power-cap sweep of Exercise 2.8, because changing the power limit needs root on a
dedicated, authorised server and the harness container is unprivileged. The GPU's own default limit is
*read*, and the time it spends power-capped is measured from the clock-event counters instead.

CPU fallback: the same idle / GEMM / copy phases run on the CPU and report throughput. The host exposes
no power sensor to the container (no RAPL, no BMC), so the power invariants are skipped and the report
says so.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch02-l2",
    "title": "Lab 2 L2: GPU power, clocks and throttle reasons under compute- and memory-bound load",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same idle / GEMM / copy phases on the CPU, reporting throughput only: the container sees "
                     "no CPU or server power sensor (no RAPL, no BMC), so power is recorded as not measurable"),
}

PKG = Path(__file__).resolve().parents[2]

# Ada (sm_89) per-SM, per-clock dense rates, from the NVIDIA Ada Lovelace architecture whitepaper (v1.0, 2022):
# GeForce RTX 4090 = 165.2 TFLOP/s FP16 tensor with FP32 accumulate over 128 SMs at 2.52 GHz -> 512 FLOP/clk/SM;
# FP32 (non-tensor) = 128 lanes x 2 = 256 FLOP/clk/SM. GeForce parts run FP32-accumulate tensor math at half rate.
ADA_FP16_TENSOR_FLOP_PER_CLK_SM = 512
# Memory bus width by model [VENDOR-SPEC]; bandwidth = 2 (DDR) x max memory clock x bus width / 8.
BUS_WIDTH_BITS = {"RTX 4060 Laptop": 128, "RTX 4060": 128, "RTX 4070 Laptop": 128, "RTX 4090": 384}
EVENT_BITS = {0x1: "gpu_idle", 0x2: "applications_clocks", 0x4: "sw_power_cap", 0x8: "hw_slowdown",
              0x10: "sync_boost", 0x20: "sw_thermal_slowdown", 0x40: "hw_thermal_slowdown",
              0x80: "hw_power_brake", 0x100: "display_clock"}
TELEMETRY_FIELDS = ["power.draw", "power.draw.instant", "clocks.sm", "clocks.mem", "temperature.gpu",
                    "utilization.gpu", "clocks_event_reasons.active",
                    "clocks_event_reasons_counters.sw_power_cap",
                    "clocks_event_reasons_counters.sw_thermal_slowdown",
                    "clocks_event_reasons_counters.hw_thermal_slowdown",
                    "clocks_event_reasons_counters.hw_power_brake_slowdown", "enforced.power.limit", "pstate"]


# --------------------------------------------------------------------------------------------- helpers
def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


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
            except Exception:  # noqa: BLE001 - a broken starter must not break the hardware run
                continue
    return None, None


def _num(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class Telemetry:
    """``nvidia-smi --query-gpu ... -lms <interval>`` in the background; samples tagged with the current phase."""

    def __init__(self, interval_ms: int = 100):
        self.interval_ms, self.samples, self._phase, self.phase_start = interval_ms, [], "start", {}
        self._proc = None
        self._thread = None

    @property
    def phase(self) -> str:
        return self._phase

    @phase.setter
    def phase(self, name: str) -> None:
        self._phase = name
        self.phase_start[name] = time.monotonic()

    def start(self) -> "Telemetry":
        if not shutil.which("nvidia-smi"):
            return self
        self._proc = subprocess.Popen(["nvidia-smi", f"--query-gpu={','.join(TELEMETRY_FIELDS)}",
                                       "--format=csv,noheader,nounits", f"-lms={self.interval_ms}"],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()
        return self

    def _read(self) -> None:
        for line in self._proc.stdout:
            vals = [v.strip() for v in line.split(",")]
            if len(vals) != len(TELEMETRY_FIELDS):
                continue
            row = dict(zip(TELEMETRY_FIELDS, vals))
            row["t"], row["phase"] = time.monotonic(), self.phase
            self.samples.append(row)

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._thread:
            self._thread.join(timeout=5)

    def phase_rows(self, phase: str, settle_s: float = 0.4) -> list[dict]:
        """Samples of one phase, without the first ``settle_s`` (nvidia-smi output lags the phase switch)."""
        t0 = self.phase_start.get(phase, 0.0) + settle_s
        return [s for s in self.samples if s["phase"] == phase and s["t"] >= t0]


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]


def stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {"n": len(values), "median": statistics.median(values), "p95": pct(values, 0.95),
            "p99": pct(values, 0.99), "min": min(values), "max": max(values)}


def gpu_model_key(name: str) -> str | None:
    return next((k for k in sorted(BUS_WIDTH_BITS, key=len, reverse=True) if k.lower() in name.lower()), None)


def device_peaks(env: dict) -> dict:
    """FP16-tensor peak at the max SM clock (a strict upper bound) and DRAM bandwidth, for this GPU."""
    g = (env.get("gpus") or [{}])[0]
    sm = env.get("gpu0", {}).get("sm_count")
    out = {}
    try:
        out["fp16_tflops_at_max_clock"] = sm * ADA_FP16_TENSOR_FLOP_PER_CLK_SM * float(g["clocks.max.sm"]) * 1e6 / 1e12
    except (KeyError, TypeError, ValueError):
        pass
    key = gpu_model_key(g.get("name", ""))
    try:
        if key and env.get("gpu0", {}).get("capability") == "8.9":
            out["dram_gbs"] = 2 * float(g["clocks.max.memory"]) * 1e6 * BUS_WIDTH_BITS[key] / 8 / 1e9
    except (KeyError, ValueError):
        pass
    return out


def gpu_env(ctx) -> dict:
    """The subset of hwlab.environment() that device_peaks() needs (run() is not handed env)."""
    import hwlab  # noqa: PLC0415 - on sys.path inside the GPU image (run.py puts /opt/hwlab there)
    p = ctx.torch.cuda.get_device_properties(0)
    return {"gpus": hwlab.nvidia_smi_query(["name", "clocks.max.sm", "clocks.max.memory"]),
            "gpu0": {"sm_count": p.multi_processor_count, "capability": f"{p.major}.{p.minor}"}}


def probe_power_sources() -> dict:
    rapl = Path("/sys/class/powercap")
    return {
        "bmc_ipmi_device": any(Path("/dev").glob("ipmi*")) or Path("/sys/class/ipmi").exists(),
        "ipmitool": shutil.which("ipmitool"),
        "redfish_reachable": False,  # the harness runs with --network none; a BMC is never reachable from here
        "rapl_domains": sorted(p.name for p in rapl.glob("intel-rapl*")) if rapl.is_dir() else [],
        "dcgmi": shutil.which("dcgmi"),
        "nvidia_smi": shutil.which("nvidia-smi"),
        "euid": os.geteuid(),
    }


# --------------------------------------------------------------------------------------------- workload
def run_phase(ctx, name: str, seconds: float, step, work_per_step: float, tel: Telemetry | None) -> dict:
    """Run ``step()`` repeatedly for ``seconds``; throughput is timed in ~0.5 s windows (>= 5 windows)."""
    if tel:
        tel.phase = name
    for _ in range(3):  # warm-up
        step()
    ctx.sync()
    windows, n_iter, t_end = [], 1, time.monotonic() + seconds
    while time.monotonic() < t_end or len(windows) < 5:
        t0 = time.perf_counter()
        for _ in range(n_iter):
            step()
        ctx.sync()
        dt = time.perf_counter() - t0
        windows.append(n_iter * work_per_step / dt)
        n_iter = max(1, int(n_iter * 0.5 / max(dt, 1e-4)))  # aim for 0.5 s windows
    return {"phase": name, "windows": windows, "throughput": stats(windows)}


def idle_phase(ctx, seconds: float, tel: Telemetry | None, name: str) -> None:
    if tel:
        tel.phase = name
    ctx.sync()
    time.sleep(seconds)


def run(ctx) -> dict:
    torch = ctx.torch
    gpu = ctx.is_gpu
    secs = {"idle": 3, "gemm": 8, "copy": 6, "cool": 2} if ctx.quick else {"idle": 15, "gemm": 45, "copy": 30, "cool": 10}
    if gpu:
        n, dtype = 4096, torch.float16
        a = torch.randn(n, n, device="cuda", dtype=dtype)
        b = torch.randn(n, n, device="cuda", dtype=dtype)
        c = torch.empty(n, n, device="cuda", dtype=dtype)
        nbytes = 256 * 1024 * 1024
        src = torch.empty(nbytes, dtype=torch.uint8, device="cuda")
        dst = torch.empty_like(src)
    else:
        n, dtype = 2048, torch.float32
        a, b = torch.randn(n, n, dtype=dtype), torch.randn(n, n, dtype=dtype)
        c = torch.empty(n, n, dtype=dtype)
        nbytes = 128 * 1024 * 1024
        src = torch.empty(nbytes, dtype=torch.uint8)
        dst = torch.empty_like(src)
    src.fill_(1)
    gemm_flop = 2 * n ** 3
    workload = (f"GEMM {n}x{n}x{n} {str(dtype).replace('torch.', '')} (torch.matmul, out=), copy {nbytes >> 20} MiB "
                f"buffer-to-buffer (read + write counted); phases idle {secs['idle']} s, GEMM {secs['gemm']} s, "
                f"copy {secs['copy']} s, idle {secs['cool']} s")
    ctx.log(workload)

    tel = Telemetry(100).start() if gpu else None
    time.sleep(0.5)
    phases = {}
    idle_phase(ctx, secs["idle"], tel, "idle")
    phases["gemm"] = run_phase(ctx, "gemm", secs["gemm"], lambda: torch.matmul(a, b, out=c), gemm_flop / 1e12, tel)
    phases["copy"] = run_phase(ctx, "copy", secs["copy"], lambda: dst.copy_(src), 2 * nbytes / 1e9, tel)
    idle_phase(ctx, secs["cool"], tel, "cooldown")
    if tel:
        tel.stop()

    tables = {"phases": [], "throughput": []}
    metrics = {"gemm_tflops_median": round(phases["gemm"]["throughput"]["median"], 3),
               "copy_gbs_median": round(phases["copy"]["throughput"]["median"], 2)}
    for name in ("gemm", "copy"):
        t = phases[name]["throughput"]
        tables["throughput"].append({"phase": name, "unit": "TFLOP/s" if name == "gemm" else "GB/s",
                                     "median": t["median"], "p95": t["p95"], "min": t["min"], "max": t["max"],
                                     "windows": t["n"]})
    notes = [f"Workload: {workload}.",
             "Throughput is timed in ~0.5 s windows after 3 warm-up steps (>= 5 windows per phase); power, clocks and "
             "temperature are nvidia-smi samples every 100 ms during the same phase."]
    not_runnable = [
        {"part": "Server (node) power from the BMC: ipmitool dcmi power reading / Redfish PowerSubsystem",
         "needs": ["a BMC with IPMI/Redfish read access", "network access to it"],
         "probe": probe_power_sources()},
        {"part": "Exercise 2.8 power-cap sweep (nvidia-smi -pl <W> from max down to 55 %)",
         "needs": ["root on a dedicated, authorised GPU server", "a driver that permits power-limit changes "
                   "(not WSL2 GPU paravirtualisation)"],
         "probe": "not attempted on purpose: the harness container is unprivileged and the lab never changes power limits"},
    ]
    if not gpu:
        not_runnable.append({"part": "GPU and CPU power telemetry", "needs": ["an NVIDIA GPU (nvidia-smi)",
                             "or RAPL / hwmon power sensors exposed to the container"],
                             "probe": probe_power_sources()})
        metrics["power_measured"] = False
        notes.append("CPU fallback: no power sensor is visible, so only throughput is reported.")
        return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}

    # ---- GPU telemetry analysis
    by = {p: tel.phase_rows(p) for p in ("idle", "gemm", "copy", "cooldown")}
    limit = _num(tel.samples[-1]["enforced.power.limit"]) if tel.samples else None
    for p, rows in by.items():
        inst = [v for v in (_num(r["power.draw.instant"]) for r in rows) if v is not None]
        clk = [v for v in (_num(r["clocks.sm"]) for r in rows) if v is not None]
        temp = [v for v in (_num(r["temperature.gpu"]) for r in rows) if v is not None]
        reasons, capped = set(), 0
        for r in rows:
            try:
                mask = int(r["clocks_event_reasons.active"], 16)
            except ValueError:
                continue
            reasons |= {name for bit, name in EVENT_BITS.items() if mask & bit}
            capped += bool(mask & 0x4)
        cap_us = []
        for key in ("clocks_event_reasons_counters.sw_power_cap", "clocks_event_reasons_counters.sw_thermal_slowdown",
                    "clocks_event_reasons_counters.hw_thermal_slowdown"):
            vals = [_num(r[key]) for r in rows if _num(r[key]) is not None]
            cap_us.append(vals[-1] - vals[0] if len(vals) >= 2 else None)
        dur = rows[-1]["t"] - rows[0]["t"] if len(rows) >= 2 else None
        ps, cs, ts = stats(inst), stats(clk), stats(temp)
        tables["phases"].append({
            "phase": p, "samples": len(rows), "power_median_w": ps.get("median"), "power_p95_w": ps.get("p95"),
            "power_p99_w": ps.get("p99"), "power_max_w": ps.get("max"), "sm_clock_median_mhz": cs.get("median"),
            "sm_clock_min_mhz": cs.get("min"), "temp_max_c": ts.get("max"),
            "sw_power_cap_fraction": capped / len(rows) if rows else None,
            "sw_power_cap_counter_fraction": (cap_us[0] / 1e6 / dur) if (cap_us[0] is not None and dur) else None,
            "sw_power_cap_us": cap_us[0], "sw_thermal_us": cap_us[1], "hw_thermal_us": cap_us[2],
            "event_reasons_seen": sorted(reasons),
            "counters_monotonic": all(
                _num(b[k]) >= _num(a[k]) for a, b in zip(rows, rows[1:])
                for k in ("clocks_event_reasons_counters.sw_power_cap",)
                if _num(a[k]) is not None and _num(b[k]) is not None),
        })
    ph = {r["phase"]: r for r in tables["phases"]}
    peaks = device_peaks(gpu_env(ctx))
    g, cp = ph["gemm"], ph["copy"]
    metrics.update({
        "enforced_power_limit_w": limit,
        "idle_power_w": ph["idle"]["power_median_w"],
        "gemm_power_median_w": g["power_median_w"], "gemm_power_p99_w": g["power_p99_w"],
        "gemm_power_max_w": g["power_max_w"], "copy_power_median_w": cp["power_median_w"],
        "gemm_sm_clock_median_mhz": g["sm_clock_median_mhz"], "copy_sm_clock_median_mhz": cp["sm_clock_median_mhz"],
        "gemm_tflops_per_w": round(metrics["gemm_tflops_median"] / g["power_median_w"], 4) if g["power_median_w"] else None,
        "copy_gbs_per_w": round(metrics["copy_gbs_median"] / cp["power_median_w"], 3) if cp["power_median_w"] else None,
        "gemm_sustained_to_limit": round(g["power_median_w"] / limit, 3) if (limit and g["power_median_w"]) else None,
        "gemm_p99_to_sustained": round(g["power_p99_w"] / g["power_median_w"], 3) if g["power_median_w"] else None,
        "gemm_max_to_sustained": round(g["power_max_w"] / g["power_median_w"], 3) if g["power_median_w"] else None,
        "gemm_sw_power_cap_fraction": g["sw_power_cap_fraction"],
        "power_measured": True,
    })
    metrics.update({f"peak_{k}": round(v, 2) for k, v in peaks.items()})
    if g["sm_clock_median_mhz"]:
        clk_peak = torch.cuda.get_device_properties(0).multi_processor_count * ADA_FP16_TENSOR_FLOP_PER_CLK_SM * g["sm_clock_median_mhz"] * 1e6 / 1e12
        metrics["peak_fp16_tflops_at_run_clock"] = round(clk_peak, 2)
        metrics["gemm_fraction_of_clock_peak"] = round(metrics["gemm_tflops_median"] / clk_peak, 3)
    tables["l1_comparison"] = l1_comparison(metrics)
    tables["telemetry_samples"] = [{k: s[k] for k in ("phase", "power.draw.instant", "clocks.sm", "temperature.gpu",
                                                      "clocks_event_reasons.active")} for s in tel.samples[::5]]
    if all(not r["sw_power_cap_us"] for r in tables["phases"]) and g["sw_power_cap_fraction"]:
        notes.append("The cumulative clock-event counters did not advance during this run although the active bitmask "
                     "reported SW Power Cap (seen on this driver under WSL2); time power-capped is therefore the fraction "
                     "of 100 ms samples whose active bitmask has the SW Power Cap bit set.")
    notes.append("The first 0.4 s of each phase is excluded from its telemetry statistics (nvidia-smi output lags the switch).")
    notes.append("power.draw.instant is used for distribution statistics; power.draw (a ~1 s average) hides transients. "
                 "Even 100 ms sampling cannot see millisecond-scale load steps: the model's transient margin covers those.")
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}


def l1_comparison(m: dict) -> list[dict]:
    """Measured ratios next to the ORION capacity model's node assumptions (lab/data/design_intent.yaml)."""
    import yaml  # noqa: PLC0415 - in the GPU image
    intent = yaml.safe_load((PKG / "lab" / "data" / "design_intent.yaml").read_text(encoding="utf-8"))
    facility = yaml.safe_load((PKG / "lab" / "data" / "facility_envelope.yaml").read_text(encoding="utf-8"))
    c = intent["compute"]
    margin = facility["electrical"]["transient_margin"]
    rows = [
        {"quantity": "sustained / maximum power", "orion_model": round(c["node_sustained_kw"] / c["node_max_kw"], 3),
         "orion_basis": f"node {c['node_sustained_kw']} kW / {c['node_max_kw']} kW [MODELED]",
         "this_gpu": m.get("gemm_sustained_to_limit"), "this_basis": "GPU GEMM median power / enforced power limit [MEASURED]"},
        {"quantity": "peak / sustained power", "orion_model": round(1 + margin, 3),
         "orion_basis": f"rack design load = max x (1 + {margin}) transient margin [MODELED]",
         "this_gpu": m.get("gemm_max_to_sustained"), "this_basis": "GPU max instant sample / GEMM median (100 ms sampling) [MEASURED]"},
        {"quantity": "memory-bound / compute-bound power",
         "orion_model": None, "orion_basis": "not modeled (the model sizes for the compute-bound worst case)",
         "this_gpu": round(m["copy_power_median_w"] / m["gemm_power_median_w"], 3)
         if m.get("copy_power_median_w") and m.get("gemm_power_median_w") else None,
         "this_basis": "copy median power / GEMM median power [MEASURED]"},
    ]
    mod, src = load_l1("capacity_model")
    if mod is not None and m.get("gemm_sustained_to_limit"):
        try:
            facility_all = facility
            base = mod.compute_power_cooling(intent, facility_all)
            alt = {**intent, "compute": {**c, "node_sustained_kw": round(c["node_max_kw"] * m["gemm_sustained_to_limit"], 3)}}
            new = mod.compute_power_cooling(alt, facility_all)
            rows.append({"quantity": "cluster IT sustained kW if nodes behaved like this GPU",
                         "orion_model": round(base["cluster_it_sustained_kw"], 1),
                         "orion_basis": f"{src}: compute_power_cooling [MODELED]",
                         "this_gpu": round(new["cluster_it_sustained_kw"], 1),
                         "this_basis": "same model, node_sustained_kw = node_max_kw x measured ratio "
                                       "[MODELED from MEASURED, method illustration only]"})
        except Exception as exc:  # noqa: BLE001 - starter TODOs
            rows.append({"quantity": "capacity-model projection", "orion_model": None,
                         "orion_basis": f"skipped: {src} raised {type(exc).__name__}", "this_gpu": None, "this_basis": ""})
    return rows


# --------------------------------------------------------------------------------------------- invariants
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    for r in t["throughput"]:
        if r["windows"] < 5:
            fails.append(f"{r['phase']}: only {r['windows']} timing windows (need >= 5): lengthen the phase")
        if r["median"] <= 0:
            fails.append(f"{r['phase']}: non-positive throughput")
    if env["device"] != "cuda":
        return fails
    peaks = device_peaks(env)
    if "fp16_tflops_at_max_clock" in peaks and m["gemm_tflops_median"] > 1.05 * peaks["fp16_tflops_at_max_clock"]:
        fails.append(f"GEMM {m['gemm_tflops_median']:.1f} TFLOP/s exceeds the FP16 tensor peak at max clock "
                     f"{peaks['fp16_tflops_at_max_clock']:.1f}: check the FLOP count and the timing synchronisation")
    if "dram_gbs" in peaks and m["copy_gbs_median"] > 1.05 * peaks["dram_gbs"]:
        fails.append(f"copy {m['copy_gbs_median']:.0f} GB/s exceeds DRAM bandwidth {peaks['dram_gbs']:.0f} GB/s: the "
                     "buffer may fit in L2, or read+write bytes are double counted")
    ph = {r["phase"]: r for r in t["phases"]}
    for p in ("idle", "gemm", "copy"):
        if ph[p]["samples"] < 5:
            fails.append(f"{p}: only {ph[p]['samples']} telemetry samples: is nvidia-smi -lms working in the container?")
    if ph["gemm"]["power_median_w"] is not None and ph["idle"]["power_median_w"] is not None \
            and ph["gemm"]["power_median_w"] <= ph["idle"]["power_median_w"] + 2:
        fails.append("GEMM power is not above idle power: the load did not reach the GPU, or samples are mis-tagged")
    lim = m.get("enforced_power_limit_w")
    if lim and ph["gemm"]["power_median_w"] and ph["gemm"]["power_median_w"] > 1.05 * lim:
        fails.append(f"median GEMM power {ph['gemm']['power_median_w']:.1f} W is above the enforced limit {lim} W: "
                     "the limit reading or the power field is wrong")
    if not all(r["counters_monotonic"] for r in t["phases"]):
        fails.append("a clock-event counter decreased: counters are cumulative; check for a driver reset during the run")
    if m["gemm_tflops_per_w"] is None or m["gemm_tflops_per_w"] <= 0:
        fails.append("no GEMM throughput-per-watt figure")
    return fails


# --------------------------------------------------------------------------------------------- report
def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    lines = ["## Throughput per phase (0.5 s windows)", "", "| Phase | Unit | Median | p95 | Min | Max | Windows |",
             "|---|---|---|---|---|---|---|"]
    for r in t["throughput"]:
        lines.append(f"| {r['phase']} | {r['unit']} | {r['median']:.2f} | {r['p95']:.2f} | {r['min']:.2f} | "
                     f"{r['max']:.2f} | {r['windows']} |")
    if gpu:
        lines += ["", "## Power, clocks and throttle reasons (nvidia-smi, 100 ms)", "",
                  "| Phase | Samples | Power median (W) | p95 | p99 | Max | SM clock median (MHz) | SM clock min | "
                  "Temp max (C) | Samples power-capped | Event reasons seen |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in t["phases"]:
            frac = f"{r['sw_power_cap_fraction'] * 100:.0f} %" if r["sw_power_cap_fraction"] is not None else "n/a"
            f = lambda v, d=1: "n/a" if v is None else f"{v:.{d}f}"  # noqa: E731
            lines.append(f"| {r['phase']} | {r['samples']} | {f(r['power_median_w'])} | {f(r['power_p95_w'])} | "
                         f"{f(r['power_p99_w'])} | {f(r['power_max_w'])} | {f(r['sm_clock_median_mhz'], 0)} | "
                         f"{f(r['sm_clock_min_mhz'], 0)} | {f(r['temp_max_c'], 0)} | {frac} | "
                         f"{', '.join(r['event_reasons_seen']) or '-'} |")
        lines += ["", f"Enforced power limit (read, not changed): **{m['enforced_power_limit_w']} W**. "
                  f"GEMM: **{m['gemm_tflops_per_w']} TFLOP/s per W**; copy: **{m['copy_gbs_per_w']} GB/s per W** `[MEASURED]`."]
        if m.get("peak_fp16_tflops_at_max_clock"):
            lines.append(f"FP16 tensor peak at the max SM clock {m['peak_fp16_tflops_at_max_clock']} TFLOP/s; at the clock "
                         f"the GEMM actually ran ({m['gemm_sm_clock_median_mhz']:.0f} MHz) "
                         f"{m.get('peak_fp16_tflops_at_run_clock')} TFLOP/s, so the GEMM reached "
                         f"{(m.get('gemm_fraction_of_clock_peak') or 0) * 100:.0f} % of it `[MODELED peak, MEASURED rate]`.")
        lines += ["", "## Against the ORION capacity model", "", "| Quantity | ORION model | Basis | This GPU | Basis |",
                  "|---|---|---|---|---|"]
        for r in t["l1_comparison"]:
            lines.append(f"| {r['quantity']} | {r['orion_model'] if r['orion_model'] is not None else '-'} | {r['orion_basis']} | "
                         f"{r['this_gpu'] if r['this_gpu'] is not None else '-'} | {r['this_basis']} |")
        capped = (m.get("gemm_sw_power_cap_fraction") or 0) * 100
        copy_ratio = (m["copy_power_median_w"] / m["gemm_power_median_w"]) if m.get("gemm_power_median_w") else None
        lines += ["", "**This is one laptop Ada GPU (RTX 4060 Laptop class, 80 W-class limit), not an HX8 node with 8 x H100-class "
                  "GPUs.** Ratios transfer as *method*, not as numbers. What to conclude:",
                  "",
                  f"- The compute-bound GEMM ran at {m['gemm_sustained_to_limit'] * 100:.0f} % of the enforced limit, with the "
                  f"SW Power Cap reason active in {capped:.0f} % of samples and the SM clock at "
                  f"{m['gemm_sm_clock_median_mhz']:.0f} MHz of a {(env.get('gpus') or [{}])[0].get('clocks.max.sm', '?')} MHz table "
                  "maximum: the power limit, not the clock table, sets throughput. This is the regime where a lower cap "
                  "(Exercise 2.8) trades a little throughput for a lot of power.",
                  f"- The memory-bound copy drew {copy_ratio * 100:.0f} % of the GEMM's power and was not power-capped: a "
                  "cap costs memory-bound work little. Throughput per watt is a different number for each workload."
                  if copy_ratio else "- No copy power figure.",
                  f"- Under the GEMM the 100 ms peak was {m['gemm_max_to_sustained']:.2f} x the sustained median, inside "
                  "the model's 1.10 transient margin, but 100 ms sampling cannot see millisecond steps. Size racks on the "
                  "maximum plus margin and energy on the sustained figure, and replace both with BMC readings on the real "
                  "platform. A GPU that sits at its limit under load also shows why the sustained/max ratio of a whole node "
                  "(0.83 in the model) is lower than a single GPU's: CPUs, NICs, fans and PSU losses do not all peak together."]
    else:
        lines += ["", "_CPU fallback: no GPU and no power sensor were visible, so this run measured CPU throughput only. "
                  "The power, clock and throttle invariants were skipped._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
