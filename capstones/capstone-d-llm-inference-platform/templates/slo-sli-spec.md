# SLO / SLI Specification

## 1. SLIs

| SLI | Definition (exact) | Measured where | Population | Unit |
|---|---|---|---|---|
| TTFT | <fill: time from request accepted at the gateway to first streamed token byte> | <fill: gateway, not engine> | <fill: prompts ≤ 2,048 tokens; long prompts reported separately> | s |
| TPOT | <fill: per-request MEAN: (last token − first token) / (output tokens − 1)> | | | ms |
| ITL (inter-token latency) | <fill: the per-token gap DISTRIBUTION across all tokens; report p95/p99. Prefill stalls (chunked or unchunked) appear here and are hidden by mean TPOT> | | | ms |
| E2E latency | <fill> | | | s |
| Availability | <fill: successful requests / valid requests; what counts as a failure (5xx, rejection, timeout)> | | | % |
| Goodput | <fill: share of requests meeting all latency targets> | | | % |

## 2. SLOs

| SLO | Target | Window | Rationale |
|---|---|---|---|
| TTFT p95 | ≤ 0.8 s end to end (≤ 2,048-token prompts); engine target 0.77 s after a 30 ms `[ILLUSTRATIVE]` frontend budget (gateway, auth, tokenization, network: 20–50 ms) | <fill> | <fill> |
| TPOT p95 | ≤ 50 ms | <fill> | <fill> |
| ITL p99 | ≤ 100 ms `[ILLUSTRATIVE]` | <fill> | <fill: users see stalls, not means> |
| Availability | 99.9 % | 30 days | <fill> |
| <fill: long-context tenant SLO> | | | |

## 3. Error budget and alerting

- Budget: <fill: 43.2 minutes of full unavailability per 30 days, or the equivalent failed-request count at forecast volume>
- Fast-burn page: <fill: burn rate ≥ 14.4 over 1 h (and 5 min confirmation)>
- Slow-burn ticket: <fill: e.g., burn ≥ 6 over 6 h>
- Budget policy: <fill: what stops when the budget is spent (feature launches, config experiments)>

## 4. Why rejection counts against availability

<fill: use configuration c4 as the worked example.>
