# K8 — Label cardinality for per-rank, per-step metrics

**Why these labels are forbidden on high-frequency metrics.** Prometheus stores one time series per
unique combination of metric name and label values. `rank` (thousands of values per job),
`request_id` (one per request), and `step` (a new value every step) are unbounded or nearly so: every
new value creates a new series with its own index entry and memory chunk, and most series receive a
single sample before going stale. Memory, index size, ingestion, and query time grow with the number
of series, not the number of samples.

**Estimate** `[MODELED]`:
steps per day = 86,400 s / 17.4 s = 4,965.5 → **4,966**;
series = 4,096 ranks × 4,966 steps ≈ **20.3 million new series per day** from one gauge of one job,
enough to destabilize a Prometheus server within hours (a typical server is sized for a few million
active series; Section 18.6 cardinality budget).

**Where the information belongs.** Per-rank, per-step timings go to logs or a trace/flight-recorder
store (queried by `job_id`, `rank`, and time range when drilling down to the workload level).
Export only aggregates as metrics: a step-time histogram labelled by `job_id` (bounded), from which
p50/p95 and the throughput ratio are computed, plus perhaps a "slowest rank" gauge without the rank
as a label.

`solve.py` reproduces the count.
