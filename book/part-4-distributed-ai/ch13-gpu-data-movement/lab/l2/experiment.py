"""Ch 13 L2: host<->GPU copy bandwidth (pinned vs pageable) and copy/compute overlap on a real GPU.

What it teaches (Sections 13.2-13.4): a host-to-device copy is bounded by the GPU's PCIe link (the
ceiling uses the maximum-capability generation and width, because an idle link may train down), pageable memory adds a staging copy, small transfers are latency-bound, and a
copy on a second stream can hide behind compute. CPU fallback: the same size sweep measures
host-memory copy bandwidth (the staging cost pageable transfers pay), and the overlap test uses two
threads; the GPU-only invariants are skipped and the report says so.
"""
from __future__ import annotations

import os
import threading

EXPERIMENT = {
    "id": "ch13-l2",
    "title": "Lab 13 L2: host-GPU copy bandwidth and copy/compute overlap",
    "evidence": "MEASURED",
    "cpu_fallback": "host-memory copy bandwidth sweep and a two-thread overlap test (no PCIe involved)",
}

PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}  # GB/s per lane after encoding


def link_ceiling_gbs(env: dict) -> float | None:
    g = (env.get("gpus") or [{}])[0]
    try:
        return PCIE_GBPS_PER_LANE[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"])
    except (KeyError, ValueError):
        return None


def run(ctx) -> dict:
    torch = ctx.torch
    sizes_mib = [1, 16, 256] if ctx.quick else [0.0625, 1, 4, 16, 64, 256, 1024]
    rows = []
    for mib in sizes_mib:
        n = int(mib * 1024 * 1024)
        if ctx.is_gpu:
            dev = torch.empty(n, dtype=torch.uint8, device="cuda")
            pageable = torch.empty(n, dtype=torch.uint8)
            pinned = torch.empty(n, dtype=torch.uint8).pin_memory()
            cases = {
                "h2d_pageable": lambda: dev.copy_(pageable),
                "h2d_pinned": lambda: dev.copy_(pinned, non_blocking=True),
                "d2h_pinned": lambda: pinned.copy_(dev, non_blocking=True),
            }
        else:
            src, dst = torch.empty(n, dtype=torch.uint8), torch.empty(n, dtype=torch.uint8)
            cases = {"host_copy": lambda: dst.copy_(src)}
        for name, fn in cases.items():
            st = ctx.bench(fn, warmup=3, reps=ctx.reps(20 if mib <= 16 else 10))
            rows.append({"case": name, "size_mib": mib, "median_s": st["median"], "p95_s": st["p95"],
                         "iqr_s": st["iqr"], "n": st["n"], "gbs_median": n / st["median"] / 1e9})
        ctx.log(f"{mib:>8} MiB  " + "  ".join(f"{r['case']}={r['gbs_median']:.2f} GB/s" for r in rows if r["size_mib"] == mib))

    overlap = measure_overlap(ctx)
    ib = sorted(os.listdir("/sys/class/infiniband")) if os.path.isdir("/sys/class/infiniband") else []
    not_runnable_parts = [] if ib else [{
        "part": "GPU<->NIC GPUDirect RDMA locality (Table 13.5 rows 2-3, 5-8 and 11, exercise 13.11)",
        "reason": "no RDMA device under /sys/class/infiniband on this host",
        "needs": ["RDMA NIC (mlx5-class) on the GPU's PCIe switch", "perftest built with CUDA", "a second node"],
    }]
    big = max(sizes_mib)
    metrics = {f"{r['case']}_gbs_at_{big:g}MiB": round(r["gbs_median"], 3) for r in rows if r["size_mib"] == big}
    metrics.update({f"overlap_{k}": v for k, v in overlap.items()})
    return {"metrics": metrics, "tables": {"bandwidth": rows}, "rdma_devices": ib,
            "not_runnable_parts": not_runnable_parts, "notes": [
        "Median of >= 5 timed repetitions after 3 warm-ups; CUDA events on the GPU, perf_counter on the CPU.",
        "PCIe ceiling = per-lane rate after encoding x maximum link generation and width from nvidia-smi (pcie.link.gen.max, pcie.link.width.max): the maximum-capability link, an upper bound; an idle link may train down.",
    ]}


def measure_overlap(ctx) -> dict:
    torch = ctx.torch
    if ctx.is_gpu:
        n = (64 if ctx.quick else 256) * 1024 * 1024
        host = torch.empty(n, dtype=torch.uint8).pin_memory()
        dev = torch.empty(n, dtype=torch.uint8, device="cuda")
        a = torch.randn(4096, 4096, device="cuda")
        copy_stream = torch.cuda.Stream()

        def compute():
            for _ in range(8):
                a @ a

        def copy():
            with torch.cuda.stream(copy_stream):
                dev.copy_(host, non_blocking=True)

        def serial():
            compute()
            torch.cuda.synchronize()
            copy()
            torch.cuda.synchronize()

        def overlapped():
            copy()
            compute()
            torch.cuda.synchronize()

        t_compute = ctx.bench(compute)["median"]
        t_copy = ctx.bench(lambda: (copy(), torch.cuda.synchronize()))["median"]
        t_serial = ctx.bench(serial)["median"]
        t_over = ctx.bench(overlapped)["median"]
    else:
        n = (32 if ctx.quick else 128) * 1024 * 1024
        src, dst = torch.empty(n, dtype=torch.uint8), torch.empty(n, dtype=torch.uint8)
        a = torch.randn(1024, 1024)

        def compute():
            for _ in range(4):
                a @ a

        def copy():
            dst.copy_(src)

        def serial():
            compute()
            copy()

        def overlapped():
            t = threading.Thread(target=copy)
            t.start()
            compute()
            t.join()

        t_compute, t_copy = ctx.bench(compute)["median"], ctx.bench(copy)["median"]
        t_serial, t_over = ctx.bench(serial)["median"], ctx.bench(overlapped)["median"]
    hidden = max(0.0, (t_serial - t_over) / t_copy) if t_copy > 0 else 0.0
    return {"compute_s": round(t_compute, 6), "copy_s": round(t_copy, 6), "serial_s": round(t_serial, 6),
            "overlapped_s": round(t_over, 6), "copy_hidden_fraction": round(min(hidden, 1.0), 3)}


def check(result: dict, env: dict) -> list[str]:
    rows = result["tables"]["bandwidth"]
    fails = []
    if any(r["gbs_median"] <= 0 for r in rows):
        fails.append("non-positive bandwidth")
    by = {(r["case"], r["size_mib"]): r["gbs_median"] for r in rows}
    sizes = sorted({r["size_mib"] for r in rows})
    o = result["metrics"]
    if env["device"] == "cuda":
        ceiling = link_ceiling_gbs(env)
        big = sizes[-1]
        if ceiling and by[("h2d_pinned", big)] > 1.05 * ceiling:
            fails.append(f"pinned H2D {by[('h2d_pinned', big)]:.1f} GB/s exceeds the PCIe ceiling {ceiling:.1f} GB/s")
        if ceiling and by[("h2d_pinned", big)] < 0.4 * ceiling:
            fails.append(f"pinned H2D {by[('h2d_pinned', big)]:.1f} GB/s is < 40 % of the {ceiling:.1f} GB/s link: check link state")
        if by[("h2d_pinned", big)] < by[("h2d_pageable", big)] * 0.95:
            fails.append("pinned H2D should not be slower than pageable at the largest size")
        if by[("h2d_pinned", sizes[0])] >= by[("h2d_pinned", big)]:
            fails.append("small copies should be latency-bound (lower GB/s than large copies)")
        if o["overlap_overlapped_s"] > o["overlap_serial_s"] * 1.05:
            fails.append("overlapped copy+compute took longer than doing them serially")
    else:
        # CPU fallback: copy and matmul compete for the same cores and memory bandwidth, so overlap is
        # informational only; the invariant is that host copies stay within a sane DRAM range.
        if max(r["gbs_median"] for r in rows) > 500:
            fails.append("host copy above 500 GB/s: timer or size bug")
    return fails


def report(result: dict, env: dict) -> str:
    ceiling = link_ceiling_gbs(env) if env["device"] == "cuda" else None
    lines = ["## Bandwidth sweep (median of repetitions)", "", "| Case | Size (MiB) | GB/s | p95 time (ms) | n |", "|---|---|---|---|---|"]
    for r in result["tables"]["bandwidth"]:
        lines.append(f"| {r['case']} | {r['size_mib']:g} | {r['gbs_median']:.2f} | {r['p95_s'] * 1e3:.3f} | {r['n']} |")
    if ceiling:
        lines += ["", f"PCIe ceiling from the maximum-capability link: **{ceiling:.1f} GB/s** per direction `[MODELED]`."]
    m = result["metrics"]
    lines += ["", "## Copy/compute overlap", "",
              f"compute {m['overlap_compute_s'] * 1e3:.1f} ms, copy {m['overlap_copy_s'] * 1e3:.1f} ms, "
              f"serial {m['overlap_serial_s'] * 1e3:.1f} ms, overlapped {m['overlap_overlapped_s'] * 1e3:.1f} ms "
              f"-> {m['overlap_copy_hidden_fraction'] * 100:.0f} % of the copy hidden."]
    for part in result.get("not_runnable_parts", []):
        lines += ["", f"**Not runnable here:** {part['part']}: {part['reason']}. Needs: {', '.join(part['needs'])}."]
    if env["device"] != "cuda":
        lines += ["", "_CPU fallback: no PCIe transfer was measured; these are host-memory copies, the staging step a pageable "
                  "H2D transfer pays on a GPU host._"]
    return "\n".join(lines)
