# Editorial Review — Chapter 22: Cross-Layer Performance Engineering

**Independent review score history (iterations 1 → 4):** 8.90 → 9.50 → 9.50 → 9.50 — PASS at iteration 4.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.95 | Fail (2 major findings; D4 and D9 below 9.0) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.53 | Pass (internal); awaiting independent review |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.0 | 9.5 | All arithmetic re-derived (TP all-reduce bytes 1.202e12 B, 3.34 s at 360 GB/s, implied 102 GB/s; MFU 38.9 %; weak-scaling 97.1 %; MDE 0.19 s; thermal 13.9 × 1830/1620 = 15.70 s). Metric names (DCGM `DCGM_FI_PROF_SM_ACTIVE`, `..._PIPE_TENSOR_ACTIVE`, `..._NVLINK_TX_BYTES`, `DCGM_FI_DEV_SM_CLOCK`), mlx5 counters, nccl-tests flags (`-b -e -f -g -w -n`), and NCCL variables are real; version-sensitive items flagged. Residual uncertainty: exact NCCL INFO wording for GDR lines and the `NCCL_IB_TIMEOUT` default (key only), both marked "verify". |
| D2 | Depth and production realism | 15 % | 9.0 | 9.5 | Mechanisms with fingerprints (TP leaving NVLink, GDR fallback, latency-tail storage recalls with slack model and its predicted interaction, thermal straggler inverse-wait signature, RoCE ACK-timeout stalls in T1). Real anti-patterns from practice. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | Progression: step equation → evidence → tree → tests → attribution → scaling → benchmark design → tuning → anti-patterns → report; worked example shows every step; three figures teach mechanisms (step anatomy, hypothesis tree, bimodal wait). |
| D4 | Hands-on lab quality | 15 % | 8.5 | 9.5 | Realistic multi-source bundle; deterministic (byte-identical regeneration verified); 10 checks with specific feedback; nine planted flaws incl. a real interaction and time-aware join trap; L2/L3 commands corrected (TP-split analogue now 4 + 4 on two nodes). |
| D5 | Exercises and assessment | 10 % | 9.0 | 9.5 | Full standard set + O1–O3 + deliverable; ★–★★★; evidence lines; key with arithmetic, marking guidance, common mistakes; numbers verified against the reference implementation. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.0 | 9.5 | Labels on every table caption and quantitative claim; MDE and sample-size reasoning; measured vs modeled vs simulated kept apart, including in the generated report. |
| D7 | Cross-layer integration | 5 % | 9.5 | 10 | Integrates GPU, host, PCIe, NVLink, NIC/RDMA, fabric, storage, scheduler, and facilities on ORION; cross-references Chapters 3–21, 23, 24 and Capstones B, C, F. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Runbook with thresholds, read-only first steps, safe actions, change-approval list, escalation; production-risky tests rejected by rule; facilities owned by Facilities. |
| D9 | Editorial polish | 5 % | 8.5 | 9.5 | Acronyms defined, all tables captioned and numbered sequentially (22.1–22.14), figures captioned, word count 9,995 within 7,000–10,000. |

Weighted (iteration 2) = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×10 + 0.05×9.5 + 0.05×9.5 = **9.53**. Lowest dimension: 9.5.

