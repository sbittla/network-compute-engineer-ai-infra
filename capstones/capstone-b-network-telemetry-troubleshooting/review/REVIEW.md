# Editorial Review — Capstone B

**Independent score history:** iteration 1 = 9.30 (fail) → iteration 2 = 9.325 (fail: B2-01 major). Author iteration 3 fixes
(below) address the iteration-2 findings; awaiting independent re-review.


| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.100 | Not met (findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.500 | Met |

Scored against [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md), reading D5 as "templates,
milestones and grading assets" for a capstone. The checker was validated with
`python scripts/validate_labs.py capstone-b`: the solution passes, the starter fails gracefully, and the data
regenerates byte-identically.

## Scores by dimension (latest)

| Dim | Weight | Iteration 1 | Iteration 2 |
|---|---|---|---|
| D1 | 20% | 9.0 | 9.5 |
| D2 | 15% | 9.5 | 9.5 |
| D3 | 15% | 9.0 | 9.5 |
| D4 | 15% | 9.0 | 9.5 |
| D5 | 10% | 9.0 | 9.5 |
| D6 | 10% | 9.0 | 9.5 |
| D7 | 5% | 9.0 | 9.5 |
| D8 | 5% | 9.5 | 9.5 |
| D9 | 5% | 9.0 | 9.5 |

Note: Ground truth is hashed in data/, and the generator (which encodes the faults) lives in tools/, which the student release removes.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| B-1 | major | tools/generate_data.py | NIC initial counters drawn from 1e5-1e9 gave healthy NICs ~6e8 CRC errors | Per-counter plausible starting ranges (NIC_INIT_RANGE) |
| B-2 | major | tools/generate_data.py | Burst injected before the ECN-misconfig multiplier produced a 750k/s pause burst on leaf r6 | Reordered the injections; burst values are now independent of the r6 fault |
| B-3 | major | EXEMPLAR section 4 | Claimed healthy-port pause p99.9 < 20/s; computed from the data it is ~760/s (burst-edge intervals) | Corrected with the real figure and its cause; burst peak 16,100/s; leaf-r7 CV 0.27 |
| B-4 | major | all files | Device names not canonical | Renamed to orion-be-leaf-rR, orion-be-spine-S, orion-nNN; ground-truth hashes regenerated |
| B-5 | minor | reference detect() | Evidence string printed 'nan' for NIC link degradation | Evidence lists only the counters present |
| B-6 | minor | README | Counter names must be real | NIC side uses only mlx5 ethtool/hw_counters names, marked VENDOR-SPEC 2026-10 with a verify note; switch formats declared vendor-neutral |

All findings above are resolved. No blocker or major finding is open.

## Release-gate items outstanding

- The L2/L3 procedures in `starter-kit/README.md` have not been run on hardware. Every hardware-facing
  number remains `[MODELED]`, `[SIMULATED]` or `[VENDOR-SPEC, 2026-10]`.
- External review by a practising GPU-cluster/network engineer (and, for Capstone A, a facilities
  specialist), per docs/RELEASE_GATES.md.
- Re-verify vendor flags, counter names and NCCL log formats against the releases current at publication.


## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer score: **9.30**, gate not met. The reviewer's findings differed from the gaps the
author had named in iteration 2. The author re-read docs/VERIFIED_FACTS.md (distributed-training
operations, FEC alerting, alert scoring, ITL vs TPOT) and docs/REFERENCE_CLUSTER.md (24 + 8 default
split, no spares) before fixing.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| B-01 | major | score() ignored time | Ground truth now carries onset and tolerance; detect() reports fired_ts; scoring matches pages fired in [onset, onset + tolerance], counts earlier pages as FPs, re-pages as duplicates, and reports latency from onset. Hysteresis (clear after 3 intervals) stops one fault from paging twice. The n17 page at 10:12 (persistence 1) is now a pre-onset FP |
| B-02 | major | Absolute fec_corrected 100k/s threshold | Healthy ports now correct ≈ 1.5e5 codewords/s (the old rule would page 512 ports). Paging uses FCS/uncorrectable; the corrected-codeword trend against each port's own baseline is an early warning; alert-rules.md has the pre-FEC BER / symbol-error-bin note |
| B-03 | minor | Wrap heuristic misreads clears | counter_delta takes a plausibility bound (max rate × dt from device_profiles); the guide's correct policy requires a discontinuity signal or the bound |
| B-04 | minor | Switch ECN-marked and NIC CE-received shared a name | Split into ecn_marked_p3 (switch egress) and ecn_ce_received_p3 (NIC NP) |
| B-05 | minor | n30 drained during W-TRAIN with 31 nodes continuing | Capture now follows the default split: W-TRAIN on n01–n24 (declared variation), n25–n32 inference; n30 is an inference node drained by the router |
| B-06 | minor | Precision ≥ 0.9 with N = 5 | README, checker and FP template state that this means zero FPs and note the small-N limitation |

### Author self-review, iteration 3 (after fixes)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 3 | 2026-10-30 | Author self-review after independent review 1 | 9.50 | Met, pending independent re-review |

Scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.5. `python scripts/validate_labs.py` passes for this package (solution, graceful starter,
no-generator release check, docs). Every number changed by these fixes was recomputed from the reference
implementation, not edited by hand.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score: **9.325 (fail: B2-01 major)**.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| B2-01 | major | Hysteresis filled gaps before checking persistence, so two glitches could page | _runs() is now a state machine: it opens only on `persistence` consecutive true intervals (fired_ts from the opening run), bridges gaps < 3 once open, and closes after 3 false. New check 10b: two separated glitches on one port produce no page. Starter spec updated; detect() tolerates missing counters. Results unchanged (5 TP, 0 FP; 195 FP at persistence 1) |
| B2-02 | minor | 10:12/10:15 hysteresis interaction undocumented | Viva Q0 in the guide and a hysteresis line in the FP template |
| B2-03 | minor | 1,024 not divisible by DP = 6 | The variation declares a 1,152-sequence global batch (192 per replica); the exemplar's DP 6 → 5 restart uses 960 with an LR adjustment |
| B2-04 | minor | Onsets in plain text | The guide states this is deliberate: onsets reveal no device or class and are needed to score timing in the student edition; graders check that reasoning comes from counters |

`python scripts/validate_labs.py capstone-a capstone-b capstone-c capstone-d`: 4/4 OK on every column
(solution, starter fails gracefully, no-generator, docs). Data regenerates byte-identically.
