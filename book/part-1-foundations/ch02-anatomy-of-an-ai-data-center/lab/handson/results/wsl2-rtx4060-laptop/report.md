# Chapter 2 hands-on: power, clocks and throttling

All values are `[MEASURED]` from `nvidia-smi --query-gpu=... -lms 100` on this machine unless labelled otherwise. ORION numbers are the chapter's `[ILLUSTRATIVE]` values.

## Platform

- Enforced power limit 80.0 W; maximum SM clock 3105.0 MHz `[MEASURED]`.
- Sampling: requested 100 ms, achieved median 110 ms (p95 137 ms) over 1119 samples `[MEASURED]`.
- Fields this platform does not report: fan.speed, power.limit, temperature.memory `[MEASURED]`.
- Changing the power limit permitted: False `[MEASURED]` (see power_controls.txt).

## Steps 2-4: phases (steady state, first 20 % of each phase skipped)

| Phase | Power median (W) | p95 (W) | Power / limit | SM clock (MHz) | Mem clock (MHz) | Temp start→max (°C) | SW power cap | SW thermal | Counter: power-cap time / phase |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| idle | 7.6 | 20.1 | 0.10 | 375 | 810 | 66→66 | 0 % | 0 % | 0 % |
| memory | 53.6 | 53.9 | 0.67 | 2535 | 8000 | 60→68 | 0 % | 0 % | 0 % |
| compute | 80.0 | 81.1 | 1.00 | 2250 | 8000 | 68→81 | 100 % | 0 % | 11 % |
| cooldown | 2.3 | 9.6 | 0.03 | 210 | 405 | 74→74 | 0 % | 0 % | 17 % |
| ramp_d025 | 9.9 | 10.5 | 0.12 | 585 | 810 | 61→61 | 0 % | 0 % | 0 % |
| ramp_d050 | 61.4 | 66.3 | 0.77 | 2520 | 8000 | 60→74 | 25 % | 0 % | 0 % |
| ramp_d075 | 73.5 | 75.7 | 0.92 | 2460 | 8000 | 73→78 | 98 % | 0 % | 0 % |
| ramp_d100 | 79.8 | 82.0 | 1.00 | 2340 | 8000 | 78→80 | 100 % | 0 % | 0 % |
| idle_end | 5.5 | 9.8 | 0.07 | 210 | 810 | 66→66 | 0 % | 0 % | 59 % |

## Step 5: where the power limit binds (GEMM duty-cycle ramp)

| Duty cycle | Power mean (W) | Power p95 (W) | SM clock mean (MHz) | SW power cap |
|---:|---:|---:|---:|---:|
| 25 % | 9.9 | 10.5 | 600 | 0 % |
| 50 % | 60.6 | 66.3 | 2495 | 25 % |
| 75 % | 73.3 | 75.7 | 2430 | 98 % |
| 100 % | 79.9 | 82.0 | 2343 | 100 % |

The limit binds from **75 % duty** `[MEASURED]`.

## Step 6: the step-boundary swing (1 s compute, 1 s idle)

- High 81.9 W, low 23.4 W, swing 58.5 W per GPU; low/high = 0.29 `[MEASURED]` over 8 cycles.
- 10-90 % rise: within one sample (0.11 s) `[MEASURED]`: the true edge is faster than a 100 ms sampler can resolve (Table 2.5 puts it at tens of milliseconds).
- ORION (Section 2.6): 700 W compute, 300 W exposed communication, low/high = 0.43, 400 W swing per GPU `[ILLUSTRATIVE]`.

## Findings

- Compute phase: 80.0 W at SM 2250 MHz, SW power cap in 100 % of samples `[MEASURED]`: the power limit binds.
- Memory phase: 53.6 W at SM 2535 MHz, SW power cap in 0 % `[MEASURED]`: the limit does not bind.
- Idle 7.6 W; peak temperature in the compute phase 81 °C, SW thermal slowdown in 0 % of its samples `[MEASURED]`.
- Violation counter for the compute phase: power-capped for 11 % of the phase, against the flag in 100 % of samples `[MEASURED]`. Where these disagree, the platform's counter is not measuring what Section 2.6 assumes; trust the flag and the clock.
