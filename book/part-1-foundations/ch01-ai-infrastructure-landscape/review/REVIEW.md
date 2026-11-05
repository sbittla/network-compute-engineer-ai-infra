# Editorial Review — Chapter 1

**Independent review score history:** 9.05 → 9.50 → 9.50 (iterations 1–3; iteration 3 PASS, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.18 | Fail (D1 and D9 below 9.0; open majors F1–F3) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.48 | Fail (total 9.475 < 9.5; D9 = 9.0) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | Pass (internal; independent review pending) |

## Scores by dimension (latest)

| Dim | Weight | It. 1 | It. 2 | It. 3 | Justification (iteration 3) |
|---|---|---|---|---|---|
| D1 Technical accuracy | 20 % | 8.5 | 9.5 | 9.5 | All arithmetic re-derived twice (TP/DP/PP volumes, decode/prefill bounds, KV capacity, Young interval, incident volumes) and cross-checked against the lab output. Version-sensitive names (DCGM fields and numeric IDs, NCCL log lines, `nvidia-smi nvlink` options) flagged `[VENDOR-SPEC, 2026-10]` or "verify". W-TRAIN HBM traffic honestly labelled `[ILLUSTRATIVE]`. |
| D2 Depth / production realism | 15 % | 9.5 | 9.5 | 9.5 | Shows why TP must live in NVLink (≥ 24 s vs 2.67 s per step), why BF16 decode at 2k context cannot reach machine balance at any batch, why DP stays on one rail, MTBF and checkpoint economics, and an orchestration-caused "network" incident with consistent numbers. |
| D3 Pedagogy / clarity | 15 % | 9.5 | 9.5 | 9.5 | Objectives map to sections; one ceiling model introduced, then reused by worked example, lab, and incident; four captioned diagrams. |
| D4 Lab quality | 15 % | 9.5 | 9.5 | 9.5 | Real capacity-review task; seeded data verified byte-identical by the checker; nine checks with actionable messages; units trap (W11) that inverts the conclusion, impossible row (W12), latency-dominated row tempting a hardware fix (W16), two mislabels; L2/L3 commands real. |
| D5 Exercises / assessment | 10 % | 9.0 | 9.5 | 9.5 | Three mandated exercises plus full standard set, each with difficulty, tier, evidence; key with arithmetic, marks, common mistakes. |
| D6 Measurement rigor / labels | 10 % | 9.0 | 9.5 | 9.5 | All quantitative claims labelled; captions carry labels; text states nothing in the worked example is measured; L2/L3 requires ≥ 5 runs after warm-up with median, p95, spread, and manifest. |
| D7 Cross-layer integration | 5 % | 9.5 | 9.5 | 9.5 | ORION throughout; compute/network/storage/orchestration connected; forward references and Capstones A, D, G. |
| D8 Operational realism / safety | 5 % | 9.0 | 9.5 | 9.5 | Runbook with thresholds and owners; read-only safety callout; changes via review and lab partition. |
| D9 Editorial polish | 5 % | 8.5 | 9.0 | 9.5 | *(Historical, iteration-3 text; superseded by the iteration-1/2 review sections below — manuscript now 10,027 words.)* Acronyms complete; figures 1.1–1.4 and tables 1.1–1.14 sequential; all relative links resolve; exercise references (1.3, 1.R2) match; ASCII lab output. |

Exact weighted totals: iteration 2 = 0.95 × 9.5 + 0.05 × 9.0 = **9.475** (below gate);
iteration 3 = **9.50**. Lowest dimension: 9.5.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript §1.6 | Claimed observed time "usually lands between" max and sum of bounds; false when latency or stragglers dominate | Rewritten: observed above the sum means costs outside the model dominate (it. 2) |
| F2 | Major | manuscript §1.11 | Step-time increase attributed only to TP moving to the NIC; ignored DP moving to NVLink | Full accounting added: +7.6 s NIC TP, −0.7 s NVLink TP, −0.2 s NIC DP ≈ +6.7 s vs 6.71 s observed (it. 2) |
| F3 | Major | manuscript length | 10,094 words, above the 10,000 cap | Tightened prerequisites, §1.2, §1.8, §1.10; 9,948 words (it. 2) |
| F4 | Minor | acronyms | BF16, FP8, FLOP, BMC, OOB, Xid, IaC undefined | Added (it. 2) |
| F5 | Minor | lab solution output | Non-ASCII "µs" garbled on Windows consoles | Changed to "us" (it. 2) |
| F6 | Minor | key WP1 | NIC total rounded inconsistently (11.96 vs 11.95 GB) | Fixed (it. 2) |
| F7 | Minor | §1.11 | NCCL log format is version-dependent | Labelled `[ILLUSTRATIVE]`, "formats vary by software version" (it. 1) |
| F8 | Minor | §1.8 | Employer table could be read as hiring claims | Caption and realism callout: representative organizations only; dated register required (it. 1) |
| F9 | Minor | D9 sweep | Caption order, link targets, exercise cross-references unverified | Verified mechanically (it. 3) |

No open blocker or major findings.

## Release-gate items outstanding

- Independent review by a practising GPU-cluster/network engineer (scale-up/scale-out arithmetic,
  NCCL transport evidence, Megatron TP all-reduce counts).
- Re-verify at publication: H100-class peaks, NVLink bandwidth, DCGM field names and numeric IDs
  (1002/1004/1005/1011), `nvidia-smi nvlink --status/--errorcounters`, NCCL INFO formats, GB200 NVL72
  domain size, `scontrol write batch_script` behaviour.
- L2/L3 lab extensions not yet run on hardware; the chapter contains no `[MEASURED]` values.
- Employer table to be refreshed each edition; job-market claims require a dated register.

## Independent review iteration 1 + author fixes (2026-10-29)

Independent score: 9.05 (FAIL). Shared docs re-read before fixing: `docs/VERIFIED_FACTS.md` (new),
`docs/REFERENCE_CLUSTER.md` (canonical reliability, names, frontend 1.5:1, 25.6 Tb/s per switch,
backend RTT), `docs/LAB_STANDARDS.md` (generators are instructor material).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | §1.7/Summary used a 10,000 h node MTBF | Canonical 1,536 h → job MTBF 48 h (ORION-XL 3 h). Young interval √(2×12.25×172,800) = 2,057.6 s ≈ 34 min ≈ 118 steps; checkpoint overhead 0.60 %. Per failure, 900 s restart + 1,029 s rework ≈ 32 min per 48 h ≈ 1.1 %. Total ≈ 1.7 % ≈ $95k/yr. Recomputed independently before use. |
| R-02 | Major | §1.5 Fact 1 claimed 2(p−1)/p·S bounds *any* all-reduce | Now restricted to endpoint algorithms (ring/tree). In-network reduction (NVLS, SHARP) gives ≈ S; pointer to Ch 12. |
| R-03 | Major | §1.11: a Slurm requeue reruns the stored script, so a template change could not affect it | Rewritten as a failed job 48211 that the auto-resubmit tool re-submitted as **new** job 48377 from the template. Evidence: `scontrol write batch_script 48377 -`. Safe change is cancel + resubmit from checkpoint. |
| R-04 | Major | Per-rank step-time spread cannot detect a straggler | Table 1.13 and runbook step 2 now compare per-rank compute vs collective wait. The straggler has the least wait. Threshold: compute max/median > 1.1. Hypothesis 2 text updated. |
| R-05 | Major | Key: ≈ 1 replay/s cannot add 44 µs × 13k all-reduces/s | Case rebased on GPU 5's NVLinks reported `inactive` (NCCL falls back to PCIe/SHM, tens of µs per hop). GPU 2's ≈ 1/s replay rate is now a watch item. Key explains why reduced width would cost only ≈ 1 µs per all-reduce. NCCL transport lines added as a test. |
| R-06 | Minor | PP ÷ 8 assumption unstated | States it assumes Megatron-style sequence parallelism. |
| R-07 | Minor | Eq 1.1 "PFS aggregate / nodes" | "nodes in the job" (manuscript, lab README, check message). |
| R-08 | Minor | "Exercise 1.R2" reference; `[MEASURE]` | "Reflection exercise R2 in exercises.md"; `[MEASURED]` in exercises and key. |
| R-09 | Minor | 12 ms healthy TPOT p95 vs 9.5 ms decode step unexplained | Exercise text explains: p95 includes steps carrying prefill chunks under continuous batching, plus scheduler jitter. |
| R-10 | Minor | L3 `mpirun` did not export NCCL variables | `-x NCCL_DEBUG=INFO -x NCCL_IB_HCA=<rail-hca-list>` added. |
| Names | — | `hx8-r*n*` hostnames | `orion-n09`/`orion-n10` (§1.11) and `orion-n23` (exercise and key). The frontend label is now "3:1 ports, 1.5:1 bandwidth". |
| LAB_STANDARDS | — | Generator is instructor material | `check.py` reports `SKIP` (still exits 0) when `lab/tools/` is absent, tested by moving the folder. Lab and chapter READMEs no longer point learners at the generator; column units moved into the lab README. Data unchanged (it contains no hostnames), so no regeneration was needed. |
| Cuts | — | Length | Acronym paragraph compacted, Units pitfall removed, §1.10 reduced to a pointer, two Summary bullets merged. Manuscript 10,027 words (cap ≈ 10,500). |

Verification: `python lab/check.py --impl solution` → 9/9 (exit 0); starter → 1/9, exit 1, no
traceback; with `lab/tools/` removed → 8/9 + 1 SKIP, exit 0; `python scripts/validate_labs.py ch01` → OK.

Author re-score (pending independent re-review): D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5,
D8 9.5, D9 9.5 → 9.50.

---

## Independent review iteration 2 + author fixes (2026-10-30)

Independent reviewer: **9.50** (pass, no margin). Minor findings fixed to protect the pass:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N-01 | Minor | Troubleshooting key assumed a GPU with all NVLinks lost always falls back to PCIe. | Added a hedge: depending on Fabric Manager degraded-mode policy and driver version, such a GPU may instead be excluded (or block job start) `[VENDOR-SPEC, 2026-10 — verify]`. |
| N-02 | Minor | Table 1.3 said "clock-throttle reasons". | Now "clock-event reasons" (VERIFIED_FACTS GPU telemetry). |
| N-03 | Minor | L3 `mpirun -H nodeA:8,nodeB:8`. | Now `-H orion-n01:8,orion-n02:8` (canonical names). |
| N-04 | Minor | Stale iteration-1 D9 row (old word count). | Marked historical, pointing to the later review sections; manuscript is 10,027 words. |

`python scripts/validate_labs.py ch01` → OK. Score unchanged at 9.50; no open findings.

---

## Independent review iteration 3 (2026-10-30)

Independent score 9.50 (PASS). The minor findings N3-* raised at this pass are closed: the wording fixes listed in the coordinator's iteration-3 notes are applied, and `python scripts/validate_labs.py` is OK.

---

## Independent review r1 (2026-11-01)

Independent reviewer scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.0 · D8 9.5 ·
D9 9.0 → **9.45** (below gate). 0 blockers, 0 majors, 9 minors. Every finding was re-verified before
it was applied; none was rejected.

| ID | Finding | Resolution |
|---|---|---|
| N01-01 | ORION's default 24 training + 8 inference split never acknowledged | §1.4 opens with the split (`orion-n01`–`n24` Slurm, `orion-n25`–`n32` Kubernetes, full-size W-TRAIN borrows the pool, Chapter 17). Table 1.1 column is now "ORION, full-size W-TRAIN run"; Table 1.2 scheduler row names the 24-node partition and 8-node pool. The design challenge (exercises.md, exercise folder, key, model answer) now asks for a *second* pool, Option A takes 8 of the 24 training nodes (leaving 16), and the key adds a "Training capacity" row and a 1-point deduction for ignoring the existing pool. |
| N01-02 | "The one row no role scores below 2 on is observability" was false | Now "two rows … observability and automation/safe change"; the Ex 1.3 key and model answer were changed to match. |
| N01-03 | "Memory-bound unless the batch is very large" contradicted §1.6 | §1.2 now says that BF16 decode at 2k context stays memory-bound at any batch, and only short-context, weight-dominated decode nears the roof. The K4 key and model answer were changed to match (intensity cap ≈ 209 FLOP/B < 295). |
| N01-04 | W01 FLOP was 6,875 in the lab and 6,881 in the manuscript | `generate_profiles.py` and the CSV now use 6,881 TFLOP (6 × 70e9 × 4,194,304 / 256 = 6,880.7). `check.py` expects 6881/989 = 6.958 s. The lab README, the solution lab README reference table (re-run: 6.96 s), key WP1, the WP1 model answer and `solve.py` assert (6.958 ± 0.005), and the 1.1, LAB and R3 answers now give 6.96 s. The data was regenerated: only the W01 field changed, the seeded jitter is unchanged, and the classification is unchanged. |
| N01-05 | Ceiling-fraction bands had holes | Four contiguous bands: < 0.25, 0.25–0.9, 0.9–1.0 (recheck counters), > 1.0. |
| N01-06 | "≈ 5 h at half speed" was unsupported by the log | Two log lines added: an 18:21 page and an 18:52 `scancel 48377`, with resubmission as 48390. Validation now computes 13:49–18:52 = 5.05 h → 32 × 5.05 × 0.5 ≈ 81 GPU-h. The detection delay is explained (alert keyed on job ID, no baseline), and a fix is given. |
| N01-07 | The design-challenge key misstated the BOM saving | Now "64 fewer backend NICs, 64 fewer rail-leaf host ports, 128 fewer 400G optics (both ends), plus the matching leaf-uplink/spine capacity at 1:1", in both the key and the model answer. |
| N01-08 | Figure 1.2's H2D volume ignored pipeline staging | Figure 1.2 now shows ≈ 2.1 MB per first-stage node (16.8 MB ÷ 8), and the caption says the last-stage nodes read labels. §1.9 Step 3 gives both the 0.52 MB average and the 2.1 MB first-stage figure (T_io ≈ 0.0004 s, negligible). The 1.1 model answer was changed to match. |
| N01-09 | Unwrapped source lines | Prose lines over ≈ 105 characters were rewrapped to ≈ 100 in the manuscript, key, exercises.md and the DC exercise README (tables and code blocks left as they are). |
| D2 advice | Inference failure modes were thin | New §1.4 list: KV cache exhaustion (670 → 335 sequences at 4k context), one degraded replica owning p99 (1/8 = 12.5 % of requests ≫ 1 %), and cold-start storms (7 TB at an assumed 100 GB/s ≈ 70 s) `[ILLUSTRATIVE]`/`[MODELED]`. |
| D8 advice | Runbook was training-only | Added an inference trigger: one replica's TPOT p95 > 1.5 × the fleet median for 10 min `[ILLUSTRATIVE]` → drain the replica, then diagnose. |
| D9 extra | $95k vs $96k checkpoint cost | Recomputed: (0.595 + 1.116) % = 1.71 % × $56.1k ≈ $96k; §1.7 now shows this. |

Not done: the D4 suggestion that starter FAIL messages name the offending row. The starter returns
TODO, by design; once a learner implements a function, the checks already name the wrong rows (for
example "misclassified (got, want): …"). Committed L2 measured bundles were not edited.

Verification: `python lab/check.py --impl solution` → 9/9 PASS; `--impl starter` → 1/9, 8 TODO, no
traceback; `python scripts/copyedit_lint.py ch01-ai` → 0 findings; `python scripts/validate_labs.py`
→ see the coordinator's run. Manuscript is 10,555 words (was 10,138).

Author re-score (pending independent re-review): D1 9.5 · D2 10 · D3 10 · D4 9.5 · D5 10 · D6 10 ·
D7 9.5 · D8 10 · D9 9.5 → 9.78.

---

## Independent review r2 (2026-11-01)

Independent reviewer scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.0 · D8 9.5 ·
D9 9.5 → **9.475**. 0 blockers, 0 majors, 5 minors. All five were re-verified and applied.

| ID | Finding | Resolution |
|---|---|---|
| R01-01 | The troubleshooting case had 12 replicas, one of them on the training node `orion-n23` | The case now uses `orion-n29` plus the other seven replicas of the default pool (`orion-n25`–`n32`), consistent with §1.4. The folders were renamed `TS-slow-replica-n29` (exercise and solution) and the index, meta.yaml and marking.json updated. The absorb arithmetic is now 8/7 = +14.3 %, with a worst-case linear TPOT p95 of 12 × 1.143 = 13.7 ms against the 50 ms SLO. `solve.py` asserts both, and its outputs were regenerated. The 1.1 model answer now reads "one of the eight default-pool replicas = 12.5 %". |
| R01-02 | "10 % slow" was ambiguous | §1.1 now says "runs at 90 % of its peers' speed … 0.10 × 256 = 25.6". The K2 prompt (exercises.md and folder) matches, and the key accepts the 10 %-longer reading (9.1 %, 23.3 GPU-equivalents). |
| R01-03 | The Ex 1.2 key ignored B's existing 40 GB of NVLink traffic | Now (40 + 30) / 450 = 0.156 s in the key, the model answer and `solve.py` (assert and outputs regenerated). The conclusion is unchanged: compute-bound at 0.404 s. |
| R01-04 | The L2 report cited Section 1.7 for `utilization.gpu` | Changed to Section 1.6 in the `experiment.py` template and in the committed report's prose cross-reference. No measured value was touched. |
| R01-05 | The Table 1.2 scheduler row implied W-TRAIN fits in 24 nodes | It now adds "a full-size run borrows the 8 inference nodes, Section 1.4". |
| Price | The canonical rate is now $3.00/GPU-hour (Chapter 21's TCO per nominal GPU-hour) | §1.7 cites Chapter 21: $6,727,680/yr, 1 % ≈ $67k, 5 % ≈ $336k, checkpoint overhead 1.71 % ≈ $115k. Summary: $6.7 M, $67k. DC: pool $1,681,920/yr, reclaimable ≤ $672,768/yr, "$1.7 M". K1 is ≈ $67,000 and K2 is $76.80/h. The DC and K2 `solve.py` outputs were regenerated, and meta.yaml/marking.json updated. |
| D1 advice | The TP/PP sequence-parallelism mix was unflagged | The Table 1.6 caption now states that TP counts full all-reduces and PP assumes sequence-parallel sharding. |
| D2 advice | No mechanism was given for how a hang becomes a failure | §1.1 point 5 now explains the watchdog: PyTorch's NCCL process-group default timeout is 10 min, so 10 min × 256 GPUs ≈ 43 GPU-h `[MODELED]`. |
| D3 advice | No figure for the reading bands | Added Figure 1.5, the four ceiling-fraction bands. |
| D6 advice | The conventional-fleet bandwidth figure had no qualifier | It is now an explicit order of magnitude, "not a survey figure". |
| D8 advice | The runbook had no priced stop condition | Step 1: half speed wastes ≈ 128 GPU-h/h (≈ $384); after 30 min (≈ 64 GPU-h) with no proven cause, checkpoint and requeue on known-good placement. |

Not done: the D4 suggestion of automated checking of `data_quality.md`. It would add a free-text check to the
grader, which we judged too brittle.

Verification: `lab/check.py` solution 9/9, starter 1/9 (graceful); `validate_labs.py ch01` OK;
`copyedit_lint.py ch01-ai` 0 findings. Manuscript is 10,787 words.

## Repetition pass (2026-11-04)

- Table 1.1: dropped the "Network per server", "Dominant traffic" and "Rack power" rows, which repeated the numbers in properties 2–4 just above. The caption now says the table covers the consequences of coupling and failure.
- Section 1.1, inference paragraph: the degraded-NVLink-replica sentence is now a short clause pointing to the Section 1.4 failure mode "One degraded replica owns the tail", which keeps the numbers.
- Section 1.4, weight loading: removed "and much longer if fifty replicas start at once"; the cold-start-storm bullet below covers it with the ≈ 70 s number.
- Section 1.11: the GPU-utilization trap is now a pointer to the Section 1.6 pitfall and is no longer re-explained.
- Runbook step 2: the straggler rule (longest compute, least collective wait) now points to Table 1.13; the explanation stays in the Table 1.13 caption and in hypothesis 2.
- Summary: the training/inference bullet copied Section 1.2 almost word for word; it has been rewritten as a summary.
- Kept on purpose: the ring all-reduce formula and the TP/PP/DP bullets in Section 1.5 (the arithmetic needs them; both point to Chapters 11 and 12); the Realism boundary restating the lower-bound caveat; Table 1.12, which reuses Table 1.7 evidence (it is the worked example); Hands-on/lab overview.
- Words: 10,782 before, 10,691 after. `copyedit_lint.py`: 0 findings; `lab/check.py --impl solution`: 9/9.
