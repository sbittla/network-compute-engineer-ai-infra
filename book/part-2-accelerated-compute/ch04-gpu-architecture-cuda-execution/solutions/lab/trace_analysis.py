#!/usr/bin/env python3
"""Chapter 4 lab — reference solution: analyse a profiler-style trace of a training step.

Inputs (lab/data/):
    gpu_trace.csv       GPU activities (kernels, memcpys) with stream, start/end (ns), launch config,
                        copy kind and memory kind, and per-kernel FLOP / DRAM-byte counters.
    cuda_api_trace.csv  CPU-side CUDA API calls (cudaLaunchKernel, cudaMemcpyAsync, sync calls)
                        joined to GPU activities by correlation_id.
    nvtx_ranges.csv     CPU-side NVTX ranges (train_step_N, forward, backward, ...).
    device.json         Device limits for the occupancy calculation and peak rates.

All times are integer nanoseconds. Fractions are 0..1. Bandwidths are GB/s (1e9 B/s).

CLI:
    python trace_analysis.py --data ../../lab/data --out report.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

SYNC_APIS = {"cudaStreamSynchronize", "cudaDeviceSynchronize", "cudaEventSynchronize"}
TINY_KERNEL_NS = 10_000
LAUNCH_LATENCY_NS = 10_000  # submit-to-start latency allowance (API start -> earliest GPU start)
LOW_OCC_THRESHOLD = 0.25
LOW_ROOF_FRACTION = 0.35
MIN_TIME_SHARE = 0.02


@dataclass
class Trace:
    gpu: pd.DataFrame
    api: pd.DataFrame
    nvtx: pd.DataFrame
    device: dict


def load_trace(data_dir: str | Path) -> Trace:
    """Load the four input files. Provided to learners (not a TODO)."""
    d = Path(data_dir)
    gpu = pd.read_csv(d / "gpu_trace.csv", keep_default_na=False)
    api = pd.read_csv(d / "cuda_api_trace.csv")
    nvtx = pd.read_csv(d / "nvtx_ranges.csv")
    device = json.loads((d / "device.json").read_text(encoding="utf-8"))
    return Trace(gpu=gpu, api=api, nvtx=nvtx, device=device)


# --------------------------------------------------------------------------------------
# Task 1 — interval arithmetic and utilisation
# --------------------------------------------------------------------------------------
def merge_intervals(intervals: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping/touching [start, end) intervals (ns). Returns a sorted, disjoint list."""
    out: list[list[int]] = []
    for s, e in sorted((int(s), int(e)) for s, e in intervals if e > s):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def _clip(intervals: Iterable[tuple[int, int]], start: int, end: int) -> list[tuple[int, int]]:
    return [(max(s, start), min(e, end)) for s, e in intervals if e > start and s < end]


def busy_ns(intervals: Iterable[tuple[int, int]]) -> int:
    """Total covered time (ns) of a set of possibly overlapping intervals."""
    return sum(e - s for s, e in merge_intervals(intervals))


