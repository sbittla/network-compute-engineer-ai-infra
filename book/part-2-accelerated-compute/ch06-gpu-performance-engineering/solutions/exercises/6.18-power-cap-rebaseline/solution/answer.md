# 6.18 — ORION under a 500 W power cap (model answer, 3 points)

Relies on manuscript Section 6.5 (clocks, power) and Section 6.4 (MFU).

**What changes.** Sustained SM clocks fall under heavy GEMMs (power cap reached sooner), so achievable FLOP/s,
kernel times, step times and fractions of the *compute* roof all change; memory-bound kernels change less.
`sw_power_cap` events become frequent rather than routine (≈ 3 % today), so the exclusion rule's thresholds
need revisiting, and noise floors may change. The A/A floor (0.66 %), Lab 6 decisions and roofline fractions
are all baseline-specific.

**MFU.** Still computed against the vendor dense peak (989 TFLOP/s), so MFU falls; if you want efficiency
against what the capped GPU can achieve, report a separate, clearly named clock-adjusted efficiency alongside
MFU, never instead of it.

**Re-baseline.** New A/A floor; new reference runs per node under the cap; peer-clock medians recomputed;
manifests recording the enforced power limit (`nvidia-smi -q -d POWER`).

(≈ 145 words.)
