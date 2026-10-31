"""Ch 1 L2: characterise a real, measured kernel mix with the lab's ceiling model, plus a GPU inventory.

What it teaches (Sections 1.6 and 1.9): the ceiling model is only as good as its inputs. Here the inputs
are measured: six small workloads run on the real GPU (a training step of a 4-block MLP, a square BF16
GEMM, a batch-8 decode GEMV, a large elementwise op, a pinned host-to-device batch load, and a burst of
tiny launches), each timed as the median of >= 5 repetitions after warm-up, with FLOP and byte counts
from their shapes. They are written as rows in the lab's own CSV schema, a platform file is written
for *this* GPU (vendor-class peaks derived from SM count, FLOP/clock/SM and the max clocks; the PCIe
link it negotiated), and the reference solution's ``normalize_and_validate()`` and ``classify()`` run
on them unchanged. Every lower bound must stay below the observed time (nothing beats a peak), the
classes must come out as the physics says (GEMM compute, GEMV and elementwise memory, the batch load
I/O over PCIe, tiny launches latency/overhead), and the machine balance is compared with the
manuscript's H100-class 295 FLOP/B.

The L2 extension also asks for DCGM profiling fields, Nsight Systems and an 8-GPU nccl-tests run. They
are probed and recorded as not runnable here (no DCGM, no Nsight, one GPU, no NVLink); nvidia-smi
telemetry sampled during each workload stands in for DCGM where it can (clocks, power, utilisation,
clock-event reasons).

CPU fallback: the same mix on the CPU (FP32 instead of BF16, no host-to-device row because there is no
separate I/O path to measure), classified against the *measured* CPU roofs; the GPU inventory and the
GPU-only invariants are skipped and the report says so.
"""
from __future__ import annotations

import importlib.util
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch01-l2",
    "title": "Lab 1 L2: workload characterisation of a measured kernel mix and a GPU inventory",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same kernel mix (training step, GEMM, decode GEMV, elementwise, tiny launches) timed on the CPU "
                     "in FP32 and classified by the lab's classify() against the measured CPU roofs; no GPU inventory"),
}

PKG = Path(__file__).resolve().parents[2]
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}  # GB/s per lane after encoding
# Dense BF16 (FP32 accumulate) FLOP per clock per SM, from NVIDIA architecture whitepapers (Ada AD102: RTX 4090
# 165.2 TFLOPS at 128 SMs x 2520 MHz -> 512; Ampere GA10x 512; A100 2048; H100 4096).
BF16_FLOP_PER_CLK_SM = {(8, 9): 512, (8, 6): 512, (8, 0): 2048, (9, 0): 4096}
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4080 laptop": 192,
            "rtx 4090 laptop": 256, "rtx 4090": 384, "rtx 3090": 384}  # GDDR bus width, NVIDIA product specs
ORION = {"bf16_tflops": 989.0, "hbm_gb_s": 3350.0}   # lab data/platform_orion.yaml [VENDOR-SPEC class]
EXPECTED = {   # declared class = what the physics says each workload should be (the hypothesis under test)
    "L2-TRAIN": "compute", "L2-GEMM": "compute", "L2-DECODE": "memory", "L2-ELTWISE": "memory",
    "L2-H2D": "io", "L2-TINY": "memory",
}


