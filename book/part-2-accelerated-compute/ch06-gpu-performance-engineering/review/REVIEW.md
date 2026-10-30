# Editorial Review — Chapter 6

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.15 | Fail |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal; external review pending) |

**Independent score history:** 9.10 (iteration 1) → 9.50 (iteration 2, Pass). Author fixes for
iteration 2 findings are recorded at the end of this file; awaiting independent iteration 3.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| I-1 | 2026-10-30 | Independent reviewer | 9.10 | Fail |
| I-2 | 2026-10-30 | Independent reviewer | 9.50 | Pass |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | Ridge points, intensity formulas, MFU/HFU conventions, GPU-Util definition, clock-event naming and HW-vs-SW thermal ordering consistent with docs/VERIFIED_FACTS.md; ncu section/metric names and DCGM fields flagged version-sensitive. |
| D2 | Depth and production realism | 15 % | 9.5 | Levers-by-bound table, time-at-roof budgeting, power-cap incident, fleet-comparison confounding, regression gate. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Ceiling → classification → action; statistics motivated by data properties; worked example walks naive → evidence → cleaned decision. |
| D4 | Hands-on lab quality | 15 % | 9.5 | Real harness with manifest and raw samples; deterministic simulated sets with eight planted traps; checker independently recomputes bootstrap and quantiles; L2 extension with CUDA-event timing and telemetry. |
| D5 | Exercises and assessment | 10 % | 9.5 | Standard set plus outline exercises 6.11–6.13; key with arithmetic, bootstrap results, marking and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | The chapter is about this; run-level replication, A/A floor, practical threshold, pre-registered rule; laptop numbers explicitly not ORION evidence. |
| D7 | Cross-layer integration | 5 % | 9.5 | W-TRAIN MFU, Chapter 4 step decomposition, Chapter 5 ceilings, Facilities power cap (Chapter 21), staged change (Chapter 20); canonical node/rack names. |
| D8 | Operational realism and safety | 5 % | 9.5 | Safety callout on clock locking/power limits; gate runbook with safe actions and escalation. |
| D9 | Editorial polish | 5 % | 9.5 | Tables renumbered after insertion, captions and labels throughout, acronyms defined. |

Weighted = 9.50; lowest dimension 9.5.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | lab data | Flash-attention kernel time implied 1.85 PFLOP/s (above the BF16 roof) — an unintended anomaly. | Time set to 4,043 µs (55 % of roof); only the planted L2 case exceeds a roof. (It 1) |
| F2 | Major | lab data | Thermal trap jumped 65 → 88 °C in one iteration — physically implausible. | Temperature now ramps 70 → 86 °C before `sw_thermal_slowdown`; all statistics recomputed. (It 1) |
| F3 | Major | manuscript | Word count 6,772 < 7,000. | Added "From classification to action" (levers by bound, fusion arithmetic, time-at-roof budget); 7,276 words. (It 1) |
| F4 | Minor | lab/check.py | Dead code in the reference bootstrap helper. | Removed. (It 1) |
| F5 | Major | manuscript §6.5, key 6.7 | Clock-limiter naming and HW/SW thermal ordering had to match VERIFIED_FACTS. | Uses `clocks_event_reasons`, legacy names stated, HW slowdown "a few °C above" SW thermal; no HW slowdown shown at moderate temperature. (It 2) |
| F6 | Minor | key 6.14 | Ambiguous "12 % faster" arithmetic. | Both interpretations given (0.48 % / 0.43 %). (It 2) |

## Iteration history

**Author self-review, iteration 1 (9.15; D4 9.0, D3 9.0, D9 9.0).** Recomputed every roofline row (692,
544, 282, 45, 3.6, 57 TFLOP/s), MFU 0.400/0.533, bootstrap numbers; found F1–F4.

**Author self-review, iteration 2 (9.50).** Applied VERIFIED_FACTS and canonical names; re-ran the
solution (B −3.07 % [−3.85, −2.28] improvement; C −0.49 % [−1.02, −0.06] below threshold; floor 1.12 %);
checker 11/11 on solution, starter 0/11 with TODO lines; `python scripts/validate_labs.py ch06` OK.

## Release-gate items outstanding

