# Editorial Review — Chapter 20

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.20 | Not passed |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.58 | Passed (internal) |
| 3 | 2026-10-29 | Independent review iteration 1 | 9.00 | FAIL |
| 4 | 2026-10-29 | Independent review iteration 1 + author fixes (author re-score) | 9.55 | Pending independent confirmation |
| 5 | 2026-10-29 | Independent review iteration 2 | 9.50 | PASS (no margin) |
| 6 | 2026-10-29 | Independent review iteration 2 + author fixes | — | Awaiting independent confirmation |
| 7 | 2026-10-29 | Independent review iteration 3 | 9.50 | PASS |

## Scores by dimension (author self-review, iteration 2 — 9.58, superseded by the independent scores above)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | MTU budget derived from RoCEv2 header sizes (BTH 12, ICRC 4, RETH 16, AETH 4) with explicit L2 overhead; InfiniBand MTU set correct; API semantics (gNMI replace/update, Kubernetes `resourceVersion`/server-side apply, NETCONF confirmed commit, Terraform saved plans) checked; tool names given as classes where unsure; version-sensitive tables flagged `[VENDOR-SPEC, 2026-10]`. Residual risk: vendor MTU-accounting differences are called out but cannot be pinned without a platform. |
| D2 | Depth and production realism | 15 % | 9.5 | Covers failure modes practitioners hit: non-idempotent operations, check-then-act races, two writers on one field (troubleshooting), truncated-input reconcilers (Exercise 20.8), anti-rollback firmware, stale QPs after an MTU change, hold-on-missing-evidence, stratified canaries. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Progression: why → interfaces → reconcile → IaC → validate → deliver → stage → rollback → guard → audit → worked example. Every concept has a diagram, table, or code sketch; the worked example is fully computed and includes the honest result that the big bang is cheaper in expectation but not in tail risk. |
| D4 | Hands-on lab quality | 15 % | 10 | Three-part lab mirroring real tasks (reconciler, rollout controller, change review); deterministic seeded data (byte-identical regeneration verified); 13 checks with TODO/PASS/FAIL; plants verified to trap naive implementations (precheck-less controller aborts wave 1 on AC5; `min`-based busbw aborts wave 1 on AC1); L2/L3 extensions with real commands and manifest fields. |
| D5 | Exercises and assessment | 10 % | 9.5 | Full standard set plus the three outline-mandated exercises (20.5, 20.6, 20.7) and the deliverable (20.10); ★–★★★ range; evidence lines; complete key with arithmetic, marking points and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | All quantitative claims labelled; noise-sized thresholds (median standard error computed); measured vs simulated vs modeled kept distinct; L3 extension follows LAB_STANDARDS §5. |
| D7 | Cross-layer integration | 5 % | 9.5 | Uses ORION naming, QoS plan, MTU plan, W-TRAIN step time; ties to Ch 7–9 (fabric/QoS), 16 (bundles, waves, lifecycle states), 17 (drain/reservations), 18 (incident), 19 (blast radius), Capstones E/F. |
| D8 | Operational realism and safety | 5 % | 10 | Runbook excerpt with signals/thresholds/escalation; explicit Safety callouts; every exercise targets simulation/lab/tabletop. |
| D9 | Editorial polish | 5 % | 9.0 | Acronyms now defined on first use; figures and tables captioned and numbered; links checked. Manuscript sits at 9,998 words, at the top of the 7,000–10,000 range, leaving no headroom for reviewer-requested additions without cuts. |

