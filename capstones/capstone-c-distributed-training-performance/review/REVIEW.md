# Editorial Review — Capstone C

**Independent score history:** iteration 1 = 8.95 (fail) → iteration 2 = 9.50 (pass). Author iteration 3 fixes
(below) address the iteration-2 findings; awaiting independent re-review.


| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.150 | Not met (findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.475 | Not met: weighted score just under 9.5 (see note) |

Scored against [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md), reading D5 as "templates,
milestones and grading assets" for a capstone. The checker was validated with
`python scripts/validate_labs.py capstone-c`: the solution passes, the starter fails gracefully, and the data
regenerates byte-identically.

## Scores by dimension (latest)

| Dim | Weight | Iteration 1 | Iteration 2 |
|---|---|---|---|
| D1 | 20% | 9.0 | 9.5 |
| D2 | 15% | 9.5 | 9.5 |
| D3 | 15% | 9.0 | 9.5 |
| D4 | 15% | 9.5 | 9.5 |
| D5 | 10% | 9.0 | 9.5 |
| D6 | 10% | 9.0 | 9.5 |
| D7 | 5% | 9.0 | 9.5 |
| D8 | 5% | 9.0 | 9.0 |
| D9 | 5% | 9.0 | 9.5 |

Note: D8 stays at 9.0. The operations content is a launcher preflight and a regression alert in the exemplar and report template; there is no separate runbook template. The weighted score sits just under the gate for that reason.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| C-1 | major | generator | Container image tag changed with each variant, confounding one-variable-at-a-time | One image for all variants; added an rdma_dev_in_container field; the stale-image run is the planted drift |
| C-2 | blocker | nccl_tests.csv | 8-GPU busbw 362 GB/s exceeded the ~257 GB/s ring ceiling; 16-GPU IB busbw 41.5 GB/s contradicted ~350+ GB/s multi-node (VERIFIED_FACTS) | Peaks now 240 (8 GPUs), 360 (IB) and 20 (socket); README states per rail = busbw/8 |
| C-3 | major | EXEMPLAR | Harness timing (41 ms) and the include-all sensitivity (1.10) were not computed | Re-ran: 22 ms median / 1.6 ms IQR (laptop CPU proxy); include-all speedup 1.128 with CI [1.049, 1.133] |
| C-4 | minor | variant names | 'rail_ib' implied a rail-mapping fix that the data does not model | Renamed to ib_gdr / ib_gdr_bucket |
| C-5 | minor | GRADING_GUIDE | Explain why baseline at 32 GPUs is not significantly slower | Added the PP-only arithmetic (~0.2 s against 3.5 % step noise) |

All findings above are resolved. No blocker or major finding is open.

## Release-gate items outstanding

- The L2/L3 procedures in `starter-kit/README.md` have not been run on hardware. Every hardware-facing
  number remains `[MODELED]`, `[SIMULATED]` or `[VENDOR-SPEC, 2026-10]`.
- External review by a practising GPU-cluster/network engineer (and, for Capstone A, a facilities
  specialist), per docs/RELEASE_GATES.md.
- Re-verify vendor flags, counter names and NCCL log formats against the releases current at publication.


## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer score: **8.95**, gate not met. The reviewer's findings differed from the gaps the
author had named in iteration 2. The author re-read docs/VERIFIED_FACTS.md (distributed-training
operations, FEC alerting, alert scoring, ITL vs TPOT) and docs/REFERENCE_CLUSTER.md (24 + 8 default
split, no spares) before fixing.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| C-01 | blocker | busbw/algbw confusion (8-GPU 'healthy' 237–239 GB/s busbw) | 8-GPU rows regenerated at ≈ 366–372 GB/s busbw (≈ 209–213 algbw); 257 GB/s is described as the ring algbw ceiling everywhere (starter README, benchmark plan T-02, profiler template, exemplar, guide §3 and failure pattern 5) |
| C-02 | minor | NET/Plugin wording pre-2.19 vs NCCL 2.23.4 | Plugin line removed; excerpts labelled [ILLUSTRATIVE], version-dependent |
| C-03 | major | 1 s overlap window / 30 % exposure | Generator uses the canonical ≈ 70 ms DP window (bucket variant +15 ms, labelled); all reference numbers recomputed; viva Q4 decomposes the 2.1 % loss |
| C-04 | major | Statistic unstated; no multiple-comparison control | Statistic stated (difference of means of run medians); holm() and compare_family() apply Holm across the 8 tests; repetitions raised to 8 so exact p can survive the correction |
| C-05 | minor | No runbook | templates/runbook.md: launcher transport preflight and scaling-regression procedure, linked from the README |

### Author self-review, iteration 3 (after fixes)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 3 | 2026-10-30 | Author self-review after independent review 1 | 9.50 | Met, pending independent re-review |

Scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.5. `python scripts/validate_labs.py` passes for this package (solution, graceful starter,
no-generator release check, docs). Every number changed by these fixes was recomputed from the reference
implementation, not edited by hand.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score: **9.50 (pass)**.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| C2-01 | minor | r0458 note did not quantify throttling | The manifest note (regenerated) reads: SW thermal slowdown clock-event reason in 100 % of sampled steps, SM ≈ 1,710 vs ≈ 1,830 MHz (−6.6 %). Exemplar and guide cite the data: median 19.22 s vs 17.96 s for peers (+7.1 %) |
| A2-02 (shared) | minor | PP exposure differs from Capstone A | Grading guide names the 50 % PP exposure as a deliberate [ILLUSTRATIVE] choice and explains its effect at 32 GPUs |

`python scripts/validate_labs.py capstone-a capstone-b capstone-c capstone-d`: 4/4 OK on every column
(solution, starter fails gracefully, no-generator, docs). Data regenerates byte-identically.
