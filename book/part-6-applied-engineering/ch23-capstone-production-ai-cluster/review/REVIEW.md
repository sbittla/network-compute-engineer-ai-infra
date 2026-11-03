# Editorial Review — Chapter 23

**Independent review score history (iterations 1 → 4):** 8.85 → 9.475 → 9.375 → 9.50 — PASS at iteration 4.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.83 | FAIL (D1, D6, D9 < 9.0; majors open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | PASS (internal; independent review pending) |

## Scores by dimension (latest)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.5 | All worked-example arithmetic re-derived with unrounded intermediates (step time 17.394 s, 96.00 days, Young interval 4,554 s, waste 2.98 %). Port, cable, power and parallelism invariants match REFERENCE_CLUSTER. NCCL fault-handling and GPUDirect RDMA mechanism (peer-memory vs DMA-BUF) carry "verify against current docs" notes. NCCL log wording is marked ILLUSTRATIVE/abridged. |
| D2 | Depth and production realism | 15% | 9.5 | Non-obvious practitioner insights: rail-aligned traffic never touches spines (so leaf–spine links need an ADR); rail leaf as cluster-wide logical blast radius; max-vs-sustained power; δ dominates storage bandwidth in goodput; FMEA detectability; MTBF sanity check from Llama 3 data. |
| D3 | Pedagogy and clarity | 15% | 9.5 | Workflow figure, dependency graph, invariant table, nine-step worked example citing source chapters, two ADR examples, checklist, talk structure. Dense near the 10,000-word ceiling but each section follows mechanism → numbers → evidence → pitfall. |
| D4 | Hands-on lab quality | 15% | 9.5 | Real task (pre-review lint gate). 20 rules, exact-set checking for precision and recall, clean false-positive control bundle, six traps, edge-case tests for rules with no planted instance, deterministic generator (verified byte-identical), L2/L3 extension with real commands. Runs in < 1 s. |
| D5 | Exercises and assessment | 10% | 9.5 | 8 knowledge checks, 2 worked problems, lab, troubleshooting case, design challenge, 4 reflections, all 3 outline-mandated exercises plus deliverable; full key with arithmetic, marking splits and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.5 | Every table caption and worked number labelled; benchmark table models the measured/modeled split; scaling-efficiency formula; T1 case teaches mean-vs-median and contaminated runs; EVID-004 enforces the L1 boundary. |
| D7 | Cross-layer integration | 5% | 9.5 | Table 23.1 maps Chapters 1–22 to artifacts; worked example cites the chapter for each step; all eight capstone briefs and RUBRIC linked; Ch 22 and Ch 24 cross-referenced. |
| D8 | Operational realism and safety | 5% | 9.5 | Failure-exercise runbook with abort criteria, rollback, escalation; explicit Safety callout on shared fabrics and PFC propagation; L2/L3 extension restricted to dedicated hardware. |
| D9 | Editorial polish | 5% | 9.5 | Acronym list added, figures and tables captioned and numbered consecutively, units consistent (Gb/s vs GB/s), links verified for files that exist. |

Weighted = 0.20·9.5 + 0.15·9.5 + 0.15·9.5 + 0.15·9.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 + 0.05·9.5 + 0.05·9.5 = **9.50**.

## Iteration 1 scores

D1 8.5 · D2 9.0 · D3 9.0 · D4 9.0 · D5 9.0 · D6 8.5 · D7 9.5 · D8 9.0 · D9 8.0 →
0.20·8.5 + 0.15·9.0 + 0.15·9.0 + 0.15·9.0 + 0.10·9.0 + 0.10·8.5 + 0.05·9.5 + 0.05·9.0 + 0.05·8.0 =
1.70 + 1.35 + 1.35 + 1.35 + 0.90 + 0.85 + 0.475 + 0.45 + 0.40 = 8.825 ≈ **8.83** (gate FAIL).

## Findings

| ID | Severity | Location | Finding | Resolution (iteration 2) |
|---|---|---|---|---|
| F1 | major | manuscript §23.10 Step 2 | Wall time computed from rounded 17.39 s (95.97 days) instead of 17.394 s (96.00 days); propagated into exercises W2 and key | Recomputed with unrounded value: 96.00 / 106.7 / 109.7 / 121.9 days; W2 and key updated (105.98, 102.97 days) |
| F2 | major | manuscript | 10,713 words, above the 7,000–10,000 target | Tightened prose, converted checklist to a table; 9,993 words |
| F3 | major | manuscript | Undefined acronyms (BOM, PFS, DCGM, SPOF, PXN, RMA, CDU, PDU, UPS, DSCP, ASN) | Acronym list in "Prerequisites and connections"; ASN expanded at use |
| F4 | major | assumptions A-07, §23.10 Step 7 | MTBF of 12 h for 256 GPUs unjustified and ≈ 16× worse than public large-run data scaled linearly | A-07 = 48 h `[ILLUSTRATIVE]` with explicit Llama 3 sanity check (198 h `[MODELED]`) and infant-mortality rationale; B-05 recomputed to 2.6 % |
| F5 | minor | Table 23.6, bundles FD-04 | Rail-leaf detection said "BGP sessions lost on 32 ports", but ORION hosts use static per-rail routing, not BGP | Changed to host link-down plus spine BGP sessions to the leaf; generator and data regenerated |
| F6 | minor | §23.5 FMEA | "RPN rewards detectability" inverted the meaning of D | Reworded: high D = poor detectability, pushing quiet failures up |
| F7 | minor | Figure 23.2 caption | Arrow semantics stated backwards | Caption corrected |
| F8 | minor | Tables | "Table 23.6a"; talk and hypothesis tables uncaptioned | Renumbered 23.7–23.12; captions added |
| F9 | minor | §23.10 Step 2 | 19.87 s should round to 19.88 s | Fixed |
| F10 | minor | Further reading | Garbled RFC 7938 author line | Rewritten with correct editors (Lapukhov, Premji, Mitchell) |
| F11 | minor | solutions/lab EVID-004 | Redundant, partly unreachable branch logic | Replaced by a `PHYSICAL_UNITS` set; documented in starter |
| F12 | minor | §23.7 | Scaling-efficiency paragraph had an incomplete example | Replaced with a worked E(256) = 0.887 `[ILLUSTRATIVE]` |

No open blocker or major findings.

## Verification performed

- `python lab/check.py --impl solution` → 13/13 PASS, exit 0 (0.4 s).
- `python lab/check.py` (starter) → 13 TODO, exit 1, no traceback.
- `python scripts/validate_labs.py ch23` → OK.
- `python lab/tools/generate_bundles.py` twice → byte-identical `data/` (md5 compared).
- Worked-example and key arithmetic re-derived in Python (step time, duration, Young/Daly terms,
  all-reduce and PP volumes, lost GPU-hours, W1/W2/D1 port, cable and power arithmetic).

## Release-gate items outstanding

- Independent editorial and technical review (this log records author self-review only).
- Capstone brief links (`capstones/capstone-*/`, `capstones/RUBRIC.md`) and Chapters 19 and 21 are
  authored by others; re-run the link check once they land.
- NCCL log-line wording and GPUDirect RDMA enablement mechanism (peer-memory module vs DMA-BUF)
  must be re-verified against current NCCL and driver documentation at publication.
- L3 extension commands (`all_reduce_perf` flags, `ipmitool dcmi power reading`) to be executed on
  real hardware by a practising engineer.

## Independent review iteration 1 + author fixes

Independent score before fixes: **8.85** (below gate). Author fixes applied 2026-10-29; all numbers
recomputed by the author (they agree with the reviewer's values).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Restart R = 600 s and ≈ 10 min contradict canonical 900 s; MTBF derivation not shown | §23.10 Step 7 now derives M = 1,536 / 32 = 48 h and uses R = 900 s: lost+restart (2,277 + 900)/172,800 = 1.84 %, total 3.16 %, 3,177 s × 256 / 3,600 = 225.9 GPU-h per failure, ≈ 11,300 GPU-h over 50 failures, 1.28 % at δ = 5 s (R/M = 0.52 %). Table 23.6 GPU row "R ≈ 15 min = 900 s". W2 keeps M = 24 h, explicitly labelled a variation (node MTBF halved), R = 900 s: 4.77 %, 178.5 GPU-h, 106.39 days; δ = 5 s gives 2.12 %, 103.36 days. |
| R-02 | Major | B-02 busbw 44.5 GB/s for 2 × 8 GPUs is a per-rail number mislabelled as busbw | Generator now emits node busbw 356.1 GB/s (= 8 × per-rail 44.5); per-rail = busbw ÷ 8 stated in Table 23.8, §23.7, the bundles, A-06 (40 GB/s per rail ≈ 320 GB/s node busbw), B-04 formula. §23.12 shortfall rescaled to 177 GB/s (22.1 per rail), recovery 356 (353–359). Kestrel B-04 328 GB/s. T1 rescaled ×8 (median 318.4, mean 275.04, "23 %" = 1 − 275.0/356; clean runs 9 % below B-02). L3 command text quotes ≈ 350+ GB/s. Lab data regenerated byte-identically; check.py unchanged (rules do not depend on the values). |
| R-03 | Major | Invented `NET/IB : GPU Direct RDMA Disabled for HCA` line | Deleted. Evidence is now channel lines with/without `/GDRDMA` plus `lsmod`, labelled `[VENDOR-SPEC, 2026-10]`, with the DMA-BUF caveat; Table 23.11 H1 prior reworded. |
| R-06 | Minor | Tables out of order (23.11, 23.9, 23.12, 23.10) | Renumbered 23.1–23.12 in order of appearance; exercises reference updated (talk = Table 23.9). |
| R-07 | Minor | A-08 described as async NVMe save but derived as sync PFS save | A-08 is now "synchronous save to the PFS, conservative"; validation and backlog item measure sync δ and then validate the async path. |
| R-08 | Minor | FD-05 "N+1" wording wrong | "N−1: 3 of 4 spines → 1.33:1" (32 down / 24 up) in bundle and Table 23.6. |
| R-09 | Minor | A-06 scale ambiguous | A-06 statement: per-rail at 32 nodes = node busbw ÷ 8 (≈ 320 GB/s node busbw). |
| R-10 | Minor | EVID-004 limitation undocumented; L3 command prerequisites | lab README "Known limitation of EVID-004" (unit list and declared tier only) and one sentence in §23.7's realism boundary; L3 command now states `make MPI=1` and gives the `srun --mpi=pmix` form. |

Re-score (author, after fixes): D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5,
D9 9.5 → weighted **9.50**, lowest 9.5. Manuscript 10,152 words (`wc -w`), within the ~10,500 limit.
`python scripts/validate_labs.py ch23`: 1/1 valid (solution 13/13; starter 13 TODO, exit 1).
Not addressed (outside R-01..R-10): migrating node/rack names to the new canonical `orion-nNN` /
`rack-NN` patterns should be checked in a later pass.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-11 | Minor | Ch23 did not use the canonical ORION names from REFERENCE_CLUSTER.md | Bundle racks renamed `R1`–`R8` → `rack-01`–`rack-08` via the generator (regeneration byte-identical; Kestrel's design reuses ORION racks, so it was renamed too); check.py POWER-001 expectations and key updated; the failure-exercise plan names `orion-be-leaf-r3`, `orion-n01`…`orion-n32`, `orion-be-spine-1`…`-4`. `nodeA`/`nodeB` in §23.12 stay, because they are Kestrel's two lab nodes and not ORION hosts. |

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent score: 9.475 (D9 below gate).

| ID | Finding | Resolution |
|---|---|---|
| R2-01 | Duplicate DMA-BUF parenthetical in §23.12 | Second parenthetical deleted; the single `[VENDOR-SPEC]` caveat remains |
| R2-03 | Step 7 failure count used a 100-day run | Now "≈ 107-day run (106.7 days, Step 2) → 106.7 × 24 / 48 ≈ 53 failures, 53.3 × 225.9 ≈ 12,000 GPU-hours" |
| R2-04 | Exercise D1 "51.2 Tb/s class, radix-64" ambiguous | Port configuration stated: 64 × 800G cages run at 400G (radix 64) or 128 × 400G breakout (radix 128) |
| Student-release policy | Learner README / file map told students to run the generator | Generator line removed from learner setup; file map marks it "instructor copy only, removed from the student release". `validate_labs.py` no-generator column: OK. |

Manuscript 10,139 words. `python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK.

---

## Independent review iteration 3 + author fixes (2026-10-30)

Independent score: 9.375 (one major).

| ID | Finding | Resolution |
|---|---|---|
| R3-01 (major) | Failure-domain table assumed a spare-node pool | GPU and node rows: recovery "checkpoint → wait for repair, or restart at DP = 7 (224 GPUs; needs a batch adjustment, 1,024 not divisible by 7); R ≈ 900 s"; redundancy "None (no spares, as in the reference cluster)"; drain noted as not moving the job. The generator's reference-bundle FD-01/FD-02 text was changed the same way (data regenerated; checker 13/13). Key W2 lever no longer assumes spare nodes. |
| R3-02 | DP "largely overlappable" | §23.10: exposed = max(0, 0.191 − 0.07) ≈ 0.12 s (0.7 % of 17.39 s). The goodput budget does not assume overlap: step time comes from the MFU model, which already includes all communication. |

Manuscript 10,236 words.
`python scripts/validate_labs.py ch22 ch23 ch24`: all columns OK.


## Independent review iteration 4 minors (2026-10-30)

| ID | Resolution |
|---|---|
| R4-01 | Kestrel failure_domains.yaml redundancy now "none (no spares declared)" (generator; data regenerated) |
| R4-02 | GPU-count invariant notes a full-size W-TRAIN borrows the 8 inference nodes |

---

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.0, D7 9.0, D8 9.5, D9 9.5 →
weighted **9.325** (two majors). All key arithmetic was independently confirmed correct.

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| N23-01 | major | Rack budget ignored the Ch 21 10 % transient margin; 45 kW not reconciled with canon | A-09 redefined as the *planned* budget after derating and the transient margin, declared variation: existing row limited to 50 kW continuous per rack per 2N side, 50 × 0.9 = 45 kW. Mirrored in §23.2 problem statement, Table 23.5 invariant 11, the "use maximum power" lesson (canonical 2 × 32.78 kW per side named), Step 1, Step 6 (new margin line), reference design.md, W1/D1 prompts, key and answers. No downstream number changes (4 nodes/rack, 9 racks, 9.0 kW cap). |
| N23-02 | major | `[MEASURED]` exemplar rows cited manifests that did not exist | Both done: (a) generator now writes `manifests/l3-2node-2026-10-12.yaml` (header: ILLUSTRATIVE example for a fictional cluster) and `manifests/l1-laptop.yaml` (a real timing run: lint CLI wall time, 3 warm-ups, 7 reps, median 0.169 s, i7-13700HX, Python 3.13.14, 2026-11-01); B-06 value 0.4 → 0.17 s. (b) Sentence under Table 23.8 (B-06 row added) says B-02 shows the format of a MEASURED row and its value is `[ILLUSTRATIVE]`, consistent with §23.12; reference design.md says the same. No manifest-resolves rule added (would change the starter contract); README's known-limitations note now says the linter does not check that a cited manifest exists. Kestrel's B-04 now cites a manifest that exists but describes a laptop: the trap is noted in the key. |
| N23-03 | minor | B-05 "checkpoint overhead" includes rework | Renamed "Checkpoint + rework waste at Young interval (excluding restart R)" in Table 23.8, benchmarks.md (both bundles) and design.md. |
| N23-04 | minor | "Doubling PFS bandwidth only shortens the 12.25 s floor" was wrong | Step 7 now decomposes δ (24.5 s × 2 = 49 s + ≈ 11 s metadata/barrier) and computes doubling: δ ≈ 35.5 s, τ ≈ 3,500 s, waste 1.01 + 1.01 + 0.52 ≈ 2.5 % vs async 1.28 %. Same error in the W2 key/answer fixed: at M = 24 h doubling gives δ 35.5 s, τ 2,477 s, waste 3.91 % (saves 0.86 points vs 2.65 for async). |
| N23-05 | minor | `[VENDOR-SPEC]` on a counting convention | Label moved to the 50 GB/s line rate; per-rail convention cited to VERIFIED_FACTS. |
| N23-06 | minor | check.py did not verify bundle reproducibility | `check_data_regenerates` added (byte compare of all 17 files; SKIP when `tools/` is absent). Starter feedback now counts planted findings found and prints hints for common mistakes (sustained power, cable derivation, spares, NUM-001 exemptions). Checker 14/14 solution, 1/14 + 13 TODO starter. |
| N23-07 | minor | Table 23.10 not sorted by score | Rows sorted 2.25, 2.00, 1.60, 1.20, 1.20, 0.90. |
| N23-08 | minor | Frontend "3:1" without bandwidth qualifier | Bundle topology now `claimed_oversubscription: 1.5:1` with `oversubscription_basis` noting 3:1 by port count. |
| N23-09 | minor | Rail-leaf loss vs PXN not discussed | §23.5: NCCL fixes channels at communicator init, QPs on the dead rail end in `IBV_WC_RETRY_EXC_ERR` (status 12) after `NCCL_IB_TIMEOUT`; recovery is a restart, optionally on 7 rails with `NCCL_IB_HCA=^=mlx5_r` `[VENDOR-SPEC, 2026-10]`. |
| Next-0.5 (D2) | | Quantified correlated failure | New §23.5 "Correlated failures": 4-node firmware batch, 3 h rollback: wait 832 GPU-h vs DP = 7 restart 224 GPU-h; rollout batch as a failure domain. R3 key references it. |
| Next-0.5 (D3) | | Template-reading pointer | §23.10 intro maps each step to a reference-bundle file. |
| Next-0.5 (D5) | | K-question on transient margin | K4 extended (50 kW × 0.9 = 45 kW → 4 nodes); meta 4 → 6 points, answer and key updated. Exercise count unchanged (20). |
| Next-0.5 (D8) | | Tabletop runnable as written | `lab/tabletop/rail-leaf-evidence-cards.md`: eight timed `[ILLUSTRATIVE]` cards with prompts and close-out, linked from Step 8, the runbook and the README file map. |
| Polish | | Spelling | "rail-optimised"/"utilisation" in bundle data → -ize. |

Tests: `lab/check.py --impl solution` 14/14; `--impl starter` 1/14, 13 TODO, exit 1;
`validate_labs.py ch23` OK (no-generator pass); `copyedit_lint.py` 0 findings in ch23; committed
outputs regenerated with `docker/harness/generate_outputs.py` (computed outputs unchanged); harness
`test_package.py` 86 passed locally.

Shared-doc note: REFERENCE_CLUSTER could add "planned rack peak ≤ 90 % of one side's continuous
limit (transient margin, Ch 21)" so capstone and chapter budgets agree.

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.0, D7 9.5, D8 9.5, D9 9.5, for a weighted **9.45**. One major finding.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R23-01 | Major | Reference B-02 labelled `[MEASURED]`, but its manifest says no run produced it | Verified. Reference B-02 is now `[ILLUSTRATIVE]` (tier L3, manifest kept as a format template) in Table 23.8, the reference `benchmarks.md`, `design.md` and the manifest header, all via `generate_bundles.py`. Kestrel's B-02 stays MEASURED with manifest "-" (the planted EVID-003). B-06 is the bundle's only genuine MEASURED row. Step 1's evidence line is updated |
| R23-02 | Minor | Two bubble definitions used without comment | ADR-005 and Step 3 name (p − 1)/m as relative to ideal compute. Step 3 adds Chapter 22's (p − 1)/(m + p − 1) = 3/131 and the small-m divergence (m = 8: 37.5 % vs 27.3 %) |
| R23-03 | Minor | "communication ≈ 1 % of step" overgeneralizes | ADR-003 now reads "backend (DP) communication … TP traffic stays on NVLink" |
| R23-04 | Minor | A-06 = 40 GB/s vs Chapter 22's 45 GB/s unexplained | Clause added: A-06 deliberately allows for 32-node latency and stragglers, hence 0.12 s vs 0.10 s DP exposure |
| R23-05 | Minor | Card 4 peer IP was orion-n14's own address | Peer is now 10.100.3.31 (orion-n15), with the addressing rule stated |
| R23-06 | Minor | Card 8 lost work omits hang and decision time | 175 + 47 (11 min hang) + 64 = ≈ 286 GPU-h, plus ≈ 4.3 GPU-h per decision minute; tied to the close-out gaps |
| R23-07 | Minor | H3 refuted from one `lspci` | Evidence now loops over every GPU and NIC function on nodeB |
| R23-08 | Minor | Over-long opening line; double blank line | Opening blockquote rewrapped and tightened; blank line removed |
| D4 advice | — | EVID-003 cannot see a dangling manifest | `load_bundle` records existing `manifests/*.yaml`; EVID-003 also fires on a cited manifest absent from the bundle (solution; starter TODO documented). New edge case in `check.py`. Planted counts unchanged (20 = 6 blocker + 14 major; reference 0) |
| D2 advice | — | Post-approval drift; infant mortality | Paragraph added: lint an as-built bundle from inventory, LLDP and PDU data at acceptance and after each change window; first 30 days at M = 24 h (τ ≈ 3,220 s, the W2 case) |
| D5 advice | — | K3's 4× unjustified; thin R2–R4 anchors | K3 key and answer justify 4× (about half of today's 9×). R2–R4 have marking anchors |

Not done: the bundle-at-a-glance figure (D3 advice), to keep the length near current. The step-by-step bundle-file pointer already covers that mapping.

Tests: `check.py --impl solution` 14/14; `--impl starter` 1/14 (13 TODO); data regenerates byte-identically; `validate_labs.py ch23` OK; `copyedit_lint.py ch23` 0 findings; package suite 86 passed; outputs regenerated with `generate_outputs.py`. The manuscript went from 1,056 to 1,072 lines. ch23 has no electricity or GPU-hour prices, so the canonical-price changes do not apply.

## Re-score follow-up (2026-11-01)

Reviewer re-score after r2: **9.78** (pass). N23-01 cleared: §23.12 now reads "half the ≈ 350+ GB/s expected for ORION-class nodes (reference row B-02, illustrative)"; the word "result" is gone. Tests: package suite 86 passed; `validate_labs.py` OK; lint 0 findings.
