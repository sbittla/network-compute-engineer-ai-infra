# Rollout and Rollback Plan

## 1. What is being rolled out

<fill: model revision / engine version / configuration change; artifact digest; owner.>

## 2. Stages

| Stage | Traffic weight | Minimum duration | Gate to advance | Automatic rollback trigger |
|---|---|---|---|---|
| Shadow (optional) | 0 % (mirrored) | <fill> | <fill: output-quality diff> | n/a |
| Canary | <fill: e.g., 1 replica / 5 %> | <fill: ≥ 30 min and ≥ N requests> | <fill> | <fill: rollback_decision()> |
| Expand | <fill: 25 % → 50 %> | <fill> | <fill> | <fill> |
| Full | 100 % | — | — | <fill> |

## 3. Rollback gates (as implemented in `rollback_decision`)

| Gate | Threshold | Why this value |
|---|---|---|
| TTFT p95 above SLO | > 0.8 s | |
| TPOT p95 above SLO | > 50 ms | |
| Regression vs baseline | > 10 % on TTFT p95 or TPOT p95 | <fill: noise floor from your repetitions> |
| Error-budget fast burn | ≥ 14.4× | |
| <fill: quality gate for FP8 or new model revisions> | | |

## 4. Rollback procedure

1. <fill: shift router weight to the previous revision (seconds); keep the canary for diagnosis>
2. <fill: confirm SLIs recover; who is paged; what is recorded>
3. <fill: KV cache and in-flight requests: drain vs cut>

## 5. Communication and ownership

<fill: Inference on-call owns the rollout; SRE owns the gates; product informed for tenant impact.>
