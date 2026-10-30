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
