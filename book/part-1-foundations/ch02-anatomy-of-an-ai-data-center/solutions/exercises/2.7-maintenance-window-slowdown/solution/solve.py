#!/usr/bin/env python3
"""2.7: arithmetic for the maintenance-window slowdown (PSU cording 2A/4B).

Usage: python solve.py --out DIR
Inputs: the prompt's DCGM and PDU evidence [ILLUSTRATIVE]; HX8 PSU and power values from manuscript
Section 2.2 (3.0 kW PSUs, 94 % efficiency, 8.5 kW sustained, 9.59 kW DC peak).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

STEP_BEFORE, STEP_DURING = 17.4, 22.6
CLOCK_PEER, CLOCK_BRAKED = 1755, 1050
FEED_A_KW = {"rack-01": 34.0, "rack-02": 24.1, "rack-03": 24.3, "rack-04": 33.8}
PSU_KW, PSU_EFF, SUSTAINED_AC_KW, DC_PEAK_KW = 3.0, 0.94, 8.5, 9.59
NODES_PER_RACK, AUX_KW = 4, 0.2
PSUS_ON_A = {"braked": 2, "normal": 3}
KEY = {"slowdown": 0.299, "clock_ratio": 0.598, "dc_available_braked": 6.0, "dc_need": 7.99,
       "rack_ac_max_braked": 25.5}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    slowdown = STEP_DURING / STEP_BEFORE - 1
    ratio = CLOCK_BRAKED / CLOCK_PEER
    # single-factor model: fraction f of the step scales with 1/clock
    f = (STEP_DURING / STEP_BEFORE - 1) / (1 / ratio - 1)
    dc_need = SUSTAINED_AC_KW * PSU_EFF
    dc_braked = PSUS_ON_A["braked"] * PSU_KW
    dc_normal = PSUS_ON_A["normal"] * PSU_KW
    node_ac_max_braked = dc_braked / PSU_EFF
    rack_ac_max_braked = NODES_PER_RACK * node_ac_max_braked
    peer_node_ac = (FEED_A_KW["rack-01"] - AUX_KW) / NODES_PER_RACK
    ans = {"slowdown": slowdown, "clock_ratio": ratio, "clock_scaled_fraction_of_step": f,
           "dc_need": dc_need, "dc_available_braked": dc_braked, "dc_available_normal": dc_normal,
           "node_ac_max_braked": node_ac_max_braked, "rack_ac_max_braked": rack_ac_max_braked,
           "peer_node_ac_kw": peer_node_ac, "peer_node_dc_kw": peer_node_ac * PSU_EFF}
    for k, v in KEY.items():
        assert abs(ans[k] - v) <= 0.005 * v, (k, ans[k], v)
    assert dc_braked < dc_need <= dc_normal < DC_PEAK_KW
    assert all(FEED_A_KW[r] <= rack_ac_max_braked for r in ("rack-02", "rack-03"))
    assert ans["peer_node_dc_kw"] <= dc_normal
    assert 0.40 <= f <= 0.50
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] evidence",
              "answer": {k: round(v, 4) for k, v in ans.items()},
              "units": {"power": "kW", "slowdown": "fraction"}}
    md = ["# 2.7 `[MODELED]`", "", f"- slowdown {slowdown:.1%}; braked clock ratio {ratio:.3f}; "
          f"clock-scaled share of step ~ {f:.0%}",
          f"- 2 PSUs on feed A: {dc_braked:.1f} kW DC < sustained need {dc_need:.2f} kW DC -> power brake",
          f"- 3 PSUs on feed A: {dc_normal:.1f} kW DC >= {dc_need:.2f} kW (peers do not brake)",
          f"- braked rack <= {rack_ac_max_braked:.1f} kW AC, measured 24.1 / 24.3 kW (consistent)"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
