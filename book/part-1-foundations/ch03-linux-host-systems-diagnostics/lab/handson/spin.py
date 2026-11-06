#!/usr/bin/env python3
"""Busy-loop one thread for a fixed time: python3 spin.py ch03-spin <seconds>. The tag names it for teardown."""
import sys
import time

end = time.monotonic() + float(sys.argv[2])
n = 0
while time.monotonic() < end:
    n += 1
