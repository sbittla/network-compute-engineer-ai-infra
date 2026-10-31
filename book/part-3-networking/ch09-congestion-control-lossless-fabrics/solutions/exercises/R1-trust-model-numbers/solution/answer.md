# R1 — Which model number to trust (model answer)

Relies on lab README Task 7 (the documented configurations), the simulation results in
`solutions/lab/outputs/check_solution.txt` (`sim_compare_A_vs_B`: paused 862.8 → 113.6 µs, CNPs 0 → 60),
manuscript Section 9.6 (DCQCN rate rules) and "Realism boundaries". All numbers are `[SIMULATED]`.

The two numbers: pause exposure 862.8 / 113.6 ≈ **7.6×** lower with the template ECN profile (B), and
incast completion 1,256.8 / 960.0 ≈ **1.31×** (≈ 31 %) longer.

**Trust the direction and rough size of the pause-exposure reduction more.** It follows from a robust,
hardware-independent mechanism. With Kmin 150 KB, marking starts well below the 1,000 KB Xoff, so CNPs
cut sender rates before PFC engages. With Kmin 1,500 KB (A), marks begin only *after* Xoff, so PFC
carries the whole incast and the model shows 0 CNPs. Any real switch with those thresholds behaves the
same way qualitatively. The exact 7.6× depends on timers and buffer behaviour and will differ.

**The ≈ 31 % completion penalty is mostly an artifact of the model's simplified recovery.** The
model implements only DCQCN *fast recovery*. It has no additive or hyper increase, no byte counter, and
it uses fixed timers. Real NICs recover rate faster once CNPs stop, so the time spent below line rate,
and therefore the penalty, is likely **overstated**. NIC firmware defaults also differ
(`[VENDOR-SPEC, 2026-10]`).

Both numbers need **L3 measurement** (O3's A/B experiment) before anyone quotes them as properties of
ORION's hardware.
