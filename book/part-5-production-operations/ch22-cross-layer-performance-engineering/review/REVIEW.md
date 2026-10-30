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
