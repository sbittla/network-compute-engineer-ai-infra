# 6.7 — `clocks_event_reasons` and thermal slowdown (model answer, 4 points)

Relies on manuscript Section 6.5 (clocks, power and thermal state). Field names `[VENDOR-SPEC, 2026-10]`.

**Definition (1 point).** `clocks_event_reasons` (nvidia-smi `--query-gpu=clocks_event_reasons.*`, NVML
"clocks event reasons") is a bit mask of the *active reasons the GPU is currently running below its maximum
clocks*: GPU idle, application-clock setting, software power cap (`sw_power_cap`), hardware slowdown
(`hw_slowdown`, including thermal and power-brake), software thermal slowdown (`sw_thermal_slowdown`), sync
boost, and others.

**Legacy names (1 point).** Older drivers called them "Clocks Throttle Reasons": `clocks_throttle_reasons.*`
in nvidia-smi, and DCGM's `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`, now `DCGM_FI_DEV_CLOCKS_EVENT_REASONS`.
Scripts written against the old names must be updated or aliased.

**Hardware vs software thermal slowdown (1 point).** *Software* thermal slowdown is the driver reducing clocks
once the GPU reaches its maximum operating temperature: a gradual, managed response. *Hardware* slowdown is a
protection mechanism that engages a few °C higher, or on external signals (power-brake from the chassis or
power supply), and cuts clocks hard. Ordering: SW thermal first, HW slowdown at a higher threshold. Seeing HW
slowdown *without* SW thermal slowdown at moderate temperature points to power delivery or chassis signals,
not heat. (Deduct 2 if HW slowdown is said to engage before SW thermal slowdown.)

**How to judge throttling (1 point).** Against peers' *sustained* clock under the same load (≈ 1,830 MHz on
ORION), not the 1,980 MHz maximum boost. `sw_power_cap` events on a few percent of iterations are routine under
heavy GEMMs and do not justify exclusion; Lab 6's B4 run (`sw_thermal_slowdown` on 48 of 60 iterations, median
1,443 MHz vs 1,826 MHz peers, −21 %) does `[SIMULATED]`.
