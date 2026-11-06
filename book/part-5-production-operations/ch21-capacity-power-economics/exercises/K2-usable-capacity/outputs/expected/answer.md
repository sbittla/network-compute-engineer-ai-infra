# K2 — Usable capacity: worked solution

Source: manuscript Section 21.2. Inputs are the prompt's reserves `[ILLUSTRATIVE]`. The result is
`[MODELED]`. `solve.py` reproduces it.

**Formula.** The reserves act one after another on the GPUs that are left, so they multiply:

```text
usable = energized × (1 − maintenance) × (1 − repair/spares) × (1 − fragmentation)
```

**Substitution.**

```text
usable = 1,024 × (1 − 0.04) × (1 − 0.05) × (1 − 0.08)
       = 1,024 × 0.96 × 0.95 × 0.92
       = 1,024 × 0.8390
       = 859.2  →  859 usable GPUs
```

So 165 GPUs (16.1 %) of an energized 1,024-GPU cluster are not available to the scheduler's queue at
any moment. A capacity plan states the 859 and then applies the allocation target, for example 85 %,
to obtain plannable demand: 859 × 0.85 ≈ 730 GPUs.

**Why multiply.** A node in maintenance cannot also be counted as in repair. Fragmentation applies to
the GPUs that remain schedulable. Subtracting the percentages instead (1 − 0.04 − 0.05 − 0.08 = 0.83)
gives 849.9, which understates capacity by ≈ 9 GPUs. The error is small here but grows with larger
reserves.

**Common wrong answers**

- Applying the reserves to installed rather than energized GPUs. Stranded GPUs (Section 21.2,
  "Energized power") come off first.
- Rounding up to 860. A fraction of a GPU is not schedulable; whole nodes are, so a planner would
  often round down further, to 856 (107 nodes).
- Reporting 1,024 × 0.83: the additive shortcut.
