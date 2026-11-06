# 2.1.4 — TDP versus peak power

Source: manuscript Section 2.6 ("Dynamic power: TDP, transients, and power capping").

**TDP** (700 W for an ORION GPU) is the *sustained* power the board and its cooling are designed to
dissipate, and it is the default power limit the GPU's controller regulates to over a control window. It
is an average, not a ceiling on instantaneous draw: when a dense kernel starts, current can exceed the
TDP-equivalent for microseconds to milliseconds before the power controller reacts.

**Who absorbs what:**

- *Microsecond excursions* are absorbed on the board: decoupling capacitors, the voltage-regulator
  stages and the PSU's hold-up capacitance. The facility never sees them.
- *Step-boundary swings*, when all 256 GPUs enter or leave a compute phase together at each training step
  or checkpoint (tens of milliseconds to seconds), pass through the PSUs to the rack PDUs, breakers,
  busway and UPS. That is why rack budgets carry a transient margin (10 % on ORION) and why breaker
  trip curves and UPS step-load ratings must be checked against synchronized load steps.

**Common wrong answer:** treating TDP as the maximum the GPU can ever draw, and so sizing circuits with no
transient margin.
