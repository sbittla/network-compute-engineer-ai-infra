#!/usr/bin/env python3
"""Chapter 4 lab — STARTER: analyse a profiler-style trace of a training step.

Inputs (lab/data/):
    gpu_trace.csv       GPU activities (kernels, memcpys) with stream, start/end (ns), launch config,
                        copy kind and memory kind, and per-kernel FLOP / DRAM-byte counters.
    cuda_api_trace.csv  CPU-side CUDA API calls (cudaLaunchKernel, cudaMemcpyAsync, sync calls)
                        joined to GPU activities by correlation_id.
    nvtx_ranges.csv     CPU-side NVTX ranges (train_step_N, forward, backward, ...).
    device.json         Device limits for the occupancy calculation and peak rates.

All times are integer nanoseconds. Fractions are 0..1. Bandwidths are GB/s (1e9 B/s).
Implement every function that raises NotImplementedError, then run `python ../check.py`.

CLI (once implemented):
    python trace_analysis.py --data ../data --out report.md
"""
from __future__ import annotations

import argparse
import json
import math  # noqa: F401  (you will need it for the occupancy calculation)
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
    """Load the four input files. Provided (not a TODO)."""
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
    """Merge overlapping/touching [start, end) intervals (ns). Returns a sorted, disjoint list.

    Example: [(0, 10), (5, 20), (30, 40)] -> [(0, 20), (30, 40)]; [(0, 10), (10, 12)] -> [(0, 12)].
    Ignore empty intervals (end <= start).
    """
    # TODO: sort by start, then sweep, extending the last interval while the next one overlaps.
    raise NotImplementedError("merge_intervals")


def _clip(intervals: Iterable[tuple[int, int]], start: int, end: int) -> list[tuple[int, int]]:
    """Helper (provided): clip intervals to [start, end), dropping those entirely outside."""
    return [(max(s, start), min(e, end)) for s, e in intervals if e > start and s < end]


def busy_ns(intervals: Iterable[tuple[int, int]]) -> int:
    """Total covered time (ns) of a set of possibly overlapping intervals."""
    # TODO: use merge_intervals — overlapping kernels on two streams must not be double counted.
    raise NotImplementedError("busy_ns")