Weighted (iteration 1) = 0.20×9.0 + 0.15×9.0 + 0.15×9.0 + 0.15×8.5 + 0.10×9.0 + 0.10×9.0 + 0.05×9.5 + 0.05×9.5 + 0.05×8.5 = **8.95**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | lab generator vs §22.10.4 | The dataloader-slack model in the manuscript implies TP-split jobs (≈ 26 s steps) hide most storage recalls, but the first generator applied the full storage effect to them — the lab contradicted the chapter. | Generator now exposes only 10 % of each recall on TP-split jobs (true interaction); model and checker include `tp_x_storage`; manuscript §22.4.4 and §22.10.4 explain it; key documents that an additive-only model produces a spurious ECC "effect". |
| F2 | Major | manuscript | 10,685 words (`wc -w`), above the 10,000 ceiling. | Tightened §22.1.3, §22.2, §22.6.3, §22.9, §22.11, trade-offs, further reading; now 9,995. |
| F3 | Minor | manuscript | Acronyms used before definition: DP/TP/PP, DCGM, NCCL, GDR, AER, CNP, ECN, PFC, ECMP, CDU, BF16, CMDB, HBM/H2D in Figure 22.1. | Defined at first use or replaced with plain words. |
| F4 | Minor | Table 22.5 caption | Said "three tests"; table has four. | Fixed. |
| F5 | Minor | §22.12 | Figure 22.3 caption sat inside the code block. | Moved outside. |
| F6 | Minor | manuscript | Four tables lacked captions. | Captioned; all tables renumbered 22.1–22.14 and in-text references updated. |
| F7 | Minor | lab/README L3 | TP-split analogue placed 4 ranks on each of 4 nodes (not 4 + 4 on two nodes). | Corrected to `-N2 --ntasks-per-node=4`; packed reference is one node with 8 ranks. |
| F8 | Minor | lab/starter | TODO hints named the planted flaws (log replay, failed job). | Replaced with generic hygiene prompts; flaws documented only in solutions. |
| F9 | Minor | lab/check.py | Non-ASCII em dash in per-check output could fail on legacy Windows consoles. | ASCII separator. |
| F10 | Minor | key K5 | Approximate value ("about 1.1 s") for dropping the period term. | Replaced with computed values (1.07 s, 1.57 s, 9.18 s). |
| F11 | Minor | §22.10.1 | "real noise" for simulated data. | "simulated noise". |

No open blocker or major findings.

## Release-gate items outstanding

- Independent editorial and technical review (this log records author self-review only).
- Verify against current NCCL documentation: wording of `NET/IB : GPU Direct RDMA Disabled/Enabled` INFO lines and `via NET/IB/x/GDRDMA` channel lines; `NCCL_IB_TIMEOUT` default (used in the T1 key).
- Verify DCGM clock-event/throttle-reasons field name and `nvidia-smi -q -d PERFORMANCE` block label for the shipping driver branch.
- L3 validation of the placement and GDR A/B commands on real hardware; record `[MEASURED]` busbw for 8 ranks in one node vs 4 + 4 across two nodes at 64 MiB.
- Links to Chapter 21 and Capstone C resolve only once those packages land (slugs match the repository README).

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent score: **8.90** (below gate). Author fixes below; re-score after fixes in the last table.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Invented `NET/IB : GPU Direct RDMA Enabled/Disabled for HCA…` lines | Regenerated `nccl_init_sample.log`: real channel-line format (`via NET/IB/0/GDRDMA` on R550 vs `via NET/IB/0` on R570) plus `lsmod \| grep nvidia_peermem` output; DMA-BUF caveat in log header, new Vendor implementation note in §22.2, lab README L2, key. Fixed hypotheses.yaml T2, Fig 22.2 M2, Table 22.5 row 4, Table 22.8 Driver row, runbook signal, key O1(b)/R4, exercise T1. All `[VENDOR-SPEC, 2026-10]`. |
| R-02 | Major | Headline 65/20/11/8 omitted −4 % interaction (summed to 104 %) | Allocation rule stated (§22.4.2): interaction is its own row; equal-split alternative (TP 62.7 %, storage 18.1 %) in key. Full row set everywhere (report, key lab table, O3). "after" renamed "common shift (period indicator), not attributable to a named change". Share SEs reported: 2.2 / 1.1 / 0.9 / 0.7 pp (classical; recomputed, match reviewer). |
| R-03 | Major | Homoskedastic SEs only | `estimate_effects` adds HC3-robust SEs; new `bootstrap_shares` (job-level, period-stratified, 2,000 resamples, seed 22, rank-deficient draws dropped and counted): common-shift share 95 % interval 4.2–14.2 %. New checker check (11 checks total). §22.4.2 recommends HC3/bootstrap and notes shares are composition-sensitive. |
| R-06 | Minor | `NCCL_IB_TIMEOUT` version | Key T1(c): 20 (≈ 4.3 s) for NCCL ≥ 2.23, 18 (≈ 1.07 s) for ≤ 2.22; exercise T1 now states NCCL 2.23+. |
| R-07 | Minor | Exercises R1/R2 vs key | R1 now 8.3 % common shift; R2 R² ≈ 0.998. |
| R-08 | Minor | §22.10.3 NIC-limit reasoning | Rewritten: halves have rail-local NICs; the cost is cross-rail hops (spine or PXN relay) and channel-to-NIC mapping. |
| R-09 | Minor | Thermal output inconsistent | Only SW Thermal Slowdown active; block marked abridged; `DCGM_FI_DEV_CLOCKS_EVENT_REASONS` named; root cause explains ≈ 20 °C GPU rise for 8 °C setpoint (lower pump speed raises coolant rise along the loop). |
| R-10 | Minor | srun all_reduce_perf | Lab README: build with `MPI=1`, launch with `srun --mpi=pmix`. |
| R-11 | Minor | Re-score ranking after each test | §22.3.4 paragraph, solution docstring/report heading, key O2 worked re-score. |
| R-12 | Minor | Job- vs GPU-hour weighting | §22.4.2 rule; solution reports step-weighted (GPU-hour) change +22.3 % vs job-weighted +23.2 %; checked. |
| — | Cuts | §22.1.3, Table 22.14 paragraph, summary last bullet | Done. |
| — | Canonical names | VERIFIED_FACTS / REFERENCE_CLUSTER | `hx8-NN` → `orion-nNN` (01–32), racks `rack-NN`, `orion-be-leaf-r3` throughout data, generator, manuscript, exercises, key (byte-identical regeneration re-verified). |

