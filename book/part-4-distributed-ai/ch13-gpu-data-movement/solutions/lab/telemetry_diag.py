"""Cross-layer diagnosis of a synchronous training job from per-rank, per-step telemetry (reference).

Input: ``data/telemetry.csv`` (see ``tools/generate_telemetry.py`` for column meanings and units).
All results are derived from [SIMULATED] telemetry.

Method (Chapter 13, Section 13.9): compute per-step straggler statistics, find ranks that are
persistently slow with a robust z-score, find when each problem started, attribute each slow rank to
a cause from *independent* evidence (clocks/temperature, tokens, NIC counters), check rails as a
group, quantify the GPU time the job loses to waiting, and reject decoys.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MAD_SCALE = 1.4826   # makes MAD a consistent estimator of sigma for normal data


def load_telemetry(path: Path) -> pd.DataFrame:
    """Read the telemetry CSV, sorted by (step, rank)."""
    return pd.read_csv(path).sort_values(["step", "rank"]).reset_index(drop=True)


def per_step_stats(df: pd.DataFrame) -> pd.DataFrame:
    """One row per step: median/max compute_ms, the slowest rank, straggler ratio (max/median),
    sync overhead (max - median compute, ms), mean wait_ms, comm_ms (median), step_ms."""
    g = df.groupby("step")
    out = pd.DataFrame({
        "median_compute_ms": g["compute_ms"].median(),
        "max_compute_ms": g["compute_ms"].max(),
        "slowest_rank": df.loc[g["compute_ms"].idxmax(), ["step", "rank"]].set_index("step")["rank"],
        "mean_wait_ms": g["wait_ms"].mean(),
        "comm_ms": g["comm_ms"].median(),
        "step_ms": g["step_ms"].first(),
    })
    out["straggler_ratio"] = out["max_compute_ms"] / out["median_compute_ms"]
    out["sync_overhead_ms"] = out["max_compute_ms"] - out["median_compute_ms"]
    return out.reset_index()


def robust_z(df: pd.DataFrame, col: str) -> pd.Series:
    """Per-step robust z-score of ``col``: (x - median_step) / (1.4826 * MAD_step)."""
    med = df.groupby("step")[col].transform("median")
    mad = (df[col] - med).abs().groupby(df["step"]).transform("median") * MAD_SCALE
    return (df[col] - med) / mad.replace(0, np.nan)


def find_stragglers(df: pd.DataFrame, z_threshold: float = 6.0, min_fraction: float = 0.25) -> list[int]:
    """Ranks whose compute_ms robust z exceeds ``z_threshold`` in at least ``min_fraction`` of steps."""
    z = robust_z(df, "compute_ms")
    frac = (z > z_threshold).groupby(df["rank"]).mean()
    return sorted(int(r) for r in frac[frac >= min_fraction].index)


def onset_step(flags: pd.Series, run: int = 3) -> int | None:
    """First step of the first run of ``run`` consecutive True values in a step-indexed boolean series."""
    s = flags.sort_index()
    count = 0
    for step, v in s.items():
        count = count + 1 if v else 0
        if count == run:
            return int(step) - run + 1
    return None


def rank_onset(df: pd.DataFrame, rank: int, z_threshold: float = 6.0) -> int | None:
    """Step at which ``rank``'s compute_ms becomes a persistent outlier."""
    z = robust_z(df, "compute_ms")
    flags = (z[df["rank"] == rank] > z_threshold)
    flags.index = df.loc[df["rank"] == rank, "step"]
    return onset_step(flags)


def attribute_cause(df: pd.DataFrame, rank: int) -> str:
    """Cause of a slow rank from evidence independent of compute time, over the steps where it is slow.

    'thermal'        SM clock >= 10 % below the step median and a thermal clocks-event reason
    'data_imbalance' tokens robust z > 6 with clocks normal
    'network'        retransmissions far above the step median
    'unknown'        none of the above
    """
    z = robust_z(df, "compute_ms")
    mine = df[(df["rank"] == rank) & (z > 6.0)]
    if mine.empty:
        return "unknown"
    steps = mine["step"]
    peers = df[df["step"].isin(steps)].groupby("step")
    clock_ratio = (mine.set_index("step")["sm_clock_mhz"] / peers["sm_clock_mhz"].median()).median()
    thermal_reason = mine["clocks_event_reason"].str.contains("thermal").mean() > 0.5
    if clock_ratio < 0.9 and thermal_reason:
        return "thermal"
    tz = robust_z(df, "tokens")[mine.index].median()
    if tz > 6.0 and clock_ratio >= 0.97:
        return "data_imbalance"
    retx_ratio = (mine.set_index("step")["nic_retx"] / (peers["nic_retx"].median() + 1)).median()
    if retx_ratio > 100:
        return "network"
    return "unknown"