Weighted = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×10 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×10 + 0.05×9.0 = **9.58**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript | Draft was 10,706 words (over 10,000 limit). | Trimmed redundant prose, merged §20.6.3 into the trade-off table, condensed summary/realism; now 9,998. Iter 2. |
| F2 | Major | manuscript | Acronyms (RDMA, DSCP, BMC, IPMI, gNMI, NETCONF, YANG, CMDB, PXE, SLO, NCCL, ECC, ACL, IPAM, CLI, header fields in Fig 20.2) not defined on first use. | Expanded at first use; Figure 20.2 caption defines header fields. Iter 2. |
| F3 | Major | §20.11 step 5 | Claimed an MTU change "breaks established RDMA connections" — imprecise. | Reworded: queues briefly reinitialise on many NICs; established connections keep their old path MTU until re-created. Iter 2. |
| F4 | Minor | §20.11 step 1 | Efficiency gain stated as 5.8 % (rounded inputs); exact is 5.9 %. | Corrected with 4-digit inputs. Iter 2. |
| F5 | Minor | lab/README §4 | Section references pointed to wrong manuscript sections after restructuring. | Re-mapped to §20.3–§20.11. Iter 2. |
| F6 | Minor | manuscript tables | Non-sequential table numbering (20.12a) and gap after removing §20.6.3. | Renumbered 20.1–20.14; cross-references in exercises/key verified (20.8 time-to-signal, 20.11 safety controls). Iter 2. |
| F7 | Minor | lab/README §8 | `gnmic` example omitted credentials. | Added `-p "$GNMI_PASSWORD"`. Iter 2. |
| F8 | Minor | lab code | Lab README asks learners to try a `min`-based controller, but `_aggregate` did not support `min`. | Added `min` to the provided helper in starter and solution; verified the trap fires (wave 1 → abort on AC1 for `orion-n09`). Iter 2. |
| F9 | Minor (open, accepted) | check.py Part 3 | Expected gap IDs are stored as salted SHA-256 hashes; a learner could brute-force them from the 20-entry catalogue. | Accepted: README states the checker is a progress meter; instructor grading of reasoning is 10 + 15 points of the rubric. |

## Lab validation

- `python lab/check.py --impl solution` → 13/13 PASS, exit 0.
- `python lab/check.py --impl starter` → 13 TODO, exit 1, no traceback.
- `python scripts/validate_labs.py ch20` → `1/1 labs valid`.
- `python lab/tools/generate_data.py` twice → byte-identical `data/` (md5 compared); `data/` ≈ 96 KB.

## Release-gate items outstanding

- External review by a practising fabric/automation engineer of §20.5 MTU rules and §20.13 scenario.
- L2 extension run on a real host (soft-RoCE acceptable) and L3 canary on a lab fabric; record manifests.
- Verify `[VENDOR-SPEC, 2026-10]` items (Redfish/gNMI/Kubernetes/Terraform semantics) against current docs at publication.

## Independent review iteration 1 + author fixes

