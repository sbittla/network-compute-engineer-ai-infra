# Canary and Rollback Plan — Bundle `<fill: target bundle>`

> Template for Capstone E artifact 5. A change-advisory board should be able to approve or reject
> this plan without asking you a question.

## 1. Change summary

| Field | Value |
|---|---|
| From bundle(s) | `<fill>` |
| To bundle | `<fill>` |
| Components changed | `<fill: OS image, kernel, driver, NIC FW, RDMA stack, BMC FW …>` |
| Rollback bundle | `<fill>` and rollback method `<fill: reimage to previous image; firmware downgrade supported? tested?>` |
| Change ticket | `<fill>` |
| Maintenance windows | `<fill: per wave, aligned with which job boundaries>` |

## 2. Prechecks (all must pass before wave 0)

| # | Precheck | Evidence |
|---|---|---|
| 1 | Bundle validated in lab; report linked | `<fill>` |
| 2 | Rollback procedure rehearsed on a lab node | `<fill>` |
| 3 | Capacity floor agreed with Training Infra / Inference | `<fill: ≥ N schedulable nodes>` |
| 4 | Fresh checkpoint for running training jobs before each wave | `<fill>` |
| 5 | `<fill>` | `<fill>` |

## 3. Wave plan

| Wave | Nodes | Racks | Nodes out | Schedulable during wave | Start condition | Duration `[MODELED]` |
|---|---|---|---|---|---|---|
| 0 (canary) | `<fill>` | `<fill>` | `<fill>` | `<fill>` | prechecks pass | `<fill>` + soak `<fill>` h |
| 1 | `<fill>` | `<fill>` | `<fill>` | `<fill>` | canary promoted | `<fill>` |
| … | | | | | | |

Wave-size cap derivation: `<fill: min(⌊fraction × eligible⌋, schedulable − floor, per-rack rule) with numbers>`

## 4. Canary gate

| Metric | Baseline (source) | Threshold | Gate on worst canary or mean? | Why |
|---|---|---|---|---|
| Xid events during soak | 0 | `<fill>` | worst | `<fill>` |
| DCGM diag | pass | pass | worst | `<fill>` |
| NCCL bus bandwidth | `<fill>` | ≤ `<fill>` % regression | `<fill>` | `<fill>` |
| RDMA write | `<fill>` | ≤ `<fill>` % | `<fill>` | `<fill>` |
| Training step time | `<fill>` | ≤ `<fill>` % | `<fill>` | `<fill>` |
| Soak duration | — | ≥ `<fill>` h | all | `<fill>` |

Decision precedence: `<fill: abort > extend > promote, and why>`

Results for supplied scenarios:

| Scenario | Decision | Reasons (from `canary_decision`) | Would a mean-based gate agree? |
|---|---|---|---|
| S1 | `<fill>` | `<fill>` | `<fill>` |
| S2 | `<fill>` | `<fill>` | `<fill>` |
| S3 | `<fill>` | `<fill>` | `<fill>` |
| S4 | `<fill>` | `<fill>` | `<fill>` |

## 5. Abort conditions (any wave)

`<fill: numbered list — automatic triggers, who can trigger manually, what happens to in-flight nodes>`

## 6. Rollback procedure

`<fill: numbered steps with expected output at each step; how long; how you verify the rolled-back node (full or short-form acceptance?)>`

## 7. Capacity and cost

`<fill: GPU-hours of planned unavailability with arithmetic; impact on W-TRAIN parallelism (e.g. DP 8 → 6) and on the inference partition>`

## 8. Audit evidence produced

`<fill: which audit records each wave produces; how the CAB verifies the change afterwards>`
