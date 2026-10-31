# M2 — Two designs: worked solution

Sources: manuscript Sections 21.4–21.5 (Tables 21.2a and 21.3); lab Task 4; `lab/data/designs.yaml`
and `assumptions.yaml` `[ILLUSTRATIVE]`. Results `[MODELED]`; `solve.py` writes `comparison.md` and
`sensitivity.csv`.

**Explicit assumptions.** 1.0 MW IT hall and 1.0 MW CDU capacity; 12 % fabric/storage overhead;
ladder factor 0.8496 × 0.85 × 0.88 = 0.636; A: 1.0× per GPU, 1:1 fabric, PUE 1.35 (air variation);
B: 2.2× per GPU, 2:1 spine → communication efficiency 1 / (1 + 0.15 × 0.5 × 1) = 0.930, PUE 1.20
(warm-water variation); TCO per Table 21.1a with staff scaled by nodes / 32; $0.09/kWh.

**Fit.** A: ⌊1,000 / (10.2 × 1.12)⌋ = 87 nodes (power). B: power ⌊1,000 / 16.02⌋ = 62, cooling
⌊1,000 / (14.3 × 0.8)⌋ = 87, so **power binds** at 62 nodes.

**Comparison table**

| Metric | A | B | B / A |
|---|---|---|---|
| Nodes / GPUs | 87 / 696 | 62 / 496 | 0.71 |
| Useful units (87 × 8 × 1.0 × 1.0 × 0.636; 62 × 8 × 2.2 × 0.93 × 0.636) | 442.3 | 644.9 | 1.46 |
| TCO per year | $16.67M | $20.57M | 1.23 |
| **Useful units per $M/yr** | **26.53** | **31.36** | 1.18 |
| Facility MW (sustained × 1.12 × PUE) | 1.118 | 1.000 | 0.89 |
| **Useful units per facility MW** | **395.6** | **645.0** | 1.63 |
| Cost per GPU-year | $23,950 | $41,463 | 1.73 |
| Cost per useful unit-year | $37,687 | $31,888 | 0.85 |

**Sensitivity: B's per-GPU throughput** (B's TCO and node count are unchanged)

| B throughput | 1.6× | 1.8× | 1.86× | 2.0× | 2.2× | 2.4× |
|---|---|---|---|---|---|---|
| B units per $M | 22.81 | 25.66 | 26.51 | 28.51 | 31.36 | 34.21 |
| Winner (A = 26.53) | A | A | ≈ tie | B | B | B |

**Sensitivity: electricity price** (both designs)

| $/kWh | 0.06 | 0.09 | 0.12 | 0.15 | 0.20 |
|---|---|---|---|---|---|
| A per $M | 27.01 | 26.53 | 26.08 | 25.63 | 24.92 |
| B per $M | 31.77 | 31.36 | 30.96 | 30.58 | 29.96 |
| B / A | 1.176 | 1.182 | 1.187 | 1.193 | 1.202 |

Energy is 5.3 % (A) and 3.8 % (B) of TCO. Even a 2.2× price change moves the ratio by only ≈ 2 % and
never flips the ranking. Higher prices slightly favour B, which uses less facility power.

**Break-even.** B's value scales linearly with per-GPU throughput x: 31.36 × x / 2.2 = 26.53 →
x = 2.2 × 26.53 / 31.36 = **1.86×** `[MODELED]`. A second risk: if B's network does not speed up with
compute, exposed communication ≈ 0.15 / (0.85 / 2.2 + 0.15) = 28 %, efficiency 1 / (1 + 0.28 × 0.5) =
0.88, and B ≈ 31.36 × 0.88 / 0.93 ≈ 29.6 per $M. B is still ahead.

**Conclusion.** B delivers 18 % more useful work per dollar and 63 % more per facility MW, despite
costing 73 % more per GPU. The decision rests on per-GPU throughput ≥ 1.86×. Measure it before
committing (R2).

**Common wrong answers:** comparing at equal GPU count; assuming cooling binds B; ranking on $ per GPU.
