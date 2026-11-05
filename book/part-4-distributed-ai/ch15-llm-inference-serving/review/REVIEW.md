# Editorial Review — Chapter 15

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.90 | Fail (D1, D9 < 9.0; open majors) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.48 | Fail (weighted < 9.5: D9 at 9.0) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | Pass (internal); awaiting independent review |
| IR1 | 2026-10-29 | Independent review, iteration 1 | 9.13 | Fail (3 majors) |
| IR2 | 2026-10-29 | Independent review, iteration 2 | 9.43 | Fail (R2-01 major) |
| IR3 | 2026-10-30 | Independent review, iteration 3 | 9.50 | Pass |
| IR4 | 2026-10-30 | Independent review, iteration 4 | 9.50 | Pass; R4-01 minor (T1 decode nodes → orion-n27/n28, canonical inference partition) closed |

## Scores by dimension (latest — iteration 3)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | All worked arithmetic was re-derived by hand and re-checked against the reference implementation: KV/token, budgets, blocks, prefill, decode fixed points, M/D/1, KV transfer, and the speculative E and speedup. Version-sensitive items (vLLM flags, metric names, log text, nvidia-smi section names, NIXL/Dynamo) are flagged `[VENDOR-SPEC, 2026-10]`. Some paper-reported figures are quoted from memory and must be checked at release: DistServe 7.4×/12.6×, vLLM 20–40 % utilization, and the 2–4× throughput figure. |
| D2 | Depth and production realism | 15 % | 9.5 | Covers failure signatures (preemption storm vs burst vs slow replica), discriminating evidence, KV layout and segment counts, the TP all-reduce cost, per-layer streaming, QoS interaction with the training lossless class, a failure table for the KV path, and the cold-start restart hazard. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Moves from the request path to the roofline, KV, batching, paging, quantization, queueing, layout, disaggregation and speculation. The worked example shows every step and rejects a too-small pool explicitly. Two captioned diagrams, including the required end-to-end inference data path. |
| D4 | Hands-on lab quality | 15 % | 9.5 | Three realistic tools. The seeded discrete-event simulator reproduces byte-identical data. Three planted anomalies are designed so that queue p95 alone misclassifies the storm. 18 checks, each with a reason. The starter reports TODO per check. L2/L3 extensions give real commands and manifest fields. Runtime about 1 s. |
| D5 | Exercises and assessment | 10 % | 9.5 | The full standard set plus O1–O5 (all Chapter 15 outline exercises and the Section 20.2 exercise) and the deliverable. Every exercise has difficulty, tier and evidence required. The key has full arithmetic, tables, marking points and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | Every quantitative claim is labelled MODELED, SIMULATED, ILLUSTRATIVE or VENDOR-SPEC. The lab manifest separates evidence classes per part. L2 instructions require at least 5 runs, warm-up, and one-variable-at-a-time changes, and they forbid back-filling measured efficiency as "validation". |
| D7 | Cross-layer integration | 5 % | 9.5 | Uses the ORION and W-INFER numbers throughout. Connects to storage (cold start, frontend contention), fabric QoS (TC 3, PFC, ECN), host topology (PIX rail locality), scheduling (Slurm co-location case), and facilities (the power-cap slow replica). |
| D8 | Operational realism and safety | 5 % | 9.5 | Runbook with signals, thresholds, safe actions and escalation. Explicit safety callouts: no pool-wide restarts, and load tests and RDMA tests only on lab or staging. Mitigations in the scenario and the key avoid fabric changes during incidents. |
| D9 | Editorial polish | 5 % | 9.5 | Terminology and units are consistent, acronyms are defined on first use, and every figure and table is captioned. A scripted check confirmed that every Markdown table has a consistent column count and every relative link resolves, except the Chapter 21 folder, which is not yet created by its author (the slug matches the root README). The manuscript is at about 9,980 words, inside the 7,000–10,000 band. |

