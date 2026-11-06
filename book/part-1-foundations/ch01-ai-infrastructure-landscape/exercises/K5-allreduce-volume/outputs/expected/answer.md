# K5 — Per-participant volume of a bandwidth-optimal all-reduce

Source: manuscript Section 1.5, "Fact 1" (Patarasuk and Yuan, 2009). `[MODELED]`.

A ring (or any bandwidth-optimal endpoint) all-reduce is a reduce-scatter followed by an all-gather. In
each phase every participant sends (p − 1) chunks of S/p bytes, so the total sent per participant is

```text
sent = 2 (p − 1) / p × S
p = 4 : 2 × 3 / 4 = 1.5  → 1.5 S
p = 8 : 2 × 7 / 8 = 1.75 → 1.75 S
p → ∞ : → 2 S
```

Each participant also *receives* the same volume. This is the endpoint lower bound; in-network reduction
(NVLink SHARP/NVLS in an NVSwitch domain, SHARP in InfiniBand switches) cuts per-GPU traffic to ≈ S
(Chapter 12). WP1 depends on this: using 1.75 for the TP = 4 group is the most common error.

**Marking note:** the key gives 2 points; this folder scores it out of 4.
