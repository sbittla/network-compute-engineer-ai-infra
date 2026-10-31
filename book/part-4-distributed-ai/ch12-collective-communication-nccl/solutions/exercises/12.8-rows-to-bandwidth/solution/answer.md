# 12.8 — From rows to bandwidth (c4, 4 nodes, 32 ranks)

Data `[SIMULATED]` from `lab/data/c4_4node_aligned.log` (out-of-place columns); derived values
`[MODELED]`. Method Section 12.5: algbw = S / t; busbw = algbw × 2(n − 1)/n; n = 32 → factor
2 × 31/32 = **1.9375**. GB = 10⁹ B.

| Size (B) | Time (µs) | algbw = S/t (GB/s) | busbw = algbw × 1.9375 (GB/s) | Region |
|---|---|---|---|---|
| 1,048,576 | 43.08 | 1,048,576 / 43.08e−6 / 1e9 = **24.34** | **47.16** | latency (t ≤ 1.5 × min time of ≈ 36 µs; c4's latency region ends at 2 MiB) |
| 67,108,864 | 405.6 | 67,108,864 / 405.6e−6 / 1e9 = **165.46** | **320.57** | bandwidth (≥ 0.8 × 349 GB/s plateau = 279 GB/s) |
| 4,294,967,296 | 23,762 | 4,294,967,296 / 23,762e−6 / 1e9 = **180.75** | **350.20** | bandwidth |

**Efficiency vs the node's NIC egress.** Each HX8 node has 8 × 400 Gb/s = 8 × 50 GB/s = 400 GB/s:

```text
350.20 / 400 = 87.6 %
```

That is normal for a rail-aligned ring (Section 12.11): the inter-node NIC hop is the bottleneck, and
≈ 88 % remains after protocol overhead.

**Region thresholds used** (state them; the lab's `classify_regions`): latency if t ≤ 1.5 × minimum time
(time is flat, α dominates); bandwidth if busbw ≥ 0.8 × plateau; otherwise transition. Learners with
other stated thresholds may label 1 MiB "transition" and still earn the mark.

**Common mistakes.** Comparing 350 GB/s with one NIC's 50 GB/s; using MiB (2²⁰) for GB in the
bandwidth (gives 22.7 instead of 24.3); using n = 4 (nodes) in the factor.
