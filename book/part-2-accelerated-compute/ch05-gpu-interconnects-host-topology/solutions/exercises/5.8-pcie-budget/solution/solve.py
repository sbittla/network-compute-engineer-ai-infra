"""Exercise 5.8: PCIe per-direction bandwidth, 400 Gb/s NIC fit, and uplink load with and without GDR.

Usage: python solve.py --out DIR
Inputs: PCIe Gen4 16 GT/s, Gen5 32 GT/s, 128b/130b encoding (manuscript Section 5.2, Table 5.1);
400 Gb/s NIC = 50 GB/s payload per direction; HX8 switch: 2 GPUs + 2 NICs behind one Gen5 x16 uplink.
Assumptions for (c): both NICs send and receive at line rate; host-staged sends are GPU D2H then NIC
reads host memory, receives are NIC writes to host memory then H2D.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LINKS = {"gen4_x16": (16e9, 16), "gen5_x8": (32e9, 8), "gen5_x16": (32e9, 16)}
ENC = 128 / 130
NIC_GBPS = 400 / 8           # GB/s per direction
ACHIEVABLE = 0.80            # typical achievable fraction of theoretical after TLP overheads [ILLUSTRATIVE]
NICS = 2
KEY = {"gen4_x16": 31.5, "gen5_x8": 31.5, "gen5_x16": 63.0}     # exercises-key.md 5.8 (a)
KEY_PER_NIC_STAGED = 63 / 4                                      # (c) ~ 16 GB/s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    a = {k: round(gt * ENC * lanes / 8 / 1e9, 2) for k, (gt, lanes) in LINKS.items()}
    for k, v in a.items():
        assert abs(v - KEY[k]) < 0.05, (k, v)
    b = {k: {"theoretical_GBps": v, "achievable_GBps": round(v * ACHIEVABLE, 1),
             "carries_400G": v > NIC_GBPS} for k, v in a.items()}
    assert [k for k, v in b.items() if v["carries_400G"]] == ["gen5_x16"]
    uplink = a["gen5_x16"]
    gdr_uplink = 0.0                                        # NIC<->GPU DMA turns around inside the switch
    # Host-staged, upstream direction of the uplink: GPU D2H for sends + NIC writes of received data.
    staged_up_demand = NICS * NIC_GBPS + NICS * NIC_GBPS
    per_nic = uplink / 4                                    # four flows share the upstream direction
    assert staged_up_demand == 200.0 and abs(per_nic - KEY_PER_NIC_STAGED) < 0.1
    res = {"exercise": "5.8", "evidence_label": "MODELED",
           "inputs": {"links": {k: {"GTps": gt, "lanes": l} for k, (gt, l) in LINKS.items()}, "encoding": "128b/130b",
                      "nic_GBps": NIC_GBPS, "nics_per_switch": NICS, "achievable_fraction": ACHIEVABLE},
           "answer": {"a_theoretical_GBps": a, "b_fit": b,
                      "c_gdr_uplink_GBps": gdr_uplink, "c_staged_upstream_demand_GBps": staged_up_demand,
                      "c_uplink_GBps": uplink, "c_staged_per_nic_GBps": round(per_nic, 2)},
           "units": {"bandwidth": "GB/s per direction"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 5.8 — PCIe budget `[MODELED]`", "",
          "| Link | GT/s × 128/130 × lanes / 8 | Theoretical | Achievable (≈ 80 %) | Carries 50 GB/s? |", "|---|---|---|---|---|"]
    for k, (gt, l) in LINKS.items():
        md.append(f"| {k} | {gt / 1e9:.0f} × 128/130 × {l} / 8 | {a[k]:.1f} GB/s | {b[k]['achievable_GBps']:.1f} GB/s | "
                  f"{'yes (tight)' if b[k]['carries_400G'] else 'no'} |")
    md += ["", f"(c) With GDR the uplink carries ≈ {gdr_uplink:.0f} GB/s of payload. Host-staged: upstream demand = "
           f"2 × 50 (D2H for sends) + 2 × 50 (NIC writes of receives) = {staged_up_demand:.0f} GB/s against {uplink:.0f} GB/s, "
           f"so each NIC gets ≈ {uplink:.0f} / 4 = {per_nic:.1f} GB/s per direction."]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
