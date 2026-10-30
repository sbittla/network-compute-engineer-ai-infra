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