Manuscript 10,390 words (`wc -w`, within the ~10,500 allowance). `python scripts/validate_labs.py ch22`: OK.

| Dimension | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|---|
| Author re-score after fixes | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 10 | 9.5 | 9.5 | 9.53 |

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent score: 9.50 (pass, no margin). Minors fixed to protect the pass:

| ID | Finding | Resolution |
|---|---|---|
| R2-01 | Bootstrap resamples exposure, so it answers a future-sweep question | §22.4.2, key and solution report: for the observed event, condition on exposure and use HC3 share SEs (common shift 8.3 ± 1.7 pp); bootstrap 4–14 % is presented as the future-sweep interval |
| R2-02 | Interval vs SE comparison | Intervals compared with intervals: HC3 ≈ 5–12 %, classical ≈ 4–13 %, bootstrap 4–14 % |
| R2-04 | Single-node 360 GB/s needs the algorithm | "(ring, NVLS off)" added in §22.10.3 (both mentions) |
| R2-05 | Clock basis | §22.12 states 1,830 MHz is the typical sustained clock, not the ≈ 1,980 MHz max boost; arithmetic unchanged (19.7 s) |
| Student-release policy | Learner README / file map told students to run the generator | Generator line removed from learner setup; file map marks it "instructor copy only, removed from the student release". `validate_labs.py` no-generator column: OK. |
| Grep for cross-node busbw < 100 GB/s | Only the §22.10.3 TP-split bracket (90–150 GB/s), which is an explicitly degraded cross-rail case with stated mechanism; kept. |

Manuscript 10,441 words. `python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK.

---

## Independent review iteration 3 + author fixes (2026-10-30)

Independent score: 9.50 (pass). Minor fixed against VERIFIED_FACTS "Distributed training operations":

| ID | Finding | Resolution |
|---|---|---|
| R3-01 | DP described as "mostly overlapped/hidden"; §22.10.5 used ≈ 0.05 s extra exposure | Exposure modeled as max(0, T_DP − 0.07 s): ≈ 0.03 s at DP = 2, ≈ 0.10 s at DP = 8 (matches Table 22.2); increase ≈ 0.07 s; unexplained term now 0.52 − 0.07 − 0.33 ≈ 0.12 s. §22.1.2 and §22.5.2 say only ≈ 70 ms can be hidden. Key W2(b) updated the same way (+0.05 s at 16 nodes, +0.07 s at 32). |
| Check | Spare-node / drain assumptions | Already consistent: troubleshooting plan B restarts at 224 GPUs; runbook drain is conditional on a checkpoint restart; key T1 notes ORION has no spare node. |

Manuscript 10,498 words.
`python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK.


## Independent review iteration 4 minors (2026-10-30)

| ID | Resolution |
|---|---|
| R4-01 | Lab README states the sweep ran on all 32 nodes because the 8 inference nodes (orion-n25..n32) were lent to training |

