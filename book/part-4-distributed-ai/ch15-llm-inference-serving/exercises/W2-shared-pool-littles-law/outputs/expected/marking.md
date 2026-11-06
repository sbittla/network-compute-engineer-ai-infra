# Marking scheme: W2 Sizing a shared pool with Little's law

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** a table for (b), the fixed-point derivation for one row, and the choice with justification

| Criterion | Points |
|---|---|
| (a) t_p = 181.1 ms, demand 4.53 replica-s/s (quadratic term about 6.9 ms credited) | 2 |
| (b) table for 6/8/10/12 replicas with ρ, TTFT, TPOT, B; 6 replicas unstable; one fixed-point derivation | 5 |
| (c) choose 10 (+2 for N+1 and bursts), worst unchunked ITL about 197 ms, recommend chunked prefill | 2 |
| (d) KV check: 288 blocks per sequence, 139 sequences per replica ≫ 38 | 1 |