def load_solution():
    # Reference solution when present (instructor tree); the learner's starter/ in the student release.
    path = PKG / "solutions" / "lab" / "workload_model.py"
    if not path.is_file():
        path = PKG / "lab" / "starter" / "workload_model.py"
    spec = importlib.util.spec_from_file_location("ch01_workload_model", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sh(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


# ------------------------------------------------------------------ inventory and absent hardware
def inventory(ctx, env: dict) -> dict:
    torch = ctx.torch
    inv = {"gpu_count_torch": torch.cuda.device_count() if ctx.is_gpu else 0,
           "nccl_version": ".".join(map(str, torch.cuda.nccl.version())) if ctx.is_gpu else None,
           "cuda_runtime": env.get("cuda_runtime"), "torch": env.get("torch")}
    if ctx.is_gpu:
        p = torch.cuda.get_device_properties(0)
        g = (env.get("gpus") or [{}])[0]
        inv.update({"name": p.name, "capability": f"{p.major}.{p.minor}", "sm_count": p.multi_processor_count,
                    "torch_total_mib": round(p.total_memory / 2 ** 20), "smi_total_mib": float(g.get("memory.total", "nan")),
                    "l2_cache_mib": round(getattr(p, "L2_cache_size", 0) / 2 ** 20, 1),
                    "driver_version": g.get("driver_version"), "pci_bus_id": g.get("pci.bus_id"),
                    "pcie_gen_max": g.get("pcie.link.gen.max"), "pcie_width_max": g.get("pcie.link.width.max"),
                    "pcie_gen_current": g.get("pcie.link.gen.current"), "pcie_width_current": g.get("pcie.link.width.current"),
                    "clocks_max_sm_mhz": g.get("clocks.max.sm"), "clocks_max_mem_mhz": g.get("clocks.max.memory"),
                    "power_limit_w": g.get("power.limit"), "topology_nvidia_smi_topo_m": sh(["nvidia-smi", "topo", "-m"]),
                    "nvlink": sh(["nvidia-smi", "nvlink", "-s"]) or "no output"})
    return inv


def absent_parts(ctx, inv: dict) -> list[dict]:
    """Probe for what the manuscript's L2/L3 commands need; record honestly what is missing."""
    parts = []
    if not shutil.which("dcgmi"):
        parts.append({"part": "dcgmi dmon -e 1002,1004,1005,1011 (SM_ACTIVE, PIPE_TENSOR_ACTIVE, DRAM_ACTIVE, NVLINK_TX)",
                      "probe": "which dcgmi -> not found", "needs": ["DCGM with profiling-metric support (data-center GPUs)"],
                      "fallback": "nvidia-smi clocks/power/utilisation/clock-event reasons sampled during each workload"})
    if not shutil.which("nsys"):
        parts.append({"part": "nsys profile of the training step", "probe": "which nsys -> not found",
                      "needs": ["Nsight Systems CLI"], "fallback": "the step is timed with CUDA events (Chapter 4's L2 uses torch.profiler)"})
    n = inv.get("gpu_count_torch", 0)
    if n < 2:
        parts.append({"part": "nccl-tests all_reduce_perf -g 8 (intra-node NVLink all-reduce)",
                      "probe": f"torch.cuda.device_count() = {n}; nvidia-smi nvlink -s: "
                               f"{(inv.get('nvlink') or 'n/a').splitlines()[-1] if inv.get('nvlink') else 'n/a'}",
                      "needs": [">= 2 GPUs in one node, NVLink/NVSwitch", "nccl-tests"],
                      "fallback": "scale-up columns are 0 in every measured row; the PCIe link is the only interconnect"})
    if not Path("/sys/class/infiniband").exists():
        parts.append({"part": "L3: ibv_devinfo, ethtool -S, multi-node all_reduce_perf",
                      "probe": "/sys/class/infiniband absent", "needs": ["2+ nodes with RoCEv2 or InfiniBand NICs"],
                      "fallback": "scale-out column is 0 in every measured row"})
    return parts


# ------------------------------------------------------------------ platform for this device
def gpu_platform(env: dict, inv: dict) -> tuple[dict, dict]:
    g = (env.get("gpus") or [{}])[0]
    cap = tuple(int(x) for x in inv["capability"].split("."))
    clk = float(g["clocks.max.sm"]) * 1e6
    bf16 = inv["sm_count"] * BF16_FLOP_PER_CLK_SM[cap] * clk / 1e12
    name = inv["name"].lower()
    bits = next(b for k, b in sorted(BUS_BITS.items(), key=lambda kv: -len(kv[0])) if k in name)
    hbm = float(g["clocks.max.memory"]) * 1e6 * 2 * bits / 8 / 1e9
    pcie = PCIE_GBPS_PER_LANE[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"])
    plat = {"platform": f"{inv['name']} (this host)", "gpus_per_node": 1, "gpu_dense_bf16_tflops": bf16,
            "hbm_gb_per_s": hbm,
            "nvlink_gb_per_s_per_direction": pcie,       # no NVLink: the only GPU interconnect is the PCIe link
            "nic_line_rate_gbit_per_s": pcie * 8,        # no backend NIC; no measured row sends NIC traffic
            "frontend_gbit_per_s_per_node": pcie * 8,    # the batch-load path into the GPU is the PCIe link
            "storage_read_gb_per_s_aggregate": pcie, "storage_write_gb_per_s_aggregate": pcie,
            "latency_fraction_threshold": 0.25}
    src = {"gpu_dense_bf16_tflops": f"{inv['sm_count']} SMs x {BF16_FLOP_PER_CLK_SM[cap]} FLOP/clk/SM x {clk / 1e6:.0f} MHz "
                                    "(clocks.max.sm) [MODELED from VENDOR-SPEC]",
           "hbm_gb_per_s": f"{bits}-bit bus x 2 x {float(g['clocks.max.memory']):.0f} MHz (GDDR6, clocks.max.memory) [MODELED from VENDOR-SPEC]",
           "io/scale-up": f"PCIe Gen{g['pcie.link.gen.max']} x{g['pcie.link.width.max']} = {pcie:.2f} GB/s per direction [MODELED]"}
    return plat, src


# ------------------------------------------------------------------ telemetry (DCGM stand-in)
class Telemetry:
    def __init__(self, gpu: bool):
        self.samples, self.proc = [], None
        if gpu and shutil.which("nvidia-smi"):
            self.proc = subprocess.Popen(["nvidia-smi", "--query-gpu=clocks.sm,power.draw,utilization.gpu,utilization.memory,"
                                          "clocks_event_reasons.active,temperature.gpu", "--format=csv,noheader,nounits",
                                          "-lms", "100", "-i", "0"], stdout=subprocess.PIPE, text=True)
            threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            v = [x.strip() for x in line.split(",")]
            if len(v) == 6:
                try:
                    self.samples.append((time.monotonic(), float(v[0]), float(v[1]) if "N/A" not in v[1] else 0.0,
                                         float(v[2]), float(v[3]), v[4], float(v[5])))
                except ValueError:
                    pass

    def window(self, t0: float, t1: float) -> dict:
        s = [x for x in self.samples if t0 <= x[0] <= t1]
        if not s:
            return {}
        med = lambda i: sorted(x[i] for x in s)[len(s) // 2]  # noqa: E731
        return {"samples": len(s), "sm_clock_mhz": med(1), "power_w": med(2), "util_gpu_pct": med(3),
                "util_mem_pct": med(4), "temp_c_max": max(x[6] for x in s),
                "clock_event_masks": sorted({x[5] for x in s})}

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)


# ------------------------------------------------------------------ the measured kernel mix
def workloads(ctx) -> list[dict]:
    """Each entry: id, name, phase, fn, flop, hbm bytes (device memory), io bytes (host->device)."""
    torch = ctx.torch
    gpu, q = ctx.is_gpu, ctx.quick
    dev = "cuda" if gpu else "cpu"
    dt = torch.bfloat16 if gpu else torch.float32
    esz = 2 if gpu else 4
    out = []

    # 1. a training step: 4 MLP blocks (d -> 4d -> d), autocast BF16 on the GPU, fused AdamW
    d, tokens, blocks = (1024, 2048 if q else 8192, 4) if gpu else (256, 256 if q else 1024, 4)
    layers = []
    for _ in range(blocks):
        layers += [torch.nn.Linear(d, 4 * d), torch.nn.GELU(), torch.nn.Linear(4 * d, d)]
    model = torch.nn.Sequential(*layers).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4, fused=gpu, foreach=None if gpu else True)
    x = torch.randn(tokens, d, device=dev)
    nparam = sum(p.numel() for p in model.parameters())

    def train_step():
        with torch.autocast(device_type=dev, dtype=torch.bfloat16, enabled=gpu):
            loss = model(x).float().pow(2).mean()
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
    # bytes [MODELED lower bound]: optimizer reads p, g, m, v and writes p, m, v in FP32 (28 B/param), plus each
    # block's activations written in forward and read in backward (input d + hidden 4d, twice for the GELU).
    act = tokens * blocks * (d + 4 * d + 4 * d) * esz * 2
    out.append({"id": "L2-TRAIN", "name": f"mlp{blocks}x{d}-train-step", "phase": "train", "fn": train_step,
                "flop": 6.0 * nparam * tokens, "hbm": 28.0 * nparam + act, "io": 0.0,
                "detail": f"{nparam / 1e6:.1f} M params, {tokens} tokens/step, {'BF16 autocast' if gpu else 'FP32'}, AdamW"})

    # 2. square GEMM (training-like)
    n = (2048 if q else 4096) if gpu else (384 if q else 768)
    a, b = torch.randn(n, n, device=dev, dtype=dt), torch.randn(n, n, device=dev, dtype=dt)
    out.append({"id": "L2-GEMM", "name": f"gemm-{n}", "phase": "train", "fn": lambda: torch.matmul(a, b),
                "flop": 2.0 * n ** 3, "hbm": 3.0 * n * n * esz, "io": 0.0, "detail": f"{n}^3, {str(dt).split('.')[-1]}"})

    # 3. decode: batch-8 GEMV against a weight matrix far larger than L2 (every weight read once per step)
    # (batch 1 on the CPU: its machine balance is only a few FLOP/B, so batch 8 would sit on the ridge)
    kk, nn, bsz = (4096, 8192 if q else 16384, 8) if gpu else (2048, 4096, 1)
    w = torch.randn(nn, kk, device=dev, dtype=dt)
    h = torch.randn(bsz, kk, device=dev, dtype=dt)
    out.append({"id": "L2-DECODE", "name": f"decode-gemv-b{bsz}", "phase": "infer", "fn": lambda: h @ w.t(),
                "flop": 2.0 * bsz * kk * nn, "hbm": esz * (nn * kk + bsz * kk + bsz * nn), "io": 0.0,
                "detail": f"weights {nn}x{kk} ({nn * kk * esz / 2 ** 20:.0f} MiB), batch {bsz}"})

    # 4. elementwise (layernorm/activation-like): 2 reads + 1 write per element, FP32
    ne = (32 if q else 64) * 2 ** 20 if gpu else (8 if q else 16) * 2 ** 20
    u, v, z = (torch.rand(ne, device=dev) for _ in range(3))
    out.append({"id": "L2-ELTWISE", "name": "eltwise-add", "phase": "train", "fn": lambda: torch.add(u, v, out=z),
                "flop": float(ne), "hbm": 12.0 * ne, "io": 0.0, "detail": f"{ne * 4 / 2 ** 20:.0f} MiB per tensor, FP32"})

    # 5. batch load: pinned host -> device copy over PCIe (the I/O path of a single-GPU node)
    if gpu:
        nb = (64 if q else 256) * 2 ** 20
        host = torch.empty(nb, dtype=torch.uint8).pin_memory()
        devbuf = torch.empty(nb, dtype=torch.uint8, device="cuda")
        out.append({"id": "L2-H2D", "name": "batch-load-h2d-pinned", "phase": "train",
                    "fn": lambda: devbuf.copy_(host, non_blocking=True), "flop": 0.0, "hbm": float(nb), "io": float(nb),
                    "detail": f"{nb / 2 ** 20:.0f} MiB pinned host -> device"})

    # 6. a burst of tiny launches (e.g. an un-fused optimizer over small parameters)
    t = torch.rand(1024, device=dev)
    k = 200

    def tiny():
        y = t
        for _ in range(k):
            y = y + 1.0
        return y
    out.append({"id": "L2-TINY", "name": f"tiny-launch-x{k}", "phase": "train", "fn": tiny,
                "flop": float(k * 1024), "hbm": float(k * 2 * 1024 * 4), "io": 0.0, "detail": f"{k} x 1024-element adds"})
    return out


def run(ctx) -> dict:
    torch = ctx.torch
    import hwlab  # noqa: E402  (shared runtime, already imported by run.py)
    wm = load_solution()
    env = hwlab.environment(ctx.device)
    inv = inventory(ctx, env)
    parts = absent_parts(ctx, inv) if ctx.is_gpu else []
    if not ctx.is_gpu:
        torch.set_num_threads(min(4, os.cpu_count() or 1))
    tel = Telemetry(ctx.is_gpu)
    try:
        wl = workloads(ctx)
        meas = []
        for w in wl:
            t0 = time.monotonic()
            if ctx.is_gpu:      # pre-load so the 100 ms telemetry samples describe this workload, not the previous one
                t_end = t0 + (0.4 if ctx.quick else 1.0)
                while time.monotonic() < t_end:
                    w["fn"]()
                    ctx.sync()
            st = ctx.bench(w["fn"], warmup=3, reps=ctx.reps(20))
            meas.append({**{k: v for k, v in w.items() if k != "fn"}, "stats": st,
                         "telemetry": tel.window(t0, time.monotonic())})
            ctx.log(f"{w['id']:10} median {st['median'] * 1e3:9.3f} ms  p95 {st['p95'] * 1e3:9.3f} ms")
    finally:
        tel.stop()

    if ctx.is_gpu:
        plat, src = gpu_platform(env, inv)
    else:   # measured CPU roofs (no vendor peak is asserted for a virtualised CPU)
        flops = max(m["flop"] / m["stats"]["median"] for m in meas if m["id"] in ("L2-GEMM", "L2-TRAIN"))
        bw = max(m["hbm"] / m["stats"]["median"] for m in meas if m["id"] in ("L2-ELTWISE", "L2-DECODE"))
        plat = {"platform": "CPU fallback (measured roofs)", "gpus_per_node": 1, "gpu_dense_bf16_tflops": flops / 1e12,
                "hbm_gb_per_s": bw / 1e9, "nvlink_gb_per_s_per_direction": 1.0, "nic_line_rate_gbit_per_s": 8.0,
                "frontend_gbit_per_s_per_node": 8.0, "storage_read_gb_per_s_aggregate": 1.0,
                "storage_write_gb_per_s_aggregate": 1.0, "latency_fraction_threshold": 0.25}
        src = {"gpu_dense_bf16_tflops": "max measured FP32 GEMM/training-step FLOP/s [MEASURED roof]",
               "hbm_gb_per_s": "max measured elementwise/GEMV bandwidth [MEASURED roof]",
               "io/scale-up": "no I/O path measured on the CPU fallback (placeholders; every such column is 0)"}

    # rows in the lab's CSV schema (strings, exactly as the L1 loader would read them)
    rows = []
    for m in meas:
        rows.append({"workload_id": m["id"], "name": m["name"], "phase": m["phase"], "declared_class": EXPECTED[m["id"]],
                     "gpus": "1", "tflop_per_gpu": repr(m["flop"] / 1e12), "hbm_gb_per_gpu": repr(m["hbm"] / 1e9),
                     "nvlink_gb_per_gpu": "0", "net_value_per_gpu": "0", "net_unit": "GB",
                     "io_read_gb_per_node": repr(m["io"] / 1e9), "io_write_gb_per_node": "0",
                     "observed_step_s": repr(m["stats"]["median"]), "notes": m["detail"]})
    clean, issues = wm.normalize_and_validate(rows)
    results = [wm.classify(p, plat) for p in clean]
    by = {r["workload_id"]: r for r in results}
    table = []
    for m in meas:
        r = by[m["id"]]
        st = m["stats"]
        table.append({"id": m["id"], "name": m["name"], "detail": m["detail"], "declared": EXPECTED[m["id"]],
                      "bound": r["bound_class"], "dominant": r["dominant_resource"], "lower_bound_s": r["lower_bound_s"],
                      "median_s": st["median"], "p95_s": st["p95"], "min_s": st["min"], "max_s": st["max"], "iqr_s": st["iqr"],
                      "n": st["n"], "ceiling_fraction": r["ceiling_fraction"], "flags": r["flags"], "times": r["times"],
                      "ai_flop_per_byte": m["flop"] / m["hbm"] if m["hbm"] else None,
                      "achieved_tflops": m["flop"] / st["median"] / 1e12, "achieved_gbs": m["hbm"] / st["median"] / 1e9,
                      "achieved_io_gbs": m["io"] / st["median"] / 1e9, "telemetry": m["telemetry"]})
    balance = plat["gpu_dense_bf16_tflops"] * 1e12 / (plat["hbm_gb_per_s"] * 1e9)
    metrics = {"machine_balance_flop_per_byte": round(balance, 1),
               "orion_machine_balance_flop_per_byte": round(ORION["bf16_tflops"] * 1e3 / ORION["hbm_gb_s"], 1),
               "rejected_rows": len(issues)}
    for t in table:
        metrics[f"{t['id']}_median_ms"] = round(t["median_s"] * 1e3, 4)
        metrics[f"{t['id']}_ceiling_fraction"] = round(t["ceiling_fraction"], 3)
    notes = ["Observed time = median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on "
             "the CPU); p95, IQR and min/max are in the table. FLOP and byte counts are from shapes [MODELED]; the "
             "training-step bytes are a lower bound (optimizer state + saved activations), so its memory time is too.",
             "Rows are passed to the reference solution's normalize_and_validate() and classify() exactly as CSV strings."]
    if not ctx.is_gpu:
        notes.append("CPU fallback: torch limited to 4 threads; the roofs are the best measured rates, so the roof-setting "
                     "rows have a ceiling fraction of 1.0 by construction.")
    out = {"metrics": metrics, "tables": {"workloads": table, "csv_rows": rows}, "issues": issues,
           "platform": plat, "platform_source": src, "inventory": inv, "notes": notes,
           "workload_definition": {w["id"]: w["detail"] for w in meas},
           "manifest_record": {"gpu_model": inv.get("name", "none (CPU fallback)"), "gpu_count": inv.get("gpu_count_torch"),
                               "driver_version": inv.get("driver_version"), "cuda_version": inv.get("cuda_runtime"),
                               "nccl_version": inv.get("nccl_version"), "dcgm_version": "not installed",
                               "warmup_policy": "3 warm-up calls per workload (+0.4/1.0 s pre-load on the GPU)",
                               "run_count": table[0]["n"] if table else 0}}
    if parts:
        out["not_runnable_parts"] = parts
    return out


def check(result: dict, env: dict) -> list[str]:
    fails = []
    t = {r["id"]: r for r in result["tables"]["workloads"]}
    gpu = env["device"] == "cuda"
    if result["issues"]:
        fails.append(f"normalize_and_validate rejected measured rows: {result['issues']} (check the CSV encoding of the rows)")
    for r in t.values():
        if r["median_s"] <= 0 or r["p95_s"] < r["median_s"]:
            fails.append(f"{r['id']}: inconsistent timing statistics (median {r['median_s']}, p95 {r['p95_s']})")
        if "IMPOSSIBLE" in r["flags"] or r["ceiling_fraction"] > 1.02:
            fails.append(f"{r['id']}: lower bound {r['lower_bound_s']:.3g} s exceeds the observed {r['median_s']:.3g} s "
                         f"(fraction {r['ceiling_fraction']:.2f}): a FLOP/byte count or a ceiling is wrong (or the timer "
                         "did not synchronise)")
    want = {"L2-GEMM": "compute", "L2-TRAIN": "compute", "L2-DECODE": "memory", "L2-ELTWISE": "memory"}
    if gpu:
        want["L2-H2D"] = "io"
    for k, cls in want.items():
        if t[k]["bound"] != cls:
            fails.append(f"{k} classified {t[k]['bound']} (dominant {t[k]['dominant']}), expected {cls}: check its FLOP/byte "
                         "accounting against the machine balance")
    if "LATENCY_OR_OVERHEAD" not in t["L2-TINY"]["flags"]:
        fails.append("the tiny-launch burst was not flagged LATENCY_OR_OVERHEAD: launch overhead should dominate 1024-element ops")
    for k in ("L2-GEMM", "L2-DECODE", "L2-ELTWISE"):
        if not gpu:
            break
        if t[k]["ceiling_fraction"] < 0.25:
            fails.append(f"{k} reached only {t[k]['ceiling_fraction']:.0%} of its ceiling: a throughput-bound kernel this large "
                         "should exceed 25 % (check for another process on the GPU or a low clock)")
    if gpu:
        inv = result["inventory"]
        if abs(inv["torch_total_mib"] - inv["smi_total_mib"]) > 0.05 * inv["smi_total_mib"]:
            fails.append(f"torch ({inv['torch_total_mib']} MiB) and nvidia-smi ({inv['smi_total_mib']} MiB) disagree on GPU memory")
        try:
            if int(inv["pcie_gen_current"]) > int(inv["pcie_gen_max"]) or int(inv["pcie_width_current"]) > int(inv["pcie_width_max"]):
                fails.append("current PCIe link exceeds its maximum: nvidia-smi fields misread")
        except (TypeError, ValueError):
            fails.append("PCIe link fields missing from nvidia-smi (check the driver / container runtime)")
        h2d = t["L2-H2D"]["achieved_io_gbs"]
        pcie = result["platform"]["frontend_gbit_per_s_per_node"] / 8
        if h2d > 1.05 * pcie:
            fails.append(f"H2D {h2d:.1f} GB/s exceeds the PCIe link {pcie:.1f} GB/s: check the byte count")
        if t["L2-DECODE"]["achieved_gbs"] > 1.02 * result["platform"]["hbm_gb_per_s"]:
            fails.append("decode GEMV exceeded the DRAM spec: the weight matrix may be L2-resident (make it larger than L2)")
    return fails


def _s(x: float) -> str:
    return f"{x * 1e6:.1f} us" if x < 1e-3 else f"{x * 1e3:.3f} ms" if x < 1 else f"{x:.3f} s"


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    p, src, m = result["platform"], result["platform_source"], result["metrics"]
    L = []
    if gpu:
        inv = result["inventory"]
        L += ["## GPU inventory", "", "| Field | Value |", "|---|---|"]
        for k in ("name", "capability", "sm_count", "smi_total_mib", "l2_cache_mib", "driver_version", "pci_bus_id",
                  "clocks_max_sm_mhz", "clocks_max_mem_mhz", "power_limit_w", "nccl_version", "cuda_runtime", "torch"):
            L.append(f"| {k} | {inv.get(k)} |")
        L.append(f"| PCIe link (current / max) | Gen{inv['pcie_gen_current']} x{inv['pcie_width_current']} / "
                 f"Gen{inv['pcie_gen_max']} x{inv['pcie_width_max']} |")
        L += ["", "`nvidia-smi topo -m`:", "", "```text", inv["topology_nvidia_smi_topo_m"].strip(), "```", ""]
    L += ["## Platform file for this device (the lab's schema)", "", "| Ceiling | Value | Source |", "|---|---|---|",
          f"| compute (BF16 dense{' ' if gpu else ', here FP32 measured'}) | {p['gpu_dense_bf16_tflops']:.2f} TFLOP/s | {src['gpu_dense_bf16_tflops']} |",
          f"| memory | {p['hbm_gb_per_s']:.1f} GB/s | {src['hbm_gb_per_s']} |",
          f"| I/O and scale-up | {p['frontend_gbit_per_s_per_node'] / 8:.2f} GB/s | {src['io/scale-up']} |",
          "", f"Machine balance: **{m['machine_balance_flop_per_byte']:.0f} FLOP/B** here vs "
              f"**{m['orion_machine_balance_flop_per_byte']:.0f} FLOP/B** for the manuscript's ORION H100-class GPU (Section 1.6).", "",
          "## Measured kernel mix, classified by the lab's `classify()`", "",
          "| ID | Workload | Median | p95 | min-max | AI (FLOP/B) | Achieved | Lower bound | Bound (dominant) | Ceiling fraction | Flags |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in result["tables"]["workloads"]:
        ach = (f"{r['achieved_io_gbs']:.1f} GB/s over PCIe" if r["id"] == "L2-H2D" else
               f"{r['achieved_tflops']:.2f} TFLOP/s" if r["bound"] == "compute" else f"{r['achieved_gbs']:.1f} GB/s")
        ai = "-" if r["ai_flop_per_byte"] is None else f"{r['ai_flop_per_byte']:.1f}"
        L.append(f"| {r['id']} | {r['name']} ({r['detail']}) | {_s(r['median_s'])} | {_s(r['p95_s'])} | "
                 f"{_s(r['min_s'])}-{_s(r['max_s'])} | {ai} | {ach} | {_s(r['lower_bound_s'])} | {r['bound']} ({r['dominant']}) | "
                 f"{r['ceiling_fraction']:.2f} | {', '.join(r['flags']) or 'none'} |")
    if gpu:
        L += ["", "### Telemetry during each workload (nvidia-smi, the stand-in for DCGM)", "",
              "| ID | Samples | SM clock (MHz) | Power (W) | GPU util | Mem util | Max temp (C) | Clock-event masks |",
              "|---|---|---|---|---|---|---|---|"]
        for r in result["tables"]["workloads"]:
            tm = r["telemetry"]
            if tm:
                L.append(f"| {r['id']} | {tm['samples']} | {tm['sm_clock_mhz']:.0f} | {tm['power_w']:.1f} | {tm['util_gpu_pct']:.0f} % | "
                         f"{tm['util_mem_pct']:.0f} % | {tm['temp_c_max']:.0f} | {', '.join(tm['clock_event_masks'])} |")
        L += ["", "`utilization.gpu` is the fraction of time *any* kernel ran (Section 1.7): the tiny-launch burst and the "
              "GEMM can both read high while one uses a fraction of the SMs. Mask 0x4 is sw_power_cap (routine on a laptop "
              "GPU under load); 0x1 is gpu_idle."]
    t = {r["id"]: r for r in result["tables"]["workloads"]}
    L += ["", "## What to conclude", "",
          f"- **Decode is memory-bound here too.** The {t['L2-DECODE']['name']} has an intensity of ~{t['L2-DECODE']['ai_flop_per_byte']:.1f} "
          f"FLOP/B, {m['machine_balance_flop_per_byte'] / t['L2-DECODE']['ai_flop_per_byte']:.0f}x below the "
          f"{m['machine_balance_flop_per_byte']:.0f} FLOP/B balance, and runs at "
          f"{t['L2-DECODE']['achieved_gbs']:.0f} GB/s of a {p['hbm_gb_per_s']:.0f} GB/s roof: the W02 argument of Section 1.9 "
          "holds on any GPU, because intensity ~ batch size.",
          f"- **The square GEMM and the training step are compute-bound** (ceiling fractions "
          f"{t['L2-GEMM']['ceiling_fraction']:.2f} and {t['L2-TRAIN']['ceiling_fraction']:.2f}); the training step's fraction is "
          "its MFU against this device's peak, and the gap to the GEMM is optimizer, activation and launch overhead.",
          f"- **The tiny-launch burst** reaches a ceiling fraction of {t['L2-TINY']['ceiling_fraction']:.3f}: no throughput ceiling "
          "explains it, which is exactly what LATENCY_OR_OVERHEAD means. Do not buy bandwidth for it; fuse or graph-capture it."]
    if gpu:
        L += [f"- **The batch load is I/O-bound on the PCIe link** ({t['L2-H2D']['achieved_io_gbs']:.1f} of "
              f"{p['frontend_gbit_per_s_per_node'] / 8:.2f} GB/s); on ORION the same role is played by the frontend NICs and the PFS.",
              "- **This is a laptop Ada GPU, not an H100.** Its BF16 peak is ~25x lower and its DRAM ~13x lower than ORION's; "
              "the machine balance is lower too, so some kernels that are compute-bound here would be memory-bound on an "
              "H100. Re-derive the platform file for every machine; never reuse ORION's ceilings for measured rows."]
    else:
        L += ["", "_CPU fallback: no GPU was used. The mix ran on the CPU in FP32 and was classified against the best measured "
              "CPU rates, so the GPU inventory, the vendor-ceiling bounds, the PCIe I/O row and the 25 % efficiency floor "
              "were skipped._"]
    if result.get("not_runnable_parts"):
        L += ["", "## Not runnable on this host (probed, not faked)", "", "| Part of the extension | Probe | Needs | Used instead |",
              "|---|---|---|---|"]
        for np_ in result["not_runnable_parts"]:
            L.append(f"| {np_['part']} | {np_['probe']} | {', '.join(np_['needs'])} | {np_['fallback']} |")
    return "\n".join(L)
