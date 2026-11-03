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

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.5 · D2 9.0 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.0 · D8 9.5 · D9 9.5 →
weighted **9.40** (gate fail: below 9.5). Counts: 0 blocker, 1 major, 6 minor. The reviewer reproduced every
number and passed `check.py` (solution 13/13, starter 0/13 with TODO lines). Author resolutions:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N06-01 | Major | No method for measuring achievable ceilings. | New §6.3 subsection "Empirical ceilings": memory roof (D2D copy and STREAM-style add/triad on buffers ≫ L2; `nvbandwidth` with a device-local caveat), compute roof (cuBLAS GEMM shape sweep via PyTorch, CUDA events), run under the §6.6 protocol, report fraction of vendor *and* measured roof, record clock/power state. `[ILLUSTRATIVE]` ORION example (2.95 TB/s, 700 TFLOP/s → 8,192³ GEMM 70 % vendor / 99 % measured; decode 85 % / 97 %), and the committed L2 run cited as `[MEASURED]` (RTX 4060: 229 GB/s = 89 % of 256; 28.7 TFLOP/s = 75 % of 38.2; thin GEMMs above the copy roof, so a measured roof is a lower bound). Exercise 6.11 extended: measured-roof fractions K1 90.4 %, K2 84.9 %, K3 97.2 %, ranking unchanged, K2 headroom 1.11 ms vs 2.95 ms; prompt (exercises.md and folder), meta (marking 3/3/2/2), answer, key, solve.py and outputs updated. Realism boundary and Summary point to it. |
| N06-02 | Minor | 100.7 MB cannot be L2-resident in a 50 MB L2. | Reworded: bytes are shape-derived; part of the input may be in L2 from the producer and part of the output in L2 write-back, but the 50 MB L2 (two ≈ 25 MB partitions) cannot hold 100 MB, so the figure overstates DRAM traffic; measure `dram__bytes_*`. Propagated to key 6.3, 6.3 meta/answer, key T7 row. Dataset name `bias_add_l2_resident` kept (renaming would change the lab's golden outputs; the name is now quoted as a label). |
| N06-03 | Minor | 6.15 budget does not fit. | Redesigned: one rotating node runs the A/B (6 + 6 interleaved), a fixed reference node runs the 6 + 6 A/A; end-to-end 12 × 2-min runs per node + 6 min setup = 30 min; 20 + 10 + 30 = 60 min × 16 GPUs = 16 GPU-h. Key, answer and solve.py (asserts runs and slot) updated; outputs regenerated. |
| N06-04 | Minor | σ_run uncertainty not quantified. | Added: with 5 runs (4 df), 95 % interval √(4/11.14) ≈ 0.60× to √(4/0.484) ≈ 2.9× the estimate; size from the upper end. |
| N06-05 | Minor | Training proxy on inference nodes unexplained. | §6.11 Symptom: the gate's single-node W-TRAIN proxy runs on every node class because full-size W-TRAIN borrows the inference nodes (Chapter 17). Chapter 12 reuse made concrete after the manifest (launch = run, `-w`/`-n`, median busbw per size; Exercise 6.12). |
| N06-06 | Minor | MPS unexpanded; mid-sentence expansions; ad-hoc table numbers. | MPS expanded; HBM and NCCL now expanded at first use in the Prerequisites paragraph; NIC expansion removed from §6.3; tables renumbered sequentially 6.1–6.11 (6.5a→6.6, 6.5b→6.7, 6.6→6.8, 6.6a→6.9, 6.7→6.10, 6.8→6.11); no other file referenced the changed numbers. |
| N06-07 | Minor | DCGM 4.7 GPU-Util deprecation missing. | Table 6.4 caption notes `DCGM_FI_DEV_GPU_UTIL` → `DCGM_FI_DEV_GPU_UTIL_RATIO` (0–1). |
| D2/D3/D6 advice | — | Confounders, strip plot, label clarity, p99 method. | Manifest gains `mem_clock_mhz`, `ecc_mode`, `row_remap_pending`, `pcie_link` with one paragraph on why; Figure 6.2 (ASCII strip plot of cleaned run medians); Figure 6.1 caption separates `[VENDOR-SPEC]` roofs from `[SIMULATED]` points; §6.7 states that medians/p95/p99 use numpy linear interpolation and that p99 from 55 iterations needs pooled or longer runs. D4 advice (an A/A trap that exceeds the floor) not taken: it would change the lab data and golden outputs; recorded for a later lab revision. |

Filler trimmed (opening abstract, worked-example Step 5, §6.8) to keep the manuscript within ≈ 7 % of its
previous length. Verification after fixes: see the test lines below.

- `python lab/check.py --impl solution` → 13/13 PASS; `--impl starter` → 0/13, TODO lines, no traceback.
- `python scripts/validate_labs.py ch06` → OK (solution pass, starter fails gracefully, no-generator pass, docs ok).
- `python scripts/copyedit_lint.py ch06-gpu` → 0 findings (the `--all` scope flags only the committed
  `lab/l2/results/*/report.md` files, which are measured outputs and are not edited by hand).
- Exercise outputs regenerated with `docker/harness/generate_outputs.py`; only 6.3, 6.11 and 6.15 outputs
  changed; `pytest docker/harness/test_package.py --pkg <ch06>` → 86 passed.

---

## Independent review r2 (2026-11-01)

Independent reviewer scores: D1 9.0, D2 9.0, D3 9.0, D4 9.5, D5 9.5, D6 9.0, D7 9.5, D8 9.5, D9 9.0 →
weighted **9.18** (gate fail; 2 major, 11 minor). Every finding was checked against the data and the
committed L2 bundle before changing anything. The committed `lab/l2/results/` files were not edited.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R06-01 | Major | RTX 4060 judged against a ceiling at `clocks.max.sm` = 3,105 MHz; the "75 %" and "same pattern as ORION" claims are artefacts. | Confirmed from `report.md`: the BF16 arm's median SM clock was 2,370 MHz. §6.3 now has "State the clock behind every compute peak": peak = SMs × FLOP/clock × clock; ORION's 989 TFLOP/s = 132 × 4,096 × ≈ 1,830 MHz; the laptop's 38.2 TFLOP/s ceiling at 3,105 MHz vs 24 × 512 × 2.370 GHz = 29.1 TFLOP/s at the sustained clock, so the 4096³ BF16 arm (28.4 TFLOP/s) is at 98 %, not 75 %; FP32 GEMMs sustained only 1,830 MHz. The "same pattern" sentence is gone. The Realism boundary's "60–80 % of tensor peak" is replaced by the honest statement (89 % of memory spec, 98 % of clock-adjusted BF16 peak). Lab README §8 gives both peaks and says how to read the bundle's "% of roof" column. `experiment.py` `report()` now also prints peaks at each arm's sustained clock (checked against the committed results.json: 29.1 TFLOP/s → 98 %, TF32 14.3 → 95 %, FP32 11.2 → 62 %); the committed bundle was not regenerated. Exercise 6.11 uses ORION `[ILLUSTRATIVE]` roofs, not the RTX numbers, so its key and outputs are unchanged by this. |
| R06-02 | Major | Session-wide peer-clock exclusion fails when the change alters the kernel's sustained clock; lesson only in the lab README. | New §6.5 Pitfall: clock as an outcome, the L2 evidence (BF16 2,370 vs FP32 1,830 MHz, session median between them, 0 of 8 baseline runs kept), the signature (one arm shifted as a block, all exclusions in it) and the pre-registered fix (lock clocks at or below sustained, or a per-arm peer clock plus clock reported as a secondary result). Table 6.5 Clocks row and §6.7 "Exclusions" point to it; §6.9 Step 3 notes the rule is valid here because every A and B run except B4 has a median clock of 1,825–1,827 MHz (verified from the CSVs). |
| R06-03 | Minor | Figure 6.1 points far from their coordinates. | Redrawn to scale by script (log–log, 10 columns and 5 rows per decade, ±12 % per cell), points lettered A–H with exact coordinates in the caption; the bias-add anomaly is now plotted above the memory roof. |
| R06-04 | Minor | Thin GEMMs "above the roof" may be L2-flattered; "take the max over kernels" can inflate the roof. | Accepted for L2 effects (small inputs L2-resident between iterations; 33.5 MB output ≈ 32 MB L2). Rejected the "compulsory-byte undercounting" part: compulsory bytes are a lower bound on traffic, so they can only understate bandwidth. Rule now: take the memory roof only from kernels whose footprint is ≥ 4–8× L2, confirmed with DRAM counters. |
| R06-05 | Minor | "40 % faster ⇒ 92 %" assumes a time reading. | Both readings given: 55 / 0.6 = 92 % (40 % less time) or 55 × 1.4 = 77 % (1.4× throughput). |
| R06-06 | Minor | Step 6 validates against a 7-day baseline (blocked design). | Now a pre-registered interleaved flag schedule on the same nodes, ≥ 10 segments per arm, with two groups of flag-off segments as the A/A check. |
| R06-07 | Minor | A3/B4 medians include warm-up. | Quoted after warm-up: A3 3.905 ms, B4 4.931 ms (verified from the CSVs); §6.5 says "median after warm-up". |
| R06-08 | Minor | Undefined acronyms. | GEMM, SIMT, MFU, HFU (objectives), TF32, cuBLAS, cuDNN, JIT, ILP, BLAS, MDE, CI expanded at first use; "GEMV" no longer used (the decode kernel is an m = 16 GEMM). |
| R06-09 | Minor | 6.13 exclusion cue is `sw_power_cap`, which the chapter calls routine. | Prompt now gives run 5's median clock (1,610 MHz vs 1,822–1,830 MHz, peer median 1,826); key, answer and meta say the exclusion rests on the clock (88 % < 95 %), not on the event, and list "excluded because `sw_power_cap` was logged" as a wrong answer. Folder prompt synced; marking.json regenerated. Numbers unchanged. |
| R06-10 | Minor | Draining training nodes on no-spare ORION has an unstated cost. | The default is now both drivers on one capped canary node; draining uncapped training nodes shrinks or pauses W-TRAIN and is limited to a maintenance or idle window. |
| R06-11 | Minor | README says 6.1–6.19; garbled warm-up sentence. | README now 6.1–6.20; sentence rewritten (A 4.912 ms = 1.2× steady state, iteration 0 ≈ 1.6×; B shows the same transient: 4.80 ms, 1.23×, verified). |
| R06-12 | Minor | Table 6.2's I = 372 uses counter bytes. | Clause added: 46.1 MB measured, 10 % above the 41.9 MB compulsory traffic (which would give I = 410). |
| R06-13 | Minor | Hard-to-find Romano citation. | Added Vargha & Delaney (2000) as an accessible source for the related *A* statistic (δ = 2A − 1), noting its thresholds are slightly lower. |
| D7 | — | Chapters 17 and 21 named but not linked. | Linked. |
| Length | — | — | Trimmed the worked-example discussion, §6.8 GPU paragraph, Realism boundary and summary; manuscript ≈ 10,100 words by `wc -w` (the to-scale figure adds several hundred `wc` tokens). |

Verification: `python lab/check.py --impl solution` → 13/13; `--impl starter` → 0/13, no traceback;
`python scripts/validate_labs.py ch06` → OK; `python scripts/copyedit_lint.py` → 0 findings in ch06;
outputs regenerated with `docker/harness/generate_outputs.py` (this round changed only 6.13's marking.json);
`pytest docker/harness/test_package.py --pkg <ch06>` → 86 passed.


## External PDF review fixes (2026-11-03)

An external reviewer of the concise PDF reported two problems in the statistics of Section 6.7 and the
worked example (concise Table 6.7 = full Table 6.8).

| # | Finding | Fix |
|---|---|---|
| X06-01 | `permutation_test` packed two statements per line with semicolons; in the PDF `total += 1` wrapped and read as if it were outside the loop. | Rewritten as plain multi-line code (one statement per line, no semicolons, every line ≤ 90 characters; `hits / len(splits)`), in the manuscript and in the concise chapter. The bootstrap block is rewritten the same way. |
| X06-02 | The C-vs-A row mixed statistics: the change was a ratio of medians of run medians (−0.50 %), the band bootstrapped that ratio ([−0.82 %, +0.18 %], straddling 0), while the test permuted a difference in means (p = 0.026); the text also quoted a median-based p = 0.054. | One primary statistic, fixed in the protocol (Section 6.7 new paragraph, 6.9 protocol, `lab/manifest.yaml`): the difference in arm means of the run medians, as a fraction of the observed baseline mean. The point estimate, the bootstrap band (replicates divided by the same fixed baseline mean) and the exact permutation test all use it. The median version is computed by the same code (`center=np.median`) and reported only as a labelled sensitivity analysis (`analysis.sensitivity_medians`). |

**Recomputed by running the published code on `lab/data`** (manuscript code blocks executed and compared with
`solutions/lab/analysis.py`):

| | Before | After (primary) | Sensitivity (median of run medians) |
|---|---|---|---|
| A/A | −0.07 % [−0.66 %, +0.48 %], p 0.57; floor 0.66 % | −0.14 % [−0.55 %, +0.29 %], p 0.57; floor **0.55 %** (bar still 1 %) | — |
| B vs A | −3.15 % [−3.49 %, −2.11 %], p 0.008 | **−2.89 %** [−3.33 %, −2.33 %], p 0.008 → improvement | −3.15 % [−3.49 %, −2.11 %], p 0.048 |
| C vs A | −0.50 % [−0.82 %, +0.18 %], p 0.026 | **−0.45 %** [−0.72 %, −0.12 %], p 0.026 → below threshold | −0.50 % [−0.82 %, +0.18 %], p 0.054 (not significant) |

Table 6.7 gains the arm means (4.0126 / 3.8968 / 3.9944 ms) beside the medians. **Decisions unchanged**
(B improvement; C real but below threshold). The text now says honestly that C's significance depends on
the statistic (median-based p = 0.054), while the action (do not ship C) does not. Derived numbers updated:
roofline cross-check 55 / 0.9711 = 56.6 %; summary bullets; Table 6.10 significance row.

Exercises and keys: 6.10 table and text; 6.13 recomputed on means of run medians (−1.14 %, [−2.69 %,
+1.14 %], p 0.36 → not significant; without run 5 −2.20 %, [−2.90 %, −1.42 %], p 0.002 → improvement;
decisions unchanged; median sensitivity −2.05 % p 0.041 / −2.45 % p 0.013 reported, showing why the
statistic is pre-registered); prompt "Evidence required" now names arm means (exercises.md and folder README
synced); 6.16/6.18 floor 0.55 %; 6.17 change 0.45 % (prompt synced); 6.19 meta; 6.20 recomputed (A3 kept:
−0.01 %, [−0.65 %, +0.93 %], p 0.99, not significant; with the rule −0.45 % [−0.72 %, −0.12 %], p 0.026).
`solve.py` for 6.13 and 6.20 assert the new keys; outputs regenerated with `docker/harness/generate_outputs.py`.

Tests added to `lab/check.py` (13 → 18 checks; starter reports them as TODO): `analysis.bootstrap_seed`
(fixed seed reproduces the band exactly, point independent of the seed, band follows the RNG recipe),
`analysis.permutation_exact` (hand case pooled 1..6, candidate {3,5,6}: p = 4/20; arm swap invariant),
`analysis.permutation_bounds` (identical arms and constant data p = 1; separated k + k arms p = 2/C(2k, k)
for k = 3, 4, 5; separated 2 + 3 arms p = 1/C(5, 3)), `analysis.sample_sizes` (2+2 … 7+7 and unequal sizes
match an independent brute-force count; p is a multiple of 1/C), `analysis.synthetic_shift` (±3 % shifts
with 0.4 % noise at 7 + 7 runs detected with the right sign, every 95 % band contains the true shift, seeded
null not significant). `analysis.bootstrap` now checks the mean-difference point; `analysis.decisions`
checks that each point lies in its band and that a significant improvement's band excludes 0. 6.10's
`lab_checks` lists the new checks.

L2 bundles (`lab/l2/results/`): not re-measured (GPU evidence). Their points and bands were computed with
the earlier ratio of medians; their decisions do not depend on it (effects −49 % to −76 % at the p floor;
A/A and no-op not significant). Stated in `lab/README.md` §8; `python scripts/hw_labs.py run ch06` refreshes them.

Verification: `python lab/check.py --impl solution` → 18/18; `--impl starter` → 0/18, no traceback;
`python scripts/validate_labs.py` → OK; `python scripts/copyedit_lint.py` → no ch06 findings;
`pytest docker/harness/test_package.py --pkg <ch06>` → 86 passed.
