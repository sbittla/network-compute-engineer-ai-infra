"""Capstone E L2: a real node burn-in and acceptance run, gated by the L1 evaluate_acceptance().

What it teaches (starter-kit README section 8.2; manuscript Ch 16 fleet lifecycle, Ch 22 acceptance):
acceptance evidence is produced by tools, converted into the schema the controller understands, and
gated by the *unchanged* policy code. On this host the experiment
  1. reads inventory and health read-only (nvidia-smi: VBIOS, driver, PCIe link, ECC, row remapping,
     clock-event-reason counters),
  2. measures host->device bandwidth (pinned, the nvbandwidth H2D case) and device memory bandwidth,
  3. runs a sustained FP16 GEMM burn-in while sampling power, SM clock, temperature, PCIe link and
     clock-event reasons through nvidia-smi, and reports throughput stability window by window,
  4. measures a storage read (the fio sequential-read case) with the page cache dropped for the file,
  5. writes all of it as an ``acceptance_results.json`` record and runs the L1 ``evaluate_acceptance()``
     twice: against the ORION HX8 policy (which a laptop must fail, and the report says on which
     checks) and against a single-GPU calibration policy derived from this host's own link and specs.
     Checks whose evidence cannot be collected here are listed as *not gated*, not silently passed.

Not runnable here: DCGM level-3 diagnostics, NVLink P2P bandwidth, nccl-tests across 8 GPUs, RDMA NIC
link/bandwidth, BMC/Redfish inventory, kernel Xid log (dmesg is not readable in the container), ECC
(not supported on this GPU), and provisioning/scheduler integration (L3). Each is probed.

CPU fallback: the same burn-in as a sustained FP32 GEMM on the CPU, host memory copy bandwidth, the
storage read, and the same record and gate (GPU-specific fields empty). GPU-only invariants are skipped.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import os
import re
import shutil
import statistics
import subprocess
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-e-l2",
    "title": "Capstone E L2: node burn-in and acceptance evidence through the L1 gate",
    "evidence": "MEASURED",
    "cpu_fallback": ("sustained FP32 GEMM burn-in on the CPU with throughput stability, host-memory copy bandwidth and a "
                     "storage read, converted into the acceptance schema and gated by evaluate_acceptance(); GPU telemetry, "
                     "PCIe and GPU health fields are empty and reported as not collectible"),
}

PKG = Path(__file__).resolve().parents[2]
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4090": 384, "rtx 3090": 384}
PCIE_GBS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}
REASONS = {0x1: "idle", 0x2: "app_clocks", 0x4: "sw_power_cap", 0x8: "hw_slowdown", 0x10: "sync_boost",
           0x20: "sw_thermal", 0x40: "hw_thermal", 0x80: "hw_power_brake", 0x100: "display_clocks"}
TELEMETRY = ["power.draw", "clocks.sm", "clocks.mem", "temperature.gpu", "utilization.gpu", "clocks_event_reasons.active",
             "pcie.link.gen.current", "pcie.link.width.current", "memory.used"]


def load_l1(name: str):
    for p in (PKG / "instructor" / "reference" / f"{name}.py", PKG / "starter-kit" / "starter" / f"{name}.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, p.relative_to(PKG).as_posix()
    return None, None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)


def utc(t: float | None = None) -> str:
    return dt.datetime.fromtimestamp(t if t is not None else time.time(), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Telemetry:
    """nvidia-smi sampled in the background (``-lms``); rows are parsed numbers plus a monotonic timestamp."""

    def __init__(self, interval_ms: int = 250):
        self.interval_ms, self.rows, self.p = interval_ms, [], None

    def __enter__(self):
        if shutil.which("nvidia-smi"):
            self.p = subprocess.Popen(["nvidia-smi", f"--query-gpu={','.join(TELEMETRY)}", "--format=csv,noheader,nounits",
                                       "-lms", str(self.interval_ms)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self.t = threading.Thread(target=self._read, daemon=True)
            self.t.start()
        return self

    def _read(self):
        for line in self.p.stdout:
            vals = [v.strip() for v in line.split(",")]
            if len(vals) == len(TELEMETRY):
                row = {k: (int(v, 16) if k.startswith("clocks_event") and v.startswith("0x") else num(v)) for k, v in zip(TELEMETRY, vals)}
                row["t"] = time.monotonic()
                self.rows.append(row)

    def __exit__(self, *a):
        if self.p:
            self.p.terminate()
            try:
                self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.p.kill()
            self.t.join(timeout=2)
        return False


def stats(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return {"n": len(xs), "median": statistics.median(xs), "p95": xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))],
            "min": xs[0], "max": xs[-1]}


# ---------------------------------------------------------------------------------- read-only health
def inventory() -> dict:
    """Read-only node inventory and health, as the README's L2 command list asks (what exists here)."""
    q = ["index", "uuid", "pci.bus_id", "vbios_version", "driver_version", "temperature.gpu",
         "ecc.errors.uncorrected.volatile.total", "ecc.errors.corrected.volatile.total", "pcie.link.gen.current",
         "pcie.link.gen.max", "pcie.link.width.current", "pcie.link.width.max", "power.max_limit", "enforced.power.limit",
         "clocks.max.sm", "name"]
    gpus = []
    if shutil.which("nvidia-smi"):
        _, out = sh(["nvidia-smi", f"--query-gpu={','.join(q)}", "--format=csv,noheader,nounits"])
        for line in out.splitlines():
            vals = [v.strip() for v in line.split(",")]
            if len(vals) == len(q):
                gpus.append(dict(zip(q, vals)))
        _, rr = sh(["nvidia-smi", "-q", "-d", "ROW_REMAPPER"])
        _, perf = sh(["nvidia-smi", "-q", "-d", "PERFORMANCE"])
        _, temp = sh(["nvidia-smi", "-q", "-d", "TEMPERATURE"])
        _, topo = sh(["nvidia-smi", "topo", "-m"])
    else:
        rr = perf = temp = topo = ""
    remap = {"pending": [], "failure": [], "correctable": [], "uncorrectable": []}
    for m in re.finditer(r"Pending\s*:\s*(\w+)", rr):
        remap["pending"].append(0 if m.group(1).lower() == "no" else 1)
    for m in re.finditer(r"Remapping Failure Occurred\s*:\s*(\w+)", rr):
        remap["failure"].append(0 if m.group(1).lower() == "no" else 1)
    for k, pat in (("correctable", r"Correctable Error\s*:\s*(\d+)"), ("uncorrectable", r"Uncorrectable Error\s*:\s*(\d+)")):
        remap[k] = [int(x) for x in re.findall(pat, rr)]
    counters = {k.strip().lower().replace(" ", "_"): int(v) for k, v in re.findall(r"^\s+([A-Za-z ]+?)\s*:\s*(\d+) us", perf, re.M)}
    target = re.search(r"GPU Target Temperature\s*:\s*(\d+) C", temp)
    probes = {
        "dcgmi": bool(shutil.which("dcgmi")), "nvbandwidth": bool(shutil.which("nvbandwidth")),
        "all_reduce_perf": bool(shutil.which("all_reduce_perf")), "fio": bool(shutil.which("fio")),
        "ibv_devinfo": bool(shutil.which("ibv_devinfo")), "ethtool": bool(shutil.which("ethtool")),
        "rdma_devices": sorted(os.listdir("/sys/class/infiniband")) if Path("/sys/class/infiniband").is_dir() else [],
        "net_interfaces": sorted(os.listdir("/sys/class/net")) if Path("/sys/class/net").is_dir() else [],
        "dmesg_readable": sh(["dmesg"])[0] == 0, "redfish_bmc": bool(os.environ.get("BMC_HOST")),
        "ipmitool": bool(shutil.which("ipmitool")), "nvlink": "NV" in topo.split("Legend")[0] if topo else False,
    }
    return {"gpus": gpus, "row_remap": remap, "event_reason_counters_us": counters,
            "target_temp_c": int(target.group(1)) if target else None, "probes": probes}


