# Expected Behaviour (Hypotheses) — written BEFORE the run

> Template for Capstone F artifact 2. Date this document before the game day. For every fault,
> predict detection, mitigation, recovery and lost GPU-hours, and show the arithmetic.

| Fault ID | Hypothesis (mechanism) | Expected first alert and time | Expected mitigation and time | Expected recovery time | Expected lost GPU-h (formula → value) `[MODELED]` |
|---|---|---|---|---|---|
| `<fill>` | `<fill: e.g. collective hangs; job fails at timeout; requeues onto spare>` | `<fill>` | `<fill>` | `<fill>` | `<fill: GPUs × (time since durable ckpt + time to resume)>` |

## Assumptions behind the predictions

| Parameter | Value | Source |
|---|---|---|
| Collective timeout | `<fill>` | simulator config / your lab config |
| Health-controller delay | `<fill>` | |
| Checkpoint interval, size, stall | `<fill>` | |
| Storage write / read bandwidth | `<fill>` | |
| Launch time | `<fill>` | |

## After the run (do not edit the predictions above)

| Fault ID | Verdict (`held` / `failed`) | Which prediction failed | Mechanism that explains the difference |
|---|---|---|---|
| `<fill>` | `<fill>` | `<fill>` | `<fill>` |