def rail_health(df: pd.DataFrame, retx_factor: float = 100.0) -> pd.DataFrame:
    """Per rail (local_rank): median retransmissions per step, median nic_tx_gbps, onset step, flag.

    A rail is flagged when its median retransmissions exceed ``retx_factor`` x (median across rails + 1)
    over the second half of the job; onset is the first step of 3 consecutive steps where the rail's
    median retransmissions exceed that limit.
    """
    by = df.groupby(["step", "local_rank"])["nic_retx"].median().unstack()
    late = by[by.index >= by.index.max() // 2]
    base = late.median(axis=1).median()
    limit = retx_factor * (base + 1)
    rows = []
    for rail in by.columns:
        flagged = bool(late[rail].median() > limit)
        rows.append({
            "rail": int(rail),
            "median_retx": float(df.loc[df["local_rank"] == rail, "nic_retx"].median()),
            "late_median_retx": float(late[rail].median()),
            "median_tx_gbps": float(df.loc[df["local_rank"] == rail, "nic_tx_gbps"].median()),
            "flagged": flagged,
            "onset_step": onset_step(by[rail] > limit) if flagged else None,
        })
    return pd.DataFrame(rows)


def hot_not_throttled(df: pd.DataFrame, temp_c: float = 80.0) -> list[int]:
    """Decoys: ranks with median temperature >= temp_c but clocks within 2 % of peers and no
    thermal clocks-event reason. Hot alone is not a cause."""
    med = df.groupby("rank").agg(temp=("gpu_temp_c", "median"), clock=("sm_clock_mhz", "median"),
                                 thermal=("clocks_event_reason", lambda s: s.str.contains("thermal").any()))
    peer_clock = med["clock"].median()
    hit = med[(med["temp"] >= temp_c) & (med["clock"] >= 0.98 * peer_clock) & (~med["thermal"])]
    return sorted(int(r) for r in hit.index)


def amplification(df: pd.DataFrame, first_step: int, last_step: int) -> dict[str, float]:
    """GPU time lost to synchronization skew in [first_step, last_step].

    lost_gpu_s     sum of wait_ms over ranks and steps / 1000 (GPU-seconds spent waiting for laggards)
    lost_fraction  lost_gpu_s / (ranks * sum of step_ms / 1000)
    ideal_step_ms  median compute + median dataloader wait + median comm + (step - max arrival - comm),
                   i.e. the step time if every rank were at the median
    """
    w = df[(df["step"] >= first_step) & (df["step"] <= last_step)]
    lost = w["wait_ms"].sum() / 1000.0
    steps = w.groupby("step")["step_ms"].first()
    ranks = w["rank"].nunique()
    arrive = w["dataloader_wait_ms"] + w["compute_ms"]
    g = w.assign(arrive=arrive).groupby("step")
    overhead = steps - g["arrive"].max() - g["comm_ms"].median()
    ideal = (g["arrive"].median() + g["comm_ms"].median() + overhead).median()
    return {"lost_gpu_s": float(lost), "lost_fraction": float(lost / (ranks * steps.sum() / 1000.0)),
            "ideal_step_ms": float(ideal), "actual_step_ms": float(steps.median())}


def symptom_windows(df: pd.DataFrame, bounds: list[tuple[int, int]]) -> pd.DataFrame:
    """Mean step_ms, gpu_util_pct, sm_active_pct, nic_tx_gbps, burst_tx_gbps, wait_ms, comm_ms per window.

    burst_tx_gbps = nic_tx_gbps * step_ms / comm_ms: the NIC rate while the all-reduce is moving data
    (the step average hides that the NIC is near line rate during the communication phase).
    """
    rows = []
    for a, b in bounds:
        w = df[(df["step"] >= a) & (df["step"] <= b)]
        rows.append({"window": f"{a}-{b}", "step_ms": w["step_ms"].mean(), "gpu_util_pct": w["gpu_util_pct"].mean(),
                     "sm_active_pct": w["sm_active_pct"].mean(), "nic_tx_gbps": w["nic_tx_gbps"].mean(),
                     "burst_tx_gbps": (w["nic_tx_gbps"] * w["step_ms"] / w["comm_ms"]).mean(),
                     "wait_ms": w["wait_ms"].mean(), "comm_ms": w["comm_ms"].mean()})
    return pd.DataFrame(rows)


def diagnose(df: pd.DataFrame) -> dict[str, object]:
    """Assemble findings: stragglers with cause and onset, flagged rails, decoys."""
    strag = find_stragglers(df)
    rails = rail_health(df)
    return {
        "stragglers": {r: {"cause": attribute_cause(df, r), "onset_step": rank_onset(df, r)} for r in strag},
        "degraded_rails": {int(r.rail): int(r.onset_step) for r in rails[rails["flagged"]].itertuples()},
        "decoys": hot_not_throttled(df),
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Diagnose the Chapter 13 telemetry bundle")
    ap.add_argument("--data", type=Path,
                    default=Path(__file__).resolve().parents[2] / "lab" / "data" / "telemetry.csv")
    args = ap.parse_args()
    pd.set_option("display.width", 200)
    df = load_telemetry(args.data)
    print(per_step_stats(df).iloc[[0, 19, 20, 29, 30, 59]].round(2).to_string(index=False))
    print(symptom_windows(df, [(0, 19), (20, 29), (30, 59)]).round(1).to_string(index=False))
    print(rail_health(df).round(1).to_string(index=False))
    print(amplification(df, 30, 59))
    print(diagnose(df))


if __name__ == "__main__":
    main()
