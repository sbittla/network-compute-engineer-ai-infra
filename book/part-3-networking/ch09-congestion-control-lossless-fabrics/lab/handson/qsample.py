#!/usr/bin/env python3
"""Chapter 9 hands-on lab: sample the bottleneck queue (run inside the ch09-sw namespace).

    python3 qsample.py <dev> <seconds> <out.csv> [interval_s]

Every interval (default 20 ms) it reads `tc -s -j qdisc show dev <dev>` and writes one CSV row for the
child qdisc (handle 10:, the queue under test): time since start, backlog in bytes and packets, and the
cumulative counters the kernel keeps for it (sent, drops, overlimits, and for RED: marked, early, pdrop).
A queue's depth is a gauge, so a slow sample misses bursts (Section 9.2); the cumulative counters never
miss an event. Standard library only.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

FIELDS = ["t_s", "backlog_bytes", "backlog_pkts", "sent_pkts", "drops", "overlimits", "marked", "early", "pdrop"]


def child(dev: str) -> dict:
    out = subprocess.run(["tc", "-s", "-j", "qdisc", "show", "dev", dev], capture_output=True, text=True, check=True).stdout
    for q in json.loads(out):
        if q.get("handle") == "10:":
            return q
    raise RuntimeError(f"no child qdisc 10: on {dev}")


def main() -> int:
    if len(sys.argv) not in (4, 5):
        print(__doc__)
        return 2
    dev, secs, path = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    step = float(sys.argv[4]) if len(sys.argv) == 5 else 0.02
    t0 = time.monotonic()
    with open(path, "w") as f:
        f.write(",".join(FIELDS) + "\n")
        nxt = t0
        while True:
            now = time.monotonic()
            if now - t0 > secs:
                break
            q = child(dev)
            row = [f"{now - t0:.4f}", q.get("backlog", 0), q.get("qlen", 0), q.get("packets", 0), q.get("drops", 0),
                   q.get("overlimits", 0), q.get("marked", 0), q.get("early", 0), q.get("pdrop", 0)]
            f.write(",".join(str(x) for x in row) + "\n")
            nxt += step
            time.sleep(max(0.0, nxt - time.monotonic()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
