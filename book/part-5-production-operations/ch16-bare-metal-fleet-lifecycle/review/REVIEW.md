# Editorial Review — Chapter 16

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.28 | Fail (D9 < 9.0; open majors) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.55 | Pass (internal) — pending independent review |
| 3 | 2026-10-29 | Independent review iteration 1 | 9.35 | FAIL (2 majors) |
| 4 | 2026-10-29 | Independent review iteration 2 | 9.40 | FAIL (minors) |
| 5 | 2026-10-29 | Independent review iteration 3 | 9.50 | PASS (R16-18/19/20 closed afterwards) |

## Scores by dimension (author self-review, iteration 2 — superseded by the independent scores above)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.5 | Mechanisms (row remap pending vs failure, idle PCIe down-training, fabric-manager/driver coupling, busbw formula and NVLS caveat, Redfish resource paths, NVMe Sanitize) stated as a practitioner would; version-sensitive items (DCGM run levels, nvidia-smi field names, NVLS) flagged. Not 10: several vendor details need verification against current docs (see release gates). |
| D2 | Depth and production realism | 15% | 9.5 | Failure signatures with realistic output for every acceptance stage; distractors (SW Power Cap, idle Gen1, 200G frontend NICs); per-device firmware drift from RMA parts; anti-rollback firmware; hand-built pilot gap in the troubleshooting case. |
| D3 | Pedagogy and clarity | 15% | 9.5 | Objectives map to sections; state machine first, then each lifecycle stage; worked example has three steps with all arithmetic; four diagrams teach mechanisms (state machine, PXE/iPXE sequence, acceptance pipeline, wave campaign). |
| D4 | Hands-on lab quality | 15% | 10 | Real fleet task; 30 checks mixing targeted fixtures (feedback) and SHA-256 dataset digests (no answer leakage); planted defects plus distractors; guarded state machine with refused shortcuts; property-based planner checks; `report.py` for the written deliverable; byte-identical generator; L2/L3 commands mapped to the JSON schema. |
| D5 | Exercises and assessment | 10% | 9.5 | Full standard set + outline M1–M3 + deliverable D1, all tagged with difficulty/tier/evidence; key with arithmetic, marking points, and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.5 | Every quantitative claim labelled; modelled calculations show formula → values → result; thresholds labelled ILLUSTRATIVE with guidance to derive from measured baselines (R1); L2 extension specifies ≥ 5 NCCL runs with median and spread. |
| D7 | Cross-layer integration | 5% | 9.5 | ORION numbers throughout (W-TRAIN step time, DP replica = wave size, rack power, rails, addressing, QoS); links to Ch 3, 5, 8, 10, 12, 14, 15, 17–20; Capstones E and G. |
| D8 | Operational realism and safety | 5% | 9.5 | Runbook FL-03 with signals/thresholds/actions/escalation; safety callouts for OOB power actions, sanitize, burn-in power, read-only fio; abort conditions and per-component rollback. |
| D9 | Editorial polish | 5% | 9.0 | Acronym block added, figures/tables/listings numbered and captioned consistently, units correct. Manuscript is close to the 10,000-word ceiling (9,937 by `wc -w`), leaving little room for reviewer additions. |

Weighted = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×10 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×9.5 + 0.05×9.0
= 1.900 + 1.425 + 1.425 + 1.500 + 0.950 + 0.950 + 0.475 + 0.475 + 0.450 = **9.55**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript (whole) | First full draft was 11,318 words by `wc -w`, above the 10,000 ceiling. | Tightened Sections 16.1–16.13, summary, and further reading without dropping content; now 9,937. (It 2) |
| F2 | Major | manuscript, acronyms | MFU, NCCL, TP/PP/DP, PXE, SEL/SDR, CPLD, TPM, VBIOS, Xid, DBE/SBE used without definition in this chapter. | Added an acronym block in "Prerequisites and connections"; BMC, CMDB, DCGM, OOB, IPMI also defined inline. (It 2) |
| F3 | Major | §16.5, single-node NCCL | Listing shows busbw 467 GB/s while the text cites 450 GB/s per direction NVLink, with no explanation — a reader could think the listing is wrong. | Added the NVLink SHARP (in-switch reduction) explanation with a VENDOR-SPEC/verify flag. (It 2) |
| F4 | Minor | §16.13 validation | Said "restart the bake clock; the 72 h already elapsed does not count", but the canary failed re-acceptance before any bake began. | Rewritten: the bake starts only after re-acceptance passes, on the image that will ship. (It 2) |
| F5 | Minor | §16.5, Listing 16.4 | Full bordered DCGM table invented row/section layout in detail. | Condensed to result rows and stated that real layout varies by DCGM version. (It 2) |
| F6 | Minor | lab | Initial automated starter generation mangled function bodies. | Starter rewritten by hand with full contracts in docstrings; `check.py` starter mode verified: 30 TODO, exit 1, no traceback. (It 1) |
| F7 | Minor | lab check design | Dataset checks could leak expected per-node codes if stored in clear. | Expected results stored as SHA-256 digests; fixture checks provide targeted feedback; counts (25/1/6, 13 rejections) disclosed as progress hints. (It 1) |
| F8 | Minor | §16.8 vs Ch 20 | Ch 20 uses a different wave schedule for a config rollout. | Acceptable (different change type); §16.8 cross-references Ch 20 as the generalisation. No change. |

