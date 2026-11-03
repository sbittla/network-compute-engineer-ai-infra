# Editorial Review — Chapter 24

**Independent review score history (iterations 1 → 4):** 9.18 → 9.13 → 9.375 → 9.50 — PASS at iteration 4.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Author self-review, iteration 1 | 2026-10-29 | Chapter author | 8.9 | Fail (D1 < 9.0, D6 < 9.0, open majors) |
| Author self-review, iteration 2 | 2026-10-29 | Chapter author | 9.5 | Pass (internal, pending independent review) |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.5 | All walk-through arithmetic re-derived twice (FLOP, GPU count, TP/DP/PP volumes, bubble, Young interval, Clos sizing, ECMP occupancy, nccl-tests busbw factor). Version-sensitive items flagged (`NCCL_IB_QPS_PER_CONNECTION`, nvidia-smi "Clocks Event Reasons" naming, vendor adaptive-routing note). No invented flags. |
| D2 | Depth and production realism | 15% | 9.5 | Interviews include the deciding calculations practitioners actually use (TP-in-node, rail-local traffic, ECMP collisions, loopback-plan scaling break), failure-domain tables, degradation-vs-failure alerting, and a realistic troubleshooting round with counters. |
| D3 | Pedagogy and clarity | 15% | 9.5 | Objectives map one-to-one to sections; readiness model worked by hand before the lab automates it; interview arc diagram; exemplar case study. |
| D4 | Hands-on lab quality | 15% | 9.5 | Two realistic tools; deterministic generator verified byte-identical by the checker; 11 checks with targeted messages; planted flaws in both datasets (incl. transitive dedupe chain and tie-break subtlety); L1+/L2/L3 extensions with real commands and record lists. |
| D5 | Exercises and assessment | 10% | 9.5 | Full standard set + M1–M3 + deliverable; ★–★★★; evidence-required lines; key with arithmetic, marking points and common mistakes; lab planted-flaw tables. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.5 | Every number in worked examples labelled; planning assumptions marked ILLUSTRATIVE; lab evidence class MODELED; synthetic register explicitly SIMULATED; simulation-as-measurement treated as an integrity rule. |
| D7 | Cross-layer integration | 5% | 9.5 | ORION/W-TRAIN numbers reused consistently; connects compute, fabric, storage, scheduler, facilities; links to Chapters 1–23 and all eight capstones plus RUBRIC. |
| D8 | Operational realism and safety | 5% | 9.5 | On-call handoff runbook with thresholds; safety callout for portfolio benchmarking; safe-change emphasis in troubleshooting round and key. |
| D9 | Editorial polish | 5% | 9.5 | Acronyms defined; 5 figures and 14 tables numbered sequentially and captioned; consistent units; table column counts and all relative links machine-checked (links to Chapter 21 and some capstones resolve once those authors deliver). Dense tables in 24.2 may need print-layout attention. |

