"""Ch 16 L2: single-GPU acceptance and burn-in, evaluated with the lab's acceptance evaluator.

What it teaches (Sections 16.5 and 16.11, Table 16.4): acceptance is evidence collected from the node
itself and judged by a versioned policy, never a feeling that "the node looks fine". The run collects the
GPU part of an ``acceptance_results.json`` record from real hardware:

1. inventory read from ``nvidia-smi`` (UUID, BDF, VBIOS, driver, memory, PCIe link at idle and under load,
   row-remapper state, ECC mode);
2. a device-memory write/verify pattern test (a small, honest cousin of a DCGM memory diagnostic);
3. a GEMM throughput check against the device's tensor-core ceiling;
4. a sustained GEMM burn-in sampled every 250 ms for temperature, power, SM clock, PCIe link and the
   clock-event-reason bitmask, plus the driver's clock-event-reason counters before and after.

The record goes through the lab's own ``evaluate_node`` (the reference solution when present, otherwise
the learner's starter) with the lab policy ``acc-2026.10``. Only the ``expected`` block is adapted to this
GPU's SKU, and the report says so. Checks that need hardware this host lacks (NVLink, ECC, DCGM, RDMA NICs,
NVMe, multi-GPU NCCL, kernel Xid log, BMC) are probed and listed as not runnable. They are never faked.

CPU fallback: the same pattern test on host RAM and a CPU GEMM burn-in with ``/proc/stat`` telemetry. The
host's acceptance record has no visible GPU, so the evaluator must FAIL it with ``GPU_COUNT``: a node whose
GPU has fallen off the bus must never pass acceptance.
"""
from __future__ import annotations

import copy
import importlib.util
import os
import platform
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import hwlab

EXPERIMENT = {
    "id": "ch16-l2",
    "title": "Lab 16 L2: single-GPU acceptance and burn-in against the acceptance policy",
    "evidence": "MEASURED",
    "cpu_fallback": ("host-RAM write/verify pattern test and a CPU GEMM burn-in with /proc/stat telemetry; the host "
                     "record (no GPU visible) is evaluated by the lab evaluator, which must FAIL it with GPU_COUNT"),
}

PKG = Path(__file__).resolve().parents[2]
LAB = PKG / "lab"

# Clock-event-reason bits (NVML nvmlClocksEventReason*, [VENDOR-SPEC, 2026-10]); names as the lab policy uses them.
REASON_BITS = {0x1: "GPU_IDLE", 0x2: "APPLICATIONS_CLOCKS_SETTING", 0x4: "SW_POWER_CAP", 0x8: "HW_SLOWDOWN",
               0x10: "SYNC_BOOST", 0x20: "SW_THERMAL_SLOWDOWN", 0x40: "HW_THERMAL_SLOWDOWN",
               0x80: "HW_POWER_BRAKE_SLOWDOWN", 0x100: "DISPLAY_CLOCK_SETTING"}
COUNTER_FIELDS = ["clocks_event_reasons_counters.sw_power_cap", "clocks_event_reasons_counters.sw_thermal_slowdown",
                  "clocks_event_reasons_counters.hw_thermal_slowdown",
                  "clocks_event_reasons_counters.hw_power_brake_slowdown"]
INVENTORY_FIELDS = ["index", "uuid", "pci.bus_id", "name", "memory.total", "vbios_version", "driver_version",
                    "pcie.link.gen.current", "pcie.link.gen.max", "pcie.link.width.current", "pcie.link.width.max",
                    "ecc.mode.current", "ecc.errors.corrected.volatile.total", "ecc.errors.uncorrected.volatile.total",
                    "remapped_rows.correctable", "remapped_rows.uncorrectable", "remapped_rows.pending",
                    "remapped_rows.failure", "clocks.max.sm", "power.max_limit", "enforced.power.limit",
                    "temperature.gpu", "temperature.gpu.tlimit"]
SAMPLE_FIELDS = ["index", "temperature.gpu", "power.draw", "clocks.sm", "utilization.gpu",
                 "clocks_event_reasons.active", "pcie.link.gen.current", "pcie.link.width.current"]

