# 5.19 — Time-correlated slow paths (model answer)

Relies on manuscript Section 5.9 ("What the model ignores": correlation between samples) and Section 5.10.

The model redraws every path's bandwidth independently each iteration, so a slow draw on one iteration is
usually followed by a normal one and the slowest-member effect averages out across iterations. Real slow
paths (congestion, a throttled link, a busy root complex) stay slow for seconds to minutes. Then whole
stretches of consecutive iterations run at the slow rate: **p99 over a run rises** (the tail is no longer a few
unlucky iterations but entire periods), and **run-to-run variance grows**, because a run either hits a slow
period or not.

Effect on "nearest vs aligned": the forced-aligned path on `orion-n17` is SYS and host-staged with high CV
(S4: CV 0.331, p99 37.45 ms), so it suffers most. The default nearest policy shares a NIC deterministically
(S3: CV 0.027), so correlation barely changes it. The conclusion that nearest beats forced alignment gets
stronger, and neither replaces repairing the node.

(≈ 150 words.)