---

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0 → weighted
**9.375** (fail: < 9.5, one open major). Findings: 1 major, 11 minor. All verified and resolved below; none rejected.

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| N22-01 | major | Dataloader slack model never states prefetch depth; "≈ 1.4 s exposed" wrong at PyTorch's default `prefetch_factor=2` | Verified with a discrete queue simulation (16 s production, 10 % recalls of U(10,18) s, in-order delivery): 1.25 s/step at prefetch 1, 0.39 s at prefetch 2, 0.40 s at prefetch 1 on 26 s TP-split steps. §22.10.4 now states the sweep config `num_workers=1, prefetch_factor=1`, gives 1.4 s as the upper bound and ≈ 1.25 s simulated `[MODELED]`, notes the default prefetch 2 would leave ≈ 0.4 s (cheap first knob), and gives the simulated TP-split value. Fix analysis (4 workers × 2) unchanged. |
| N22-02 | minor | No sync/straggler term in the step equation or Table 22.2 | Note under Table 22.2: straggler wait lands in `T_comm,exposed` on non-slowest ranks; Table 22.2 is a critical-path budget so it sits in the compute row; ≈ 2.07σ at 32 nodes; pointers to §22.10.5 and §22.12. |
| N22-03 | minor | Per-rank collective-wait source not named | New Table 22.14 in §22.12: framework timers, PyTorch flight recorder (`TORCH_FR_BUFFER_SIZE`, `TORCH_NCCL_DUMP_ON_TIMEOUT`), NCCL profiler plugin, Nsight Systems on sampled ranks, each with overhead; MegaScale's slow-compute/low-wait detector cited. Old Table 22.14 renumbered 22.15. |
| N22-04 | minor | Frontend "3:1 oversubscribed" | "3:1 by port count, 1.5:1 by bandwidth". |
| N22-05 | minor | check.py lacks dataset-reproducibility check | New first check `data_regenerates` (filecmp against a temp regeneration); `SKIP` when `tools/` is absent; summary line counts skips. Lab README §6 documents it. |
| N22-06 | minor | Third L3 `srun` lacks `--gpus-per-node=8` | Added, plus `NCCL_DEBUG_SUBSYS=INIT,NET`. |
| N22-07 | minor | T1(d) acceptance on absolute corrected-codeword counts | Key and T1 answer: pre-FEC BER within fleet baseline (< 1e-7) and stable over a 1 h soak, zero uncorrectable/CRC, Rx power inside warning thresholds; corrected codewords as a trend only. T1 evidence block gains "pre-FEC BER ≈ 1e-5 (other ports ≈ 1e-8)" (consistent with 1.9e9 corrected/10 min at ≈ 78 M codewords/s), mirrored in the exercise README. |
| N22-08 | minor | Backend tx 6 → 38 GB/s not reconciled with the TP model | Verified: every node of a split job holds two split halves (placement shifts ranks by 4), each sending 1.2e12 B per ≈ 26.5 s step → ≈ 91 GB/s extra, so "mean over job-nodes" would not explain 38. Regenerated the metric from the model instead: generator `nic = 96.0 if split` (same RNG draws; only `backend_tx_GBps_mean` changes, +58.0 on the 56 split rows). Now 6.06 → 95.93 GB/s; propagated to Table 22.6, key O1(b), O1/O3/K4/K7/R2 answers, O1 `solve.py` and outputs. |
| N22-09 | minor | CDU "last rack on the loop" implies series racks | Rephrased: ΔT = P/(ṁ·c_p) across each cold plate; rack-06 at the far end of CDU 3's secondary manifold, lowest differential pressure, lost the most flow. |
| N22-10 | minor | -ise/-ize mix; overlong line 7 | utilization/utilized/optimized throughout (manuscript, exercises, K2 README, key); line 7 rewrapped. |
| N22-11 | minor | "tasks 1–9" omits 6b | "tasks 1–9 (including 6b)" in exercises.md and the L1 README (prompt kept in sync). |
| N22-12 | minor | ECC alert "/h" vs "per job-node" | Jobs run ≈ 1 h (verified from step_log); key, L1/O3 answers and lab README state the per-job-node count equals the alert's per-hour rate. |
| Next-0.5 (D4) | — | Report should carry hygiene counts | New `hygiene_counts` (solution + starter TODO); `render_report` takes it and prints a `Hygiene:` line; the report check requires 44 / 480 / 0. README tasks 1 and 9 updated. |
| Next-0.5 (D5) | — | Per-part points for W1/W2/T1/D1 | *Marking* lines added to the key, matching meta.yaml. |
| Next-0.5 (D8) | — | Plan-B trigger; bimodality threshold | §22.12: plan B (DP = 7, rack-06 excluded) only if slowdown passes ≈ +12.5 % or HW Thermal Slowdown appears; Training Infra lead decides; fresh checkpoint if newest > 1 h old. RB-PERF-03 signal: ≥ 1 node's ranks waiting < 25 % of the median rank's wait. |
| Next-0.5 (D9) | — | Table 22.13 Prior column | Uniform "Level: reason" form. |

