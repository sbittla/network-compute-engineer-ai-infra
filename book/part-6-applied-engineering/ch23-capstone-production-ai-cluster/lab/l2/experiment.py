"""Ch 23 L2: validate the bundle's node-level assumptions against the node this runs on, and lint the new evidence.

The chapter's L2 extension takes the design bundle's node-level assumptions (A-01 GPU peak, A-02 GPU
memory, A-03 node power, A-10 RoCE MTU, the GPU-NIC affinity, the NUMA layout) and checks them on a real
GPU host with ``nvidia-smi``, ``topo -m``, ``numactl``, ``ibv_devinfo`` and a BMC power reading under
sustained load. This experiment does that for every assumption this host can answer:

* **A-01** dense tensor throughput: an FP16 and a BF16 GEMM sweep, best of three sizes, against this
  GPU's own peak (SM count x Ada per-SM rate x clock). The achieved fraction is the realistic ceiling for
  the bundle's MFU assumption **A-04**.
* **A-02** GPU memory: ``nvidia-smi memory.total`` against what CUDA reports.
* **A-03** node power: GPU board power under the GEMM load (``nvidia-smi``, 100 ms). Node (PDU/BMC) power
  is not measurable here and is recorded as such.
* **A-08 / B-03** checkpoint write: a GPU state of fixed size copied to host and written with
  ``torch.save`` + ``fsync``, then read back and verified bit for bit (>= 5 repetitions).
* **A-10**, GPU-NIC affinity, NUMA: probed (no RDMA NIC, so A-10 cannot be validated here).

It then writes the measured rows into a copy of the reference bundle's ``benchmarks.md`` as
``MEASURED`` / tier ``L2`` with this run's manifest, and runs the lab's own ``check_evidence`` on it. The
new rows must pass EVID-001..004, and two negative controls (the same row at tier L1, and one with no
manifest) must fire EVID-004 and EVID-003.

This is a laptop Ada GPU, not an HX8 node. The experiment validates the *method* and shows how an
acceptance check flags a node that does not match the bundle (8 GB is not 80 GB).

CPU fallback: A-01 becomes an FP32 CPU GEMM; A-02 the host memory; the checkpoint test writes host
tensors; GPU power is not measurable. The lint step is identical.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch23-l2",
    "title": "Lab 23 L2: node-level bundle assumptions validated on this host, new evidence linted",
    "evidence": "MEASURED",
    "cpu_fallback": ("A-01 as an FP32 CPU GEMM, A-02 as host memory, the checkpoint write/verify on host tensors, no power "
                     "reading; the benchmarks.md lint step is identical"),
}

PKG = Path(__file__).resolve().parents[2]
ADA_FP16_TENSOR_FLOP_PER_CLK_SM = 512  # Ada whitepaper: RTX 4090 165.2 TFLOP/s FP16 (FP32 acc) / (128 SM x 2.52 GHz)


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip("\n")
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
            except Exception:  # noqa: BLE001
                continue
    return None, None


def smi(fields: list[str]) -> dict:
    rc, out = sh(["nvidia-smi", f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    vals = [v.strip() for v in out.splitlines()[0].split(",")] if rc == 0 and out else []
    return dict(zip(fields, vals)) if len(vals) == len(fields) else {}


class PowerSampler:
    def __init__(self):
        self.samples, self._p, self._t = [], None, None

    def start(self):
        self._p = subprocess.Popen(["nvidia-smi", "--query-gpu=power.draw.instant,clocks.sm,temperature.gpu",
                                    "--format=csv,noheader,nounits", "-lms=100"], stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True)
        self._t = threading.Thread(target=self._read, daemon=True)
        self._t.start()
        return self

    def _read(self):
        for line in self._p.stdout:
            try:
                p, c, t = (float(v) for v in line.split(","))
                self.samples.append({"power_w": p, "sm_mhz": c, "temp_c": t})
            except ValueError:
                continue

    def stop(self):
        self._p.terminate()
        try:
            self._p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._p.kill()
        self._t.join(timeout=5)


def gemm_sweep(ctx, dtype, sizes) -> list[dict]:
    torch = ctx.torch
    rows = []
    for n in sizes:
        a = torch.randn(n, n, device=ctx.device, dtype=dtype)
        b = torch.randn(n, n, device=ctx.device, dtype=dtype)
        c = torch.empty(n, n, device=ctx.device, dtype=dtype)
        st = ctx.bench(lambda: torch.matmul(a, b, out=c), warmup=3, reps=ctx.reps(10))
        rows.append({"dtype": str(dtype).replace("torch.", ""), "n": n, "median_s": st["median"], "p95_s": st["p95"],
                     "n_reps": st["n"], "tflops_median": 2 * n ** 3 / st["median"] / 1e12,
                     "tflops_at_p95_time": 2 * n ** 3 / st["p95"] / 1e12})
        del a, b, c
    return rows


def sustained_power(ctx, seconds: float) -> dict:
    torch = ctx.torch
    n = 4096
    a = torch.randn(n, n, device="cuda", dtype=torch.float16)
    b = torch.randn(n, n, device="cuda", dtype=torch.float16)
    c = torch.empty_like(a)
    ps = PowerSampler().start()
    time.sleep(0.6)
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        for _ in range(20):
            torch.matmul(a, b, out=c)
        torch.cuda.synchronize()
    ps.stop()
    s = ps.samples[6:]  # drop the samples taken before the load started
    pw = sorted(x["power_w"] for x in s)
    return {"samples": len(s), "power_median_w": statistics.median(pw) if pw else None,
            "power_p99_w": pw[min(len(pw) - 1, round(0.99 * (len(pw) - 1)))] if pw else None,
            "power_max_w": max(pw) if pw else None, "sm_mhz_median": statistics.median(x["sm_mhz"] for x in s) if s else None,
            "temp_max_c": max(x["temp_c"] for x in s) if s else None, "seconds": seconds}


def checkpoint_test(ctx, mib: int, reps: int) -> dict:
    """D2H + torch.save + fsync, then torch.load + H2D, verified with SHA-256 of the bytes."""
    torch = ctx.torch
    n = mib << 18  # float32 elements
    state = {f"layer{i}.weight": torch.randn(n // 4, device=ctx.device) for i in range(4)}
    ref = hashlib.sha256(b"".join(v.cpu().numpy().tobytes() for v in state.values())).hexdigest()
    d = Path(tempfile.mkdtemp(prefix="ckpt-"))
    writes, reads, ok = [], [], True
    try:
        for i in range(reps + 1):
            path = d / f"ckpt{i}.pt"
            ctx.sync()
            t0 = time.perf_counter()
            host = {k: v.to("cpu") for k, v in state.items()}
            with open(path, "wb") as fh:
                torch.save(host, fh)
                fh.flush()
                os.fsync(fh.fileno())
            t1 = time.perf_counter()
            back = torch.load(path, map_location=ctx.device, weights_only=True)
            ctx.sync()
            t2 = time.perf_counter()
            if i == reps:  # verify the last round trip bit for bit
                got = hashlib.sha256(b"".join(back[k].cpu().numpy().tobytes() for k in state)).hexdigest()
                ok = got == ref
            if i >= 1:  # the first round is the warm-up
                writes.append(t1 - t0)
                reads.append(t2 - t1)
            path.unlink()
            del back, host
    finally:
        shutil.rmtree(d, ignore_errors=True)
    nbytes = sum(v.numel() * v.element_size() for v in state.values())
    st = statistics
    return {"bytes": nbytes, "reps": len(writes), "write_s_median": st.median(writes), "read_s_median": st.median(reads),
            "write_gbs_median": nbytes / st.median(writes) / 1e9, "read_gbs_median": nbytes / st.median(reads) / 1e9,
            "write_gbs_min": nbytes / max(writes) / 1e9, "verified": ok, "filesystem": tempfile.gettempdir()}


def probe_node() -> dict:
    ib = Path("/sys/class/infiniband")
    nodes = sorted(p.name for p in Path("/sys/devices/system/node").glob("node[0-9]*"))
    rc, topo = sh(["nvidia-smi", "topo", "-m"])
    return {"rdma_devices": sorted(p.name for p in ib.iterdir()) if ib.is_dir() else [], "numa_nodes": nodes,
            "topo_has_nic": "NIC0" in topo, "ibv_devinfo": bool(shutil.which("ibv_devinfo")),
            "ipmitool": bool(shutil.which("ipmitool")), "bmc_device": any(Path("/dev").glob("ipmi*"))}


def mem_total_gib_host() -> float | None:
    try:
        for ln in Path("/proc/meminfo").read_text().splitlines():
            if ln.startswith("MemTotal:"):
                return int(ln.split()[1]) / 2 ** 20
    except OSError:
        pass
    return None


# --------------------------------------------------------------------------------------------- lint
def lint_new_rows(rows: list[dict], manifest: str) -> dict:
    mod, src = load_l1("design_lint")
    if mod is None:
        return {"error": "design_lint not found"}
    try:
        bundle = mod.load_bundle(PKG / "lab" / "data" / "bundle_orion_reference")
        before = {f["location"] for f in mod.check_evidence(bundle)}
        table = "".join(f"| {r['id']} | {r['metric']} | {r['value']} | {r['unit']} | MEASURED | L2 | {manifest} |\n" for r in rows)
        good = copy.deepcopy(bundle)
        good["benchmarks.md"] = bundle["benchmarks.md"].rstrip("\n") + "\n" + table
        found = [f for f in mod.check_evidence(good) if f["location"] not in before]
        bad = copy.deepcopy(bundle)
        r0 = rows[0]
        bad["benchmarks.md"] = bundle["benchmarks.md"].rstrip("\n") + "\n" + (
            f"| B-90 | {r0['metric']} | {r0['value']} | {r0['unit']} | MEASURED | L1 | {manifest} |\n"
            f"| B-91 | {r0['metric']} | {r0['value']} | {r0['unit']} | MEASURED | L2 | - |\n")
        neg = [f for f in mod.check_evidence(bad) if f["location"] not in before]
        return {"module": src, "rows_added": len(rows), "new_findings": found, "negative_control_findings": neg,
                "rows_markdown": table}
    except Exception as exc:  # noqa: BLE001 - starter TODO
        return {"module": src, "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    import yaml  # noqa: PLC0415
    torch = ctx.torch
    gpu = ctx.is_gpu
    assumptions = {a["id"]: a for a in yaml.safe_load((PKG / "lab" / "data" / "bundle_orion_reference" / "assumptions.yaml")
                                                       .read_text(encoding="utf-8"))["assumptions"]}
    node = probe_node()
    metrics, tables, notes = {}, {}, []
    sizes = [2048, 4096] if ctx.quick else [2048, 4096, 6144]
    if gpu:
        sweep = gemm_sweep(ctx, torch.float16, sizes) + gemm_sweep(ctx, torch.bfloat16, sizes)
        p = torch.cuda.get_device_properties(0)
        info = smi(["name", "memory.total", "clocks.max.sm", "power.limit", "enforced.power.limit", "driver_version"])
        power = sustained_power(ctx, 5.0 if ctx.quick else 30.0)
        peak_max = p.multi_processor_count * ADA_FP16_TENSOR_FLOP_PER_CLK_SM * float(info["clocks.max.sm"]) * 1e6 / 1e12 \
            if f"{p.major}.{p.minor}" == "8.9" else None
        peak_run = p.multi_processor_count * ADA_FP16_TENSOR_FLOP_PER_CLK_SM * power["sm_mhz_median"] * 1e6 / 1e12 \
            if peak_max and power["sm_mhz_median"] else None
        best = max(r["tflops_median"] for r in sweep)
        metrics.update({
            "gpu": info.get("name"), "best_tensor_tflops": round(best, 2), "peak_fp16_tflops_at_max_clock": round(peak_max, 2) if peak_max else None,
            "peak_fp16_tflops_at_run_clock": round(peak_run, 2) if peak_run else None,
            "achieved_fraction_of_run_clock_peak": round(best / peak_run, 3) if peak_run else None,
            "achieved_fraction_of_max_clock_peak": round(best / peak_max, 3) if peak_max else None,
            "memory_total_mib_smi": float(info["memory.total"]), "memory_total_mib_cuda": p.total_memory / 2 ** 20,
            "gpu_power_median_w": power["power_median_w"], "gpu_power_max_w": power["power_max_w"],
            "gpu_power_limit_w": info.get("enforced.power.limit"), "power_samples": power["samples"],
            "driver": info.get("driver_version"),
        })
        tables["power"] = [power]
    else:
        sweep = gemm_sweep(ctx, torch.float32, [1024, 2048] if ctx.quick else [1024, 2048, 3072])
        best = max(r["tflops_median"] for r in sweep)
        metrics.update({"best_cpu_fp32_tflops": round(best, 4), "host_memory_gib": round(mem_total_gib_host() or 0, 2)})
    tables["gemm"] = sweep
    ck = checkpoint_test(ctx, 64 if ctx.quick else 256, ctx.reps(5))
    tables["checkpoint"] = [ck]
    metrics.update({"ckpt_bytes": ck["bytes"], "ckpt_write_gbs_median": round(ck["write_gbs_median"], 3),
                    "ckpt_read_gbs_median": round(ck["read_gbs_median"], 3), "ckpt_verified": ck["verified"]})
    ctx.log(f"best dense {'tensor' if gpu else 'CPU'} GEMM {best:.2f} TFLOP/s; checkpoint write {ck['write_gbs_median']:.2f} "
            f"GB/s, read {ck['read_gbs_median']:.2f} GB/s, verified {ck['verified']}")

    # assumption register: bundle value vs what this node shows
    a = assumptions
    pfs_per_node = a["A-05"]["value"] / 32  # 80 GB/s across 32 nodes
    reg = [
        {"id": "A-01", "statement": a["A-01"]["statement"], "bundle": f"{a['A-01']['value']} {a['A-01']['unit']} [{a['A-01']['label']}]",
         "this_node": (f"{best:.1f} TFLOP/s measured (dense FP16/BF16 GEMM); this GPU's peak {metrics.get('peak_fp16_tflops_at_max_clock')} "
                       "at max clock") if gpu else f"{best:.3f} TFLOP/s FP32 on the CPU (no GPU)",
         "verdict": "node class differs: validate the ratio achieved/peak, not the number"},
        {"id": "A-04", "statement": a["A-04"]["statement"], "bundle": f"{a['A-04']['value']} [{a['A-04']['label']}]",
         "this_node": (f"dense GEMM reached {metrics.get('achieved_fraction_of_run_clock_peak')} of the clock-adjusted peak: an upper "
                       "bound on any model's MFU on this GPU") if gpu else "not measurable without a GPU",
         "verdict": "MFU 0.40 must sit below the measured GEMM ceiling; measure end-to-end on the 64-GPU slice (L3)"},
        {"id": "A-02", "statement": a["A-02"]["statement"], "bundle": f"{a['A-02']['value']} {a['A-02']['unit']}",
         "this_node": (f"{metrics['memory_total_mib_smi'] / 1024:.1f} GiB (nvidia-smi) / {metrics['memory_total_mib_cuda'] / 1024:.2f} "
                       "GiB (CUDA)") if gpu else f"no GPU; host memory {metrics['host_memory_gib']} GiB",
         "verdict": "FAILS acceptance on this node: not the bundle's GPU (exactly what the check is for)"},
        {"id": "A-03", "statement": a["A-03"]["statement"], "bundle": f"{a['A-03']['value']} {a['A-03']['unit']}",
         "this_node": (f"GPU board {metrics['gpu_power_median_w']:.1f} W median / {metrics['gpu_power_max_w']:.1f} W max under GEMM; "
                       "node power not measurable (no BMC/PDU)") if gpu else "not measurable (no GPU, no BMC, no RAPL)",
         "verdict": "NOT VALIDATED: needs a BMC/PDU reading over >= 10 min of burn-in"},
        {"id": "A-08", "statement": a["A-08"]["statement"], "bundle": f"{a['A-08']['value']} {a['A-08']['unit']}",
         "this_node": (f"{ck['bytes'] / 2 ** 20:.0f} MiB state: write {ck['write_gbs_median']:.2f} GB/s, read "
                       f"{ck['read_gbs_median']:.2f} GB/s to local disk, verified={ck['verified']}"),
         "verdict": (f"local write {'above' if ck['write_gbs_median'] > pfs_per_node else 'below'} the per-node PFS share "
                     f"({pfs_per_node:.1f} GB/s = 80 GB/s / 32 nodes); A-08 itself needs the 32-node sync save (L3)")},
        {"id": "A-10", "statement": a["A-10"]["statement"], "bundle": f"{a['A-10']['value']} {a['A-10']['unit']}",
         "this_node": f"RDMA devices: {node['rdma_devices'] or 'none'}; ibv_devinfo {'present' if node['ibv_devinfo'] else 'absent'}",
         "verdict": "NOT VALIDATED: no RDMA NIC"},
        {"id": "affinity", "statement": "GPU-NIC PCIe affinity and NUMA layout", "bundle": "PIX per rail; 2 NUMA nodes (HX8)",
         "this_node": f"topo -m lists a NIC: {node['topo_has_nic']}; NUMA nodes: {node['numa_nodes']}",
         "verdict": "NOT VALIDATED: no NIC; single NUMA node"},
    ]
    tables["assumptions"] = reg

    import hwlab  # noqa: PLC0415 - /opt/hwlab is on sys.path inside the image
    label = hwlab.label_for({"device": ctx.device, "gpus": [],
                             "gpu0": {"name": torch.cuda.get_device_name(0)} if gpu else {}})
    manifest = f"lab/l2/results/{label}/environment.json"
    unit_rows = [
        {"id": "B-07", "metric": f"Dense {'FP16/BF16 tensor' if gpu else 'FP32 CPU'} GEMM, best of {len(sizes)} sizes (median of reps)",
         "value": f"{best:.2f}", "unit": "TFLOP/s"},
        {"id": "B-08", "metric": f"Checkpoint write, {ck['bytes'] / 2 ** 20:.0f} MiB, D2H + torch.save + fsync, local disk",
         "value": f"{ck['write_gbs_median']:.2f}", "unit": "GB/s"},
    ]
    if gpu:
        unit_rows.append({"id": "B-09", "metric": "GPU board power under sustained FP16 GEMM (median, 100 ms samples)",
                          "value": f"{metrics['gpu_power_median_w']:.1f}", "unit": "W"})
    lint = lint_new_rows(unit_rows, manifest)
    tables["lint"] = [lint]
    metrics["lint_new_findings"] = len(lint.get("new_findings", [])) if "error" not in lint else None
    metrics["lint_negative_rules"] = sorted({f["rule"] for f in lint.get("negative_control_findings", [])}) if "error" not in lint else None
    not_runnable = [
        {"part": "A-03 node power: sudo ipmitool dcmi power reading during >= 10 min of burn-in",
         "needs": ["a BMC with DCMI/Redfish read access", "an HX8-class server"], "probe": node},
        {"part": "A-10 RoCE MTU and NIC firmware: ibv_devinfo active_mtu, fw_ver; GPU-NIC affinity in topo -m",
         "needs": ["RDMA NICs on the GPU host", "rdma-core"], "probe": node},
        {"part": "L3 B-02 row: 2-node all_reduce_perf busbw with /GDRDMA evidence",
         "needs": ["2+ multi-GPU nodes with RDMA NICs", "nccl-tests built with MPI"], "probe": "single host"},
    ]
    notes += [
        "GEMM: 3 warm-ups, >= 5 timed repetitions per size (CUDA events on the GPU). Checkpoint: 1 warm-up round trip, then >= 5; "
        "the last round trip is verified with SHA-256 over every tensor's bytes.",
        f"Checkpoint files go to {ck['filesystem']} inside the container (the image's overlay filesystem on the host's disk).",
        f"The benchmarks.md rows point at {manifest}, the environment manifest this run writes.",
    ]
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if not m["ckpt_verified"]:
        fails.append("the checkpoint read back does not match what was written: never trust a save you have not restored")
    if t["checkpoint"][0]["reps"] < 5:
        fails.append("fewer than 5 checkpoint repetitions")
    if any(r["n_reps"] < 5 for r in t["gemm"]):
        fails.append("fewer than 5 GEMM repetitions")
    if m.get("lint_new_findings") is not None:
        if m["lint_new_findings"]:
            fails.append(f"the new MEASURED L2 rows raised {[f['rule'] for f in t['lint'][0]['new_findings']]}: a labelled, "
                         "manifest-backed L2 row must pass EVID-001..004")
        if m["lint_negative_rules"] != ["EVID-003", "EVID-004"]:
            fails.append(f"negative controls raised {m['lint_negative_rules']}, expected EVID-003 (no manifest) and EVID-004 "
                         "(physical MEASURED at L1)")
    if env["device"] == "cuda":
        if m.get("peak_fp16_tflops_at_max_clock") and m["best_tensor_tflops"] > 1.05 * m["peak_fp16_tflops_at_max_clock"]:
            fails.append(f"GEMM {m['best_tensor_tflops']} TFLOP/s exceeds the device peak {m['peak_fp16_tflops_at_max_clock']}: "
                         "check the FLOP count and synchronisation")
        if abs(m["memory_total_mib_smi"] - m["memory_total_mib_cuda"]) > 0.03 * m["memory_total_mib_smi"]:
            fails.append("nvidia-smi and CUDA disagree on GPU memory by > 3 %: check you are reading the same device")
        try:
            if m["gpu_power_median_w"] > 1.05 * float(m["gpu_power_limit_w"]):
                fails.append("median GPU power above the enforced limit: the power reading or limit is wrong")
        except (TypeError, ValueError):
            pass
        if m["power_samples"] < 5:
            fails.append("fewer than 5 power samples under load")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    lines = ["## Assumption register against this node", "", "| ID | Assumption | Bundle | This node | Verdict |", "|---|---|---|---|---|"]
    for r in t["assumptions"]:
        lines.append(f"| {r['id']} | {r['statement']} | {r['bundle']} | {r['this_node']} | {r['verdict']} |")
    lines += ["", "## Dense GEMM sweep (A-01)", "", "| dtype | n | TFLOP/s (median) | TFLOP/s at p95 time | reps |", "|---|---|---|---|---|"]
    for r in t["gemm"]:
        lines.append(f"| {r['dtype']} | {r['n']} | {r['tflops_median']:.2f} | {r['tflops_at_p95_time']:.2f} | {r['n_reps']} |")
    if gpu:
        p = t["power"][0]
        lines += ["", f"Peak FP16 tensor rate at the max SM clock **{m['peak_fp16_tflops_at_max_clock']} TFLOP/s**, at the clock the "
                  f"GEMM held ({p['sm_mhz_median']:.0f} MHz) **{m['peak_fp16_tflops_at_run_clock']} TFLOP/s** `[MODELED]`; best "
                  f"measured **{m['best_tensor_tflops']} TFLOP/s** `[MEASURED]`. GPU power under the GEMM: median "
                  f"{p['power_median_w']:.1f} W, p99 {p['power_p99_w']:.1f} W, max {p['power_max_w']:.1f} W against an enforced limit of "
                  f"{m['gpu_power_limit_w']} W ({p['samples']} samples over {p['seconds']:.0f} s)."]
    ck = t["checkpoint"][0]
    lines += ["", "## Checkpoint write and restore (A-08 / B-03 at node scale)", "",
              f"{ck['bytes'] / 2 ** 20:.0f} MiB per checkpoint, {ck['reps']} repetitions: write median **{ck['write_gbs_median']:.2f} GB/s** "
              f"(worst {ck['write_gbs_min']:.2f}), read-back median {ck['read_gbs_median']:.2f} GB/s; bit-exact restore: "
              f"**{ck['verified']}**."]
    lint = t["lint"][0]
    lines += ["", "## New evidence rows, linted with the lab's `check_evidence`", ""]
    if "error" in lint:
        lines.append(f"_Not run: {lint['error']}._")
    else:
        lines += ["| id | metric | value | unit | label | tier | manifest |", "|---|---|---|---|---|---|---|",
                  lint["rows_markdown"].rstrip(), "",
                  f"New findings on these rows: **{len(lint['new_findings'])}**. Negative controls (same metric at tier L1; MEASURED "
                  f"with no manifest) raised: **{', '.join(sorted({f['rule'] for f in lint['negative_control_findings']}))}**."]
    lines += ["", "What to conclude:", "",
              "- An acceptance run is a set of yes/no answers against the bundle, each with evidence. On this host A-02 fails "
              "outright (wrong GPU), A-03 and A-10 cannot be answered (no BMC, no NIC), and A-01/A-04 transfer only as a ratio.",
              "- Keep the vendor maximum for rack budgeting and record the measured value next to it; do not overwrite one with "
              "the other.",
              "- A MEASURED row is only evidence with its manifest and the right tier; the linter enforces that, and the negative "
              "controls show it would have caught the two common mistakes.",
              "- Never trust a checkpoint you have not restored: the round trip here is verified bit for bit."]
    if not gpu:
        lines += ["", "_CPU fallback: no GPU, so A-01 is a CPU FP32 GEMM, A-02 is host memory and no power was measured; the GPU-only "
                  "invariants were skipped._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
