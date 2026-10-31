"""8.9 — The price of a lost packet: 1 MiB RDMA WRITE cross-rail on ORION under go-back-N.

Usage: python solve.py --out DIR

Prompt parameters: path MTU 4,096 B; payload ceiling 392 Gb/s; cross-rail RTT 5 us [ILLUSTRATIVE];
timeout = 18, retry_cnt = 7; per-packet loss p = 1e-5. T_ack = 4.096 us x 2^timeout (Section 8.6).
[MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MSG_B = 1024 * 1024
MTU_B = 4096
CEIL_GBPS = 392
RTT_US = 5.0
TIMEOUT, RETRY_CNT = 18, 7
P_LOSS = 1e-5
LOST_PKT = 50
KEY = {"packets": 256, "t_us": 21.4, "bdp_pkts": 60, "b_extra_us": 5.0, "t_ack_s": 1.074,
       "d_cost_us": 10.7, "d_goodput": 0.67, "e_s": 8.59}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    bytes_per_us = CEIL_GBPS * 1e9 / 8 / 1e6          # 49,000 B/us
    packets = MSG_B // MTU_B
    t_us = MSG_B / bytes_per_us
    bdp_b = bytes_per_us * RTT_US
    bdp_pkts = round(bdp_b / MTU_B)
    b_extra_us = bdp_pkts * MTU_B / bytes_per_us      # resend of the window sent before the NAK came back
    t_ack_s = 4.096e-6 * 2 ** TIMEOUT
    d_tail_cost_us = P_LOSS * t_ack_s * 1e6           # only the last packet (or final ACK) forces a timeout
    d_mid_cost_us = packets * P_LOSS * RTT_US
    goodput = t_us / (t_us + d_tail_cost_us + d_mid_cost_us)
    e_s = (RETRY_CNT + 1) * t_ack_s
    burst = {k: round(t_us / (t_us + d_tail_cost_us / k + d_mid_cost_us), 3) for k in (1, 4, 16, 64)}

    assert packets == KEY["packets"] and abs(t_us - KEY["t_us"]) < 0.05
    assert bdp_pkts == KEY["bdp_pkts"] and abs(b_extra_us - KEY["b_extra_us"]) < 0.05
    assert abs(t_ack_s - KEY["t_ack_s"]) < 0.0005 and abs(d_tail_cost_us - KEY["d_cost_us"]) < 0.05
    assert abs(goodput - KEY["d_goodput"]) < 0.005 and abs(e_s - KEY["e_s"]) < 0.005

    result = {
        "exercise": "8.9", "evidence_label": "[MODELED]",
        "inputs": {"message_b": MSG_B, "path_mtu_b": MTU_B, "ceiling_gbps": CEIL_GBPS, "rtt_us": RTT_US,
                   "timeout": TIMEOUT, "retry_cnt": RETRY_CNT, "p_loss": P_LOSS, "lost_packet": LOST_PKT},
        "steps": {"bytes_per_us": bytes_per_us, "bdp_b": round(bdp_b), "b_extra_pct_of_a": round(100 * b_extra_us / t_us, 1),
                  "d_mid_cost_us": round(d_mid_cost_us, 4), "d_goodput_back_to_back_by_burst_len": burst},
        "answer": {"a_packets": packets, "a_time_us": round(t_us, 2), "b_bdp_packets": bdp_pkts,
                   "b_extra_us": round(b_extra_us, 2), "c_extra_s": round(t_ack_s, 4),
                   "d_expected_tail_cost_us": round(d_tail_cost_us, 2), "d_goodput": round(goodput, 3),
                   "e_time_to_retry_exc_err_s": round(e_s, 2)},
        "units": "us, s, packets", "tolerance": "key rounding (±0.05 us, ±0.005)",
    }
    md = f"""# 8.9 — result `[MODELED]`

- (a) {MSG_B:,} / {MTU_B:,} = **{packets} packets**; {MSG_B:,} B / {bytes_per_us:,.0f} B/µs = **{t_us:.1f} µs**
- (b) BDP = {bytes_per_us:,.0f} B/µs × {RTT_US} µs = {bdp_b:,.0f} B ≈ **{bdp_pkts} packets**; extra ≈ {bdp_pkts} × 4,096 B / {bytes_per_us:,.0f} B/µs = **{b_extra_us:.1f} µs** ({100 * b_extra_us / t_us:.0f} % of (a))
- (c) T_ack = 4.096 µs × 2^{TIMEOUT} = **{t_ack_s:.3f} s** extra
- (d) 10⁻⁵ × {t_ack_s:.3f} s = **{d_tail_cost_us:.1f} µs** per isolated message (+ {d_mid_cost_us:.3f} µs mid-message) → goodput **{100 * goodput:.0f} %**; back-to-back bursts of k messages: {burst}
- (e) ({RETRY_CNT} + 1) × {t_ack_s:.3f} s = **{e_s:.2f} s**
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("8.9 ok")


if __name__ == "__main__":
    main()
