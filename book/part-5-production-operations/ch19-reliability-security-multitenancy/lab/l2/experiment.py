"""Ch 19 L2: read-only GPU health queries and clock-event-reason interpretation on a real GPU.

What it teaches (Sections 19.2-19.3, 19.6; exercises K2, T1): the first minutes of a GPU incident are
read-only. You identify the device, read its memory-health state, check the PCIe link and its replay
counter, and interpret clock-event reasons before anyone resets anything.

1. **Read-only health queries:** identity (UUID, BDF, serial, VBIOS, InfoROM), ECC mode and counters,
   row-remapper state and bank-availability histogram, retired pages, the driver's recommended recovery
   action, the PCIe link (device and host maximum, current) and replays since reset, and ``nvidia-smi topo -m``.
   The row goes into the lab's ``gpu_actions`` (the reference solution, or the learner's starter) to get a health
   decision on real data. The rank-map row is built from what one host can see.
2. **Clock-event reasons under controlled phases:** idle, a compute-bound GEMM soak, a memory-bound copy soak,
   and idle again. The bitmask is sampled every 200 ms, together with SM clock, power and temperature, and the
   driver's per-reason counters are read before and after each phase. Each phase is then classified with the
   chapter's decision rules (normal / investigate / drain).

Absent here (probed, recorded as not runnable): ECC on this SKU, kernel Xid/AER logs (no kernel-log access in
the container), ``lspci`` AER capability, DCGM diagnostics, RDMA HCAs for the rank map's NIC columns, and the
L3 link-flap trials.

CPU fallback: read-only host health queries (CPU, memory, kernel, EDAC/ECC presence, kernel-log access) and
the same idle/load/idle phases, interpreted through Linux pressure-stall information (``/proc/pressure/cpu``):
the host-side analogue of "why is this device slower than it could be". GPU-only invariants are skipped.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import hwlab

EXPERIMENT = {
    "id": "ch19-l2",
    "title": "Lab 19 L2: read-only GPU health queries and clock-event-reason interpretation",
    "evidence": "MEASURED",
    "cpu_fallback": ("read-only host health queries (CPU, memory, EDAC, kernel-log access) and idle/load/idle phases "
                     "interpreted through /proc/pressure/cpu stall time; the lab's gpu_actions runs on the (empty) GPU table"),
}

PKG = Path(__file__).resolve().parents[2]
LAB = PKG / "lab"

REASON_BITS = {0x1: "GPU_IDLE", 0x2: "APPLICATIONS_CLOCKS_SETTING", 0x4: "SW_POWER_CAP", 0x8: "HW_SLOWDOWN",
               0x10: "SYNC_BOOST", 0x20: "SW_THERMAL_SLOWDOWN", 0x40: "HW_THERMAL_SLOWDOWN",
               0x80: "HW_POWER_BRAKE_SLOWDOWN", 0x100: "DISPLAY_CLOCK_SETTING"}   # NVML, [VENDOR-SPEC, 2026-10]
COUNTERS = ["sw_power_cap", "sw_thermal_slowdown", "hw_thermal_slowdown", "hw_power_brake_slowdown", "sync_boost"]
HEALTH_FIELDS = ["index", "uuid", "pci.bus_id", "serial", "name", "vbios_version", "driver_version", "inforom.img",
                 "persistence_mode", "ecc.mode.current", "ecc.errors.corrected.volatile.total",
                 "ecc.errors.uncorrected.volatile.total", "remapped_rows.correctable", "remapped_rows.uncorrectable",
                 "remapped_rows.pending", "remapped_rows.failure", "retired_pages.pending", "gpu_recovery_action",
                 "pcie.link.gen.current", "pcie.link.gen.max", "pcie.link.width.current", "pcie.link.width.max",
                 "clocks_event_reasons.supported", "clocks.max.sm", "enforced.power.limit", "temperature.gpu.tlimit"]
SAMPLE_FIELDS = ["index", "clocks_event_reasons.active", "clocks.sm", "clocks.mem", "power.draw", "temperature.gpu",
                 "utilization.gpu", "utilization.memory"]


# ----------------------------------------------------------------------------------------------- helpers
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


def decode(mask) -> list[str]:
    return [n for b, n in REASON_BITS.items() if mask is not None and int(mask) & b]


class NvSampler:
    def __init__(self, fields, interval_ms=200):
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


def sh(cmd: list[str]) -> tuple[int, str]:
    if not shutil.which(cmd[0]):
        return 127, f"{cmd[0]}: not installed"
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return p.returncode, (p.stdout + p.stderr).strip()


def load_lab_model(name: str):
    """The lab's L1 model: the reference solution when the instructor tree is present, else the learner's starter."""
    for path in (PKG / "solutions" / "lab" / f"{name}.py", LAB / "starter" / f"{name}.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, path.relative_to(PKG).as_posix()
    return None, None


def med(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(hwlab.summarize(vals)["median"], 2) if vals else None


def read_counters() -> dict:
    rows = hwlab.nvidia_smi_query([f"clocks_event_reasons_counters.{c}" for c in COUNTERS])
    return {c: _num(rows[0][f"clocks_event_reasons_counters.{c}"]) for c in COUNTERS} if rows else {}


def psi_cpu() -> dict | None:
    try:
        out = {}
        for line in Path("/proc/pressure/cpu").read_text().splitlines():
            kind, *kv = line.split()
            out[kind] = {k: float(v) for k, v in (x.split("=") for x in kv)}
        return out
    except (OSError, ValueError):
        return None


def proc_stat():
    try:
        f = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
        return f[3] + f[4], sum(f)
    except (OSError, ValueError, IndexError):
        return None


# ----------------------------------------------------------------------------------------------- interpretation
def interpret(phase: dict, max_sm: float | None) -> tuple[str, str]:
    """Chapter 18/19 decision rules for one phase -> (interpretation, action class)."""
    r = {k for k, v in phase["reason_share"].items() if v >= 0.2}
    if r & {"SW_THERMAL_SLOWDOWN", "HW_THERMAL_SLOWDOWN"}:
        return ("thermal slowdown: the cooling path cannot remove the heat (airflow, fan, cold plate, inlet)",
                "drain; inspect cooling; compare with peers; do not RMA first")
    if "HW_POWER_BRAKE_SLOWDOWN" in r:
        return "external power-brake signal from the platform (PSU/BMC)", "escalate to facilities/platform; drain"
    if "HW_SLOWDOWN" in r:
        return "hardware slowdown without a named child reason", "drain and run diagnostics"
    if "SW_POWER_CAP" in r:
        return ("power-limited at the enforced limit: the normal state of a GPU working flat out",
                "none: normal under full load (judge the sustained clock against peers)")
    if (phase.get("util_pct") or 0) < 5:
        if max_sm and (phase.get("sm_mhz") or 0) > 0.5 * max_sm:
            return ("just after load: no work, but clocks and power are still decaying and GPU_IDLE is not yet asserted "
                    "in every sample", "none: sample idle state several seconds after the last kernel")
        return "idle: clocks parked, nothing to run", "none"
    if max_sm and phase.get("sm_mhz") and phase["sm_mhz"] < 0.9 * max_sm and (phase.get("util_pct") or 0) > 50:
        return ("busy below max boost with no reason asserted: the voltage/frequency curve, not throttling",
                "none: compare against peers' sustained clock")
    return "busy at or near boost with no limiting reason", "none"


# ----------------------------------------------------------------------------------------------- run
def gpu_health(ctx) -> tuple[dict, list[dict]]:
    raw = hwlab.nvidia_smi_query(HEALTH_FIELDS)[0]
    h = {k: (v if k in ("uuid", "pci.bus_id", "serial", "name", "vbios_version", "driver_version", "inforom.img",
                        "persistence_mode", "ecc.mode.current", "remapped_rows.pending", "remapped_rows.failure",
                        "retired_pages.pending", "gpu_recovery_action") else _num(v)) for k, v in raw.items()}
    rc, q = sh(["nvidia-smi", "-q"])
    for label, key in (("Replays Since Reset", "pcie_replays_since_reset"), ("Replay Number Rollovers", "pcie_replay_rollovers"),
                       ("Host Max", "pcie_host_max_gen"), ("Device Max", "pcie_device_max_gen")):
        m = re.search(rf"{label}\s*:\s*(\S+)", q)
        v = _num(m.group(1)) if m else None
        h[key] = int(v) if isinstance(v, float) else v
    hist = dict(re.findall(r"^\s+(Max|High|Partial|Low|None)\s*:\s*(\d+) bank", q, re.M))
    h["bank_remap_availability"] = {k: int(v) for k, v in hist.items()}
    _, topo = sh(["nvidia-smi", "topo", "-m"])
    h["topo_m"] = re.sub(r"\x1b\[[0-9;]*m", "", topo)   # drop ANSI underline codes
    ctx.log(f"identity: {h['name']} {h['uuid']} {h['pci.bus_id']} VBIOS {h['vbios_version']} InfoROM {h['inforom.img']}")
    ctx.log(f"memory health: ECC {h['ecc.mode.current']}, remapped rows corr/uncorr {h['remapped_rows.correctable']}/"
            f"{h['remapped_rows.uncorrectable']}, pending {h['remapped_rows.pending']}, failure {h['remapped_rows.failure']}, "
            f"recovery action {h['gpu_recovery_action']}")
    ctx.log(f"PCIe: Gen{h['pcie.link.gen.current']:.0f} x{h['pcie.link.width.current']:.0f} (device max Gen{h['pcie.link.gen.max']:.0f} "
            f"x{h['pcie.link.width.max']:.0f}, host max Gen{h['pcie_host_max_gen']}), replays since reset {h['pcie_replays_since_reset']}")
    return h, probes(ctx, h)


def probes(ctx, h: dict | None) -> list[dict]:
    parts = []
    if h is not None and h.get("ecc.mode.current") in (None, "[N/A]", "N/A"):
        parts.append({"part": "ECC volatile/aggregate counters (nvidia-smi -q -d ECC)", "probe": "ECC mode [N/A] on this SKU",
                      "needs": ["a GPU with ECC-protected HBM/GDDR (data-centre SKU)"]})
    rc, out = sh(["dmesg"])
    parts.append({"part": "Xid / AER lines in the kernel log (journalctl -k | grep -E 'NVRM: Xid|AER')",
                  "probe": f"dmesg rc={rc}: {out.splitlines()[0][:70] if out else ''}; journalctl present: {bool(shutil.which('journalctl'))}",
                  "needs": ["host kernel-log access (root on the host, not in an unprivileged container)"]})
    rc, out = sh(["lspci", "-vvv"])
    devs = sorted(os.listdir("/sys/bus/pci/devices")) if os.path.isdir("/sys/bus/pci/devices") else []
    parts.append({"part": "PCIe AER capability (lspci -vvv -s <bdf>)",
                  "probe": f"lspci rc={rc}; /sys/bus/pci/devices = {devs[:4]} (WSL2 exposes virtual PCI, not the GPU's BDF)",
                  "needs": ["bare-metal Linux with pciutils and root"]})
    parts.append({"part": "dcgmi diag -r 2/3", "probe": f"dcgmi on PATH: {bool(shutil.which('dcgmi'))}",
                  "needs": ["DCGM host engine on a data-centre GPU"]})
    ib = Path("/sys/class/infiniband")
    parts.append({"part": "rank_map NIC columns (hca, hca_bdf, rail, leaf, leaf_port, backend_ip)",
                  "probe": f"/sys/class/infiniband present: {ib.is_dir()}; ibdev2netdev: {bool(shutil.which('ibdev2netdev'))}; "
                           f"lldpctl: {bool(shutil.which('lldpctl'))}",
                  "needs": ["RDMA HCAs, rdma-core, LLDP neighbours on the backend switches"]})
    parts.append({"part": "L3 link-flap trials (3 s / 8 s / 15 s) vs NCCL_IB_TIMEOUT x NCCL_IB_RETRY_CNT",
                  "probe": f"torch.cuda.device_count() = {ctx.torch.cuda.device_count() if ctx.is_gpu else 0}; no RDMA device",
                  "needs": ["2+ RDMA nodes in a dedicated partition and an authorised port to disable"]})
    return parts


def phase_load(ctx, kind: str):
    torch = ctx.torch
    dev = "cuda" if ctx.is_gpu else "cpu"
    if kind == "gemm":
        n = 4096 if ctx.is_gpu else 1024
        dt = torch.float16 if ctx.is_gpu else torch.float32
        a, b = torch.randn(n, n, device=dev, dtype=dt), torch.randn(n, n, device=dev, dtype=dt)
        c = torch.empty(n, n, device=dev, dtype=dt)
        return lambda: [torch.matmul(a, b, out=c) for _ in range(4)]
    if kind == "copy":
        mib = 256 if ctx.is_gpu else 64
        src = torch.empty(mib * 2 ** 20, dtype=torch.uint8, device=dev)
        dst = torch.empty_like(src)
        return lambda: [dst.copy_(src) for _ in range(4)]
    return None


def run(ctx) -> dict:
    torch = ctx.torch
    notes = ["All health queries are read-only: nothing is reset, reconfigured, or written to the device.",
             "Clock-event reasons sampled every 200 ms (nvidia-smi -lms); per-reason counters read before and after each phase."]
    health, not_runnable = (gpu_health(ctx) if ctx.is_gpu else (None, probes(ctx, None)))
    host = {"hostname": socket.gethostname(), "kernel": platform.release(), "cpu": hwlab.cpu_model(),
            "cpus": os.cpu_count(), "mem_gib": hwlab.mem_total_gib(),
            "edac_present": Path("/sys/devices/system/edac/mc").is_dir(), "psi_present": psi_cpu() is not None}
    if not host["edac_present"]:
        not_runnable.append({"part": "host DRAM ECC (EDAC: /sys/devices/system/edac/mc)", "probe": "EDAC sysfs absent",
                             "needs": ["a server platform with ECC DIMMs and the EDAC driver"]})

    # -------- lab model on real data
    mod, model_path = load_lab_model("incident_toolkit")
    import pandas as pd
    if health:
        ecc_ok = health.get("ecc.mode.current") not in (None, "[N/A]", "N/A")
        row = {"node": host["hostname"], "gpu": 0, "gpu_uuid": health["uuid"], "gpu_bdf": health["pci.bus_id"],
               "ecc_sbe_volatile": int(health["ecc.errors.corrected.volatile.total"] or 0) if ecc_ok else 0,
               "ecc_dbe_volatile": int(health["ecc.errors.uncorrected.volatile.total"] or 0) if ecc_ok else 0,
               "remapped_rows_correctable": int(health["remapped_rows.correctable"] or 0),
               "remapped_rows_uncorrectable": int(health["remapped_rows.uncorrectable"] or 0),
               "remap_pending": health["remapped_rows.pending"], "remap_failure": health["remapped_rows.failure"]}
        gh = pd.DataFrame([row])
        rank_map = [{"rank": 0, "node": host["hostname"], "local_rank": 0, "gpu_uuid": health["uuid"],
                     "gpu_bdf": health["pci.bus_id"].lower()[-12:], "numa": None, "hca": None, "rail": None}]
    else:
        row, gh, rank_map = None, pd.DataFrame(columns=["node", "gpu", "gpu_uuid", "gpu_bdf", "ecc_sbe_volatile", "ecc_dbe_volatile",
                                                        "remapped_rows_correctable", "remapped_rows_uncorrectable",
                                                        "remap_pending", "remap_failure"]), []
    actions = None
    if mod:
        try:
            acts = mod.gpu_actions(gh)
            actions = {"model": model_path, "rows": acts.to_dict("records"),
                       "decision": acts["action"].iloc[0] if len(acts) else ("healthy (no action)" if row else "no GPU rows")}
            ctx.log(f"lab gpu_actions ({model_path}): {actions['decision']}")
        except NotImplementedError as exc:
            notes.append(f"gpu_actions is not implemented yet in {model_path} ({exc}); the health decision was skipped.")

    # -------- phases
    secs = {"idle": 2.0, "gemm": 6.0, "copy": 4.0, "idle_after": 2.0} if ctx.quick else \
           {"idle": 4.0, "gemm": 25.0, "copy": 12.0, "idle_after": 6.0}
    phases = []
    sampler = NvSampler(SAMPLE_FIELDS, 200) if ctx.is_gpu else None
    if sampler:
        sampler.__enter__()
    try:
        for name, dur in secs.items():
            kind = {"gemm": "gemm", "copy": "copy"}.get(name)
            fn = phase_load(ctx, kind) if kind else None
            c0, p0, s0 = (read_counters() if ctx.is_gpu else {}), psi_cpu(), proc_stat()
            t0 = time.perf_counter()
            iters = 0
            while time.perf_counter() - t0 < dur:
                if fn:
                    fn()
                    iters += 1
                    if iters % 4 == 0:
                        ctx.sync()
                else:
                    time.sleep(0.05)
            ctx.sync()
            t1 = time.perf_counter()
            c1, p1, s1 = (read_counters() if ctx.is_gpu else {}), psi_cpu(), proc_stat()
            ph = {"phase": name, "seconds": round(t1 - t0, 2)}
            if sampler:
                w = sampler.window(t0 + (0.8 if fn else 0.3), t1)        # skip the ramp
                ph.update({"samples": len(w), "sm_mhz": med([s["clocks.sm"] for s in w]),
                           "mem_mhz": med([s["clocks.mem"] for s in w]), "power_w": med([s["power.draw"] for s in w]),
                           "temp_c_max": max([s["temperature.gpu"] for s in w if s["temperature.gpu"] is not None] or [None]),
                           "util_pct": med([s["utilization.gpu"] for s in w]),
                           "mem_util_pct": med([s["utilization.memory"] for s in w]),
                           "masks": sorted({int(s["clocks_event_reasons.active"] or 0) for s in w}),
                           "reason_share": {n: round(sum(1 for s in w if int(s["clocks_event_reasons.active"] or 0) & b) / max(1, len(w)), 3)
                                            for b, n in REASON_BITS.items()},
                           "counter_delta_s": {k: (round((c1[k] - c0[k]) / 1e6, 3) if c1.get(k) is not None and c0.get(k) is not None
                                                   else None) for k in COUNTERS},
                           "counter_regressed": any(c1.get(k) is not None and c0.get(k) is not None and c1[k] < c0[k] for k in COUNTERS)})
                ph["reason_share"] = {k: v for k, v in ph["reason_share"].items() if v}
                cap_s = ph["reason_share"].get("SW_POWER_CAP", 0) * (t1 - t0)
                cd = ph["counter_delta_s"].get("sw_power_cap")
                ph["sw_power_cap_counter_vs_samples"] = round(cd / cap_s, 3) if cap_s > 0.5 and cd is not None else None
                ph["interpretation"], ph["action"] = interpret(ph, health["clocks.max.sm"])
            else:
                busy = (1 - (s1[0] - s0[0]) / max(1, s1[1] - s0[1])) if (s0 and s1) else None
                some = ((p1["some"]["total"] - p0["some"]["total"]) / 1e6) if (p0 and p1) else None
                ph.update({"cpu_busy": round(busy, 3) if busy is not None else None,
                           "psi_some_stall_s": round(some, 3) if some is not None else None,
                           "psi_some_share": round(some / (t1 - t0), 3) if some is not None else None,
                           "psi_regressed": bool(p0 and p1 and p1["some"]["total"] < p0["some"]["total"])})
                ph["interpretation"] = ("runnable tasks waited for a CPU (PSI is VM-wide: other workloads on the host count)"
                                        if (ph["psi_some_share"] or 0) > 0.2 else "no material CPU contention")
                ph["action"] = "none"
            if fn and iters:
                ph["iterations"] = iters
            phases.append(ph)
            ctx.log(f"{name:10} " + ", ".join(f"{k}={ph[k]}" for k in ("sm_mhz", "power_w", "util_pct", "reason_share", "cpu_busy",
                                                                    "psi_some_share") if k in ph))
            del fn
            if ctx.is_gpu:
                torch.cuda.empty_cache()
    finally:
        if sampler:
            sampler.__exit__(None, None, None)

    by = {p["phase"]: p for p in phases}
    metrics = {"phases": len(phases)}
    if ctx.is_gpu:
        metrics.update({
            "remap_pending": health["remapped_rows.pending"], "remap_failure": health["remapped_rows.failure"],
            "ecc_mode": health["ecc.mode.current"], "pcie_replays_since_reset": health["pcie_replays_since_reset"],
            "gpu_recovery_action": health["gpu_recovery_action"],
            "gemm_sm_mhz": by["gemm"]["sm_mhz"], "gemm_power_w": by["gemm"]["power_w"],
            "copy_sm_mhz": by["copy"]["sm_mhz"], "copy_power_w": by["copy"]["power_w"],
            "gemm_sw_power_cap_share": by["gemm"]["reason_share"].get("SW_POWER_CAP", 0.0),
            "copy_sw_power_cap_share": by["copy"]["reason_share"].get("SW_POWER_CAP", 0.0),
            "idle_gpu_idle_share": by["idle"]["reason_share"].get("GPU_IDLE", 0.0),
            "gemm_power_cap_counter_vs_samples": by["gemm"].get("sw_power_cap_counter_vs_samples"),
            "enforced_power_limit_w": health["enforced.power.limit"], "clocks_max_sm_mhz": health["clocks.max.sm"],
            "supported_mask": health["clocks_event_reasons.supported"]})
    else:
        metrics.update({"idle_cpu_busy": by["idle"]["cpu_busy"], "gemm_cpu_busy": by["gemm"]["cpu_busy"],
                        "gemm_psi_some_share": by["gemm"]["psi_some_share"]})
    if actions:
        metrics["health_decision"] = actions["decision"]
    return {"metrics": metrics,
            "tables": {"health": {k: v for k, v in (health or {}).items() if k != "topo_m"}, "topo_m": (health or {}).get("topo_m"),
                       "host": host, "gpu_health_row": row, "rank_map": rank_map, "lab_actions": actions, "phases": phases},
            "not_runnable_parts": not_runnable, "notes": notes}


# ----------------------------------------------------------------------------------------------- check
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    by = {p["phase"]: p for p in t["phases"]}
    fails = []
    # decode self-test: the bit table must round-trip (logical invariant, both devices)
    if decode(0x1FF) != list(REASON_BITS.values()) or decode(0x4) != ["SW_POWER_CAP"]:
        fails.append("clock-event-reason decoder is wrong: check REASON_BITS against NVML nvmlClocksEventReason*")
    act = t.get("lab_actions")
    if env["device"] == "cuda":
        h = t["health"]
        sup = int(m["supported_mask"] or 0)
        for p in t["phases"]:
            bad = [x for x in p["masks"] if x & ~sup]
            if bad:
                fails.append(f"{p['phase']}: active mask {bad} has bits outside the supported mask {hex(sup)}: check the field parse")
            if p["counter_regressed"]:
                fails.append(f"{p['phase']}: a clock-event-reason counter decreased without a reset: counters are cumulative")
            if p["samples"] < 0.5 * p["seconds"]:
                fails.append(f"{p['phase']}: only {p['samples']} samples in {p['seconds']} s: check nvidia-smi -lms")
            if p["sm_mhz"] and p["sm_mhz"] > 1.01 * m["clocks_max_sm_mhz"]:
                fails.append(f"{p['phase']}: SM clock above clocks.max.sm")
            if p["reason_share"].get("SW_POWER_CAP", 0) > 0.5 and (p["power_w"] or 0) < 0.85 * (m["enforced_power_limit_w"] or 0):
                fails.append(f"{p['phase']}: SW_POWER_CAP asserted but power {p['power_w']} W is far below the "
                             f"{m['enforced_power_limit_w']} W enforced limit: check power.draw against enforced.power.limit")
        g = by["gemm"]
        if g["reason_share"].get("GPU_IDLE", 0) > 0.1 or (g["util_pct"] or 0) < 50:
            fails.append(f"GEMM phase: GPU_IDLE share {g['reason_share'].get('GPU_IDLE', 0)}, util {g['util_pct']} %: the load did not run")
        if (by["idle"]["util_pct"] or 0) == 0 and by["idle"]["reason_share"].get("GPU_IDLE", 0) < 0.5:
            fails.append("a GPU at 0 % utilization must assert GPU_IDLE: check the bitmask parse")
        if (g["power_w"] or 0) <= (by["idle"]["power_w"] or 0):
            fails.append("GEMM power not above idle power: check power.draw")
        if h.get("remapped_rows.pending") not in ("Yes", "No") or h.get("remapped_rows.failure") not in ("Yes", "No"):
            fails.append("row-remapper pending/failure did not parse as Yes/No: check nvidia-smi -q -d ROW_REMAPPER")
        if act:
            row = t["gpu_health_row"]
            want = ("quarantine_rma" if row["remap_failure"] == "Yes" or row["ecc_dbe_volatile"] > 0 else
                    "drain_reset_validate" if row["remap_pending"] == "Yes" else
                    "monitor" if row["remapped_rows_correctable"] or row["remapped_rows_uncorrectable"] else "healthy (no action)")
            if act["decision"] != want:
                fails.append(f"lab gpu_actions says {act['decision']!r} for the real row, the chapter's rule says {want!r}: check gpu_actions")
    else:
        if by["gemm"]["cpu_busy"] is not None and by["idle"]["cpu_busy"] is not None and by["gemm"]["cpu_busy"] <= by["idle"]["cpu_busy"]:
            fails.append("CPU busy under GEMM load not above idle: check /proc/stat sampling")
        if any(p.get("psi_regressed") for p in t["phases"]):
            fails.append("/proc/pressure/cpu total decreased: PSI totals are cumulative")
        if act and act["rows"]:
            fails.append("gpu_actions returned actions for an empty GPU table")
    return fails


# ----------------------------------------------------------------------------------------------- report
def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    L = []
    if gpu:
        h = t["health"]
        L += ["## Read-only health queries", "", "| Query | Value | Reading |", "|---|---|---|",
              f"| Identity | `{h['name']}`, {h['uuid']}, BDF {h['pci.bus_id']}, serial {h['serial']} | serial is [N/A] on GeForce: track the UUID |",
              f"| Firmware | VBIOS {h['vbios_version']}, InfoROM {h['inforom.img']}, driver {h['driver_version']} | record in the manifest |",
              f"| ECC | mode {h['ecc.mode.current']} | no ECC on this SKU; on HBM parts read volatile and aggregate counters |",
              f"| Row remapper | corr {h['remapped_rows.correctable']:.0f} / uncorr {h['remapped_rows.uncorrectable']:.0f}, pending "
              f"{h['remapped_rows.pending']}, failure {h['remapped_rows.failure']}; bank availability {h['bank_remap_availability']} | "
              "pending=Yes means a reset is needed before the remap takes effect (exercise K2) |",
              f"| Retired pages pending | {h['retired_pages.pending']} | pre-Ampere mechanism |",
              f"| Recovery action | {h['gpu_recovery_action']} | the driver's own recommendation |",
              f"| PCIe | Gen{h['pcie.link.gen.current']:.0f} x{h['pcie.link.width.current']:.0f}; device max Gen{h['pcie.link.gen.max']:.0f} "
              f"x{h['pcie.link.width.max']:.0f}; host max Gen{h['pcie_host_max_gen']}; replays {h['pcie_replays_since_reset']} "
              f"(rollovers {h['pcie_replay_rollovers']}) | a rising replay count is the quiet-downtrain signal (exercise T1) |", ""]
        act = t.get("lab_actions")
        if act:
            L += [f"Lab `gpu_actions` (`{act['model']}`) on this real row: **{act['decision']}**.", ""]
        L += ["`nvidia-smi topo -m`:", "", "```text", t["topo_m"] or "", "```", ""]
    else:
        hst = t["host"]
        L += ["## Read-only host health queries", "", "| Query | Value |", "|---|---|",
              f"| CPU / cores / memory | {hst['cpu']} / {hst['cpus']} / {hst['mem_gib']} GiB |",
              f"| Kernel | {hst['kernel']} |", f"| EDAC (host ECC) present | {hst['edac_present']} |",
              f"| PSI present | {hst['psi_present']} |", ""]
    L += ["## Clock-event reasons by phase" if gpu else "## Pressure-stall information by phase", ""]
    if gpu:
        L += ["| Phase | s | SM MHz | Mem MHz | Power W | Max C | Util % | Reasons (share of samples) | Counter delta (s) | Interpretation | Action |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for p in t["phases"]:
            cd = {k: v for k, v in p["counter_delta_s"].items() if v}
            L.append(f"| {p['phase']} | {p['seconds']} | {p['sm_mhz']} | {p['mem_mhz']} | {p['power_w']} | {p['temp_c_max']} | {p['util_pct']} | "
                     f"{p['reason_share'] or 'none'} | {cd or 0} | {p['interpretation']} | {p['action']} |")
        lim = m["enforced_power_limit_w"]
        L += ["", "## What to conclude", "",
              f"- Under the GEMM soak the GPU sits at its **{lim:.0f} W enforced limit** with `SW_POWER_CAP` in "
              f"{100 * m['gemm_sw_power_cap_share']:.0f} % of samples and the SM clock at {m['gemm_sm_mhz']} MHz, below the "
              f"{m['clocks_max_sm_mhz']:.0f} MHz maximum. That is normal operation, not a fault (Section 19.3, "Thermal and power events"): the clock that matters is "
              "the *sustained* clock compared with the GPU's peers.",
              f"- The memory-bound copy soak draws {m['copy_power_w']} W with `SW_POWER_CAP` in {100 * m['copy_sw_power_cap_share']:.0f} % "
              "of samples: the reason depends on the workload, so compare like with like.",
              "- A thermal or power-brake reason would change the action from \"none\" to \"drain and inspect\". A rising PCIe replay "
              "count, or a link below its maximum under load, is a hardware signal even when no job has failed yet.",
              f"- The driver's `sw_power_cap` counter advanced by {m['gemm_power_cap_counter_vs_samples']} x the time the sampled bit "
              "said the cap was active. A ratio well below 1 means the counter lags or is not maintained on this platform (WSL2), so "
              "the sampled bitmask is the evidence here. A report must say which source it used.",
              "- Right after a load ends, clocks and power take seconds to decay and `GPU_IDLE` is not yet asserted in every sample "
              "(the `idle_after` row). An idle health snapshot taken too early looks like a busy GPU.",
              "- This is a **laptop Ada GPU** with an 80 W-class limit, not an H100 at 700 W. The reason codes and the decision rules "
              "transfer; the clock and power values do not."]
    else:
        L += ["| Phase | s | CPU busy | PSI some stall (s) | share of wall time | Interpretation |", "|---|---|---|---|---|---|"]
        for p in t["phases"]:
            L.append(f"| {p['phase']} | {p['seconds']} | {p['cpu_busy']} | {p['psi_some_stall_s']} | {p['psi_some_share']} | {p['interpretation']} |")
        L += ["", "_CPU fallback: no GPU was visible, so there are no clock-event reasons, no row remapper and no PCIe link to read. "
              "The host-side health queries ran read-only, and PSI stands in for \"why is this device slower than it could be\". "
              "GPU-only invariants were skipped._"]
    L += ["", "## Not runnable on this host", "", "| Part | Probe | Needs |", "|---|---|---|"]
    L += [f"| {p['part']} | {p['probe']} | {', '.join(p['needs'])} |" for p in result.get("not_runnable_parts", [])]
    return "\n".join(L)
