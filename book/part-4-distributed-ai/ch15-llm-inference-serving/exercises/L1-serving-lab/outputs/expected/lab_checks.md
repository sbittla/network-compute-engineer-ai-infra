# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `A1 kv_bytes_per_token (W-INFER BF16 and FP8 KV)` | PASS A1 kv_bytes_per_token (W-INFER BF16 and FP8 KV) |
| `A2 kv_budget_bytes (TP=8 BF16, TP=4 FP8, TP=2 FP8)` | PASS A2 kv_budget_bytes (TP=8 BF16, TP=4 FP8, TP=2 FP8) |
| `A3 max_concurrent_sequences (paged, 16-token blocks)` | PASS A3 max_concurrent_sequences (paged, 16-token blocks) |
| `A4 prefill_time_s (2k prompt, TP=8 BF16, 40% MFU)` | PASS A4 prefill_time_s (2k prompt, TP=8 BF16, 40% MFU) |
| `A5 decode step lower bound and tokens/s (TP=8 BF16, B=32, ctx=2176)` | PASS A5 decode step lower bound and tokens/s (TP=8 BF16, B=32, ctx=2176) |
| `A6 compare_serving_configs + recommendation per objective` | PASS A6 compare_serving_configs + recommendation per objective |
| `B1 request_metrics (queue, prefill, TTFT, TPOT, e2e)` | PASS B1 request_metrics (queue, prefill, TTFT, TPOT, e2e) |
| `B2 latency_percentiles (chat TTFT p50/p95/p99)` | PASS B2 latency_percentiles (chat TTFT p50/p95/p99) |
| `B3 itl_values_s + ITL tail (sampled token gaps)` | PASS B3 itl_values_s + ITL tail (sampled token gaps) |
| `B4 slo_report (attainment, goodput, throughput)` | PASS B4 slo_report (attainment, goodput, throughput) |
| `B5 detect queueing collapse under the arrival burst` | PASS B5 detect queueing collapse under the arrival burst |
| `B6 detect preemption storm (and do not call it a burst)` | PASS B6 detect preemption storm (and do not call it a burst) |
| `B7 detect the slow replica` | PASS B7 detect the slow replica |
| `B8 telemetry_evidence corroborates the diagnoses` | PASS B8 telemetry_evidence corroborates the diagnoses |
| `B9 analyzer robustness: missing and out-of-order timestamps` | PASS B9 analyzer robustness: missing and out-of-order timestamps |
| `C1 kv_transfer_time_s (2k-token KV over 4x400G RDMA)` | PASS C1 kv_transfer_time_s (2k-token KV over 4x400G RDMA) |
| `C2 md1_wait_s` | PASS C2 md1_wait_s |
| `C3 compare_designs (shared vs disaggregated RDMA/TCP) [MODELED]` | PASS C3 compare_designs (shared vs disaggregated RDMA/TCP) [MODELED] |
| `C4 speculative decoding expected tokens and speedup` | PASS C4 speculative decoding expected tokens and speedup |
