# 6.19 — Changing the lab protocol for a serving-latency SLO (model answer, 3 points)

Relies on manuscript Section 6.6 (protocol) and forward reference to Chapter 15 (LLM inference serving).

**Decision to change:** the statistic. The lab summarizes each run by its *median* latency of isolated,
back-to-back kernel calls and compares medians of run medians.

**Replacement:** use **tail percentiles** (p95/p99 time-to-first-token and time-per-output-token, or request
latency) as the statistic, measured under **realistic concurrency and arrival processes** (open-loop Poisson or
replayed production traces at target load, mixed prompt lengths), with **longer runs** so the tails are
estimated from enough samples (p99 needs thousands of requests per run). Still replicate by run and keep the
A/A floor, now on p99.

**Why:** an SLO is a statement about the tail under load. Medians of isolated runs miss queueing, batching and
scheduling effects (continuous batching, KV cache pressure) that dominate the tail; a kernel can improve the
median and worsen p99 (Chapter 15).

(≈ 140 words.)
