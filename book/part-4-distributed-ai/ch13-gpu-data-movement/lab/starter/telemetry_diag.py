"""Cross-layer diagnosis of a synchronous training job from per-rank, per-step telemetry (STARTER -- implement the TODOs).

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
    # TODO: group by step; median/max compute, slowest rank, mean wait, median comm, step_ms, ratio, overhead.
    raise NotImplementedError("per_step_stats")


def robust_z(df: pd.DataFrame, col: str) -> pd.Series:
    """Per-step robust z-score of ``col``: (x - median_step) / (1.4826 * MAD_step)."""
    # TODO: per-step median and MAD (scaled by 1.4826); return (x - median) / scaled MAD.
    raise NotImplementedError("robust_z")


def find_stragglers(df: pd.DataFrame, z_threshold: float = 6.0, min_fraction: float = 0.25) -> list[int]:
    """Ranks whose compute_ms robust z exceeds ``z_threshold`` in at least ``min_fraction`` of steps."""
    # TODO: fraction of steps with robust z(compute_ms) > threshold, per rank; keep ranks >= min_fraction.
    raise NotImplementedError("find_stragglers")


def onset_step(flags: pd.Series, run: int = 3) -> int | None:
    """First step of the first run of ``run`` consecutive True values in a step-indexed boolean series."""
    # TODO: scan steps in order; return the first step of the first run of `run` consecutive True values.
    raise NotImplementedError("onset_step")


def rank_onset(df: pd.DataFrame, rank: int, z_threshold: float = 6.0) -> int | None:
    """Step at which ``rank``'s compute_ms becomes a persistent outlier."""
    # TODO: robust z of compute_ms for this rank -> boolean series indexed by step -> onset_step.
    raise NotImplementedError("rank_onset")


def attribute_cause(df: pd.DataFrame, rank: int) -> str:
    """Cause of a slow rank from evidence independent of compute time, over the steps where it is slow.

    'thermal'        SM clock >= 10 % below the step median and a thermal clocks-event reason
    'data_imbalance' tokens robust z > 6 with clocks normal
    'network'        retransmissions far above the step median
    'unknown'        none of the above
    """
    # TODO: over the rank's slow steps compare clocks/thermal reason, tokens z, and retransmissions with peers.
    raise NotImplementedError("attribute_cause")


def rail_health(df: pd.DataFrame, retx_factor: float = 100.0) -> pd.DataFrame:
    """Per rail (local_rank): median retransmissions per step, median nic_tx_gbps, onset step, flag.

    A rail is flagged when its median retransmissions exceed ``retx_factor`` x (median across rails + 1)
    over the second half of the job; onset is the first step of 3 consecutive steps where the rail's
    median retransmissions exceed that limit.
    """
    # TODO: per-step per-rail median retransmissions; flag rails far above the cross-rail median; find onset.
    raise NotImplementedError("rail_health")


def hot_not_throttled(df: pd.DataFrame, temp_c: float = 80.0) -> list[int]:
    """Decoys: ranks with median temperature >= temp_c but clocks within 2 % of peers and no
    thermal clocks-event reason. Hot alone is not a cause."""
    # TODO: ranks with median temp >= temp_c, clock within 2 % of peers, and no thermal reason.
    raise NotImplementedError("hot_not_throttled")


def amplification(df: pd.DataFrame, first_step: int, last_step: int) -> dict[str, float]:
    """GPU time lost to synchronization skew in [first_step, last_step].

    lost_gpu_s     sum of wait_ms over ranks and steps / 1000 (GPU-seconds spent waiting for laggards)
    lost_fraction  lost_gpu_s / (ranks * sum of step_ms / 1000)
    ideal_step_ms  median compute + median dataloader wait + median comm + (step - max arrival - comm),
                   i.e. the step time if every rank were at the median
    """
    # TODO: sum wait_ms -> GPU-seconds lost; fraction of rank-time; ideal vs actual step time.
    raise NotImplementedError("amplification")


def symptom_windows(df: pd.DataFrame, bounds: list[tuple[int, int]]) -> pd.DataFrame:
    """Mean step_ms, gpu_util_pct, sm_active_pct, nic_tx_gbps, burst_tx_gbps, wait_ms, comm_ms per window.

    burst_tx_gbps = nic_tx_gbps * step_ms / comm_ms: the NIC rate while the all-reduce is moving data
    (the step average hides that the NIC is near line rate during the communication phase).
    """
    # TODO: window means of the listed columns, including burst_tx_gbps.
    raise NotImplementedError("symptom_windows")


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
