# Marking scheme: T1 Periodic stalls on the full run

Type troubleshooting · kind computed · tier L1 · 15 points

**Evidence required:** tree; ranked test table with scores; causal chain naming the counters that support each link; a fix plan that obeys the runbook's "not without change approval" list; validation criteria.

| Criterion | Points |
|---|---|
| (a) hypothesis tree with at least four leaves, each with a predicted fingerprint, and the physical-layer leaf matched | 4 |
| (b) three tests ranked by info / (cost × risk) with scores (1.6, 1.2, 0.117) | 3 |
| (c) causal chain from optic to step time naming FEC, CRC, out_of_sequence and local_ack_timeout_err, with the NCCL_IB_TIMEOUT arithmetic (2^20 × 4.096 µs ≈ 4.3 s) | 4 |
| (d) safe fix under a change ticket, no switch config or NCCL_IB_TIMEOUT change, with acceptance test and numeric validation | 4 |