Tests: `python lab/check.py --impl solution` 12/12 (0 skipped); `--impl starter` 1/12, TODO lines, exit 1;
`python scripts/validate_labs.py ch22` OK (solution, starter, no-generator, docs); package test suite run
locally (`pytest docker/harness/test_package.py --pkg <ch22>`) 86 passed; committed outputs regenerated with
`docker/harness/generate_outputs.py` run locally; `python scripts/copyedit_lint.py`: 0 ch22 findings.
Manuscript 11,006 words (was 10,556).

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.0, D5 9.5, D6 9.0, D7 9.5, D8 9.5, D9 9.5 → weighted **9.28** (below the gate; two major findings). Each finding was verified before it was changed.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R22-01 | Major | The L2 GPU report's narrative over-claimed: pageable was called "recovered" and a "strong inferred cause" while its own verdict was "inconclusive" (OLS 6.02 ± 2.12 vs 2.65 ms direct; common shift 3.02 ms = 16× MDE) | Verified. `experiment.py` now builds the narrative from the verdict column. A factor reads "recovered and corroborated" or "direction recovered, OLS 2.3× the A/B, inconclusive at this n". The mechanism bullet claims three-way agreement only when the statistical verdict corroborates. A common shift above 3× MDE is called block-order drift, with "interleave or add a drift covariate" advice. Both committed `report.md` files were re-rendered from the unchanged `results.json`/`environment.json` through `hwlab` `render()` + `report()`; invariants re-checked and passing. Measurements are byte-identical, and the A/B rows are kept in their original order. The lab README "Observed on the reference run" is rewritten to match. The Table 22.6 cross-reference was checked and is correct |
| R22-02 | Major | The L3 `srun -N2 --gpus-per-node=4` binds GPUs 0–3 on both nodes, i.e. rail-aligned, not the modeled cross-rail split | Verified. The lab README now uses a `pin_split.sh` wrapper that sets `CUDA_VISIBLE_DEVICES` from `SLURM_NODEID`: GPUs 4–7 on node 0 and 0–3 on node 1 for the cross-rail run, and `SPLIT=aligned` for the control. `NCCL_DEBUG=INFO` is set and the channel lines are grepped to show the NICs used. Predictions: cross-rail ≈ 100 GB/s; aligned control ≈ 170–180 GB/s (four rails, half the ≈ 350 GB/s eight-rail figure); one node ≈ 360 GB/s. All are `[ILLUSTRATIVE]`. §22.10.3 states the same predictions and the falsification condition |
| R22-03 | Minor | PXN offered for a hop where no communicator rank owns the rail-matched NIC | §22.10.3 reworded: the hop goes cross-rail through the spine or uses a non-local NIC (NODE/SYS, host-staged under the default `NCCL_NET_GDR_LEVEL`); PXN cannot help |
| R22-04 | Minor | Plan-B trigger mixed step-time and throughput percentages; batch not divisible by 7 | Break-even is 1/0.875 − 1 = +14.3 % before the 64 GPU-h restart, so the trigger is ≈ +15 %, and immediate on any HW Thermal Slowdown (this also covers the D8 abort condition). The global batch becomes 1,022 or 1,029 with the matching LR adjustment |
| R22-05 | Minor | "DMA-BUF unavailable on R570" read as a property of the driver branch | Scenario reason added: proprietary kernel-module flavour and an RDMA stack built without DMA-BUF. R570 with the open modules, kernel ≥ 5.12 and a capable stack does support DMA-BUF |
| R22-06 | Minor | Uncorrectables at pre-FEC BER 1e-5 left unexplained | Key and T1 `answer.md`: mean BER is far below the RS(544,514) limit (≈ 2.4e-4); bursty errors from the dirty connector fill the 15-symbol histogram bin, and that tail explains the uncorrectables |
| R22-07 | Minor | K5 omits the alert coefficient moving | Re-fit confirmed (−0.05 → +0.16 s). Added to the key; the K5 `answer.md` already had it |
| R22-08 | Minor | 8.40 s illustrative vs ≈ 9.0 s lab effect not bridged | One sentence before §22.10.3: different samples, both inside the 4.7–10.0 s modeled range |
| R22-09 | Minor | Over-long source lines; awkward PXN expansion | Long prose lines rewrapped. Expansion is "PXN (PCI × NVLink)": the reviewer's "PCIe" spelling was not used because the book's copyedit rule `exp-pxn` follows NCCL's own expansion |
| D2 advice | — | Per-rank-wait telemetry pitfalls; continuous pipeline | Paragraph added after Table 22.14: cross-host clock skew (compare durations, not timestamps), asynchronous CUDA timing (use CUDA events, aggregate per step), and running the pipeline continuously so that every change window becomes a natural experiment |
| D7 advice | — | Tie the CDU numbers to Ch 21 | Thermal root cause uses Ch 21's flow formula: a 34 kW rack at 10 K needs ≈ 0.81 kg/s; at half flow the rise is 20 K, so +10 K + 8 K setpoint ≈ +18 K, consistent with the ≈ 20 °C rise |
| Price canon | — | $0.08/kWh, ≈ $3.00/GPU-h | No energy price or GPU-hour price appears in ch22, so nothing to change |
| Line endings | — | (found while testing) | The data generator now writes its YAML/log files with `newline="\n"`, so it reproduces byte-identically on Windows as well as in the container. `lab/data` is all LF again; only the r1 `node_metrics.csv` change remains in the diff |

