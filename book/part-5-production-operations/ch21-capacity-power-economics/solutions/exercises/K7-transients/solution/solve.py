"""K7 - synchronized power swing of a 1,024-GPU job (650 W <-> 400 W per GPU each step).

python solve.py --out DIR.  Inputs from the prompt [ILLUSTRATIVE]; result [MODELED].
Method (manuscript Section 21.7): swing = GPUs × (P_high - P_low); all GPUs move together in a synchronous job.
"""
import argparse
import json
from pathlib import Path

GPUS = 1024
P_HIGH_W = 650
P_LOW_W = 400
GPUS_PER_NODE = 8
LEGACY_RACK_PLANNED_KW = 29.5  # K6(b), for scale
KEY_SWING_KW = 256.0
TOL = 0.5                      # kW


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    swing_kw = GPUS * (P_HIGH_W - P_LOW_W) / 1000
    per_node_kw = GPUS_PER_NODE * (P_HIGH_W - P_LOW_W) / 1000
    high_kw = GPUS * P_HIGH_W / 1000
    low_kw = GPUS * P_LOW_W / 1000
    assert abs(swing_kw - KEY_SWING_KW) <= TOL, swing_kw

    result = {
        "exercise": "K7", "evidence_label": "[MODELED]",
        "inputs": {"gpus": GPUS, "p_high_w": P_HIGH_W, "p_low_w": P_LOW_W},
        "steps": {"gpu_power_high_kw": round(high_kw, 1), "gpu_power_low_kw": round(low_kw, 1),
                  "swing_per_node_kw": round(per_node_kw, 2),
                  "swing_as_fraction_of_high": round(swing_kw / high_kw, 3),
                  "swing_in_legacy_rack_budgets": round(swing_kw / LEGACY_RACK_PLANNED_KW, 1)},
        "answer": {"swing_kw": round(swing_kw, 1)}, "units": {"swing_kw": "kW of GPU power, per step cycle"},
        "tolerance_kw": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# K7 - transients `[MODELED]`", "",
          f"swing = {GPUS} × ({P_HIGH_W} - {P_LOW_W}) W = **{swing_kw:.0f} kW** every step "
          f"({low_kw:.1f} kW <-> {high_kw:.1f} kW of GPU power; {per_node_kw:.1f} kW per node).", "",
          f"For scale: {swing_kw / LEGACY_RACK_PLANNED_KW:.1f} legacy-rack budgets switching on and off together.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
