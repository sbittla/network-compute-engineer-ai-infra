"""Chapter 14 lab -- reference implementation (INSTRUCTOR ONLY).

Three tools an AI-infrastructure storage engineer actually builds:

Part A  checkpoint planner        -- size, sync/async write time, overhead, Young/Daly interval,
                                     lost GPU-hours per day, RPO and time-to-resume per strategy.
Part B  I/O trace analyzer         -- metadata-bound vs bandwidth-bound phases, tail latency,
                                     slow storage targets, fio acceptance outliers.
Part C  checkpoint validator       -- detect incomplete/corrupt checkpoints and pick the latest
                                     valid one.

Every number this module produces is MODELED (Part A) or derived from SIMULATED data (B, C).
Units: bytes (B), seconds (s), GB = 1e9 B, MiB = 2**20 B.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MiB = 1024 * 1024
STRATEGIES = ("sync_pfs", "async_pfs", "sync_local_drain", "async_two_level")
META_OPS = ("open", "close", "stat")

# ============================================================================================
# Part A -- checkpoint planner
# ============================================================================================


def checkpoint_size_bytes(params: float, bytes_per_param: float) -> float:
    """Checkpoint size in bytes = parameters x bytes per parameter (weights + optimizer state)."""
    return float(params) * float(bytes_per_param)


def transfer_time_s(nbytes: float, GBps: float, efficiency: float = 1.0) -> float:
    """Seconds to move ``nbytes`` at ``GBps`` (1e9 B/s) times an achieved-efficiency factor."""
    return float(nbytes) / (float(GBps) * 1e9 * float(efficiency))


def young_interval_s(ckpt_cost_s: float, mtbf_s: float) -> float:
    """Young (1974) first-order optimum compute time between checkpoints: sqrt(2 * delta * M)."""
    return math.sqrt(2.0 * ckpt_cost_s * mtbf_s)


def daly_interval_s(ckpt_cost_s: float, mtbf_s: float) -> float:
    """Daly (2006) higher-order optimum.

    tau = sqrt(2 d M) * [1 + (1/3) sqrt(d / 2M) + (1/9)(d / 2M)] - d   for d < 2M, else M.
    """
    d, m = ckpt_cost_s, mtbf_s
    if d >= 2 * m:
        return m
    x = d / (2 * m)
    return math.sqrt(2 * d * m) * (1 + math.sqrt(x) / 3 + x / 9) - d


def choose_interval_s(ckpt_cost_s: float, mtbf_s: float, min_interval_s: float,
                      step_time_s: float) -> float:
    """Young interval, floored at ``min_interval_s`` (one checkpoint in flight), rounded UP to a
    whole number of training steps (checkpoints are taken at step boundaries)."""
    tau = max(young_interval_s(ckpt_cost_s, mtbf_s), min_interval_s)
    return math.ceil(tau / step_time_s - 1e-9) * step_time_s


def strategy_timings(cfg: dict, strategy: str) -> dict[str, float]:
    """Per-checkpoint timings for one strategy (all seconds).

    Returns keys:
      delta      -- effective training time lost per checkpoint (blocking + interference)
      blocking   -- time the training loop is stalled per checkpoint
      L_soft     -- completion latency of the copy a *soft* failure restores from
      L_hard     -- completion latency of the copy a *hard* (node-loss) failure restores from
      load_soft, load_hard -- restore read time for each failure class
      pfs_every  -- PFS copy taken every this many checkpoints (1 except two-level)
    """
    w, s, h, a = cfg["workload"], cfg["storage"], cfg["host"], cfg["async"]
    size = checkpoint_size_bytes(w["params"], w["ckpt_bytes_per_param"])
    t_pfs_w = transfer_time_s(size, s["pfs_write_GBps"], s["pfs_efficiency"])
    t_pfs_r = transfer_time_s(size, s["pfs_read_GBps"], s["pfs_efficiency"])
    commit = s["commit_overhead_s"]
    persist = t_pfs_w + commit
    t_snap = transfer_time_s(size / w["gpus"], h["d2h_GBps_per_gpu"]) + h["snapshot_fixed_s"]
    t_loc_w = transfer_time_s(size / w["nodes"], h["nvme_write_GBps_per_node"])
    t_loc_r = transfer_time_s(size / w["nodes"], h["nvme_read_GBps_per_node"])
    i = a["interference_frac"]
    k = int(a["pfs_every_k"])

    if strategy == "sync_pfs":
        blocking = persist
        return dict(delta=blocking, blocking=blocking, L_soft=persist, L_hard=persist,
                    load_soft=t_pfs_r, load_hard=t_pfs_r, pfs_every=1)
    if strategy == "async_pfs":
        return dict(delta=t_snap + i * persist, blocking=t_snap, L_soft=t_snap + persist,
                    L_hard=t_snap + persist, load_soft=t_pfs_r, load_hard=t_pfs_r, pfs_every=1)
    if strategy == "sync_local_drain":
        blocking = t_loc_w + commit
        return dict(delta=blocking + i * t_pfs_w, blocking=blocking, L_soft=blocking,
                    L_hard=blocking + persist, load_soft=t_loc_r, load_hard=t_pfs_r, pfs_every=1)
    if strategy == "async_two_level":
        local = t_snap + t_loc_w + commit
        return dict(delta=t_snap + i * (t_loc_w + t_pfs_w / k), blocking=t_snap, L_soft=local,
                    L_hard=local + persist, load_soft=t_loc_r, load_hard=t_pfs_r, pfs_every=k)
    raise ValueError(f"unknown strategy {strategy!r}")


def plan_strategy(cfg: dict, strategy: str, interval_s: float | None = None) -> dict[str, Any]:
    """Evaluate one checkpoint strategy. If ``interval_s`` is None, choose it with
    :func:`choose_interval_s` (Young, floored at the in-flight completion latency).

    Model (MODELED; assumptions in the lab README):
      E_lost  = (1-h)(tau/2 + L_soft) + h(k*tau/2 + L_hard)     expected recomputed work/failure
      E_ttr   = detect + relaunch + validate + warmup + (1-h) load_soft + h (replace + load_hard)
      lost GPU-h/day = gpus/3600 * [ (86400/tau) * delta + (86400/M) * (E_lost + E_ttr) ]
      RPO_max = k*tau + L_hard  (worst case, hard failure); overhead % = 100 * delta / tau
    """
    w, r, rel = cfg["workload"], cfg["restart"], cfg["reliability"]
    t = strategy_timings(cfg, strategy)
    m = rel["job_mtbf_h"] * 3600.0
    hf = rel["hard_failure_frac"]
    k = t["pfs_every"]
    if interval_s is None:
        floor = t["L_soft"] if k > 1 else t["L_hard"]
        interval_s = choose_interval_s(t["delta"], m, floor, w["step_time_s"])
    tau = float(interval_s)
    e_lost = (1 - hf) * (tau / 2 + t["L_soft"]) + hf * (k * tau / 2 + t["L_hard"])
    base = r["detect_s"] + r["relaunch_s"] + r["validate_s"] + r["warmup_s"]
    ttr_soft = base + t["load_soft"]
    ttr_hard = base + r["replace_s"] + t["load_hard"]
    e_ttr = (1 - hf) * ttr_soft + hf * ttr_hard
    ckpt_per_day = 86400.0 / tau
    fail_per_day = 86400.0 / m
    gpu_s_ckpt = ckpt_per_day * t["delta"] * w["gpus"]
    gpu_s_fail = fail_per_day * (e_lost + e_ttr) * w["gpus"]
    size = checkpoint_size_bytes(w["params"], w["ckpt_bytes_per_param"])
    return {
        "strategy": strategy,
        "size_GB": size / 1e9,
        "blocking_s": t["blocking"],
        "delta_s": t["delta"],
        "completion_s": t["L_hard"],
        "interval_s": tau,
        "interval_steps": round(tau / w["step_time_s"]),
        "overhead_pct": 100.0 * t["delta"] / tau,
        "rpo_max_s": k * tau + t["L_hard"],
        "rpo_expected_s": e_lost,
        "ttr_soft_s": ttr_soft,
        "ttr_hard_s": ttr_hard,
        "ttr_expected_s": e_ttr,
        "lost_gpu_h_ckpt": gpu_s_ckpt / 3600.0,
        "lost_gpu_h_fail": gpu_s_fail / 3600.0,
        "lost_gpu_h_day": (gpu_s_ckpt + gpu_s_fail) / 3600.0,
        "pfs_write_share": (size / (k * tau)) / (cfg["storage"]["pfs_write_GBps"] * 1e9),
    }


def compare_strategies(cfg: dict) -> pd.DataFrame:
    """One row per strategy in :data:`STRATEGIES`, each at its own chosen interval, indexed by
    strategy name and sorted by ``lost_gpu_h_day`` ascending."""
    df = pd.DataFrame([plan_strategy(cfg, s) for s in STRATEGIES]).set_index("strategy")
    return df.sort_values("lost_gpu_h_day")


# ============================================================================================
# Part B -- I/O trace analyzer
# ============================================================================================


def load_trace(path: str | Path) -> pd.DataFrame:
    """Load the data-loader trace (columns t_s, worker, op, target, bytes, lat_us)."""
    return pd.read_csv(path)


def latency_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """Per-op latency percentiles in microseconds: index = op, columns p50, p99, p999, count.
    Use numpy's default (linear) percentile interpolation."""
    rows = {}
    for op, g in df.groupby("op"):
        v = g["lat_us"].to_numpy()
        rows[op] = {"p50": float(np.percentile(v, 50)), "p99": float(np.percentile(v, 99)),
                    "p999": float(np.percentile(v, 99.9)), "count": int(len(v))}
    return pd.DataFrame.from_dict(rows, orient="index")