Tests: `check.py --impl solution` 12/12; `--impl starter` 1/12 (graceful); `validate_labs.py ch22` OK including no-generator; `copyedit_lint.py ch22` 0 findings; outputs regenerated with `generate_outputs.py` (0 failures); package test suite run locally: 86 passed. The manuscript grew from 11,006 to ≈ 11,330 words.

## Re-score follow-up (2026-11-01)

Reviewer re-score after r2: **9.78** (pass). N22-01 cleared: the single-node L3 reference command now sets `NCCL_NVLS_ENABLE=0 NCCL_ALGO=Ring` for the ≈ 360 GB/s prediction. The README and §22.10.3 now state that with NVLS left on (default 2), an NVLS-capable node reports more than ≈ 400 GB/s. Tests: package suite 86 passed; `validate_labs.py` OK; lint 0 findings.

---

## Repetition pass (2026-11-04)

- §22.1.2: the DP traffic derivation (7.7 GB, 0.17 s, 70 ms hidden) removed from the budget paragraph; kept in §22.5.2 (and reused in the §22.10.5 worked example). The paragraph keeps "≈ 0.10 s exposed" with a pointer to §22.5.2.
- Table 22.3 GPU blind-spot cell repeated the GPU-utilization Pitfall; cell now points to the Pitfall, and the unique fact (SM_ACTIVE counts only the few SMs NCCL occupies) moved into the Pitfall.
- §22.2 vendor note: general `nvidia_peermem` versus DMA-BUF teaching reduced to a pointer to Chapter 13 (Table 13.5), which owns GPUDirect RDMA verification. Kept: the `/GDRDMA` evidence rule, the lab R570 facts, and the NCCL topology-line note.
- §22.3.4 Key idea ("Rank tests before you run them … partition of evidence you already hold") removed: it restated the §22.3.3 closing paragraph and the §22.3.4 prose next to it.
- Realism boundaries: the MDE-assumptions bullet duplicated §22.6.1; merged (bootstrap alternative now in §22.6.1) and bullet removed. The "observational attribution" bullet now points to §22.4.4's Key idea instead of restating it.
- Table 22.9 noisy-fabric antidote now points to §22.6.3 instead of repeating its list.
- §22.9: the "Add the scope, hygiene, recommended change, manifest" paragraph duplicated the report skeleton; folded into the skeleton lead-in, with "run manifest" added to its last line.
- Figure 22.3 caption no longer restates the "slow ranks wait least" conclusion (kept in the prose and the closing Key idea).
- Summary bullet on mean versus median rephrased (it copied §22.3.1 almost verbatim).
- Deliberately kept: the worked example's reuse of 17.4 s, the straggler factors and MDE; the anti-pattern and trade-off tables (catalogs required by objective 7); the §22.12 cooling-flow arithmetic (one step, already pointing to §21.7); the runbook's operational restatements.

Words: 11,336 → 11,223. Checks: `copyedit_lint.py` 0 findings; `check.py --impl solution` 12/12.
