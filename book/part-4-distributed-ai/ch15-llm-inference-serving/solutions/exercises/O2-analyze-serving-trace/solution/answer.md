# O2 — Analyze a serving trace: worked solution

**Method.** Lab Part B on `lab/data/` `[SIMULATED]`: per-request metrics from `requests.csv`, episodes
detected by the lab's window analysis (queueing collapse 240–345 s, preemption storm 465–600 s), ITL from
the 5 % sample in `token_gaps.csv`, and replica telemetry averaged over the segment. Segments are by
arrival time. Rates are per second of segment.

| Segment | req/s | out tokens/s | TTFT p50 / p95 | ITL p50 / p99 (sampled) | Queue p95 | GPU busy | KV max | Waiting (mean) |
|---|---|---|---|---|---|---|---|---|
| Baseline 0–230 s | 6.00 | 1,216 | 0.138 / 0.449 s | 21.8 / 216 ms | 0.11 s | 97.6 % | 13.5 % | 0.1 |
| Burst 240–345 s | 14.8 | 2,980 | 11.8 / 28.8 s | 26.9 / 444 ms | 28.5 s | 100 % | 43.3 % | 46.1 |
| Storm 465–600 s | 5.81 | 1,434 | 0.278 / 33.2 s | 37.2 / 386 ms | 32.6 s | 100 % | 100 % | 6.0 |

**Reading it.**

- *Burst:* arrivals 2.5× baseline, the queue explodes (p95 28.5 s), and KV stays at 43 %. The replicas are
  slot-bound at the 48-sequence cap, not memory-bound.
- *Storm:* arrivals *flat*, but KV hits 100 %, preemptions rise (+38 over the episode) and ITL p50 rises
  to 37 ms. It is memory-bound with a long TTFT tail (p50 still 0.28 s, p95 33 s).
- *Baseline:* ITL p99 of 216 ms reflects unchunked prefill stalls (K2), which is expected for this pool.

**Why GPU utilization is least informative.** `gpu_busy_pct` is 97.6–100 % in all three segments. It
counts time with any kernel running (K7), so it cannot distinguish healthy from overloaded, or slot-bound
from memory-bound. Every other column changes by 3–300× between segments.
