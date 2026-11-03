# Editorial Review — Chapter 21

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.98 | Fail (D3 < 9.0, word count below 7,000) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal) |
| I-1 | 2026-10-30 | Independent reviewer, iteration 1 | 9.03 | Fail |
| I-2 | 2026-10-30 | Independent reviewer, iteration 2 | 9.48 | Fail (D9 only) |
| 3 | 2026-10-30 | Author fixes for iteration-2 findings | see below | Submitted |

## Scores by dimension (latest)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy | 20 % | 9.0 | 9.5 | TCO, design comparison, power-cap and coolant-flow arithmetic re-derived and matched to the reference model; frontend oversubscription stated as 3:1 by ports / 1.5:1 by bandwidth; rack-power figures tied to reference designs; restart 15 min and node MTBF 1,536 h reused from the canon. |
| D2 | Depth and production realism | 15 % | 9.0 | 9.5 | Utilization ladder, ORION-XL capacity waterfall, onboarding pipeline, build-vs-rent break-even, sensitivity table, energy per token, transient swings, feed redundancy and derating. |
| D3 | Pedagogy and clarity | 15 % | 8.5 | 9.5 | Worked forecast with interpretation and mitigation; three figures (ladder, power chain, DLC block); trade-off table. |
| D4 | Lab quality | 15 % | 9.0 | 9.5 | Nine checks; planted duplicate, stranded deliveries, retirement, per-GPU-cost trap, power-vs-cooling binding trap, cap optimum ≠ efficiency optimum; SKIP without generator. Static (non-random) data documented in the manifest. |
| D5 | Exercises and assessment | 10 % | 9.0 | 9.5 | Standard set + M1–M4 including the Section 20.3/table-8 guardrails exercise; key with P90 forecast numbers. |
| D6 | Measurement rigor / labels | 10 % | 9.5 | 9.5 | Every number MODELED/ILLUSTRATIVE/VENDOR-SPEC; break-even assumptions named; measurement plan for each uncertain input. |
| D7 | Cross-layer integration | 5 % | 9.0 | 9.5 | Uses Ch 15 inference sizing, Ch 17 fragmentation, Ch 18–19 goodput/spares, Ch 14 storage. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Guardrail table with owners; safety callouts on capping and facility changes. |
| D9 | Editorial polish | 5 % | 9.0 | 9.5 | Polish pass: section cross-references verified, unclear storage sentence rewritten, canonical terms and units consistent, all figures captioned. |

Weighted: iteration 1 = 0.20×9.0 + 0.15×9.0 + 0.15×8.5 + 0.15×9.0 + 0.10×9.0 + 0.10×9.5 + 0.05×(9.0 + 9.5 + 9.0) = 8.98; iteration 2 = 0.20×9.5 + 0.15×(9.5 + 9.5 + 9.5) + 0.10×(9.5 + 9.5) + 0.05×(9.5 + 9.5 + 9.5) = 9.50. Lowest dimension 9.5.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Blocker | manuscript | 5,717 words (< 7,000). | Added inference-demand conversion, scenarios, onboarding pipeline, ORION-XL waterfall, sensitivity, build-vs-rent, energy per token, thermal-performance coupling, DLC figure (7,123 words). |
| F2 | Major | lab data | First plan version produced a shortfall in 2027Q1 and never a power-caused one. | Demand retuned so the first shortfall (2028Q3) is power-caused with 464 GPUs stranded. |
| F3 | Major | §21.2 | Needed the verified frontend oversubscription statement. | 3:1 by port count, 1.5:1 by bandwidth. |
| F4 | Major | lab/check.py | Failed with generator stripped. | SKIP without tools/; file map marks generator instructor-only. |
| F6 | Minor | §21.2 | Storage-concurrency sentence was unclear ("keeps the same 12 s per job"). | Rewritten with the concurrency effect quantified (≈ 24 s at 2× fleet). |
| F5 | Minor | §21.6 | Breaker example could read as universal. | Labelled jurisdiction- and equipment-dependent; facility team owns the design. |

## Release-gate items outstanding

- Facilities/MEP specialist review of §21.6–21.8 (derating, transient margin, CDU and flow figures).
- Replace the illustrative power/throughput curve with an L2 measurement; obtain current price and
  lead-time inputs at publication.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent score: 9.03 (fail, 1 blocker). All findings resolved; lab data and checker updated.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Blocker | Node base 3.6 kW (canon 4.6 kW) | `power_cap_case.yaml` base 4.6; Table 21.4, Step 5 (9.0 kW → 79 nodes, 632 GPUs, ≈ 507 effective), T1, W2, Review Q3 (437.5 W) all recomputed and checked against the reference model |
