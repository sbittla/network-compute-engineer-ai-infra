# Editorial Review — Capstone A

**Independent score history:** iteration 1 = 9.30 (fail) → iteration 2 = 9.475 (fail: A2-01 major). Author iteration 3 fixes
(below) address the iteration-2 findings; awaiting independent re-review.


| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.000 | Not met (findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.475 | Not met: weighted score just under 9.5 (see note) |

Scored against [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md), reading D5 as "templates,
milestones and grading assets" for a capstone. The checker was validated with
`python scripts/validate_labs.py capstone-a`: the solution passes, the starter fails gracefully, and the data
regenerates byte-identically.

## Scores by dimension (latest)

| Dim | Weight | Iteration 1 | Iteration 2 |
|---|---|---|---|
| D1 | 20% | 9.0 | 9.5 |
| D2 | 15% | 9.0 | 9.5 |
| D3 | 15% | 9.0 | 9.5 |
| D4 | 15% | 9.0 | 9.5 |
| D5 | 10% | 9.0 | 9.5 |
| D6 | 10% | 9.0 | 9.5 |
| D7 | 5% | 9.5 | 9.5 |
| D8 | 5% | 8.5 | 9.0 |
| D9 | 5% | 9.0 | 9.5 |

Note: D8 stays at 9.0. The capstone supplies failure-analysis and facility-handoff templates, and the exemplar shows the drain policy, but there is no stand-alone runbook-excerpt template for Capstone A. The outline does not require one for A. The weighted score is just under the 9.5 gate for that reason, and this is recorded rather than inflated.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| A-1 | major | starter-kit/check.py | DataFrame truthiness in a cache `or` expression raised ValueError | Replaced with an explicit `_cables()` cache helper |
| A-2 | major | check 16 | Expected sustained IT power 334.12 kW was a hand error | Recomputed: 8 x 34.0 + 2 x 8.336 + 16 + 5.45 = 310.12 kW; formula shown in the message |
| A-3 | major | all files | Rack/node names did not follow the canonical names (G0x, orion-gpu-NN) | Renamed to rack-NN and orion-nNN; data regenerated; hostfile parser updated |
| A-4 | minor | README scenario | 'hall with 13 rack positions' contradicted the 15 positions in facility.yaml | Reworded: 13 racks allocated across rows A, B and D |
| A-5 | major | EXEMPLAR, acceptance plan | Busbw floor and optic Rx thresholds not aligned with docs/VERIFIED_FACTS.md | Added ~350+ GB/s busbw (per rail = busbw/8) and DR4 warn -4 dBm / critical -5.9 dBm; assumption A-04 notes that 0.80 is conservative |
| A-6 | minor | catalog notes | Switch capacity and frontend oversubscription not stated per VERIFIED_FACTS | Notes now say 25.6 Tb/s in use and frontend 3:1 by ports, 1.5:1 by bandwidth |
| A-7 | minor | acceptance-plan.csv | Unquoted commas produced a 12-column row | Quoted; every template CSV parses with a constant column count |
| A-8 | minor | EXEMPLAR section 4 | Break-even and ECMP Monte Carlo figures needed an independent check | Re-derived: break-even 2.94; Monte Carlo (seed 7, 20,000 trials) reproduced 4.83 / 3.34 / 2.06 / 1.21 |

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
| A-01 | major | DP exposure used a fixed 30 % overlap with PP; VERIFIED_FACTS says only a ≈ 70 ms window | Model is now max(0, T_DP − 0.07 s) for PP > 1 (PP send/recv assumed hidden in 1F1B); the 30 % fraction is kept only for FSDP and labelled a variation. Baseline exposure 0.121 s (A) and 0.313 s (B, launcher order). Checker 13, assumptions A-05, guide (penalty 1.1–2.1 %) and exemplar updated |
| A-02 | minor | Guide P2 distance wording | Now reads 50.8 m routed, 55.9 m with 10 % slack → 70 m stock |
| A-03 | major | No runbook | Added templates/runbook.md: rail/ToR-leaf failure and rack-05 power-cap event, with read-only first steps, owners and approvals; linked from the README |
| A-04 | minor | ECMP Monte Carlo lacked QP sensitivity | Added 2-sub-flow rows (3.94 / 1.54) and the NCCL_IB_QPS_PER_CONNECTION / multi-channel explanation |
| A-05 | minor | 50 m MM reach unlabelled | Catalog note and guide label it an [ILLUSTRATIVE] site policy; OM4 module reach ≈ 70–100 m |
| A-06 | minor | 24 + 8 default split and no-spares rule (REFERENCE_CLUSTER) not stated | Scenario now states the split, that a full-size run borrows inference nodes, and that any spare pool is a priced variation; failure template adds DP = 7 and the 900 s restart cost |

### Author self-review, iteration 3 (after fixes)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 3 | 2026-10-30 | Author self-review after independent review 1 | 9.50 | Met, pending independent re-review |

Scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.5. `python scripts/validate_labs.py` passes for this package (solution, graceful starter,
no-generator release check, docs). Every number changed by these fixes was recomputed from the reference
implementation, not edited by hand.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score: **9.475 (fail: A2-01 major)**.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| A2-01 | major | RB-1 offered DP = 7 for both options; wrong for option A, where a rail-leaf loss removes rail R from all 32 nodes | Split into RB-1a (option A: wait for repair / checkpointed restart on 7 rails excluding mlx5_R via NCCL_IB_HCA, ≈ 12.5 % less inter-node bandwidth, PXN cross-rail validation / take the job down) and RB-1b (option B: one replica lost, DP = 7 restart or wait). Viva Q1 expected answer and exemplar aligned |
| A2-02 | minor | PP exposure differs from Capstone C | Grading guide names it a deliberate per-capstone [ILLUSTRATIVE] choice and notes that it makes P7's PP-contention leg cost-free, with a bound for learners |

`python scripts/validate_labs.py capstone-a capstone-b capstone-c capstone-d`: 4/4 OK on every column
(solution, starter fails gracefully, no-generator, docs). Data regenerates byte-identically.
