# Marking scheme: DEL Inference capacity model and tuning recommendation

Type deliverable · kind lab · tier L1 · 20 points

**Evidence required:** the checker at 19/19, every number labelled, and the validation plan with the commands from lab Section 9.

| Criterion | Points |
|---|---|
| Completed lab module, checker at 19/19 | 4 |
| Replica layout and pool size for 40 req/s (8 x TP = 4 FP8 with chunked prefill, 5 nodes incl. N+1, or a numerically argued alternative) | 4 |
| Latency tier L and throughput tier T with numbers | 2 |
| Disaggregation decision with the KV network budget (about 215 Gb/s, RDMA)  | 3 |
| Phase-specific SLOs and alert thresholds (TTFT, TPOT, ITL p99, preemption, per-replica TPOT) | 3 |
| Validation plan with L2/L3 measurements, lab Section 9 commands and manifest fields; every number labelled | 4 |