def _intersect_ns(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> int:
    """Helper (provided): overlap (ns) between two *merged* interval lists (two-pointer sweep)."""
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
    """Return (name, start_ns, end_ns) for every NVTX range whose name starts with `prefix`,
    sorted by start time."""
    # TODO
    raise NotImplementedError("step_windows")


def utilization(gpu: pd.DataFrame, start: int, end: int) -> dict:
    """GPU busy fractions inside [start, end).

    Return a dict with keys: window_ns, busy_any_ns, busy_kernel_ns, busy_copy_ns,
    busy_any_frac, busy_kernel_frac.
      busy_any   = union of ALL activity intervals (kernels and copies, every stream), clipped
      busy_kernel= union of kernel intervals only
      busy_copy  = union of memcpy intervals only
    """
    # TODO: filter by gpu["kind"], clip with _clip(), measure with busy_ns().
    raise NotImplementedError("utilization")


def copy_compute_overlap(gpu: pd.DataFrame, start: int, end: int) -> dict:
    """How much copy time ran concurrently with kernel execution inside [start, end).

    Return dict: copy_ns (union of copy intervals), overlapped_ns (copy ∩ kernel time),
    overlap_frac (= overlapped_ns / copy_ns, 0.0 if no copies).
    """
    # TODO: merge copies and kernels separately, then use _intersect_ns().
    raise NotImplementedError("copy_compute_overlap")


# --------------------------------------------------------------------------------------
# Task 2 — idle gaps and their causes
# --------------------------------------------------------------------------------------
def find_gaps(gpu: pd.DataFrame, api: pd.DataFrame, start: int, end: int,
              min_gap_ns: int = 2_000) -> pd.DataFrame:
    """Find GPU-idle gaps between activities inside [start, end) and attribute a cause.

    A gap is a period >= min_gap_ns when no GPU activity (any stream) executes, bounded on both
    sides by activity in the window (ignore leading/trailing idle time). For each gap, find the
    NEXT activity (the one starting at the gap end), look up its API call via correlation_id, and
    classify:
      * "dependency"   — its API call started more than LAUNCH_LATENCY_NS before the gap began
                         (work was queued, GPU waited on something else);
      * "host_sync"    — otherwise, if a host-blocking call RETURNED inside the gap. Host-blocking
                         calls are SYNC_APIS plus cudaMemcpyAsync calls whose GPU memcpy touches
                         pageable memory (src_mem or dst_mem == "pageable");
      * "launch_bound" — otherwise (the CPU simply did not submit work fast enough).
    Return a DataFrame with columns:
      gap_start_ns, gap_end_ns, gap_ns, next_id, next_name, cause
    """
    # TODO 1: merged busy intervals of activities overlapping the window.
    # TODO 2: iterate consecutive pairs; gap = next.start - prev.end.
    # TODO 3: apply the cause rules above.
    raise NotImplementedError("find_gaps")


# --------------------------------------------------------------------------------------
# Task 3 — copies
# --------------------------------------------------------------------------------------
def copy_table(gpu: pd.DataFrame) -> pd.DataFrame:
    """One row per memcpy with effective bandwidth and host memory kind.

    Columns: id, stream, copy_kind, host_mem, bytes, dur_ns, gbps
      host_mem = src_mem for HtoD copies, dst_mem for DtoH copies ("pageable"/"pinned")
      gbps     = bytes / dur_ns   (bytes per ns == GB/s)
    """
    # TODO
    raise NotImplementedError("copy_table")


# --------------------------------------------------------------------------------------
# Task 4 — occupancy
# --------------------------------------------------------------------------------------
def theoretical_occupancy(block_threads: int, regs_per_thread: int, smem_per_block: int, device: dict) -> dict:
    """Theoretical occupancy of one kernel configuration on one SM.

    Use this simplified CUDA occupancy-calculator model:
      warps_per_block = ceil(block_threads / warp_size)
      by_warps        = floor(max_warps_per_sm / warps_per_block)
      regs_per_warp   = ceil(regs_per_thread * warp_size / reg_alloc_unit_per_warp) * reg_alloc_unit_per_warp
      warps_fit       = floor(floor(regs_per_sm / regs_per_warp) / warp_alloc_granularity) * warp_alloc_granularity
      by_registers    = floor(warps_fit / warps_per_block)
      by_smem         = floor(smem_per_sm_bytes / (smem_per_block + smem_reserved_per_block_bytes))
      by_blocks       = max_blocks_per_sm
      blocks_per_sm   = min of the four
      occupancy       = blocks_per_sm * warps_per_block / max_warps_per_sm
      limiter         = first of ("warps", "registers", "shared_memory", "blocks") equal to the min
    Return {"blocks_per_sm", "active_warps", "occupancy", "limiter"}.
    """
    # TODO
    raise NotImplementedError("theoretical_occupancy")


def kernel_summary(gpu: pd.DataFrame, device: dict) -> pd.DataFrame:
    """Per kernel name: name, count, total_ns, mean_ns, time_share, occupancy, limiter,
    roof_frac, bound.

      time_share = total_ns / total kernel ns (all kernels)
      roof_frac  = max(sum(flop)/sum(seconds)/peak_bf16_dense_flops,
                       sum(dram_bytes)/sum(seconds)/hbm_bytes_per_s)
      bound      = "compute" if the FLOP fraction >= the bandwidth fraction else "memory"
    Use the launch configuration of the first instance for occupancy. Sort by total_ns desc.
    """
    # TODO
    raise NotImplementedError("kernel_summary")


# --------------------------------------------------------------------------------------
# Task 5 — findings and report
# --------------------------------------------------------------------------------------
def analyze(data_dir: str | Path, min_gap_ns: int = 2_000) -> dict:
    """Run every analysis and return a dict with keys:
      steps   — list of per-step dicts: step, step_ms, the utilization() keys, the
                copy_compute_overlap() keys, and gaps = {cause: {"count": n, "ms": total}}
      kernels — kernel_summary(...).to_dict("records")
      copies  — copy_table(...).to_dict("records")
      low_occupancy_by_design — kernel names with occupancy < LOW_OCC_THRESHOLD but
                roof_frac >= LOW_ROOF_FRACTION (running near their roof: NOT a problem)
      gaps_by_cause — {cause: count over all steps}
      findings — list of dicts, each with code, evidence (str with numbers),
                 est_saving_ms_per_step (float), recommendation (str); plus "kernel" for
                 LOW_OCCUPANCY. Codes:
        PAGEABLE_H2D  — copies >= 1 MiB whose host memory is pageable (saving: their time/step)
        EXCESS_SYNC   — host_sync gaps (saving: their total idle time per step)
        LAUNCH_BOUND  — launch_bound gaps; cite kernels < TINY_KERNEL_NS (saving: gap time/step)
        STREAM_DEPENDENCY — dependency gaps: work was queued but waited on another stream/event
                        (saving: their total idle time per step)
        LOW_OCCUPANCY — one per kernel with occupancy < LOW_OCC_THRESHOLD AND
                        roof_frac < LOW_ROOF_FRACTION AND time_share >= MIN_TIME_SHARE
                        (saving: total_ns/step * (1 - roof_frac/0.80))
    """
    # TODO: loop over step_windows(); compute per-step metrics; then build the findings.
    raise NotImplementedError("analyze")


def render_report(analysis: dict) -> str:
    """Render the analysis as a Markdown report (provided). Extend it for your deliverable."""
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
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data")
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
