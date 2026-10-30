# Editorial Review — Chapter 17

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.23 | Not passed (blockers/majors open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Internal gate passed (pending independent review) |
| 3 | 2026-10-29 | Independent review iteration 1 | 9.00 | FAIL (2 majors) |
| 4 | 2026-10-29 | Independent review iteration 2 | 9.30 | FAIL (minors) |
| 5 | 2026-10-29 | Independent review iteration 3 | 9.50 | PASS (validator false positive fixed by coordinator) |

## Scores by dimension (author self-review, iteration 2 — superseded by the independent scores above)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.0 | 9.5 | Device-plugin/allocatable mechanics, taint semantics, MIG strategies, Topology Manager placement of the decision, Kueue/ResourceQuota admission points, Slurm `cons_tres`/QOS/states/backfill are described correctly; DRA, Kueue field names, GFD labels, MIG profiles, `topology/block`, and Slurm reason strings carry `[VENDOR-SPEC, 2026-10]`/verify notes. |
| D2 | Depth and production realism | 15% | 9.5 | 9.5 | Failure signatures (allocatable < physical, MIG `nvidia.com/gpu: 0`, `TopologyAffinityError` loop, quota invisible at pod level, RESUME of mid-upgrade node), rail-degraded node policy, fragmentation metric, asymmetric preemption with cost. |
| D3 | Pedagogy and clarity | 15% | 9.5 | 9.5 | Five-question pipeline (Fig 17.1) reused in worked example, lab, and troubleshooting; worked example shows every share and placement. |
| D4 | Hands-on lab quality | 15% | 9.0 | 9.5 | Real task (policy replay + pending-job triage); deterministic (byte-identical regeneration verified); fixtures give targeted feedback; hashed expectations avoid leaking answers; 20+ planted traps; L2/L3 commands. |
| D5 | Exercises and assessment | 10% | 9.5 | 9.5 | Full standard set + M1–M3 + deliverable; objective evidence lines; key with arithmetic, marking, common mistakes; W2 verified with the simulator. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.0 | 9.5 | All quantitative claims labelled; MODELED formulas shown (deadlock, preemption, rack exposure, rail bandwidth); lab outputs labelled SIMULATED; L3 extension specifies repetitions, median/p95, warm-up. |
| D7 | Cross-layer integration | 5% | 9.5 | 9.5 | Uses ORION nodes/racks/rails, HX8 sockets/NICs, W-TRAIN/W-INFER; explicit lifecycle mapping to Chapter 16; links to Ch 5, 7, 11, 15, 18–21, Capstones E/G. |
| D8 | Operational realism and safety | 5% | 9.5 | 9.5 | Runbook with signals/thresholds/safe actions/escalation; change-review boundary; Safety callouts on every state-changing command. |
| D9 | Editorial polish | 5% | 8.5 | 9.5 | Acronyms defined on first use (NHC, CEL, NVML, SLI, RBAC, PDU/CDU, DCGM, HBM/SM, TRES, NUMA, QOS, TP, MIG); figures/tables captioned and numbered; relative links checked. |

Weighted (iteration 2) = 0.20·9.5 + 0.15·9.5 + 0.15·9.5 + 0.15·9.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 +
0.05·9.5 + 0.05·9.5 = **9.50** (meets gate: ≥ 9.5, no dimension < 9.0).

Iteration 1 weighted = 0.20·9.0 + 0.15·9.5 + 0.15·9.5 + 0.15·9.0 + 0.10·9.5 + 0.10·9.0 + 0.05·9.5 +
0.05·9.5 + 0.05·8.5 = 1.80 + 1.425 + 1.425 + 1.35 + 0.95 + 0.90 + 0.475 + 0.475 + 0.425 = **9.225**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | lab data / manuscript 17.5.3, 17.9 | `orion-n23` was lifecycle `draining` with zero jobs, while Slurm would show it `drained`; inconsistent with Chapter 16 semantics and the `sinfo` excerpt. | Generator sets `drained`; manuscript and key updated; checker hashes unaffected (re-verified 9/9). |
| F2 | Major | lab/check.py `T4 gang` | Third assertion in the gang fixture expected the wrong reason (16 free, 1 whole node is Fragmentation, not InsufficientCapacity) and had convoluted logic. | Rewritten: Fragmentation for 16-GPU, InsufficientCapacity for 24-GPU; verified against reference. |
| F3 | Major | lab design | Initial queue produced no `Fragmentation` outcome in the schedule and J02 tie-broke onto a rail-complete node only by name. | Added rail-preference to the single-node score, changed R-rs-002 to 2 GPUs and J09 to priority 5 so J06 sees exactly 8 scattered GPUs; documented in key. |
| F4 | Minor | manuscript 17.5.2 | `sacctmgr modify account research set …` lacked the `where name=` clause. | Fixed. |
| F5 | Minor | manuscript 17.5.2 | `QOSGrpGRES` presented without version caveat. | Added "exact reason strings vary by Slurm version" note. |
| F6 | Minor | manuscript 17.9 | Cross-reference to non-existent "Exercise 17.E3". | Now "Exercise 17-W2". |
| F7 | Minor | manuscript (various) | Acronyms used before definition (NHC, CEL, NVML, SLI, RBAC, PDU, CDU, DCGM, HBM, SM, TRES, NUMA, QOS, TP, MIG in abstract). | Defined on first use. |
| F8 | Minor | manuscript 17.5.1 | Example partition used `OverSubscribe=EXCLUSIVE`, contradicting the small-job packing in the lab. | Removed from config; discussed as an option in Table 17.8. |
| F9 | Minor | manuscript length | Draft exceeded 10,000 words after fixes. | Trimmed to 9,996 (`wc -w`). |

Reviewer note on iteration 2 scoring: D9 raised to 9.5 only after the acronym pass and caption check;
D1 remains the dimension most exposed to version drift (DRA GA version, Kueue field renames, GFD label
values) — all are flagged in-text, but an independent reviewer should spot-check them.

## Release-gate items outstanding

- Independent technical review by a practising GPU-cluster platform engineer (Kubernetes + Slurm).
- Verify at publication: DRA API maturity per Kubernetes version; Kueue API version and field names
  (`cohort`, stop policy, TAS annotations); GPU Operator/GFD label keys and `mig.config` values; H100
  MIG profile table; Slurm `topology/block` availability and `squeue` reason strings for the target
  Slurm release.
- L2 validation of the extension commands on a real single-GPU Kubernetes node and a single-node Slurm
  install; capture real event strings and compare with `pending_cases.json`.
- L3 validation of the placement experiment (`all_reduce_perf` under rail-complete vs rail-degraded
  placement) on ≥ 2 RDMA nodes.

---

## Independent review iteration 1 + author fixes (2026-10-29)

The independent reviewer scored the chapter at **9.00 (FAIL)** (see docs/REVIEW_STATUS.md). Author fixes:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R17-01 | Major | QOS `GrpTRES` limits are unenforced without slurmdbd accounting enforcement | §17.5.1 `slurm.conf` now has `AccountingStorageType=accounting_storage/slurmdbd` and `AccountingStorageEnforce=associations,limits,qos`. §17.5.2 states that without them the limits are silently ignored, and adds `QOSMaxGRESPerUser` next to `QOSGrpGRES` (also in the §17.5.3 reason list). |
| R17-02 | Major | Rail-degraded nodes were handled as a drain | NHC text (§17.5.5) now reserves DRAIN for GPU faults, fatal Xids, and all-rails-down. §17.6 Level 2 gives the mechanism: Slurm feature `rails8`→`rails7` plus lower `Weight` and `--constraint=rails8` for gangs; Kubernetes label `halcyon.ai/rails-complete` plus required node affinity. The `slurm.conf` gives n14 its own NodeName line. The lab data carries the label, and the lab README §5.2, key planted-item 1 and key M2 mirror the policy. |
| R17-03 | Minor | `preempt/qos` wording | Preemption is now described between QOSes (`Preempt=` list, `PreemptMode=REQUEUE`), not partitions. |
| R17-04 | Minor | 24/8 pool split vs the 32-node W-TRAIN gang | §17.5.1 explains that day-to-day pretraining is TP 8 × PP 4 × DP ≤ 6 (≤ 24 nodes). The full 32-node gang needs the inference nodes moved in through a lifecycle transition. |
| R17-05 | Minor | DRA version | Now "GA in 1.34 as `resource.k8s.io/v1`", keeping the verify label. |
| R17-06 | Minor | Where ResourceQuota errors appear | §17.4.2: admission rejects the pod at creation (never Pending) and the controller logs `FailedCreate`. Lab README §5.6 and the key's pending-guide marking now say the same. |
| R17-07 | Minor | Key K6 | Rewritten: the pod goes to `Failed` with `TopologyAffinityError`, the controller recreates it, and only `best-effort` admits misaligned pods. |
| R17-08 | Minor | Kueue suspend | Table 17.6 now uses `spec.stopPolicy: Hold` / `HoldAndDrain`. |
| R17-09 | Minor | J06 vs J01 order ("submitted first") | J01 is now described as the earliest priority-50 submission. The key notes that J06 (t = 42 s, priority 10) was submitted earlier. |
| R17-10 | Minor | §17.11 cross-reference | The lab README background table now points to 17.11 (was 17.10). The Table 17.8 reference now reads "Section 17.11". |
| R17-11 | Minor | P03/P04/48211/P10 consistency | The manuscript `squeue` sweep job is now 48288, so 48211 is only P03. Slurm bundles use tenant QOS names (pretrain/finetune/research). P04's device-plugin pod is in `gpu-operator` and its quota used = 8. P10 now includes `orion-n24 ALLOCATED`, matching §17.11 `sinfo`. The README says the bundles are independent incidents from different days. Diagnoses are unchanged (hash-verified). |
| R17-12 | Minor | Kueue TAS details | Key D1(a) now covers the `Topology` levels, `ResourceFlavor.spec.topologyName`, and the `podset-required-topology` / `podset-preferred-topology` annotations, with a version flag. |
| VF-1 | Consistency | Canonical names | Racks are `rack-NN` everywhere: generator, data, check.py fixtures, manuscript and key. `rack_key` now parses `rack-NN`. The topology.conf example uses `orion-be-leaf-r0`. |
| VF-2 | Consistency | Restart cost 900 s | The preemption example is now 64 × (0.25 + 0.25) h = 32 GPU-h (was 26.7, using 10 min). Exercise W1.6 uses 15 min: 128 × 0.625 h = 80 GPU-h. |
| VF-3 | Consistency | Other VERIFIED_FACTS items | Checked: the chapter does not use clock-reason fields, NCCL GDR log lines, node MTBF or frontend oversubscription, so nothing conflicts. |
| Budget | — | Word count | §17.10 was condensed, and one production-note sentence, one further-reading item and one Step 8 clause were cut. `wc -w` = 9,984. |

**Re-scores after fixes (author):**

| Dim | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 |
|---|---|---|---|---|---|---|---|---|---|
| Score | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 |

Weighted = **9.50**; lowest dimension 9.5. The lab passes in both modes after regenerating the data: solution 9/9, starter fails gracefully, `validate_labs.py ch17` 1/1. Awaiting independent re-review.

---

## Independent review iteration 2 + author fixes (2026-10-29)

The independent re-review scored the chapter at **9.30 (FAIL)**. Author fixes:

| ID | Finding | Resolution |
|---|---|---|
| R17-13 | §17.3.4 DRA accuracy | Heading changed to "(GA in 1.34)". The text now reads "with extended resources require the kubelet" and adds `ResourceClaimTemplate`. The note says classic DRA was removed in 1.32 and that ORION's 1.30+ baseline must be ≥ 1.34. To pay for it, the §17.10 task description lost ≈ 30 words. |
| R17-14 | L2 quota reproduction watched the wrong event | Lab README §8 now creates a 2-GPU Job and checks `--field-selector reason=FailedCreate`. FailedScheduling is kept only for the taint/selector causes. |
| R17-15 | Learners were told to run the instructor-only generator | Removed the generator from the lab README setup steps. The lab README data section, chapter-card file map and `manifest.yaml` comment now mark `tools/generate_data.py` "instructor copy only". `check.py` never needs the generator. |
| R17-16 | Quota-cause scope in §5.6 | Lab README §5.6 now says only the ClusterQueue/QOS bundles can show QUOTA_EXHAUSTED. The six ResourceQuota bundles are all below their limit (checked: P02 24+8, P04 8+8, P06 20+4, P07 47+1, P09 28+4, P12 32+8, all ≤ 48). |
| R17-17 | Generator comment for P03 | Changed "26 idle GPUs" to "34" (4+3+6+2+8+1+5+5). Data regenerated; md5 is identical before and after a re-run. |

The manuscript is 9,989 words. `validate_labs.py ch17` is OK: solution pass, starter fails gracefully, no-generator pass. The author re-score is unchanged at 9.50 with every dimension at 9.5, pending independent re-review.

## Independent review iteration 3 + author fixes (2026-10-29)

Closed: independent scores recorded in the header table; the dimension table is relabelled as a superseded author self-review.
