"""8.16 — Numbers behind the model ORION-XL fabric policy: 3-tier BDP, timeout/retry time-to-failure,
and the expected tail-loss cost at the design loss rate.

Usage: python solve.py --out DIR

Design choices (stated in answer.md): RoCEv2 lossless class; 3-tier cross-pod RTT 10 us
[ILLUSTRATIVE]; payload ceiling 392 Gb/s = 49 GB/s at path MTU 4,096 (Section 8.7); timeout 20,
retry_cnt 7; design loss rate 1e-7 per packet; 4 MiB messages for the trade-off. [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RTT_US = 10.0
CEIL_GBPS = 392
MTU_B = 4096
TIMEOUTS = (14, 18, 20)
CHOSEN_TIMEOUT, RETRY_CNT = 20, 7
P_DESIGN = 1e-7
MSG_B = 4 * 1024 * 1024
NODES, NICS_PER_NODE = 512, 8
KEY = {"bdp_kb": 490, "bdp_pkts": 120, "t_ack_s": 4.29, "ttf_s": 34.4, "tail_cost_us": 0.43}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    bytes_per_us = CEIL_GBPS * 1e9 / 8 / 1e6
    bdp_b = bytes_per_us * RTT_US
    bdp_pkts = round(bdp_b / MTU_B)
    t_ack = {t: 4.096e-6 * 2 ** t for t in TIMEOUTS}
    ttf = {t: (RETRY_CNT + 1) * v for t, v in t_ack.items()}
    msg_us = MSG_B / bytes_per_us
    tail_cost = {t: P_DESIGN * v * 1e6 for t, v in t_ack.items()}            # us per isolated message
    overhead_pct = {t: round(100 * c / msg_us, 4) for t, c in tail_cost.items()}

    assert abs(bdp_b / 1000 - KEY["bdp_kb"]) < 0.5 and bdp_pkts == KEY["bdp_pkts"]
    assert abs(t_ack[CHOSEN_TIMEOUT] - KEY["t_ack_s"]) < 0.005 and abs(ttf[CHOSEN_TIMEOUT] - KEY["ttf_s"]) < 0.05
    assert abs(tail_cost[CHOSEN_TIMEOUT] - KEY["tail_cost_us"]) < 0.005

    result = {
        "exercise": "8.16", "evidence_label": "[MODELED]",
        "inputs": {"rtt_us": RTT_US, "ceiling_gbps": CEIL_GBPS, "path_mtu_b": MTU_B, "retry_cnt": RETRY_CNT,
                   "design_loss_rate": P_DESIGN, "message_b": MSG_B, "nics": NODES * NICS_PER_NODE},
        "steps": {"t_ack_s": {str(k): round(v, 4) for k, v in t_ack.items()},
                  "time_to_failure_s": {str(k): round(v, 2) for k, v in ttf.items()},
                  "message_time_us": round(msg_us, 1),
                  "tail_cost_us_per_isolated_message": {str(k): round(v, 4) for k, v in tail_cost.items()},
                  "tail_cost_pct_of_message": {str(k): v for k, v in overhead_pct.items()}},
        "answer": {"bdp_b": round(bdp_b), "bdp_packets": bdp_pkts, "timeout": CHOSEN_TIMEOUT,
                   "t_ack_s": round(t_ack[CHOSEN_TIMEOUT], 3), "time_to_failure_s": round(ttf[CHOSEN_TIMEOUT], 1),
                   "tail_cost_us": round(tail_cost[CHOSEN_TIMEOUT], 2)},
        "units": "B, packets, s, us", "tolerance": "key rounding",
    }
    rows = "\n".join(f"| {t} | {t_ack[t]:.4f} | {ttf[t]:.2f} | {tail_cost[t]:.4f} | {overhead_pct[t]} % |" for t in TIMEOUTS)
    md = f"""# 8.16 — result `[MODELED]`

- BDP = {bytes_per_us:,.0f} B/µs × {RTT_US} µs = **{bdp_b:,.0f} B** ≈ **{bdp_pkts} packets** of 4,096 B
- A 4 MiB message takes {msg_us:.1f} µs at {CEIL_GBPS} Gb/s

| timeout | T_ack (s) | Time to failure, retry_cnt 7 (s) | Tail cost at p = 10⁻⁷ (µs/msg) | % of a 4 MiB message |
|---|---|---|---|---|
{rows}
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("8.16 ok")


if __name__ == "__main__":
    main()