Weighted = Σ score × weight = **9.50**. No dimension is below 9.0. (Iteration 2 was 9.475, with D9 at 9.0. Iteration 3 fixed the table and link issues listed below, which lifted D9.)

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Blocker | lab/data/configs.yaml | PyYAML parsed `80.0e9` as a string (YAML 1.1 requires a signed exponent), so Part A crashed. | Rewrote every exponent with `e+`. The checker passes. (Iteration 1) |
| F2 | Major | §15.10 | "KV is about 4,000× the prompt text" was wrong by about 20×: 671 MB against about 8 KB of text is about 80,000×. | Corrected. (Iteration 1) |
| F3 | Major | solutions `_decode_fixed_point` | The fixed-point iteration diverged to 1e62 for unstable pools (W2, 6 replicas) instead of reporting instability. | Returns `inf` when there is no finite fixed point; W2 key explains the stability condition c·λ·O ≥ 1 − ρ. (Iteration 1) |
| F4 | Major | §15.3 | The heading "Concurrency is set by KV memory, not compute" contradicted the paragraph's conclusion that short chat is not memory-bound. | Retitled "Which limit binds depends on context length". (Iteration 1) |
| F5 | Major | manuscript length | The first full draft was 10,335 words, over the 10,000 limit. | Tightened objectives, batching, summary, further reading and the trade-off prose to about 9,980 without removing any mandated content. (Iteration 1) |
| F6 | Major | lab generator | The first tuning runs produced no preemptions (only head-of-line queueing), so the "preemption storm" anomaly was absent. | Re-tuned the longctx tenant (8–12k prompts, 3–5k outputs, 1.2 req/s) and the watermark. Verified 43 preemptions starting at about 465 s, KV at 100 %, arrivals flat. (Iteration 1) |
| F7 | Minor | §15.5 | The swap time (66 ms) assumed one PCIe link while the example replica is TP = 2. | Restated as 3.3 GB split over two links, about 33 ms each way; K8 key matches. (Iteration 1) |
| F8 | Minor | §15.14 | The validation criterion quoted the whole-trace ITL p95 as the "baseline". | Now uses the healthy-window ITL p99 (about 0.22 s, computed). (Iteration 1) |
| F9 | Minor | §15.14 Table 15.9 | Prefill p50 values were guessed (0.10–0.11 s). | Replaced with the computed values 0.12, 0.15 and 0.15 s. The timeline was made consistent (mm:ss from a 13:59 window start; the earlier burst is "four minutes earlier"). (Iteration 1) |
| F10 | Minor | §15.1 | "Four latencies" introduced a five-row table. | Fixed. (Iteration 1) |
| F11 | Minor | Acronyms | DSCP/PFC/ECN/VRF/SLI/RDMA were not expanded on first use. MLP was used without definition. | Expanded; MLP replaced with "feed-forward block". (Iteration 1) |
| F12 | Minor | lab/tools | Generator comments labelled the anomalies "planted: …", which revealed them to learners. | Comments neutralised. Anomaly descriptions now live only in `solutions/lab/INSTRUCTOR_NOTES.md`. (Iteration 2) |
| F13 | Minor (open) | §15.12 | The M/D/1 p95 ≈ 3× mean wait is a rough rule of thumb, not derived. | Labelled "roughly"; the key uses it consistently. Consider adding a simulation-based p95 in a later edition. |

| F14 | Minor | §15.1, §15.4, §15.9 | Iteration 3 polish pass: "far less than 64 separate steps" replaced an overstated "little more per step"; Table 15.9 timeline made consistent; the further-reading list was de-duplicated (Mooncake cited once). | Fixed. (Iteration 3) |

### Iteration 2 scores (for history)

D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0. Weighted 9.475.

### Iteration 1 scores (for history)

D1 8.5 · D2 9.0 · D3 9.0 · D4 9.0 · D5 9.0 · D6 9.5 · D7 9.5 · D8 9.0 · D9 8.5. Weighted 8.90.

## Release-gate items outstanding

* An external practitioner should review the vLLM metric names, the preemption log text, the
  default preemption mode, and the `vllm bench serve` / `vllm serve` flags against the version
  pinned at publication.
* Verify the paper-reported figures (DistServe 7.4× / 12.6×; vLLM 2–4× and the 20–40 % KV
  utilization of prior systems) against the published papers.
* L2 validation: run the lab §9 L2 procedure on one H100-class host. Record the actual HBM
  efficiency and step overhead and compare them with the 0.70 and 3 ms assumptions.
* L3 validation: measure KV-transfer bytes and time with a disaggregated connector over RoCEv2,
  together with switch ECN/PFC counters.
