# Marking scheme: D1 RAG serving tier

Type design-challenge · kind computed · tier L1 · 25 points

**Evidence required:** a sizing table with ρ, TTFT, TPOT and batch per pool, the network budget in Gb/s with the arithmetic, a transport decision with numbers, a failure table, and an explicit MODELED/MEASURED labelling of every number.

| Criterion | Points |
|---|---|
| Sizing: prefill t_p 390 ms with quadratic term, P table (12/13/14) with exact M/D/1 p95, D table (3/4/5), choice 14P + 4D with node count | 8 |
| Network budget: 2.684 GB per request, 429.5 Gb/s aggregate, 107.4 Gb/s per decode replica | 5 |
| Transport decision with numbers: RDMA 7.9 % and 15.8 ms (hidden per layer) vs TCP 107 % infeasible | 4 |
| Failure table: decode replica loss, prefill replica loss, KV transfer timeout | 4 |
| Three L2/L3 measurements before committing | 2 |
| Every number labelled MODELED/MEASURED | 2 |
