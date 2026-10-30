# Results Table

| # | Result | Value | Evidence class | Source | Tier | Notes |
|---|---|---|---|---|---|---|
| 1 | Checker | `<fill: 11/11 PASS>` | SIMULATED/MODELED | `python starter-kit/check.py` | L1 | |
| 2 | KV bytes/token and per 2k prompt | `<fill>` | MODELED | `kv_cache_bytes` | L1 | |
| 3 | Pool sizing and bottleneck at 30 req/s | `<fill>` | MODELED | `size_pools`, `utilizations` | L1 | |
| 4 | Colocated vs disaggregated (target load) | `<fill>` | SIMULATED | `serving_sim.run` | L1 | |
| 5 | Colocated vs disaggregated (low load) | `<fill>` | SIMULATED | | L1 | |
| 6 | RDMA vs TCP exposed KV p95 | `<fill>` | SIMULATED | | L1 | |
| 7 | Admission control effect | `<fill>` | SIMULATED | | L1 | |
| 8 | $/M output tokens per option | `<fill>` | MODELED | `cost_per_million_tokens` | L1 | ILLUSTRATIVE prices |
| 9 | `<fill: L3 ib_write_bw per rail>` | | MEASURED | | L3 | manifest |
