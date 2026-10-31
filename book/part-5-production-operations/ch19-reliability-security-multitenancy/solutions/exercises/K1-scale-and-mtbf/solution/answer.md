# K1 — Scale and MTBF: worked solution

**Relies on:** Section 19.1; Reference Cluster "Reliability assumptions" (node MTBF ≈ 1,536 node-hours
`[ILLUSTRATIVE]`). Results are `[MODELED]`.

## Method

A synchronous training job stops when *any* of its nodes suffers a job-interrupting fault. If node
failures are independent with a constant rate λ_node = 1 / MTBF_node, the job's failure rate is the sum
of its nodes' rates, N × λ_node. So:

```text
MTBF_job          = MTBF_node / N
interruptions/day = 24 h / MTBF_job = 24 × N / MTBF_node
```

## Results

| Nodes (GPUs) | Job MTBF | Interruptions/day |
|---|---|---|
| 8 (64) | 1,536 / 8 = 192 h | 24 / 192 = 0.125 (one every 8 days) |
| 32 (256, ORION-256) | 1,536 / 32 = 48 h | 24 / 48 = 0.5 |
| 128 (1,024) | 1,536 / 128 = 12 h | 24 / 12 = 2 |
| 512 (4,096, ORION-XL) | 1,536 / 512 = 3 h | 24 / 3 = 8 |

## Interpretation

Interruptions scale linearly with job size: a 512-node job should *expect* eight restarts a day, so
restart overhead and checkpoint policy (W1) are throughput engineering, not edge cases. The 3 h figure is
the same order as the Llama 3 report of roughly one interruption every three hours on a ≈ 16k-GPU job.

## Common wrong answers

- Multiplying instead of dividing (treating the job as *more* reliable than one node).
- Using GPU count instead of node count: the canon MTBF is per HX8 node and already includes all eight
  GPUs, the HCAs and node-attributable links.
- Forgetting the units: MTBF in hours, interruptions per day.

`solve.py` reproduces the table and asserts it against the key.
