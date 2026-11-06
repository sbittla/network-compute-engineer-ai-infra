# 12.16 — Why "Avg bus bandwidth" is a poor single-number summary

nccl-tests prints `# Avg bus bandwidth` as the arithmetic mean of busbw over **every message size in
the sweep**. With the usual 8 B – 8 GiB sweep, about half the rows are latency-bound and show busbw near
0 GB/s, so the average depends mostly on how many small sizes the sweep includes — not on the fabric.
In the lab, c5 reports **117 GB/s** while its plateau is **345 GB/s** `[SIMULATED]`. Change `-b` or `-f`
and the "average" changes without any hardware change; it is also not comparable between runs with
different ranges.

**Report instead:**

1. **Plateau busbw** — the median out-of-place busbw of the largest sizes (e.g. 1–8 GiB), which measures
   bandwidth capability and is compared with the node's NIC egress (Section 12.10).
2. **Small-message latency** — the p50 time at 8 B (≈ α), which governs small collectives and DDP bucket
   efficiency.

Add **n½** (the size reaching half of plateau) when bucket sizing matters, and the spread across
launches (CV or min/median) so a reader sees jitter. Two numbers plus the spread answer the two
questions a reader actually has: "how fast for big messages" and "how slow for small ones".
