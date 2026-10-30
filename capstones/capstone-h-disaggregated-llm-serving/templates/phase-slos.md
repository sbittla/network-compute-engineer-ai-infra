# Phase SLOs (TTFT / ITL / Throughput Targets)

> Template for Capstone H artifact 6.

| Phase | SLI | Target | Budget derivation |
|---|---|---|---|
| Admission + queue | wait p95 | `<fill>` | |
| Prefill | duration p95 (≤ 4k prompts) | `<fill>` | |
| End-to-end TTFT | p95 | ≤ 800 ms | sum of the above |
| KV transfer | exposed p95 | `<fill>` | must fit inside the second-token budget |
| Decode | TPOT p95 (per-request mean) | ≤ 50 ms | |
| Decode | ITL p99 (per-token gap) | ≤ 100 ms | |
| KV hand-off | Second-token gap p95 (once per request; not diluted into ITL) | ≤ 100 ms | |
| Throughput | output tokens/s at 30 req/s | `<fill>` | |
| Shedding | rejected fraction during bursts | ≤ 10 % | |

Alerting: `<fill: which SLIs page, burn-rate windows (Chapter 18)>`