def window_profile(df: pd.DataFrame, window_s: float = 1.0) -> pd.DataFrame:
    """Aggregate the trace into fixed windows by op *start* time ``floor(t_s / window_s)``.

    Columns (index = window start time in s, every window from 0 to the last, including empty):
      n_ops, meta_ops, read_GBps (read bytes / window / 1e9), mean_read_bytes,
      meta_time_share (sum lat of META_OPS / sum lat of all ops; 0 if no ops),
      read_p99_us (p99 latency of reads >= 1 MiB; NaN if none), cls (see :func:`classify_window`).
    """
    w = np.floor(df["t_s"] / window_s).astype(int)
    n_win = int(w.max()) + 1
    out = []
    for i in range(n_win):
        g = df[w == i]
        is_meta = g["op"].isin(META_OPS)
        reads = g[g["op"] == "read"]
        big = reads[reads["bytes"] >= MiB]
        tot_lat = float(g["lat_us"].sum())
        row = {
            "t_start": i * window_s,
            "n_ops": int(len(g)),
            "meta_ops": int(is_meta.sum()),
            "read_GBps": float(reads["bytes"].sum()) / window_s / 1e9,
            "mean_read_bytes": float(reads["bytes"].mean()) if len(reads) else 0.0,
            "meta_time_share": float(g.loc[is_meta, "lat_us"].sum()) / tot_lat if tot_lat else 0.0,
            "read_p99_us": float(np.percentile(big["lat_us"], 99)) if len(big) else float("nan"),
        }
        row["cls"] = classify_window(row)
        out.append(row)
    return pd.DataFrame(out).set_index("t_start")