- L2 validation of the protocol on an H100-class GPU; replace `[SIMULATED]` examples with `[MEASURED]` ones where possible.
- Re-verify ncu section names (`SpeedOfLight_RooflineChart`), DCGM field names and clock-event bitmask decoding for current releases.
- External review by a performance engineer and a statistician.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer weighted score: **9.10** (gate fail). All four validator columns passed and data was
deterministic; findings below were all addressed by the author.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Warm-up mean effect overstated (4 %). | (59 × 4 + 6)/60 = 4.033 ms = +0.83 %; lab case ≈ 1.9 %. |
| R-02 | Major | Throttle judged against 1,980 MHz max boost. | Generator now sustains ≈ 1,830 MHz; rule = clock < 95 % of peer median or thermal/HW events on > 5 % of iterations; device.yaml renamed max_boost/typical_sustained; §6.5, §6.9, §6.11 (ceiling 1,830/1,665 − 1 ≈ 9.9 %) updated. |
| R-03 | Major | MFU peak convention inconsistent. | MFU always vendor dense peak; clock-adjusted efficiency reported separately (§6.4 pitfall, key 6.18). |
| R-04 | Major | Bootstrap at n = 5–6; no permutation test or MDE. | Under-coverage stated; exact permutation test on run medians (B p = 2/252); significance from permutation, bootstrap as magnitude band; MDE subsection (σ_run 0.37 % → 0.65 % at n = 5); ≥ 10 runs near threshold. |
| R-05 | Major | `--runs` looped in one process. | `run_independent` re-execs the harness per run; manifest records pid; checker asserts distinct pids. |
| R-06 | Major (safety) | §6.11 lifted a maintenance power cap. | Driver A/B on uncapped drained nodes outside racks 07–08, or both arms at 500 W; cap never lifted. |
| R-07 | Minor | Clock lock above sustained. | Lock at or below sustained (1,755–1,830 MHz) and verify event reasons stay none (§6.5, lab README). |
| R-08 | Minor | Cliff's δ level unstated. | Both levels reported (B −0.95/−1.00; C −0.28/−0.67); key 6.17 rewritten. |
| R-09 | Minor | Exclusion on any event. | > 5 % share or peer-relative clock; sw_power_cap routine (planted on ≈ 3 % of iterations, kept). |
| R-10 | Minor | No reflection on symmetric exclusion. | Exercise/key 6.20 (keeping A3: C −0.44 %, band [−0.77, +1.19], p = 0.99). |
| R-11 | Minor | Missing point allocations. | Added for every key item (106 pts); 6.12 marking enumerated. |
| R-12 | Minor | Unlabelled figures; δ thresholds uncited. | Labels added; Romano et al. 2006 and Good 2005 cited. |
| R-13 | Minor | query-compute-apps form. | `--query-compute-apps=pid,process_name,used_memory --format=csv`. |
| R-14 | Minor | Driver version clash. | §6.11 new driver 575.57.08 `[ILLUSTRATIVE]` vs fleet 570.124.06. |
| R-15 | Minor | Checker accepted two decisions for C. | Asserts `below_threshold` only (C: −0.50 %, p = 0.026). |

**Author re-score after fixes:** weighted **9.55** (all ≥ 9.5; lowest D4/D6 9.5). Verified after fixes: `python lab/check.py
--impl solution` passes all checks, `--impl starter` reports TODO and exits 1, `python
scripts/validate_labs.py ch04 ch05 ch06` OK on all four columns, regenerated data byte-identical,
manuscript under 11,000 words. Outstanding: an independent re-review.

## Independent re-review (iteration 2) — 9.50, Pass

Recorded separately from the author's self-review. The reviewer confirmed all four validator columns
and determinism and re-checked the arithmetic. Findings and the author's fixes:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Minor | Warm-up factor quoted as 1.6× and 1.7×. | 1.6× everywhere (data 1.62×). |
| R2-02 | Minor | B4 clock quoted as ≈ 1,440/1,445 MHz. | 1,443 MHz throughout; ratio 1,826/1,443 = 1.27×. |
| R2-03 | Minor | Mean statistic vs median effect unexplained. | Sentence added; median-based p for C = 0.054, so marginal. |
| R2-04 | Minor | σ_run source unnamed; z-based MDE optimistic. | Source named (SD of 5 cleaned A run medians / mean); t (8 df) multiplier ≈ 3.2 → MDE ≈ 0.74 %. |
| R2-05 | — | Inference partition naming. | No change: REFERENCE_CLUSTER.md defines n25–n32 on racks 07–08 (coordinator confirmed). |
| R2-06 | Minor | Peer median computed per arm. | `clean_runs(..., peer_clock_mhz=)`; `compare()` passes the session-wide peer median over all runs of both arms; documented in §6.7, §6.9, Table 6.5 and manifest. |
| R2-07 | Minor | Key 6.17 run-level δ. | δ = −20/30 (25 of 30 run pairs favour C). |
| R2-08 | Minor | Re-review not recorded separately. | This section. |

After these fixes: solution checks pass, starter fails gracefully, `python scripts/validate_labs.py ch04 ch05
ch06` is OK on all columns, and manuscripts stay under 11,000 words. The next independent score is pending.
