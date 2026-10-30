#!/usr/bin/env python3
"""Workload-characterization model for ORION (Chapter 1 lab) -- STARTER (learner edition).

Implement the functions marked TODO. Run ``python ../check.py`` to see your progress.

Given per-GPU, per-step work profiles (FLOP, HBM bytes, NVLink bytes, NIC bytes, storage bytes)
and the ORION platform ceilings, compute a lower-bound time for each resource, name the dominant
bound, and flag profiles that are invalid, physically impossible, mislabeled, or dominated by
latency/overhead rather than any throughput ceiling.

The model is a *ceiling* (roofline-style) model: each resource time is ``work / peak rate``.
Real systems never reach peak, so every lower bound must be <= the observed step time.

Usage:
    python workload_model.py ../data/workload_profiles.csv ../data/platform_orion.yaml \
        --compare W01 W02
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import yaml

NUMERIC_FIELDS = [
    "gpus", "tflop_per_gpu", "hbm_gb_per_gpu", "nvlink_gb_per_gpu", "net_value_per_gpu",
    "io_read_gb_per_node", "io_write_gb_per_node", "observed_step_s",
]
ALLOWED_NET_UNITS = {"GB": 1.0, "Gb": 1.0 / 8.0}   # volume units -> GB
RESOURCE_CLASS = {
    "compute": "compute",
    "memory": "memory",
    "scaleup": "communication",
    "scaleout": "communication",
    "io_read": "io",
    "io_write": "io",
}
EVIDENCE = {
    "compute": "SM/tensor-pipe activity high (DCGM_FI_PROF_PIPE_TENSOR_ACTIVE), step time scales with FLOP",
    "memory": "DRAM activity high (DCGM_FI_PROF_DRAM_ACTIVE), tensor activity low; time scales with bytes",
    "communication": "NCCL/collective time dominates trace; NVLink or NIC byte counters near ceiling",
    "io": "GPUs idle waiting on loader/checkpoint; storage or frontend NIC throughput near ceiling",
}


# ---------------------------------------------------------------- helpers (given in starter too)
def load_platform(path: str | Path) -> dict[str, Any]:
    """Load the platform-ceiling YAML into a dict."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_csv(path: str | Path) -> list[dict[str, str]]:
    """Load the profile CSV as a list of raw string dicts (no conversion, no validation)."""
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- learner functions
def normalize_and_validate(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Convert raw rows to typed profiles and reject bad rows.

    Returns ``(clean, issues)``. ``clean`` rows contain every original key, numeric fields as
    float (``gpus`` as int), and a new key ``net_gb_per_gpu`` (NIC volume converted to GB).
    ``issues`` is a list of ``{"workload_id", "code", "detail"}`` with codes:

    * ``MISSING``   -- a numeric field is blank
    * ``NEGATIVE``  -- a numeric field is < 0
    * ``BAD_UNIT``  -- ``net_unit`` is not a volume unit in {GB, Gb}
    * ``DUPLICATE`` -- ``workload_id`` already seen (first occurrence is kept)

    A row produces at most one issue (checked in the order above, duplicate last) and is
    excluded from ``clean`` if it has any issue.
    """
    # TODO 1: for each raw row, in order: MISSING (blank numeric field), NEGATIVE,
    #         BAD_UNIT (net_unit not in ALLOWED_NET_UNITS), DUPLICATE (id already seen).
    # TODO 2: convert numeric fields to float (gpus to int) and add net_gb_per_gpu,
    #         converting Gb -> GB with ALLOWED_NET_UNITS. Watch the units trap!
    raise NotImplementedError("normalize_and_validate is not implemented yet")


def resource_times(profile: dict[str, Any], platform: dict[str, Any]) -> dict[str, float]:
    """Return the lower-bound time in seconds for each resource.

    Keys: compute, memory, scaleup, scaleout, io_read, io_write.

    * compute  = tflop_per_gpu / gpu_dense_bf16_tflops
    * memory   = hbm_gb_per_gpu / hbm_gb_per_s
    * scaleup  = nvlink_gb_per_gpu / nvlink_gb_per_s_per_direction
    * scaleout = net_gb_per_gpu / (nic_line_rate_gbit_per_s / 8)
    * io_*     = io_*_gb_per_node / per-node ceiling, where the per-node ceiling is
                 min(frontend_gbit_per_s_per_node / 8, storage_*_aggregate / nodes) and
                 nodes = ceil(gpus / gpus_per_node). (Optimistic: assumes the job owns the PFS.)
    """
    # TODO: compute the six lower-bound times (seconds). Remember 400 Gb/s = 50 GB/s and
    #       that shared storage bandwidth is divided across the job's nodes.
    raise NotImplementedError("resource_times is not implemented yet")


def classify(profile: dict[str, Any], platform: dict[str, Any]) -> dict[str, Any]:
    """Classify one clean profile.

    Returns a dict with: workload_id, name, times (from resource_times), dominant_resource
    (key with the largest time), bound_class (compute|memory|communication|io via RESOURCE_CLASS),
    lower_bound_s (largest time), ceiling_fraction (lower_bound_s / observed_step_s), and flags
    (sorted list drawn from):

    * IMPOSSIBLE          -- any resource time exceeds observed_step_s (claims > peak rate)
    * LATENCY_OR_OVERHEAD -- ceiling_fraction < platform["latency_fraction_threshold"]
    * MISLABELED          -- declared_class != bound_class
    """
    # TODO: call resource_times, pick the dominant resource, map it with RESOURCE_CLASS,
    #       compute ceiling_fraction and the three flags (sorted).
    raise NotImplementedError("classify is not implemented yet")


def _fmt_s(x: float) -> str:
    """Human format for seconds."""
    if x == 0:
        return "0"
    if x < 1e-3:
        return f"{x * 1e6:.1f} us"
    if x < 1:
        return f"{x * 1e3:.2f} ms"
    return f"{x:.2f} s"


def comparison_markdown(a: dict[str, Any], b: dict[str, Any]) -> str:
    """Render the one-page comparison of two classified workloads as Markdown.

    Must contain: a heading naming both workload ids, a table with one row per resource
    (compute, memory, scaleup, scaleout, io_read, io_write) and columns for each workload's
    lower-bound time and share of observed step time, rows for dominant resource, bound class,
    ceiling fraction and flags, and an "Evidence to confirm" section naming, for each workload,
    the telemetry that would confirm its bound class.
    """
    # TODO: build the Markdown one-pager. Use _fmt_s() for times and EVIDENCE for the
    #       'Evidence to confirm' section.
    raise NotImplementedError("comparison_markdown is not implemented yet")


def analyze(profiles_path: str | Path, platform_path: str | Path) -> dict[str, Any]:
    """End-to-end: load, validate, classify. Returns {"results": [...], "issues": [...]}."""
    # TODO: load_platform + load_csv -> normalize_and_validate -> classify each clean row.
    raise NotImplementedError("analyze is not implemented yet")


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parent / "data"
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profiles", nargs="?", default=default_data / "workload_profiles.csv")
    ap.add_argument("platform", nargs="?", default=default_data / "platform_orion.yaml")
    ap.add_argument("--compare", nargs=2, metavar=("ID_A", "ID_B"), default=["W01", "W02"])
    args = ap.parse_args()
    out = analyze(args.profiles, args.platform)
    print("## Rejected rows")
    for i in out["issues"]:
        print(f"- {i['workload_id']}: {i['code']} -- {i['detail']}")
    print("\n## Classification")
    print("| id | name | bound | dominant | lower bound | observed | fraction | flags |")
    print("|---|---|---|---|---:|---:|---:|---|")
    for r in out["results"]:
        print(f"| {r['workload_id']} | {r['name']} | {r['bound_class']} | {r['dominant_resource']} | "
              f"{_fmt_s(r['lower_bound_s'])} | {_fmt_s(r['observed_step_s'])} | "
              f"{r['ceiling_fraction']:.2f} | {', '.join(r['flags'])} |")
    by_id = {r["workload_id"]: r for r in out["results"]}
    a, b = args.compare
    if a in by_id and b in by_id:
        print()
        print(comparison_markdown(by_id[a], by_id[b]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