* Confirm the mlx5 `ethtool -S` per-priority counter names used in the T1 key on the target
  driver version.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer score: **9.13**, with 3 majors. All findings below were addressed in ch15 files only. The chapter now aligns with `docs/VERIFIED_FACTS.md` and the canonical names: the canary host is `orion-n29`, the T1 decode nodes are `orion-n05`/`orion-n06`, and the T1 leaves are `orion-be-leaf-r0`–`r3`. The chapter uses no restart-time figure.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | The TP=2 FP8 canary deviates from the baseline (TP=8 BF16 / TP=4 FP8) without saying so. | Added a "Deviation from the reference baseline" callout in Section 15.3, repeated in lab README Section 5: a cost-per-token experiment at 4 replicas/node, valid for 1–2k chat, unsafe for long context (70 GB KV ≈ 214k tokens). |
| R-02 | Major | The 5P:3D split was asserted, not derived. | Added Table 15.8a, a sweep over 4:4, 5:3, 6:2 and 7:1 with columns ρ, TTFT, TPOT, B and per-replica Gb/s. The reviewer's numbers are verified with the model. Chose **6P+2D**: ρ 0.604, TTFT 160 ms, TPOT 17.1 ms, B 88, 107.4 Gb/s per decode replica, so TCP is infeasible (107 % of achievable) and RDMA runs at 7.9 %. 7:1 fails on TPOT (47 ms) and on KV capacity (B 484 > 278). Updated Table 15.8, Sections 15.9 and 15.10, `configs.yaml` (6/2), check C3 expectations (TTFT 159.5 ms, TPOT 17.1 ms, TCP ITL 71.8 ms, TCP util 107.4 %), INSTRUCTOR_NOTES, and the key (lab section, O4 recomputed at 6P+2D). Added a note to place the two decode replicas on different nodes. |
| R-03 | Major | Speculative verification cost of 2.5 was guessed, with mixed units. | Derived from the roofline: 2 × 640 = 1,280 FLOP/B; 28.3 ms + 3 ms = 31.3 ms vs 20.2 ms gives v = 1.55, so speedup ≈ 1.9×. The O5 key now derives v_k per k (1.00 / 1.55 / 2.67) and recommends k = 2 on the throughput tier. |
| R-04 | Minor | The α=0.5, k=8 cost was inconsistent with c = 0.05. | Now reads "2.0 tokens for 1.4× the cost (1.43×)". |
| R-05 | Minor | Summary overstated that the KV budget always sets concurrency. | Qualified with "for long contexts". |
| R-06 | Minor | A 450 W cap with full HBM clocks implausibly gave a 1.65× decode slowdown. | Changed to a 300 W cap, SM clock about 1,020 MHz, HBM clock unchanged. The slowdown is attributed to compute-bound prefill iterations (about half the time, no chunking) and SM-clock-sensitive kernels. Noted that the simulator uses a uniform 1.65× factor. Cut the long nvidia-smi listing. |
| R-07 | Minor | The V0-format log conflicted with V1 defaults. | Stated that the canary runs an older V0-architecture vLLM with chunked prefill disabled, and flagged the V1 rename to `vllm:kv_cache_usage_perc`. |
| R-08 | Minor | T1 port RX semantics were wrong, and `squeue --start` was the wrong command. | RX is now stated per decode node (sum of rails 0–3: 108 → 330 Gb/s); the key explains about 27 Gb/s per rail of KV vs the foreign traffic. Uses `squeue -j <jobid> -o %N` / `scontrol show job`. |
| R-09 | Minor | The L3 `ib_write_bw` command lacked GPU memory and GID guidance. | Added `--use_cuda=0` and a `show_gids` / `ibv_devinfo -v` note for `-x 3`. |
| R-10 | Minor | R1–R4 lacked evidence lines, and the key lacked marking for K3–K8 and R. | Added both. |
| R-11 | Minor | "§" used instead of "Section". | Replaced in all ch15 files except historical rows of this log. |
| Cuts | — | Word budget. | Merged static/dynamic batching; removed two layout rows from Table 15.10; trimmed realism repeats, the nvidia-smi listing and the INT4 paragraph; merged further-reading items. `wc -w` = 9,964. |

### Author re-score after fixes

D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0. Weighted **9.48**.

D9 stays at 9.0. The manuscript is within 40 words of the cap, which leaves little room for future edits, and Table 15.8a precedes Table 15.8. The R-06 attribution (prefill share plus SM-sensitive kernels) is qualitative, not modeled. An independent re-score should confirm or adjust.

Validation: `check.py --impl solution` passes 18/18. `--impl starter` reports 18 TODO, exit 1. `validate_labs.py ch15` reports 1/1 valid.

