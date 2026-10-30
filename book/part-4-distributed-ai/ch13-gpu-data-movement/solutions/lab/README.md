# Lab 13 — Instructor Notes

Reference implementation: `telemetry_diag.py` (passes `python ../../lab/check.py --impl solution`).

## Planted causes (generator `tools/generate_telemetry.py`, seed 13)

| Planted cause | Ranks | Onset | Generator rule | Signature the learner must use |
|---|---|---|---|---|
| Data imbalance | 12 (`orion-n18`, GPU 4) | step 0 | tokens × 1.30 | Tokens z ≫ 6, clocks/temperature normal; compute ≈ 777 ms vs 600 ms |
| Thermal straggler | 37 (`orion-n21`, GPU 5) | step 20 (3-step ramp) | clock 1,980 → ≈ 1,530 MHz, temperature → ≈ 89 °C, power ≈ 575 W, `sw_thermal_slowdown` | Clock −22 %, thermal clocks-event reason, tokens normal |
| Rail retransmissions | local rank 2 on all 8 nodes (2, 10, …, 58) → `orion-be-leaf-r2` | step 30 | retransmissions ≈ Poisson(3,200) vs 1; transfer × 1.65 for everyone; tx bytes +12 % on rail 2 | Rail grouping; global transfer time up; burst rate down |
| Decoy | 51 (`orion-n23`, GPU 3) | always | temperature ≈ 84 °C, clocks normal, no reason | Must be rejected |
| Masking | 12 and 37 | steps 20+ | equal slowdown | Step time unchanged at step 20 — fixing one alone shows no gain |

`utilization.gpu` is ≈ 99.7 % everywhere by construction (NCCL kernels spin while waiting).

## Expected outputs

- `find_stragglers` → [12, 37]; `rank_onset` → 0 and 20; causes → data_imbalance, thermal.
- `rail_health` → rail 2 flagged, onset 30.
- `hot_not_throttled` → [51].
- `amplification(30, 59)` → 334 GPU-s, 17.3 %, ideal ≈ 827 ms vs actual ≈ 1,004 ms;
  `amplification(0, 19)` → 220 GPU-s, 18.6 %, ideal ≈ 749 ms.

## Grading notes

- Mean/standard-deviation z-scores happen to find ranks 12 and 37 here, but reports that do not
  justify robust statistics lose report points.
- Attributing rank 37 to "network" because its wait is 0 shows a misunderstanding: the slowest rank
  never waits.
- Learners who blame eight NICs individually for the rail problem miss the common-factor lesson.
