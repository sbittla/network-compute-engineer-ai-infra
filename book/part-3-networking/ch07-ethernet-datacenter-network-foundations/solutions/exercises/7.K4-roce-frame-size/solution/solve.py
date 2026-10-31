"""7.K4 — RoCEv2 RDMA WRITE first-packet frame size and the RDMA active MTU at netdev MTU 1500.

Usage: python solve.py --out DIR

Header sizes from manuscript Section 7.4 (Figure 7.2). [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADERS_B = {  # Figure 7.2, RoCEv2 over IPv4, untagged, RDMA WRITE first packet
    "ethernet": 14, "ipv4": 20, "udp": 8, "bth": 12, "reth": 16, "icrc": 4, "fcs": 4,
}
PAYLOAD_B = 4096
IB_MTUS = (256, 512, 1024, 2048, 4096)   # InfiniBand path MTU set
NETDEV_MTU_SMALL = 1500
KEY = {"frame_b": 4174, "ip_packet_b": 4156, "frame_no_reth_b": 4158, "active_mtu_1500": 1024}


def rdma_mtu_for(netdev_mtu: int, with_reth: bool = True) -> int:
    """Largest IB MTU whose RoCEv2 IP packet (IP + UDP + BTH [+ RETH] + payload + ICRC) fits the IP MTU."""
    overhead = HEADERS_B["ipv4"] + HEADERS_B["udp"] + HEADERS_B["bth"] + HEADERS_B["icrc"]
    overhead += HEADERS_B["reth"] if with_reth else 0
    return max(m for m in IB_MTUS if m + overhead <= netdev_mtu)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    frame = sum(HEADERS_B.values()) + PAYLOAD_B
    ip_packet = frame - HEADERS_B["ethernet"] - HEADERS_B["fcs"]
    frame_no_reth = frame - HEADERS_B["reth"]
    space_1500 = NETDEV_MTU_SMALL - HEADERS_B["ipv4"] - HEADERS_B["udp"] - HEADERS_B["bth"] - HEADERS_B["icrc"]
    active = rdma_mtu_for(NETDEV_MTU_SMALL)
    min_ip_mtu_for_4096 = ip_packet  # IP MTU must hold the 4,156-byte first packet

    assert (frame, ip_packet, frame_no_reth) == (KEY["frame_b"], KEY["ip_packet_b"], KEY["frame_no_reth_b"])
    assert active == KEY["active_mtu_1500"] and rdma_mtu_for(9000) == 4096   # exact (tolerance 0)

    result = {
        "exercise": "7.K4", "evidence_label": "[MODELED]",
        "inputs": {"headers_b": HEADERS_B, "payload_b": PAYLOAD_B, "netdev_mtu_b": NETDEV_MTU_SMALL},
        "steps": {"ip_packet_b": ip_packet, "frame_without_reth_b": frame_no_reth,
                  "payload_space_at_1500_without_reth_b": space_1500, "min_ip_mtu_for_4096_b": min_ip_mtu_for_4096},
        "answer": {"frame_on_wire_incl_fcs_b": frame, "active_mtu_at_netdev_1500": active,
                   "active_mtu_at_netdev_9000": rdma_mtu_for(9000)},
        "units": "bytes", "tolerance": "exact",
    }
    terms = " + ".join(f"{k} {v}" for k, v in HEADERS_B.items())
    md = f"""# 7.K4 — result `[MODELED]`

- Frame = {terms} + payload {PAYLOAD_B:,} = **{frame:,} B** (IP packet {ip_packet:,} B; {frame_no_reth:,} B without RETH)
- Netdev MTU 1500: space for payload = 1500 − 20 − 8 − 12 − 4 = {space_1500:,} B (less 16 B RETH) → largest IB MTU that fits = **{active:,}**
- Netdev MTU 9000 → active MTU {rdma_mtu_for(9000):,}; 4,096 needs an IP MTU ≥ {min_ip_mtu_for_4096:,} B
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.K4 ok:", frame, active)


if __name__ == "__main__":
    main()
