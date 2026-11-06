# R2 — What one-minute switch aggregates cannot show

`lab/data/switch_metrics.csv` holds one-minute per-switch aggregates (PFC pause TX/RX, ECN-marked
packets, TX utilization). With that resolution you cannot establish:

1. **Which ports and queues paused.** A per-switch sum shows that a rail leaf sent ≈ 95× more pauses,
   not whether one egress port toward one host or all ports did; you cannot locate the congestion
   point or distinguish incast toward a few hosts from fabric-wide back-pressure.
2. **Microburst structure.** A 2 ms line-rate burst is 0.0033 % of a 60 s average (exercise K2); the
   events that fill buffers and trigger XOFF are invisible.
3. **Ordering inside the minute.** Whether ECN marks *should* have come first and PFC took over (the
   hypothesized mechanism) needs sub-second ordering of mark and pause events.
4. **Pause storms and propagation paths.** Whether pauses formed a spreading tree (leaf → spine →
   other leaves) or a persistent storm from one port.

**Telemetry to add** (Section 18.4, Table 18.3): gNMI `SAMPLE` subscriptions at 1–10 s for per-port,
per-priority pause frames *and pause duration*, per-queue buffer occupancy watermarks, ECN-marked
packets per queue, and `ON_CHANGE` for oper-status; host-side `rx/tx_prio3_pause_duration` and CNP
counters to pair the two ends; optionally the switch's congestion/telemetry snapshots on threshold.
Keep cardinality bounded by aggregating by port role in Prometheus and sending raw high-rate data to
a short-retention store.
