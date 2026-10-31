"""O2 -- Serving-trace metrics for the baseline and each detected episode. [SIMULATED data]

Usage: python solve.py --out DIR
Inputs: lab/data/requests.csv, token_gaps.csv, replica_telemetry.csv, configs.yaml (window 15 s).
Episodes are detected as in lab Part B: queueing collapse = windows with queue p95 > 2 s containing an
arrival spike >= 1.5× the median window; preemption storm = windows with >= 2 preemptions, bridging gaps
of up to 2 windows. Baseline = arrivals before 230 s (prompt).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
BASELINE_END = 230.0
# Key O2 table: (req/s, out tokens/s, TTFT p50, TTFT p95, ITL p50 ms, ITL p99 ms, queue p95, busy %, KV max %)
KEY = {"baseline": (6.00, 1216, 0.138, 0.449, 21.8, 216, 0.11, 97.6, 13.5),
       "burst": (14.8, 2980, 11.8, 28.8, 26.9, 444, 28.5, 100.0, 43.3),
       "storm": (5.81, 1434, 0.278, 33.2, 37.2, 386, 32.6, 100.0, 100.0)}


def episodes(flags: pd.Series, w: float, max_gap: int) -> list:
    eps = []
    for s in sorted(float(i) for i, f in flags.items() if f):
        if eps and s - eps[-1][1] <= max_gap * w:
            eps[-1][1] = s + w
        else:
            eps.append([s, s + w])
    return eps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    w = float(cfg["trace"]["window_s"])
    r = pd.read_csv(DATA / "requests.csv")
    r["queue_s"] = r["sched_s"] - r["arrival_s"]
    r["ttft_s"] = r["first_token_s"] - r["arrival_s"]
    gaps = pd.read_csv(DATA / "token_gaps.csv", dtype={"itl_ms": str}, keep_default_na=False)
    tel = pd.read_csv(DATA / "replica_telemetry.csv")

    win = r.groupby((r["arrival_s"] // w) * w)
    arrivals, q95, pre = win.size(), win["queue_s"].quantile(0.95), win["preemptions"].sum()
    storm = episodes(pre >= 2, w, 2)
    burst = [e for e in episodes(q95 > 2.0, w, 0)
             if arrivals.loc[e[0]:e[1] - w].max() / arrivals.median() >= 1.5]
    assert storm == [[465.0, 600.0]] and burst == [[240.0, 345.0]], (storm, burst)
    segs = {"baseline": (0.0, BASELINE_END), "burst": tuple(burst[0]), "storm": tuple(storm[0])}

    rows = {}
    for name, (a, b) in segs.items():
        seg = r[(r["arrival_s"] >= a) & (r["arrival_s"] < b)]
        dur = b - a
        itl = np.array([float(x) for s in gaps[gaps["request_id"].isin(seg["request_id"])]["itl_ms"] if s
                        for x in s.split(";")])
        t = tel[(tel["t_s"] >= a) & (tel["t_s"] <= b)]
        rows[name] = {"start_s": a, "end_s": b, "req_per_s": round(len(seg) / dur, 2),
                      "out_tok_per_s": round(seg["output_tokens"].sum() / dur),
                      "ttft_p50_s": round(float(np.percentile(seg["ttft_s"], 50)), 3),
                      "ttft_p95_s": round(float(np.percentile(seg["ttft_s"], 95)), 3),
                      "itl_p50_ms": round(float(np.percentile(itl, 50)), 1),
                      "itl_p99_ms": round(float(np.percentile(itl, 99)), 1),
                      "queue_p95_s": round(float(np.percentile(seg["queue_s"], 95)), 2),
                      "gpu_busy_pct": round(float(t["gpu_busy_pct"].mean()), 1),
                      "kv_max_pct": round(float(t["kv_usage_pct"].max()), 1),
                      "waiting_mean": round(float(t["num_waiting"].mean()), 1)}
    for name, k in KEY.items():
        v = rows[name]
        got = (v["req_per_s"], v["out_tok_per_s"], v["ttft_p50_s"], v["ttft_p95_s"], v["itl_p50_ms"],
               v["itl_p99_ms"], v["queue_p95_s"], v["gpu_busy_pct"], v["kv_max_pct"])
        for x, y in zip(got, k):
            assert abs(x - y) <= max(0.011, 0.006 * abs(y)), (name, x, y)   # key rounding (3 s.f.)
    busy = [v["gpu_busy_pct"] for v in rows.values()]
    assert max(busy) - min(busy) < 3, busy      # GPU busy barely moves: the least informative metric

    result = {"inputs": {"files": ["requests.csv", "token_gaps.csv", "replica_telemetry.csv"], "window_s": w,
                         "baseline_end_s": BASELINE_END},
              "steps": {"episodes": {"queueing_collapse": burst, "preemption_storm": storm}},
              "answer": rows, "units": {"rates": "1/s", "ttft/queue": "s", "itl": "ms", "pct": "%"},
              "evidence_label": "[SIMULATED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# O2 trace analysis `[SIMULATED]`", "",
             "| Segment | req/s | out tokens/s | TTFT p50/p95 | ITL p50/p99 | Queue p95 | GPU busy | KV max | Waiting |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, v in rows.items():
        lines.append(f"| {name} {v['start_s']:.0f}-{v['end_s']:.0f} s | {v['req_per_s']} | {v['out_tok_per_s']:,} | "
                     f"{v['ttft_p50_s']} / {v['ttft_p95_s']} s | {v['itl_p50_ms']} / {v['itl_p99_ms']} ms | "
                     f"{v['queue_p95_s']} s | {v['gpu_busy_pct']} % | {v['kv_max_pct']} % | {v['waiting_mean']} |")
    lines += ["", "GPU busy is ≈ 98-100 % in every segment and cannot separate healthy, slot-bound and memory-bound.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