## Verification performed

- `python lab/check.py --impl solution` → 30/30 PASS, exit 0; `python lab/check.py` → 30 TODO, exit 1,
  no traceback; `python scripts/validate_labs.py ch16` → OK.
- `python lab/tools/generate_data.py` run twice → byte-identical `data/` (md5 compared); `data/` is
  ≈ 312 KB.
- Recomputed every number in §16.3–16.10 and the answer key with Python: 0.99¹⁶ × 0.97 = 0.826;
  E = 5.6 nodes; 1 − 0.826³² = 99.8 %; 22.04 s / 21.1 % / 54 GPUs; 7.66 GB, 0.170 s → 0.340 s;
  1,526 min; 6,510 and 9,070 GPU-hours; 1 − e^(−1.44) = 76 %; ln 20 = 3.0; 8 waves, 195 h, 768
  GPU-hours, 1.5 %; Little's law 1.1 nodes; busbw 267.02 × 1.75 = 467.3; PCIe 63.0 / 31.5 GB/s;
  W1 16 waves / 219 h / 12,288 GPU-h / 94.4 % / 25.0 % / 2,303 node-h; W2 19.55 s / 11.0 % / 28.1
  GPUs / +0.116 s / 0.67 %; DC1 3.87 h.

## Release-gate items outstanding

- Independent technical review by a practising GPU-fleet engineer.
- Verify against current vendor documentation at publication: DCGM run-level contents and
  durations; `nvidia-smi` query field names (`clocks_throttle_reasons.active` vs
  `clocks_event_reasons.active`) and `-q` section labels (Clocks Event Reasons, Fabric State/Status,
  ROW_REMAPPER); Xid 63/64/94/95 meanings; NVLink SHARP effect on `all_reduce_perf` busbw on HGX
  H100; fabric-manager error text; Redfish property support on target BMCs; `nvme sanitize` action
  codes; the Llama 3 paper's interruption breakdown wording.