The independent reviewer scored the chapter 9.00 (FAIL) with four majors and seven minors
(docs/REVIEW_STATUS.md). The parent added an addendum asking for consistency with
docs/VERIFIED_FACTS.md and the canonical names. Each finding and its resolution:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R20-01 | Major | Claimed host MTU 9,216 breaks RoCE | §20.5.1 rule 2, §20.11 Step 2, key (planted-flaw table, 20.4a) now state that RoCE is bounded by the 4,096 path MTU and is unaffected; backend TCP/UDP black-holes at the 9,216 port. Marking note added. |
| R20-02 | Major | Vendor MTU conventions | Pitfall replaced by a vendor implementation note (EOS/NX-OS L3 `mtu` = IP MTU; Junos media MTU includes L2 header; `[VENDOR-SPEC, 2026-10]`, verify). The +22 B rule is described as a conservative portable policy, exact only for full-frame conventions. |
| R20-03 | Major | n06 host MTU 1,500 with path MTU 4,096 is impossible | Generator sets n06 observed `rdma_path_mtu` = 1,024 (the largest IB MTU under a 1,500 netdev MTU). Plan is now 24 actions on 22 targets; check.py `EXP_ACTIONS` = 24 plus the n06 RDMA drift expectation; manuscript Step 3/4, lab overview and key updated; data regenerated (byte-identical on re-run). On hardware, n06's RDMA action becomes a read-back check (stated). |
| R20-04 | Major | MTU-cap mechanism for rack-03 to rack-08 unexplained | §20.11 Situation explains `active_mtu` = min(port max RDMA MTU, largest IB MTU fitting the netdev MTU), cross-references Ch 8 §8.7, and attributes the 1,024 cap to an old host profile's vendor-specific RoCE MTU setting. |
| R20-05 | Minor | PFC ratio was 1.6× | Recomputed from data: 1.69× (n25) and 1.80× (n29). Text and key say 1.7–1.8× (≈ 30 → 55/s). |
| R20-06 | Minor | Firmware timeline inconsistent (fleet already on 28.43.1014 before the 28.42 → 28.43 rollout) | Part 1 fleet default and observed firmware are now 28.42.1000; the 28.43.1014 rollout (CHG-2026-1110) comes after the MTU change (CHG-2026-1103), as stated in Step 7. |
| R20-07 | Minor | Standard error understated (0.09) | Now the SE of the difference of medians: √(0.09² + 0.13²) ≈ 0.16 GB/s, so a 2.2 GB/s threshold is ≈ 14 SE. |
| R20-08 | Minor | Step 5/7 framing | Step 4 notes that production batches are the waves; Step 5 states that the 32-node plan is an upper bound here and exact for the companion firmware change; Step 7 is retitled as the companion change. |
| R20-09 | Minor | Commit-confirm needs vendor detail | Table 20.10 row names Junos `commit confirmed` and NETCONF `:confirmed-commit`, with a verify-per-platform note for EOS/NX-OS. |
| R20-10 | Minor | Hypergeometric probability | Key 20.3a gives both binomial 0.149 and exact hypergeometric 1 − C(502,8)/C(512,8) ≈ 0.147, and accepts either with the method stated. |
| R20-11 | Minor | AC3 floor (1,000/s against a ≈ 40/s baseline made AC3 inert); rack/rail naming collision | AC3 floor lowered to 150/s (data, manuscript Table 20.9, rationale). Naming: racks are now `rack-NN` and rail leaves `orion-be-leaf-rR` everywhere (generator, regenerated data, check.py, manuscript, exercises, key, findings, manifest); no bare r1..r8 remain. |
| VF-1 | Addendum | VERIFIED_FACTS: multi-node busbw ≈ 350+ GB/s, per-rail = busbw ÷ 8 | `busbw_GBps` is redefined as per-rail busbw (2-node all-rail busbw ÷ 8, ≈ 44 of 50 GB/s, ≈ 352 GB/s total) in the data definitions, Table 20.9 and §20.7.4; the lab README L3 note says to divide by 8. |
| VF-2 | Addendum | Other verified facts (restart 900 s, MTBF 1,536 h, `clocks_event_reasons`, NCCL GDR log line, 51.2T, frontend oversubscription) | Checked: none of these appear in ch20, so no conflicts. Ch 8 consistency: the 5.9 % gain is also stated as 5.6 % relative to the 4,096 figure, to match Chapter 8. |

Word count after fixes, with cuts paying for additions: `wc -w manuscript.md` = 9,992.
Lab: solution 13/13 PASS; starter 13 TODO, exit 1; `validate_labs.py ch20` → 1/1 valid.

### Re-scores (author, after fixes)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 10 | 10 | 9.5 | 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×10 + 0.05×10 + 0.05×9.5 = **9.55** |

D4 drops to 9.5 from 10: the simulated fleet treats `rdma_path_mtu` as independently settable,
whereas on hardware it is derived from the netdev MTU and the NIC cap. This is documented, not
modelled. D7 rises to 10 because of canonical naming and the Chapter 8 cross-reference.

## Independent review iteration 2 + author fixes

The independent re-review passed the chapter at 9.50 with no margin. The fixes below protect the pass.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R20-12 | Minor | SimFleet treats `rdma_path_mtu` as independently settable without saying so | Lab README §2 and the manuscript's Realism boundaries now state that `rdma_path_mtu` models the NIC's RoCE MTU cap, that the hardware value is the derived `active_mtu`, and that SimFleet does not recompute it when `host_mtu` changes. Paid for by trimming the closing paragraph of §20.11 Step 6. |
| R20-13 | Minor | The student release strips `tools/` (updated LAB_STANDARDS §2) | Generator removed from the learner setup steps. Lab README §2, the chapter-card file map, and the manifest comment mark it "instructor copy only". check.py never calls the generator. `validate_labs.py ch20` no-generator column = pass. |
| R20-14 | Minor | Storage/checkpoint traffic was placed on the backend NICs, but ORION storage uses the frontend | §20.5.1 rule 2 and key 20.4a now list NCCL bootstrap/socket fallback, iperf/health checks, and ssh over backend addresses; the key also notes that ORION storage uses the frontend NICs. |

