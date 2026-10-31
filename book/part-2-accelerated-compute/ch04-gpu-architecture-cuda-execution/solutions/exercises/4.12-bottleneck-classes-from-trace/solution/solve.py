"""Exercise 4.12: one instance each of launch overhead, transfer cost, occupancy constraint and a
memory-bandwidth bottleneck, computed directly from the Lab 4 capture (step train_step_41).

Usage: python solve.py --out DIR
Reads lab/data/{gpu_trace,cuda_api_trace,nvtx_ranges}.csv and device.json of this package. The trace is
[SIMULATED]; derived occupancy and roof fractions are [MODELED].
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
STEP = "train_step_41"
LN = "layernorm_bwd_fused_kernel"
# exercises-key.md 4.12
KEY = {"opt_kernel_median_us": 2.6, "launch_interval_us": 9.3, "pageable_bytes": 100_663_296,
       "pageable_ms": 8.26, "pageable_GBps": 12.19, "ln_occupancy": 0.125, "ln_roof": 0.216, "ln_GBps": 725}
TOL = 0.02  # relative


def occupancy(threads: int, regs: int, smem: int, d: dict) -> tuple[float, str, int]:
    wpb = math.ceil(threads / d["warp_size"])
    unit = d["reg_alloc_unit_per_warp"]
    rpw = math.ceil(regs * d["warp_size"] / unit) * unit
    warps_regs = (d["regs_per_sm"] // rpw) // d["warp_alloc_granularity"] * d["warp_alloc_granularity"]
    limits = {"warps": d["max_warps_per_sm"] // wpb, "registers": warps_regs // wpb,
              "shared_memory": d["smem_per_sm_bytes"] // (smem + d["smem_reserved_per_block_bytes"]),
              "blocks": d["max_blocks_per_sm"]}
    b = min(limits.values())
    return b * wpb / d["max_warps_per_sm"], next(k for k, v in limits.items() if v == b), warps_regs


def close(a: float, b: float) -> bool:
    return abs(a - b) <= TOL * abs(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    gpu = pd.read_csv(DATA / "gpu_trace.csv")
    api = pd.read_csv(DATA / "cuda_api_trace.csv")
    nvtx = pd.read_csv(DATA / "nvtx_ranges.csv")
    dev = json.loads((DATA / "device.json").read_text(encoding="utf-8"))
    step = nvtx[nvtx["name"] == STEP].iloc[0]
    in_step = nvtx[(nvtx["start_ns"] >= step["start_ns"]) & (nvtx["end_ns"] <= step["end_ns"])]
    opt = in_step[in_step["name"] == "optimizer_step"].iloc[0]

    # 1. Launch overhead: the optimizer comb.
    k = gpu[(gpu["kind"] == "kernel") & (gpu["start_ns"] >= opt["start_ns"]) & (gpu["start_ns"] < opt["end_ns"])]
    tiny = k[k["grid_x"] == 4].sort_values("start_ns")
    dur = (tiny["end_ns"] - tiny["start_ns"]).to_numpy()
    gaps = tiny["start_ns"].to_numpy()[1:] - tiny["end_ns"].to_numpy()[:-1]
    launches = api[(api["name"] == "cudaLaunchKernel") & (api["start_ns"] >= opt["start_ns"])
                   & (api["start_ns"] < opt["end_ns"])].sort_values("start_ns")
    interval = float(np.median(np.diff(launches["start_ns"].to_numpy())))
    opt_ms = (opt["end_ns"] - opt["start_ns"]) / 1e6
    busy_ms = dur.sum() / 1e6
    launch = {"nvtx_range": "optimizer_step", "tiny_kernels": int(len(tiny)), "grid_x": 4,
              "first_row_id": int(tiny["id"].iloc[0]), "last_row_id": int(tiny["id"].iloc[-1]),
              "median_kernel_us": round(float(np.median(dur)) / 1e3, 2),
              "median_gap_us": round(float(np.median(gaps)) / 1e3, 2),
              "median_launch_interval_us": round(interval / 1e3, 2),
              "range_ms": round(opt_ms, 3), "tiny_kernel_busy_ms": round(busy_ms, 3)}

    # 2. Transfer cost: the large pageable H2D copy of this step.
    c = gpu[(gpu["kind"] == "memcpy") & (gpu["start_ns"] >= step["start_ns"]) & (gpu["start_ns"] < step["end_ns"])].copy()
    c["dur_ns"] = c["end_ns"] - c["start_ns"]
    c["GBps"] = c["bytes"] / c["dur_ns"]
    big = c[c["src_mem"] == "pageable"].sort_values("bytes", ascending=False).iloc[0]
    call = api[api["correlation_id"] == big["correlation_id"]].iloc[0]
    pinned = c[(c["src_mem"] == "pinned") | (c["dst_mem"] == "pinned")]
    transfer = {"row_id": int(big["id"]), "bytes": int(big["bytes"]), "gpu_ms": round(big["dur_ns"] / 1e6, 3),
                "GBps": round(float(big["GBps"]), 2), "api_call": call["name"],
                "api_ms": round((call["end_ns"] - call["start_ns"]) / 1e6, 3),
                "pinned_GBps_median": round(float(pinned["GBps"].median()), 1)}

    # 3 and 4. layernorm_bwd: occupancy limiter and fraction of the HBM roof (the 12 instances in this step).
    ln = gpu[(gpu["name"] == LN) & (gpu["start_ns"] >= step["start_ns"]) & (gpu["start_ns"] < step["end_ns"])]
    first = ln.iloc[0]
    occ, limiter, warps_regs = occupancy(int(first["block_x"]), int(first["regs_per_thread"]),
                                         int(first["smem_per_block_bytes"]), dev)
    secs = (ln["end_ns"] - ln["start_ns"]).sum() / 1e9
    gbps = ln["dram_bytes"].sum() / secs / 1e9
    roof = gbps * 1e9 / dev["hbm_bytes_per_s"]
    occ_rec = {"kernel": LN, "row_id_example": int(first["id"]), "block_threads": int(first["block_x"]),
               "regs_per_thread": int(first["regs_per_thread"]), "warps_allowed_by_registers": warps_regs,
               "occupancy": occ, "limiter": limiter}
    bw_rec = {"kernel": LN, "instances": int(len(ln)), "dram_bytes_each": int(first["dram_bytes"]),
              "achieved_GBps": round(gbps, 1), "fraction_of_hbm": round(roof, 4)}

    assert close(launch["median_kernel_us"], KEY["opt_kernel_median_us"]), launch
    assert close(launch["median_launch_interval_us"], KEY["launch_interval_us"]), launch
    assert transfer["bytes"] == KEY["pageable_bytes"]
    assert close(transfer["gpu_ms"], KEY["pageable_ms"]) and close(transfer["GBps"], KEY["pageable_GBps"]), transfer
    assert occ == KEY["ln_occupancy"] and limiter == "registers", occ_rec
    assert close(roof, KEY["ln_roof"]) and close(gbps, KEY["ln_GBps"]), (roof, gbps)

    res = {"exercise": "4.12", "evidence_label": "SIMULATED trace; occupancy and roof fractions MODELED",
           "inputs": {"data": "lab/data (seed 4 capture)", "step": STEP},
           "answer": {"launch_overhead": launch, "memory_transfer": transfer, "occupancy_constraint": occ_rec,
                      "memory_bandwidth": bw_rec},
           "units": {"time": "µs or ms as named", "bandwidth": "GB/s", "bytes": "B"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 4.12 — four bottleneck classes in `{STEP}`

| Class | Evidence (quoted from the capture) | Label |
|---|---|---|
| Launch overhead | `optimizer_step` range ({launch['range_ms']:.2f} ms): {launch['tiny_kernels']} grid-4 kernels, rows {launch['first_row_id']}–{launch['last_row_id']}; median kernel {launch['median_kernel_us']:.2f} µs, median `cudaLaunchKernel` interval {launch['median_launch_interval_us']:.2f} µs, median GPU gap {launch['median_gap_us']:.2f} µs; kernels busy {launch['tiny_kernel_busy_ms']:.2f} ms of the range | `[SIMULATED]` |
| Memory-transfer cost | row {transfer['row_id']}: {transfer['bytes']:,} B HtoD from pageable memory in {transfer['gpu_ms']:.2f} ms = {transfer['GBps']:.2f} GB/s; its `{transfer['api_call']}` blocks the host for {transfer['api_ms']:.2f} ms; pinned copies run at {transfer['pinned_GBps_median']:.1f} GB/s | `[SIMULATED]` |
| Occupancy constraint | `{LN}` (row {occ_rec['row_id_example']}): {occ_rec['block_threads']} threads, {occ_rec['regs_per_thread']} registers → {occ_rec['warps_allowed_by_registers']} warps by registers → 1 block of 8 warps → {occ * 100:.1f} % ({limiter}) | `[MODELED]` |
| Memory-bandwidth bottleneck | `{LN}`: {bw_rec['instances']} instances × {bw_rec['dram_bytes_each']:,} B; {bw_rec['achieved_GBps']:.0f} GB/s = {roof * 100:.1f} % of 3.35 TB/s | `[SIMULATED]` / `[MODELED]` |
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
