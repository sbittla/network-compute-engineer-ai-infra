# M2 — Two designs: worked solution

Sources: manuscript Sections 21.4–21.5 (Tables 21.5 and 21.6); lab Task 4; `lab/data/designs.yaml`
and `assumptions.yaml` `[ILLUSTRATIVE]`. Results `[MODELED]`; `solve.py` writes `comparison.md` and
`sensitivity.csv`.

**Explicit assumptions.** 1.0 MW IT hall and 1.0 MW CDU capacity; 12 % fabric/storage overhead;
ladder factor 0.8496 × 0.85 × 0.88 = 0.636; A: 1.0× per GPU, 1:1 fabric, PUE 1.35 (air variation);
B: 2.2× per GPU, 2:1 spine → communication efficiency 1 / (1 + 0.15 × 0.5 × 1) = 0.930, PUE 1.20
(warm-water variation); TCO per Table 21.3 with staff scaled by nodes / 32; $0.08/kWh (canonical).

**Fit.** A: ⌊1,000 / (10.2 × 1.12)⌋ = 87 nodes (power). B: power ⌊1,000 / 16.02⌋ = 62, cooling
⌊1,000 / (14.3 × 0.8)⌋ = 87, so **power binds** at 62 nodes.

**Comparison table**

| Metric | A | B | B / A |
|---|---|---|---|
| Nodes / GPUs | 87 / 696 | 62 / 496 | 0.71 |
| Useful units (87 × 8 × 1.0 × 1.0 × 0.636; 62 × 8 × 2.2 × 0.93 × 0.636) | 442.3 | 644.9 | 1.46 |
| TCO per year | $16.57M | $20.48M | 1.24 |
| **Useful units per $M/yr** | **26.69** | **31.49** | 1.18 |
| Facility MW (sustained × 1.12 × PUE) | 1.118 | 1.000 | 0.89 |
| **Useful units per facility MW** | **395.6** | **645.0** | 1.63 |
| Cost per GPU-year | $23,810 | $41,286 | 1.73 |
| Cost per useful unit-year | $37,465 | $31,752 | 0.85 |

**Sensitivity: B's per-GPU throughput** (B's TCO and node count are unchanged)

| B throughput | 1.6× | 1.8× | 1.86× | 2.0× | 2.2× | 2.4× |
|---|---|---|---|---|---|---|
| B units per $M | 22.90 | 25.77 | 26.63 | 28.63 | 31.49 | 34.36 |
| Winner (A = 26.69) | A | A | ≈ tie | B | B | B |

**Sensitivity: electricity price** (both designs)

| $/kWh | 0.06 | 0.08 | 0.12 | 0.15 | 0.20 |
|---|---|---|---|---|---|
| A per $M | 27.01 | 26.69 | 26.08 | 25.63 | 24.92 |
| B per $M | 31.77 | 31.49 | 30.96 | 30.58 | 29.96 |
| B / A | 1.176 | 1.180 | 1.187 | 1.193 | 1.202 |

Energy is 4.7 % (A) and 3.4 % (B) of TCO at $0.08/kWh. Even a 2.5× price change (0.08 → 0.20) moves the ratio by only ≈ 2 % and
never flips the ranking. Higher prices slightly favour B, which uses less facility power.

**Break-even.** B's value scales linearly with per-GPU throughput x: 31.49 × x / 2.2 = 26.69 →
x = 2.2 × 26.69 / 31.49 = **1.86×** `[MODELED]`. A second risk: the 2.2× and the 0.93 assume B's NICs
keep exposed communication at 15 % of B's shorter step. If B's network does not speed up with compute,
B's step at 1:1 is 0.85 / 2.2 + 0.15 = 0.536 of A's (1.86×). At 2:1 the spine-crossing half of the
exposed 0.15 doubles: 0.386 + 0.075 + 0.150 = 0.611 → **1.64×** per GPU, useful units ≈ 496 × 1.636 ×
0.636 ≈ 516, ≈ **25.2 per $M, below A**. B's advantage depends on its NICs scaling with its compute, so
the benchmark must measure step time on B-class fabric. (0.93 is itself an upper bound: slowed
overlapped traffic can overflow its overlap window, Section 21.5.)

**Conclusion.** B delivers 18 % more useful work per dollar and 63 % more per facility MW, despite
costing 73 % more per GPU. The decision rests on per-GPU throughput ≥ 1.86×. Measure it before
committing (R2).

**Common wrong answers:** comparing at equal GPU count; assuming cooling binds B; ranking on $ per GPU.
