# Editorial Review — Chapter 19

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.15 | Fail (open majors) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.53 | Pass (internal) |
| I-1 | 2026-10-30 | Independent reviewer, iteration 1 | 9.15 | Fail |
| I-2 | 2026-10-30 | Independent reviewer, iteration 2 | 9.50 | Pass |
| 3 | 2026-10-30 | Author fixes for iteration-2 findings | see below | Submitted |

## Scores by dimension (latest)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy | 20 % | 9.0 | 9.5 | Xid table with 94/95 handling per docs/VERIFIED_FACTS.md; NCCL_IB_TIMEOUT default stated by version (18 ≤ 2.22, 20 ≥ 2.23); retry-budget arithmetic matches the lab timing; row-remapper semantics; DR4 RX-power thresholds; all labelled VENDOR-SPEC. |
| D2 | Depth and production realism | 15 % | 9.5 | 10 | Section 20.1 covered end to end: taxonomy, signatures, isolation path, containment with fault domain vs scheduling unit, evidence preservation, recovery, retry-loop cost quantified, spares sized. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | Five figures (fault domains, isolation path, GPU↔HCA↔switch data path, recovery state machine, tenant layers); nine-step worked example. |
| D4 | Lab quality | 15 % | 9.5 | 9.5 | 12 checks; one flaky HCA, one ECC fault, NCCL timeout, plus five red herrings, unsafe checkpoint, bad spare, FMEA and isolation errors; SKIP without generator. |
| D5 | Exercises and assessment | 10 % | 9.0 | 9.5 | Standard set + M1–M4 covering risk register, isolation model, recovery test plan, 512-node incident evidence pack. |
| D6 | Measurement rigor / labels | 10 % | 9.0 | 9.5 | Canonical MTBF 1,536 h / restart 15 min used and labelled; proven-vs-correlated framework with intervention requirement. |
| D7 | Cross-layer integration | 5 % | 9.0 | 9.5 | orionxl-nNNN names; ties to Ch 5, 10, 14, 16–18, 20–21, Capstones F/G. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Read-only-until-step-4 runbook; safety callouts on resets and link disables. |
| D9 | Editorial polish | 5 % | 9.0 | 9.0 | 9,362 words; acronyms defined; some long tables. |

Weighted: iteration 1 = 0.20×9.0 + 0.15×9.5 + 0.15×9.0 + 0.15×9.5 + 0.10×9.0 + 0.10×9.0 + 0.05×(9.0 + 9.5 + 9.0) = 9.18; iteration 2 = 0.20×9.5 + 0.15×10 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×(9.5 + 9.5 + 9.0) = 9.55. Lowest dimension 9.0 (D9).

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | §19.3 Table 19.3 | Xid 94/95 actions did not match verified handling. | 94: drain when convenient, then reset; 95: drain immediately. Key K3 updated. |
| F2 | Major | §19.4, §19.11, W2 | NCCL_IB_TIMEOUT default stated without version. | Version-dependent default stated; lab assumes a 2.21-class build; W2 explores 20. |
| F3 | Major | Package | Node names (xl-nNNN, 0-based) not canonical. | orionxl-n001..n512 (1-based), orionxl-be-leaf-rR-gGG, orionxl-sNN spares; data regenerated; text and key updated. |
| F4 | Major | Reliability numbers | Needed to match the canonical assumptions. | MTBF 1,536 h, 48 h / 3 h job MTBF, restart 15 min used throughout (§19.1, §19.7, W1, W2). |
| F5 | Minor | §19.11 | Optic power interpretation lacked the receiver-sensitivity anchor. | Added DR4 ≈ −5.9 dBm sensitivity and warn/critical thresholds. |
| F6 | Major | lab/check.py | Failed with generator stripped. | SKIP without tools/; READMEs mark generator instructor-only. |
| F7 | Minor | §19.11 | "43 min" vs data 42.3 min. | Corrected to 42 min. |

## Release-gate items outstanding