def _intersect_ns(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> int:
    """Overlap (ns) between two *merged* interval lists."""
    i = j = total = 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if hi > lo:
            total += hi - lo
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return total


def step_windows(nvtx: pd.DataFrame, prefix: str = "train_step_") -> list[tuple[str, int, int]]:
    """Return (name, start_ns, end_ns) for every top-level step range, in time order."""
    steps = nvtx[nvtx["name"].str.startswith(prefix)].sort_values("start_ns")
    return [(r.name, int(r.start_ns), int(r.end_ns)) for r in steps.itertuples(index=False)]


def utilization(gpu: pd.DataFrame, start: int, end: int) -> dict:
    """GPU busy fractions inside [start, end).

    Returns dict with window_ns, busy_any_ns, busy_kernel_ns, busy_copy_ns, busy_any_frac,
    busy_kernel_frac. "Busy" means *some* activity was executing — it says nothing about how
    many SMs were active (see manuscript Section 4.8).
    """
    win = end - start
    k = gpu[gpu["kind"] == "kernel"]
    c = gpu[gpu["kind"] == "memcpy"]
    any_iv = _clip(zip(gpu["start_ns"], gpu["end_ns"]), start, end)
    k_iv = _clip(zip(k["start_ns"], k["end_ns"]), start, end)
    c_iv = _clip(zip(c["start_ns"], c["end_ns"]), start, end)
    b_any, b_k, b_c = busy_ns(any_iv), busy_ns(k_iv), busy_ns(c_iv)
    return {"window_ns": win, "busy_any_ns": b_any, "busy_kernel_ns": b_k, "busy_copy_ns": b_c,
            "busy_any_frac": b_any / win, "busy_kernel_frac": b_k / win}


def copy_compute_overlap(gpu: pd.DataFrame, start: int, end: int) -> dict:
    """How much copy time ran concurrently with kernel execution inside [start, end).

    Returns copy_ns (union of copy intervals), overlapped_ns, overlap_frac (= overlapped/copy).
    """
    k = gpu[gpu["kind"] == "kernel"]
    c = gpu[gpu["kind"] == "memcpy"]
    k_iv = merge_intervals(_clip(zip(k["start_ns"], k["end_ns"]), start, end))
    c_iv = merge_intervals(_clip(zip(c["start_ns"], c["end_ns"]), start, end))
    copy_ns = sum(e - s for s, e in c_iv)
    ov = _intersect_ns(c_iv, k_iv)
    return {"copy_ns": copy_ns, "overlapped_ns": ov, "overlap_frac": (ov / copy_ns) if copy_ns else 0.0}


# --------------------------------------------------------------------------------------
# Task 2 — idle gaps and their causes
# --------------------------------------------------------------------------------------
def find_gaps(gpu: pd.DataFrame, api: pd.DataFrame, start: int, end: int,
              min_gap_ns: int = 2_000) -> pd.DataFrame:
    """Find GPU-idle gaps between activities inside [start, end) and attribute a cause.

    A gap is a period when no GPU activity (any stream) executes, bounded on both sides by
    activity inside the window (leading/trailing idle time is excluded). Cause rules:
      * dependency   — the next activity was already submitted (its API call started more than
                       LAUNCH_LATENCY_NS before the gap began) yet the GPU sat idle: waiting on an
                       event or another stream.
      * host_sync    — work was not yet submitted AND a host-blocking call (sync API, or a
                       cudaMemcpyAsync touching pageable memory) returned during the gap: the CPU
                       was blocked waiting for the GPU, then had to issue new work.
      * launch_bound — otherwise: work was not submitted (or only just submitted) and no blocking
                       call returned: the CPU could not issue work as fast as the GPU retired it.
    Returns columns: gap_start_ns, gap_end_ns, gap_ns, next_id, next_name, cause.
    """
    win = gpu[(gpu["end_ns"] > start) & (gpu["start_ns"] < end)].sort_values(["start_ns", "id"])
    merged = merge_intervals(zip(win["start_ns"], win["end_ns"]))
    starts = win.drop_duplicates("start_ns").set_index("start_ns")
    api_start = api.set_index("correlation_id")["start_ns"]

    pageable_corr = set(gpu.loc[(gpu["kind"] == "memcpy") &
                                ((gpu["src_mem"] == "pageable") | (gpu["dst_mem"] == "pageable")),
                                "correlation_id"])
    blocking = api[api["name"].isin(SYNC_APIS) | api["correlation_id"].isin(pageable_corr)]
    b_end = blocking["end_ns"].to_numpy()

    rows = []
    for (_, e0), (s1, _) in zip(merged, merged[1:]):
        gap = s1 - e0
        if gap < min_gap_ns:
            continue
        nxt = starts.loc[s1]
        a0 = int(api_start.loc[int(nxt["correlation_id"])])
        if a0 < e0 - LAUNCH_LATENCY_NS:
            cause = "dependency"
        elif ((b_end >= e0) & (b_end <= s1)).any():
            cause = "host_sync"
        else:
            cause = "launch_bound"
        rows.append({"gap_start_ns": e0, "gap_end_ns": s1, "gap_ns": gap,
                     "next_id": int(nxt["id"]), "next_name": nxt["name"], "cause": cause})
    return pd.DataFrame(rows, columns=["gap_start_ns", "gap_end_ns", "gap_ns", "next_id", "next_name", "cause"])


# --------------------------------------------------------------------------------------
# Task 3 — copies
# --------------------------------------------------------------------------------------
def copy_table(gpu: pd.DataFrame) -> pd.DataFrame:
    """One row per memcpy with effective bandwidth (GB/s) and host memory kind.

    Columns: id, stream, copy_kind, host_mem, bytes, dur_ns, gbps.
    host_mem is the host-side memory kind (pageable/pinned).
    """
    c = gpu[gpu["kind"] == "memcpy"].copy()
    c["host_mem"] = c.apply(lambda r: r["src_mem"] if r["copy_kind"] == "HtoD" else r["dst_mem"], axis=1)
    c["dur_ns"] = c["end_ns"] - c["start_ns"]
    c["gbps"] = c["bytes"] / c["dur_ns"]  # B/ns == GB/s
    return c[["id", "stream", "copy_kind", "host_mem", "bytes", "dur_ns", "gbps"]].reset_index(drop=True)


# --------------------------------------------------------------------------------------
# Task 4 — occupancy
# --------------------------------------------------------------------------------------
def theoretical_occupancy(block_threads: int, regs_per_thread: int, smem_per_block: int, device: dict) -> dict:
    """Theoretical occupancy of one kernel configuration on one SM.

    Model (CUDA occupancy-calculator style, simplified [MODELED]):
      warps/block   = ceil(block_threads / warp_size)
      by warps      = floor(max_warps_per_sm / warps_per_block)
      by registers  = floor(warps_fit / warps_per_block), where
                      regs_per_warp = ceil(regs*warp_size / reg_alloc_unit) * reg_alloc_unit and
                      warps_fit = floor(floor(regs_per_sm / regs_per_warp) / warp_alloc_granularity) * granularity
      by smem       = floor(smem_per_sm / (smem_per_block + smem_reserved_per_block))
      by blocks     = max_blocks_per_sm
    blocks_per_sm = min(...); occupancy = blocks_per_sm*warps_per_block / max_warps_per_sm.
    limiter = first of (warps, registers, shared_memory, blocks) attaining the minimum.
    """
    ws = device["warp_size"]
    wpb = math.ceil(block_threads / ws)
    by_warps = device["max_warps_per_sm"] // wpb
    unit = device["reg_alloc_unit_per_warp"]
    regs_per_warp = math.ceil(regs_per_thread * ws / unit) * unit
    gran = device.get("warp_alloc_granularity", 1)
    warps_by_regs = ((device["regs_per_sm"] // regs_per_warp) // gran) * gran if regs_per_warp else device["max_warps_per_sm"]
    by_regs = warps_by_regs // wpb
    by_smem = device["smem_per_sm_bytes"] // (smem_per_block + device["smem_reserved_per_block_bytes"])
    by_blocks = device["max_blocks_per_sm"]
    limits = {"warps": by_warps, "registers": by_regs, "shared_memory": by_smem, "blocks": by_blocks}
    blocks = min(limits.values())
    limiter = next(k for k, v in limits.items() if v == blocks)
    active_warps = blocks * wpb
    return {"blocks_per_sm": blocks, "active_warps": active_warps,
            "occupancy": active_warps / device["max_warps_per_sm"], "limiter": limiter}


def kernel_summary(gpu: pd.DataFrame, device: dict) -> pd.DataFrame:
    """Per kernel name: count, total_ns, mean_ns, time_share, occupancy, limiter, roof_frac.

    roof_frac = max(achieved FLOP/s / peak, achieved DRAM B/s / HBM peak) over the summed
    counters — how close the kernel runs to *its* binding hardware ceiling.
    """
    k = gpu[gpu["kind"] == "kernel"].copy()
    k["dur_ns"] = k["end_ns"] - k["start_ns"]
    total = k["dur_ns"].sum()
    rows = []
    for name, g in k.groupby("name", sort=False):
        first = g.iloc[0]
        occ = theoretical_occupancy(int(first["block_x"]), int(first["regs_per_thread"]),
                                    int(first["smem_per_block_bytes"]), device)
        secs = g["dur_ns"].sum() / 1e9
        flop_frac = g["flop"].sum() / secs / device["peak_bf16_dense_flops"]
        bw_frac = g["dram_bytes"].sum() / secs / device["hbm_bytes_per_s"]
        rows.append({"name": name, "count": len(g), "total_ns": int(g["dur_ns"].sum()),
                     "mean_ns": float(g["dur_ns"].mean()), "time_share": g["dur_ns"].sum() / total,
                     "occupancy": occ["occupancy"], "limiter": occ["limiter"],
                     "roof_frac": max(flop_frac, bw_frac),
                     "bound": "compute" if flop_frac >= bw_frac else "memory"})
    return pd.DataFrame(rows).sort_values("total_ns", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------------------
# Task 5 — findings and report
# --------------------------------------------------------------------------------------
def analyze(data_dir: str | Path, min_gap_ns: int = 2_000) -> dict:
    """Run every analysis and return a dict with keys: steps (list of per-step metrics),
    kernels (records), copies (records) and findings (list of dicts with code, evidence,
    est_saving_ms_per_step, recommendation). Finding codes: PAGEABLE_H2D, EXCESS_SYNC,
    LAUNCH_BOUND, STREAM_DEPENDENCY, LOW_OCCUPANCY. Savings are averaged over all steps and count
    removed idle/copy time only (manuscript Section 4.12 reconciles them with a per-step analysis)."""
    tr = load_trace(data_dir)
    steps = []
    gaps_all = []
    for name, s, e in step_windows(tr.nvtx):
        u = utilization(tr.gpu, s, e)
        o = copy_compute_overlap(tr.gpu, s, e)
        g = find_gaps(tr.gpu, tr.api, s, e, min_gap_ns)
        g["step"] = name
        gaps_all.append(g)
        by = g.groupby("cause")["gap_ns"].agg(["count", "sum"])
        steps.append({"step": name, "step_ms": (e - s) / 1e6, **{k: v for k, v in u.items()},
                      **o, "gaps": {c: {"count": int(r["count"]), "ms": r["sum"] / 1e6} for c, r in by.iterrows()}})
    gaps = pd.concat(gaps_all, ignore_index=True)
    n_steps = len(steps)
    kern = kernel_summary(tr.gpu, tr.device)
    copies = copy_table(tr.gpu)

    findings = []
    pg = copies[(copies["host_mem"] == "pageable") & (copies["bytes"] >= 1 << 20)]
    pn = copies[(copies["host_mem"] == "pinned") & (copies["bytes"] >= 1 << 20)]
    if len(pg):
        findings.append({
            "code": "PAGEABLE_H2D",
            "evidence": (f"{len(pg)} large copies from pageable memory, {pg['bytes'].sum() / 2**20:.0f} MiB, "
                         f"{pg['dur_ns'].sum() / 1e6:.1f} ms total at {pg['bytes'].sum() / pg['dur_ns'].sum():.1f} GB/s "
                         f"vs {pn['bytes'].sum() / pn['dur_ns'].sum():.1f} GB/s for pinned; host thread blocked and "
                         f"no kernel overlaps them"),
            "est_saving_ms_per_step": pg["dur_ns"].sum() / 1e6 / n_steps,
            "recommendation": "Pin the source buffers (DataLoader pin_memory=True or a pinned staging pool), copy with "
                              "non_blocking=True on a side stream one step ahead, and make the compute stream wait on an event.",
        })
    sync = gaps[gaps["cause"] == "host_sync"]
    if len(sync):
        findings.append({
            "code": "EXCESS_SYNC",
            "evidence": (f"{len(sync) / n_steps:.0f} host-sync gaps per step, {sync['gap_ns'].sum() / 1e6 / n_steps:.2f} ms "
                         f"GPU idle per step; the CPU blocks on .item()/synchronize and the GPU drains before new work arrives"),
            "est_saving_ms_per_step": sync["gap_ns"].sum() / 1e6 / n_steps,
            "recommendation": "Remove the per-layer debug .item() hook; accumulate metrics on the GPU and read them "
                              "once every N steps; time steps with CUDA events instead of cudaDeviceSynchronize.",
        })
    lb = gaps[gaps["cause"] == "launch_bound"]
    k = tr.gpu[tr.gpu["kind"] == "kernel"]
    tiny = k[(k["end_ns"] - k["start_ns"]) < TINY_KERNEL_NS]
    if len(lb):
        findings.append({
            "code": "LAUNCH_BOUND",
            "evidence": (f"{len(tiny) / n_steps:.0f} kernels/step shorter than {TINY_KERNEL_NS / 1000:.0f} µs "
                         f"(median {(tiny['end_ns'] - tiny['start_ns']).median() / 1000:.1f} µs, grids of "
                         f"{int(tiny['grid_x'].median())} blocks on a {tr.device['sm_count']}-SM GPU); "
                         f"{len(lb) / n_steps:.0f} launch-bound gaps/step totalling {lb['gap_ns'].sum() / 1e6 / n_steps:.2f} ms"),
            "est_saving_ms_per_step": lb["gap_ns"].sum() / 1e6 / n_steps,
            "recommendation": "Use fused/foreach optimizer kernels (multi-tensor apply), flatten small parameters into "
                              "one buffer, or capture the optimizer step in a CUDA Graph.",
        })
    dep = gaps[gaps["cause"] == "dependency"]
    if len(dep):
        findings.append({
            "code": "STREAM_DEPENDENCY",
            "evidence": (f"{len(dep) / n_steps:.0f} gap(s)/step totalling {dep['gap_ns'].sum() / 1e6 / n_steps:.2f} ms where "
                         f"the next kernel ({dep['next_name'].iloc[0]}) had been submitted long before the GPU went idle: "
                         f"the compute stream was waiting on an event from another stream"),
            "est_saving_ms_per_step": dep["gap_ns"].sum() / 1e6 / n_steps,
            "recommendation": "Find the cudaStreamWaitEvent/cudaLaunchHostFunc pair (here a monitoring callback) and take "
                              "the host function off the compute stream's dependency chain (record an event and poll it later).",
        })
    low = kern[(kern["occupancy"] < LOW_OCC_THRESHOLD) & (kern["roof_frac"] < LOW_ROOF_FRACTION)
               & (kern["time_share"] >= MIN_TIME_SHARE)]
    for r in low.itertuples(index=False):
        findings.append({
            "code": "LOW_OCCUPANCY",
            "kernel": r.name,
            "evidence": (f"{r.name}: theoretical occupancy {r.occupancy:.1%} (limited by {r.limiter}), "
                         f"{r.bound}-bound at {r.roof_frac:.0%} of its roof, {r.time_share:.1%} of kernel time"),
            "est_saving_ms_per_step": r.total_ns / 1e6 / n_steps * (1 - r.roof_frac / 0.80),
            "recommendation": "Reduce register pressure (launch bounds / maxrregcount, split the fused kernel) or use "
                              "smaller blocks so more warps are resident to hide memory latency; re-measure with ncu.",
        })
    by_design = kern[(kern["occupancy"] < LOW_OCC_THRESHOLD) & (kern["roof_frac"] >= LOW_ROOF_FRACTION)]
    return {"steps": steps, "kernels": kern.to_dict("records"), "copies": copies.to_dict("records"),
            "low_occupancy_by_design": list(by_design["name"]), "findings": findings,
            "gaps_by_cause": {c: int(n) for c, n in gaps["cause"].value_counts().items()}}


def render_report(analysis: dict) -> str:
    """Render the analysis as a Markdown report: step table, findings ranked by saving, notes."""
    lines = ["# Training-step trace analysis (ORION HX8 GPU0, SIMULATED capture)", "",
             "| Step | Step time (ms) | GPU busy (any) | Kernel busy | Copy time (ms) | Copy overlapped | Sync gaps | Launch-bound gaps |",
             "|---|---|---|---|---|---|---|---|"]
    for s in analysis["steps"]:
        g = s["gaps"]
        lines.append(f"| {s['step']} | {s['step_ms']:.1f} | {s['busy_any_frac']:.1%} | {s['busy_kernel_frac']:.1%} | "
                     f"{s['copy_ns'] / 1e6:.1f} | {s['overlap_frac']:.1%} | "
                     f"{g.get('host_sync', {}).get('count', 0)} ({g.get('host_sync', {}).get('ms', 0):.2f} ms) | "
                     f"{g.get('launch_bound', {}).get('count', 0)} ({g.get('launch_bound', {}).get('ms', 0):.2f} ms) |")
    lines += ["", "## Findings (ranked by estimated saving per step, [MODELED] upper bounds; savings overlap)", ""]
    for i, f in enumerate(sorted(analysis["findings"], key=lambda f: -f["est_saving_ms_per_step"]), 1):
        lines += [f"{i}. **{f['code']}** — ≈ {f['est_saving_ms_per_step']:.1f} ms/step", f"   - Evidence: {f['evidence']}",
                  f"   - Recommendation: {f['recommendation']}"]
    lines += ["", "Low occupancy by design (near their roof; not a problem): " +
              ", ".join(analysis["low_occupancy_by_design"]), ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    ap.add_argument("--out", type=Path, default=None, help="write Markdown report here")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = render_report(analyze(args.data))
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
