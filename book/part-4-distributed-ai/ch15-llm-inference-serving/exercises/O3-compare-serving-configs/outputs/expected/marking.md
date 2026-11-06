# Marking scheme: O3 Compare two serving configurations

Type outline-mandated · kind computed · tier L1 · 6 points

**Evidence required:** the comparison table, both recommendations with numbers, and the flip conditions.

| Criterion | Points |
|---|---|
| Comparison table from compare_serving_configs (max_seqs, batch, TPOT, tokens/s/node, prefill) | 2 |
| Latency: L-tp8-bf16 (TPOT 11.7 ms); throughput: T-tp4-fp8 (12,678 vs 2,740 tokens/s/node) | 2 |
| Flip conditions: TPOT SLO below about 20 ms; contexts beyond about 5k cap T's batch below 128; FP8 quality unacceptable | 2 |
