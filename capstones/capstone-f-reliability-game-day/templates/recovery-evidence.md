# Recovery Evidence

> Template for Capstone F artifact 5. Every value `[SIMULATED]` unless from an L2/L3 run with a
> filled manifest (`[MEASURED]`).

## 1. Per-fault metrics

| Fault | Detect (s) | Mitigate (s) | Recover (s) | Recovered? | Restore step (durable) | Steps lost | Lost work (GPU-h) | Idle (GPU-h) | Total lost (GPU-h) |
|---|---|---|---|---|---|---|---|---|---|
| `<fill>` | | | | | | | | | |

MTTD = `<fill>` s, MTTR = `<fill>` s over `<fill: which faults; how unrecovered faults are treated>`.

## 2. Hypothesis verdicts

| Fault | Expected (detect / lost / recovered) | Observed | Verdict |
|---|---|---|---|
| `<fill>` | | | |

## 3. Restore validation

`<fill: for each restart — which checkpoint was restored, why it was the latest DURABLE one, and what a naive reading of "last checkpoint started" would have concluded>`

## 4. What-if re-runs

| Change (config / rules) | Fault | Lost GPU-h before → after | Recovery s before → after |
|---|---|---|---|
| `<fill: e.g. fast_fail=True>` | `<fill>` | `<fill>` | `<fill>` |
