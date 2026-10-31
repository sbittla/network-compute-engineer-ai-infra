# K7 — Instantaneous samples versus watermarks (worked solution)

Relies on manuscript Section 9.2 ("Microbursts and what counters can see") and Section 9.8 ("The
counter set", "Reading counters correctly").

## The "contradiction" explained

There is none. The two metrics measure different things:

- **Instantaneous queue depth sampled every 10 s** shows the queue at one random instant in each 10 s
  window. Congestion in an AI fabric comes in **microbursts**: queues fill and drain in tens of
  microseconds. A burst lasting 50 µs is caught by a given sample with probability ≈ 50 µs / 10 s =
  5 × 10⁻⁶. The dashboard almost always samples an idle queue (≤ 20 KB).
- **ECN-marked counters are cumulative**: the switch increments them on every marked packet, so they
  miss nothing between samples. 2 million marks per interval is 200,000 marks/s on average. The queue
  repeatedly exceeds Kmin, just never at the sampling instant.

## What to plot instead

- The **queue watermark** (peak occupancy since last read, cleared on read) per TC 3 queue: it records
  the burst even when the sample misses it (the lab's `q_tc3_max_kb` is exactly this).
- The **ECN-mark rate**: the counter delta divided by the true elapsed time, handling resets and gaps
  (lab Task 1).
- Pause-frame rate alongside it, to see whether DCQCN or PFC is doing the work.

**Common mistake:** "sample every second instead". 1 s sampling still misses microsecond bursts; the
fix is watermarks (or streaming/event telemetry), not a faster poll.