# Per-SKU expectations for the adapted policy [VENDOR-SPEC, 2026-10: NVIDIA product pages]. A SKU not listed
# falls back to the maximum link the device reports and 97 % of its reported memory (stated in the report).
SKU_EXPECTED = {
    "NVIDIA GeForce RTX 4060 Laptop GPU": {"gpu_hbm_total_mib_min": 8000, "gpu_pcie": {"gen": 4, "width": 8}},
}
# Dense FP16 tensor-core FLOP per clock per SM with FP16 accumulate (Ada/Hopper whitepapers): an upper bound
# for any FP16 GEMM. GeForce Ada runs FP32-accumulate (what cuBLAS uses for torch.half) at half that rate.
FP16_FLOP_PER_CLK_SM = 1024


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
    """Background ``nvidia-smi --query-gpu ... -lms`` reader; rows of GPU 0 stamped with perf_counter()."""

    def __init__(self, fields: list[str], interval_ms: int = 250):
        self.fields, self.interval_ms, self.samples, self.proc = fields, interval_ms, [], None
        self._thread = None

    def __enter__(self):
        if shutil.which("nvidia-smi"):
            self.proc = subprocess.Popen(
                ["nvidia-smi", f"--query-gpu={','.join(self.fields)}", "--format=csv,noheader,nounits",
                 f"-lms={self.interval_ms}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
            self._thread = threading.Thread(target=self._read, daemon=True)
            self._thread.start()
            time.sleep(0.6)  # first rows arrive after nvidia-smi initializes
        return self

    def _read(self):
        for line in self.proc.stdout:
            vals = line.split(",")
            if len(vals) == len(self.fields):
                row = dict(zip(self.fields, map(_parse, vals)))
                if row.get("index") in (0, 0.0, None):
                    row["t"] = time.perf_counter()
                    self.samples.append(row)

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        return False

    def window(self, t0: float, t1: float) -> list[dict]:
        return [s for s in self.samples if t0 <= s["t"] <= t1]


class CpuSampler:
    """Host telemetry for the CPU fallback: /proc/stat busy fraction and the mean 'cpu MHz' of /proc/cpuinfo."""

    def __init__(self, interval_s: float = 0.25):
        self.interval_s, self.samples, self._stop = interval_s, [], threading.Event()

    @staticmethod
    def _stat():
        try:
            f = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
            return f[3] + f[4], sum(f)
        except (OSError, ValueError, IndexError):
            return None

    @staticmethod
    def _mhz():
        try:
            v = [float(l.split(":")[1]) for l in Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("cpu MHz")]
            return sum(v) / len(v) if v else None
        except (OSError, ValueError):
            return None

    def _loop(self):
        prev = self._stat()
        while not self._stop.wait(self.interval_s):
            cur = self._stat()
            if prev and cur and cur[1] > prev[1]:
                busy = 1 - (cur[0] - prev[0]) / (cur[1] - prev[1])
                self.samples.append({"t": time.perf_counter(), "cpu_util_pct": 100 * busy, "cpu_mhz": self._mhz()})
            prev = cur

    def __enter__(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=2)
        return False

    def window(self, t0, t1):
        return [s for s in self.samples if t0 <= s["t"] <= t1]


def load_lab_model(name: str):
    """The lab's L1 model: the reference solution when the instructor tree is present, else the learner's starter."""
    for path in (PKG / "solutions" / "lab" / f"{name}.py", LAB / "starter" / f"{name}.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, path.relative_to(PKG).as_posix()
    return None, None


def reasons(mask) -> list[str]:
    return [n for b, n in REASON_BITS.items() if mask and int(mask) & b]


def stats(vals: list[float]) -> dict | None:
    vals = [v for v in vals if isinstance(v, (int, float))]
    return {k: round(v, 3) for k, v in hwlab.summarize(vals).items()} if vals else None


# ----------------------------------------------------------------------------------------------- measurements
def memory_pattern_test(ctx) -> dict:
    """Write/verify four patterns over a fresh allocation; returns mismatches and fill bandwidth."""
    torch = ctx.torch
    dev = "cuda" if ctx.is_gpu else "cpu"
    mib = (512 if ctx.quick else 1536) if ctx.is_gpu else (256 if ctx.quick else 1024)
    n = mib * 1024 * 1024 // 4
    x = torch.empty(n, dtype=torch.int32, device=dev)
    mismatches, fills = 0, []
    for pat in (0x00000000, -1, 0x55555555, -0x55555556):     # 0x00.., 0xFF.., 0x55.., 0xAA..
        t0 = time.perf_counter()
        x.fill_(pat)
        ctx.sync()
        fills.append(n * 4 / (time.perf_counter() - t0) / 1e9)
        mismatches += int((x != pat).sum().item())
    k = -1640531535                                         # 2654435761 as int32: address-dependent pattern
    chunk = 16 * 1024 * 1024
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        x[s:e].copy_(torch.arange(s, e, dtype=torch.int32, device=dev)).mul_(k)
    ctx.sync()
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        mismatches += int((x[s:e] != torch.arange(s, e, dtype=torch.int32, device=dev).mul_(k)).sum().item())
    del x
    if ctx.is_gpu:
        torch.cuda.empty_cache()
    return {"size_mib": mib, "patterns": 5, "mismatches": mismatches, "fill_gbs_median": round(sorted(fills)[len(fills) // 2], 2)}


def gemm_setup(ctx):
    torch = ctx.torch
    if ctx.is_gpu:
        n, dtype = 4096, torch.float16
    else:
        n, dtype = (1024 if ctx.quick else 2048), torch.float32
    dev = "cuda" if ctx.is_gpu else "cpu"
    a, b = torch.randn(n, n, device=dev, dtype=dtype), torch.randn(n, n, device=dev, dtype=dtype)
    c = torch.empty(n, n, device=dev, dtype=dtype)
    return n, (lambda: torch.matmul(a, b, out=c)), 2.0 * n ** 3


def burn_in(ctx, gemm, flop: float, seconds: float, sampler) -> list[dict]:
    """Sustained GEMM load in ~1 s windows (sync every 8 GEMMs); per-window achieved TFLOP/s and telemetry."""
    windows, t_end = [], time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        t0, done = time.perf_counter(), 0
        while time.perf_counter() - t0 < 1.0:
            for _ in range(8):
                gemm()
            done += 8
            ctx.sync()
        t1 = time.perf_counter()
        windows.append({"t0": t0, "t1": t1, "tflops": done * flop / (t1 - t0) / 1e12})
    return windows


def probe_absent(ctx, inv: dict | None) -> list[dict]:
    """Probe each acceptance check that needs hardware absent on a one-GPU host; record why and what is needed."""
    torch = ctx.torch
    parts = []
    ngpu = torch.cuda.device_count() if ctx.is_gpu else 0
    nvl = subprocess.run(["nvidia-smi", "nvlink", "--status"], capture_output=True, text=True).stdout.strip() \
        if shutil.which("nvidia-smi") else ""
    links = sum(1 for line in nvl.splitlines() if line.strip().startswith("Link "))
    parts.append({"check": "NVLINK_DOWN (18 links per GPU)", "probe": f"nvidia-smi nvlink --status lists {links} links",
                  "needs": ["NVLink/NVSwitch GPUs (HX8 baseboard)"]})
    ecc = (inv or {}).get("ecc.mode.current")
    if ecc is None:
        parts.append({"check": "ECC_DBE / ECC_SBE_ELEVATED",
                      "probe": "ecc.mode.current = [N/A] (no ECC on this SKU)" if inv else "no GPU visible",
                      "needs": ["a data-centre GPU with HBM ECC enabled"]})
    parts.append({"check": "DCGM_DIAG_FAIL (dcgmi diag -r 3)", "probe": f"dcgmi on PATH: {bool(shutil.which('dcgmi'))}",
                  "needs": ["DCGM host engine + dcgmi (data-centre GPU, root)"]})
    ib = Path("/sys/class/infiniband")
    parts.append({"check": "NIC_COUNT / NIC_SPEED / NIC_MTU / RDMA_PAIR_BW_LOW",
                  "probe": f"/sys/class/infiniband present: {ib.is_dir()}; container runs with --network none",
                  "needs": ["8 x 400G RDMA NICs + 2 front-end NICs, perftest, a reference node per rail"]})
    nvme = sorted(str(p) for p in Path("/dev").glob("nvme*"))
    parts.append({"check": "NVME_COUNT / NVME_MEDIA_ERRORS / STORAGE_THROUGHPUT_LOW",
                  "probe": f"/dev/nvme*: {nvme or 'none visible'}; uid {os.getuid()}",
                  "needs": ["root, nvme-cli, fio, dedicated data drives"]})
    parts.append({"check": "NCCL_BUSBW_LOW / NCCL_ALGO_UNRECORDED", "probe": f"torch.cuda.device_count() = {ngpu}",
                  "needs": [">= 2 GPUs (8 on NVSwitch for NVLS), nccl-tests"]})
    dm = subprocess.run(["dmesg"], capture_output=True, text=True)
    parts.append({"check": "XID_PRESENT (kernel log scan)",
                  "probe": f"dmesg rc={dm.returncode}: {(dm.stderr or dm.stdout).strip()[:60]}",
                  "needs": ["kernel log access on the host (root, journalctl -k)"]})
    parts.append({"check": "FW_OFF_MATRIX (BIOS/BMC/NIC firmware bundle)", "probe": "no BMC/Redfish endpoint on a laptop",
                  "needs": ["BMC with Redfish FirmwareInventory, a platform compatibility matrix"]})
    return parts


# ----------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    burn_s = 12.0 if ctx.quick else 90.0
    notes = [
        "Burn-in is a short scripted soak, not the policy's 24 h burn-in: duration_h in the record is the real duration.",
        "Telemetry sampled every 250 ms with nvidia-smi -lms (GPU) or /proc/stat (CPU); medians and p95 over the soak.",
        "GPU evidence runs are serial; another job on the same GPU would show up as dips in the per-window TFLOP/s.",
    ]
    inv = None
    if ctx.is_gpu:
        inv = {k: _parse(v) for k, v in hwlab.nvidia_smi_query(INVENTORY_FIELDS)[0].items()}
        inv["name"] = hwlab.nvidia_smi_query(["name"])[0]["name"]
        inv["uuid"], inv["pci.bus_id"] = (hwlab.nvidia_smi_query(["uuid", "pci.bus_id"])[0][k] for k in ("uuid", "pci.bus_id"))
        inv["vbios_version"], inv["driver_version"] = (hwlab.nvidia_smi_query(["vbios_version", "driver_version"])[0][k]
                                                       for k in ("vbios_version", "driver_version"))
        for k in ("remapped_rows.pending", "remapped_rows.failure"):
            raw = hwlab.nvidia_smi_query([k])[0][k]
            inv[k] = None if raw.startswith("[") else raw
        ctx.log(f"inventory: {inv['name']} {inv['pci.bus_id']} VBIOS {inv['vbios_version']} driver {inv['driver_version']}")

    mem = memory_pattern_test(ctx)
    ctx.log(f"memory pattern test: {mem['size_mib']} MiB x {mem['patterns']} patterns, {mem['mismatches']} mismatches")

    n, gemm, flop = gemm_setup(ctx)
    g = ctx.bench(gemm, warmup=3, reps=ctx.reps(10))
    gemm_tflops = flop / g["median"] / 1e12
    ctx.log(f"GEMM {n}^3: {gemm_tflops:.2f} TFLOP/s (median of {g['n']})")

    counters0 = hwlab.nvidia_smi_query(COUNTER_FIELDS) if ctx.is_gpu else []
    sampler_cls = (lambda: NvSampler(SAMPLE_FIELDS, 250)) if ctx.is_gpu else (lambda: CpuSampler(0.25))
    with sampler_cls() as smp:
        t_idle0 = time.perf_counter()
        time.sleep(1.0)
        idle = smp.window(t_idle0, time.perf_counter())
        tb0 = time.perf_counter()
        windows = burn_in(ctx, gemm, flop, burn_s, smp)
        tb1 = time.perf_counter()
        time.sleep(0.3)
        load = smp.window(tb0 + 1.0, tb1)        # skip the first second: clocks and link ramp up
    counters1 = hwlab.nvidia_smi_query(COUNTER_FIELDS) if ctx.is_gpu else []
    tput = [w["tflops"] for w in windows]
    tel = {"burn_in_s": round(tb1 - tb0, 1), "samples": len(load), "tflops_windows": stats(tput)}
    if tput:
        tel["tflops_first_last_ratio"] = round(tput[-1] / tput[0], 3)
    record_gpus = []
    if ctx.is_gpu:
        mask_union = 0
        for s in load:
            mask_union |= int(s.get("clocks_event_reasons.active") or 0)
        frac = {}
        for name in REASON_BITS.values():
            bit = next(b for b, nm in REASON_BITS.items() if nm == name)
            frac[name] = round(sum(1 for s in load if int(s.get("clocks_event_reasons.active") or 0) & bit) / max(1, len(load)), 3)
        cdelta = {}
        if counters0 and counters1:
            for f in COUNTER_FIELDS:
                try:
                    cdelta[f.split(".")[-1]] = round((float(counters1[0][f]) - float(counters0[0][f])) / 1e6, 3)
                except ValueError:
                    cdelta[f.split(".")[-1]] = None
        if cdelta.get("sw_power_cap") == 0 and frac.get("SW_POWER_CAP", 0) > 0.5:
            notes.append("The driver's sw_power_cap counter did not advance although the SW_POWER_CAP bit was set in "
                         f"{100 * frac['SW_POWER_CAP']:.0f} % of samples: on this driver (WSL2) the counters are not a reliable "
                         "duration source, so this run judges by the sampled bitmask. Check both on your own fleet.")
        gens = [s["pcie.link.gen.current"] for s in load if s.get("pcie.link.gen.current")]
        widths = [s["pcie.link.width.current"] for s in load if s.get("pcie.link.width.current")]
        tel.update({
            "temp_c": stats([s["temperature.gpu"] for s in load]), "power_w": stats([s["power.draw"] for s in load]),
            "sm_clock_mhz": stats([s["clocks.sm"] for s in load]), "util_pct": stats([s["utilization.gpu"] for s in load]),
            "reasons_seen": reasons(mask_union), "reason_fraction_of_samples": {k: v for k, v in frac.items() if v},
            "reason_counter_delta_s": cdelta,
            "pcie_gen_idle": min([s["pcie.link.gen.current"] for s in idle if s.get("pcie.link.gen.current")] or [None]),
            "pcie_gen_load_min": min(gens) if gens else None, "pcie_width_load_min": min(widths) if widths else None,
        })
        rr_pending = inv.get("remapped_rows.pending")
        record_gpus.append({
            "index": 0, "uuid": inv["uuid"], "bdf": inv["pci.bus_id"], "product": inv["name"],
            "hbm_total_mib": int(inv["memory.total"]),
            "pcie": {"gen": int(tel["pcie_gen_load_min"] or 0), "width": int(tel["pcie_width_load_min"] or 0),
                     "gen_idle": tel["pcie_gen_idle"]},
            "nvlink_links_up": 0,
            "ecc": ({} if inv.get("ecc.mode.current") is None else
                    {"sbe_volatile": int(inv.get("ecc.errors.corrected.volatile.total") or 0),
                     "dbe_volatile": int(inv.get("ecc.errors.uncorrected.volatile.total") or 0)}),
            "row_remap": {"correctable": int(inv.get("remapped_rows.correctable") or 0),
                          "uncorrectable": int(inv.get("remapped_rows.uncorrectable") or 0),
                          "pending": rr_pending == "Yes", "failure": inv.get("remapped_rows.failure") == "Yes",
                          "available": rr_pending is not None},
            "burn_in": {"duration_h": round((tb1 - tb0) / 3600, 4),
                        "max_temp_c": tel["temp_c"]["max"] if tel["temp_c"] else None,
                        "throttle_reasons": tel["reasons_seen"]},
        })
        ctx.log(f"burn-in {tel['burn_in_s']} s: {tel['tflops_windows']['median']:.1f} TFLOP/s median, max "
                f"{tel['temp_c']['max']:.0f} C, power p95 {tel['power_w']['p95']:.1f} W, reasons {tel['reasons_seen']}")
    else:
        tel.update({"cpu_util_pct": stats([s["cpu_util_pct"] for s in load]),
                    "cpu_mhz": stats([s["cpu_mhz"] for s in load if s.get("cpu_mhz")])})
        ctx.log(f"CPU burn-in {tel['burn_in_s']} s: {tel['tflops_windows']['median'] * 1e3:.1f} GFLOP/s median")

    # -------- evaluate with the lab model
    mod, model_path = load_lab_model("fleet_lifecycle")
    policy = mod.load_yaml(LAB / "data" / "acceptance_policy.yaml") if mod else None
    matrix = mod.load_yaml(LAB / "data" / "compat_matrix.yaml") if mod else None
    local = copy.deepcopy(policy) if policy else None
    sku = None
    if local:
        sku = inv["name"] if inv else "none visible"
        exp = SKU_EXPECTED.get(sku) or ({"gpu_hbm_total_mib_min": int(0.97 * inv["memory.total"]),
                                         "gpu_pcie": {"gen": int(inv["pcie.link.gen.max"]), "width": int(inv["pcie.link.width.max"])}}
                                        if inv else {"gpu_hbm_total_mib_min": 1, "gpu_pcie": {"gen": 1, "width": 1}})
        local["expected"].update({"gpu_count": 1, "gpu_product": sku if inv else "any GPU",
                                  "nvlink_links_per_gpu": 0, **copy.deepcopy(exp)})
        local["policy_version"] = policy["policy_version"] + "+local-sku"
    record = {
        "node": socket.gethostname(), "acceptance_policy": local["policy_version"] if local else None,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "firmware": {"kernel": platform.release(), "gpu_driver": inv["driver_version"] if inv else None,
                     "gpu_vbios": inv["vbios_version"] if inv else None},
        "gpus": record_gpus, "dcgm_diag": None, "nics": [], "storage": {}, "nccl_single_node": None, "xid_events": [],
    }
    applicable = {"GPU_COUNT", "GPU_PRODUCT", "HBM_CAPACITY", "PCIE_DEGRADED", "HBM_ROW_REMAP_PENDING",
                  "HBM_ROW_REMAP_FAILURE", "THERMAL_THROTTLE"}
    if record_gpus and record_gpus[0]["ecc"]:
        applicable |= {"ECC_DBE", "ECC_SBE_ELEVATED"}
    evaluation = None
    if mod:
        try:
            ev = mod.evaluate_node(record, local, matrix)
            app_codes = sorted(c for c in ev["codes"] if c in applicable)
            app_warn = sorted(c for c in ev["warnings"] if c in applicable)
            evaluation = {"model": model_path, "raw_codes": ev["codes"], "raw_warnings": ev["warnings"],
                          "applicable_codes": app_codes, "applicable_warnings": app_warn,
                          "verdict_applicable": "FAIL" if app_codes else ("WARN" if app_warn else "PASS"),
                          "details": [d for d in ev["details"] if d.split(":")[0] in applicable]}
            ctx.log(f"lab evaluator ({model_path}): applicable verdict {evaluation['verdict_applicable']} {app_codes}")
        except NotImplementedError as exc:
            notes.append(f"Lab evaluator not implemented yet in {model_path} ({exc}); the evaluation step was skipped. "
                         "Implement evaluate_node in lab/starter/fleet_lifecycle.py and rerun.")
    else:
        notes.append("No lab model found (solutions/lab or lab/starter fleet_lifecycle.py); the evaluation step was skipped.")

    not_runnable = probe_absent(ctx, inv)
    metrics = {"memtest_mismatches": mem["mismatches"], "memtest_fill_gbs": mem["fill_gbs_median"],
               "gemm_tflops": round(gemm_tflops, 3), "burn_in_s": tel["burn_in_s"],
               "burn_in_tflops_median": round(tel["tflops_windows"]["median"], 3) if tput else None}
    if ctx.is_gpu:
        p = torch.cuda.get_device_properties(0)
        ceiling = FP16_FLOP_PER_CLK_SM * p.multi_processor_count * float(inv["clocks.max.sm"]) * 1e6 / 1e12
        metrics.update({"gemm_ceiling_tflops": round(ceiling, 1), "sm_count": p.multi_processor_count,
                        "clocks_max_sm_mhz": inv["clocks.max.sm"], "power_max_limit_w": inv["power.max_limit"],
                        "enforced_power_limit_w": inv["enforced.power.limit"],
                        "temp_margin_to_slowdown_c_idle": inv.get("temperature.gpu.tlimit"),
                        "burn_in_temp_max_c": tel["temp_c"]["max"], "burn_in_power_p95_w": tel["power_w"]["p95"],
                        "burn_in_sm_clock_median_mhz": tel["sm_clock_mhz"]["median"]})
    if evaluation:
        metrics["verdict_applicable"] = evaluation["verdict_applicable"]
    return {"metrics": metrics,
            "tables": {"inventory": inv or {}, "memtest": mem, "gemm": {"n": n, **{k: g[k] for k in ("median", "p95", "iqr", "n")}},
                       "burn_in": tel, "burn_in_windows": [{"tflops": round(w["tflops"], 3)} for w in windows],
                       "record": record, "policy_expected_local": local["expected"] if local else None,
                       "evaluation": evaluation},
            "not_runnable_parts": not_runnable, "notes": notes}


# ----------------------------------------------------------------------------------------------- check
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if m["memtest_mismatches"] != 0:
        fails.append(f"memory pattern test found {m['memtest_mismatches']} mismatches on a fresh allocation: rerun; if it "
                     "repeats, read nvidia-smi -q -d ROW_REMAPPER and treat the GPU as failed (RMA path)")
    if not m["gemm_tflops"] > 0 or not m.get("burn_in_tflops_median"):
        fails.append("GEMM or burn-in throughput is not positive: the workload did not run")
    ev = t.get("evaluation")
    if env["device"] == "cuda":
        bi = t["burn_in"]
        if m["gemm_tflops"] > m["gemm_ceiling_tflops"]:
            fails.append(f"GEMM {m['gemm_tflops']:.1f} TFLOP/s exceeds the FP16 tensor ceiling {m['gemm_ceiling_tflops']:.1f} "
                         "(1024 FLOP/clk/SM x SMs x max SM clock): check the timing (missing synchronize?)")
        if bi["samples"] < 0.5 * bi["burn_in_s"]:
            fails.append(f"only {bi['samples']} telemetry samples in {bi['burn_in_s']} s: check that nvidia-smi -lms works")
        pmax = m.get("power_max_limit_w")
        if pmax and bi["power_w"] and bi["power_w"]["max"] > 1.10 * pmax:
            fails.append(f"sampled power {bi['power_w']['max']} W above 1.1 x the {pmax} W max power limit: check power.draw units")
        if bi["sm_clock_mhz"] and bi["sm_clock_mhz"]["max"] > m["clocks_max_sm_mhz"] * 1.01:
            fails.append("SM clock above clocks.max.sm: check the clock field")
        if bi["util_pct"] and bi["util_pct"]["median"] < 50:
            fails.append(f"GPU utilization median {bi['util_pct']['median']} % during burn-in: the soak did not load the GPU")
        if ev:
            # The L1 model must agree with the raw telemetry it was fed (validates evaluate_node against reality).
            fail_reasons = {"HW_THERMAL_SLOWDOWN", "SW_THERMAL_SLOWDOWN", "HW_POWER_BRAKE_SLOWDOWN"}
            thermal_expected = bool(set(bi["reasons_seen"]) & fail_reasons) or (bi["temp_c"]["max"] >= 87)
            if thermal_expected != ("THERMAL_THROTTLE" in ev["applicable_codes"]):
                fails.append(f"evaluator THERMAL_THROTTLE={'THERMAL_THROTTLE' in ev['applicable_codes']} disagrees with the "
                             f"telemetry (reasons {bi['reasons_seen']}, max {bi['temp_c']['max']} C): check evaluate_node")
            exp = t["policy_expected_local"]["gpu_pcie"]
            degraded = (bi["pcie_gen_load_min"], bi["pcie_width_load_min"]) != (exp["gen"], exp["width"])
            if degraded != ("PCIE_DEGRADED" in ev["applicable_codes"]):
                fails.append("evaluator PCIE_DEGRADED disagrees with the link sampled under load: check evaluate_node")
            if "SW_POWER_CAP" in bi["reasons_seen"] and "THERMAL_THROTTLE" in ev["applicable_codes"] and not thermal_expected:
                fails.append("SW_POWER_CAP alone must not fail acceptance (policy throttle_reasons_ignore)")
    else:
        if m["gemm_tflops"] * 1e12 > (env.get("cpu_count") or 1) * 5e9 * 32:
            fails.append("CPU GFLOP/s above cores x 5 GHz x 32 FP32 FLOP/clk (AVX2 FMA): check the timing")
        if ev and "GPU_COUNT" not in ev["applicable_codes"]:
            fails.append("a host with no visible GPU must FAIL acceptance with GPU_COUNT: check evaluate_node")
    return fails


# ----------------------------------------------------------------------------------------------- report
def _fmt(st, unit="", scale=1.0):
    return "n/a" if not st else f"{st['median'] * scale:.1f} / {st['p95'] * scale:.1f} / {st['min'] * scale:.1f}-{st['max'] * scale:.1f}{unit}"


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    bi = t["burn_in"]
    L = ["## Acceptance measurements", "",
         "| Check | Result | Note |", "|---|---|---|",
         f"| Memory write/verify ({t['memtest']['size_mib']} MiB, 5 patterns) | {m['memtest_mismatches']} mismatches | "
         f"fill {m['memtest_fill_gbs']} GB/s |"]
    if gpu:
        L += [f"| FP16 GEMM 4096³ | {m['gemm_tflops']:.2f} TFLOP/s | {100 * m['gemm_tflops'] / m['gemm_ceiling_tflops']:.0f} % of the "
              f"{m['gemm_ceiling_tflops']:.1f} TFLOP/s dense FP16 tensor ceiling `[MODELED]` (1024 FLOP/clk/SM x SMs x max SM clock) |",
              f"| PCIe link idle → under load | Gen{bi['pcie_gen_idle'] or 0:.0f} → Gen{bi['pcie_gen_load_min'] or 0:.0f} x{bi['pcie_width_load_min'] or 0:.0f} | "
              f"expected Gen{t['policy_expected_local']['gpu_pcie']['gen']} x{t['policy_expected_local']['gpu_pcie']['width']} "
              "under load; a low idle gen is normal power saving (exercise K2) |",
              f"| Row remapper | pending={t['record']['gpus'][0]['row_remap']['pending']}, "
              f"failure={t['record']['gpus'][0]['row_remap']['failure']} | read-only `nvidia-smi` query |"]
    else:
        L.append(f"| FP32 GEMM | {m['gemm_tflops'] * 1e3:.1f} GFLOP/s | CPU fallback |")
    L += ["", f"## Burn-in ({bi['burn_in_s']} s soak, {bi['samples']} telemetry samples)", "",
          "| Signal | median / p95 / min-max |", "|---|---|",
          f"| Throughput per 1 s window | {_fmt(bi['tflops_windows'], ' TFLOP/s' if gpu else ' GFLOP/s', 1.0 if gpu else 1e3)} |"]
    if gpu:
        L += [f"| GPU temperature | {_fmt(bi['temp_c'], ' C')} |", f"| Power draw | {_fmt(bi['power_w'], ' W')} |",
              f"| SM clock | {_fmt(bi['sm_clock_mhz'], ' MHz')} |", f"| GPU utilization | {_fmt(bi['util_pct'], ' %')} |",
              "", f"Clock-event reasons seen under load: **{', '.join(bi['reasons_seen']) or 'none'}** "
              f"(share of samples: {bi['reason_fraction_of_samples']}). Driver counters, seconds accrued during the soak: "
              f"{bi['reason_counter_delta_s']}. Enforced power limit {m['enforced_power_limit_w']} W."]
    else:
        L += [f"| CPU busy | {_fmt(bi.get('cpu_util_pct'), ' %')} |", f"| CPU MHz (/proc/cpuinfo) | {_fmt(bi.get('cpu_mhz'), ' MHz')} |"]
    ev = t.get("evaluation")
    L += ["", "## Verdict from the lab evaluator", ""]
    if ev:
        L += [f"Model: `{ev['model']}`, policy `acc-2026.10` thresholds unchanged; `expected` adapted to this SKU: "
              f"`{t['policy_expected_local']['gpu_product']}`, ≥ {t['policy_expected_local']['gpu_hbm_total_mib_min']} MiB, "
              f"Gen{t['policy_expected_local']['gpu_pcie']['gen']} x{t['policy_expected_local']['gpu_pcie']['width']}, 1 GPU, 0 NVLinks.", "",
              f"**Verdict on the checks that apply here: {ev['verdict_applicable']}** "
              f"{ev['applicable_codes'] + ev['applicable_warnings'] or ''}", ""]
        L += [f"- {d}" for d in ev["details"]]
        other = sorted(set(ev["raw_codes"]) - set(ev["applicable_codes"]))
        L += ["", f"The evaluator also raised {other}: those checks have no input on this host (table below), so they are "
              "reported as not runnable, not as node faults. A real acceptance run must supply them."]
    else:
        L.append("The lab evaluator was not available (see notes).")
    L += ["", "## Not runnable on this host", "", "| Policy check | Probe | Needs |", "|---|---|---|"]
    L += [f"| {p['check']} | {p['probe']} | {', '.join(p['needs'])} |" for p in result.get("not_runnable_parts", [])]
    L += ["", "## What to conclude", ""]
    if gpu:
        L += [f"- This is a **laptop Ada GPU** (`{t['inventory'].get('name')}`), not an H100 SXM in an HX8. The policy thresholds "
              "(87 C, throttle-reason classes) transfer; the expected hardware does not, so `expected` is per-SKU and versioned.",
              "- `SW_POWER_CAP` under a GEMM soak is the normal state of a GPU working at its power limit (policy "
              "`throttle_reasons_ignore`); a thermal reason (`SW/HW_THERMAL_SLOWDOWN`) or `HW_POWER_BRAKE_SLOWDOWN` is the failure "
              "signal (exercise K4). The counters say how long each reason held, which a 1 s sample can miss.",
              "- A real acceptance run is the same code path fed by more collectors: DCGM, NCCL, perftest, NVMe, Xid and BMC. Until "
              "those exist, a PASS here means only that the listed GPU checks passed."]
    else:
        L += ["- _CPU fallback: no GPU was visible, so the acceptance record has no GPU section and the lab evaluator FAILs it with "
              "`GPU_COUNT`. That is the correct outcome for a node whose GPU has fallen off the bus. The memory and burn-in "
              "measurements exercise the same harness on host RAM and CPU cores; GPU-only invariants were skipped._"]
    return "\n".join(L)
