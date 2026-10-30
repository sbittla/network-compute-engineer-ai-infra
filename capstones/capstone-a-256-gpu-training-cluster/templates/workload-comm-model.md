# Workload and Communication Model — W-TRAIN on ORION-256

All values `[MODELED]` unless marked otherwise. Show substituted values, not just formulas.

## 1. Workload definition

| Parameter | Value | Source |
|---|---|---|
| Parameters, layers, hidden | <fill> | REFERENCE_CLUSTER §3 |
| Tokens per step | <fill: seq × global batch> | |
| Step FLOP | <fill: 6 × N × tokens> | |
| Compute time per step at MFU = <fill> | <fill> s | FLOP / (GPUs × peak × MFU) |

## 2. Parallelism scenarios

| Scenario | TP | PP | DP | Sharding | Parameters per GPU | Why consider it |
|---|---|---|---|---|---|---|
| baseline_3d | 8 | 4 | 8 | DP all-reduce | <fill> | <fill> |
| fsdp_dp32 | 8 | 1 | 32 | ZeRO-3 / FSDP | <fill> | <fill> |

## 3. Bytes per GPU per step

| Traffic | Formula | Substitution | Result |
|---|---|---|---|
| DP all-reduce (baseline) | 2(n−1)/n × S | <fill> | <fill> GB |
| FSDP (all-gather ×2 + reduce-scatter) | 3(n−1)/n × S | <fill> | <fill> GB |
| PP activations per boundary per direction | tokens/DP × hidden × 2 B / TP | <fill> | <fill> GB |
| TP all-reduce (inside NVLink, not on the fabric) | <fill> | <fill> | <fill> |

## 4. Rank layout and leaf contention

Explain how ranks map to nodes for `dp_contiguous` and `pp_contiguous`, and what the launcher's
`hostfile_job4471.txt` order does. Then fill:

| Option | Scenario | Node order | Scheme | DP contention | PP contention | Step time (s) | $/M tokens |
|---|---|---|---|---|---|---|---|
| A | baseline_3d | sorted | dp_contiguous | <fill> | <fill> | <fill> | <fill> |
| <fill: all combinations you analysed> | | | | | | | |

## 5. Sensitivity

| Effective contention on option B (FSDP) | Step time (s) | $/M tokens | vs option A |
|---|---|---|---|
| 1.0 | <fill> | <fill> | <fill> |
| 2.0 | <fill> | <fill> | <fill> |
| 3.0 | <fill> | <fill> | <fill> |
| 4.0 | <fill> | <fill> | <fill> |

Break-even effective contention: <fill> (show the algebra).

## 6. What the model leaves out

<fill: at least five effects, each with the direction it would move your conclusion.>
