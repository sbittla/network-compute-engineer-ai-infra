# Marking scheme: 6.7 clocks_event_reasons and thermal slowdown

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** definition, legacy names, ordering of thresholds.

| Criterion | Points |
|---|---|
| Definition: the active reasons the GPU runs below maximum clocks (power cap, SW thermal, HW slowdown, idle, application clocks, sync boost) | 1 |
| Legacy names: Clocks Throttle Reasons, clocks_throttle_reasons.*, DCGM_FI_DEV_CLOCK_THROTTLE_REASONS | 1 |
| SW thermal slowdown engages at the maximum operating temperature; HW slowdown a few degrees higher or on external power-brake signals (deduct 2 if reversed) | 1 |
| Throttling judged against peers' sustained clock (about 1,830 MHz), not the 1,980 MHz max boost; sw_power_cap is routine | 1 |