Word count: `wc -w manuscript.md` = 9,986. Lab: solution 13/13 PASS; starter 13 TODO, exit 1;
`python scripts/validate_labs.py ch20` → OK (solution pass, starter fails gracefully, no-generator
pass).

## Independent review iteration 3 + author fixes (2026-10-29)

Closed: R20-15 (the dimension table is relabelled as a superseded author self-review; independent iteration 3 score of 9.50 recorded).

## Independent review r1 (2026-11-01)

Reviewer scores (independent, before fixes):

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.0 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.0 | **9.40** |

Reviewer's check.py results: solution 13/13, exit 0; starter 0/13 TODO, exit 1.

| ID | Severity | Finding (verified) | Resolution |
|---|---|---|---|
| N20-01 | Major | §20.13 contradicted §20.11 Step 3 and the lab: `desired_state.json` has no leaf-r2 override, the reconciler *adds* `48 → 6`, and POL-PFC already has the CNP clause. Verified against `lab/data/` and `solutions/lab/safe_change.py`. | Preferred fix applied. §20.13 is now the September incident, two months *before* CHG-2026-1103; audit timestamps are 2026-09-08. The fix list retires `qos-cron`, removes the override, and adds the POL-PFC CNP clause that the lab enforces. A new "What was missed" paragraph explains why the drift came back: the saved config dated from 09:07 mid-incident, an October reload, and leaf QoS left alert-only. §20.11 Step 3 now names the leaf-r2 drift as that residue. |
| N20-02 | Minor | Exercise IDs 20.1–20.11 collided with section numbers | Renumbered to 20-K1…K8, 20-W1/W2, 20-L1, 20-M1…M3, 20-T1, 20-D1, 20-DEL, 20-R1…R4. Applied to exercises.md headings and items, the key, `git mv` of every learner and solution folder, meta.yaml `id`/`folder`, the index, answer/solve.py headers, learner prompts, chapter README, lab README and the manuscript ("Exercise 20-DEL"). Outputs were regenerated. No other chapter referenced the old IDs. |
| N20-03 | Minor | Big-bang lost-state window was unexplained | Step 6 now says that the defect is latent and surfaces after jobs resume, so the running job loses ≈ 2 h since its last checkpoint. |
| N20-04 | Minor | Epigraph over-expanded acronyms | Epigraph cleaned. An **Acronyms.** paragraph (GPU, QoS, MTU, CI/CD, IaC, gNMI, BMC) follows Prerequisites, as in Ch16/Ch19/Ch21. |
| N20-05 | Minor | "Every 10 minutes" misread the data | "For five minutes in every ten". Matches the audit writes at :04:58 and :09:41. |
| N20-06 | Minor | No generator-reproducibility check | New `p0.dataset_reproducible`: regenerates all 7 files with seed 20 into a temp dir and compares bytes. It reports `SKIP` (exit still 0) when `tools/` is absent. Lab README §6, exercise 20-L1 evidence text and answer updated (14 checks). |
| D2 advice | — | Partial-apply/timeout handling deserved a worked paragraph | §20.9 "Timeouts and partial apply, worked" covers 3 of 8 gNMI Sets timing out: unknown ≠ failed, read-back before resending, the circuit breaker trips (37.5 % > 10 %, > 2 targets), each unknown resolved from observed state, and one transaction per target. Realism boundaries and Summary point to it. |

Rejected: none.

Length: additions paid for by trimming §20.1, §20.2.1, §20.3.4, §20.4/20.4.1, §20.7.1–20.7.2, §20.7.4
pitfall, §20.10, §20.12 and the Summary. `wc -w manuscript.md` = 10,330 (was 10,030).

