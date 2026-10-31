# D1 — The inference pool: reference approach

Sources: manuscript Section 21.3 ("Converting inference demand to GPUs") and Section 21.11 (the idle
dedicated pool); Chapter 15 for the TTFT SLO and Chapter 17 for preemption. Inputs `[ILLUSTRATIVE]`;
results `[MODELED]`, reproduced by `solve.py`.

**Sizing (given).** Peak 25 req/s ÷ 2.5 req/s per replica = 10 replicas, plus N+2 = 12 replicas ×
8 GPUs = 96 GPUs → 96 × 8,760 = **840,960 GPU-h/yr** provisioned. The average load is 40 % of *peak*,
so on average 0.4 × 10 = 4 replicas are busy (Section 21.3: "≈ 4 of 12").

**Option 1: dedicated.** Busy = 4 × 8 × 8,760 = 280,320 GPU-h (33 % allocated). Idle = **560,640
GPU-h/yr**. No borrowed work, and the simplest operation.

**Option 2: shared.** Assumptions, stated:
- the N+2 headroom (2 replicas, 140,160 GPU-h) is **never** lent, which leaves 420,480 idle GPU-h;
- training borrows only replicas above a forecast-plus-margin threshold, assumed to be 60 % of idle
  hours → 0.6 × 560,640 = **336,384 GPU-h lent** (inside the 420,480 limit);
- borrowed work runs at goodput 0.7. It is preemptible, checkpoints often, and loses work at every
  reclaim.

Useful borrowed work = 336,384 × 0.7 = **235,469 GPU-h/yr**, worth ≈ **$1.12M/yr** at $4.75 per
useful GPU-hour (Section 21.4). Pool allocation rises from 33 % to 73 %.

| | Dedicated | Shared |
|---|---|---|
| Useful GPU-h/yr | 280,320 (serving) | 515,789 (serving + 235,469 training) |
| TTFT SLO risk | Lowest: capacity always resident | Reclaim latency adds a new failure path |
| Complexity | Low | High: preemption, checkpoint cadence, reclaim path, two owners |

**SLO risk analysis.** The risk is a traffic ramp arriving faster than reclaim. Reclaim = signal +
training checkpoint or kill + model load. A 70B-class model is ≈ 140 GB of BF16 weights; loading it from
the network in < 60 s needs ≥ 2.3 GB/s per node. Keeping the weights resident in host memory or local
NVMe makes that feasible. If reclaim misses 60 s while queue depth is rising, TTFT p99 breaches. The
N+2 replicas absorb a sudden ramp or a failure during reclaim, which is why they are never lent.

**Guardrails.** (1) Lending stops when forecast peak minus 30 min is reached, and reclaim is
triggered on *rising queue depth*, not on an SLO breach. (2) A TTFT burn-rate alert inhibits all
lending. (3) The N+2 replicas are excluded from the lendable set by policy. (4) Reclaim times are
audited continuously (p99 < 60 s), with an automatic fallback to dedicated mode when the audit fails.
(5) Borrowing jobs must checkpoint at ≤ 10 min intervals and tolerate a SIGTERM grace of ≤ 30 s.

**Recommendation.** Shared, *if* the reclaim drill measures p99 < 60 s including model reload.
Otherwise run dedicated and lend only overnight in a fixed window. Weak answers ignore reload time or
lend the headroom replicas.

*Key correction:* the earlier key took 40 % of the whole 96-GPU pool as busy (≈ 505,000 idle GPU-h).
The N+2 replicas are idle by design, so idle is 560,640 GPU-h.