- External review by a GPU-cluster reliability engineer; verify Xid table and row-remapper behaviour
  against current NVIDIA documents per GPU generation.
- Verify PyTorch watchdog default and flight-recorder variables for the PyTorch release in use.
- Run the L3 link-flap survival trials on a dedicated partition to convert the retry-budget model into
  `[MEASURED]` evidence.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent score: 9.15 (fail). All findings resolved; data regenerated; labs re-validated.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Spare pool undeclared, 3-day MTTR | Declared variation outside the partition, Poisson P99 at 5-day MTTR: mean 40 → 55 nodes (orionxl-s00–s54, 10.7 %); lab's 8 entries explained (47 already substituted); W2(c) key uses quantiles (36 at 3 d, 55 at 5 d) |
| R-02 | Major | Elastic granularity wrong | One DP replica = 8 nodes; re-packed 59 replicas (−7.8 %) vs not re-packed expected ≈ 33 left / worst 24; DP 59 batch divisibility; D1 and key recomputed |
| R-03 | Major | §20.1 checkpoint depth | New subsection: DCP `async_save`, Megatron `--async-save` (torch_dist), staging, persisting, commit consistency boundary; Table 19.6 metrics from the lab (72 s completion latency, unsafe window, detect/reschedule/restore decomposition) |
| R-04 | Minor | Watchdog citation | PyTorch 2.x `init_process_group` docs; `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC`; large jobs raise timeouts |
| R-05 | Minor | MPS wording | Separate address spaces; gaps are capacity, performance, and shared fault exposure (manuscript, Table 19.7, K7 key) |
| R-06 | Minor | Missing Xids | 119/120 (GSP), 154, NVSwitch SXid and fabric-manager behaviour added |
| R-07 | Minor | −7.8 dBm steady unrealistic | DOM now marginal (−5.6 to −6.4 dBm) around DR4 sensitivity; host TX −5.8 dBm; arithmetic re-derived |
| R-08 | Minor | RTO vs canonical 15 min | Reconciled: watchdog + 16-min requeue + 12-min restore; improvement path stated |
| R-09 | Minor | Naming/addressing | orionxl-be-leaf-pPP-rR, orionxl-be-spine-p06-03, host links 10.(130+R) — data, checker, text |
| R-10 | Minor | Xid PCI format | Data now `(PCI:0000:5d:00)`; checker parses the Xid from events.jsonl |
| R-11 | Minor | M3, VNI vs P_Key | M3 requires a tabletop run report; tenants.yaml comments; switch-side P_Key enforcement |
| R-12 | Major | Spares conflict in T1 key and §19.13 | T1 key: checkpoint + `scontrol requeue`, borrow node or wait, break-even 5.6 h; §19.13 rewritten for the 24-node partition with a borrowed inference node |

