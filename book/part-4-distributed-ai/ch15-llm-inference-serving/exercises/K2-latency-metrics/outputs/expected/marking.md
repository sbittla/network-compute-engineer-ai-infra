# Marking scheme: K2 Latency metrics

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the three definitions as formulas over request timestamps, plus the failure and the reason it averages away

| Criterion | Points |
|---|---|
| TTFT = first_token − arrival | 1 |
| TPOT = (finish − first_token) / (n_out − 1); ITL = t_{i+1} − t_i | 1 |
| A failure visible in ITL p99 but not mean TPOT (e.g. a prefill stall of about 90 ms) | 1 |
| Arithmetic showing why it averages away (90 ms over 255 gaps ≈ 0.35 ms) | 1 |
