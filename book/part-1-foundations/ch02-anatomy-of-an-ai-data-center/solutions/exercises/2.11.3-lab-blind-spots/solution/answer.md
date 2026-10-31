# 2.11.3 — What the Chapter 2 lab cannot tell you

The lab is a static, steady-state model: it multiplies maximum powers, capture fractions and mass, and
checks them against limits. It cannot show **dynamics**: thermal transients when 256 GPUs enter a compute
phase together, the CDU's control loop (pump and valve response, overshoot of TCS supply temperature),
PSU behaviour under synchronized load steps, or where breaker trip curves sit relative to those steps.
It cannot show **real component performance**: the true coolant flow through each cold-plate branch,
fouling, real capture fraction at the hall's inlet temperature, or airflow recirculation in the row. And
it cannot show **workload behaviour**: actual power profiles of W-TRAIN steps and checkpoints, and how
power capping changes step time. "Fits" is necessary but not sufficient for "runs well". Close the gap
with a commissioning plan that includes workload-level burn-in (Section 2.8), measured node power
profiles (the L2 extension), and rack and CDU telemetry under load (the L3 extension).
