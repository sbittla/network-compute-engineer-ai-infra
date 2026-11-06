# K7 — Transients: worked solution

Source: manuscript Section 21.7 ("Transient headroom") and Table 21.8. Inputs `[ILLUSTRATIVE]`;
result `[MODELED]`.

**Arithmetic.** In a synchronous job every GPU enters its compute phase and its
communication/checkpoint phase at the same time, so the per-GPU swings add:

```text
swing = 1,024 GPUs × (650 W − 400 W) = 1,024 × 0.25 kW = 256 kW
GPU power alternates between 409.6 kW and 665.6 kW every step (2.0 kW per node)
```

The 256 kW recurs at step frequency (seconds), and the full ramp from idle to peak happens at once
when the job starts, stops, or hangs. 256 kW is ≈ 8.7 legacy-rack budgets of 29.5 kW switching
together. At ORION-XL scale (4,096 GPUs) the same swing is ≈ 1.0 MW. The Llama 3 report describes
data-center-wide fluctuations of tens of megawatts from one large job.

**Mitigations with owners** (two needed):

| Mitigation | Mechanism | Owner |
|---|---|---|
| Power caps on every node of the job | Lowers the high end of the swing and the peak the feeds see | Platform |
| Staged job start/stop ramps (ramp over ≥ 60 s for steps > 500 kW, Table 21.8) | Turns an instantaneous step into a slope that UPS and generators can follow | Training Infra |
| Facility agreement on maximum step change; UPS/generator sizing and utility notification | Makes the site's absorbable step explicit and designs to it | Facilities |
| 10 % transient margin in rack planning | Keeps planned peaks below breaker and PDU limits during swings | Platform + Facilities |

**Caveat.** GPU power limits act over averaging windows of milliseconds to seconds. They do not bound
millisecond-scale excursions, which PSU and PDU sizing must absorb `[VENDOR-SPEC, 2026-10]`
(Section 21.8).

**Common wrong answers:** computing 1,024 × 650 W (the level, not the swing); treating the swing as a
one-off at start-up rather than repeating every step; naming a mitigation without an owner.