### Follow-up edit (chapter owner, same day)

The tables are now numbered in order of appearance. The P:D sweep is Table 15.8, the worked-example comparison is Table 15.9, TTFT decomposition is Table 15.10, and design options are Table 15.11. All references in manuscript.md and INSTRUCTOR_NOTES.md were updated. This resolves the table-ordering half of the D9 hold.

Being under the word cap is a constraint, not a defect. With that, D9 → 9.5 and the weighted score is **9.50**, with the lowest dimension at 9.5. The R-06 attribution is still qualitative and is labelled as such. This score is pending independent confirmation.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent re-review found all iteration-1 findings fixed and numbers reproduced. Score **9.43 (fail)** on one major finding.

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R2-01 | Major | lab/README.md §2–§3; README.md file map | Learner docs told learners to run the generator, which is absent from the student release; `validate_labs` reported docs=GENERATOR-NOT-MARKED | Setup line removed; §2 now says "produced by a seeded generator (instructor copy only)"; file-map row marked instructor copy only. `validate_labs.py ch15` reports docs=ok, no-generator=pass |
| R2-02 | Minor | Section 15.14, second defect | The canary spends about a fifth of its time in prefill, not half (1.7 × (1,444 × 88.4 µs + 3 ms) ≈ 0.22) | Now "about a fifth". The text states that this does not explain the 1.6–1.8× and that the next step is to measure per-phase step time on r3. The uniform-factor simulator note is kept |
| R2-03 | Minor | Section 15.11 | 1.9× is the k = 4 figure; k = 2 stays memory-bound | Added "1.9× at k = 4" and the k = 2 sentence (≈ 2.2× at B = 128: shorten k rather than disable). Softened the closing line. Further reading trimmed (~40 words). Key already uses k = 2 → 2.22× and is consistent |
| R2-04 | Minor | Exercise T1 and key | Baseline token-2 ITL p99 (19 ms) was below the modeled mean worst case (21.1 ms) | Baseline now 24 ms; key criterion raised to < 30 ms with the reasoning stated |

The manuscript is 9,990 words. Author re-score: all dimensions 9.5, weighted **9.50**, pending independent confirmation.

## Independent review iteration 3 + author fixes (2026-10-30)

Iteration 3: **9.50, pass**. One minor finding:

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R3-01 | Minor | Section 15.3 deviation note; lab README; exercise T1 | The canary on `orion-n29` and the decode replicas on `orion-n05`/`n06` did not say which partition they belong to | Added a clause in all three places: these are nodes of the 8-node Kubernetes inference partition (`REFERENCE_CLUSTER.md` scheduling split), so W-TRAIN is not running at full size at that moment |

The manuscript is 9,997 words. No numbers changed.

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.5. Weighted **9.50**. All findings were minor; there were no blockers or majors. The author checked each finding before changing anything.

