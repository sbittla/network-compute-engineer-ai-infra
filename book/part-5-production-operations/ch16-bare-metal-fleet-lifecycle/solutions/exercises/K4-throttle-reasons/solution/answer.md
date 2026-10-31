# K4 — SW Power Cap versus SW Thermal Slowdown

**Failing reason: `SW Thermal Slowdown: Active` on GPU 6.** The acceptance policy fails HW/SW
thermal slowdown and HW power brake (`THERMAL_THROTTLE`, Table 16.4: "No thermal/power-brake
slowdown; max < 87 °C"). Thermal slowdown means the GPU lowered its clocks because it is too hot,
so in a synchronous job every step waits for GPU 6.

**Why `SW Power Cap` on all eight GPUs is normal.** Burn-in deliberately drives the GPUs to their
power limit (700 W on an H100 SXM). The power controller then trims clocks to stay at the limit;
that is the GPU working as designed, and it shows on every GPU equally. A reason that is present on
all eight GPUs under full load is a property of the workload; a reason present on one GPU is a
property of that slot. (Bitmask view: `0x4` SW Power Cap, `0x20` SW Thermal Slowdown.)

**Plausible physical causes for GPU 6 (any two):**
- a failed or slow fan, or an airflow obstruction in front of that GPU's slot;
- a missing blanking panel or rack hot-air recirculation raising the local inlet temperature;
- poor heatsink contact (thermal interface material) after shipping or a repair;
- high rack inlet temperature (facility side), which usually affects more than one GPU.

**Next step.** Compare GPU 6's temperature with its peers at the same inlet temperature, read BMC
fan RPM and inlet sensors, rerun burn-in after the fix; do not enable the node meanwhile.

**Common wrong answer:** failing the node for `SW Power Cap` (≈ 60 % of GPUs in the lab data show
it as a distractor). Source: Section 16.5 ("Thermals and burn-in"); lab planted fault orion-n27.
