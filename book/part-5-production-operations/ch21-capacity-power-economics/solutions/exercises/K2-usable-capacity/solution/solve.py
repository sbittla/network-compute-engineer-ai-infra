"""K2 - usable GPUs of an energized 1,024-GPU cluster.  python solve.py --out DIR

Inputs are the prompt's stated reserves [ILLUSTRATIVE]; result [MODELED].
Method (manuscript Section 21.2): usable = energized × (1 - maintenance) × (1 - repair/spares) × (1 - fragmentation).
"""
import argparse
import json
import math
from pathlib import Path

ENERGIZED_GPUS = 1024          # prompt
MAINTENANCE = 0.04             # prompt
REPAIR_SPARES = 0.05           # prompt
FRAGMENTATION = 0.08           # prompt
KEY_USABLE = 859               # solutions/exercises-key.md K2
TOL = 1.0                      # GPUs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    factor = (1 - MAINTENANCE) * (1 - REPAIR_SPARES) * (1 - FRAGMENTATION)
    usable = ENERGIZED_GPUS * factor
    additive_wrong = ENERGIZED_GPUS * (1 - MAINTENANCE - REPAIR_SPARES - FRAGMENTATION)
    usable_whole = math.floor(usable)
    assert abs(usable - KEY_USABLE) <= TOL, usable
    assert usable_whole == KEY_USABLE

    result = {
        "exercise": "K2", "evidence_label": "[MODELED]",
        "inputs": {"energized_gpus": ENERGIZED_GPUS, "maintenance": MAINTENANCE, "repair_spares": REPAIR_SPARES,
                   "fragmentation": FRAGMENTATION},
        "steps": {"usable_factor": round(factor, 4), "usable_gpus_exact": round(usable, 2),
                  "additive_shortcut_gpus_wrong": round(additive_wrong, 2)},
        "answer": {"usable_gpus": usable_whole}, "units": {"usable_gpus": "GPUs"},
        "tolerance": {"usable_gpus": TOL},
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# K2 - usable capacity `[MODELED]`", "",
        "usable = energized × (1 - maintenance) × (1 - repair) × (1 - fragmentation)",
        f"= {ENERGIZED_GPUS} × {1 - MAINTENANCE:.2f} × {1 - REPAIR_SPARES:.2f} × {1 - FRAGMENTATION:.2f}",
        f"= {ENERGIZED_GPUS} × {factor:.4f} = {usable:.2f} -> **{usable_whole} usable GPUs**", "",
        f"(Subtracting the percentages instead gives {additive_wrong:.1f}: the reserves compound, they do not add.)", "",
    ]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