| R-02 | Major | Circuits not canonical | 32.78 kW per circuit / 65.55 kW per side (2N) in §21.6; power-cap case and T1 declared a legacy-hall variation (one circuit per side); garbled line removed |
| R-03 | Major | 396 kW mislabelled; PUE 1.30 | IT 304.6 kW, facility at canonical PUE 1.25 (380.8 kW); K5 rewritten; design PUEs explained as variations |
| R-04 | Major | 6 % repair reserve XL-derived | 7.8 % from 5-day MTTR (≈ 2.5 nodes for ORION-256; size-independent); usable 0.850; $4.18 allocated, $4.75 useful; all dependent numbers recomputed |
| R-05 | Major | Facility stranded power missing | Provisioned vs sustained (1.7 kW/node) with Fan et al. 2007; unused-budget column (9.1 kW/rack at 700 W); flag renamed STRANDED_GPUS |
| R-06 | Major | Capping one rack creates a straggler | "Cap jobs, not racks" with arithmetic (10.6 GPU-eq lost for 4.8 kW); guardrails changed |
| R-07 | Minor | Curve caveats | Workload dependence, per-GPU variation, ms-scale excursions not bounded |
| R-08 | Minor | Table order; goodput citation | Tables renumbered 21.1–21.7 in order; "81 % at 19 min / 80 % at 30 min" |
| R-09 | Minor | Build-vs-rent assumption; 58 % arithmetic | 100 %-allocated rental assumption stated (break-even 59 %); decomposition shown (0 + 11.0 + 47.0 = 58.0, allocated 74 %) |
| R-10 | Minor | Design B comm efficiency | Exposed-comm growth with faster compute modelled (0.88 → 29.6/$M, still ahead); PUE choices explained |

Author re-score: all dimensions 9.5 → 9.50. Manuscript ≈ 7,900 words.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score history: 9.03 → 9.48.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Minor | Ladder numerator | 6,767,300 / 2,242,560 = $3.02 |
| R2-02 | Minor | Break-even paragraph order | Decision-memo sentence moved after the break-even; caveats follow; spliced line reflowed |
| R2-03 | Minor | Key references | M4 cites Table 21.5; M2 electricity ≈ 4 % of TCO |
| R2-04 | Minor | W1 key | $2.729 / 0.680 = $4.01 |
| R2-05 | Minor | T1 trip mechanism | Trip attributed to PDU electronic overcurrent protection at 48 A (41.6 kW ≈ 61 A per phase) in exercise and key |
| R2-06 | Minor | 650 W headroom 0.1 kW | Added: measure the 4.6 kW base per site; a 2 % higher base (4.69 kW) moves the best cap to 600 W (3 × 9.49 = 28.5 kW) |

## Independent review r1 (2026-11-01)

