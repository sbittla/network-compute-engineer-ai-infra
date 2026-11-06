#!/usr/bin/env python3
"""Run a command while nvidia-smi samples GPU-Util, SM clock and power every 100 ms.

    python3 with_util.py samples.csv -- <command ...>

The command's stdout and stderr pass through; the sampler is stopped when the command exits.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 4 or sys.argv[2] != "--":
        print(__doc__, file=sys.stderr)
        return 2
    out, cmd = sys.argv[1], sys.argv[3:]
    q = "timestamp,utilization.gpu,clocks.sm,power.draw,temperature.gpu,clocks_event_reasons.active"
    with open(out, "w") as f:
        sampler = subprocess.Popen(["nvidia-smi", f"--query-gpu={q}", "--format=csv", "-lms", "100", "-i", "0"], stdout=f)
        try:
            rc = subprocess.call(cmd)
        finally:
            sampler.terminate()
            try:
                sampler.wait(timeout=10)
            except subprocess.TimeoutExpired:
                sampler.kill()
    return rc


if __name__ == "__main__":
    sys.exit(main())