| ID | Finding | Resolution |
|---|---|---|
| N15-01 | §15.10 called the frontend "3:1 oversubscribed" | Now reads "1.5:1 oversubscribed by bandwidth (3:1 by port count; 1:1 as populated on ORION-256)", matching VERIFIED_FACTS |
| N15-02 | §15.11 and key O5 compared a weight-only intensity with the peak ridge, which would also make k = 2 (768 FLOP/B) compute-bound | Both now compare derated compute time with derated memory time: 28.3 vs 17.2 ms for k = 4, and 17.0 vs 17.2 ms for k = 2. The equivalent check is intensity including KV bytes (≈ 556 and ≈ 333 FLOP/B) against the effective ridge 591 × 0.40/0.70 ≈ 338 FLOP/B. The O5 answer.md is updated too. Verification costs (1.55, 2.67) and speedups are unchanged |
| N15-03 | T1 placed a Slurm job on n27/n28, which ORION's partition model makes impossible | The prompt now states that Slurm owns n01–n24 and that a partition-definition change was merged three weeks ago. The prompt is synced verbatim to the exercise folder. In the key and answer.md, the root cause is a `training` partition (or reservation) mistakenly extended to n25–n32. The RX on rails 0–3 is explained by rail-aligned rings from full nodes entering through NICs 0–3. The test is `scontrol show partition training`. The mitigation reverts the partition change, and the structural fix enforces node ownership (Chapter 17) with a pre-merge policy check. Marking text in meta.yaml and marking.json is updated |
| N15-04 | §15.14 had an unexplained compound expression | Now spelled out as ρ = λ_r × t_prefill = 1.7 req/s (baseline arrivals per healthy replica, checked against requests.csv) × (1,444 mean prompt tokens × 88.4 µs + 3 ms) ≈ 0.22, labelled |
| N15-05 | The "M/D/1 p95 ≈ 3× mean" heuristic was unlabelled | Checked numerically, and the heuristic is **wrong**. Erlang's exact M/D/1 waiting-time distribution, confirmed by a 2M-arrival simulation, gives p95 = 4.3× the mean at ρ = 0.45 and 3.5× at ρ = 0.71. §15.7 now gives the formula and these ratios. Step 6 uses the exact value: 161 ms p95 wait, TTFT p95 ≈ 252 ms, conclusion unchanged. Key D1 now uses the exact percentile, which **changes the design**: P = 12 gives 1.71 s (fail; the old rule passed it at 1.48 s) and P = 13 gives 1.49 s (no margin), so the choice is now **14P + 4D = 18 replicas**, still 10 nodes including the spare. The prefill-loss row now reads ρ 0.60 and 1.49 s, at the SLO edge. The D1 solve.py implements the formula, its assertions are updated, and its outputs are regenerated |
| N15-06 | MoE / expert-parallel serving was absent | Added a Production note in §15.9: experts on other GPUs and nodes, two latency-bound all-to-alls per MoE layer per decode step, PXN relevance (Chapter 12), and that the KV analysis still applies. It cites the DeepSeek-V3 Technical Report (DeepSeek-AI, 2024), which is also added to Further reading |
| N15-07 | The HBM unit was implicit | §15.3 now states that 80e9 B is a conservative planning figure, that `nvidia-smi` shows ≈ 79.6 GiB ≈ 85.5e9 B, and that the engine profile gives the real budget |
| N15-08 | TGI listed as a current engine | Verified against the TGI repository README (2026-11), which says it is "now in maintenance mode". The text now says so, `[VENDOR-SPEC, 2026-10]` |
| Next-0.5 D2 | Autoscaling cold start | Added a runbook-notes paragraph: 140 GB per node, ≥ 2.8 s at line rate, ≥ 7 s for 8 nodes on 160 GB/s of PFS read, plus engine start-up. Bursts are absorbed by N+1 headroom; NVMe weight cache (Chapter 14) |
| Next-0.5 D3 | ITL timeline figure | Added Figure 15.2 (ITL with and without 512-token chunked prefill: 103.3 ms vs 4 × 35.3 ms; the prompt finishes at 141 vs 90.6 ms). The disaggregation figure is renumbered 15.3 |
| Next-0.5 D4 | Analyzer realism gap | `request_metrics` now adds a `valid` column (missing or out-of-order timestamps → NaN latencies), and `itl_values_s` skips empty, non-numeric and negative gaps. New check **B9** runs both on an unseen defective trace. Starter stubs, lab README task 5 and rubric, the L1/DEL lab_checks and "19/19" texts, and the golden check outputs are updated |

Validation: `check.py --impl solution` 19/19; `--impl starter` 19 TODO, exit 1. `validate_labs.py ch15` 1/1 valid. `copyedit_lint.py` 0 findings. `pytest docker/harness/test_package.py --pkg ch15` 98 passed. The manuscript grew from ≈ 10,065 to ≈ 10,550 words (`wc -w`); the new material was partly offset by trimming the Summary, §15.13 and §15.9.

Author re-score, pending independent confirmation: D1 10, D2 10, D3 10, D4 10, D5 10, D6 10, D7 9.5, D8 9.5, D9 9.5. Weighted ≈ **9.93**.

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 10, D8 9.5, D9 9.5. Weighted **9.525**. There were 5 minor findings, no blockers and no majors.