def classify_window(row: dict) -> str:
    """'idle' if n_ops < 50; 'metadata' if meta_time_share >= 0.5; 'bandwidth' if
    mean_read_bytes >= 1 MiB and meta_time_share < 0.2; otherwise 'mixed'."""
    if row["n_ops"] < 50:
        return "idle"
    if row["meta_time_share"] >= 0.5:
        return "metadata"
    if row["mean_read_bytes"] >= MiB and row["meta_time_share"] < 0.2:
        return "bandwidth"
    return "mixed"


def phases(profile: pd.DataFrame) -> list[tuple[float, float, str]]:
    """Merge consecutive windows with the same ``cls`` into (start_s, end_s, cls) tuples, where
    end_s = start of the last window + window width."""
    idx = list(profile.index)
    width = idx[1] - idx[0] if len(idx) > 1 else 1.0
    res: list[tuple[float, float, str]] = []
    for t, c in zip(idx, profile["cls"]):
        if res and res[-1][2] == c:
            res[-1] = (res[-1][0], t + width, c)
        else:
            res.append((t, t + width, c))
    return res


def degraded_windows(profile: pd.DataFrame, factor: float = 2.0) -> list[float]:
    """Bandwidth-class windows whose read_p99_us exceeds ``factor`` x the median read_p99_us of all
    bandwidth-class windows. Returns window start times (ascending)."""
    bw = profile[profile["cls"] == "bandwidth"]
    med = float(bw["read_p99_us"].median())
    return [float(t) for t, v in bw["read_p99_us"].items() if v > factor * med]


def slow_targets(df: pd.DataFrame, factor: float = 2.0) -> list[int]:
    """Targets whose median latency for reads >= 1 MiB exceeds ``factor`` x the median of the
    per-target medians. Returns sorted target ids."""
    big = df[(df["op"] == "read") & (df["bytes"] >= MiB)]
    med = big.groupby("target")["lat_us"].median()
    ref = float(med.median())
    return sorted(int(t) for t, v in med.items() if v > factor * ref)


