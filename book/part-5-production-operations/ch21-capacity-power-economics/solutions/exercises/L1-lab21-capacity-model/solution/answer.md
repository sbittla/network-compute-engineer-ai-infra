# L1 — Lab 21: reference results and marking

Sources: `lab/README.md` (tasks and rubric), manuscript Sections 21.2–21.9, and the reference
implementation `solutions/lab/capacity_model.py`. All outputs are `[MODELED]` from `[ILLUSTRATIVE]`
inputs. Completion is verified by the checker: `python check.py` must report **9/9 checks passed**.
The named checks are listed in `meta.yaml`, and their PASS lines are in `outputs/lab_checks.json`.

**Reference results**

| Task | Expected |
|---|---|
| T1 plan hygiene | 12 quarters after dropping the exact duplicate 2027Q3 row; a *conflicting* duplicate raises `ValueError` |
| T2 usable fraction | 0.97 × 0.922 × 0.95 = 0.8496; IT kW per GPU = 10.2 × 1.12 / 8 = 1.428 |
| T2 energizable | 420 / 800 / 1,500 kW → 288 / 560 / 1,048 GPUs (whole nodes) |
| T2 forecast | 2028Q2: 1,024 installed, 560 energized, 464 stranded; 2028Q3 usable 475.8 < required 494.1 → SHORTFALL; 2029Q4 870.0 < 964.7 |
| T2 order-by | first shortfall 2028Q3 → GPUs 2028Q1, network 2028Q2, facility power **2027Q3** |
| T3 TCO | $6.77M/yr; $3.02 nominal, $4.18 allocated, $4.75 useful per GPU-h |
| T4 designs | A 87 nodes, 442.3 units, 26.53 per $M, 395.6 per MW; B 62 nodes (power-bound; cooling would allow 87), 644.9 units, 31.36 per $M, 645.0 per MW |
| T5 power cap | 700 W: 2 per rack, 32.0; 650 W: 3 per rack, 47.52 (best); 4 per rack would need ≤ 347 W |
| T6 flags | STRANDED_GPUS 2028Q2, 2028Q3, 2029Q2; RESERVE_SHORTFALL 2028Q3, 2029Q4; PER_GPU_COST_MISLEADS B-liquid-nextgen |

**Decision memo, what a strong one says**

1. *Order-by:* commit facility power (phase 2 a quarter earlier) by 2027Q3. The 2028Q3 shortfall is
   power, not GPUs: 464 delivered GPUs are stranded, ≈ $3.1M of nominal capacity per quarter. As an
   in-quarter mitigation, a fleet-wide 550 W cap lets 800 kW energize 79 nodes (632 GPUs, ≈ 507
   effective usable), which barely closes the 494 gap (Section 21.9).
2. *TCO:* capex 55 %, support 18 %, power ≈ 4 %. Allocation 0.85 → 0.75 moves the useful cost +13 %,
   more than a 10 % server discount does (Table 21.2).
3. *Design:* B, because it wins per $ and per MW, but only if per-GPU throughput is ≥ 1.86×. Name the
   L2/L3 benchmark that de-risks this. B is power-bound, not cooling-bound.
4. *Guardrail:* in legacy racks, 3 nodes at 650 W, uniform per job, with Table 21.5 thresholds and
   owners.
5. *Assumptions register:* every input with label, owner and measurement method (for example the
   power curve via an L2 cap sweep, fragmentation via a quarter of scheduler logs).

**Deductions (from the key):** any recommendation that does not name the binding constraint; unlabeled
numbers; counting the duplicate row (+256 phantom GPUs); assuming liquid cooling binds Design B;
picking the throughput-per-kW optimum (≈ 500 W) as the cap.
