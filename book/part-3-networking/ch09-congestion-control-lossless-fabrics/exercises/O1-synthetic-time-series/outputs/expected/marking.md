# Marking scheme: O1 Analyze the synthetic time series

Type outline-mandated · kind computed · tier L1 · 12 points

**Evidence required:** per episode: label, root or source device, and the quoted discriminating values.

| Criterion | Points |
|---|---|
| Incast 100–158 s: label, root orion-be-leaf-r3:eth1/5, discriminating rates (tx ≈ 394 Gb/s, queue ≈ 1,430 KB held near Xoff, ECN median 0, sender pause ≈ 17–19 k/s, pause rx 0) | 3 |
| Pause propagation 250–318 s: root eth1/10, fabric-port pause and spine branches quoted | 3 |
| PFC storm 400–468 s: source orion-n12:mlx5_3 (pause rx ≈ 23,700/s, tx ≈ 0 Gb/s, queue ≈ 4,000 KB, NIC pfc_tx confirms) | 3 |
| Benign 520–558 s busy port recognized as not an episode (no pause, shallow queue) | 1 |
| Values are rates from the learner's code, with units, and handle the counter reset and telemetry gap | 2 |
