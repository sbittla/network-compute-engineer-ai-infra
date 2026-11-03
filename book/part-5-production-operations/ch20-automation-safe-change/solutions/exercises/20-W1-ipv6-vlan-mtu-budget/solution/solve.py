"""Exercise 20-W1 — MTU budget for an IPv6, 802.1Q-tagged ORION variant.

    python solve.py --out DIR

All inputs are the prompt's stated parameters (exercises.md, Section 20.2) and the ORION policy of
manuscript Section 20.5.1. Results are [MODELED] from header sizes. Asserts the values in
solutions/exercises-key.md (Section 20.2).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# --- inputs from the prompt (exercises.md 20-W1) -------------------------------------------------
LEAF_PORT_MTU = 9_100          # B, full frame incl. Ethernet header, 802.1Q tag and FCS (vendor-documented)
ETH_HDR, VLAN_TAG, FCS = 14, 4, 4
IPV4_HDR, IPV6_HDR = 20, 40
IPV4_HEADER_BUDGET = 64        # B, Section 20.5.1 budget for IPv4 + UDP + BTH + ext. headers + ICRC
RDMA_PAYLOAD = 4_096           # B
ORION_HOST_MTU = 9_000         # B
LINE_RATE_GBPS = 400           # Gb/s
WIRE = {"preamble_sfd": 8, "ethernet": 14, "dot1q": 4, "ipv6": 40, "udp": 8, "bth": 12, "icrc": 4,
        "fcs": 4, "ifg": 12}   # per-packet wire overhead listed in the prompt
RDMA_MTUS = (1_024, 4_096)
ALLOWED_RDMA_MTU = (256, 512, 1_024, 2_048, 4_096)


def pol_mtu_fabric(node: dict, leaves: list[dict], pol: dict) -> bool:
    """POL-MTU-FABRIC: host frame fits through the smallest leaf port on every rail."""
    return node["host_mtu"] + pol["l2_overhead_bytes"] <= min(l["port_mtu"] for l in leaves)


def pol_mtu_rdma(node: dict, pol: dict) -> bool:
    """POL-MTU-RDMA: RDMA path MTU is an IB value and fits in the IP MTU with the header budget."""
    return (node["rdma_path_mtu"] in pol["allowed_rdma_path_mtu"]
            and node["rdma_path_mtu"] + pol["roce_header_budget_bytes"] <= node["host_mtu"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    # (a) full-frame switch MTU: frame = IP MTU + Ethernet + 802.1Q + FCS
    l2_overhead = ETH_HDR + VLAN_TAG + FCS
    max_ip_mtu = LEAF_PORT_MTU - l2_overhead

    # (b) IPv6 header is 20 B larger than IPv4; the extended-header allowance stays the same
    ipv6_budget = IPV4_HEADER_BUDGET + (IPV6_HDR - IPV4_HDR)
    min_ip_mtu = RDMA_PAYLOAD + ipv6_budget
    fixed_ipv6 = IPV6_HDR + WIRE["udp"] + WIRE["bth"] + WIRE["icrc"]
    ext_allowance = ipv6_budget - fixed_ipv6

    # (c) both inequalities for host MTU 9,000
    fabric_ok = ORION_HOST_MTU + l2_overhead <= LEAF_PORT_MTU
    rdma_ok = min_ip_mtu <= ORION_HOST_MTU

    # (d) wire efficiency and packet rate
    overhead = sum(WIRE.values())
    rate_Bps = LINE_RATE_GBPS * 1e9 / 8
    rows = []
    for mtu in RDMA_MTUS:
        wire = mtu + overhead
        rows.append({"rdma_mtu_B": mtu, "wire_B": wire, "efficiency_pct": round(100 * mtu / wire, 2),
                     "packets_per_s_M": round(rate_Bps / wire / 1e6, 2)})
    gain_pct = round(100 * ((RDMA_MTUS[1] / (RDMA_MTUS[1] + overhead)) /
                            (RDMA_MTUS[0] / (RDMA_MTUS[0] + overhead)) - 1), 2)

    # (e) the two rules, evaluated with policy data for this variant
    pol = {"l2_overhead_bytes": l2_overhead, "roce_header_budget_bytes": ipv6_budget,
           "allowed_rdma_path_mtu": list(ALLOWED_RDMA_MTU)}
    leaves = [{"name": f"leaf-r{i}", "port_mtu": LEAF_PORT_MTU} for i in range(8)]
    good = {"host_mtu": 9_000, "rdma_path_mtu": 4_096}
    too_big = {"host_mtu": 9_100, "rdma_path_mtu": 4_096}       # 9,122 > 9,100
    too_small = {"host_mtu": 4_160, "rdma_path_mtu": 4_096}     # IPv4 budget is not enough on IPv6
    rule_tests = {
        "good_fabric": pol_mtu_fabric(good, leaves, pol), "good_rdma": pol_mtu_rdma(good, pol),
        "host_9100_fabric": pol_mtu_fabric(too_big, leaves, pol),
        "host_4160_rdma": pol_mtu_rdma(too_small, pol),
    }

    # --- assertions against solutions/exercises-key.md (20-W1) ------------------------------------
    assert max_ip_mtu == 9_078
    assert ipv6_budget == 84 and min_ip_mtu == 4_180 and ext_allowance == 20
    assert fabric_ok and rdma_ok
    assert overhead == 106
    assert abs(rows[0]["efficiency_pct"] - 90.6) <= 0.05 and abs(rows[1]["efficiency_pct"] - 97.5) <= 0.05
    assert abs(rows[0]["packets_per_s_M"] - 44.2) <= 0.06 and abs(rows[1]["packets_per_s_M"] - 11.9) <= 0.06
    assert abs(gain_pct - 7.6) <= 0.1
    assert rule_tests == {"good_fabric": True, "good_rdma": True, "host_9100_fabric": False, "host_4160_rdma": False}

    result = {
        "exercise": "20-W1", "evidence_label": "[MODELED]", "units": "bytes, percent, million packets/s",
        "inputs": {"leaf_port_mtu_B": LEAF_PORT_MTU, "l2": {"ethernet": ETH_HDR, "dot1q": VLAN_TAG, "fcs": FCS},
                   "ipv4_header_budget_B": IPV4_HEADER_BUDGET, "rdma_payload_B": RDMA_PAYLOAD,
                   "host_mtu_B": ORION_HOST_MTU, "line_rate_Gbps": LINE_RATE_GBPS, "wire_overhead_B": WIRE},
        "steps": {"a_l2_overhead_B": l2_overhead, "b_fixed_ipv6_headers_B": fixed_ipv6,
                  "b_extended_header_allowance_B": ext_allowance, "c_fabric_frame_B": ORION_HOST_MTU + l2_overhead,
                  "d_overhead_B": overhead, "d_line_rate_Bps": rate_Bps, "e_rule_tests": rule_tests,
                  "e_policy_data": pol},
        "answer": {"a_max_host_ip_mtu_B": max_ip_mtu, "b_ipv6_header_budget_B": ipv6_budget,
                   "b_min_host_ip_mtu_B": min_ip_mtu, "c_host_mtu_9000_valid": fabric_ok and rdma_ok,
                   "d_rows": rows, "d_efficiency_gain_pct": gain_pct},
        "tolerance": "integers exact; efficiency +/-0.05 pp; packet rate +/-0.06 M/s; gain +/-0.1 pp",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = [
        "# Exercise 20-W1 — result `[MODELED]`", "",
        f"a. Frame = IP MTU + {ETH_HDR} + {VLAN_TAG} + {FCS} = IP MTU + {l2_overhead}. "
        f"Max IP MTU = {LEAF_PORT_MTU:,} − {l2_overhead} = **{max_ip_mtu:,} B**.",
        f"b. Budget = {IPV4_HEADER_BUDGET} + ({IPV6_HDR} − {IPV4_HDR}) = {ipv6_budget} B "
        f"(fixed {fixed_ipv6} B + {ext_allowance} B extended). Min IP MTU = {RDMA_PAYLOAD:,} + {ipv6_budget} = **{min_ip_mtu:,} B**.",
        f"c. {ORION_HOST_MTU:,} + {l2_overhead} = {ORION_HOST_MTU + l2_overhead:,} ≤ {LEAF_PORT_MTU:,} and "
        f"{min_ip_mtu:,} ≤ {ORION_HOST_MTU:,}: **valid**.",
        f"d. Overhead = {overhead} B per packet; line rate {rate_Bps / 1e9:.0f} × 10⁹ B/s.", "",
        "| RDMA MTU (B) | Wire bytes | Efficiency | Packets/s |", "|---|---|---|---|",
    ]
    md += [f"| {r['rdma_mtu_B']:,} | {r['wire_B']:,} | {r['efficiency_pct']:.2f} % | {r['packets_per_s_M']:.2f} M |"
           for r in rows]
    md += ["", f"Efficiency gain 4,096 vs 1,024: {gain_pct:.2f} %.", "",
           f"e. Rules evaluated with policy data {pol['l2_overhead_bytes']} B / {pol['roce_header_budget_bytes']} B: {rule_tests}.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
