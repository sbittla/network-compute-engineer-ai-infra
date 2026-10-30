# Test Plan — Telemetry Pipeline

| ID | Level | What is tested | Input | Expected result | Evidence | Tier |
|---|---|---|---|---|---|---|
| T-01 | unit | Leaf CLI parser handles column-count mismatch | crafted text | raises ValueError | test output | L1 |
| T-02 | unit | 32-bit wrap vs 64-bit reset | crafted pairs | wrap delta / None | test output | L1 |
| T-03 | unit | Timestamp decoding for all three encodings | crafted samples | identical UTC instants | test output | L1 |
| T-04 | integration | Full bundle parse | data/ | 267,264 samples, 44 devices | checker | L1 |
| T-05 | system | Detection on supplied capture | data/ | recall 1.0, precision ≥ <fill> | checker + results table | L1 |
| T-06 | system | Persistence and threshold sweeps | data/ | table in false-positive analysis | results-table.csv | L1 |
| T-07 | system | Your additional injected scenario | extended capture | detected, no new FP | results-table.csv | L1 |
| T-08 | system | Real NIC counters parse | L2 host dump | all expected canonical counters present | dump + manifest | L2 |
| T-09 | system | Incast with ECN disabled on lab switch | L3 lab | ecn_misconfig-type alert within <fill> s, ≥ 5 repetitions | manifest + results | L3 |
| <fill> | | | | | | |

Entry criteria: <fill>. Exit criteria: <fill>. What would block release of the rules to production
on-call: <fill>.