Also fixed: GPUDirect RDMA evidence wording aligned with docs/VERIFIED_FACTS.md (`/GDRDMA` channel
lines; DMA-BUF); tables renumbered in order. Author re-score: D1 9.5, D2 10, D3 9.5, D4 9.5, D5 9.5, D6 9.5,
D7 9.5, D8 9.5, D9 9.0 → 9.55. Manuscript 9,988 words.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score history: 9.15 → 9.50.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Minor | Canonical restart includes detect | Reconciliation states detect + reschedule + restore + warm-up with early hang detection |
| R2-02 | Minor | Megatron async-save mechanics | Background process writes; finalisation (metadata commit) called from the training loop |
| R2-03 | Minor | Long lines | Prose paragraphs reflowed to ≤ 112 characters (tables unchanged) |

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.5, D2 9.0, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.0 → **9.40** (below
gate; D2 held at 9.0 by N19-01). Checker at review: solution 12/12 (exit 0), starter 1/12 (exit 1).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N19-01 | Major | Isolation model omits GPU/RDMA-specific escape paths | New Section 19.9.1 with Table 19.7a (toolkit env-var injection and its `config.toml` keys / volume-mount or CDI injection, PSA `baseline`/`restricted`, RDMA netns exclusive + SR-IOV VFs, toolkit CVE-2024-0132 tracked in the Ch16 matrix, NetworkPolicy default-deny with YAML), each with how to audit; limits of PSA and NetworkPolicy stated. Lab: `pod_security` per tenant and three policy keys; planted `GPU_INJECTION_BYPASS` (acme-dev/notebook-7 sets `NVIDIA_VISIBLE_DEVICES=all` with no GPU request under `baseline` PSA); generator, data, solution, starter docstring, checker (10 → 11 violations), lab README, key, M2/R4/L1 answers and outputs updated. Following tables renumbered 19.7a/b → 19.7b/c (M3 answer reference updated) |
| N19-02 | Minor | Early-abort saving ≈ 9 vs ≈ 10 min | Both places now ≈ 9 min (10-min watchdog less ≈ 1 min to recognize the signature) |
| N19-03 | Minor | Megatron `--async-save` prerequisite | Added "current main also requires `--use-persistent-ckpt-worker`; verify per release" |
| N19-04 | Minor | $3/GPU-hour inconsistent with other chapters | Canonical $2.50/GPU-hour `[ILLUSTRATIVE]`: worked example 9,091 GPU-h ≈ $22,700; W1(c) 5,461 GPU-h/day ≈ $13,700/day (≈ $5.0M/year); exercises.md, W1 folder prompt, key, W1/L1/M4 answers, W1 solve.py (re-run, outputs regenerated) |
| N19-05 | Minor | "Section 20.1" reads as this book's Ch20 | "course-outline §20.1" in exercises.md, README, exercise index, M4 prompt and meta |
| N19-06 | Minor | K6 coinciding case | PSU/motherboard (whole-node fault) given as the coinciding case; the 4-GPU replica presented as the unit shrinking toward the domain (key and K6 answer) |
| N19-07 | Minor | MPS wording contradicts Ch17 | No change in Ch19 (correct for Volta+); fixed in Ch17 (N17-04) |
| N19-08 | Minor | T1 averages do not show the x8 cap binding | Evidence adds per-NIC burst peaks (mlx5_2 ≈ 205 Gb/s, others ≈ 370 Gb/s); key and T1 answer explain the duty-cycle dilution |

Also: epigraph shortened and an unused acronym (CNP) removed to offset the new section (manuscript
+≈ 30 lines). Tests: `check.py --impl solution` 12/12 (exit 0), `--impl starter` 1/12 (exit 1);
`docker/harness/test_package.py` 90 passed; `validate_labs.py` OK for ch19; `copyedit_lint.py` 0 findings
in ch19. Shared-doc change needed: add $2.50/GPU-hour `[ILLUSTRATIVE]` to REFERENCE_CLUSTER.md.

---

## Independent review r2 (2026-11-01)

Reviewer scores (independent, after the r1 fixes):

| Dim | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|---|
| Score | 9.5 | 9.0 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.0 | **9.40 (FAIL)** |

