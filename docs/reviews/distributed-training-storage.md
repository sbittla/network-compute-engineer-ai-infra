# Pre-publication technical review: distributed training, storage and checkpointing

**Nature of review.** AI-assisted specialist review (Claude, acting as a distributed-training and
storage/checkpointing reviewer). It is **not** an independent external human review and does not
replace one.

**Date.** 2026-11-05

**Scope.** Concise print edition `concise/ch11.md` (Distributed Training Architecture), `ch12.md`
(Collective Communication and NCCL), `ch13.md` (GPU-to-GPU and GPU-to-NIC Data Movement), `ch14.md`
(Storage, Data Pipelines, and Checkpointing); the matching full-length manuscripts under
`book/part-4-distributed-ai/`; checked against `docs/REFERENCE_CLUSTER.md`, Appendix A, Appendix E and
the evidence labels of Table 0.1. `concise/ch19.md` was read for recovery cross-references only and
was not edited. The `> **Hands-on.**` note in `concise/ch14.md` was not edited (another engineer is
rewriting it; it changed on disk during this review).

**Checks run.** Evidence labels; recomputation of every headline model; recovery completeness
(release gate); ORION/H100 scoping; simulated-result boundaries; Mermaid diagrams versus prose;
version-sensitive guidance versus Appendix E; lab safety of quoted commands; word budget
(`python scripts/build_concise.py --check`).

## Findings

Severity: **Major** = wrong or missing content a practitioner could act on; **Minor** = labeling,
consistency, safety wording or build gate; **Info** = polish or verify-later.