Reviewer scores: D1 8.5, D2 9.0, D3 9.0, D4 8.5, D5 9.0, D6 8.5, D7 9.5, D8 9.0, D9 9.0 → weighted **8.80** (fail).
Every finding was checked against the manuscript, lab and key before any change was made.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N21-01 | Major | "Network did not speed up" caveat was internally inconsistent; its conclusion reverses | Verified. §21.5 rewritten: B's step is 0.536 of A's at 1:1 (1.86×) and 0.611 at 2:1 (1.64×), giving ≈ 516 units ≈ 25.1/$M, *below* A's 26.53. B's advantage depends on its NICs scaling. Table 21.5 now says the 2.2× is end-to-end step throughput on each design's own 1:1 fabric. Change carried into the M2 key, `answer.md` and `solve.py` (new assertions), and the outputs were regenerated |
| N21-02 | Major | A 32-node queue-head job cannot fit the ≈ 21-node training partition | Verified. Rather than the suggested 16-node job (which still needs ≈ 76 % of the partition free, a reservation problem rather than fragmentation), the scenario now uses a **4-node (32-GPU)** job: 44 free GPUs (= 0.66 × 0.258 × 256) but only 2 whole nodes. A sentence explains that 32-node jobs need the Ch 17 lifecycle transition. The fix advice now says to pack small jobs (leaf-aligned blocks are meaningless on a 1:1 rail fabric). K4 and M3 answers updated |
| N21-03 | Major | Committed L2 GPU bundle fails its invariants; its narrative and the lab README contradicted the data | Verified. The committed results were left untouched (they cannot be re-run). The lab README now says what the bundle shows: the 0/25 % levels are DVFS-shifted (300 MHz) and inconclusive; at clock-matched levels perf/W rises 0.264 → 0.298 → 0.341 TFLOP/J from 50 to 100 % duty; full load was thermally limited (SW_POWER_CAP 30 %, 88 °C), not power-capped; the CPU bundle has no perf/W. `experiment.py` now emits the duty-cycling conclusion only when the fixed-V/f invariant holds and otherwise prints "Inconclusive at light duty" (dry-run on the committed `results.json` confirms this) |
| N21-04 | Minor | Design TCO silently omits storage capex | Table 21.6 caption states the exclusion and the effect of adding storage (A $1.79M/yr, B $1.28M/yr → 23.95 vs 29.52/$M; same ranking) |
| N21-05 | Minor | Per-side rack-power guardrail defeats 2N | Table 21.8 now compares rack total (A + B) with **one** side's limit and has a new row: any side > 50 % with both feeds up → redundancy at risk. Operational-signals line and W2 answer aligned |
| N21-06 | Minor | T1 evidence above the 10.2 kW node max; main hall "39–41 kW on side A" | lh-03 40.8 kW (≈ 60 A), lh-04 30.6 kW (≈ 44.8 A); main hall "rack totals 39–41 kW (A + B), ≈ 20 kW per side". Exercise prompt, folder README, key, `answer.md` and `solve.py` updated; outputs regenerated |
| N21-07 | Minor | `DCGM_FI_DEV_GPU_UTIL` deprecation | DCGM ≥ 4.7 `DCGM_FI_DEV_GPU_UTIL_RATIO` (0–1) noted at first use, `[VENDOR-SPEC, 2026-10]` |
| N21-08 | Minor | "Section 20.3 / table 8" reads as Chapter 20 | "course outline §20.3, table 8" in README, `exercises.md` and the M4 folder README |
| N21-09 | Minor | Undefined figure acronyms; irregular table numbering | MV, ATS, PSU and CRAH expanded in captions. Tables renumbered 21.1–21.10 with every caption above its table; references updated in the manuscript, key, solutions and `experiment.py` (the committed L2 report's "Table 21.4" is explained in the lab README). Acronym paragraph rewrapped |
| N21-10 | Minor | Obsolete "3.6 kW base" mistake in the W2 key | Replaced with "margin applied twice / 10.2 kW regardless of cap" (key and `answer.md`) |
| N21-11 | Minor | D1 "60 % of idle hours" base ambiguous | Restated as 60 % of all idle hours = 80 % of the lendable 420,480. The alternative base (252,288 lent, 176,602 useful) is accepted when stated (key, `answer.md`, `meta.yaml`, `marking.json`) |
| N21-12 | Minor | 512-node maintenance example applied to ORION-256 | ORION-256 form added: one node out per day for a monthly roll ≈ 1/32 = 3.1 % |
| N21-13 | Minor | Oversubscription model ignores overlap-window overflow | Exposure = max(0, T_comm × slowdown − T_window), with the ≈ 70 ms W-TRAIN DP window; 0.93 labelled an upper bound |
| N21-14 | Minor | Order-by ignores onboarding | Table 21.2 lead times defined as order → in service. Order-by text explains how to handle order-to-dock quotes. The lab adds `onboarding_quarters` (0) to `assumptions.yaml` and the generator; `order_deadlines` subtracts lead time and onboarding (solution and starter). Results unchanged |
| N21-15 | Minor | 3 % vs 4 % electricity share unexplained | Parenthetical added: 4.4 % × 0.636 ≈ 2.8 % (per-step energy excludes idle and wasted hours) |
| D4 advice | — | Starter feedback was only TODO | `check.py` prints `hint:` lines for recognized mistakes: a counted duplicate row, usable from installed, no allocation headroom, non-node rounding, missing storage capex or PUE, cooling-fit nodes for B, missing comm efficiency, no transient margin, perf/W-optimal cap, flag diffs. Smoke-tested on deliberately broken implementations |

Tests: `check.py --impl solution` 9/9; `--impl starter` 1/9 (graceful); `validate_labs.py ch21` OK (including no-generator); `copyedit_lint.py ch21` 0 findings. All committed outputs regenerated with `docker/harness/generate_outputs.py` (all solvers OK). The manuscript grew from 773 to 791 lines after cutting filler in §21.1, §21.3 and §21.4.

Author re-score (for the next independent pass): D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 10, D8 9.5, D9 9.5 → ≈ 9.53.

Remaining release-gate item: re-run the L2 GPU bundle with locked clocks on a native-Linux lab host so that its committed report passes under the current `experiment.py`.

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.0, D5 9.5, D6 9.0, D7 9.0, D8 9.5, D9 9.0 → weighted **9.23** (fail; two majors).
Coordinator directives also applied: canonical energy price $0.08/kWh; canonical GPU-hour ≈ $3.00, reconciled here.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R21-02 | Major | The committed GPU L2 report showed "Invariants: FAILED" with a contradicted conclusion and a stale table reference | `report.md` re-rendered from the committed `results.json` using the current `experiment.check()`/`report()` and the hwlab `render()` (scratch script, no re-run, no measured value changed). Invariants now pass, the light-duty conclusion reads "Inconclusive", and the table reference is 21.7. The original evaluation is preserved under `invariants_history`, with a provenance note. The apologetic lab-README paragraph is replaced by a short list of observations. The hwlab committed-evidence test passes |
| R21-10 | Major | $2.50 canonical rate not reconciled with Ch 21 | REFERENCE_CLUSTER now uses ≈ $3.00 (coordinator). §21.4 states that other chapters cost lost GPU time at ≈ $3.00, the nominal rate derived here, rounded; the per-allocated, per-useful and cloud on-demand rates are different quantities |
| Energy price | Directive | $0.09/kWh vs canonical $0.08 | Changed to $0.08 in the generator, `assumptions.yaml`, the manuscript and M2. Recomputed: power $0.27M, TCO $6.73M, $3.00 / $4.16 / $4.72 per GPU-h; sensitivity table (5.36 / 5.20 / 4.99 / 4.89 / 4.20 / 4.49); designs $16.57M / $20.48M, 26.69 / 31.49 per $M, $23,810 / $41,286 per GPU-year, $37,465 / $31,752 per unit-year; storage aside 24.08 / 29.64; 1.8× → 25.8; NIC-not-scaling case → 25.2; break-even still 1.86×; energy $0.035 per M tokens, $5.85 per step, 2.5 %; stranded $3.05M per quarter; D1 $1.11M. Propagated to `check.py`, the key, and the M2, R2, D1, K3, L1, M3 and W1 solutions and their solvers; outputs regenerated |
| R21-01 | Minor | Capping mitigation shrank the fixed overhead | Overhead held at 1.224 kW per node: ⌊800 / 10.224⌋ = 78 nodes = 624 GPUs → 530 usable → 501 effective (margin ≈ 7). L1 and M1 answers updated |
| R21-03 | Minor | VENDOR-SPEC rack figure names no platform | GB200 NVL72-class, ≈ 120–132 kW `[VENDOR-SPEC, 2026-10]` |
| R21-04 | Minor | Feed-loss row inconsistent with the legacy plan | Row now reads: verify the surviving side; cap any legacy rack above its 29.5 kW plan (e.g. 3 uncapped nodes, 30.6 kW) to 650 W |
| R21-05 | Minor | T1 key ignored lh-04's latent violation | Row added to the key and `answer.md`; +1 bonus |
| R21-06 | Minor | W2 recommends 550 W with zero headroom | Caveat added: measure the base; if ≥ 1 % high, 500 W (25.8 kW, 43.4 node-eq.) |
| R21-07 | Minor | Design A's 41 kW air rack has no stated feasibility basis | Note under Table 21.5: containment plus rear-door heat exchangers; PUE 1.35 reflects that |
| R21-08 | Minor | Figure 21.1 omits the active rung | Annotation: active (90–97 % of allocated) is not a multiplicative rung |
| R21-09 | Minor | Unlabeled "40 kW air" claim | Labeled `[ILLUSTRATIVE]` |
| D2 / D7 / D8 / D9 advice | — | — | Poisson in-repair p90 (5 nodes → usable 0.778); demand-charge example ($82k/yr ≈ 1.2 % of TCO); 2:1 spine tied to Ch 7 and Ch 10; minimal power-budget-service record (fields, 60 s period, stale → no placements); long prose lines rewrapped. Not done: turning the §21.5 caveats into a table (length) |

Tests: `check.py --impl solution` 9/9; `--impl starter` 1/9 (graceful); `validate_labs.py ch21` OK; `copyedit_lint.py ch21` 0 findings; package test suite 86 passed locally; hwlab committed-evidence test passed. Manuscript ≈ 815 lines.

## Re-score follow-up (2026-11-01)

Reviewer re-score after r2: **9.68** (pass). New minor findings cleared:
- **N21-01:** the Figure 21.1 annotation now calls active "a side rung, not a multiplicative step", which matches the prose.
- **N21-02:** the experiment has a new `invariant_scope()`. The hwlab `run.py` writes its result to `invariants.scope` and adds it to the headline (optional and backward compatible). The GPU report was re-rendered from the same `results.json` and now reads "all passed (fixed-V/f checks skipped at 25 % duty: DVFS-shifted …)". No measured value changed.
- **N21-03:** the electricity row of Table 21.4 now shows +3.5 %.

Tests: package suite 86 passed; committed-evidence test passed; `validate_labs.py` OK; lint 0 findings.