# ---------------------------------------------------------------------------------- measurements
def gbs(t: dict, nbytes: int) -> dict:
    """GB/s from time statistics: median, worst repetition (longest time) and best repetition."""
    return {"median": nbytes / t["median"] / 1e9, "worst": nbytes / t["max"] / 1e9, "best": nbytes / t["min"] / 1e9}


def bandwidth(ctx) -> dict:
    torch = ctx.torch
    n = (64 if ctx.quick else 256) * 2 ** 20
    out = {}
    if ctx.is_gpu:
        host = torch.empty(n, dtype=torch.uint8).pin_memory()
        dev = torch.empty(n, dtype=torch.uint8, device="cuda")
        dev2 = torch.empty_like(dev)
        h2d = ctx.bench(lambda: dev.copy_(host, non_blocking=True), reps=ctx.reps(10))
        d2h = ctx.bench(lambda: host.copy_(dev, non_blocking=True), reps=ctx.reps(10))
        d2d = ctx.bench(lambda: dev2.copy_(dev), reps=ctx.reps(10))
        out = {"h2d": h2d, "d2h": d2h, "d2d": d2d}
        out["h2d_gbs"], out["d2h_gbs"], out["d2d_gbs"] = gbs(h2d, n), gbs(d2h, n), gbs(d2d, 2 * n)
        # Worst repetition = longest time -> the 'min' GB/s the policy gates on.
        out["h2d_gbs_worst"] = n / h2d["max"] / 1e9
    else:
        a, b = torch.empty(n, dtype=torch.uint8), torch.empty(n, dtype=torch.uint8)
        cp = ctx.bench(lambda: b.copy_(a), reps=ctx.reps(10))
        out = {"host_copy": cp, "host_copy_gbs": gbs(cp, 2 * n)}
    out["bytes"] = n
    return out