| ID | Chapter / section | Severity | Finding | Resolution |
|---|---|---|---|---|
| DT-01 | ch11 §11.9 (rank loss) | Major | Concise text drops elastic relaunch entirely, although Appendix E Table E.5 cites Chapter 11 for `torchrun --nnodes=MIN:MAX --max-restarts` and the manuscript covers it. The concise reader also isn't told that restarting at DP = 7 needs a re-shardable checkpoint (ZeRO-1 optimizer shards change owner). | **Fixed** (concise): one sentence, `torchrun --max-restarts` and `--nnodes=MIN:MAX` automate the relaunch, but a smaller world size needs a checkpoint that can be re-sharded. Manuscript already correct. |
| DT-02 | ch14 §14.8 | Minor | Non-standard evidence label `[derived from a published operator report]` (not in Table 0.1) on M ≈ 198 h. The value is a linear-scaling computation, so it's MODELED. | **Fixed**: concise `[MODELED]`; manuscript `[MODELED, from a published operator report]`. Value verified (below). |
| DT-03 | ch12 §12.4 | Minor | The quoted sweep `all_reduce_perf -b 8 -e 8G -f 2 -g 1` relies on the default 1 warm-up iteration. Appendix E (Table E.4) says to pass `-w` explicitly, and the manuscript uses `-w 5 -n 20`. | **Fixed** (concise): command now `… -g 1 -w 5 -n 20`, with the flags explained. |
| DT-04 | ch12 worked ex., ch13 troubleshooting, ch14 §14.4 | Minor | `[SIMULATED]` lab results in the concise edition don't say what the simulator omits, so a reader could take plateaus, magnitudes or loader throughput as capacity figures. The manuscripts have "Realism boundary" notes. | **Fixed**: one sentence each. ch12: logs omit NCCL algorithm switching and congestion, size nothing from them. ch13: simple causal rules plus noise; real telemetry has missing samples, clock skew and interacting causes. ch14: trace omits MDS queueing and caching, shows the bound, not your capacity. |
| DT-05 | ch14 troubleshooting | Minor (lab safety) | `lfs find` over a 262,400-entry checkpoint directory is shown during an MDS storm (CPU 96 %). This contradicts the chapter's own rule that `find` sweeps on the shared PFS are unsafe without Storage. | **Fixed**: concise "counted after the storm"; manuscript adds a comment that Storage ran it after the storm because a sweep during one adds MDS load. |
| DT-06 | ch11 §11.9 vs ch14 §14.8 | Minor | ch11 budgets C = 45 s (τ_opt 66 min), while ch14 derives δ_sync = 17.83 s (τ 41 min) and δ_async = 1.19 s (τ 10.7 min). Both are labeled, but nothing links them and readers see two "ORION intervals". | **Fixed**: ch11 now notes "Chapter 14 derives 17.8 s". The 45 s stays as a conservative budget (metadata, writer stragglers, barriers, per the manuscript). |
| DT-07 | ch12 §12.6 | Info | "2.20+ print `status=12`" is stale for late 2.28+ and 2.32, which print `status=<name>(12)` (Appendix E Table E.4). | **Fixed**: "2.20+ print a `status=` field". |
| DT-08 | ch11 opening | Info | First Part 4 mention of ORION-256 doesn't say ORION is illustrative (front matter and labels do). | **Fixed**: "the illustrative reference cluster ORION-256". ch12–14 rely on front matter plus per-value labels; accepted. |
| DT-09 | ch11 §11.9 (hangs) | Info | "on the order of 10 minutes in recent releases" was vaguer than Appendix E (10 min default for NCCL, 30 min other backends). | **Fixed**: "10 minutes by default for NCCL; verify". |
| DT-10 | ch14 (build gate) | Minor | `--check` failed at the start of the review: ch14 had 4,001 words after the concurrent Hands-on edit. | **Fixed**: trimmed outside the Hands-on note. ch14 is now 3,997 words, **only 3 words of margin** for the Hands-on rewrite. |
| DT-11 | ch14 Fig. 14.2 | Minor | Sequence diagram shows `S->>C: all ranks done`. Completion is reported by the ranks (barrier after each rank's `fsync`), not by the storage; the prose (§14.7) is correct. | **Open**. Recommend `T->>C: shard durable (fsync)`, which doesn't change prose word count materially. |
| DT-12 | ch14 §14.7 pitfall | Minor | `[MEASURED, lab/l2 bundles, PyTorch 2.5.1 …]` torn-tensor finding. The L2 GPU experiment is being rerun and the Hands-on note now reports a new reference run. Appendix E pins PyTorch 2.15 for DCP claims. | **Open**: owner of the L2 rerun should confirm the pitfall still reproduces and update the bundle/version in the label. |
| DT-13 | ch14 §14.2 (Little's law) | Minor | QD = 32 example uses 78 µs latency, lower than the QD = 1 latency of 80 µs. Latency normally rises with queue depth. Arithmetic is right (32 / 78 µs ≈ 410k IOPS ≈ 1.68 GB/s) and it matches the lab's simulated fio run, but the premise is implausible. | **Open**: change the lab and text together, e.g. 100 µs at QD 32 → 320k IOPS ≈ 1.31 GB/s, or state that the drive's internal parallelism keeps latency flat to QD 32. |
| DT-14 | ch14 Table 14.4 | Info | Planner is first-order: failures cluster, restores contend for the PFS, detection times vary. The manuscript has a realism boundary; the concise edition doesn't (no space). Table and inputs are labeled MODELED/ILLUSTRATIVE. | **Open**: add "a ranking, not a budget" to the caption if space frees up. |
| DT-15 | ch14 §14.3 | Info | "no atomic rename" for object stores is true for S3 general-purpose buckets. Some newer S3 storage classes/bucket types and S3-compatibles may offer rename. | **Open**: verify at next Appendix E refresh; manifest-last guidance is unaffected. |
| DT-16 | ch11 §11.9 | Info | Async C ≈ 5 s (ch11) vs 1.19 s (ch14): ch11's value is a conservative illustrative budget. | No change (accepted; DT-06 cross-reference covers it). |
| DT-17 | ch14 §14.6 note | Info | "`dcp.async_save` … returns a future": Appendix E records `Future` or `AsyncSaveResponse`. Text carries "Verify against your release". | No change (accepted). |

**Counts.** Major 1, Minor 9, Info 7 (17 total). Fixed 10 (DT-01 to DT-10); open 5 (DT-11 to DT-15);
accepted without change 2 (DT-16, DT-17).

## Recomputations (all reproduce the published values unless noted)

### Chapter 11

- 6ND = 6 × 70e9 × 4,194,304 = 1.7616e18 FLOP. Ideal step = 1.7616e18 / (256 × 989e12) = 6.96 s; at
  40 % MFU 17.4 s.
- Model state 16 B × 70e9 = 1.12 TB = 14 × 80 GB.
- Korthikanti: 5as/h = 5 × 64 × 4096 / 8192 = 160. 34-term with SP: 4096 × 8192 × 34 / 8 = 142.6 MB.
  Full recompute 2sbh/t = 8.39 MB.
- Baseline memory: P = 70e9 / 32 = 2.1875e9; W + G = 8.75 GB; optimizer 12 × P / 8 = 3.28 GB;
  activations 142.6 MB × 20 × 4 = 11.41 GB; + 4 GB overhead = 27.44 GB (34 %).
- DP: G = 4.375 GB; 2 × 7/8 × 4.375 = 7.66 GB; / 45 GB/s = 0.170 s. Window 13.92 / 128 × 2/3 =
  72.5 ms. Exposed 98 ms.
- TP: M = 4096 × 8192 × 2 = 67.1 MB; V = 4 × 1.75 × 67.1e6 × 20 × 128 = 1.20e12 B (157 × DP).
  Per collective 1.75 × 67.1e6 / 300e9 = 391 µs + 10 µs; × 10,240 = 4.11 s; exposed 3.08 s.
  The (t − 1) identity V = 8(t − 1)·M·L·B/(W·b) checks out algebraically.
- Bubble 3/131 = 2.3 % (pipeline time) and 3/128 × 13.92 = 0.33 s. PP: 2 × 128 × 8.4 MB = 2.15 GB;
  0.048 + 256 × 30 µs = 0.055 s; × 0.5 = 0.028 s.
- Step 13.92 + 0.33 + 3.08 + 0.098 + 0.028 = 17.45 s; MFU 0.399.
- Strong scaling: at 1,024 GPUs, compute 3.48 s, bubble 0.326 s (8.6 %), TP 2,560 × 401 µs × 0.75 =
  0.77 s, DP 1.9375 × 4.375 / 45 − 0.0725 = 0.116 s → 4.70 s, MFU 37.0 %. At 4,096 GPUs: 0.87 + 0.326 +
  0.193 + 0.120 → 1.51 s, bubble 27.3 %, MFU 28.8 %. Efficiency 93 % / 72 %.
- Candidates: D (4/8/8) memory 12.03 + 285 MB × 10 × 8 + 4 = 38.85 GB; TP 5,120 × 345 µs × 0.75 =
  1.33 s; bubble 0.76 s; step ≈ 16.08 s. J (2/8/16) 17.5 + 3.28 + 45.6 + 4 = 70.4 GB. I (b = 4, DDP)
  35 + 45.6 + 4 = 84.6 GB. E (16/2/8) 391 + 186 + 60 = 637 µs × 20,480 = 13.05 s.
- Troubleshooting: 335 + 373 + 60 = 768 µs × 10,240 = 7.86 s; 17.45 + 0.75 × (7.86 − 4.11) = 20.26 s
  versus 20.4 s observed.
- Straggler waste 256 × (1 − 1/1.1) = 23.3 GPUs.
- Young/Daly: √(2 × 45 × 172,800) = 3,944 s; waste 1.14 + 1.66 = 2.80 %; lost per failure 2,872 s ×
  256 = 204 GPU-h; 4 h interval 0.31 + 4.69 = 5.0 %. XL: √(2 × 45 × 10,800) = 986 s; 4.56 + 12.90 =
  17.5 %. Async C = 5 s: τ = 329 s, 1.52 + 9.85 = 11.4 %; R/MTBF = 8.3 %.

### Chapter 12

- Ring 16 ranks, 1 GiB, 50 GB/s: 1.875 × 1,073,741,824 / 50e9 = 40.3 ms; latency 2 × 15 × 5 µs = 150 µs.
- Double binary tree, n = 8: 3 × S/2 + S/2 = 2S versus ring 1.75S (1.14×).
- Listing 12.1: 1,073,741,824 / 5,711.7 µs = 187.99 GB/s; × 1.875 = 352.48. The 1 MiB, 32 MiB and 8 GiB rows
  also check.
- n½ = 28.1e−6 × 354e9 / 1.875 = 5.3 MB; 25 MB bucket at 25 / 30.3 = 82 %.
- c5 fit: 47.3 µs + 1.969 × 25e6 / 346e9 = 190 µs (75 %); 1 GiB: 6.16 ms; n½ = 8.3 MB.
- c3: 4 × 50 × 0.92 = 184 GB/s. Plateau efficiency 345–352 / 400 = 86–88 %.
- All-to-all n = 16: per-NIC S/2, algbw 90, busbw 84.4 GB/s; N = 32: 45 × 32/31 × 255/256 = 46.3 GB/s;
  spine share 7/15 = 47 % and 217/255 = 85 %. Top-1 dispatch 67.1 MB, 33.5 MB / 45 GB/s = 0.75 ms.
- algbw/busbw factors match nccl-tests `PERFORMANCE.md` (Appendix E).

### Chapter 13

- NVLink:NIC bytes 1.20 TB / (7.66 + 2.15) GB = 122.3.
- P(≥ 1 slow rank) at p = 0.1 %: N = 64 → 6.2 %, 256 → 22.6 %, 4,096 → 98.3 %.
- One 29 %-slow rank of 64: 63 × 0.29 × 0.60 s ≈ 11 GPU-s per step, × 20 = 220 GPU-s; / (64 × 0.924 × 20)
  = 18.6 %.
- Small-message budget 1.83–2.33 µs.
- Host staging: uplink 2 × (7.66 + 7.66) = 30.6 GB / 55 GB/s = 0.56 s; DRAM 4 × 30.64 = 122.6 GB / 300 =
  0.41 s. Exposed 0.56 − 0.072 = 0.49 s; +0.39 s / 17.4 = 2.2 %; ≈ 135–140 GPU-h/day. Partial GDR:
  15.3 GB per direction (0.28 s), 61.3 GB DRAM.
- Troubleshooting: 334 GPU-s / (64 × 30 × 1.005 s) = 17.3 %; 1,004 − 177 = 827 ms; − 78 = 749 ms; 25 %
  loss; clock −22 %; tokens +31 %. Rank→host mapping (37 → `orion-n21` GPU 5, etc.) checks.

### Chapter 14

- Tokens/s 4,194,304 / 17.4 = 241,000; × 4 B = 0.96 MB/s. Vision 384,000 × 110 KB = 42 GB/s.
- Little's law: 1 / 80 µs = 12,500 IOPS = 51 MB/s; 32 / 78 µs = 410k IOPS = 1.68 GB/s (see DT-13).
  Stripe 8 × 3.5 = 28, 8 × 6 = 48 GB/s; degraded 8 × 1.5 = 12 versus 26 GB/s.
- Loader: 6.57 ms → 152/s per worker, 1,218/s per node ≈ 0.20 GB/s, metadata 89 %. Shards 8 × 16.8 MB /
  17.6 ms = 7.6 GB/s (38×). Vision 12,000 × 6.57 ms = 79 in flight; prefetch 1,500 × 0.06 = 90.
- Tail: 0.99^256 = 0.076 (92 %); 1 − 0.999^256 = 22.6 %.
- Checkpoint 140 + 3 × 280 = 980 GB (14 B/param, matches REFERENCE_CLUSTER). Per rank 840/256 +
  140/256 = 3.28 + 0.547 = 3.83 GB; node 30.6 GB; staging 1.4 % of 2 TiB. Independent DP restore reads
  840 + 8 × 140 = 1,960 GB = 2 × 980 (the "doubling").
- Write 980 / 60 = 16.33 s; δ_sync 17.83 s; snapshot 3.83 / 25 = 0.153 + 0.5 = 0.653 s; L = 18.49 s;
  δ_async = 0.653 + 0.535 = 1.188 s; local 30.6 / 28 = 1.09 s, / 48 = 0.64 s; δ_local 3.08 s;
  two-level δ = 0.653 + 0.03 × (1.09 + 3.27) = 0.78 s.
- Intervals: √(2 × 1.188 × 172,800) = 641 s → 37 steps (643.8 s); sync 2,483 s → 143 (2,488.2 s); Daly
  2,482.3 × 1.0024 − 17.83 = 2,470.5 s; two-level 519 s → 30 (522 s); sync local 1,032 s → 60 (1,044 s).
- Time-to-resume 300 + 330 + 20 + 150 + 8.17 = 808.2 s; hard 1,048.2 s; E = 904.2 s.
- Lost GPU-h/day (0.5 failures/day, 256/3,600 = 0.0711 GPU-h per s):
  - Async PFS: 134.2 × 1.188 s → 11.34 + 0.5 × (340.4 + 904.2) × 0.0711 = 44.25 → **55.6**.
  - Two-level: 165.5 × 0.78 s → 9.2. Lost work 0.6 × 264.3 + 0.4 × 1,326.1 = 689 s. Resume
    0.6 × 800.7 (local load) + 0.4 × 1,048.2 = 899.7 s. → **65.7**.
  - Sync local: 18.1. Lost work 522 + 0.6 × 2.59 + 0.4 × 20.4 = 532 s. → **69.0**.
  - Sync PFS: 44.0 + 0.5 × (1,262 + 904.2) × 0.0711 = 77.0 → **121.1**.
  - At 10 % hard: two-level 51.7 vs async 53.0, matching the text's 51.75 vs 53.03. Detection
    300 → 60 s saves 0.5 × 240 × 0.0711 = 8.5 GPU-h/day. Per failure 904 s × 256 / 3,600 = 64.3 GPU-h.
- Llama 3: 419 / (54 d × 16,384) = 4.74e−4 per GPU-day; × 256 = 0.121/day → M = 198 h. At 198 h
  the async interval is √(2 × 1.188 × 712,800) = 1,301 s → 75 steps (21.8 min), as in the manuscript.
- Troubleshooting: 256 × 1,025 = 262,400 creates / 2,700 s⁻¹ = 97 s; node rate 30.6 GB / 16.33 s = 15 Gb/s
  (< 4 % of 400 Gb/s).

No numeric errors were found in the concise chapters, the manuscripts' corresponding passages, or the
canonical values in `docs/REFERENCE_CLUSTER.md`. None of those were changed for numbers.

## Recovery completeness (release gate)

| Concept | Where covered | Assessment |
|---|---|---|
| GPU / node failure detection (watchdog, Xid, hangs, stragglers, silent degradation, SDC) | ch11 §11.9, Fig. 11.2; ch13 §13.6–13.7; ch19 | Adequate |
| Evidence before restart (flight recorder, `py-spy`, NCCL logs) | ch11 §11.9, Table 11.6; ch12 Table 12.6; ch19 | Adequate |
| Rank replacement / spares (same local ranks, rail alignment, no spares in ORION-256, declared spare pool variation) | ch11 (repair or DP = 7); ch14 step 7 (spare pool outside ORION-256); ch19 (spare sizing, re-packing) | Adequate |
| Elastic recovery (`torchrun --max-restarts`, `--nnodes=MIN:MAX`, re-sharding on world-size change) | ch11 §11.9 (**added, DT-01**); ch14 §14.6 (format with global shapes enables resharding); ch19 (elastic loses whole DP replicas) | Adequate after fix. It was a gap in concise ch11, cited by Appendix E. |
| Checkpoint consistency (consistent cut, torn async snapshots, per-rank `fsync`, barrier, manifest, temp-name commit, `rename`, directory `fsync`, `latest` only after commit, manifest-last on object stores) | ch14 §14.6–14.7, Fig. 14.2 | Strong. Fig. 14.2 has one minor arrow (DT-11). |
| Validation before restore (ladder, ignore `latest`, first-step loss check) | ch14 Table 14.2, operating notes | Strong |
| Retention and rollback past corruption | ch11 (two generations, roll back past SDC); ch14 (retain validated, not count-based) | Adequate |
| Restart behaviour and cost (detect, collect, isolate, replace, restore, validate; R decomposition; retry/quarantine policy) | ch11 Fig. 11.2; ch14 step 7; ch19 retry policy | Adequate |
| RPO / RTO (τ + L worst case, skipped checkpoints stretch RPO, age-of-newest-validated alert, RTO from measured time-to-resume) | ch14 §14.8, Tables 14.4–14.5; ch19 definitions | Adequate |
| Data-pipeline resume state (shard order, position, seed, RNG) | ch14 §14.4, §14.6 | Adequate |
| Restore read amplification across DP replicas | ch14 §14.6 | Adequate |

**Verdict: PASS** for the release gate, after DT-01. Open recovery-adjacent items (DT-11, DT-12)
are diagram and evidence-bundle polish, not missing concepts.

## Other checks

- **Evidence labels.** Modeled results are presented as models. ch11's worked example says it shows
  consistency, not truth. The only `[MEASURED]` claim (ch14 pitfall) carries a procedure and version
  (see DT-12). One non-standard label was fixed (DT-02).
- **Generalization.** H100 figures carry `[VENDOR-SPEC, 2026-10]` and "H100-class" wording. ORION
  quantities are `[ILLUSTRATIVE]` or `[MODELED]`. The spare pool in ch14 is declared as a variation, as
  `REFERENCE_CLUSTER.md` requires.
- **Mermaid diagrams.** Figs 11.1, 11.2, 12.1, 13.1, 13.2 and 14.1 match the prose: TP on NVLink,
  DP/PP rail-local, PXN on NIC 0, the SHM fallback crossing sockets with GPU 5 on switch 2, and GPU 2
  on switch 1. Fig. 14.2 is DT-11.
- **Version-sensitive guidance.** Checked against Appendix E for the NCCL variables (`NCCL_PXN_DISABLE`,
  `NCCL_P2P_PXN_LEVEL`, `NCCL_NVLS_ENABLE`, `NCCL_ALGO` names, `NCCL_MIN/MAX_CTAS`, `NCCL_TOPO_DUMP_FILE`,
  GDR level `PXB`, GDR log level 2.29/2.30, error formats), the PyTorch items (DDP 25 MiB, timeout,
  flight-recorder variables, DCP `.metadata` commit, `async_save`, `torchrun`), Megatron rank order,
  S3 limits and conditional writes, and fio `psync`. All consistent apart from DT-03 and DT-07 (fixed).
- **Lab safety.** Warnings are present for nccl-tests at 8 GiB (ch12), discriminating tests on
  reserved allocations (ch12), the read-only GDR plan plus ACS/IOMMU change control (ch13), no
  throttling in production (ch13), fio on raw devices and shared-PFS load tests (ch14), and PFS sweeps
  and striping changes (ch14 operating notes). One inconsistency was fixed (DT-05).
- **Word budget.** `python scripts/build_concise.py --check` after the edits: ch11 3,998, ch12 4,000,
  ch13 3,967, ch14 3,997 (all OK). ch12 and ch14 are at or near the 4,000 cap.

## Files changed

- `concise/ch11.md`, `concise/ch12.md`, `concise/ch13.md`, `concise/ch14.md`. The ch14 Hands-on note
  was not touched.
- `book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/manuscript.md` (DT-02, DT-05).
- This log.