Checker at review time: solution 12/12 (exit 0), starter 1/12 (exit 1).

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| R19-01 | Major | Silent data corruption missing | New §19.4 subsection "Silent data corruption": why it evades every error- and timeout-based detector (ECC protects storage not arithmetic; the all-reduce completes and spreads bad gradients); gradient vs local-update signatures; detection by loss/grad-norm anomaly rules, cross-replica parameter checksums, golden-batch replay with bisection, and `dcgmi diag -r 3/4` plus vendor screens `[VENDOR-SPEC]`; containment by restoring the newest checkpoint *before* the onset. Llama 3 is cited only for listing SDC among the root causes of its 419 unexpected interruptions; Dixit et al. (Meta 2021) and Hochschild et al. (Google 2021) were added to Further reading. Also added: an SDC row in the distributed-signatures table, objective 4, an acronym, a summary bullet, a chapter-card mention, the realism boundary ("the lab has no SDC case"), and a new knowledge check K9 (folder, meta, answer, key, index; exercise count 22). |
| R19-02 | Minor | §19.7 said the second spare is in repair | Verified against `spares.csv`: s00 failed acceptance, s01 ready, s02 in repair. The text now names s00 and the third spare, s02. |
| R19-03 | Minor | "only four of those are `ready`" | Verified: the file has five ready spares. The text now lists them (s01, s03, s04, s06, s07), plus s05 reserved, s02 in repair and s00 failed. The R3 answer was corrected from four to five. |
| R19-04 | Minor | L2 cross-reference "exercise K4" for SW_POWER_CAP | Lab README and `lab/l2/experiment.py` now point to Section 19.3 "Thermal and power events". The committed `report.md` was **not edited**, because it is measured evidence and cannot be re-run. The lab README notes that it still cites K4 and should be read as Section 19.3. |
| R19-05 | Minor | Retry budget stated as fact | Now "in this model", with the caveat that local link-down survival depends on HCA firmware and driver, RoCE vs IB, and NCCL's async-event handling, and that the L3 flap test measures it. |
| R19-06 | Minor | Unsafe window "hang at +62 s" | Verified: ckpt-0085 started 03:40:00, link down 03:41:02 (+62 s), first NET/IB error 03:41:11 (+71 s). The table and the §19.7 sentence are corrected. |
| D2 → 10 | — | Faster hang detection | Step 8 now describes a job-level progress heartbeat (minimum completed sequence number) `[ILLUSTRATIVE]`. |
| D5 → 10 | — | Point allocations | The key lists points for K1–K9 and R1–R4. |
| D7 → 10 | — | Fabric assumed in the isolation table | The Table 19.8 caption states that ORION-XL's backend is RoCEv2, and that the IB row is for IB fleets and comparisons. |
| D8 → 10 | — | Abort criteria for the quarantine bot | §19.13 adds a rate limit, a false-positive budget from "no fault found" repairs, and auto-suspension `[ILLUSTRATIVE]`. |
| D9 | — | Polish | Tables renumbered sequentially (19.2a/19.7a–c → 19.1–19.12) across the manuscript, exercises, key and folders; the acronym block reflowed; the GPU-sharing paragraph that duplicated Table 19.8 / Ch17 Table 17.3 was cut. |
| Price | — | Coordinator correction | $2.50 → $3.00/GPU-h `[ILLUSTRATIVE]`, cited as Chapter 21's owned-cluster TCO of $3.02 per nominal GPU-hour `[MODELED]`, rounded. The worked example is 9,091 GPU-h ≈ $27,300. W1(c) is 5,461 GPU-h/day ≈ $16,400/day (≈ $6.0M/yr); the solver was re-run (16,384). |

Not done: the D3 timeline figure and D4 starter failure messages (scope and length). The D6 note on p = 0.001 was left alone because it is a stated `[ILLUSTRATIVE]` assumption, not a dataset property. The manuscript is 11,023 words (+4.5 %), with cuts in §19.3, §19.4, §19.7, §19.8, §19.10, the Pitfall, the summary and Further reading offsetting part of the growth.

Tests: `check.py --impl solution` 12/12 (exit 0); `--impl starter` 1/12 (exit 1); `validate_labs.py ch19` OK; package test suite 94 passed; `copyedit_lint.py` 0 findings in ch19. Outputs were regenerated with `docker/harness/generate_outputs.py`.

### r2 re-score fixes (2026-11-03)

| ID | Finding | Resolution |
|---|---|---|
| R19-07 | The $3.00/GPU-hour price was labelled `[ILLUSTRATIVE]` although it is the Chapter 21 TCO | Relabelled `[MODELED]` (Chapter 21 owned-cluster TCO $3.02, rounded) in the manuscript, exercises.md and folder prompts, key, answers, meta.yaml and solve.py comments; outputs regenerated. Tests: check.py solution/starter as before, `validate_labs.py` OK, package tests pass, `copyedit_lint.py` 0 findings. |