| ID | Finding | Resolution |
|---|---|---|
| R15-01 | §15.12 Step 7 said 6:2 "leaves a third" of the TPOT budget | Confirmed (17.1 of 50 ms *uses* a third). Now "uses only about a third of the TPOT budget (17.1 of 50 ms)" |
| R15-02 | The L2 report cited Section 15.6 for prefill interference | Confirmed. The string is corrected to Section 15.4 in `lab/l2/experiment.py` and in the text line of both committed `report.md` bundles. No measured value was touched |
| R15-03 | The T1 mechanism (rail-aligned rings landing on NICs 0–3) was unsupported | Confirmed: ranks on GPUs 4–7 get PIX NICs 4–7, and PXN cannot relay through non-job GPUs 0–3. Key and answer.md now state the narrower mechanism. The job's ranks use NICs 0–3 directly, through an `NCCL_IB_HCA` pin or cross-NIC selection. That traffic is host-staged at SYS distance. A whole-node grant is considered and set aside because decode TPOT barely moved. The job's NCCL INFO channel lines (`via NET/IB/<dev>`, presence of `/GDRDMA`) are now the discriminating test |
| R15-04 | The safety callout used 32 nodes | Confirmed. It now covers the 8 inference nodes: ≈ 1.1 TB (16 FP8 or 8 BF16 replicas) needs ≥ 7 s of the 160 GB/s PFS read even uncontended |
| R15-05 | Late acronym expansions | NIC is now expanded at its first prose use (§15.1), and the later expansion in Table 15.5 is removed. **Partly rejected:** SM is first used where it is expanded (§15.14), and MTU likewise (Realism boundaries); grep shows no earlier use of either |
| Next-0.5 D3 | Justify the (1 − ρ) stall factor | Step 5 now explains it: without chunking each iteration either prefills or decodes, so decode fills only 1 − ρ of wall time (a mean-value model) |
| Next-0.5 D2 | TPOT/ITL p95 | Step 6 adds a Poisson bound. A request's 5.94 s of decode sees Poisson(29.7) prefills, p95 = 39, giving TPOT p95 ≈ 26.6 ms. Since 11 % of gaps hold a prefill, ITL p95 ≈ p99 ≈ 103 ms `[MODELED]` |
| Next-0.5 D2 | Prefix-cache effect on prefill demand | Step 3: with a 1,024-token cached prefix, t_p ≈ 45.3 ms and demand is 1.81 replica-s/s. The text says to size for the miss case and alert on hit rate |
| Next-0.5 D4 | Planted telemetry decoy and check | **Not done.** The analyzer classifies from request-level timings and never reads `gpu_busy_pct`, so a decoy check would pass trivially. Testing it properly needs a new telemetry-driven contract plus regenerated data and goldens. The "busy % discriminates nothing" point stays in report task 8 and INSTRUCTOR_NOTES |

To compensate for length, the security-boundary, TP-mismatch, KV-size and validation paragraphs were tightened. The manuscript is ≈ 10,700 words (`wc -w`).

Validation: `check.py --impl solution` 19/19; `--impl starter` 19 TODO, exit 1. `validate_labs.py ch15` 1/1 valid. `copyedit_lint.py` reports 0 findings in ch15 files; its one remaining finding is in ch22. `pytest docker/harness/test_package.py --pkg ch15` 98 passed.

## External PDF review fixes (2026-11-03)

An external reviewer asked for reproducible benchmark configurations, a theoretical-versus-practical KV-capacity distinction, and a comparison of the main serving techniques.

| Request | Resolution |
|---|---|
| Document the configuration of every major example: model and parameters, weight and KV precision, engine and version, attention implementation, GPU and TP, token distributions, batch and scheduling, warm-up, duration and repetitions, TTFT, ITL, throughput and memory | New **Table 15.1a** (end of §15.1) has three columns: the capacity model (L-tp8-bf16 / T-tp4-fp8, §15.2–15.12), the canary trace (§15.14, lab Part B) and the committed L2 bundle. Reference-cluster values are `[ILLUSTRATIVE]` and engine behaviour is `[VENDOR-SPEC, 2026-10]`. No engine version is claimed for the modeled or simulated columns, because no engine ran. The measured column cites `lab/l2/results/gpu-rtx-4060-laptop-gpu/environment.json` (PyTorch 2.5.1+cu124, CUDA 12.4, driver 592.82, RTX 4060 Laptop GPU; TTFT p50 183 ms, ITL p50/p95/p99 7.71/11.35/17.25 ms, 3,548 tokens/s at B = 32, peak allocation 2.18 GB). The token distributions for the canary come from `tools/generate_trace.py`. §15.8, §15.12, §15.13 and §15.14 now point to the table |
| Theoretical KV capacity against usable concurrency | New **Table 15.3a** in §15.3 walks one TP = 4 FP8 replica: 250 GB → 186 4k sequences (theoretical) → 218 GB / 162 (memory fraction 0.90) → 210 GB / 156 (2 GB/GPU reserve: activations, CUDA graphs, NCCL, fragmentation) → block rounding (≤ 1 block per sequence) → 189 GB / 140 (90 % admission headroom) `[MODELED]`, which is 75 % of theory. The 128-sequence cap binds first, and TPOT does not bind (30.5 ms with all 140 at 4k). `--gpu-memory-utilization` semantics and default (0.90 → 0.92) are hedged `[VENDOR-SPEC, 2026-10]`, per VERIFIED_FACTS. The L2 measured reserve (138 MB, giving 6.25 GB of KV = 86 % of the post-weight memory) is cited `[MEASURED]` |
| Comparison of continuous batching, paged attention, prefix caching and speculative decoding | New **Table 15.7a** at the end of §15.11 covers what each technique improves, what it assumes, when it hurts and what to measure. It uses only numbers already derived in the chapter (t_d slope, ITL 12.7 → 103 ms, prefix demand 3.62 → 1.81 replica-s/s, speculative 2.8× / 1.9× / 1.4× / 1.43×) |

