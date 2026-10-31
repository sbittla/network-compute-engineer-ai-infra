"""13.1 -- NVLink vs NIC bytes per GPU per step for W-TRAIN on ORION. [MODELED]

Usage: python solve.py --out DIR
Inputs: Table 13.1 (manuscript Section 13.1, from Chapter 11 Table 11.2).
"""
import argparse
import json
from pathlib import Path

TP_BYTES = 1.20e12   # tensor parallel, NVLink, per GPU per step (Table 13.1)
DP_BYTES = 7.66e9    # data parallel, NIC (Table 13.1)
PP_BYTES = 2.15e9    # pipeline parallel, NIC (Table 13.1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    nic = DP_BYTES + PP_BYTES
    ratio = TP_BYTES / nic
    ratio_dp = TP_BYTES / DP_BYTES
    # Key (solutions/exercises-key.md 13.1): 9.81 GB, ratio ≈ 123 (≈ 157 vs DP alone); tolerance 1.5x.
    assert abs(nic - 9.81e9) < 1e6
    assert abs(ratio - 123) < 1.5, ratio
    assert abs(ratio_dp - 157) < 1.0, ratio_dp

    result = {
        "inputs": {"tp_bytes": TP_BYTES, "dp_bytes": DP_BYTES, "pp_bytes": PP_BYTES},
        "steps": {"nic_bytes": nic, "ratio_tp_over_nic": round(ratio, 1),
                  "ratio_tp_over_dp": round(ratio_dp, 1)},
        "answer": {"ratio": round(ratio, 1), "cause": "tensor parallelism (TP 8) over NVLink"},
        "units": {"bytes": "B per GPU per step", "ratio": "dimensionless"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# 13.1 result `[MODELED]`\n\n"
          f"- NIC bytes = DP + PP = {DP_BYTES/1e9:.2f} + {PP_BYTES/1e9:.2f} = {nic/1e9:.2f} GB per GPU per step\n"
          f"- NVLink (TP) bytes = {TP_BYTES/1e12:.2f} TB\n"
          f"- Ratio = {TP_BYTES:.3e} / {nic:.3e} = {ratio:.1f}× (vs DP alone {ratio_dp:.1f}×)\n"
          f"- Cause: tensor parallelism's per-layer collectives stay on NVLink.\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
