# False-Positive Analysis

## 1. Scoring definition

- Unit of scoring: <fill: one root-cause alert keyed by device, interface and fault class, de-duplicated>
- Ground truth: <fill: injected faults; how symptoms are treated>
- Why root-only scoring matters for on-call load: <fill>
- Time-aware matching: <fill: a page counts only if it fires within [onset, onset + tolerance]; pages before
  onset are FPs; re-pages of a matched fault are duplicates; report latency from onset>
- Hysteresis: <fill: how an open episode bridges short gaps (e.g. the leaf-r6 ECN episode across the 10:12
  checkpoint burst) without letting separated single-interval glitches open a page>
- Small-N limitation: with 5 positives, one FP drops precision to 0.83, so "≥ 0.9" means zero FPs. These
  numbers demonstrate mechanisms; they are not an estimate of production precision.

## 2. Persistence sweep `[SIMULATED]`

| Persistence (intervals) | TP | FP | FN | Precision | Recall | Worst-case detection latency |
|---|---|---|---|---|---|---|
| 1 | <fill> | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

## 3. Threshold sweeps `[SIMULATED]`

| Rule | Parameter | Values tried | Precision/recall at each | Chosen value and margin to the nearest failure |
|---|---|---|---|---|
| pfc_storm | rx_pause_per_s | <fill> | <fill> | <fill> |
| ecmp_imbalance | cv_threshold | <fill> | <fill> | <fill> |
| <fill> | | | | |

## 4. False-positive classes

For every FP your rules produced at any setting, classify it.

| FP class | Example (device, time) | Root reason | Fix (rule change, suppression, data quality) | Residual risk |
|---|---|---|---|---|
| Benign synchronized burst | <fill> | <fill> | <fill> | <fill> |
| Single-interval error glitch | <fill> | | | |
| Counter reset / wrap mishandled | <fill> | | | |
| Planned maintenance (device or link peer) | <fill> | | | |
| Symptom reported as root cause | <fill> | | | |

## 5. The trade-off

<fill: what you give up in detection latency for each step of precision; why your chosen point is
right for a fabric that carries synchronous training jobs (where a 3-minute delay may cost many
GPU-hours); what a false page costs in on-call trust.>

## 6. What this analysis cannot tell you

<fill: the simulated noise model; unseen fault types; production base rates.>