Weighted: 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×9.5 + 0.05×9.5
= **9.5**. Lowest dimension: 9.5 (all). D9 was raised from 9.0 only after the table/link check below
(finding F12) was run and passed.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | 24.12 nccl-tests block | busbw values used an incorrect factor (40.92/31.22) and the `count` column assumed 4-byte elements for BF16 | Recomputed with busbw = algbw × 2(n−1)/n, n = 128 → 40.88/31.18; count = 536,870,912; type shown as `bfloat16` |
| F2 | Major | 24.8 exemplar | Impact computed from step-time increase rather than throughput loss; and a +9 % step-time change from NIC misalignment was inconsistent with W-TRAIN's ~1 % fabric share | Changed to an FSDP job with per-layer all-gathers on the critical path; impact = (1 − 2.10/2.29) × 128 × 144 h ≈ 1,530 GPU-h |
| F3 | Major | 24.4 register paragraph | "31 citable postings" omitted the six archived postings from the arithmetic (51 − 11 − 3 ≠ 31) | Text now 51 → 40 complete → −6 archived −3 stale → 31 |
| F4 | Major | 24.2 pitfall | Claimed-vs-demonstrated averages were wrong (2.9/2.4) | Recomputed: 25/8 = 3.1 vs 20/8 = 2.5 |
| F5 | Minor | 24.1 | "Roughly 300 kW" unlabelled | Replaced by 256–326 kW `[MODELED]` with arithmetic |
| F6 | Minor | 24.6 follow-ups | MFU-drop follow-up answer was garbled | Rewritten: DP divisibility constraint; next clean layout DP = 16 |
| F7 | Major | 24.7 | Extending ORION's loopback plan to 32 leaves collides with spine addresses — not called out | Added explicit re-plan (spines .1–.16, leaves .101–.132; AS 65101–65132) |
| F8 | Minor | 24.5–24.7 | Non-standard `[ASSUMPTION]` label not in STYLE_GUIDE §3 | Replaced with `[ILLUSTRATIVE]` and an explanatory sentence |
| F9 | Major | manuscript length | Draft was 10,617 words (> 10,000) | Trimmed to 9,983 (`wc -w`) without removing required elements |
| F10 | Minor | lab/check.py | Staff gap-plan expectation was wrong in the first draft of the checker | Corrected to congestion (priority 6), verified against hand calculation |
| F11 | Minor | 24.3 | Incident example referred to "rail-3 leaves" (plural) though ORION-256 has one leaf per rail | Reworded |
| F12 | Minor | all Markdown | Table column consistency and relative links not verified | Scripted check: all tables consistent; all links resolve except to packages other authors are still writing (Ch 21, Capstones C/D/G/H, `capstones/RUBRIC.md`) |

## Iteration history

**Author self-review, iteration 1 (2026-10-29).** Scores: D1 8.5, D2 9.0, D3 9.0, D4 9.5, D5 9.0, D6 8.5,
D7 9.0, D8 9.0, D9 8.5 → weighted 8.9. Findings F1–F11 raised.

**Author self-review, iteration 2 (2026-10-29).** All findings resolved; all calculations re-checked
(see `solutions/exercises-key.md`); `python lab/check.py --impl solution` → 11/11 PASS;
`--impl starter` → 1/11 PASS, 10 TODO, exit 1, no traceback; `python scripts/validate_labs.py ch24` →
OK. Scores as in the table above.

## Release-gate items outstanding