- L2/L3 extension not yet executed on hardware; no MEASURED values in this chapter.

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer score: **9.35** (gate fail; 2 majors). The review summary provided only one-line notes for
R16-03, R16-08, R16-09 and R16-10 ("consistency notes"); the author ran a full consistency sweep and records
below what was changed under those IDs. The reviewer should confirm these match the intended findings.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R16-01 | Major | 400 GB/s single-node busbw floor assumes NVLS; ring algbw ceiling ≈ 257 GB/s | §16.5 now explains NVLS vs Ring, derives the ring ceiling (450 / 1.75 ≈ 257 GB/s algbw), and requires recording the NCCL version and algorithm (`NCCL_DEBUG=INFO`). Table 16.4 and the policy now set per-algorithm floors (NVLS 400, Ring 330 GB/s, ILLUSTRATIVE). Data records `nccl_version` and `algorithm`; the evaluator selects the floor by algorithm; new check `T2.nccl_floor_follows_algorithm`. Listing 16.9 is labelled NVLS. Lab README L2 and key M2 updated. |
| R16-02 | Major | "4 nodes = one DP replica → DP = 7" contradicts 1-node-per-rack cap | §16.8 now defines replica striping (each replica's 4 PP stages in 4 racks) as the condition for wave = replica. Without striping, a wave touches up to 4 replicas, so align waves with checkpoints. The lab planner enforces only the rack and wave caps. Key M2 now requires the condition to be stated. |
| R16-04 | Minor | Inconsistent throttle field names | `clocks_event_reasons.active` used everywhere (manuscript, exercise T1, lab README), with the legacy name noted once in Listing 16.8's caption. |
| R16-05 | Minor | Xid 94 vs 95 handling; map Xid 63 | Bullet rewritten: 94 is contained (drain and reset at the next opportunity); 95 is uncontained (drain immediately, reset before reuse); 63 is a row-remap event that needs a reset; 64 is a remap failure (RMA). |
| R16-06 | Minor | DCGM r3 missing the Diagnostic plugin | Added to Table 16.3 and Listing 16.4. |
| R16-07 | Minor | perftest iteration count / server flags | Iterations corrected to ≈ 3.69 × 10⁶, with the derivation; the server command now shows flags matching the client (manuscript and lab README). |
| R16-03 | Minor | Consistency (author interpretation) | §16.13 no longer claims DCGM `-r 1` passed with the fabric manager down (not reliably true on NVSwitch systems). |
| R16-08 | Minor | Consistency (author interpretation) | Check count updated from 30 to 31 in manuscript §16.12, exercises L1 and the key. |
| R16-09 | Minor | Consistency (author interpretation) | Abort condition and key M2 compare NCCL busbw against a baseline *for the same algorithm*. |
| R16-10 | Minor | Consistency (author interpretation) | Table 16.2's "two strategies" now matches its rows: diskless moved to the caption. Listing 16.9's caption states the algorithm. |

Word budget: additions offset by cuts (diskless row, §16.5 and §16.6 prose); `wc -w manuscript.md` = 10,084 at that point; 10,126 after the addendum below (corrected in iteration 2).
Lab: 31/31 solution PASS, starter 31 TODO and exit 1, data regenerated byte-identically,
`validate_labs.py ch16` OK.

Author re-score after fixes: D1 9.5, D2 9.5, D3 9.5, D4 10, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.0 → **9.55**
(pending independent re-review).

### Addendum — book-wide consistency (docs/VERIFIED_FACTS.md, REFERENCE_CLUSTER "Canonical names")

| Item | Resolution |
|---|---|
| Rack naming | `gpu-rN` replaced with `rack-NN` in the manuscript, exercises, key, planted-fault notes, and generator. Data regenerated (byte-identical on re-run); digests unchanged. No rail-leaf names appear in Ch16. |
| HW vs SW thermal slowdown | Listing 16.8 now shows SW Thermal Slowdown active and HW slowdown not active, at the software limit. The lab plant (orion-n27 GPU6) is now 89 °C with `SW_THERMAL_SLOWDOWN`, and K4 and its key were updated to match. |
| Node MTBF 1,536 h | The §16.9 spare-pool calculation now uses λ = 32 / 1,536 h = 0.5 faults/day, giving L ≈ 2.5 nodes in repair. It also notes the 48 h interruption interval for a 256-GPU job. |
| Frontend oversubscription | Stated as 3:1 by port count and 1.5:1 by bandwidth. |
| NCCL busbw / NVLS, `clocks_event_reasons`, Xid 94/95 | Already consistent after R16-01, R16-04 and R16-05. Ch16 contains no NCCL GDR log lines and no restart-cost figure. |

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review: **9.40** (gate fail, minors only; all iteration-1 majors closed).

| ID | Finding | Resolution |
|---|---|---|
| R16-03 | Acceptance-FAIL nodes appear `schedulable` in the inventory and in waves | Lab README §4 now states the six nodes were repaired and re-accepted before the ops week |
| R16-08 | Fig 16.3 and §16.5 claim MTU checks; the evaluator had none | Policy and data now carry NIC `mtu` 9000 and compute `active_mtu` 4096; the evaluator emits `NIC_MTU`; new fixture check. The realism boundary notes that end-to-end fabric path MTU is not checked |
| R16-09 | PLANTED_FAULTS seq 34–35 mislabelled; abort condition lacks the algorithm | Now "Maintenance drain (wave 2 node)"; abort condition says "baseline for the same NCCL algorithm" |
| R16-10 | §16.6 Step 3 assumed a week undetected without saying so | Assumption stated, Chapter 18 detection referenced, 9,070 GPU-h framed as an upper bound |
| R16-11 | Spare sizing from Little's law alone was weak | Poisson with mean 2.5: P(≤2) 54 %, P(≤3) 76 %, P(≤4) 89 %, P(≤5) 96 % [MODELED]. Spares sit outside the 32-node cluster; 4 spares ≈ 89 %, 5 ≈ 96 % |
| R16-12 | Runbook lumped Xid 94/95/63 together | Split into three rows: 95/48/79/64 immediate fault drain; 94 drain at next opportunity then reset; 63 / remap pending |
| R16-13 | Algorithm not forced; missing algorithm silently defaulted to NVLS | Text uses `NCCL_ALGO=NVLS`/`Ring` and confirms NVLS initialisation in the INFO log. The evaluator emits `NCCL_ALGO_UNRECORDED` when the algorithm is missing or unknown; new fixture check |
| R16-14 | Floors not tied to healthy ranges | Healthy ranges stated (NVLS ≈ 455–480, Ring ≈ 360–390 GB/s [ILLUSTRATIVE]), floor = baseline − margin. orion-n15 is now a Ring run at ≈ 367 GB/s that must PASS (documented as a distractor) |
| R16-15 | Learners told to run the generator, which the release strips | Removed from lab README setup; generator marked "instructor copy only" in the lab README, chapter card and manifest. check.py never calls it |
| R16-17 | "in rack rack-04" | Now "in rack-04" |
| Cuts | §16.4 and Summary | Table 16.2 condensed; three Summary bullets merged |

Lab: 33/33 solution PASS, starter 33 TODO and exit 1, no-generator PASS. Data regenerated and byte-identical on re-run;
acceptance digests unchanged (verdicts 25/1/6). `wc -w manuscript.md` = 10,233, within the 11,000 maximum.

## Independent review iteration 3 + author fixes (2026-10-29)

Closed: R16-18 (lab README L2 forces `NCCL_ALGO=NVLS` then `Ring`, confirms NVLS init, and records `algorithm`); R16-19 (Table 16.4 now lists `NIC_MTU` and `NCCL_ALGO_UNRECORDED`, paid for with Summary cuts); R16-20 (independent scores added to the header table).
