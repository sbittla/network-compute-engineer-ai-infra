# Editorial Review — Chapter 4

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.05 | Fail |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal; external review pending) |

**Independent score history:** 9.18 (iteration 1) → 9.50 (iteration 2, Pass). Author fixes for
iteration 2 findings are recorded at the end of this file; awaiting independent iteration 3.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| I-1 | 2026-10-30 | Independent reviewer | 9.18 | Fail |
| I-2 | 2026-10-30 | Independent reviewer | 9.50 | Pass |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | CC 9.0 limits, H100 resources, pageable-copy semantics, GPU-Util definition and profiler commands checked against vendor documentation as known at writing; version-sensitive items (nsys report names, DCGM field IDs, ncu metric names, clock-event naming) flagged. Residual risk: exact nsys CSV column names in the L2 adapter. |
| D2 | Depth and production realism | 15 % | 9.5 | Mechanisms (Little's law, register allocation granularity, implicit syncs incl. boolean indexing and `cudaFree`), failure signatures table, runbook with thresholds, profiling safety in multi-node jobs. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Progression from execution model to timeline reading; worked example decomposes one step with every subtraction shown; Figures 4.1–4.3 teach hierarchy, the vector-add data path and the annotated trace. |
| D4 | Hands-on lab quality | 15 % | 9.5 | Realistic task, deterministic seeded data (byte-identical regeneration verified), independent checker (inclusion–exclusion for overlap, hand-derived occupancy cases), planted problems plus distractors, L2 extension with real commands. |
| D5 | Exercises and assessment | 10 % | 9.5 | Full standard set plus outline exercises 4.11–4.13 and the deliverable; each has evidence-required; key has arithmetic, marking and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | All quantitative claims labelled; SIMULATED vs MODELED distinction made explicit in the worked example and Exercise 4.16; validation step uses repeated runs with warm-up and IQR. |
| D7 | Cross-layer integration | 5 % | 9.5 | ORION HX8 used throughout; links to Chapters 3, 5, 6, 12, 15, 16, 18, 19, 22 and Capstone C. |
| D8 | Operational realism and safety | 5 % | 9.5 | Safety callout on ncu replay stalling collectives; dev-node reproduction; canary rollout in the case. |
| D9 | Editorial polish | 5 % | 9.5 | Acronyms defined on first use, figures and tables captioned, consistent units (GB/s vs Gb/s, MiB vs MB stated). |

Weighted = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×9.5 + 0.05×9.5 = **9.50**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript §4.5, §4.10 | Forward-pass GPU time stated as ≈ 17 ms; the trace gives 19.6 ms (17.6 ms is the CPU wait in `log_loss`). | Corrected to 19.6 ms in both places; distinction used as distractor D3 in the key. (It 1) |
| F2 | Major | lab/check.py | Loading the module via `spec_from_file_location` without registering it in `sys.modules` crashed `@dataclass` with a traceback (starter mode would violate the contract). | Module registered before exec; import errors reported as `FAIL import` without traceback. (It 1) |
| F3 | Major | lab/check.py | Windows console (cp1252) raised `UnicodeEncodeError` on "≈"/"—". | `sys.stdout.reconfigure(encoding="utf-8")` in checker and CLI. (It 1) |
| F4 | Major | lab/tools/generate_data.py | Copy durations were computed in seconds, not ns (all copies 1.5 µs). | Unit fixed; regeneration verified byte-identical. (It 1) |
| F5 | Minor | lab solution `find_gaps` | Gaps where the next op was submitted < 10 µs before the GPU went idle were labelled `dependency`. | Added `LAUNCH_LATENCY_NS` allowance; documented; Exercise 4.17 asks learners to critique it. (It 1) |
| F6 | Major | manuscript §4.12 | Worked example lacked the "annotated execution trace" the outline names as the deliverable. | Added Figure 4.3 with phase times from the data. (It 1) |
| F7 | Minor | manuscript §4.12 | GEMM share of kernel time stated as 69.9 %; recomputed 72.0 %. | Corrected. (It 1) |
| F8 | Minor | manuscript | Word count 10,088 > 10,000. | Trimmed redundant prose to 9,980 (wc -w). (It 1) |
| F9 | Minor | exercises-key 4.8 | Common-mistake note about the 1 KB smem reservation was confused. | Rewritten with a size where it changes the answer (45 KB). (It 1) |
| F10 | Minor | manuscript §4.14; lab READMEs | Node name `hx8-n07` and learner-facing generator references diverged from updated REFERENCE_CLUSTER.md / LAB_STANDARDS.md. | Renamed to `orion-n07`; generator marked "instructor copy only"; clock-event naming checked against VERIFIED_FACTS. Validator (incl. no-generator run) OK. (It 2) |

## Iteration history

**Author self-review, iteration 1 (score 9.05; D4 8.5, D1 9.0, D3 9.0).** Found F1–F9 by re-running
every number in §4.12 from the data, running both checker modes and the validator on Windows, and
re-deriving Table 4.3 by hand. All fixed.

**Author self-review, iteration 2 (score 9.50; all dimensions 9.5).** Re-verified: Little's law
(2.01 MB, 15.2 KB/SM), vector-add timings (0.27 ms kernel, 10.3 ms H2D), Table 4.3, wave quantization
(3.88 → 97 %; 0.48 → 48 %), worked-example decomposition (67,254,320 + 8,764,091 + 9,243,520 =
85,261,931 ns), layernorm roof fraction (725 GB/s, 21.6 %), projected step 63.2 ms (1.35×), achieved
382 → 515 TFLOP/s. `python check.py --impl solution` 11/11 PASS; starter 0/11 with TODO lines, exit 1;
`python scripts/validate_labs.py ch04` OK.

Command spot-check in this iteration: `nsys profile -t cuda,nvtx,osrt -s none
--capture-range=cudaProfilerApi --capture-range-end=stop`, `nsys stats --report … --format csv --output`,
`ncu --set full -k regex: --launch-skip --launch-count`, `ncu --section SpeedOfLight|Occupancy|LaunchStats`,
`nvcc -Xptxas -v`, `cuobjdump --dump-resource-usage`, `torch.cuda.set_sync_debug_mode`,
`torch.cuda.CUDAGraph`/`torch.cuda.graph`, `dcgmi dmon -e`. Lowest dimension 9.5. Gate: pass (internal).

## Release-gate items outstanding

- External review by a practising GPU performance engineer.
- L2 validation of the lab adapter against a real `nsys stats` CSV export (column names are version-sensitive).
- Re-verify H100-class values, DCGM field IDs and nsys report names against current vendor documentation at publication.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer weighted score: **9.18** (gate fail). All four validator columns passed and data was
deterministic; findings below were all addressed by the author.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Lab tool savings (two-step mean, idle only) did not reproduce §4.12 (step 41 + kernel time). | Added Table 4.5 reconciling both bases per finding; key states both totals (20.47 vs 22.36 ms) and accepts 63–65 ms with the basis stated. |
| R-02 | Major | §4.14 cuda_api_sum counts (2,904 syncs, 88,412 launches) inconsistent with a two-step capture. | Rescaled to 48 syncs and 3,610 launches with matching time percentages. |
| R-03 | Major | "≈ 2 KB in flight" implied ≤ 13 % of roof vs 21.6 % measured. | 8 warps × ≈ 3.25 outstanding 128-B requests ≈ 3.3 KB ≈ 22 % in §4.7 and key 4.7. |
| R-04 | Major | Missing MIG/MPS/time-slicing, copy engines, UM page faults, NCCL SM sharing. | Added "Copy engines and bidirectional overlap" (§4.6), "Sharing a GPU" (§4.9), UM row in Table 4.4 (now five pathologies), NCCL-kernels-hold-SMs paragraph (§4.11). |
| R-05 | Minor | Warp allocation granularity omitted. | Added to the occupancy rule, solution, starter docstring, device.json and a checker case (32 thr / 96 regs → 20 warps); self-check answer updated. |
| R-06 | Minor | 12 AdamFunctor launches unexplained. | Explained (large params in foreach group; 120 small tensors in a per-tensor group). |
| R-07 | Minor | Launch latency range. | "several to tens of µs (≈ 3–8 µs on a fast host)". |
| R-08 | Minor | 724 vs 725 GB/s; register total; GELU %; snippet lacked final sync. | 725 throughout; 33 MiB ≈ 34.6 MB; GELU 83–84 %; `torch.cuda.synchronize()` added to the NVTX snippet. |
| R-09 | Minor | Fig 4.2 arrow order. | D2H enqueue and sync now precede "H2D complete". |
| R-10 | Minor | Deprecated sort key; outline phrasing; peak derivation. | `device_time_total` noted; rephrased; 528 × 1,024 × ≈ 1.83 GHz note added (verify). |
| R-11 | Minor | Dependency branch of find_gaps never exercised. | Planted a host-callback cross-stream wait (0.31 ms/step, no extra RNG draws); new STREAM_DEPENDENCY finding; checks assert 1 dependency gap/step and 5 finding codes; §4.12 and key updated (85.57 ms step). |

**Author re-score after fixes:** weighted **9.55** (all ≥ 9.5; lowest D2/D4 9.5). Verified after fixes: `python lab/check.py
--impl solution` passes all checks, `--impl starter` reports TODO and exits 1, `python
scripts/validate_labs.py ch04 ch05 ch06` OK on all four columns, regenerated data byte-identical,
manuscript under 11,000 words. Outstanding: an independent re-review.

## Independent re-review (iteration 2) — 9.50, Pass

Recorded separately from the author's self-review. The reviewer confirmed all four validator columns
and determinism and re-checked the arithmetic. Findings and the author's fixes:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N-01 | Minor | §4.5 "tens of microseconds" per op. | "several to tens of microseconds". |
| N-02 | Minor | §4.14 cuda_api_sum rows not sorted by Time %. | Sorted descending (launch 49.9 %, sync 41.1 %). |
| N-03 | Minor | Key Task 7 said "≈ 63 ms". | "63–65 ms with the basis stated (Table 4.5)". |
| N-04 | Minor | Runbook clock-event rule too blunt. | Thermal/HW reasons > 1 % of samples, or `sw_power_cap` with clock < ≈ 95 % of peers; DCGM field named. |
| N-05 | Minor | MPS metrics described as "sums". | "aggregate over all clients (capped at 100 %)". |

After these fixes: solution checks pass, starter fails gracefully, `python scripts/validate_labs.py ch04 ch05
ch06` is OK on all columns, and manuscripts stay under 11,000 words. The next independent score is pending.
