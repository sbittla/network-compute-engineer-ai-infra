# 12.11 (O2) — Analyze the six configurations

Data `[SIMULATED]` (`lab/data/`); fits `[MODELED]` with the lab method: t = α + factor × S/B fitted by
least squares weighted by 1/t on out-of-place and in-place times; plateau = median out-of-place busbw of
the four largest sizes (1–8 GiB); regions: latency if t ≤ 1.5 × min time, bandwidth if busbw ≥ 0.8 ×
plateau (Section 12.10, Table 12.7).

| Config | Ranks | Latency region | Bandwidth region | α (µs) | B (GB/s) | n½ (MB) | Plateau (GB/s) |
|---|---|---|---|---|---|---|---|
| c1 1 node (NVLS) | 8 | 8 B – 1 MiB | ≥ 16 MiB | 14.1 | 448 | 3.6 | 449 |
| c2 2 nodes aligned | 16 | 8 B – 1 MiB | ≥ 32 MiB | 28.1 | 354 | 5.3 | 352 |
| c3 2 nodes alt map | 16 | 8 B – 1 MiB | ≥ 16 MiB | 39.2 | 185 | 3.9 | 184 |
| c4 4 nodes | 32 | 8 B – 2 MiB | ≥ 32 MiB | 36.2 | 349 | 6.5 | 349 |
| c5 8 nodes | 64 | 8 B – 2 MiB | ≥ 32 MiB | 47.3 | 346 | 8.3 | 345 |
| c6 8 nodes run 2 | 64 | 8 B – 1 MiB | ≥ 16 MiB | 49.8 | 185 | 4.7 | 177 |

**Plot.** `solve.py` writes `plot_data_c2_c5.csv` (size, time for c2 and c5); the learner's matplotlib
plot uses log-log axes, x = message size (B), y = time (µs). The pinned grading runtime has no
matplotlib, so the instructor output is the data, not the image. The plot shows a flat floor at α
(≈ 28 µs for c2, ≈ 47 µs for c5) and slope-1 lines at large sizes that almost coincide.

**Scaling verdict (≈ 150 words).** For large messages the fabric scales: aligned plateau busbw is flat
within 2 % from 2 to 8 nodes (352 → 349 → 345 GB/s), i.e. 86–88 % of the 400 GB/s node NIC egress,
which is what a non-blocking rail-optimized fabric should give. Small messages get slower with scale:
α grows by ≈ 10 µs per doubling of nodes (28 → 36 → 47 µs), the log-depth signature of tree-based
small-message all-reduce, and n½ grows from 5.3 to 8.3 MB, so on 64 ranks any bucket below ≈ 8 MB runs at
under half of plateau — size DDP buckets accordingly. The single node's 449 GB/s reflects NVLS
in-switch reduction and is not comparable with the multi-node rows. Two configurations are anomalous
and must be excluded from the baseline: c3 (≈ half the plateau, steady) and c6 (half the plateau and
jittery, CV 0.088 vs 0.016).

A learner whose region boundaries differ by one size step because of different stated thresholds gets
full marks.
