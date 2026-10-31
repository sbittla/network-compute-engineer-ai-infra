"""D1 - dedicated vs shared chat-70b inference pool: useful GPU-hours per year.

python solve.py --out DIR.  Pool sizing from manuscript Section 21.3 [ILLUSTRATIVE]; lending assumptions are
the reference approach's stated assumptions; results [MODELED].
Method: busy GPU-h = average busy replicas × 8 × 8,760; idle = provisioned - busy; never lend the N+2 headroom;
lend a stated fraction of idle hours; useful borrowed work = lent GPU-h × preemptible goodput.
"""
import argparse
import json
from pathlib import Path

HOURS = 8760
PEAK_RPS = 25.0                # Section 21.3 forecast at daily peak
RPS_PER_REPLICA = 2.5          # measured per-replica capacity at the SLO [ILLUSTRATIVE]
HEADROOM_REPLICAS = 2          # N+2
GPUS_PER_REPLICA = 8           # TP = 8 on one HX8 node
AVG_LOAD_OF_PEAK = 0.40        # prompt: average load 40 % of peak
LENDABLE_FRACTION_OF_IDLE = 0.60   # assumption: idle hours beyond a forecast-plus-margin threshold
PREEMPTIBLE_GOODPUT = 0.70     # assumption: frequent checkpoints, lost work at each reclaim
USD_PER_USEFUL_GPU_H = 4.75    # Section 21.4 ORION-256 cost per useful GPU-hour
KEY = {"provisioned_gpu_h": 840_960, "idle_gpu_h": 560_640, "lent_gpu_h": 336_384,
       "useful_borrowed_gpu_h": 235_469, "value_musd": 1.12}
TOL_H = 1.0
TOL_MUSD = 0.005


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    peak_replicas = PEAK_RPS / RPS_PER_REPLICA
    replicas = peak_replicas + HEADROOM_REPLICAS
    gpus = int(replicas * GPUS_PER_REPLICA)
    provisioned = gpus * HOURS
    busy_replicas = AVG_LOAD_OF_PEAK * peak_replicas
    busy = busy_replicas * GPUS_PER_REPLICA * HOURS
    idle = provisioned - busy
    headroom_h = HEADROOM_REPLICAS * GPUS_PER_REPLICA * HOURS
    idle_beyond_headroom = idle - headroom_h
    lent = LENDABLE_FRACTION_OF_IDLE * idle
    assert lent <= idle_beyond_headroom, "lending must never touch the N+2 headroom"
    useful_borrowed = lent * PREEMPTIBLE_GOODPUT
    value = useful_borrowed * USD_PER_USEFUL_GPU_H / 1e6
    dedicated_alloc = busy / provisioned
    shared_alloc = (busy + lent) / provisioned
    # common mistake: treating 40 % of peak as 40 % of the whole 96-GPU pool (ignores the N+2 replicas)
    wrong_idle = provisioned * (1 - AVG_LOAD_OF_PEAK)

    assert gpus == 96
    for k, v in (("provisioned_gpu_h", provisioned), ("idle_gpu_h", idle), ("lent_gpu_h", lent),
                 ("useful_borrowed_gpu_h", useful_borrowed)):
        assert abs(v - KEY[k]) <= TOL_H, (k, v)
    assert abs(value - KEY["value_musd"]) <= TOL_MUSD, value

    result = {
        "exercise": "D1", "evidence_label": "[MODELED]",
        "inputs": {"peak_rps": PEAK_RPS, "rps_per_replica": RPS_PER_REPLICA, "headroom_replicas": HEADROOM_REPLICAS,
                   "avg_load_of_peak": AVG_LOAD_OF_PEAK, "lendable_fraction_of_idle": LENDABLE_FRACTION_OF_IDLE,
                   "preemptible_goodput": PREEMPTIBLE_GOODPUT, "usd_per_useful_gpu_h": USD_PER_USEFUL_GPU_H},
        "steps": {"replicas": replicas, "gpus": gpus, "busy_replicas_avg": round(busy_replicas, 2),
                  "busy_gpu_h": round(busy), "headroom_gpu_h": headroom_h,
                  "idle_beyond_headroom_gpu_h": round(idle_beyond_headroom),
                  "dedicated_allocated_fraction": round(dedicated_alloc, 3),
                  "shared_allocated_fraction": round(shared_alloc, 3),
                  "wrong_idle_if_40pct_of_pool": round(wrong_idle)},
        "answer": {"option1_dedicated_useful_gpu_h": round(busy), "option2_shared_useful_gpu_h": round(busy + useful_borrowed),
                   "provisioned_gpu_h": provisioned, "idle_gpu_h": round(idle), "lent_gpu_h": round(lent),
                   "useful_borrowed_gpu_h": round(useful_borrowed), "borrowed_value_musd_per_year": round(value, 2)},
        "units": {"gpu_h": "GPU-hours per year", "value": "USD millions per year at $4.75 per useful GPU-hour"},
        "tolerance": {"gpu_h": TOL_H, "value_musd": TOL_MUSD},
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# D1 - the inference pool `[MODELED]`", "",
          f"- Pool: {peak_replicas:.0f} peak replicas + N+{HEADROOM_REPLICAS} = {replicas:.0f} replicas = {gpus} GPUs "
          f"-> {provisioned:,} GPU-h/yr",
          f"- Average busy: {AVG_LOAD_OF_PEAK} × {peak_replicas:.0f} = {busy_replicas:.0f} replicas -> {busy:,.0f} GPU-h "
          f"({dedicated_alloc * 100:.1f} % of the pool)",
          f"- Idle: {idle:,.0f} GPU-h, of which {idle_beyond_headroom:,.0f} beyond the N+2 headroom",
          f"- Lent: {LENDABLE_FRACTION_OF_IDLE} × idle = {lent:,.0f} GPU-h; useful at goodput "
          f"{PREEMPTIBLE_GOODPUT} = **{useful_borrowed:,.0f} GPU-h** = **${value:.2f}M/yr** at ${USD_PER_USEFUL_GPU_H}", "",
          "| Option | Useful GPU-h/yr | Allocated fraction |", "|---|---|---|",
          f"| 1 Dedicated | {busy:,.0f} | {dedicated_alloc * 100:.1f} % |",
          f"| 2 Shared | {busy + useful_borrowed:,.0f} | {shared_alloc * 100:.1f} % |", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
