"""Ch 12 L2: what one GPU can tell you about collectives - NCCL bring-up, the per-call floor, and the
reduction kernel - fitted with the lab's alpha-beta model.

The L2 extension in the README needs an 8-GPU host and nccl-tests. This machine has one GPU, so every
multi-GPU collective is **not runnable** here, and it is recorded that way after probing
(``torch.cuda.device_count()``, ``nvidia-smi topo -m``, ``nvidia-smi nvlink -s``,
``/sys/class/infiniband``). What one GPU *can* measure, and what Sections 12.2-12.3 use:

1. **NCCL bring-up with world_size 1**: ``init_process_group("nccl")`` + communicator creation time,
   and the NCCL version actually linked into PyTorch.
2. **The per-call floor (alpha)**: a world-size-1 NCCL all_reduce sweep from 8 B up. With one rank
   there is nothing to send, so this is pure software + launch cost: the lowest alpha any NCCL
   collective on this stack can have. Fitted with the lab's ``t = alpha + factor*S/B``.
3. **The reduction kernel**: every ring step ends in ``dst = a + b`` on the receiving GPU. Its
   bandwidth sets a ceiling on reduce-scatter/all-reduce busbw that is independent of the links.
   Swept over message size, fitted with alpha-beta, and bounded by the GPU's DRAM bandwidth.
4. **A real two-rank collective**: the lab's ``optional/gloo_allreduce.py`` (gloo over loopback, two
   processes), parsed and fitted with the same model. It is CPU/TCP, never comparable with NCCL.

CPU fallback: (1) and (2) use the gloo backend with world_size 1, (3) is ``a + b`` on host memory, and
(4) runs unchanged; GPU-only invariants (DRAM bound, NCCL version) are skipped.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch12-l2",
    "title": "Lab 12 L2: NCCL bring-up, per-call floor and reduction-kernel bandwidth on one GPU",
    "evidence": "MEASURED",
    "cpu_fallback": ("gloo world_size-1 init and all_reduce floor sweep, a host-memory a+b reduction sweep, and a "
                     "two-process gloo all_reduce over loopback; all fitted with the lab's alpha-beta model"),
}

PKG = Path(__file__).resolve().parents[2]
# GDDR6/HBM bus widths (bits) for DRAM peak = memory clock x 2 (DDR) x width/8. NVIDIA product pages.
BUS_WIDTH_BITS = {"RTX 4060 Laptop": 128, "RTX 4060": 128, "RTX 4070 Laptop": 128, "RTX 4090": 384}
L2_CACHE_MIB = {"RTX 4060 Laptop": 32, "RTX 4060": 24, "RTX 4090": 72}


def _lab_model():
    """The lab's alpha-beta fit and log parser: the reference solution when present (instructor copy),
    else the learner's module; None if neither is implemented."""
    for path in (PKG / "solutions" / "lab" / "nccl_analysis.py", PKG / "lab" / "starter" / "nccl_analysis.py"):
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"nccl_analysis_{path.parent.name}", path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            import pandas as pd
            probe = pd.DataFrame({"size": [8, 1 << 20], "time_us": [10.0, 20.0], "time_us_ip": [10.0, 20.0]})
            mod.fit_alpha_beta(probe, 2)
            return mod, path.relative_to(PKG).as_posix()
        except Exception:  # starter not implemented yet
            continue
    return None, "none"


def fit(sizes, times_us, n: int, op: str):
    """alpha-beta fit via the lab's fit_alpha_beta (weighted by 1/t); local equivalent if unavailable."""
    mod, _ = _lab_model()
    if mod is not None:
        import pandas as pd
        df = pd.DataFrame({"size": sizes, "time_us": times_us, "time_us_ip": times_us})
        return mod.fit_alpha_beta(df, n, op)
    import numpy as np
    f = {"all_reduce": 2 * (n - 1) / n}.get(op, 1.0)
    s, t = np.asarray(sizes, float), np.asarray(times_us, float)
    w = 1.0 / t
    coef, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(s), f * s]) * w[:, None], t * w, rcond=None)
    b = 1.0 / (coef[1] * 1e-6) / 1e9
    return {"alpha_us": float(coef[0]), "busbw_fit_GBps": b, "n_half_bytes": coef[0] * 1e-6 * b * 1e9 / f}


