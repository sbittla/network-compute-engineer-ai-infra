# Load-Test Plan

> **Safety:** Dedicated, reserved capacity only. Never target production endpoints.

## 1. Objectives

<fill: validate the simulator's knee per configuration; measure TTFT/TPOT/throughput under identical
workload and hardware; find the max SLO-compliant load; exercise rollback gates.>

## 2. Workload

| Item | Value |
|---|---|
| Trace | <fill: arrival process, length distributions, tenant mix; reuse trace.csv's shape> |
| Load levels | <fill: 0.5×, 1.0×, 1.5×, 2.0×, 2.5× node load> |
| Duration per level | <fill: ≥ 10 min steady state after excluding warm-up and cool-down (the supplied traces are 15 min with 60 s excluded at each end)> |
| Warm-up | <fill: requests or minutes discarded> |
| Repetitions | <fill: ≥ 5 independent seeds/traces per level and configuration; report the median p95 with min–max across seeds> |

## 3. Environment (identical across configurations)

<fill: node, GPUs, driver, serving stack and version, model and revision, dtype, all engine arguments,
load generator and version, client location (same rack / same network path). Use the manifest fields in
starter-kit/manifest.yaml.>

## 4. Test matrix

| ID | Config | Load | Mix | Expected (from simulator) | Pass criterion | Status |
|---|---|---|---|---|---|---|
| LT-01 | <fill> | 1.0× | mixed | <fill> | <fill> | <fill> |

## 5. Metrics collected

<fill: client-side TTFT/ITL per request; engine metrics (running/waiting requests, KV-cache usage,
preemptions); GPU utilization and memory; error counts.>

## 6. Analysis method

<fill: detect instability first (queue/TTFT growing over the run, ρ ≥ 1) and report such points as UNSTABLE, not as a p95;
percentiles with spread across repetitions; ITL p95/p99 from per-token gaps next to mean-based TPOT; compare configurations only at matched load; report
simulated vs measured side by side, never merged.>

## 7. Exit criteria

<fill>
