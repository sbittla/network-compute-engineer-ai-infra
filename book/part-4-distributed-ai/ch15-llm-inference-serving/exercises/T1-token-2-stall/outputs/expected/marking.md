# Marking scheme: T1 Token-2 stall in the disaggregated pool

Type troubleshooting · kind written · tier L1 · 20 points

**Evidence required:** ranked hypotheses with for/against evidence, at least two discriminating tests with real commands or data sources, a mitigation that touches no shared fabric configuration without change control, and a validation criterion with numbers.

| Criterion | Points |
|---|---|
| Ranked hypotheses with for/against evidence (shared NICs/rail ports first; fabric hot spot; KV demand rejected by request rate; physical fault unlikely) | 6 |
| At least two discriminating tests with real commands or data sources (squeue/scontrol node list, ethtool prio counters, leaf ECN/PFC per port, job NCCL INFO) | 6 |
| Safe mitigation touching no shared fabric configuration (exclude decode nodes from the job, revert the partition change); structural fix enforcing node ownership via change control | 4 |
| Validation criteria with numbers over the next windows (KV p99 < 10 ms, token-2 ITL p99 < 30 ms, ECN < 100/s, PFC 0) | 4 |