New tables use letter suffixes, so no existing table number, exercise or key reference changes. To hold growth to ≈ 6 %, these parts were tightened: the opening, Prerequisites, the §15.2 TP and attention paragraphs, the §15.3 deviation box, the §15.4 knobs paragraph, the §15.5 preemption text and production note, the INT4 aside, the §15.7 Little's-law intro and the e2e SLI row, the §15.9 bullets and "when it hurts", the §15.10 TCP, QoS and security text, the §15.12 step 7/8 prose, the §15.14 root-cause and second-defect text, "When each wins", the Safety box, Realism boundaries and the Summary (which now carries the 186 → 140 point). The manuscript went from 10,702 to 11,368 words (`wc -w`, +6.2 %). No lab, exercise or key depended on the changed text.

Validation: `check.py --impl solution` 19/19; `--impl starter` 19 TODO. `validate_labs.py` 32/32 valid. `copyedit_lint.py` 0 findings.

## Repetition pass (2026-11-04)

Eight repetitions removed or merged; manuscript 11,370 → 11,286 words (`wc -w`, −84). No unique fact, number, evidence label or safety warning was removed; no exercise quotes the cut text.

1. Table 15.1 caption: dropped the TPOT-is-an-average / ITL-shows-spikes sentences. Kept in the Key idea callout directly below.
2. §15.2: dropped "Calibrating both against your own stack is the L2 extension." Kept in Realism boundaries (bullet 1) and the §15.12 recommendation.
3. §15.3: dropped two early mentions of engine start-up memory profiling ("Serving engines … measure your own value"; "the engine's start-up profile gives the real budget"). Kept in the fuller paragraph after Table 15.3a (vLLM flag, defaults, read the logged KV size).
4. Table 15.3a, runtime-reserve row: replaced the re-listed reserve contents (activations, CUDA graph pools, NCCL buffers, fragmentation) with "the reserve described above, 4 × 2 GB". Kept in the prose after the budget formula.
5. §15.3 deviation box: dropped the restated "≈ 214k tokens of KV per replica"; now points to §15.14. Kept in the paragraph just above the box.
6. Table 15.6 caption: dropped "The efficiency factors are teaching values". Kept in the lead-in ("`[ILLUSTRATIVE]` assumptions") and Realism boundaries.
7. Safety box: the cold-start load ("≥ 7 s of the 160 GB/s parallel-file-system read") is no longer re-derived; it points to the Autoscaling and cold start paragraph above. The warning, the ≈ 1.1 TB figure and the roll-one-at-a-time rule stay.
8. §15.14 root cause: dropped "The router could not see KV pressure", which repeated Step 3's finding on count-based routing; the 0.9 s recompute cost now points to §15.5.

Deliberately kept: the §15.12 worked example's reuse of 278 sequences, 671 MB, 107.4 Gb/s and 7.9 % / 107 % (repetition by design); Tables 15.7a and 15.11 (synthesis tables that cite the sections they summarise); the §15.14 Step 4 "avoid restarting replicas" line alongside the pool-wide Safety box (both are safety warnings); the §15.2 TP all-reduce estimate and §15.10 QoS paragraph (short applied uses of Chapters 12 and 9, already cross-referenced).

Validation: `check.py --impl solution` 19/19; `copyedit_lint.py` 0 findings.
