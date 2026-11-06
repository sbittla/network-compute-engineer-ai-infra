# Marking scheme: T1 The afternoon slowdown in rack-04

Type troubleshooting · kind written · tier L1 · 20 points

**Evidence required:** Decoded bitmask; ranked hypotheses with discriminating tests; a root cause that explains *time of day* and *rack locality*; a validation measurement with a pass threshold; a lifecycle decision with justification.

| Criterion | Points |
|---|---|
| Decodes 0x24 = 0x20 | 0x04 (SW Thermal Slowdown + SW Power Cap); 0x4 alone is normal | 3 |
| Ranks rack-level airflow (FAC-2210) above node fan/heatsink fault and workload change, with reasons | 5 |
| A discriminating test for each hypothesis | 4 |
| Root cause explaining time of day and rack locality; safe facilities change; validation with thresholds (inlet ≤ 27 °C, no 0x20, p99/p50 ≤ 3 %) | 5 |
| Lifecycle decision: no fault drain/repair/RMA; steer or maintenance-drain against the rack, referencing FAC-2210 | 3 |
