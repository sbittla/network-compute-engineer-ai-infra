# Editorial Review — Capstone F: AI Infrastructure Reliability Game Day

**Independent score history:** 9.30 → 9.50 → 9.50 (iterations 1 → 2 → 3; PASS at iteration 3, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Author self-review, iteration 1 | 2026-10-29 | Author | 8.85 | FAIL |
| Author self-review, iteration 2 | 2026-10-29 | Author | 9.50 | PASS (internal) |

Rubric: [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md). For a capstone, D4 scores
the starter kit, simulator and checker; D5 scores templates, milestones and grading assets.

## Scores by dimension (latest — iteration 2)

| Dim | Weight | Score | Justification |
|---|---|---|---|
| D1 Technical accuracy | 20 % | 9.5 | Recovery mechanics (collective hang → timeout → requeue → durable restore), absence alerting, `for` semantics, netem/ip/systemctl/ipmitool/scontrol commands checked; simulator limits stated; parameters aligned with the canonical reliability assumptions (≈ 15-min restart overhead, per-node MTBF 1,536 h). |
| D2 Depth and production realism | 15 % | 9.5 | Overlapping faults, aborted in-flight checkpoints, restore at degraded bandwidth, control-plane outage delaying drains, spare exhaustion and missing return-to-service, alert fatigue. |
| D3 Pedagogy and clarity | 15 % | 9.5 | Hypothesis-first structure; Figures F.1/F.2; worked numbers reproduce simulator output to within 2 GPU-h; hints point at evidence without giving answers. |
| D4 Hands-on lab quality | 15 % | 9.5 | Given simulator is deterministic and documented; 11 checks incl. learner plan execution, false-positive budget, canonical detection, recorded-day analysis with targeted pitfall message; ≈ 9 s. |
| D5 Assessment assets | 10 % | 9.5 | Nine templates covering the seven outline artifacts and nine common sections; planted-finding table; expected numbers; failure patterns; oral questions. |
| D6 Evidence labelling | 10 % | 9.5 | SIMULATED vs MODELED kept apart throughout (e.g. fast-fail saving 28.8 GPU-h modeled and reproduced by simulation); unrecovered loss reported as lower bound. |
| D7 Cross-layer integration | 5 % | 9.5 | Links to Chapters 11, 12, 14, 16–21; return-to-service ties to Capstone E acceptance. |
| D8 Operational realism and safety | 5 % | 10 | Safety callouts, protected partition enforced by the checker, abort/rollback for every lab injection. |
| D9 Editorial polish | 5 % | 9.0 | Acronyms, captions, consistent units; some tables dense. |

Weighted: 0.90 × 9.5 + 0.05 × 10 + 0.05 × 9.0 = 8.55 + 0.50 + 0.45 = **9.50**. Lowest: D9 9.0.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F-01 | blocker | sim `_health_controller` | With `fast_fail`, the job was failed before the node was drained, so it was requeued onto the faulty node and hung again — fast-fail looked harmful. | Drain first, then fail; S1 now shows the modeled 28.8 GPU-h saving exactly. |
| F-02 | major | sim defaults, README §2/§9 | Restart overhead (≈ 13.4 min) and backlog frequencies did not match the canonical reliability assumptions added to REFERENCE_CLUSTER.md. | Launch + warm-up 280 s → ≈ 903 s ≈ 15 min; RB-03 uses 137 interruptions/yr (MTBF 1,536 / 24 nodes = 64 h); all expected numbers regenerated and re-verified. |
| F-03 | major | instructor/GRADING_GUIDE.md P1 | Alert counts on the recorded day mis-stated. | Recounted from the regenerated recording (8 of 11 `JobStalled`, 5 noise). |
| F-04 | minor | sim `requeue_blocked` | Logged twice at scheduler return. | Logged once per blocked episode. |
| F-05 | minor | starter header | Shell stripped inline code markup. | Fixed. |
| F-06 | major | sim, data, docs | Node names did not follow canonical `orion-nNN` / `rack-NN`. | Simulator, generator, checker, reference and docs renamed; data regenerated; 11/11. |
| F-07 | major | check.py, READMEs | Generator stripped from student release. | Dataset check SKIPs without `tools/`; learner docs mark the generator instructor copy only. |

## Release-gate items outstanding

- L2/L3 lab drills not executed; collective-timeout behaviour on real hardware unvalidated.
- External SRE review of the alert designs and postmortem template.
- Verify Chaos Mesh / LitmusChaos experiment names against current releases if learners use them.

## Independent review iteration 1 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 1 | 2026-10-30 | Independent reviewer | 9.30 | FAIL (major findings) |
| Author fixes, iteration 3 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-01 | major | README §2 | The partition layout differed from REFERENCE_CLUSTER without a declaration. | Added a "Variation from REFERENCE_CLUSTER" callout: n25–n26 fine-tune, n27–n28 spares, n29–n32 inference. |
| R-02 | major | README §2 | 17.4 s is the step time for 256 GPUs at batch 1,024. | Stated batch 768 (128 per replica, as DP 6 requires) with the full derivation; 17.4 s still holds, and 23.2 s at batch 1,024 is noted. |
| R-03 | minor | `detection_time`, checker | Alerts without a node label were credited to any fault. | A `job` label must name a job that this fault hung; the checker applies the same rule to the canonical scenarios. Recorded-day values are unchanged. |
| R-04 | minor | simulator `_on_restart_done` | Progress time was reset without a completed step. | `last_progress_t` is now kept, with an `awaiting_first_step` flag; progress age counts from the last real step. |
| R-05 | minor | simulator | Concurrent checkpoint writes each got full bandwidth. | Writes now share storage write bandwidth equally (rebalanced on start, finish, abort and storage change). Recorded results are unchanged because overlaps are short. |
| R-06 | minor | simulator docstring | Renaming left "orion-n25/n2" and "orion-n27/n4". | Fixed. |

Validation after fixes: `python scripts/validate_labs.py capstone-f` — solution pass, starter fails gracefully, no-generator pass, docs ok.

## Independent review iteration 2 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 2 | 2026-10-30 | Independent reviewer | 9.50 (PASS) | PASS |
| Author fixes, iteration 4 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-07 | minor | `detection_time`, checker | No upper bound on the scoring window. | Alerts count only inside [onset, onset + 2 × target] (`DETECTION_TOLERANCE_S`); the checker adds a case with an early and a late alert, and neither counts. Recorded-day values are unchanged. |
| R-08 | minor | README §9, guide P7 | Spare exhaustion lacked quantitative backing. | Poisson with the canonical 5-day MTTR: 0.375 failures/day × 5 ≈ 1.9 nodes in repair, P(≤ 2) ≈ 0.71, so two spares run out on ≈ 29 % of days. |

Validation after fixes: `python scripts/validate_labs.py capstone-f`: solution pass, starter fails gracefully, no-generator pass, docs ok.
