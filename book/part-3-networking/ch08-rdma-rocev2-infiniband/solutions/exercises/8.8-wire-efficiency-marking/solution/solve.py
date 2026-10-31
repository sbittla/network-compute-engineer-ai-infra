"""8.8 — RoCEv2 wire efficiency (VLAN-tagged IPv4 at 2,048; untagged IPv6 at 4,096), packet rate, and
what NCCL_IB_TC=26 puts in the IP traffic-class byte.

Usage: python solve.py --out DIR

Overheads from manuscript Section 8.7 (82 B per packet, untagged IPv4 Middle packet, incl. preamble/SFD
and IFG); ORION QoS map from Chapter 7 Table 7.6 / Chapter 8 (DSCP 26 -> TC 3, DSCP 48 -> TC 6). [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LINE_GBPS = 400
BASE_OVERHEAD = {"preamble_sfd": 8, "ethernet": 14, "ipv4": 20, "udp": 8, "bth": 12, "icrc": 4, "fcs": 4, "ifg": 12}
VLAN_B = 4
IPV6_EXTRA_B = 40 - 20
ORION_DSCP_TO_TC = {26: 3, 48: 6}
ECN ={0b00: "Not-ECT", 0b01: "ECT(1)", 0b10: "ECT(0)", 0b11: "CE"}
NCCL_IB_TC = 26
KEY = {"a_gbps": 383.9, "b_gbps": 390.3, "c_mpps": 11.91, "dscp": 6, "ecn": "ECT(0)", "correct_tc": 106}


def ceiling(payload: int, overhead: int) -> tuple[float, float]:
    eff = payload / (payload + overhead)
    return eff, LINE_GBPS * eff


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    base = sum(BASE_OVERHEAD.values())
    oh_a = base + VLAN_B
    oh_b = base + IPV6_EXTRA_B
    eff_a, gbps_a = ceiling(2048, oh_a)
    eff_b, gbps_b = ceiling(4096, oh_b)
    pps_b = LINE_GBPS * 1e9 / ((4096 + oh_b) * 8)
    dscp, ecn_bits = NCCL_IB_TC >> 2, NCCL_IB_TC & 0b11
    tc_class = ORION_DSCP_TO_TC.get(dscp, 0)
    correct = 26 << 2 | 0b10

    assert base == 82 and oh_a == 86 and oh_b == 102
    assert abs(gbps_a - KEY["a_gbps"]) < 0.05 and abs(gbps_b - KEY["b_gbps"]) < 0.05
    assert abs(pps_b / 1e6 - KEY["c_mpps"]) < 0.005
    assert dscp == KEY["dscp"] and ECN[ecn_bits] == KEY["ecn"] and tc_class == 0 and correct == KEY["correct_tc"]

    result = {
        "exercise": "8.8", "evidence_label": "[MODELED]",
        "inputs": {"line_gbps": LINE_GBPS, "base_overhead_b": BASE_OVERHEAD, "vlan_b": VLAN_B,
                   "ipv6_extra_b": IPV6_EXTRA_B, "nccl_ib_tc": NCCL_IB_TC},
        "steps": {"a_overhead_b": oh_a, "a_efficiency": round(eff_a, 4), "b_overhead_b": oh_b,
                  "b_efficiency": round(eff_b, 4), "tc_byte_binary": format(NCCL_IB_TC, "08b")},
        "answer": {"a_ceiling_gbps": round(gbps_a, 1), "b_ceiling_gbps": round(gbps_b, 1),
                   "c_packets_per_s_millions": round(pps_b / 1e6, 2), "d_dscp": dscp, "d_ecn": ECN[ecn_bits],
                   "d_orion_traffic_class": tc_class, "d_correct_nccl_ib_tc": correct},
        "units": "Gb/s, M packets/s", "tolerance": "±0.05 Gb/s, ±0.005 Mpps, exact for bit fields",
    }
    md = f"""# 8.8 — result `[MODELED]`

- (a) overhead {base} + 4 VLAN = {oh_a} B; 2,048 / {2048 + oh_a:,} = {eff_a:.4f} → **{gbps_a:.1f} Gb/s**
- (b) overhead {base} + 20 IPv6 = {oh_b} B; 4,096 / {4096 + oh_b:,} = {eff_b:.4f} → **{gbps_b:.1f} Gb/s**
- (c) 400 × 10⁹ / ({4096 + oh_b:,} × 8) = **{pps_b / 1e6:.2f} M packets/s**
- (d) `NCCL_IB_TC={NCCL_IB_TC}` = 0b{NCCL_IB_TC:08b} → DSCP **{dscp}**, ECN **{ECN[ecn_bits]}** → ORION TC {tc_class} (default lossy); correct value 26 × 4 + 2 = **{correct}**
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("8.8 ok")


if __name__ == "__main__":
    main()