def storage_read(ctx) -> dict:
    """fio-style sequential read of a fresh file, with the page cache dropped for it (posix_fadvise DONTNEED)."""
    size = (64 if ctx.quick else 512) * 2 ** 20
    path = Path("/tmp/acceptance_seqread.bin")
    block = os.urandom(2 ** 20)
    with open(path, "wb") as f:
        for _ in range(size // len(block)):
            f.write(block)
        f.flush()
        os.fsync(f.fileno())
    rates = []
    for _ in range(ctx.reps(5)):
        fd = os.open(path, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            t0 = time.perf_counter()
            while os.read(fd, 1 << 20):
                pass
            rates.append(size / (time.perf_counter() - t0) / 1e9)
        finally:
            os.close(fd)
    path.unlink(missing_ok=True)
    fs = "unknown"
    try:
        for line in Path("/proc/mounts").read_text().splitlines():
            parts = line.split()
            if parts[1] == "/":
                fs = parts[2]
    except OSError:
        pass
    return {"bytes": size, "gbs": stats(rates), "fs": fs, "block": "1 MiB", "note": "cache dropped per read with POSIX_FADV_DONTNEED"}


def burn_in(ctx, seconds: float) -> dict:
    """Sustained GEMM load; throughput per ~1 s window with device timing, telemetry sampled alongside."""
    torch = ctx.torch
    if ctx.is_gpu:
        n, dtype = 4096, torch.float16
    else:
        n, dtype = 1024, torch.float32
    a = torch.randn(n, n, device=ctx.device, dtype=dtype)
    b = torch.randn(n, n, device=ctx.device, dtype=dtype)
    c = torch.empty_like(a)
    for _ in range(5):
        torch.matmul(a, b, out=c)
    ctx.sync()
    # calibrate the batch so one window is ~1 s
    t0 = time.perf_counter()
    for _ in range(10):
        torch.matmul(a, b, out=c)
    ctx.sync()
    per = (time.perf_counter() - t0) / 10
    batch = max(1, int(1.0 / per))
    windows = []
    idle = None
    with Telemetry(250) as tel:
        time.sleep(0.8)
        idle = list(tel.rows)
        t_start = time.monotonic()
        while time.monotonic() - t_start < seconds:
            if ctx.is_gpu:
                e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                e0.record()
                for _ in range(batch):
                    torch.matmul(a, b, out=c)
                e1.record()
                torch.cuda.synchronize()
                dur = e0.elapsed_time(e1) / 1000
            else:
                w0 = time.perf_counter()
                for _ in range(batch):
                    torch.matmul(a, b, out=c)
                dur = time.perf_counter() - w0
            windows.append({"t_s": time.monotonic() - t_start, "dur_s": dur, "tflops": 2 * n ** 3 * batch / dur / 1e12})
        t_end = time.monotonic()
        time.sleep(0.3)
    load = [r for r in tel.rows if t_start + 1.0 <= r["t"] <= t_end]   # skip the first second (clock ramp)
    tf = [w["tflops"] for w in windows]
    k = max(1, len(tf) // 4)
    reasons = {}
    for r in load:
        mask = int(r.get("clocks_event_reasons.active") or 0)
        for bit, name in REASONS.items():
            if mask & bit:
                reasons[name] = reasons.get(name, 0) + 1
    return {"seconds": t_end - t_start, "gemm_n": n, "dtype": str(dtype), "batch_per_window": batch, "windows": windows,
            "tflops": stats(tf), "first_quarter_tflops": statistics.median(tf[:k]), "last_quarter_tflops": statistics.median(tf[-k:]),
            "cv": (statistics.pstdev(tf) / statistics.fmean(tf)) if len(tf) > 1 else 0.0,
            "telemetry": {f: stats([r[f] for r in load]) for f in ("power.draw", "clocks.sm", "clocks.mem", "temperature.gpu",
                                                                   "utilization.gpu", "pcie.link.gen.current", "pcie.link.width.current")},
            "idle_pcie_gen": stats([r["pcie.link.gen.current"] for r in idle]) if idle else None,
            "idle_power_w": stats([r["power.draw"] for r in idle]) if idle else None,
            "event_reason_share": {k2: v / len(load) for k2, v in reasons.items()} if load else {},
            "n_samples": len(load)}


# ---------------------------------------------------------------------------------- acceptance record and gate
def acceptance_record(ctx, inv, bw, st, bi, started, image_done) -> dict:
    gpus = inv["gpus"]
    to_i = lambda v: int(num(v)) if num(v) is not None else 0  # noqa: E731
    load_gen = bi["telemetry"]["pcie.link.gen.current"]
    load_width = bi["telemetry"]["pcie.link.width.current"]
    tests = {
        "gpu_count": len(gpus),
        # read under load (README pitfall: links downshift when idle)
        "gpu_pcie": [{"gpu": to_i(g["index"]), "gen": int(load_gen["max"]) if load_gen else to_i(g["pcie.link.gen.current"]),
                      "width": int(load_width["max"]) if load_width else to_i(g["pcie.link.width.current"])} for g in gpus],
        "nic_pcie": [], "nic_link_gbps": [],
        "ecc_uncorrected_volatile": [to_i(g["ecc.errors.uncorrected.volatile.total"]) for g in gpus if num(g["ecc.errors.uncorrected.volatile.total"]) is not None],
        "ecc_corrected_volatile": [to_i(g["ecc.errors.corrected.volatile.total"]) for g in gpus if num(g["ecc.errors.corrected.volatile.total"]) is not None],
        "row_remap_pending": inv["row_remap"]["pending"], "row_remap_failure": inv["row_remap"]["failure"],
        "dcgm_diag_level3": "not-run", "nvlink_p2p_GBps_min": 0.0,
        "h2d_GBps_min": round(bw["h2d_gbs_worst"], 2) if ctx.is_gpu else 0.0,
        "rdma_write_Gbps_min": 0.0, "storage_read_GBps": round(st["gbs"]["min"], 3),
        "burn_in_hours": round(bi["seconds"] / 3600, 5),
        "gpu_temp_max_c": bi["telemetry"]["temperature.gpu"]["max"] if bi["telemetry"]["temperature.gpu"] else 0.0,
        "xid_events": [],
    }
    return {"node": os.uname().nodename if hasattr(os, "uname") else "localhost", "image_completed_utc": image_done,
            "started_utc": started, "completed_utc": utc(), "tests": tests}


def local_policy(orion: dict, inv: dict, bi: dict, ctx) -> tuple[dict, dict]:
    """A calibration policy for this single-GPU host: link expectations from nvidia-smi's max fields, H2D floor at
    60 % of the negotiated link, burn-in at least the run length. Checks without evidence here are not gated
    (thresholds neutralised) and listed, so the report never presents them as passed."""
    p = dict(orion)
    g = inv["gpus"][0] if inv["gpus"] else {}
    gen, width = int(num(g.get("pcie.link.gen.max")) or 0), int(num(g.get("pcie.link.width.max")) or 0)
    p.update({"policy_version": "local-single-gpu-calibration", "expected_gpus": len(inv["gpus"]), "expected_nics": 0,
              "pcie_min_gen": gen, "pcie_min_width": width,
              "h2d_GBps_min": round(0.6 * PCIE_GBS_PER_LANE.get(gen, 0) * width, 2) if ctx.is_gpu else 0.0,
              "storage_read_GBps_min": 0.2, "burn_in_hours_min": round(bi["seconds"] / 3600 * 0.99, 5),
              "gpu_temp_max_c": float(inv["target_temp_c"] or orion["gpu_temp_max_c"])})
    not_gated = {
        "dcgm_diag": "dcgmi not installed (DCGM absent on this host)",
        "nvlink_bw": "no NVLink on a single PCIe GPU",
        "rdma_bw": "no RDMA NIC (/sys/class/infiniband absent)",
        "nic_pcie_link / nic_link_speed": "no backend NIC visible (container network: " + ",".join(inv["probes"]["net_interfaces"]) + ")",
        "xid_events": "kernel log not readable in the container (dmesg: Operation not permitted)",
        "ecc_uncorrected": "ECC not supported/enabled on this GPU (nvidia-smi reports N/A)" if ctx.is_gpu else "no GPU",
    }
    p.update({"dcgm_diag_required": "not-run", "nvlink_p2p_GBps_min": 0.0, "rdma_write_Gbps_min": 0.0})
    if not ctx.is_gpu:
        p["policy_version"] = "local-cpu-host-calibration"
        not_gated.update({"gpu_count": "no GPU: expected_gpus set to 0 for a CPU-only host", "gpu_pcie_link": "no GPU", "h2d_bw": "no GPU", "thermal": "no GPU temperature sensor read", "row_remap": "no GPU"})
        p.update({"pcie_min_gen": 0, "pcie_min_width": 0})
    return p, not_gated


def run(ctx) -> dict:
    torch = ctx.torch
    if not ctx.is_gpu:
        torch.set_num_threads(min(8, os.cpu_count() or 1))
    image_done = utc(Path("/proc/1").stat().st_ctime) if Path("/proc/1").exists() else utc()
    started = utc()
    inv = inventory()
    bw = bandwidth(ctx)
    st = storage_read(ctx)
    secs = 8.0 if ctx.quick else 90.0
    bi = burn_in(ctx, secs)
    inv_after = inventory()
    ctx.log(f"burn-in {bi['seconds']:.0f} s: {bi['tflops']['median']:.2f} TFLOP/s median (first/last quarter "
            f"{bi['first_quarter_tflops']:.2f}/{bi['last_quarter_tflops']:.2f}), CV {bi['cv']:.3f}")
    rec = acceptance_record(ctx, inv, bw, st, bi, started, image_done)
    import yaml
    orion = yaml.safe_load(open(PKG / "starter-kit" / "data" / "acceptance_policy.yaml", encoding="utf-8"))
    lp, not_gated = local_policy(orion, inv, bi, ctx)
    fleet, src = load_l1("fleet")
    gate = {"available": False}
    if fleet is not None:
        try:
            gate = {"available": True, "source": src, "orion": fleet.evaluate_acceptance(rec, orion),
                    "local": fleet.evaluate_acceptance(rec, lp)}
        except NotImplementedError as e:
            gate = {"available": False, "why": f"starter fleet.evaluate_acceptance not implemented yet ({e})"}
    counters_delta = {k: inv_after["event_reason_counters_us"].get(k, 0) - v for k, v in inv["event_reason_counters_us"].items()}
    pr = inv["probes"]
    nr = [{"part": "DCGM level-3 diagnostics (dcgmi diag -r 3)", "probe": f"dcgmi on PATH={pr['dcgmi']}", "needs": ["DCGM installed, data-center GPU"]},
          {"part": "nvbandwidth device<->device / NVLink P2P", "probe": f"nvbandwidth={pr['nvbandwidth']}, NVLink in topo={pr['nvlink']}, GPUs={len(inv['gpus'])}",
           "needs": ["2+ NVLink-connected GPUs"]},
          {"part": "nccl-tests intra-node bus bandwidth (-g 8)", "probe": f"all_reduce_perf={pr['all_reduce_perf']}, GPUs={len(inv['gpus'])}", "needs": ["8-GPU node"]},
          {"part": "RDMA NIC link speed, PCIe and ib_write_bw (L3)", "probe": f"/sys/class/infiniband={pr['rdma_devices'] or 'none'}, ibv_devinfo={pr['ibv_devinfo']}",
           "needs": ["RDMA NICs", "second node on the same rail"]},
          {"part": "Redfish/IPMI out-of-band inventory", "probe": f"BMC_HOST set={pr['redfish_bmc']}, ipmitool={pr['ipmitool']}", "needs": ["BMC with a read-only account"]},
          {"part": "Kernel Xid scan (dmesg | grep -i xid)", "probe": f"dmesg readable={pr['dmesg_readable']}", "needs": ["host kernel log access (root)"]},
          {"part": "provisioning (Ironic/MAAS/Metal3) and scheduler drain/undrain (L3)", "probe": "single container, no lab provisioner",
           "needs": ["lab provisioning system", "lab Slurm or Kubernetes"]}]
    metrics = {"burnin_tflops_median": round(bi["tflops"]["median"], 3), "burnin_cv": round(bi["cv"], 4),
               "storage_read_gbs_min": round(st["gbs"]["min"], 3)}
    if ctx.is_gpu:
        metrics.update({"h2d_gbs_median": round(bw["h2d_gbs"]["median"], 2), "d2d_gbs_median": round(bw["d2d_gbs"]["median"], 1),
                        "power_w_median": bi["telemetry"]["power.draw"]["median"] if bi["telemetry"]["power.draw"] else None,
                        "temp_c_max": rec["tests"]["gpu_temp_max_c"]})
    if gate.get("available"):
        metrics.update({"orion_policy_passed": gate["orion"]["passed"], "local_policy_passed": gate["local"]["passed"]})
    return {"metrics": metrics, "inventory": inv, "bandwidth": bw, "storage": st, "burn_in": bi,
            "event_reason_counters_delta_us": counters_delta, "acceptance_record": rec, "policies": {"orion": orion, "local": lp},
            "not_gated": not_gated, "gate": gate, "not_runnable_parts": nr,
            "notes": ["Burn-in windows are ~1 s of back-to-back GEMMs timed with CUDA events (GPU) or perf_counter (CPU); "
                      "telemetry sampled every 250 ms by nvidia-smi -lms; the first second of load is excluded (clock ramp).",
                      f"Burn-in length {bi['seconds']:.0f} s (quick mode 8 s): a real acceptance burn-in is >= 12 h (policy "
                      f"burn_in_hours_min {orion['burn_in_hours_min']}). This run calibrates the tooling, not the node.",
                      "Bandwidth: >= 5 repetitions after 3 warm-ups; the policy gates on the worst repetition (h2d_GBps_min).",
                      "This record is evidence from ONE node: the README asks for calibration on >= 2 known-good nodes "
                      "before any threshold is trusted."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    bi = result["burn_in"]
    if len(bi["windows"]) < 5:
        fails.append(f"only {len(bi['windows'])} burn-in windows: the burn-in did not run long enough to judge stability")
    if bi["tflops"]["min"] <= 0:
        fails.append("non-positive burn-in throughput")
    st = result["storage"]["gbs"]
    if st["min"] <= 0:
        fails.append("storage read rate is not positive")
    g = result.get("gate", {})
    if g.get("available") and g["orion"]["passed"] and result["acceptance_record"]["tests"]["gpu_count"] != 8:
        fails.append("the ORION policy accepted a node without 8 GPUs: evaluate_acceptance is not gating gpu_count")
    if env["device"] == "cuda":
        gp = (env.get("gpus") or [{}])[0]
        sm, clk = env.get("gpu0", {}).get("sm_count"), num(gp.get("clocks.max.sm"))
        if sm and clk and bi["tflops"]["max"] * 1e12 > 1.05 * sm * 512 * clk * 1e6:
            fails.append(f"burn-in {bi['tflops']['max']:.1f} TFLOP/s exceeds the FP16 tensor peak "
                         f"{sm * 512 * clk / 1e6:.1f} TFLOP/s (SMs x 512 FLOP/clk x clocks.max.sm): check the FLOP count")
        try:
            ceiling = PCIE_GBS_PER_LANE[int(gp["pcie.link.gen.max"])] * int(gp["pcie.link.width.max"])
        except (KeyError, ValueError):
            ceiling = None
        bw = result["bandwidth"]
        if ceiling and bw["h2d_gbs"]["best"] > 1.05 * ceiling:
            fails.append(f"H2D {bw['h2d_gbs']['best']:.1f} GB/s exceeds the PCIe ceiling {ceiling:.1f} GB/s")
        name, mclk = (gp.get("name") or "").lower(), num(gp.get("clocks.max.memory"))
        bits = next((b for k, b in BUS_BITS.items() if k in name), None)
        if bits and mclk and bw["d2d_gbs"]["best"] * 1e9 > 1.05 * 2 * mclk * 1e6 * bits / 8:
            fails.append("device copy bandwidth exceeds the memory peak: copy too small (L2-resident) or timer wrong")
        tel = bi["telemetry"]
        if bi["n_samples"] < 5 or not tel["power.draw"]:
            fails.append(f"only {bi['n_samples']} telemetry samples during the burn-in: check that nvidia-smi -lms works in the container")
        else:
            pmax = num(gp.get("power.max_limit"))
            if pmax and tel["power.draw"]["median"] > 1.05 * pmax:
                fails.append(f"median power {tel['power.draw']['median']:.0f} W exceeds power.max_limit {pmax:.0f} W: telemetry is wrong")
            if clk and tel["clocks.sm"]["max"] > 1.02 * clk:
                fails.append("SM clock above clocks.max.sm: telemetry parse error")
            idle = bi.get("idle_power_w")
            if idle and tel["power.draw"]["median"] <= idle["median"]:
                fails.append("power under load is not above idle: the burn-in did not load the GPU (check device placement)")
            if tel["utilization.gpu"]["median"] < 50:
                fails.append(f"GPU utilization median {tel['utilization.gpu']['median']:.0f} % during burn-in: load is not sustained")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    bi, bw, st, rec = result["burn_in"], result["bandwidth"], result["storage"], result["acceptance_record"]
    L = ["## Read-only inventory and health", ""]
    if result["inventory"]["gpus"]:
        L += ["| GPU | UUID | bus | VBIOS | driver | PCIe max | ECC uncorr. | row remap pending/failed |", "|---|---|---|---|---|---|---|---|"]
        rr = result["inventory"]["row_remap"]
        for g in result["inventory"]["gpus"]:
            L.append(f"| {g['index']} {g['name']} | {g['uuid'][:13]}... | {g['pci.bus_id']} | {g['vbios_version']} | {g['driver_version']} | "
                     f"Gen{g['pcie.link.gen.max']} x{g['pcie.link.width.max']} | {g['ecc.errors.uncorrected.volatile.total']} | "
                     f"{rr['pending']}/{rr['failure']} |")
    else:
        L.append("No GPU visible (CPU fallback).")
    L += ["", f"## Burn-in ({bi['seconds']:.0f} s sustained {bi['dtype']} GEMM n={bi['gemm_n']}, ~1 s windows)", "",
          "| Metric | median | p95 | min | max |", "|---|---|---|---|---|",
          f"| TFLOP/s per window | {bi['tflops']['median']:.2f} | {bi['tflops']['p95']:.2f} | {bi['tflops']['min']:.2f} | {bi['tflops']['max']:.2f} |"]
    for k, label in (("power.draw", "power (W)"), ("clocks.sm", "SM clock (MHz)"), ("clocks.mem", "memory clock (MHz)"),
                     ("temperature.gpu", "temperature (C)"), ("utilization.gpu", "utilization (%)"), ("pcie.link.gen.current", "PCIe gen (under load)")):
        x = bi["telemetry"].get(k)
        if x:
            L.append(f"| {label} | {x['median']:.0f} | {x['p95']:.0f} | {x['min']:.0f} | {x['max']:.0f} |")
    L += ["", f"Throughput first vs last quarter: {bi['first_quarter_tflops']:.2f} -> {bi['last_quarter_tflops']:.2f} TFLOP/s; "
          f"window CV {bi['cv'] * 100:.1f} %."]
    if gpu:
        share = ", ".join(f"{k} {v * 100:.0f} %" for k, v in sorted(bi["event_reason_share"].items())) or "none"
        deltas = ", ".join(f"{k} {v}" for k, v in result["event_reason_counters_delta_us"].items() if v)
        L.append(f"Clock-event reasons active during load (share of samples): {share}. Cumulative counter deltas over the run (us): "
                 + (deltas + "." if deltas else "none recorded: the counters did not advance within this short window "
                    "(the driver refreshes them periodically on this platform), so the sampled reason bitmask is the evidence."))
        if bi.get("idle_pcie_gen") and bi["telemetry"].get("pcie.link.gen.current"):
            L.append(f"PCIe link generation idle -> under load: Gen{bi['idle_pcie_gen']['median']:.0f} -> "
                     f"Gen{bi['telemetry']['pcie.link.gen.current']['max']:.0f}. This is the README's pitfall: read link state under load.")
    L += ["", "## Bandwidth and storage (>= 5 repetitions)", "", "| Test | median | worst rep | best rep |", "|---|---|---|---|"]
    if gpu:
        for k, label in (("h2d_gbs", "H2D pinned (GB/s)"), ("d2h_gbs", "D2H pinned (GB/s)"), ("d2d_gbs", "device copy (GB/s, r+w)")):
            L.append(f"| {label} | {bw[k]['median']:.1f} | {bw[k]['worst']:.1f} | {bw[k]['best']:.1f} |")
    else:
        L.append(f"| host memory copy (GB/s, r+w) | {bw['host_copy_gbs']['median']:.1f} | {bw['host_copy_gbs']['worst']:.1f} | {bw['host_copy_gbs']['best']:.1f} |")
    L.append(f"| sequential read, {st['bytes'] >> 20} MiB on {st['fs']} (GB/s) | {st['gbs']['median']:.2f} | {st['gbs']['min']:.2f} | {st['gbs']['max']:.2f} |")
    g = result["gate"]
    L += ["", "## Acceptance gate (L1 `evaluate_acceptance()`, unchanged)", ""]
    if g.get("available"):
        L += [f"Source: `{g['source']}`. Record written in the `acceptance_results.json` schema (see results.json, `acceptance_record`).", "",
              "| Policy | passed | failing checks |", "|---|---|---|",
              f"| {result['policies']['orion']['policy_version']} (ORION HX8) | {g['orion']['passed']} | {', '.join(g['orion']['failures']) or '-'} |",
              f"| {result['policies']['local']['policy_version']} (this host) | {g['local']['passed']} | {', '.join(g['local']['failures']) or '-'} |",
              "", "Not gated in the local policy (no evidence can be collected here; never counted as passed):", ""]
        L += [f"- `{k}`: {v}" for k, v in result["not_gated"].items()]
    else:
        L.append(f"Gate skipped: {g.get('why', 'no L1 fleet model found')}")
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}.")
    L += ["", "## What to conclude", "",
          "- The ORION policy correctly rejects this host. A laptop is not an HX8 node: wrong GPU count, a Gen4 x8 link, no NICs, "
          "and no DCGM. That rejection is the gate working.",
          "- A burn-in is judged on stability (first vs last quarter, window CV, clock-event reasons, temperature), not on one "
          "peak number. Power-cap or thermal reasons that appear only late in the run are exactly what a short test misses.",
          "- Thresholds are calibrations: derive them from repeated runs on >= 2 known-good nodes of the *same* SKU, as the local "
          "policy here does for one node, and keep the checks you cannot evidence visibly ungated."]
    if gpu:
        L.append("- This is a **laptop Ada GPU (RTX 4060 class, ~80 W enforced limit), not an H100**: compare behaviour, not numbers.")
    else:
        L.append("- _CPU fallback: no GPU was used. GPU telemetry, PCIe, peak-FLOP and memory-peak invariants were skipped._")
    return "\n".join(L)
