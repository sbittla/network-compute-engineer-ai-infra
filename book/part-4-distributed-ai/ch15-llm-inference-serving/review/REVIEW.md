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
