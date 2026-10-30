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
