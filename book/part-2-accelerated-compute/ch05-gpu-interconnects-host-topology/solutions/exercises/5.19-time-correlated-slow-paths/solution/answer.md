# 5.19 — Time-correlated slow paths (model answer)

Relies on manuscript Section 5.9 ("What the model ignores": correlation between samples) and Section 5.10.

The model redraws every path's bandwidth independently each iteration, so a slow draw on one iteration is
usually followed by a normal one and the slowest-member effect averages out across iterations. Real slow
paths (congestion, a throttled link, a busy root complex) stay slow for seconds to minutes. If each path's
marginal distribution and the independence between paths stay the same, the long-run per-iteration
distribution of the slowest path, and so its **p99, is unchanged**. What changes is clustering: slow
iterations arrive as long stretches. **Run-to-run variance grows**, because a run either hits a slow period
or not; a short (5-run) benchmark can miss or over-weight a slow episode; and windowed statistics (for
example a per-minute p99) describe the job better than per-iteration ones.

Effect on "nearest vs aligned": the forced-aligned path on `orion-n17` is SYS and host-staged with high CV
(S4: CV 0.331, p99 37.45 ms), so it has the longest slow stretches. The default nearest policy shares a NIC almost
deterministically (S3: CV 0.027), so correlation barely changes it. The conclusion that nearest beats
forced alignment stands, and neither replaces repairing the node.

(≈ 150 words.)
