#!/usr/bin/env python3
"""Turn the raw outputs of one Chapter 13 hands-on run into summary.json and report.md.

    python summarize.py results/<run-id>

Only parses what run.sh captured; it never edits the raw files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def label(c: dict) -> str:
    pf = f", prefetch {c['prefetch_factor']}" if c["workers"] > 0 else ""
    return f"workers {c['workers']}, pin {'on' if c['pin_memory'] else 'off'}{pf}"


def main() -> int:
    d = Path(sys.argv[1])
    env = load(d / "environment.json")
    cp = load(d / "step1-copies" / "copies.json")
    ov = load(d / "step2-overlap" / "overlap.json")
    ld = load(d / "step3-dataloader" / "loader.json")
    sc = ov["schedules"]
    cfg = ld["configs"]
    w0 = next(c for c in cfg if c["workers"] == 0 and not c["pin_memory"])
    best = max(cfg, key=lambda c: c["samples_per_s"])
    pin_pairs = []
    for w in sorted({c["workers"] for c in cfg}):
        off = [c for c in cfg if c["workers"] == w and not c["pin_memory"] and c["prefetch_factor"] in (None, 2)]
        on = [c for c in cfg if c["workers"] == w and c["pin_memory"] and c["prefetch_factor"] in (None, 2)]
        if off and on:
            pin_pairs.append({"workers": w, "off": off[0]["samples_per_s"], "on": on[0]["samples_per_s"]})
    sm = {
        "lab": "ch13-data-to-gpu", "run": d.name, "environment": env,
        "step1": {"rows": [{k: r[k] for k in ("mib", "pageable_gb_per_s", "pinned_gb_per_s", "pageable_cpu_blocked_ms",
                                              "pinned_cpu_blocked_ms", "pin_memory_first_call_ms", "pin_memory_call_ms", "pin_every_batch_gb_per_s", "pinned_ms")}
                           for r in cp["rows"]]},
        "step2": {"chunk_mib": ov["chunk_mib"], "chunks": ov["chunks"], "calibration": ov["calibration"],
                  **{name: {k: s[k] for k in ("wall_ms", "sum_copy_ms", "sum_compute_ms", "overlap_ms", "copy_hidden_fraction")}
                     for name, s in sc.items()},
                  "serial_over_overlap_pinned": ov["serial_over_overlap_pinned"], "ideal_overlap_wall_ms": ov["ideal_overlap_wall_ms"],
                  "profiler": ov.get("profiler")},
        "step3": {"gpu_only": ld["gpu_only"], "cpu_batch": ld["cpu_batch"], "workers_needed_estimate": ld["workers_needed_estimate"],
                  "batch_mib_float32": ld["batch_mib_float32"], "configs": [{k: v for k, v in c.items() if k != "nvidia_smi_util_samples"} for c in cfg],
                  "workers0": {k: w0[k] for k in ("samples_per_s", "gpu_busy_fraction", "data_wait_fraction", "nvidia_smi_util_mean")},
                  "best": {"config": label(best), **{k: best[k] for k in ("samples_per_s", "gpu_busy_fraction", "data_wait_fraction", "nvidia_smi_util_mean")}},
                  "cheapest_within_5pct_of_best": ld["cheapest_within_5pct_of_best"], "best_over_ceiling": ld["best_over_ceiling"],
                  "pin_memory_pairs": pin_pairs},
    }
    (d / "summary.json").write_text(json.dumps(sm, indent=1) + "\n", encoding="utf-8")

    M = "`[MEASURED]`"
    s2, s3 = sm["step2"], sm["step3"]
    L = [f"# Chapter 13 hands-on: moving data to the GPU on `{env.get('gpu')}`", "",
         f"Run captured {env.get('captured_at')} ({env.get('cpus')} CPUs, kernel `{env.get('kernel')}`). Every number is "
         f"{M} by the step named; raw outputs are in the step directories.", "",
         "## Step 1: pinned versus pageable, and what pinning costs", "",
         "| Size | Pageable H2D | Pinned H2D | CPU held, pageable | CPU held, pinned | `pin_memory()` first / median | Pin every batch |",
         "|---|---|---|---|---|---|---|"]
    for r in sm["step1"]["rows"]:
        L.append(f"| {r['mib']} MiB | {r['pageable_gb_per_s']:.2f} GB/s | {r['pinned_gb_per_s']:.2f} GB/s | {r['pageable_cpu_blocked_ms']:.3f} ms | "
                 f"{r['pinned_cpu_blocked_ms']:.3f} ms | {r['pin_memory_first_call_ms']:.2f} / {r['pin_memory_call_ms']:.2f} ms | {r['pin_every_batch_gb_per_s']:.2f} GB/s |")
    L += ["", f"All cells {M}.", "", "## Step 2: overlapping copies with compute", "",
          f"{s2['chunks']} chunks of {s2['chunk_mib']} MiB; compute per chunk calibrated to ≈ one chunk's copy "
          f"({s2['calibration']['copy_ms_per_chunk']} ms copy, k = {s2['calibration']['k']}).", "",
          "| Schedule | Wall | Σ copy | Σ compute | Copy time overlapped with compute | Copy hidden |", "|---|---|---|---|---|---|"]
    for name in ("serial", "overlap_pinned", "overlap_pageable"):
        x = s2[name]
        L.append(f"| {name} | {x['wall_ms']:.1f} ms | {x['sum_copy_ms']:.1f} ms | {x['sum_compute_ms']:.1f} ms | {x['overlap_ms']:.1f} ms | {x['copy_hidden_fraction']:.0%} |")
    pr = s2.get("profiler") or {}
    L += ["", f"All cells {M} from per-operation CUDA event timestamps. Serial / overlapped (pinned) = {s2['serial_over_overlap_pinned']}× "
          f"{M}; the ideal overlapped wall time is max(Σ copy, Σ compute) = {s2['ideal_overlap_wall_ms']:.1f} ms.",
          f"torch.profiler GPU-side events captured: {pr.get('gpu_side_events', 'n/a')} {M}"
          + (" (no CUPTI GPU activity on this platform, so the event timestamps are the evidence)." if not pr.get("gpu_side_events") else "."),
          "", "## Step 3: the DataLoader configuration that keeps the GPU busy", "",
          f"- Ceiling (batch already on the GPU): {s3['gpu_only']['samples_per_s']} samples/s ({s3['gpu_only']['step_ms']} ms per step) {M}.",
          f"- One process produces a batch in {s3['cpu_batch']['batch_ms']} ms ({s3['cpu_batch']['samples_per_s_per_worker']} samples/s) {M}; "
          f"estimate ⌈{s3['cpu_batch']['batch_ms']} / {s3['gpu_only']['step_ms']}⌉ = {s3['workers_needed_estimate']} workers to keep up.", "",
          "| Configuration | Samples/s | Data wait | GPU busy (events) | utilization.gpu |", "|---|---|---|---|---|"]
    for c in s3["configs"]:
        L.append(f"| {label(c)} | {c['samples_per_s']:.0f} | {c['data_wait_fraction']:.0%} | {c['gpu_busy_fraction']:.0%} | "
                 f"{c['nvidia_smi_util_mean'] if c['nvidia_smi_util_mean'] is not None else 'n/a'} % |")
    ch = s3["cheapest_within_5pct_of_best"]
    L += ["", f"All cells {M}.", "",
          f"- Best: {s3['best']['config']} at {s3['best']['samples_per_s']:.0f} samples/s, {s3['best_over_ceiling']:.0%} of the ceiling {M}.",
          f"- Cheapest configuration within 5 % of the best: workers {ch['workers']}, pin {'on' if ch['pin_memory'] else 'off'}, "
          f"prefetch {ch['prefetch_factor']} ({ch['samples_per_s']:.0f} samples/s, GPU busy {ch['gpu_busy_fraction']:.0%}) {M}.", ""]
    (d / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {d / 'summary.json'} and {d / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
