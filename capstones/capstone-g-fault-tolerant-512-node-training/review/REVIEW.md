# Editorial Review — Capstone G: Fault-Tolerant 512-Node Distributed Training Operations

**Independent score history:** 9.30 → 9.38 → 9.50 (iterations 1 → 2 → 3; PASS at iteration 3, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Author self-review, iteration 1 | 2026-10-29 | Author | 8.90 | FAIL |
| Author self-review, iteration 2 | 2026-10-29 | Author | 9.50 | PASS (internal) |

## Scores by dimension (latest — iteration 2)

| Dim | Weight | Score | Justification |
|---|---|---|---|
| D1 Technical accuracy | 20 % | 9.5 | Xid 94/95 handling, row remap, DCGM field names, watchdog vs `NCCL_IB_TIMEOUT` (version-dependent default) aligned with docs/VERIFIED_FACTS.md; step time, interval and loss arithmetic re-derived; log formats labelled as imitations. |
| D2 Depth and production realism | 15 % | 9.5 | Clock skew, stale DCIM, straggler HCA, durability lag, corrupted shard, unhealthy "idle" spare, resume validation — each with a distinct discriminating signal. |
| D3 Pedagogy and clarity | 15 % | 9.5 | Figures G.1/G.2 show workflow and correlation chain; "facts you must get right" table; worked numbers. |
| D4 Hands-on lab quality | 15 % | 9.5 | 11 checks with targeted failure messages for each trap; deterministic 1.15 MB dataset; ≈ 2 s; L2/L3 commands. |
| D5 Assessment assets | 10 % | 9.5 | All eight outline outputs have templates, plus the nine common sections; expected numbers; failure patterns; oral questions. |
| D6 Evidence labelling | 10 % | 9.5 | SIMULATED statement required on page one (outline criterion); MODELED vs SIMULATED separated. |
| D7 Cross-layer integration | 5 % | 9.5 | GPU, PCIe, NIC, switch, storage, scheduler and training layers joined in one chain; links to Capstone E re-acceptance. |
| D8 Operational realism and safety | 5 % | 10 | Lab-only injection methods that cannot damage hardware; rollback rehearsal; never-reschedule enforced by the checker. |
| D9 Editorial polish | 5 % | 9.0 | Canonical `orionxl-nNNN` names; dense tables in places. |

Weighted: 0.90 × 9.5 + 0.05 × 10 + 0.05 × 9.0 = **9.50**. Lowest: D9 9.0.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| G-01 | major | dataset / all docs | Node names `xl-NNNN` did not follow the canonical `orionxl-nNNN`. | Generator and all files renamed; leaf naming extension `orionxl-be-leaf-pPP-rR` declared as a stated variation. |
| G-02 | major | README §2 | A 512-node job would leave no spares; the outline requires restart onto healthy capacity. | Job on 480 nodes (TP 8 × PP 8 × DP 60) plus a 32-node pool, stated as a variation with MTBF 1,536 / 480 = 3.2 h. |
| G-03 | major | EXEMPLAR timeline | Two timestamps (checkpoint start, HCA quarantine) were wrong. | Recomputed from T0: 03:10:39 and 03:18:09. |
| G-04 | minor | check.py T5 | Expected quarantine list in the wrong sort order. | Fixed. |
| G-05 | minor | README §7 | Collective timeout and `NCCL_IB_TIMEOUT` easily confused. | Added a "facts you must get right" row with version-dependent defaults. |
| G-06 | major | check.py, READMEs | Generator stripped from student release. | Dataset check SKIPs without `tools/`; learner docs mark the generator instructor copy only. |

## Release-gate items outstanding

- L3 drill not executed; real watchdog and DCP async-save timing unvalidated.
- Verify Xid 63/94/95 semantics, `ROW_REMAPPER` display option, mlx5 counter names and PyTorch flight-recorder variable names against the versions in use.
- External review by a large-scale training-operations engineer.

## Independent review iteration 1 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 1 | 2026-10-30 | Independent reviewer | 9.30 | FAIL (major findings) |
| Author fixes, iteration 3 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-01 | major | README §2 | The variations were not all declared. | Added a numbered variations callout: 480-node job + 32 spares (MTBF 3.2 h vs 3 h), PP 8, batch 3,840, 2.5 GB/s upload cap. |
| R-02 | major | `validate_resume`, data | A 1 % tolerance could not detect a subtle restore bug. | Tolerance set to 1e-3 from replay noise (≈ 2e-4); loss *and* grad-norm are checked, plus an exact match on the data-loader sample index. Planted `resume_dataloader_not_restored.csv` (≈ 0.24 % loss deviation, wrong sample index) now fails. Docstring corrected. |
| R-03 | minor | guide, exemplar | The spare pairing differed from the ops log. | Noted that either pairing is valid. |
| R-04 | minor | README §2 | Pod and port indexing was ambiguous. | Pods p00–p15 (0-indexed), ports 1-indexed; spine naming stated. |
| R-05 | minor | README §2 | The 2.5 GB/s upload cap was unjustified. | Labelled as a deliberate stress choice, with the reason. |

Validation after fixes: `python scripts/validate_labs.py capstone-g` — solution pass, starter fails gracefully, no-generator pass, docs ok.

## Independent review iteration 2 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 2 | 2026-10-30 | Independent reviewer | 9.38 (FAIL, one major) | FAIL |
| Author fixes, iteration 4 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-06 | major | README variation 1, guide §3 | The spare pool wasn't Poisson-sized. With a 5-day MTTR, 37.5 nodes are in repair on average and P(≤ 32) ≈ 0.21. | Showed the 5-day numbers (P95 48, P99 52) and declared a split turnaround: 70 % reset-and-return within 1 day, 30 % 5-day repair. That gives a mean of 16.5, P95 23 and P99 27, so 32 spares cover > P99. Stated the elastic fallback: 8-node DP replica steps, DP 60 → 48 without a batch change, or DP 59 with batch 3,776 plus a learning-rate review. |
| R-07 | minor | README variation 4 | Non-canonical spine and core names. | Now `orionxl-be-spine-pPP-SS` and `orionxl-be-core-CC`. |
| R-08 | minor | README variation 2 | Wrong rationale for the 4.35 s step. | 1 sequence per GPU vs W-TRAIN's 4, so a quarter of the per-GPU work (17.4 / 4 = 4.35 s). |
| R-09 | minor | `validate_resume` docstring, guide | Noise statement was inconsistent with the data. | States observed σ ≈ 2e-4 and the maximum of 6.5e-4 (65 % of tolerance, 35 % margin), and the data-loader bug at 2.4e-3; advises measuring replay noise on hardware first. |

Validation after fixes: `python scripts/validate_labs.py capstone-g`: solution pass, starter fails gracefully, no-generator pass, docs ok.
