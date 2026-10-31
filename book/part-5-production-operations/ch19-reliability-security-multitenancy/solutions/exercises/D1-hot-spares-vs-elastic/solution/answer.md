# D1 — Hot spares vs elastic training: reference approach

**Relies on:** Section 19.1 (Young's model), Section 19.7 ("Rank remapping and spares", "Elastic training
granularity is a whole DP replica"), Table 19.8; Reference Cluster canon. All results `[MODELED]` from
`[ILLUSTRATIVE]` inputs.

## Model and assumptions

- 512-node job, TP = 8, PP = 8, DP = 64; one DP replica = 64 GPUs = 8 nodes.
- Job MTBF M = 1,536 / 512 = 3 h = 180 min; checkpoint interval τ = 19 min (τ_opt); blocking cost δ = 1 min.
- Failures: 512 × 24 / 1,536 = 8 per day; MTTR 5 days → nodes in repair ~ Poisson(40).
- Goodput = 1 − [δ/τ + (τ/2 + R)/M].
- Metric: **useful throughput per fleet node** = goodput × (fraction of the fleet doing training). The
  fleet includes the spare pool in option A.
- Steady state: the failure rate is unchanged when the job runs smaller, and re-shard cost (B) is
  paid per failure like R.

## Numbers

| Option | Goodput | Capacity factor | Useful per fleet node |
|---|---|---|---|
| **A**: p99 pool of 55 outside the partition, fixed world size, R = 15 min | 1/19 + (9.5 + 15)/180 = 0.189 → **0.811** | 512 / (512 + 55) = 0.903 | **0.733** |
| **B, re-packed**: no spares; healthy nodes regrouped into full replicas, R = 5 min | 1/19 + (9.5 + 5)/180 = 0.133 → **0.867** | ⌊(512 − 40)/8⌋ = 59 replicas → 59/64 = 0.922 | **0.799** |
| **B, not re-packed, expected**: 40 failed nodes at random positions | 0.867 | 64 × (1 − C(504,40)/C(512,40)) ≈ 30.8 replicas lost → 33.2/64 = 0.519 | **0.450** |
| **B, not re-packed, worst**: 40 failures in 40 distinct replicas | 0.867 | 24/64 = 0.375 | **0.325** |

The pool size 55 is the smallest k with P(Poisson(40) ≤ k) ≥ 0.99 (P = 0.990). The expected-loss term
uses the probability that a given 8-node replica contains at least one of the 40 failed nodes.

## Global-batch divisibility

A global batch sized for 64 replicas (global batch = DP × micro-batch × accumulation steps) cannot be
split evenly over 59 replicas, because 59 is prime. The job must then do one of three things.

- **Change micro-batch or accumulation steps.** This changes the effective global batch, so the learning
  rate and warm-up schedule must change with it. That is a model-quality decision, needing a validated
  policy, not just a scheduling one.
- **Run at a DP that divides the batch** (for example 56 or 48). This idles 3 or 11 more replicas
  (24–88 nodes) and erodes B's advantage: at DP = 56, 0.867 × 56/64 = 0.758.
- **Use uneven per-replica batches.** These need framework support and careful gradient weighting.

## Recommendation

- B beats A (0.799 vs 0.733, about 9 % more useful work per node) **only with** topology-aligned
  re-packing, a validated batch/LR policy for changing DP, and re-shard time actually measured at
  ≈ 5 min.
- Without re-packing, B is far worse (0.450 expected, 0.325 worst). Choose A.
- A pragmatic hybrid: a smaller pool (p90 ≈ 48 nodes) for fast fixed-size restarts, with elastic
  re-packed fallback when the pool runs dry. This keeps the common case reproducible and bounds capex.

## Risks

- Elastic code paths (re-sharding data loader and optimizer state) are rarely exercised, so they fail
  in the incident.
- Changing DP mid-run makes results harder to reproduce and compare.
- Re-packing must preserve rail alignment and TP placement inside nodes.
- A's pool is only as good as its acceptance testing: in the lab, orionxl-s00 failed acceptance and
  orionxl-s02 is in repair.
- Both options assume independent failures. A correlated event (a leaf or PDU) can take out more nodes
  than either plan absorbs.

## Common wrong answers

- Comparing per *partition* node instead of per *fleet* node, which ignores the pool's capex.
- Assuming B loses only 40 nodes' worth of capacity without re-packing.
- Ignoring divisibility.
