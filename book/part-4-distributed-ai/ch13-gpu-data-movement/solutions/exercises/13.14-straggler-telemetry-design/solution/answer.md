# 13.14 — Straggler telemetry for ORION-XL: worked solution

**Fields per rank row** (Section 13.7, "Instrumenting a job"):

- *Identity / join keys:* job ID, step, rank, host, GPU index and UUID/BDF, NIC, rail, leaf port (from
  Chapter 5's mapping CSV).
- *Phases (CUDA events, read one step late):* forward, backward, collective entry, collective complete,
  optimizer end, giving compute, wait and transfer. Data-loader wait.
- *Work:* tokens and samples processed.
- *GPU context:* SM clock, clocks-event reasons bitmask, temperature, power.
- *Network:* NIC TX/RX bytes over the transfer phase, and deltas of `packet_seq_err`,
  `local_ack_timeout_err` and `out_of_sequence`.

About 20 numeric fields of 8 B each.

**Sampling.** One row per rank every 10 steps, plus DCGM at 1 Hz on the node agent, which is already
collected fleet-wide.

**Arrival skew without synchronized clocks.** Wait = collective duration − post-arrival transfer time,
measured on each rank's own clock. Alternatively, every N steps all-gather each rank's entry timestamp
relative to a common collective completion. No cross-host wall-clock comparison is needed.

**Volume `[MODELED]` (W-TRAIN-like 2 s step at ORION-XL scale, an `[ILLUSTRATIVE]` assumption):**

```text
steps/day           = 86,400 s / 2 s           = 43,200
sampled steps/day   = 43,200 / 10              = 4,320
bytes per sample    = 4,096 ranks × 20 × 8 B   = 655,360 B
volume per day      = 655,360 B × 4,320        = 2.83 GB/day (before compression)
```

Every step instead of every 10th: 28.3 GB/day. Both are small next to checkpoint data. The constraint
is the per-step cost on the training critical path, not storage.

**Alert rules.**

1. *Straggler:* robust z of compute ≥ 6 in ≥ 25 % of a 50-step window for the same rank → page Training
   Infra with the rank → host → GPU join.
2. *Synchronization tax:* median wait fraction > 10 % of step time over 100 steps → ticket.
3. *Rail:* retransmission delta for local index *i* ≥ 100× the median of other indices, on ≥ 3 nodes →
   Network page naming `orion-be-leaf-r<i>`.
4. *Thermal:* clocks-event reason set with clock < 90 % of peer median for ≥ 10 samples → Fleet.

**Trade-off defended.** Per-rank rows every 10 steps rather than every step: event recording costs
nothing, but logging, serialization and any all-gather run on the host path of every rank. At 4,096
ranks a 1 ms host hiccup per step is itself a straggler source (Section 13.7). Persistent causes like
the lab's last tens of steps. A 10-step stride still sees onset within about 30 steps (three
consecutive flagged samples). Transient single-step events are covered by DCGM at 1 Hz and by the
flight recorder for hangs. Fidelity is traded only where the robust statistics do not need it.