Tests: `python lab/check.py --impl solution` → 14/14 PASS, exit 0; `--impl starter` → 1/14 (dataset
check PASS, rest TODO), exit 1; `python scripts/validate_labs.py` → 32/32 valid (ch20: solution
pass, starter fails gracefully, no-generator pass); `python scripts/copyedit_lint.py` → 0 findings in
ch20; package harness `pytest docker/harness/test_package.py --pkg <ch20>` → 90 passed.

---

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.5 · D2 9.0 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0 → **9.40 (FAIL)**. Findings: 0 blocker, 1 major, 5 minor. Checker at review: solution 14/14, starter 1/14.

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| R20-01 | Major | §20.11 cost model charged only drained GPUs and ignored the partition-wide gang and the lack of spares | Verified: every wave holds training nodes (2, 3, 2, 6, 6, 5), and with rack-aligned DP replicas waves 3–5 hit at least 5 of 6 replicas, so reduced DP is infeasible. Steps 5–6 are rewritten. Staged plan in a maintenance reservation, with a checkpoint before every drain: 192 × 7.5 + 48 + 80 = **1,568 GPU-h**; bad case 208; expected ≈ 1,578. Big bang in the same reservation: 176; bad case 256 × 4 + 192 × 2 = 1,408; expected ≈ 246. The old conclusion ("staging wins on GPU-hour tail") **did not hold**: the big-bang worst case (1,584) is below the staged worst case (1,776). The text now says staging buys serving continuity and protection against defects of unknown severity, and introduces ORION's hybrid (canary, then one 22-node training batch, then inference waves): 608 GPU-h, expected ≈ 618. 20-R1 key, 20-R1 answer.md and a summary bullet are updated. |
| R20-02 | Minor | Automation identity and credentials absent | Added an "Automation identity" row to Table 20.11, a sentence in §20.10 linking to the Chapter 19 identity and audit controls, and a K8 key/answer row. |
| R20-03 | Minor | Unlinked LAB_STANDARDS reference; "Section 20.3–Section 20.5" phrasing | Linked `LAB_STANDARDS §5`; changed to "Sections 20.3–20.5" and "Sections 20.7 and 20.9" (also in the lab README background table). |
| R20-04 | Minor | §20.13 "What was missed" reads as an unexplained downgrade to alert-only | Gave the reason: Fabric held leaf QoS alert-only until the drift policy (20-D1) fixed ownership, because two automated writers had just fought over the field. |
| R20-05 | Minor | Lab README claimed ≈ 20 % injected regression; committed evidence shows 16.5 % | Now "≈ 15–20 % regression (16.5 % on the reference run)". Measured results untouched. |
| R20-06 | Minor | Waves mix Slurm and Kubernetes nodes without saying how each drains | Added a paragraph after Figure 20.5 (Slurm drain in a reservation after a checkpoint; Kubernetes cordon and drain behind PDBs; wave 2's n25/n29 must fit the serving headroom), repeated in Step 5. |
| D5 advice | — | K3–K8 lacked point values in the key | Added marking points matching each meta.yaml. |
| D8 advice | — | No rollback-time targets | Runbook "Before" step 3 now lists `[ILLUSTRATIVE]` rollback targets per change type; a slower rehearsal blocks the change. |
| D4 advice | — | Timeout/partial-apply fault mode in `SimFleet` | Not done this round: it would change the lab contract, and the hashes are optional per the reviewer. |

Manuscript: 10,889 words (r1 ≈ 10,330); cuts in §20.2.1 and §20.11 offset part of the additions. Tests: check.py solution 14/14 (exit 0), starter 1/14 (exit 1); `validate_labs.py ch20` OK; package pytest 90 passed; copyedit_lint 0 findings in ch20. Outputs regenerated with `generate_outputs.py`.

### r2 re-score fixes (2026-11-03)

Re-score: **9.525**. The only gate blocker was R20-07.

| ID | Resolution |
|---|---|
| R20-07 (major) | Step 6 now names the per-batch caps the training batch breaks: ≤ 1 node/rack, ≤ 8 nodes, > 25 % of the fleet (22–24 nodes = 69–75 %). It makes the batch a recorded exception justified by the paused, checkpointed gang inside a reservation. Safeguards: second approval, reservation and checkpoint verified, concurrency ≤ 4 kept (≈ 6 rounds of 5 min), circuit breaker and kill switch unchanged, per-rack health baseline, inference pool keeps every cap. Table 20.11's cap row and runbook step 4 carry the same single exception. |
| R20-08 | Added the batch-only shape: 96 + 48 + 80 = 224 GPU-h; bad case 192 × 6 = 1,152; expected ≈ 282. The canary costs ≈ 240 GPU-h of paused training and protects ≈ 58 GPU-h expected, so the text says it loses on mean cost and is bought only against unknown-severity defects (bricking, anti-rollback). Decision rule: batch-only for minutes-reversible changes (this MTU change), hybrid for firmware. The canary bake now uses a replayed collective workload at representative load. The additive bad-case simplification is stated. Step 7 now says the lab's slot-major replay corresponds to the hybrid in production, with the n25/n29 regression caught in the first inference wave. |
| R20-09 | The Table 20.14 rollout-shape row gains the gang-partition caveat. The 20-M3 key and answer.md now use the hybrid (firmware) and batch-only (MTU) shapes under the recorded exception; 2/3/4/8/8/7 is accepted only when the stalled gang is priced. Also fixed a stale "Exercise 20.6" → "Exercise 20-M2" in the M3 answer, and added ≈ 282 to the 20-R1 key and answer. |

Tests: check.py solution 14/14, starter 1/14; `validate_labs.py ch20` OK; package pytest 90 passed; copyedit_lint 0 findings in ch20; outputs regenerated. Manuscript: 11,438 words.

### R20-10 fix (2026-11-03)

| ID | Finding | Resolution |
|---|---|---|
| R20-10 | The batch-only "≈ 30 min" left out the 10-min pair test | Batch only now takes ≈ 40 min: 192 × 40/60 = 128 GPU-h, planned 128 + 48 + 80 = 256, expected 256 + 57.6 ≈ **314 GPU-h** (was 282). Updated §20.11 Step 6, the 20-R1 answer and the key. Table 20.14 carries no number. The conclusion is unchanged: batch only still beats the hybrid (≈ 618) on mean cost. Tests: `validate_labs.py ch20` OK, package tests 90 passed, `copyedit_lint.py` 0 findings in ch20. |

## Repetition pass (2026-11-04)

Full manuscript 11,447 → 11,384 words (wc). Five repetitions removed, one wording fix:

- §20.7.2 two-scheduler paragraph: the Slurm drain/reservation, PodDisruptionBudget and wave-2 serving-headroom detail removed; kept in §20.11 Step 5. §20.7.2 keeps one sentence and the pointer.
- §20.11 Step 3: the account of how the `orion-be-leaf-r2` drift survived the incident fix (cron retired, map saved mid-incident, alert-only QoS) cut to a pointer; kept in §20.13 "What was missed".
- §20.10: restated automation-identity requirement (scoped, short-lived credential per controller) replaced by a pointer to Table 20.11 and Chapter 19.
- §20.11 Step 6: "the method transfers and the numbers do not" removed; kept in Realism boundaries. Step 6 keeps "recompute the Step 5–6 numbers…".
- §20.13 intro: "the lab enforces" removed; kept in Fix step 3 (`validate_desired`).
- §20.9: "The last row deserves emphasis" pointed at the identity row while discussing sanity bounds; now "The sanity-bounds row".

Deliberately kept: Step 1's header-byte sum (worked example re-uses Figure 20.2), the cap list and exception safeguards in Step 6 (Table 20.11 and runbook item 4 only point to it), the Trade-offs table and runbook (synthesis/template), and the one-sentence PFC/CNP and `active_mtu` statements with Chapter 9/8 cross-references.

Checks: `copyedit_lint.py` 0 findings; `lab/check.py --impl solution` 14/14.
