#!/usr/bin/env python3
"""Read an Nsight Systems capture (the .sqlite that `nsys export --type sqlite` writes) and do the chapter's
timeline analysis on each NVTX step range: GPU busy time, idle gaps, and the cause of every gap.

Gap rule (Section 4.11): for each idle gap, find the CUDA API call that submitted the next GPU activity
(through its correlation ID).
  - it had already returned when the gap began    -> "dependency" (the work was queued; the GPU waited on
                                                     something else)
  - it was still running or had not started, and a host-blocking call (a synchronize, or a synchronous
    copy) returned during the gap                 -> "host_sync"
  - otherwise                                     -> "launch_bound" (the CPU could not launch fast enough)

Standard library only:  python3 gaps.py capture.sqlite [--min-gap-us 10] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

BLOCKING = {"cudaStreamSynchronize", "cudaDeviceSynchronize", "cudaEventSynchronize", "cudaMemcpy"}


def base_name(name: str) -> str:
    """cudaStreamSynchronize_v3020 -> cudaStreamSynchronize (nsys appends the API version)."""
    return name.split("_v")[0]


def table_exists(db, name: str) -> bool:
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def load(path: str):
    db = sqlite3.connect(path)
    strings = dict(db.execute("SELECT id, value FROM StringIds"))
    acts = []   # (start, end, kind, name, correlationId)
    if table_exists(db, "CUPTI_ACTIVITY_KIND_KERNEL"):
        for s, e, c, n in db.execute("SELECT start, end, correlationId, shortName FROM CUPTI_ACTIVITY_KIND_KERNEL"):
            acts.append((s, e, "kernel", strings.get(n, str(n)), c))
    if table_exists(db, "CUPTI_ACTIVITY_KIND_MEMCPY"):
        for s, e, c, k, b in db.execute("SELECT start, end, correlationId, copyKind, bytes FROM CUPTI_ACTIVITY_KIND_MEMCPY"):
            acts.append((s, e, "memcpy", {1: "HtoD", 2: "DtoH", 8: "DtoD"}.get(k, f"kind{k}") + f" {b} B", c))
    if table_exists(db, "CUPTI_ACTIVITY_KIND_MEMSET"):
        for s, e, c in db.execute("SELECT start, end, correlationId FROM CUPTI_ACTIVITY_KIND_MEMSET"):
            acts.append((s, e, "memset", "memset", c))
    api = {}
    calls = []  # (start, end, name)
    if table_exists(db, "CUPTI_ACTIVITY_KIND_RUNTIME"):
        for s, e, c, n in db.execute("SELECT start, end, correlationId, nameId FROM CUPTI_ACTIVITY_KIND_RUNTIME"):
            name = strings.get(n, str(n))
            api[c] = (s, e, name)
            calls.append((s, e, name))
    ranges = []
    if table_exists(db, "NVTX_EVENTS"):
        for s, e, t, tid in db.execute("SELECT start, end, text, textId FROM NVTX_EVENTS WHERE end IS NOT NULL"):
            name = t if t is not None else strings.get(tid, "")
            if name and name.startswith("train_step"):
                ranges.append((name, s, e))
    return sorted(acts), api, sorted(calls), sorted(ranges, key=lambda r: r[1])


def analyse(acts, api, calls, ranges, min_gap_ns: int):
    steps = []
    for name, w0, w1 in ranges:
        inside = [a for a in acts if a[1] > w0 and a[0] < w1]
        # union of busy intervals, clipped to the window
        busy, cur = 0, None
        merged = []
        for s, e, *_ in inside:
            s, e = max(s, w0), min(e, w1)
            if cur and s <= cur[1]:
                cur[1] = max(cur[1], e)
            else:
                if cur:
                    merged.append(cur)
                cur = [s, e]
        if cur:
            merged.append(cur)
        busy = sum(e - s for s, e in merged)
        gaps = []
        edges = [(w0, w0)] + [tuple(m) for m in merged]
        for (p0, p1), (n0, n1) in zip(edges, edges[1:]):
            g0, g1 = p1, n0
            if g1 - g0 < min_gap_ns:
                continue
            nxt = next((a for a in inside if a[0] >= n0), None)
            sub = api.get(nxt[4]) if nxt else None
            blocking = [c for c in calls if g0 <= c[1] <= g1 and base_name(c[2]) in BLOCKING]
            if sub is not None and sub[1] <= g0:   # submitted (call returned) before the GPU went idle
                cause = "dependency"
            elif blocking:
                cause = "host_sync"
            else:
                cause = "launch_bound"
            gaps.append({"start_ns": g0, "dur_us": (g1 - g0) / 1e3, "cause": cause,
                         "next": f"{nxt[2]} {nxt[3]}"[:60] if nxt else "",
                         "submitted_by": sub[2] if sub else "", "blocking_call": blocking[-1][2] if blocking else ""})
        win = w1 - w0
        syncs = [c for c in calls if w0 <= c[0] <= w1 and base_name(c[2]) in ("cudaStreamSynchronize", "cudaDeviceSynchronize")]
        by = {}
        for g in gaps:
            d = by.setdefault(g["cause"], {"count": 0, "total_us": 0.0})
            d["count"] += 1
            d["total_us"] += g["dur_us"]
        kernels = [a for a in inside if a[2] == "kernel"]
        steps.append({"range": name, "window_ms": win / 1e6, "busy_ms": busy / 1e6, "busy_frac": busy / win if win else 0,
                      "idle_ms": (win - busy) / 1e6, "kernels": len(kernels), "sync_calls": len(syncs),
                      "gaps_by_cause": by, "largest_gaps": sorted(gaps, key=lambda g: -g["dur_us"])[:8]})
    return steps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sqlite")
    ap.add_argument("--min-gap-us", type=float, default=10.0)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    acts, api, calls, ranges = load(a.sqlite)
    if not ranges:
        print("no train_step NVTX ranges in the capture", file=sys.stderr)
        return 1
    steps = analyse(acts, api, calls, ranges, int(a.min_gap_us * 1e3))
    for s in steps:
        print(f"{s['range']}: window {s['window_ms']:.2f} ms, GPU busy {s['busy_ms']:.2f} ms ({100 * s['busy_frac']:.1f} %), "
              f"idle {s['idle_ms']:.2f} ms, {s['kernels']} kernels, {s['sync_calls']} synchronize calls")
        for cause, d in sorted(s["gaps_by_cause"].items()):
            print(f"   gaps >= {a.min_gap_us:g} us  {cause:13s} {d['count']:4d}  {d['total_us'] / 1e3:7.2f} ms")
        for g in s["largest_gaps"][:5]:
            print(f"   {g['dur_us']:8.1f} us  {g['cause']:12s} next: {g['next']:40s} after: {g['blocking_call'] or '-'}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"min_gap_us": a.min_gap_us, "steps": steps}, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
