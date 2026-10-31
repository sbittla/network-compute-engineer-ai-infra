"""Exercise 4.8: theoretical occupancy (Section 4.7 rules) and the Little's-law bandwidth bound.

Usage: python solve.py --out DIR
Device limits come from the package's lab/data/device.json (Table 4.1, CC 9.0 class); kernel
parameters from the prompt: 128 threads/block, 80 registers/thread, 49,152 B then 32,768 B shared
memory per block, two independent 128-B loads in flight per warp, 600 ns latency, 3.35 TB/s.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
THREADS, REGS = 128, 80
SMEM_CASES = {"a_b": 49_152, "c": 32_768}
LOADS_PER_WARP, LOAD_B = 2, 128
LATENCY_S, HBM_BPS = 600e-9, 3.35e12
# exercises-key.md 4.8: (occupancy, limiter, fraction of HBM)
KEY = {"a_b": (0.25, "shared_memory", 0.269), "c": (0.375, "registers", 0.403)}
TOL = 0.001  # absolute, on the fraction of HBM bandwidth


def occupancy(threads: int, regs: int, smem: int, d: dict) -> dict:
    wpb = math.ceil(threads / d["warp_size"])
    by_warps = d["max_warps_per_sm"] // wpb
    unit = d["reg_alloc_unit_per_warp"]
    regs_per_warp = math.ceil(regs * d["warp_size"] / unit) * unit
    warps_regs_raw = d["regs_per_sm"] // regs_per_warp
    gran = d["warp_alloc_granularity"]
    warps_regs = warps_regs_raw // gran * gran
    by_regs = warps_regs // wpb
    by_smem = d["smem_per_sm_bytes"] // (smem + d["smem_reserved_per_block_bytes"])
    limits = {"warps": by_warps, "registers": by_regs, "shared_memory": by_smem, "blocks": d["max_blocks_per_sm"]}
    blocks = min(limits.values())
    limiter = next(k for k, v in limits.items() if v == blocks)  # Section 4.7 order: warps, registers, smem, blocks
    return {"warps_per_block": wpb, "regs_per_warp": regs_per_warp, "warps_by_regs_raw": warps_regs_raw,
            "warps_by_regs": warps_regs, "limits_blocks": limits, "blocks_per_sm": blocks,
            "active_warps": blocks * wpb, "occupancy": blocks * wpb / d["max_warps_per_sm"], "limiter": limiter,
            "tied_limits": sorted(k for k, v in limits.items() if v == blocks)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    d = json.loads((DATA / "device.json").read_text(encoding="utf-8"))
    need_sm = HBM_BPS * LATENCY_S / d["sm_count"]
    assert round(need_sm) == 15_227, need_sm
    cases = {}
    for name, smem in SMEM_CASES.items():
        o = occupancy(THREADS, REGS, smem, d)
        in_flight = o["active_warps"] * LOADS_PER_WARP * LOAD_B
        frac = min(1.0, in_flight / need_sm)
        k_occ, k_lim, k_frac = KEY[name]
        assert abs(o["occupancy"] - k_occ) < 1e-9 and o["limiter"] == k_lim, o
        assert abs(frac - k_frac) < TOL, frac
        o.update({"smem_per_block_B": smem, "in_flight_per_sm_B": in_flight, "fraction_of_hbm": round(frac, 5),
                  "bandwidth_bound_TBps": round(frac * HBM_BPS / 1e12, 3), "occupancy": round(o["occupancy"], 4)})
        cases[name] = o
    # The 1 KB reservation matters at other sizes: 45 KB per block gives 5 blocks without it, 4 with it.
    no_res = d["smem_per_sm_bytes"] // 46_080
    with_res = d["smem_per_sm_bytes"] // (46_080 + d["smem_reserved_per_block_bytes"])
    assert (no_res, with_res) == (5, 4)
    res = {"exercise": "4.8", "evidence_label": "MODELED",
           "inputs": {"threads_per_block": THREADS, "regs_per_thread": REGS, "smem_cases_B": SMEM_CASES,
                      "loads_in_flight_per_warp": LOADS_PER_WARP, "load_bytes": LOAD_B, "latency_s": LATENCY_S,
                      "hbm_Bps": HBM_BPS, "device": d["name"]},
           "steps": {"needed_in_flight_per_sm_B": round(need_sm, 1),
                     "reservation_example_45KB_blocks": {"without_reservation": no_res, "with_reservation": with_res}},
           "answer": cases,
           "units": {"occupancy": "fraction of 64 warps", "bandwidth": "TB/s", "bytes": "B"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Exercise 4.8 — occupancy and bytes in flight `[MODELED]`", "",
             f"Needed in flight per SM = 3.35 × 10¹² B/s × 600 ns / 132 = {need_sm:,.0f} B.", ""]
    for name, o in cases.items():
        lim = o["limits_blocks"]
        lines += [f"## Case {name} (shared memory {o['smem_per_block_B']:,} B per block)", "",
                  f"- Warps per block = {THREADS} / 32 = {o['warps_per_block']}",
                  f"- Warp limit = ⌊64 / {o['warps_per_block']}⌋ = {lim['warps']} blocks",
                  f"- Register limit: {REGS} × 32 = {o['regs_per_warp']:,} registers per warp; "
                  f"⌊65,536 / {o['regs_per_warp']:,}⌋ = {o['warps_by_regs_raw']} warps → granularity 4 → "
                  f"{o['warps_by_regs']} warps → {lim['registers']} blocks",
                  f"- Shared-memory limit = ⌊233,472 / ({o['smem_per_block_B']:,} + 1,024)⌋ = {lim['shared_memory']} blocks",
                  f"- Block limit = {lim['blocks']}",
                  f"- Resident = {o['blocks_per_sm']} blocks = {o['active_warps']} warps → occupancy "
                  f"{o['occupancy'] * 100:.1f} %, limiter {o['limiter']} (tied: {', '.join(o['tied_limits'])})",
                  f"- In flight = {o['active_warps']} × {LOADS_PER_WARP} × {LOAD_B} B = {o['in_flight_per_sm_B']:,} B → "
                  f"{o['fraction_of_hbm'] * 100:.1f} % of HBM ≈ {o['bandwidth_bound_TBps']:.2f} TB/s upper bound", ""]
    lines.append(f"Reservation check (45 KB = 46,080 B per block): {no_res} blocks without the 1 KB reservation, "
                 f"{with_res} with it.")
    (out / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
