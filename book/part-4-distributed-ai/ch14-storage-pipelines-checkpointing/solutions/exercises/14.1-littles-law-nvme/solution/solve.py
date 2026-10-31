"""14.1 -- Little's law on NVMe. [MODELED]

Usage: python solve.py --out DIR
Inputs (prompt): 4 KiB random reads, 95 µs mean latency at QD 1; iostat r/s = 330,000, r_await = 0.097 ms.
Formula (manuscript Section 14.2): outstanding = throughput × latency.
"""
import argparse
import json
from pathlib import Path

BLOCK_B = 4096
LAT_QD1_S = 95e-6
IOSTAT_RPS = 330_000
IOSTAT_AWAIT_S = 0.097e-3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    iops = 1 / LAT_QD1_S
    mbps = iops * BLOCK_B / 1e6
    mibps = iops * BLOCK_B / 2**20
    qd = IOSTAT_RPS * IOSTAT_AWAIT_S
    # Key 14.1: 10,526 IOPS, 43.1 MB/s (41.1 MiB/s); QD 32.0. Tolerances: 1 IOPS, 0.05 MB/s, 0.05.
    assert abs(iops - 10526) < 1, iops
    assert abs(mbps - 43.1) < 0.05 and abs(mibps - 41.1) < 0.05, (mbps, mibps)
    assert abs(qd - 32.0) < 0.05, qd

    result = {
        "inputs": {"block_B": BLOCK_B, "latency_qd1_s": LAT_QD1_S, "iostat_r_per_s": IOSTAT_RPS,
                   "iostat_r_await_s": IOSTAT_AWAIT_S},
        "steps": {"formula": "QD = IOPS × latency", "iops_qd1": round(iops, 1)},
        "answer": {"iops_qd1": round(iops), "MBps_qd1": round(mbps, 1), "MiBps_qd1": round(mibps, 1),
                   "avg_queue_depth": round(qd, 1),
                   "util_100pct_is_saturation": False},
        "units": {"iops": "1/s", "MBps": "1e6 B/s", "MiBps": "2^20 B/s", "queue_depth": "requests"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# 14.1 result `[MODELED]`\n\n"
          f"- (a) IOPS = 1 / 95 µs = {iops:,.0f}; x 4,096 B = {mbps:.1f} MB/s ({mibps:.1f} MiB/s)\n"
          f"- (b) QD = 330,000 /s × 0.097e-3 s = {qd:.1f}\n"
          f"- (c) %util = time with >= 1 request outstanding; NVMe is parallel, so 100 % is not saturation.\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