- Independent editorial and technical review (this log records only the author's self-review).
- Review by a practising AI-infrastructure hiring manager or staff engineer of the level table (Table
  24.5) and the interview walk-throughs for realism of expectations.
- Re-verify version-sensitive items at publication: `NCCL_IB_QPS_PER_CONNECTION` semantics; nvidia-smi
  clock-event field names; mlx5 `hw_counters` names used in Section 24.12.
- Re-check that Capstone briefs (`capstones/capstone-*/`) and `capstones/RUBRIC.md` exist at the linked
  paths once their authors finish, and that Chapter 23 provides the design-review checklist and ADR
  template this chapter points to.
- The employer table reproduces the course outline's representative organisations; refresh the
  outline-sourced table if the outline is revised.

---

## Independent review iteration 1 + author fixes

Independent score received: **9.18** (below gate). Author fixes applied 2026-10-29; all numbers recomputed
before writing.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Non-canonical reliability (50 node-days, 600 s restart) | §24.6 now uses node MTBF 1,536 h → job M = 48 h = 172,800 s, restart 900 s: τ = √(2 × 12.25 × 172,800) = 2,058 s; 0.60 % + 0.60 % + 0.52 % ≈ 1.7 %. WP2(c) now halves node MTBF to 768 h: M = 86,400 s, τ = 1,455 s, 0.84 + 0.84 + 1.04 ≈ 2.7 %; key's comparison now "≈ 1.7 %". Matches reviewer. |
| R-02 | Major | DP = 16 presented as next layout | Cheaper next layout TP8/PP5/DP8 = 320 GPUs (40 nodes): 16 layers/stage, 28 GB state/GPU, bubble 4/132 = 3.0 %, 1.76e18/(320 × 989e12 × 0.32) = 17.4 s; cost = second leaf per rail and spine-crossing PP/DP traffic. DP = 16 kept as alternative. |
| R-03 | Major | "51.2 Tb/s with 64 × 400G" | Uses REFERENCE_CLUSTER wording (25.6T-class, or 51.2T with 64 × 800G cages at 400G). Added breakout case: 51.2T as 128 × 400G → k²/2 = 8,192 hosts; 1,024 GPUs = 2 leaves/rail, 16 leaves, 8 spines. |
| R-04 | Major | T1: 58 % clock vs +12 % step | Clock now 1,715 MHz (87 % of 1,980). Magnitude check in key: 13.5 s compute × 1,980/1,715 = 15.6 s → +2.1 s → 19.5 s (+12 %). I chose 1,715 MHz rather than the reviewer's 1,750–1,800 because it reproduces the stated 17.4 → 19.5 s exactly; 1,750 MHz would give ≈ 19.2 s. |
| R-06 | Minor | 32 flows presented as exact | Stated as a lower bound (multiple channels/QPs; `NCCL_IB_SPLIT_DATA_ON_QPS`). |
| R-07 | Minor | nvidia-smi block; DCGM field | Block marked abridged and changed to SW Thermal Slowdown only (consistent with 89 °C per VERIFIED_FACTS); `DCGM_FI_DEV_CLOCKS_EVENT_REASONS` added to the key. |
| R-08 | Minor | Register labelled [SIMULATED] | `[ILLUSTRATIVE — synthetic data]`. |
| R-09 | Minor | 256–326 kW; "2 % drop" | ≈ 256–288 kW sustained, ≈ 326 kW max; "2 % rise in step time". |
| R-10 | Minor | Lab README section refs | §24.4 (register), §24.2–24.3 (maps, levels), §24.9 (portfolio). |
| R-11 | Minor | ECN explanation stated as fact | Presented as an open hypothesis with its test (ECN per port before/after excluding the node); exercise and marking updated. |
| R-12 | Minor | Only one role matrix shown | Added Table 24.4 (highest-weight competencies for the other five roles, from the YAML); later tables renumbered and references in exercises/key updated. |
| R-13 | Minor | Rank-to-NIC row unclear | Row now explains why misalignment cannot produce FEC/CRC/Rx-power symptoms and that the NIC-to-NIC test bypasses GPU memory. |
| Names | Minor | Non-canonical host names | `hx8-NN` → `orion-nNN`, racks → `rack-03`/`rack-06` (REFERENCE_CLUSTER canonical names). |
| Cuts | — | Length | ADR subsection reduced to a pointer to Chapter 23; frequency pitfall folded into prose; "Underneath the table" sentence removed. Manuscript 10,234 words (`wc -w`), within the ~10,500 limit. |

Lab data and checker expectations unchanged (no data affected); `python scripts/validate_labs.py ch24`
→ 1/1 valid (solution 11/11, starter fails gracefully).

### Re-scores (author, after fixes)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | **9.5** |

Pending: independent re-review.

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent score: 9.13 (one blocker, one major).

| ID | Finding | Resolution |
|---|---|---|
| R2-01 (blocker) | `check.py` failed when `lab/tools/` is absent (student release) | `data_regenerates` now raises `CheckSkipped` and reports SKIP when the generator is absent; SKIP does not count as failure (exit 0 when all others pass). Generator marked "instructor copy only" in lab README and file map. |
| R2-02 (major) | §24.12 healthy 16-node busbw 40.88 GB/s implausible | Rescaled: last week 360.04 GB/s (algbw 181.44, 5,918 µs), today 205.76 GB/s (algbw 103.69, 10,355 µs); algbw = busbw / 1.984. Drop 43 % = rail-3 ratio 212/371 = 0.571, explained by lock-step channels. Validation target ≈ 360 GB/s. Grep of ch22–24 found no other cross-node busbw < 100 GB/s (per-rail figures are labelled busbw ÷ 8). |
| R2-04 | Key T1 +2.1 s | Stated as an upper bound (memory-bound kernels scale less than clock) |
| R2-05 | Clock basis | Exercise T1 states peers are boost-locked at ≈ 1,980 MHz max (not the 1,830 MHz typical sustained); 1,715 MHz → 19.5 s arithmetic unchanged |
| R2-06 | §24.6 divisor | "1.12 TB / (TP × PP = 40)" |

Manuscript 10,253 words. `python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK (solution, starter, no-generator, docs).

---

## Independent review iteration 3 + author fixes (2026-10-30)

Independent score: 9.375 (one major).

| ID | Finding | Resolution |
|---|---|---|
| R3-01 (major) | Table 24.10 and key T1 relied on spares | GPU and NIC rows: "restart from checkpoint without the node: wait for repair, or DP = 7 / 224 GPUs with a batch/LR adjustment (ORION has no spares)"; drain noted as not moving the job. The two-hot-spare recommendation is now framed as an explicit design proposal, a variation from the reference cluster. Key T1: drain + DP = 7 restart or wait for repair; a spare-based answer is accepted only when framed as that proposal (§24.6). |
| R3-02 | TP "much of it overlappable" | Now "on the critical path". |
| R3-03 | DP "overlappable with backward" | ≈ 0.19 − 0.07 ≈ 0.12 s (0.7 %) exposed after the ≈ 70 ms window. |

Manuscript 10,337 words.
`python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK.

---

## Release gate G7 — job-market register refresh (2026-10-30)

| Item | Resolution |
|---|---|
| G7: dated, deduplicated register | Added a real register: `lab/data/job_register_2026-10_collected.csv` (50 rows, one per requisition), `lab/data/job_register_2026-10.csv` (42 roles) and `lab/data/register_meta_2026-10.yaml` (sources, scope screen, dedupe rule `ch24-role-v1`, counts). 54 public postings read in full on 2026-10-30 from 11 employers' ATS listings; 4 excluded by the scope screen. Both CSVs pass `validate_register` with 0 issues. Report: `docs/verification/G7-ch24.md`. |
| Synthetic lab data | Unchanged (`job_register.csv`, `register_meta.yaml`); `data_regenerates` still byte-identical. `check.py` does not read the new files. |
| Manuscript | §24.2: note after Table 24.1 (two families outside the six; AI-network split). §24.4: new subsection "A real, dated register (October 2026)" and Table 24.8a `[OBSERVED, 2026-10-30]` (numbered 24.8a so later table numbers and their cross-references stay valid). Realism boundaries and Summary updated. |
| Exercises / key | R4 cites the real register; key R4 adds the one-day-sample limit. |
| Open | The style guide has no evidence label for labour-market observations; `[OBSERVED, 2026-10-30]` is defined inline in §24.4. The register goes stale on 2026-11-29. |

---

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0 · D2 9.0 · D3 9.5 · D4 9.0 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0 →
weighted **9.225** (gate not met). Counts: 2 major, 10 minor.

| ID | Finding | Resolution |
|---|---|---|
| N24-01 (major) | §24.12 evidence physically inconsistent: Rx −9.8 dBm is ≈ 4 dB below DR4 sensitivity, and ≈ 1e-5 loss cannot cost 43 % of goodput | Verified. Table 24.15 rebuilt as benchmark-window rates: n11 Rx −6.8 dBm (≈ 1 dB past the ≈ −5.9 dBm sensitivity, below the −4 dBm warning), pre-FEC BER ≈ 1.2e-3 vs ≈ 1e-7, uncorrectable/FCS drops ≈ 1.7 × 10⁵ frames/s (≈ 1.5 % of ≈ 11 M frames/s), `out_of_sequence` at the same rate. Added `[MODELED]` go-back-N arithmetic: goodput ≈ 371 / (1 + 50 × 0.015) = 212 Gb/s (W ≈ 200 KB same-rail BDP ≈ 50 frames); 1e-5 loss would cost ≈ 0.05 %. Validation and alerting moved to pre-FEC BER/trend + uncorrectable/FCS counts. K7 model answer updated. |
| N24-02 (major) | L2 harness gives E08 (`host_topology`) level 3 on a host with no RDMA NIC | Verified. `experiment.py` now claims level 3 only when an RDMA device is present; otherwise level 2, summary marked `PARTIAL_EVIDENCE`, readiness unchanged; new "What to conclude" bullet (evidence must cover the competency's scope). Smoke-tested with stubbed hardware (no NIC → 2, 78.4 → 78.4; NIC → 3, 78.4 → 82.4). The committed GPU bundle cannot be re-run now (Docker down, shared GPU host), so it is left unedited; lab README carries a labelled correction stating that its measurements stand but its level-3 credit and 82.4 readiness are invalid. |
| N24-03 | Table 24.8 says a canonical URL catches re-posts under new IDs | Verified. Row now prescribes a role key; canonical URL catches only copies of the same requisition. Key K4 and K4 model answer updated. |
| N24-04 | `register_meta_2026-10.yaml` `url_rule` describes the old strip-all rule | Fixed (hand-written file; generator does not emit it). |
| N24-05 | README "50 postings read" | README and lab README: 54 read, 4 excluded, 50 recorded, 42 roles. |
| N24-06 | Walk-through 2 health check has no numbers | Added `[ILLUSTRATIVE]` acceptance targets: Rx above warning, pre-FEC BER < ≈ 1e-6, zero uncorrectable/CRC over 30 min, `ib_write_bw` ≥ ≈ 370 Gb/s per rail, ≈ 350 GB/s large-message busbw on 8 rails (NVLS stated); alert on pre-FEC BER, not absolute corrected codewords. |
| N24-07 | Key T1 cites Ch 22 budget imprecisely | "Chapter 22's 77.7 % compute share (13.90 of 17.90 s, Table 22.2) applied to the 17.4 s step". |
| N24-08 | WP1 sources levels to Section 24.2 | Prompt (exercises.md and folder README) and solve.py comment now cite the lab's `demonstrated_levels` output. |
| N24-09 | "SpaceXSI" unexplained | `employer_note` added to the metadata; one sentence in §24.4. |
| N24-10 | "worse than no evidence" contradicts cap of 1 | Reworded to "capped at awareness (level 1), and in an interview it costs more than the level it was meant to show" (cap kept; no data change). |
| N24-11 | Ad hoc table numbers 24.8a/24.14a/24.15a | Renumbered sequentially 24.1–24.18; every reference in manuscript, exercises, key, exercise folders, meta.yaml and solvers updated (M3 marking.json regenerated). |
| N24-12 | Course outline cited by section number | Lab README links `docs/COURSE_OUTLINE_SOURCE.md`, "Scope note on job-posting coverage". |
| Next-0.5 | D3/D6/D7/D8 advice | Added a short "Reading one posting, worked" paragraph; qualified the 0.6-level inflation as one fictional learner and said how to measure it (blind second scorer); walk-through 1 TP term tied to Ch 22's 3.34 s (Section 22.10.3); runbook gains a post-cabling/optic soak step with thresholds (Table 24.18). |

Tests: `lab/check.py --impl solution` 11/11; `--impl starter` 1/11 (fails gracefully);
`docker/harness/generate_outputs.py` (local) OK, 0 failures; `scripts/validate_labs.py` 32/32 valid;
`scripts/copyedit_lint.py` 0 findings in ch24. Manuscript ≈ 11,700 words (+≈ 500, mostly the go-back-N
arithmetic and the health-check thresholds).

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.5 → weighted **9.40** (fail; one major finding).
Each finding was verified before any change was made. Coordinator directives applied in the same pass:
canonical GPU-hour ≈ $3.00 (Ch 21 TCO), energy $0.08/kWh (Ch 24 quotes no energy price), and an erratum on the committed L2 report.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R24-02 | Major | Walk-through 1 uses the 12.25 s write floor as the blocking checkpoint cost; Ch 23 uses δ = 60 s | Verified. §24.6 now calls 12.25 s a floor and derives δ ≈ 60 s as Ch 23 Step 7 does: τ = √(2 × 60 × 172,800) ≈ 4,554 s ≈ 76 min; 1.32 + 1.32 + 0.52 ≈ 3.2 %. Async saving at δ ≈ 5 s gives ≈ 1.3 % (Ch 23). WP2(c) now uses δ = 60 s: τ = 3,220 s, 1.86 + 1.86 + 1.04 = 4.77 %, matching Ch 23 W2. Updated in the prompt, folder README, key, `answer.md`, `meta.yaml` and `solve.py` (new assertions), and in the M2 and R3 answers |
| R24-01 | Minor | 45 kW described as a limit while claiming to size for the transient | Now "45 kW planned budget (a 50 kW limit less Ch 21's 10 % transient margin)" in Clarify and in Power and racks |
| R24-03 | Minor | Peers "locked at 1,980 MHz" under dense load is unrealistic | Peers now run at the canonical ≈ 1,830 MHz sustained clock (intermittent `SW Power Cap`), and GPU 5 at 1,585 MHz: 13.5 × 1,830 / 1,585 = 15.6 s, +2.1 s, +12 %, 87 % of peers. The wrong-baseline counterfactual is now the 1,980 MHz boost (≈ 3.4 s). Updated in the prompt, README, key, `answer.md`, `meta.yaml` and `solve.py` |
| R24-04 | Minor | `10.100.r.(2n)/31` for n = 0…127 silently re-indexes nodes | Re-indexing stated (node 001 → n = 0); with 1-based numbering, node 128 would overflow the /24 |
| R24-05 | Minor | 360 GB/s described as link bandwidth instead of bus bandwidth | Table 24.10: "NVLink ring all-reduce bus bandwidth ≈ 360 GB/s (NVLS off; link peak 450 GB/s per direction)"; NIC row says "all-reduce bus bandwidth per rail NIC" |
| R24-06 | Minor | Bubble defined differently from Ch 23 | Definition named (fraction of the step) and reconciled with Ch 23's (p − 1)/m = 2.34 % |
| R24-07 | Minor | "Data-centre" in Figure 24.1; long source lines | "Data-center"; overlong prose lines rewrapped (remaining > 106 characters are link, table and code lines) |
| Coordinator ($3.00) | — | Canonical GPU-hour cost changed | §24.1: 256 × $3.00 = $768/h idle; 0.05 × 256 × 720 × $3.00 = $27,648. Case study 1,530 GPU-h ≈ $4,590. M3 answer updated |
| Coordinator (L2) | — | Committed L2 report's scoring contradicts its evidence | Measured values untouched. A clearly marked ERRATUM block at the top of `gpu-rtx-4060-laptop-gpu/report.md` says Effective 2 and readiness unchanged at 78.4. A re-render cannot fix it, because the levels are stored by the run. Lab README correction cross-references it |
| D3 advice | — | Follow-up paragraph too dense | New Table 24.12 (follow-up → recomputation → answer); later tables renumbered 24.13–24.19 with all references updated |
| D2 advice | — | No promotion-packet example | Senior vs staff packet lines, each with an outcome, a number and a verification source `[ILLUSTRATIVE]` |
| D4 advice | — | Real-register worked example not checked | New check `real_register_worked_example` (50/50/50 collected, 42/42/42 roles, 0 issues); lab now 12 checks (README task 8b, L1 prompt/meta/key 12/12) |
| D5 advice | — | R2/R3 lacked marking anchors | Marking anchors added in the key |
| D6 advice | — | Case-study `ib_write_bw` figures unlabelled | 46 and 27 GB/s labelled `[ILLUSTRATIVE]` inline |
| D8 advice | — | No abort criterion in the first-15-minutes runbook | "Abort containment" row: hand over to the incident commander if the blast radius grows, a second symptom appears, or 15 min pass without containment |

Tests: `check.py --impl solution` 12/12; `--impl starter` 1/12 (graceful); `generate_outputs.py` 0 failures; package pytest 86 passed; `validate_labs.py ch24` OK; `copyedit_lint.py ch24` 0 findings. Manuscript 1,075 → 1,096 lines.

## Re-score follow-up (2026-11-01)

Reviewer re-score after r2: **9.75** (pass).
- **N24-02 cleared:** the rail-leaf rows of Tables 24.11 and 24.12 now include Chapter 23's restart on 7 rails (`NCCL_IB_HCA=^=mlx5_r`, ≈ 8/7 traffic per remaining rail; Section 23.5).
- **N24-01:** the erratum stays, because a re-run is not possible here. It says plainly that the scoring section is wrong and the correct result is Effective 2, readiness 78.4, and it states which measurement remains valid.

Tests: package suite 86 passed; `validate_labs.py` OK; lint 0 findings.