def _sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return -1, str(exc)


def probe_hardware(torch) -> dict:
    n_gpu = torch.cuda.device_count() if torch.cuda.is_available() else 0
    topo = _sh(["nvidia-smi", "topo", "-m"])[1] if shutil.which("nvidia-smi") else "nvidia-smi absent"
    nvl = _sh(["nvidia-smi", "nvlink", "-s"])[1] if shutil.which("nvidia-smi") else "nvidia-smi absent"
    ib = sorted(os.listdir("/sys/class/infiniband")) if os.path.isdir("/sys/class/infiniband") else []
    return {"cuda_device_count": n_gpu, "nvidia_smi_topo_m": topo[:2000], "nvidia_smi_nvlink_s": nvl[:1000],
            "nvlink_active": "GB/s" in nvl, "infiniband_devices": ib, "nccl_tests_on_path": bool(shutil.which("all_reduce_perf"))}


def sizes_bytes(quick: bool) -> list[int]:
    exps = [3, 10, 16, 20, 24, 27] if quick else list(range(3, 30, 2))   # 8 B .. 128 MiB / 512 MiB
    return [1 << e for e in exps]


def iters_for(nbytes: int) -> int:
    """Calls per timed sample so that one sample is >> timer resolution."""
    return max(1, min(200, (64 << 20) // max(nbytes, 1)))


def measure_collective_floor(ctx, store_dir: str) -> dict:
    """init + world_size-1 all_reduce sweep with NCCL (GPU) or gloo (CPU)."""
    torch = ctx.torch
    import torch.distributed as dist
    backend = "nccl" if ctx.is_gpu else "gloo"
    init_s = []
    for i in range(ctx.reps(5)):
        store = dist.FileStore(os.path.join(store_dir, f"store{i}"), 1)
        t0 = time.perf_counter()
        kw = {"device_id": torch.device("cuda", 0)} if ctx.is_gpu else {}
        dist.init_process_group(backend, store=store, rank=0, world_size=1, **kw)
        warm = torch.ones(1, device=ctx.device)
        dist.all_reduce(warm)                     # communicator is usable end-to-end
        ctx.sync()
        init_s.append(time.perf_counter() - t0)
        if i < ctx.reps(5) - 1:
            dist.destroy_process_group()
    import hwlab
    rows = []
    for nbytes in sizes_bytes(ctx.quick):
        buf = torch.ones(max(1, nbytes // 4), dtype=torch.float32, device=ctx.device)
        k = iters_for(nbytes)

        def op():
            for _ in range(k):
                dist.all_reduce(buf)
        st = ctx.bench(op, warmup=3, reps=ctx.reps(10))
        rows.append({"size": buf.numel() * 4, "time_us": st["median"] / k * 1e6, "p95_us": st["p95"] / k * 1e6,
                     "min_us": st["min"] / k * 1e6,
                     "iqr_us": st["iqr"] / k * 1e6, "calls_per_sample": k, "n": st["n"]})
    dist.destroy_process_group()
    ab = fit([r["size"] for r in rows], [r["time_us"] for r in rows], 1, "reduce")
    return {"backend": backend, "init": hwlab.summarize(init_s), "rows": rows, "fit": ab}


def measure_reduction_kernel(ctx) -> dict:
    torch = ctx.torch
    rows = []
    for nbytes in sizes_bytes(ctx.quick):
        n = max(1, nbytes // 4)
        a, b = torch.ones(n, device=ctx.device), torch.ones(n, device=ctx.device)
        out = torch.empty_like(a)
        k = iters_for(nbytes)

        def op():
            for _ in range(k):
                torch.add(a, b, out=out)
        st = ctx.bench(op, warmup=3, reps=ctx.reps(10))
        t = st["median"] / k
        rows.append({"size": n * 4, "time_us": t * 1e6, "p95_us": st["p95"] / k * 1e6, "iqr_us": st["iqr"] / k * 1e6,
                     "min_us": st["min"] / k * 1e6,
                     "algbw_GBps": n * 4 / t / 1e9, "dram_traffic_GBps": 3 * n * 4 / t / 1e9,
                     "calls_per_sample": k, "n": st["n"]})
        del a, b, out
    if ctx.is_gpu:
        torch.cuda.empty_cache()
    ab = fit([r["size"] for r in rows], [r["time_us"] for r in rows], 1, "reduce")
    # best-of-n series: the uncontended cost, used by the physical invariants (robust to GPU time-slicing)
    ab_min = fit([r["size"] for r in rows], [r["min_us"] for r in rows], 1, "reduce")
    return {"rows": rows, "fit": ab, "fit_min": ab_min}


def measure_gloo_two_rank(ctx) -> dict:
    script = PKG / "lab" / "optional" / "gloo_allreduce.py"
    max_bytes = (4 << 20) if ctx.quick else (64 << 20)
    cmd = [sys.executable, str(script), "--world", "2", "--max-bytes", str(max_bytes), "--warmup", "5",
           "--iters", "10" if ctx.quick else "20", "--port", "29531"]
    rc, out = _sh(cmd, timeout=600)
    if rc != 0:
        return {"ran": False, "error": out[-1500:]}
    rows = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 13 and parts[0].isdigit():
            rows.append({"size": int(parts[0]), "time_us": float(parts[5]), "busbw_GBps": float(parts[7])})
    ab = fit([r["size"] for r in rows], [r["time_us"] for r in rows], 2, "all_reduce")
    return {"ran": True, "rows": rows, "fit": ab, "command": " ".join(cmd[1:]).replace(str(PKG) + "/", "")}


def lab_reference() -> dict:
    """alpha and B the lab's own model fits on the synthetic 8 x H100 single-node log (c1)."""
    mod, _ = _lab_model()
    if mod is None:
        return {}
    meta, df = mod.parse_nccl_log((PKG / "lab" / "data" / "c1_1node_8gpu.log").read_text(encoding="utf-8"))
    f = mod.fit_alpha_beta(df, meta["nranks"])
    return {"c1_alpha_us": f["alpha_us"], "c1_busbw_fit_GBps": f["busbw_fit_GBps"], "c1_nranks": meta["nranks"],
            "c1_plateau_busbw": mod.plateau_busbw(df)}


def dram_peak_gbs(env: dict) -> tuple[float | None, float | None, str]:
    name = env.get("gpu0", {}).get("name", "")
    g = (env.get("gpus") or [{}])[0]
    for key, width in BUS_WIDTH_BITS.items():
        if key in name and (key != "RTX 4060" or "Laptop" not in name):
            try:
                mclk = float(g["clocks.max.memory"]) * 1e6
            except (KeyError, ValueError):
                return None, None, "memory clock unavailable"
            return (mclk * 2 * width / 8 / 1e9, L2_CACHE_MIB.get(key),
                    f"{g['clocks.max.memory']} MHz x 2 (DDR) x {width}-bit bus ({key}, NVIDIA spec)")
    return None, None, f"no bus-width entry for {name}"


def run(ctx) -> dict:
    torch = ctx.torch
    hw = probe_hardware(torch)
    needs = []
    if hw["cuda_device_count"] < 2:
        needs.append(f"2+ GPUs in one host (found {hw['cuda_device_count']})")
    if not hw["nvlink_active"]:
        needs.append("NVLink/NVSwitch between GPUs (nvidia-smi nvlink -s shows no active links)")
    if not hw["infiniband_devices"]:
        needs.append("RDMA NICs for the L3 multi-node runs (/sys/class/infiniband is empty or absent)")
    if not hw["nccl_tests_on_path"]:
        needs.append("nccl-tests all_reduce_perf built against this CUDA/NCCL (not in the image)")
    not_runnable_parts = [
        {"part": "L2: all_reduce_perf -g 8 sweep, plateau busbw, 8 B latency over 5 launches",
         "reason": "; ".join(needs) or "n/a", "needs": ["1 x 8-GPU host with NVLink", "nccl-tests"]},
        {"part": "L3: multi-node rail-pinned all_reduce_perf, ib_write_bw per rail",
         "reason": "single host, no RDMA NIC", "needs": ["2+ HX8-class nodes", "RoCEv2/InfiniBand NICs", "MPI or Slurm"]},
    ]
    ctx.log("not runnable here: " + "; ".join(needs))

    with tempfile.TemporaryDirectory() as tmp:
        floor = measure_collective_floor(ctx, tmp)
    ctx.log(f"{floor['backend']} world=1 init p50 {floor['init']['median'] * 1e3:.1f} ms; "
            f"all_reduce floor alpha {floor['fit']['alpha_us']:.2f} us")
    red = measure_reduction_kernel(ctx)
    ctx.log(f"reduction kernel alpha {red['fit']['alpha_us']:.2f} us, B {red['fit']['busbw_fit_GBps']:.1f} GB/s; "
            f"largest {red['rows'][-1]['algbw_GBps']:.1f} GB/s algbw")
    gloo = measure_gloo_two_rank(ctx)
    if gloo["ran"]:
        ctx.log(f"gloo 2-rank loopback alpha {gloo['fit']['alpha_us']:.1f} us, B {gloo['fit']['busbw_fit_GBps']:.2f} GB/s")
    ref = lab_reference()
    _, model_src = _lab_model()

    metrics = {
        "backend": floor["backend"],
        "init_p50_ms": floor["init"]["median"] * 1e3, "init_p95_ms": floor["init"]["p95"] * 1e3,
        "floor_alpha_us": floor["fit"]["alpha_us"],
        "floor_8B_p50_us": floor["rows"][0]["time_us"],
        "reduction_alpha_us": red["fit"]["alpha_us"], "reduction_B_fit_GBps": red["fit"]["busbw_fit_GBps"],
        "reduction_n_half_bytes": red["fit"]["n_half_bytes"],
        "reduction_alpha_min_us": red["fit_min"]["alpha_us"], "reduction_B_min_fit_GBps": red["fit_min"]["busbw_fit_GBps"],
        "reduction_algbw_largest_GBps": red["rows"][-1]["algbw_GBps"],
        "reduction_dram_traffic_largest_GBps": red["rows"][-1]["dram_traffic_GBps"],
        "gloo2_alpha_us": gloo["fit"]["alpha_us"] if gloo["ran"] else None,
        "gloo2_busbw_fit_GBps": gloo["fit"]["busbw_fit_GBps"] if gloo["ran"] else None,
        "alpha_beta_model_source": model_src, **ref,
    }
    if ctx.is_gpu:
        metrics["nccl_version"] = ".".join(map(str, torch.cuda.nccl.version()))
    notes = [
        f"alpha-beta fits use the lab's fit_alpha_beta ({model_src}): t = alpha + factor*S/B, least squares "
        "weighted by 1/t. World-size-1 and the a+b kernel use factor 1 (no bus correction applies).",
        "Tables and fits report medians. The physical invariants (monotonicity, DRAM bound, fit quality) use the "
        "best-of-n sample per size, the uncontended cost, so that GPU time-slicing with another process cannot "
        "fail or pass them by accident.",
        "Small sizes run many calls per timed sample (calls_per_sample) so the sample is >> timer resolution; "
        "times are medians of >= 5 samples after 3 warm-ups.",
        "Not runnable on this host: " + "; ".join(p["part"] for p in not_runnable_parts)
        + ". Needs: " + "; ".join(needs) + ".",
        "gloo over loopback measures CPU memory copies and the TCP stack: never compare it with NCCL.",
    ]
    if not ctx.is_gpu:
        notes.append("CPU fallback: the floor sweep uses gloo (world_size 1) and the reduction kernel runs on host "
                     "memory; no GPU, NCCL or DRAM-bound invariant applies.")
    return {"metrics": metrics, "not_runnable_parts": not_runnable_parts, "probe": hw,
            "tables": {"collective_floor": floor["rows"], "reduction_kernel": red["rows"],
                       "gloo_two_rank": gloo.get("rows", [])},
            "gloo": {k: v for k, v in gloo.items() if k != "rows"}, "notes": notes}


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    gpu = env["device"] == "cuda"
    if result["probe"]["cuda_device_count"] >= 2 and gpu:
        fails.append("2+ GPUs are visible: run the real multi-GPU nccl-tests sweep (README Section 8) "
                     "instead of recording it as not runnable")
    red = t["reduction_kernel"]
    if any(r["time_us"] <= 0 for r in red + t["collective_floor"]):
        fails.append("non-positive time: check the timer and synchronisation")
    if m["floor_alpha_us"] <= 0 or m["reduction_alpha_us"] <= 0:
        fails.append("alpha fit <= 0: the small-size points are not latency-bound; check calls_per_sample")
    # monotonic in the bandwidth region: a bigger reduction never takes less time (best-of-n, 10 % allowance).
    # Below ~1 MiB the call is latency-bound and differences are launch jitter, not physics.
    bw_region = [r for r in red if r["size"] >= (1 << 20)]
    for r1, r2 in zip(bw_region, bw_region[1:]):
        if r2["min_us"] < 0.9 * r1["min_us"]:
            fails.append(f"reduction time fell from {r1['size']} B to {r2['size']} B: device shared or clocks "
                         "changing mid-run; rerun on an idle device")
            break
    if red[0]["algbw_GBps"] >= red[-1]["algbw_GBps"]:
        fails.append("8 B reductions should be latency-bound (lower GB/s than the largest size)")
    big = red[-1]
    if m["reduction_B_min_fit_GBps"] <= 0:
        fails.append("alpha-beta fit gave a non-positive bandwidth: the sweep has no bandwidth-bound points")
    if result["gloo"].get("ran") is False:
        fails.append("the two-rank gloo all_reduce failed: " + result["gloo"].get("error", "")[-300:])
    if gpu:
        peak, l2_mib, _ = dram_peak_gbs(env)
        if peak:
            for r in red:
                best = 3 * r["size"] / (r["min_us"] * 1e-6) / 1e9
                if r["size"] >= 4 * (l2_mib or 0) * 2**20 and best > 1.05 * peak:
                    fails.append(f"a+b at {r['size']} B moved {best:.0f} GB/s > DRAM peak "
                                 f"{peak:.0f} GB/s: check the byte count (2 reads + 1 write)")
            best_big = 3 * big["size"] / (big["min_us"] * 1e-6) / 1e9
            if best_big < 0.4 * peak:
                fails.append(f"a+b reached only {best_big:.0f} GB/s of {peak:.0f} GB/s DRAM peak: "
                             "check clocks (nvidia-smi -q -d PERFORMANCE) or other GPU tenants")
        if not m.get("nccl_version"):
            fails.append("NCCL version not recorded")
        if m["floor_alpha_us"] > 200:
            fails.append(f"NCCL world-1 alpha {m['floor_alpha_us']:.0f} us is implausibly high: check for "
                         "NCCL_DEBUG/blocking-wait settings or a shared GPU")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    lines = ["## Not runnable on this host", "", "| Part | Why | Needs |", "|---|---|---|"]
    for p in result["not_runnable_parts"]:
        lines.append(f"| {p['part']} | {p['reason']} | {', '.join(p['needs'])} |")
    lines += ["", f"Probe: `torch.cuda.device_count()` = {result['probe']['cuda_device_count']}, NVLink active = "
              f"{result['probe']['nvlink_active']}, /sys/class/infiniband = {result['probe']['infiniband_devices'] or 'none'}.",
              "", f"## {m['backend'].upper()} bring-up, world_size 1", "",
              f"init_process_group + first all_reduce: p50 **{m['init_p50_ms']:.1f} ms**, p95 {m['init_p95_ms']:.1f} ms"
              + (f"; NCCL {m['nccl_version']}." if gpu else "."),
              "", "## Per-call floor and reduction kernel (median per call)", "",
              "| Size (B) | world-1 all_reduce (us) | a+b kernel (us) | a+b p95 (us) | a+b algbw (GB/s) | a+b DRAM traffic (GB/s) |",
              "|---|---|---|---|---|---|"]
    for f, r in zip(t["collective_floor"], t["reduction_kernel"]):
        lines.append(f"| {r['size']} | {f['time_us']:.2f} | {r['time_us']:.2f} | {r['p95_us']:.2f} | "
                     f"{r['algbw_GBps']:.2f} | {r['dram_traffic_GBps']:.1f} |")
    lines += ["", "## alpha-beta fits (`fit_alpha_beta`, weighted by 1/t)", "",
              "| Series | alpha (us) | B (GB/s) | Note |", "|---|---|---|---|",
              f"| {m['backend']} world-1 all_reduce | {m['floor_alpha_us']:.2f} | - | software + launch floor; no data moves |",
              f"| a+b reduction kernel | {m['reduction_alpha_us']:.2f} | {m['reduction_B_fit_GBps']:.1f} | "
              f"n_half = {m['reduction_n_half_bytes'] / 1e3:.0f} kB |"]
    if m["gloo2_alpha_us"] is not None:
        lines.append(f"| gloo 2-rank loopback all_reduce | {m['gloo2_alpha_us']:.1f} | {m['gloo2_busbw_fit_GBps']:.2f} | "
                     "CPU + TCP; not comparable with NCCL |")
    if m.get("c1_alpha_us") is not None:
        lines.append(f"| lab c1: 8 x H100 NVLink (SIMULATED) | {m['c1_alpha_us']:.1f} | {m['c1_busbw_fit_GBps']:.0f} | "
                     "the lab's synthetic log, same fit |")
    if gpu:
        peak, l2_mib, src = dram_peak_gbs(env)
        if peak:
            lines += ["", f"DRAM peak `[VENDOR-SPEC]`: **{peak:.0f} GB/s** ({src}); L2 cache {l2_mib} MiB. "
                      f"The a+b kernel reached {m['reduction_dram_traffic_largest_GBps']:.0f} GB/s of traffic "
                      f"({m['reduction_dram_traffic_largest_GBps'] / peak * 100:.0f} % of peak) at the largest size; "
                      "points below ~4 x L2 can exceed DRAM rate because they hit in cache."]
    lines += ["", "## What to conclude", "",
              "- alpha has a floor you can measure on one GPU: the world-1 call cost is pure software/launch. The lab's "
              "8-GPU alpha (tens of us) is that floor plus link latency times the algorithm's step count (Section 12.3).",
              "- The reduction kernel is a + b over 3 S bytes of memory traffic, so its rate is ~DRAM/3. On an H100 "
              "(3.35 TB/s HBM) that is ~1.1 TB/s, far above NVLink busbw (~360-480 GB/s): reductions do not limit "
              "NVLink all-reduce there. On this laptop GPU the same ratio holds against PCIe (~15.75 GB/s).",
              "- Below n_half the fixed cost dominates: bucket small gradients (DDP's 25 MB buckets) to stay on the "
              "bandwidth side of the curve."]
    if gpu:
        lines += ["", "_Laptop Ada GPU (RTX 4060 class, 128-bit GDDR6), not H100: compare shapes and ratios, not "
                  "absolute numbers. No multi-GPU collective was measured._"]
    else:
        lines += ["", "_CPU fallback: gloo replaced NCCL and host memory replaced GPU DRAM. GPU-only invariants (DRAM "
                  "bound, NCCL version, alpha plausibility) were skipped._"]
    return "\n".join(lines)
