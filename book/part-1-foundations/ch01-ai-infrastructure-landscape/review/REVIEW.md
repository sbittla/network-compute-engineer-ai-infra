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