def parse_fio(path: str | Path) -> pd.DataFrame:
    """Parse fio JSON output into one row per job.

    Columns: job, device, rw, bs, iodepth (int), iops, bw_GBps, mean_lat_us, p99_us, p999_us,
    p9999_us, littles_qd (= iops x mean latency in s; should approximate iodepth).
    Uses the 'read' section for rw in {read, randread}, otherwise the 'write' section.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for j in data["jobs"]:
        o = j["job options"]
        sec = j["read"] if o["rw"] in ("read", "randread") else j["write"]
        pct = sec["clat_ns"]["percentile"]
        mean_us = sec["clat_ns"]["mean"] / 1e3
        rows.append({
            "job": j["jobname"], "device": o["filename"], "rw": o["rw"], "bs": o["bs"],
            "iodepth": int(o["iodepth"]), "iops": float(sec["iops"]),
            "bw_GBps": sec["bw_bytes"] / 1e9, "mean_lat_us": mean_us,
            "p99_us": pct["99.000000"] / 1e3, "p999_us": pct["99.900000"] / 1e3,
            "p9999_us": pct["99.990000"] / 1e3,
            "littles_qd": float(sec["iops"]) * mean_us / 1e6,
        })
    return pd.DataFrame(rows)


def fio_outliers(fio: pd.DataFrame, bw_factor: float = 0.7,
                 tail_factor: float = 5.0) -> set[tuple[str, str]]:
    """Within each (rw, bs) group: ('device', 'LOW_BANDWIDTH') if bw < bw_factor x group median bw;
    ('device', 'TAIL_LATENCY') if p999 > tail_factor x group median p999."""
    out: set[tuple[str, str]] = set()
    for _, g in fio.groupby(["rw", "bs"]):
        mbw, mt = g["bw_GBps"].median(), g["p999_us"].median()
        for _, r in g.iterrows():
            if r["bw_GBps"] < bw_factor * mbw:
                out.add((r["device"], "LOW_BANDWIDTH"))
            if r["p999_us"] > tail_factor * mt:
                out.add((r["device"], "TAIL_LATENCY"))
    return out


# ============================================================================================
# Part C -- checkpoint manifest validator
# ============================================================================================


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_checkpoint(ckpt_dir: str | Path) -> list[str]:
    """Return a list of defect codes for one checkpoint directory (empty list = valid).

    Checks, in order (stop after a fatal manifest problem):
      NO_COMMIT               COMMIT marker missing
      BAD_MANIFEST            manifest.json missing or not parseable JSON
      MANIFEST_HASH_MISMATCH  COMMIT content != sha256(manifest.json bytes)
      WORLD_SIZE_MISMATCH     shard ranks != {0..world_size-1}
      MISSING_SHARD           a listed shard file does not exist
      SIZE_MISMATCH           shard file size != manifest bytes
      CHECKSUM_MISMATCH       shard sha256 != manifest sha256 (only checked if size matches)
    Codes are de-duplicated and returned in the order above.
    """
    d = Path(ckpt_dir)
    codes: list[str] = []
    commit_p, man_p = d / "COMMIT", d / "manifest.json"
    if not commit_p.exists():
        codes.append("NO_COMMIT")
    try:
        mbytes = man_p.read_bytes()
        manifest = json.loads(mbytes)
    except (OSError, ValueError):
        codes.append("BAD_MANIFEST")
        return codes
    if commit_p.exists():
        if commit_p.read_text(encoding="ascii").strip() != hashlib.sha256(mbytes).hexdigest():
            codes.append("MANIFEST_HASH_MISMATCH")
    shards = manifest.get("shards", [])
    if sorted(s["rank"] for s in shards) != list(range(int(manifest.get("world_size", -1)))):
        codes.append("WORLD_SIZE_MISMATCH")
    found: list[str] = []
    for s in shards:
        p = d / s["file"]
        if not p.exists():
            found.append("MISSING_SHARD")
        elif p.stat().st_size != s["bytes"]:
            found.append("SIZE_MISMATCH")
        elif _sha256_file(p) != s["sha256"]:
            found.append("CHECKSUM_MISMATCH")
    for c in ("MISSING_SHARD", "SIZE_MISMATCH", "CHECKSUM_MISMATCH"):
        if c in found:
            codes.append(c)
    return codes


def audit_store(root: str | Path) -> dict[str, list[str]]:
    """Validate every ``step_*`` directory under ``root``: {dir name: defect codes}."""
    r = Path(root)
    return {p.name: validate_checkpoint(p) for p in sorted(r.glob("step_*")) if p.is_dir()}


def select_latest_valid(root: str | Path) -> str | None:
    """Name of the highest-step checkpoint with no defects (ignore the ``latest`` pointer)."""
    valid = [name for name, codes in audit_store(root).items() if not codes]
    return max(valid, key=lambda n: int(n.split("_")[1])) if valid else None
