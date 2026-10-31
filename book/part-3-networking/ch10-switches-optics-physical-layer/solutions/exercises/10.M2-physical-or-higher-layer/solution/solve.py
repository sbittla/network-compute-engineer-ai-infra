"""10.M2 — Classify six ports as physical or higher-layer, and compute FEC margins.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (port data [ILLUSTRATIVE], from the prompt table)
Rules: the five discriminating questions of Section 10.8.1, with the thresholds of
lab/data/thresholds.yaml (DR4 receiver minimum, lane imbalance, BER rising factor, flap warning).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
WINDOW_S = 600

# Prompt table (exercises.md 10.M2). Symbol errors: qualitative column.
PORTS = {
    "P1": dict(flaps=0, corr=3.1e7, uncorr=0, fcs=0, sym="low", giants=0, disc=52410, pfc=1.1e6,
               ber=1.2e-7, ber7=1.1e-7, rx=[-1.1, -1.3, -0.9, -1.2]),
    "P2": dict(flaps=0, corr=8.6e9, uncorr=340, fcs=322, sym="high", giants=0, disc=0, pfc=0,
               ber=4.0e-5, ber7=3.6e-5, rx=[-2.0, -2.1, -1.9, -2.0]),
    "P3": dict(flaps=0, corr=5.1e6, uncorr=0, fcs=1870, sym="~0", giants=0, disc=0, pfc=0,
               ber=2.0e-8, ber7=2.1e-8, rx=[-0.8, -0.7, -0.9, -0.8]),
    "P4": dict(flaps=5, corr=2.0e7, uncorr=12, fcs=9, sym="low", giants=0, disc=0, pfc=0,
               ber=8.0e-8, ber7=7.5e-8, rx=[-1.4, -1.5, -1.3, -1.6]),
    "P5": dict(flaps=0, corr=1.9e10, uncorr=0, fcs=0, sym="high", giants=0, disc=0, pfc=0,
               ber=9.0e-5, ber7=2.0e-6, rx=[-6.8, -2.1, -2.0, -2.2]),
    "P6": dict(flaps=0, corr=2.6e6, uncorr=0, fcs=0, sym="~0", giants=12044, disc=0, pfc=0,
               ber=1.0e-8, ber7=1.0e-8, rx=[-0.5, -0.6, -0.4, -0.5]),
}


def p_uncorrectable(ber: float) -> float:
    """Binomial P(>= 16 bad symbols of 544), p = 1 - (1 - b)^10 (Table 10.1 model)."""
    p = 1 - (1 - ber) ** 10
    return sum(math.comb(544, k) * p ** k * (1 - p) ** (544 - k) for k in range(16, 60))


def classify(d: dict, th: dict) -> tuple[str, str]:
    dr4, fec, link = th["optics"]["400G-DR4"], th["fec"], th["link"]
    rx_min, imb = min(d["rx"]), max(d["rx"]) - min(d["rx"])
    rising = d["ber"] >= fec["pre_fec_ber_rising_factor"] * d["ber7"] and d["ber"] >= fec["pre_fec_ber_rising_floor"]
    if d["flaps"] >= link["flap_events_warn"]:
        return "physical", "link flap (FEC/FCS counts are side effects of transitions)"
    if rx_min < dr4["rx_power_low_crit_dbm"] or imb > link["lane_imbalance_db"]:
        return "physical", "one-lane loss: contamination/damage on one MPO fiber" + (", BER rising" if rising else "")
    if d["uncorr"] > 0 and d["fcs"] > 0:
        return "physical", "bursty corruption (uncorrectables at moderate BER, DOM normal)"
    if d["fcs"] > 0 and d["uncorr"] == 0 and d["ber"] < fec["pre_fec_ber_warn"]:
        return "physical-elsewhere", "stomped frames from an upstream cut-through hop"
    if d["giants"] > 0:
        return "higher-layer", "MTU mismatch"
    if d["disc"] > 0 or d["pfc"] / WINDOW_S > th["higher_layer"]["pfc_pause_rate_warn_per_s"]:
        return "higher-layer", "congestion"
    return "healthy", "none"


def solve() -> dict:
    th = yaml.safe_load((DATA / "thresholds.yaml").read_text(encoding="utf-8"))
    limit = th["fec"]["pre_fec_ber_threshold"]
    rows = {}
    for name, d in PORTS.items():
        layer, cause = classify(d, th)
        rows[name] = {
            "layer": layer, "cause": cause,
            "margin_decades": round(math.log10(limit / d["ber"]), 3),
            "ber_ratio_7d": round(d["ber"] / d["ber7"], 2),
            "lane_imbalance_db": round(max(d["rx"]) - min(d["rx"]), 2),
            "pfc_per_s": round(d["pfc"] / WINDOW_S, 1),
            "p_uncorr_random_model": float(f"{p_uncorrectable(d['ber']):.2e}"),
        }
    p5_sibling = sorted(PORTS["P5"]["rx"])[2]       # median of the 3 healthy lanes ~ -2.1
    rows["P5"]["drop_vs_siblings_db"] = round(p5_sibling - min(PORTS["P5"]["rx"]), 2)
    return {"inputs": {"window_s": WINDOW_S, "ber_limit": limit, "ports": PORTS},
            "answer": rows, "units": {"margin": "decades", "rx": "dBm", "pfc": "frames/s"},
            "evidence_label": "[MODELED]"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    r = solve()
    a = r["answer"]
    # Answer key 10.M2: layers per port; margins P2 0.78, P5 0.43 decades (tolerance 0.005); P5 gap 4.7 dB.
    layers = {k: v["layer"] for k, v in a.items()}
    assert layers == {"P1": "higher-layer", "P2": "physical", "P3": "physical-elsewhere",
                      "P4": "physical", "P5": "physical", "P6": "higher-layer"}, layers
    assert abs(a["P2"]["margin_decades"] - 0.78) < 0.005 and abs(a["P5"]["margin_decades"] - 0.43) < 0.005
    assert abs(a["P5"]["drop_vs_siblings_db"] - 4.7) < 0.05 and abs(a["P1"]["pfc_per_s"] - 1833.3) < 0.1
    assert a["P5"]["ber_ratio_7d"] == 45.0
    (out / "result.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# 10.M2 — Physical or higher-layer? `[MODELED]`", "",
          "| Port | Layer | Cause | Margin (decades) | BER now/7 d | Lane imbalance (dB) | P(uncorr) random model |",
          "|---|---|---|---|---|---|---|"]
    for k, v in a.items():
        md.append(f"| {k} | {v['layer']} | {v['cause']} | {v['margin_decades']} | {v['ber_ratio_7d']}x | "
                  f"{v['lane_imbalance_db']} | {v['p_uncorr_random_model']:.1e} |")
    md += ["", "Margins: P2 log10(2.4e-4/4.0e-5) = 0.78; P5 log10(2.4e-4/9.0e-5) = 0.43.",
           f"P1 PFC rate = 1.1e6 / {WINDOW_S} s = {a['P1']['pfc_per_s']} frames/s.",
           "P2's uncorrectables are far above the random-error model at its BER: bursts.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
