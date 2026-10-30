#!/usr/bin/env python3
"""Workload-characterization model for ORION (Chapter 1 lab) -- REFERENCE SOLUTION.

Given per-GPU, per-step work profiles (FLOP, HBM bytes, NVLink bytes, NIC bytes, storage bytes)
and the ORION platform ceilings, compute a lower-bound time for each resource, name the dominant
bound, and flag profiles that are invalid, physically impossible, mislabeled, or dominated by
latency/overhead rather than any throughput ceiling.

The model is a *ceiling* (roofline-style) model: each resource time is ``work / peak rate``.
Real systems never reach peak, so every lower bound must be <= the observed step time.

Usage:
    python workload_model.py ../../lab/data/workload_profiles.csv ../../lab/data/platform_orion.yaml \
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
    clean: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in rows:
        wid = raw["workload_id"].strip()
        missing = [f for f in NUMERIC_FIELDS if raw.get(f, "").strip() == ""]
        if missing:
            issues.append({"workload_id": wid, "code": "MISSING", "detail": f"blank: {', '.join(missing)}"})
            continue
        vals = {f: float(raw[f]) for f in NUMERIC_FIELDS}
        neg = [f for f, v in vals.items() if v < 0]
        if neg:
            issues.append({"workload_id": wid, "code": "NEGATIVE", "detail": f"negative: {', '.join(neg)}"})
            continue
        unit = raw["net_unit"].strip()
        if unit not in ALLOWED_NET_UNITS:
            issues.append({"workload_id": wid, "code": "BAD_UNIT",
                           "detail": f"net_unit '{unit}' is not a volume unit (expected GB or Gb)"})
            continue
        if wid in seen:
            issues.append({"workload_id": wid, "code": "DUPLICATE", "detail": f"duplicate id ({raw['name']})"})
            continue
        seen.add(wid)
        prof: dict[str, Any] = dict(raw)
        prof.update(vals)
        prof["workload_id"] = wid
        prof["gpus"] = int(vals["gpus"])
        prof["net_gb_per_gpu"] = vals["net_value_per_gpu"] * ALLOWED_NET_UNITS[unit]
        clean.append(prof)
    return clean, issues


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
    nodes = max(1, math.ceil(profile["gpus"] / platform["gpus_per_node"]))
    fe = platform["frontend_gbit_per_s_per_node"] / 8.0
    rd = min(fe, platform["storage_read_gb_per_s_aggregate"] / nodes)
    wr = min(fe, platform["storage_write_gb_per_s_aggregate"] / nodes)
    return {
        "compute": profile["tflop_per_gpu"] / platform["gpu_dense_bf16_tflops"],
        "memory": profile["hbm_gb_per_gpu"] / platform["hbm_gb_per_s"],
        "scaleup": profile["nvlink_gb_per_gpu"] / platform["nvlink_gb_per_s_per_direction"],
        "scaleout": profile["net_gb_per_gpu"] / (platform["nic_line_rate_gbit_per_s"] / 8.0),
        "io_read": profile["io_read_gb_per_node"] / rd,
        "io_write": profile["io_write_gb_per_node"] / wr,
    }


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
    t = resource_times(profile, platform)
    dom = max(t, key=lambda k: t[k])
    lb = t[dom]
    obs = profile["observed_step_s"]
    frac = lb / obs if obs > 0 else math.inf
    flags = []
    if any(v > obs for v in t.values()):
        flags.append("IMPOSSIBLE")
    if frac < platform["latency_fraction_threshold"]:
        flags.append("LATENCY_OR_OVERHEAD")
    cls = RESOURCE_CLASS[dom]
    if profile["declared_class"].strip() != cls:
        flags.append("MISLABELED")
    return {
        "workload_id": profile["workload_id"],
        "name": profile["name"],
        "phase": profile["phase"],
        "declared_class": profile["declared_class"],
        "observed_step_s": obs,
        "times": t,
        "dominant_resource": dom,
        "bound_class": cls,
        "lower_bound_s": lb,
        "ceiling_fraction": frac,
        "flags": sorted(flags),
    }


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
    lines = [
        f"# Workload comparison: {a['workload_id']} ({a['name']}) vs {b['workload_id']} ({b['name']})",
        "",
        "All times are `[MODELED]` lower bounds against ORION peak ceilings; observed times are as "
        "supplied by workload owners.",
        "",
        f"| Resource | {a['workload_id']} lower bound | {a['workload_id']} % of step | "
        f"{b['workload_id']} lower bound | {b['workload_id']} % of step |",
        "|---|---:|---:|---:|---:|",
    ]
    for k in RESOURCE_CLASS:
        ta, tb = a["times"][k], b["times"][k]
        lines.append(
            f"| {k} | {_fmt_s(ta)} | {100 * ta / a['observed_step_s']:.1f} % | "
            f"{_fmt_s(tb)} | {100 * tb / b['observed_step_s']:.1f} % |"
        )
    lines += [
        f"| observed step | {_fmt_s(a['observed_step_s'])} | 100 % | {_fmt_s(b['observed_step_s'])} | 100 % |",
        f"| dominant resource | {a['dominant_resource']} | | {b['dominant_resource']} | |",
        f"| bound class | {a['bound_class']} | | {b['bound_class']} | |",
        f"| ceiling fraction | {a['ceiling_fraction']:.2f} | | {b['ceiling_fraction']:.2f} | |",
        f"| flags | {', '.join(a['flags']) or 'none'} | | {', '.join(b['flags']) or 'none'} | |",
        "",
        "## Evidence to confirm",
        "",
        f"- **{a['workload_id']} ({a['bound_class']})**: {EVIDENCE[a['bound_class']]}.",
        f"- **{b['workload_id']} ({b['bound_class']})**: {EVIDENCE[b['bound_class']]}.",
        "",
    ]
    return "\n".join(lines)


def analyze(profiles_path: str | Path, platform_path: str | Path) -> dict[str, Any]:
    """End-to-end: load, validate, classify. Returns {"results": [...], "issues": [...]}."""
    platform = load_platform(platform_path)
    clean, issues = normalize_and_validate(load_csv(profiles_path))
    return {"results": [classify(p, platform) for p in clean], "issues": issues}


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parent.parent / "lab" / "data"
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
