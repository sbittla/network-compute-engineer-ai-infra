#!/usr/bin/env python3
"""Chapter 1 hands-on lab: apply the ceiling model (Equation block 1.1) to the raw outputs.

    python ch01_analyze.py results/<run-id>      # writes summary.json and report.md in that directory

Peaks come from vendor-class constants scaled by the SM clock *measured during each segment*
(the "clock-adjusted peak"): a laptop GPU's clock moves with power and temperature, so dividing by the
spec-sheet maximum understates how close a kernel came to what the chip could do at that moment.
Override the constants for an unlisted GPU with CH01_FLOP_PER_CLK_SM and CH01_BUS_BITS.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from pathlib import Path

from ch01_telemetry import read_csv, reasons, stats, window

# name substring -> (dense BF16 tensor FLOP per clock per SM with FP32 accumulate, memory bus width in bits)
# [VENDOR-SPEC]: derived from NVIDIA's published peak TFLOP/s divided by (SM count x boost clock).
# GeForce parts run FP32-accumulate tensor math at half the FP16-accumulate rate; PyTorch uses FP32
# accumulation for BF16 matmuls, so that is the relevant peak.
SPECS = {
    "RTX 4060 Laptop": (512, 128), "RTX 4070 Laptop": (512, 128), "RTX 4080 Laptop": (512, 192),
    "RTX 4090 Laptop": (512, 256), "RTX 4060": (512, 128), "RTX 4070": (512, 192), "RTX 4080": (512, 256),
    "RTX 4090": (512, 384), "RTX 3060": (512, 192), "RTX 3070": (512, 256), "RTX 3080": (512, 320),
    "RTX 3090": (512, 384), "L4": (1024, 192), "A10": (1024, 384), "A100": (2048, 5120),
    "H100": (4096, 5120),
}
GDDR_DATA_RATE_PER_CLOCK = 2  # nvidia-smi's memory clock x 2 = per-pin data rate (GDDR6/6X and HBM alike)
ORION = {"peak_bf16_flops": 989e12, "hbm_bytes_per_s": 3.35e12, "machine_balance": 295, "w_train_mfu": 0.40}


def band(f: float) -> str:
    if f > 1.0:
        return "impossible (> 1.0): fix the data"
    if f >= 0.9:
        return "recheck (0.9-1.0): suspiciously close to peak"
    if f >= 0.25:
        return "meaningful (0.25-0.9): gap is ordinary inefficiency"
    return "latency or overhead (< 0.25): no throughput ceiling explains the time"


def main() -> None:
    run = Path(sys.argv[1])
    inv = json.loads((run / "gpu_inventory.json").read_text())
    seg = json.loads((run / "segments.json").read_text())
    tel = read_csv(run / "ch01_telemetry.csv")
    gemm = json.loads((run / "ceiling_gemm.json").read_text())
    copy = json.loads((run / "ceiling_copy.json").read_text())
    model = json.loads((run / "train_model.json").read_text())
    with open(run / "gemv_sweep.csv") as fh:
        gemv = list(csv.DictReader(fh))
    with open(run / "train_steps.csv") as fh:
        steps = list(csv.DictReader(fh))

    spec = next((v for k, v in SPECS.items() if k in inv["name"]), None)
    fpc = float(os.environ.get("CH01_FLOP_PER_CLK_SM", spec[0] if spec else 0))
    bus = float(os.environ.get("CH01_BUS_BITS", spec[1] if spec else 0))
    sms = inv["sm_count"]
    fields = inv["nvidia_smi_fields"]
    max_sm = float(fields["clocks.max.sm"].split()[0])
    max_mem = float(fields["clocks.max.mem"].split()[0])

    def seg_tel(name: str) -> dict:
        rows = window(tel, *seg[name])
        mask = [r.get("clocks_event_reasons.active") for r in rows]
        cap = [m for m in mask if isinstance(m, int)]
        return {
            "samples": len(rows),
            "sm_clock_mhz": stats([r.get("clocks.sm") for r in rows]),
            "mem_clock_mhz": stats([r.get("clocks.mem") for r in rows]),
            "power_w": stats([r.get("power.draw.instant", r.get("power.draw")) for r in rows]),
            "temp_c": stats([r.get("temperature.gpu") for r in rows]),
            "sw_power_cap_fraction": sum(1 for m in cap if m & 0x4) / len(cap) if cap else None,
            "sw_thermal_fraction": sum(1 for m in cap if m & 0x20) / len(cap) if cap else None,
            "reasons_seen": sorted({x for m in cap for x in reasons(m)}),
        }

    def peak_at(clock_mhz: float) -> float:
        return sms * fpc * clock_mhz * 1e6

    def bw_at(mem_mhz: float) -> float:
        return bus / 8 * GDDR_DATA_RATE_PER_CLOCK * mem_mhz * 1e6

    S: dict = {"gpu": inv["name"], "sm_count": sms, "flop_per_clk_per_sm_bf16": fpc, "bus_bits": bus,
               "spec_source": "table [VENDOR-SPEC, 2026-10]" if spec and "CH01_FLOP_PER_CLK_SM" not in os.environ else "override/unknown",
               "max_sm_clock_mhz": max_sm, "max_mem_clock_mhz": max_mem,
               "peak_bf16_flops_at_max_clock": peak_at(max_sm), "theoretical_bw_bytes_per_s": bw_at(max_mem)}
    S["machine_balance_at_max_clock"] = S["peak_bf16_flops_at_max_clock"] / S["theoretical_bw_bytes_per_s"]
    S["idle"] = seg_tel("idle")

    # Step 2: empirical ceilings
    tg = seg_tel("gemm")
    clk = tg["sm_clock_mhz"]["mean"]
    S["gemm"] = {"achieved_flops": gemm["achieved_flops"], "telemetry": tg, "clock_adjusted_peak": peak_at(clk),
                 "fraction_of_clock_adjusted_peak": gemm["achieved_flops"] / peak_at(clk),
                 "fraction_of_max_clock_peak": gemm["achieved_flops"] / peak_at(max_sm)}
    tc = seg_tel("copy")
    bw = bw_at(tc["mem_clock_mhz"]["mean"])
    S["copy"] = {"achieved_bytes_per_s": copy["achieved_bytes_per_s"], "telemetry": tc, "theoretical_bw": bw,
                 "fraction_of_theoretical": copy["achieved_bytes_per_s"] / bw}
    S["machine_balance_measured_clock"] = peak_at(clk) / bw
    S["machine_balance_empirical"] = gemm["achieved_flops"] / copy["achieved_bytes_per_s"]

    # Step 3: GEMV -> GEMM sweep
    sweep = []
    for r in gemv:
        b = int(r["batch"]); it = int(r["iterations"]); el = float(r["elapsed_s"])
        fl, by = float(r["flop_per_iter"]), float(r["bytes_per_iter_min"])
        t = seg_tel(f"gemv_B{b}")
        c = t["sm_clock_mhz"].get("mean", clk)
        obs = el / it
        tcomp, tmem = fl / peak_at(c), by / bw
        sweep.append({"batch": b, "intensity_flop_per_byte": fl / by, "observed_s": obs,
                      "t_compute_s": tcomp, "t_memory_s": tmem,
                      "dominant": "compute" if tcomp > tmem else "memory",
                      "ceiling_fraction": max(tcomp, tmem) / obs,
                      "achieved_flops": fl / obs, "achieved_bytes_per_s": by / obs, "sm_clock_mhz": c})
    for s in sweep:
        s["band"] = band(s["ceiling_fraction"])
    S["gemv_sweep"] = sweep

    # Step 4: training step
    flop_tok = model["flop_per_token_6N"]
    attn_tok = model["flop_per_token_attention"]
    seq = model["config"]["seq"]
    train = []
    for b in sorted({int(r["batch"]) for r in steps}):
        ts = [float(r["step_s"]) for r in steps if int(r["batch"]) == b]
        med = statistics.median(ts)
        t = seg_tel(f"train_B{b}")
        c = t["sm_clock_mhz"]["mean"]
        tok = b * seq
        achieved = flop_tok * tok / med
        min_bytes = 36 * model["params_total"] + 2 * model["saved_activation_bytes"][str(b)]
        tcomp = flop_tok * tok / peak_at(c)
        tmem = min_bytes / bw
        peak_mem = max((int(r["peak_mem_bytes"]) for r in steps if int(r["batch"]) == b and r["peak_mem_bytes"]), default=0)
        train.append({
            "batch": b, "tokens_per_step": tok, "steps_timed": len(ts), "median_step_s": med,
            "p95_step_s": sorted(ts)[int(0.95 * (len(ts) - 1))],
            "tokens_per_s": tok / med, "achieved_flops_6N": achieved,
            "achieved_flops_with_attention": (flop_tok + attn_tok) * tok / med,
            "sm_clock_mhz": c, "clock_adjusted_peak": peak_at(c),
            "mfu_clock_adjusted": achieved / peak_at(c), "mfu_at_max_clock": achieved / peak_at(max_sm),
            "mfu_with_attention_clock_adjusted": (flop_tok + attn_tok) * tok / med / peak_at(c),
            "fraction_of_empirical_gemm": achieved / gemm["achieved_flops"],
            "modeled_min_bytes": min_bytes, "intensity_flop_per_byte": flop_tok * tok / min_bytes,
            "t_compute_s": tcomp, "t_memory_s": tmem, "dominant": "compute" if tcomp > tmem else "memory",
            "ceiling_fraction": max(tcomp, tmem) / med, "peak_mem_bytes": peak_mem, "telemetry": t,
        })
    for x in train:
        x["band"] = band(x["ceiling_fraction"])
    S["train"] = train
    big, mid = train[-1], train[-2]
    # Table 1.7's confirming evidence: does step time scale with FLOPs (time per token flat)?
    tpt_ratio = (big["median_step_s"] / big["tokens_per_step"]) / (mid["median_step_s"] / mid["tokens_per_step"])
    S["scaling"] = {"time_per_token_ratio_largest_vs_next": tpt_ratio,
                    "flop_ratio": big["tokens_per_step"] / mid["tokens_per_step"],
                    "step_time_ratio": big["median_step_s"] / mid["median_step_s"],
                    "scales_with_flops": 0.8 <= tpt_ratio <= 1.1}
    verdict = big["dominant"] if big["band"].startswith("meaningful") or big["band"].startswith("recheck") else "overhead"
    S["verdict"] = {
        "batch": big["batch"], "class": verdict, "ceiling_fraction": big["ceiling_fraction"],
        "confirmed_by_scaling": S["scaling"]["scales_with_flops"] and verdict == "compute",
        "smallest_batch_band": train[0]["band"],
    }
    S["orion_comparison"] = {
        "orion_machine_balance": ORION["machine_balance"], "this_gpu_machine_balance": S["machine_balance_measured_clock"],
        "orion_w_train_mfu": ORION["w_train_mfu"], "this_gpu_mfu": big["mfu_clock_adjusted"],
        "orion_peak_over_this_gpu_peak": ORION["peak_bf16_flops"] / peak_at(clk),
    }
    (run / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (run / "report.md").write_text(report(S))
    print((run / "report.md").read_text())


def report(S: dict) -> str:
    T = lambda f: f"{f / 1e12:.1f} TFLOP/s"  # noqa: E731
    G = lambda b: f"{b / 1e9:.0f} GB/s"  # noqa: E731
    g, c = S["gemm"], S["copy"]
    L = [f"# Chapter 1 hands-on: {S['gpu']} against its ceilings", "",
         "Every number below is `[MEASURED]` on this machine by `ch01_ceilings.py` unless labelled "
         "`[VENDOR-SPEC, 2026-10]` (peak constants) or `[MODELED]` (derived through the ceiling model).", "",
         "## Step 1: inventory", "",
         f"- {S['sm_count']} SMs, {S['flop_per_clk_per_sm_bf16']:.0f} BF16 FLOP/clock/SM `[VENDOR-SPEC, 2026-10]`, "
         f"{S['bus_bits']:.0f}-bit memory bus `[VENDOR-SPEC, 2026-10]`; maximum SM clock {S['max_sm_clock_mhz']:.0f} MHz `[MEASURED]` (nvidia-smi).",
         f"- Peak at maximum clock {T(S['peak_bf16_flops_at_max_clock'])}; theoretical bandwidth "
         f"{G(S['theoretical_bw_bytes_per_s'])}; machine balance {S['machine_balance_at_max_clock']:.0f} FLOP/B `[MODELED]` "
         f"(ORION HX8: 295 FLOP/B).",
         f"- Idle: {S['idle']['power_w']['median']:.1f} W, SM clock {S['idle']['sm_clock_mhz']['median']:.0f} MHz `[MEASURED]`.", "",
         "## Step 2: empirical ceilings", "",
         f"- BF16 GEMM 8192³: {T(g['achieved_flops'])} `[MEASURED]` at a mean SM clock of "
         f"{g['telemetry']['sm_clock_mhz']['mean']:.0f} MHz and {g['telemetry']['power_w']['median']:.1f} W "
         f"(power cap active in {100 * (g['telemetry']['sw_power_cap_fraction'] or 0):.0f} % of samples) `[MEASURED]`.",
         f"- Clock-adjusted peak {T(g['clock_adjusted_peak'])} `[MODELED]`: the GEMM reaches "
         f"{g['fraction_of_clock_adjusted_peak']:.2f} of it, but only {g['fraction_of_max_clock_peak']:.2f} of the max-clock peak.",
         f"- Device copy: {G(c['achieved_bytes_per_s'])} `[MEASURED]` = {c['fraction_of_theoretical']:.2f} of "
         f"{G(c['theoretical_bw'])} theoretical at SM clock {c['telemetry']['sm_clock_mhz']['mean']:.0f} MHz, "
         f"{c['telemetry']['power_w']['median']:.1f} W.",
         f"- Machine balance at the GEMM's clock {S['machine_balance_measured_clock']:.0f} FLOP/B `[MODELED]`; "
         f"empirical (GEMM ÷ copy) {S['machine_balance_empirical']:.0f} FLOP/B `[MEASURED]`.", "",
         "## Step 3: from decode-like to GEMM-like (Y = X·W, W = 8192 × 8192 BF16)", "",
         "| Batch B | Intensity (FLOP/B) | Observed (µs) | T_compute (µs) | T_memory (µs) | Dominant | Ceiling fraction | Achieved |",
         "|---:|---:|---:|---:|---:|---|---:|---|"]
    for s in S["gemv_sweep"]:
        ach = G(s["achieved_bytes_per_s"]) if s["dominant"] == "memory" else T(s["achieved_flops"])
        L.append(f"| {s['batch']} | {s['intensity_flop_per_byte']:.1f} | {s['observed_s'] * 1e6:.1f} | "
                 f"{s['t_compute_s'] * 1e6:.1f} | {s['t_memory_s'] * 1e6:.1f} | {s['dominant']} | "
                 f"{s['ceiling_fraction']:.2f} | {ach} |")
    L += ["", "Observed times and achieved rates `[MEASURED]`; lower bounds `[MODELED]` from the clock-adjusted peak.", "",
          "## Step 4: a training step (8-layer, d = 768 decoder, sequence 512, BF16 autocast, fused AdamW)", "",
          "| Batch | Tokens/step | Median step (ms) | Tokens/s | Achieved (6N) | SM clock (MHz) | MFU (clock-adjusted) | MFU (max clock) | T_compute (ms) | T_memory (ms) | Dominant | Ceiling fraction | Band |",
          "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|---|"]
    for x in S["train"]:
        L.append(f"| {x['batch']} | {x['tokens_per_step']} | {x['median_step_s'] * 1e3:.1f} | {x['tokens_per_s']:,.0f} | "
                 f"{T(x['achieved_flops_6N'])} | {x['sm_clock_mhz']:.0f} | {x['mfu_clock_adjusted']:.2f} | "
                 f"{x['mfu_at_max_clock']:.2f} | {x['t_compute_s'] * 1e3:.1f} | {x['t_memory_s'] * 1e3:.1f} | "
                 f"{x['dominant']} | {x['ceiling_fraction']:.2f} | {x['band'].split(' (')[0]} |")
    v, sc = S["verdict"], S["scaling"]
    L += ["", "Step time, tokens/s, clocks `[MEASURED]`; FLOP counts, MFU, lower bounds `[MODELED]` "
          "(6N FLOPs per token; minimum bytes = 36 B per parameter plus twice the measured bytes saved for backward).", "",
          "## Verdict", "",
          f"- Batch {v['batch']}: **{v['class']}-bound**, ceiling fraction {v['ceiling_fraction']:.2f} `[MODELED]`.",
          f"- Confirming evidence (Table 1.7): tokens ×{sc['flop_ratio']:.0f} → step time ×{sc['step_time_ratio']:.2f}; "
          f"time per token ratio {sc['time_per_token_ratio_largest_vs_next']:.2f} `[MEASURED]` "
          f"({'scales with FLOPs' if sc['scales_with_flops'] else 'does not scale with FLOPs'}).",
          f"- Smallest batch: {v['smallest_batch_band']}.",
          f"- ORION W-TRAIN runs at MFU 0.40 against a 295 FLOP/B machine; this GPU's best step reached "
          f"{S['orion_comparison']['this_gpu_mfu']:.2f} against {S['orion_comparison']['this_gpu_machine_balance']:.0f} FLOP/B. "
          "Ratios and mechanisms carry over; absolute values do not.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
