# W-INFER Serving Platform — Design Document

**Author:** <fill> · **Date:** <fill> · **Tier(s):** <fill>

> Master document for Capstone D. Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`,
> `[ILLUSTRATIVE]` or `[VENDOR-SPEC, YYYY-MM]`.

## 0. Summary (≤ 150 words)

<fill: recommended configuration, fleet size for the forecast, SLO compliance, $/M tokens, top risk.>

## 1. Problem statement

- Product requirement: <fill: chat model, tenants, traffic forecast with peak/mean>
- Constraints: <fill: HX8 nodes, budget, FP8 quality gate, long-context tenant>
- Success criteria: <fill: SLOs met at forecast peak with stated headroom; error budget policy; $/M tokens target>

## 2. Service architecture

<fill: Mermaid diagram of the end-to-end request path: client → API gateway (authN, rate limits) →
router / load balancer (tenant-aware) → serving replicas (tokenizer, scheduler, engine, KV cache) →
streaming response; plus model registry, config store, metrics/logs/traces, autoscaler. Caption it.>

| Component | Responsibility | Scaling unit | Failure mode | Mitigation |
|---|---|---|---|---|
| Gateway | <fill> | | | |
| Router | <fill: tenant isolation for long-context traffic> | | | |
| Replica | <fill> | <fill: TP group> | | |
| <fill> | | | | |

Architecture decision: [adr-serving-config.md](adr-serving-config.md).

## 3. Assumptions

[assumptions-register.csv](assumptions-register.csv)

## 4. Implementation and simulation boundary

| Claim | Evidence class | What would make it `[MEASURED]` |
|---|---|---|
| <fill> | | |

## 5. Capacity model

[capacity-model.md](capacity-model.md), [capacity-model.csv](capacity-model.csv)

## 6. SLOs and SLIs

[slo-sli-spec.md](slo-sli-spec.md)

## 7. Load-test plan and results

[load-test-plan.md](load-test-plan.md), [results-table.csv](results-table.csv)

## 8. Rollout and rollback

[rollout-rollback-plan.md](rollout-rollback-plan.md)

## 9. Cost analysis

[cost-analysis.md](cost-analysis.md)

## 10. Failure analysis

| Failure | Detection | Effect on SLIs | Mitigation | Recovery |
|---|---|---|---|---|
| One GPU in a TP group fails (Xid) | <fill> | <fill: whole replica lost> | <fill> | <fill> |
| KV-cache exhaustion under a long-context burst | <fill: preemption counter> | | | |
| Bad model or config release | <fill: canary gate> | | | |
| Router overload / hot tenant | <fill> | | | |
| <fill> | | | | |

## 11. Security considerations

<fill: tenant isolation (no cross-tenant KV/prefix-cache sharing), prompt/response logging policy and
PII, authN/Z at the gateway, rate limiting, model-weight integrity (signed artifacts), secrets for model
registries, GPU node isolation from the internet.>

## 12. Final engineering review

[final-engineering-review.md](final-engineering-review.md)
