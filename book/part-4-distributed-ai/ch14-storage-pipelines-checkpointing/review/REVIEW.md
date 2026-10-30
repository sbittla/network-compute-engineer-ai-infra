# Editorial Review — Chapter 14

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.25 | Fail (D9 8.5 < 9.0; 2 major findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal, pending independent review) |
| 3 | 2026-10-29 | Author self-review, iteration 3 (coordinator: canonical reliability assumptions) | 9.50 | Pass (internal, pending independent review) |
| IR1 | 2026-10-29 | Independent review, iteration 1 | 9.50 | Pass (borderline) |
| IR2 | 2026-10-29 | Independent review, iteration 2 | 9.43 | Fail (R2-01 major) |
| IR3 | 2026-10-30 | Independent review, iteration 3 | 9.40 | Fail (R3-01 major) |
| IR4 | 2026-10-30 | Independent review, iteration 4 | 9.50 | Pass; R4-01 minor (DCP line reflow) closed |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | Every calculation re-derived by hand and reproduced by the reference planner (Table 14.8 = lab A6 expectations). NVMe/Little's law, PCIe Gen4/Gen5 x4 rates, Lustre MDS/OST semantics, commit/fsync/rename semantics, Young and Daly formulas checked. Version-sensitive APIs (DCP `save`/`async_save`/`load`, Megatron `--async-save`, GDS `gdscheck`, S3 limits) carry `[VENDOR-SPEC, 2026-10]` with verify notes. Residual risk: the Llama 3 interruption figures are quoted from memory of the paper and must be re-checked against the publication. |
| D2 | Depth and production realism | 15 % | 9.5 | Failure signatures (metadata storm, write-burst interference, slow target, tail-only NVMe fault, torn checkpoint via `latest`), read amplification on restore, staging-memory and one-in-flight costs, hard vs soft failures, PFS tenant burst. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Progression: workloads → device → path → file systems → pipelines → measurement → checkpoint anatomy → sync/async → commit → economics → worked example. Worked example shows every step and ends in a sensitivity-backed recommendation. Four figures plus listings. |
| D4 | Hands-on lab quality | 15 % | 9.5 | Three realistic tools; 15 checks; deterministic byte-identical data (1.3 MB); 12 planted anomalies documented for instructors; checker includes on-the-fly defects (C3) so hard-coding fails; L2/L3 extensions with real fio/nvme-cli/lspci/lfs commands and manifest fields. |
| D5 | Exercises and assessment | 10 % | 9.5 | Full standard set (7 knowledge checks, 2 worked problems, lab, troubleshooting, design, 4 reflection) plus all outline-mandated items (Section 14 ×3, deliverable, Section 21 checkpoint benchmark/RPO-RTO/restore test as 14.18–14.19). Key has arithmetic, marking points, common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | Labels on all quantitative claims and table captions; MODELED vs SIMULATED vs ILLUSTRATIVE kept distinct; fio rules (cache, warm-up/preconditioning, ≥ 5 reps, Little's-law check); realism boundaries explicit. |
| D7 | Cross-layer integration | 5 % | 9.5 | ORION numbers throughout (NVMe, frontend 2×200G, 3:1 spines, 80/160 GB/s PFS, W-TRAIN layout); links to Ch 3, 5, 7, 11, 13, 15, 18, 19, 21 and Capstones A/G. |
| D8 | Operational realism and safety | 5 % | 9.5 | Runbook thresholds, restore procedure, safe/unsafe actions, escalation paths; Safety callouts on fio writes and shared-PFS load. |
| D9 | Editorial polish | 5 % | 9.5 | Acronyms defined at first use, figures and tables captioned and numbered, units SI/IEC explicit, manuscript 9,989 words (`wc -w`). |

Weighted: 0.20·9.5 + 0.15·9.5 + 0.15·9.5 + 0.15·9.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 + 0.05·9.5 +
0.05·9.5 = **9.50**; lowest dimension 9.5.

Iteration 1 scores (before fixes): D1 9.0, D2 9.5, D3 9.0, D4 9.5, D5 9.5, D6 9.5, D7 9.0, D8 9.5,
D9 8.5 → 9.25. D1 was held at 9.0 for the `iostat` column error, the `lfs` pattern field, and the
95 %/5 % inconsistency; D3 for stale section cross-references; D7 for the missing Chapter 15 link;
D9 for length over the ceiling and undefined acronyms.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R1-01 | Major | manuscript.md | 10,998 words, above the 10,000-word ceiling | Tightened 14.1–14.12, troubleshooting, summary, realism boundaries; now 9,989 |
| R1-02 | Major | lab/README.md §4, §1 | Section references pointed at pre-renumbering sections (14.7–14.11, 14.13) and Exercise 14.17 | Remapped to 14.8–14.12, 14.14, Exercise 14.18 |
| R1-03 | Minor | manuscript abstract / prerequisites | Referenced a nonexistent "Section 14.16" for runbook signals | Now "runbook signals at the end of this chapter" |
| R1-04 | Minor | Listing 14.1, lab README | `iostat -x` prints kB columns, not `rMB/s` | Changed to `iostat -xm` |
| R1-05 | Minor | manuscript | HBM, PCIe, NVMe, NIC, IOPS, SLI, HPC used before definition | Defined at first use |
| R1-06 | Minor | 14.5 | "a fifth of what it already delivers" (1.3/7.6 = 0.17) | "about a sixth" |
| R1-07 | Minor | solutions/lab/README.md | A "common mistake" bullet described an error that does not change the result | Replaced with two real mistakes (RPO_max vs E[lost]; applying k to soft failures) |
| R1-08 | Minor | 14.1 prerequisites | Chapter 15 mentioned without a link | Link added |
| R1-09 | Minor | 14.2 | "wastes 95 %" / "delivering 5 %" inconsistent with 12.5k vs 410k IOPS (≈ 3 %) | "over 95 % idle" / "a few percent" |
| R1-10 | Minor | Listing 14.2 | `pattern: 0` is not how `lfs getstripe` prints the RAID-0 pattern | `pattern: raid0` |

| R3-01 | Major | manuscript 14.11–14.12, runbook, summary; lab YAML/check.py; exercises 14.10, 14.12, 14.13; key; instructor notes | Reliability inputs (M = 24 h, ~12 min restart, ORION-XL 12.4 h) disagreed with the new canonical assumptions in `docs/REFERENCE_CLUSTER.md` (per-node MTBF 1,536 node-h → 48 h for 32 nodes, 3 h for 512 nodes; restart ≈ 15 min) | Planner inputs set to M = 48 h, relaunch 330 s, warm-up 150 s (E[time-to-resume] 904 s ≈ 15 min); all tables, intervals (async 37 steps, 643.8 s), lost GPU-h (55.6 vs 121.1), sensitivities, checker expectations, the 14.12 incident timeline, and the ORION-XL design answer (M = 3 h, 9 steps, 9,927 GPU-h/day) recomputed with the reference planner and re-verified by hand. Llama 3 rate kept as a comparison (Exercise 14.10). Manuscript 9,997 words; checker 15/15 and validate_labs pass. |

No open blocker or major findings.

## Release-gate items outstanding

- Independent technical review by a practising storage/HPC engineer (Lustre/GPFS-class operations)
  and a training-infrastructure engineer (DCP/Megatron checkpointing).
- Re-verify against primary sources at publication: Llama 3 interruption counts and percentages;
  Amazon S3 per-prefix request rates and consistency statement; PyTorch DCP API names
  (`async_save`, staging options); Megatron-LM `--async-save` prerequisites and the fully parallel
  save option; GDS tool names; `lfs`/`iostat`/`nvme-cli` output formats in Listings 14.1–14.2.
- Hardware validation of the L2 extensions (fio on NVMe; `dcp.save` vs `dcp.async_save` timing and
  restore test) and the L3 shared-PFS extension.

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer: **9.50, pass (borderline)**; all numbers verified against the canonical
reliability assumptions. Minor findings and author resolutions:

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| IR1-01 | Minor | 14.5 Pipeline 2 | 8 × 16 MiB / 12 ms = 11.2 GB/s, not 7.6 | Now: median ≈ 12 ms healthy, mean ≈ 17 ms incl. target 5; 8 × 16.8 MB / 17.6 ms ≈ 7.6 GB/s (checked against the trace: healthy-window median 12.8 ms, mean 17.2 ms) |
| IR1-02 | Minor | 14.12 Step 10.3; instructor notes | Sensitivity statement ambiguous; inconsistent rounding | States `pfs_write_GBps: 20` (read unchanged) at 10 % hard failures; 51.75 vs 53.03 used consistently |
| IR1-03 | Minor | 14.4 object storage | Missing S3 conditional writes, Express One Zone `RenameObject`, gradual prefix scaling / 503 SlowDown | Added, `[VENDOR-SPEC, 2026-10]` |
| IR1-04 | Minor | 14.9 DCP note; 14.10 commit step 3 | DCP's coordinator `.metadata` write is the commit point; no separate marker | Stated in both places |
| IR1-05 | Minor | Listing 14.1 | `r_await` 0.08 vs text 0.078 | 0.078 |
| IR1-06 | Minor | 14.14 | `lfs find -type f` also counts manifest and COMMIT | `-name 'shard_*'`; "shard files" in log and validation |
| IR1-07 | Minor | 14.3, Step 9, Table 14.9 | Frontend spine capacity used 3:1; VERIFIED_FACTS gives 1.5:1 by bandwidth | ≈ 8.5 Tb/s ≈ 1,067 GB/s; utilisation 6 % (and 6 % → 1 % in the incident table) |
| IR1-08 | Minor | Exercise 14.12, key | Non-canonical node name `hx8-21` | `orion-n21` |
| IR1-09 | Minor (cut) | 14.4, Summary, 14.11, review questions | Length pressure | PFS vendor note condensed; Summary bullets 2 and 5 merged; failure-rate paragraph and review questions tightened |

Checked: restart model gives E[time-to-resume] 904 s, consistent with the canonical ≈ 900 s.
Manuscript 9,984 words. Checker 15/15 (solution), 0/15 graceful (starter); `validate_labs.py ch14` OK.

Author re-score after fixes: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.5 →
**9.50**, lowest 9.5. The remaining risk is unchanged: primary-source re-verification of the
Llama 3 figures and the S3 and DCP/Megatron details.

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review found every iteration-1 finding fixed and every changed number reproduced. It scored **9.43 (fail)** because of one major finding.

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R2-01 | Major | lab/README.md §2–§3; README.md file map | Learner docs told learners to run the dataset generator, which is not shipped in the student release, and `validate_labs` docs=GENERATOR-NOT-MARKED | Removed the Setup line. §2 now says "produced by a seeded generator (instructor copy only)". File-map row marked "instructor copy only". `validate_labs.py ch14`: docs=ok, no-generator=pass |
| R2-02 | Minor | 14.3 step 3 | The 1.5:1 frontend ratio is the design ratio, but ORION-256 is populated 1:1 | Added "(design ratio; 1:1 as populated on ORION-256, ≈ 1,600 GB/s)"; conclusion unchanged |
| R2-03 | Minor | 14.9 DCP note; 14.5; 14.2 pitfall | Over-long line and orphan line break | Reflowed |

Manuscript is 9,995 words. Author re-score: all dimensions 9.5, weighted **9.50**.

## Independent review iteration 3 + author fixes (2026-10-30)

Iteration 3 scored **9.40 (fail)** on one major finding:

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R3-01 | Major | 14.12 Step 7; Key idea; lab YAML `replace_s`; exercise 14.12; key 14.13 | The hard-failure path assumed a hot spare, but ORION-256 has no spares (24 training + 8 inference nodes; full W-TRAIN uses all 32) | Step 7 and the YAML comment now declare a small spare pool *outside* ORION-256 as an explicit, deliberate variation (VERIFIED_FACTS option c). Step 7 adds the no-spare alternative: wait for repair, or restart at DP = 7 (224 GPUs, −12.5 %); 1,024 is not divisible by 7, so global batch or LR must change. Exercise 14.12 states that the restart used a node from that pool. The Key idea and the key now say "spare capacity" instead of "hot spares". No numbers changed; Table 14.8 and E[resume] = 904 s stand |
| R3-02 | Minor | 14.9 DCP note | Over-long line | Reflowed |

To stay under the cap, Further reading was condensed (Young/Daly merged; SCR, ZeRO and NVMe entries shortened). The manuscript is 9,995 words. Author re-score: all dimensions 9.5, weighted **9.50**.
