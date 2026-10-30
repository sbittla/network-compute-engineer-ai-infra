# Editorial Review — Capstone E: Bare-Metal GPU Fleet Lifecycle Automation

**Independent score history:** 9.05 → 9.50 → 9.50 (iterations 1 → 2 → 3; PASS at iteration 3, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Author self-review, iteration 1 | 2026-10-29 | Author | 8.95 | FAIL |
| Author self-review, iteration 2 | 2026-10-29 | Author | 9.50 | PASS (internal) |

Rubric: [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md). For a capstone, D4 scores
the starter kit and checker, and D5 scores the templates, milestones and grading assets (there is
no chapter exercise set).

## Scores by dimension (latest — iteration 2)

| Dim | Weight | Score | Justification |
|---|---|---|---|
| D1 Technical accuracy | 20 % | 9.5 | Lifecycle semantics, acceptance tests and commands (`nvidia-smi --query-gpu` fields, `dcgmi diag -r 3`, `ib_write_bw --report_gbits`, `scontrol update … State=DRAIN/RESUME`, `kubectl drain --ignore-daemonsets --delete-emptydir-data`, Redfish paths) checked; version-sensitive items (`-d ROW_REMAPPER`, Ironic sub-commands, provisioner state names) carry verify notes. RoCEv2 wire-efficiency arithmetic re-derived. |
| D2 Depth and production realism | 15 % | 9.5 | Covers evidence freshness, per-GPU firmware uniformity after repair, blocked-combination drift, at-least-once/out-of-order delivery, noop vs reject, capacity floors tied to W-TRAIN parallelism, idle PCIe downshift pitfall, audit anchoring. |
| D3 Pedagogy and clarity | 15 % | 9.5 | Scenario → problem → artifacts → milestones → tiers; worked numbers section; Figure E.1 shows control flow and ownership; hints steer without giving answers. |
| D4 Hands-on lab quality | 15 % | 9.5 | 17 discriminating checks (graph safety, policy-driven thresholds, mutation tests on audit chain, converged-plan idempotency, dataset determinism); 17 planted anomalies incl. red herrings; deterministic; ≈ 2 s; L2/L3 extension with real commands and manifest fields. |
| D5 Assessment assets | 10 % | 9.5 | Eight templates covering all seven outline artifacts plus the nine common sections; rubric interpretation table; expected numbers; ten failure patterns; oral questions. |
| D6 Evidence labelling | 10 % | 9.5 | Every threshold and cost labelled; results template forces an evidence class per row; ORION variation (40 nodes) declared; L1 results consistently SIMULATED/MODELED. |
| D7 Cross-layer integration | 5 % | 9.5 | Links acceptance to Chapters 5/8/10/12/14 consequences, capacity floor to Chapter 11/17 parallelism, cost to Chapter 21. |
| D8 Operational realism and safety | 5 % | 10 | Safety callouts on every state-changing command; dedicated-lab rule; firmware caution; runbook template with escalation and "never do" list. |
| D9 Editorial polish | 5 % | 9.0 | Acronyms defined; figures captioned; links relative. Some tables are dense; chapter links point to packages being written in parallel. |

Weighted: 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×10 + 0.05×9.0 = 8.55 + 0.50 + 0.45 = **9.50**. Lowest dimension: D9 at 9.0.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| E-01 | major | instructor/GRADING_GUIDE.md §3 | Final schedulable count stated as 32; recomputation with the reference gives 31 (29 − orion-n07 + 3 admissions). | Fixed; added full per-state breakdown and journal outcome counts (iteration 2). |
| E-02 | major | instructor/EXEMPLAR.md §4 | RoCEv2 efficiency quoted as ≈ 97 % in prose but 0.98 in the formula. | Re-derived: 4096 / 4178 ≈ 0.980 → ≈ 392 Gb/s payload ceiling; prose fixed. |
| E-03 | minor | starter-kit/check.py | Em-dash separators printed as mojibake in a Windows cp1252 console. | Switched to ASCII `--`. |
| E-04 | minor | reference `plan_waves` docstring | Said "round-robin" but the algorithm is greedy in name order with a per-rack cap. | Docstring and comment corrected. |
| E-05 | minor | starter/fleet.py header | Shell heredoc stripped inline code markup. | Header rewritten. |
| E-06 | minor | README §2 | Capacity floor needed a link to W-TRAIN parallelism to be credible. | Stated as TP 8 × PP 4 × DP 6 = 192 GPUs = 24 nodes. |
| E-07 | minor | starter-kit/README §8 | Idle PCIe link downshift can cause false `gpu_pcie_link` failures on real hardware. | Added pitfall callout. |
| E-08 | major | all files | Node and rack names did not follow the canonical `orion-nNN` / `rack-NN` scheme (docs/REFERENCE_CLUSTER.md). | Generator, checker, reference and docs renamed (expansion nodes `orion-n33`–`n40`, racks `rack-09`/`rack-10`, lab node `orion-lab-n01`); data regenerated; 17/17. |
| E-09 | major | README §9, grading P9 | Canary busbw 455 GB/s implies NVLS; GDR-fallback evidence needed the reliable signals from docs/VERIFIED_FACTS.md. | NVLS assumption stated (ring ceiling ≈ 257 GB/s algbw); `/GDRDMA` channel lines and `nvidia_peermem`/DMA-BUF caveat added. |
| E-10 | major | check.py, READMEs | Student release strips `tools/`; the dataset check failed and READMEs told learners to run the generator. | Dataset check reports SKIP when the generator is absent; learner docs mark it instructor copy only; `no-generator` column OK. |

## Release-gate items outstanding

- L2/L3 extension not executed on hardware; thresholds remain ILLUSTRATIVE until calibrated.
- Verify `nvidia-smi -q -d ROW_REMAPPER`, Ironic CLI sub-commands, and MAAS/Metal3 state names
  against the versions used at publication.
- External review by a practising fleet/platform engineer (RELEASE_GATES.md).
- Chapter links resolve only once the Part 5 chapter packages are committed.

## Independent review iteration 1 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 1 | 2026-10-30 | Independent reviewer | 9.05 | FAIL (major findings) |
| Author fixes, iteration 3 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-01 | major | `plan_waves`, README §9, guide §3, exemplar | The capacity floor counted inference nodes and a node about to be drained, so the true training headroom was 1, not 5. | Floors are now per partition (`partition_floors`: training ≥ 16 at DP 4, inference ≥ 6), nodes on non-compliant stacks count as pending drains, and the default ORION split (training n01–n24, inference n25–n32) is used. The checker verifies every wave against each floor and adds a refusal case (inference floor 7 with orion-n30 pending drain). Docs updated. |
| R-02 | minor | `plan_waves` | The greedy plan produced more waves than the limits require. | The planner serves the racks with the most remaining nodes first. The reference plan has 7 waves, which is the minimum (inference headroom of 1 per wave forces canary + 6). The checker asserts the computed lower bound, and the one-node tails are explained as floor-driven. |
| R-03 | minor | README §2 | DP = 6 needs a global batch divisible by 6. | Batch 768 (128 per replica) at DP 6; batch 512 at the DP 4 maintenance floor. |
| R-04 | minor | README §9, results template | Said "accepted" where only some nodes passed. | Changed to "tested". |
| R-05 | minor | `plan_waves` | Expiring-bundle nodes were not prioritised. | Added `prefer_first: [deprecated]`. rack-07 nodes go in the canary and waves 1–3, and the checker enforces this. |
| R-06 | minor | README §2 | The partition the expansion nodes join was not stated. | Stated: the training partition. |

Validation after fixes: `python scripts/validate_labs.py capstone-e` — solution pass, starter fails gracefully, no-generator pass, docs ok.

## Independent review iteration 2 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 2 | 2026-10-30 | Independent reviewer | 9.50 (PASS) | PASS |
| Author fixes, iteration 4 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-07 | minor | canary data, `canary_decision` | The planner's canary (n25 + n01) did not match the metrics file, and an inference canary needs serving metrics. | `canary_metrics.csv` now uses exactly the planner's canary pair. It adds a `partition` column, per-partition baselines (n17/n21 training, n29/n31 inference), training step time and inference TPOT p95 (`max_tpot_regression_pct`). `canary_decision` compares each canary with its own partition. S1–S4 outcomes are unchanged (S2 −8.4 %, S4 Xid on n25); P14 arithmetic recomputed. |
| R-08 | minor | README §2 | This week training runs at DP 5, and 768 / 5 is not an integer. | Stated batch 640 at DP 5 (128 per replica) and the 20 % throughput cost of dropping to DP 4 during the waves. |

Validation after fixes: `python scripts/validate_labs.py capstone-e`: solution pass, starter fails gracefully, no-generator pass, docs ok.
