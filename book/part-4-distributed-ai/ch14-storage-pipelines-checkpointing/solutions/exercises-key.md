# Chapter 14 — Exercise Answer Key (INSTRUCTOR ONLY)

All numbers are `[MODELED]` from the stated inputs unless noted. Every calculation below was
computed twice (by hand and with `solutions/lab/storage_lab.py` or a Python one-liner). Marking:
award the stated points; deduct for missing units, missing evidence labels, or unlabelled
assumptions as indicated.

---

## 14.1 Little's law on NVMe (5 points)

(a) IOPS at QD 1 = 1 / latency = 1 / 95 µs = **10,526 IOPS**; × 4,096 B = **43.1 MB/s**.
(b) QD = IOPS × latency = 330,000 /s × 0.097 × 10⁻³ s = **32.0**.
(c) `%util` is the fraction of wall time with *at least one* request outstanding. NVMe services
many requests in parallel, so a drive at QD 1 reads 100 % while delivering a few percent of its
capability. Saturation shows as latency rising at constant throughput as QD increases.

*Marking:* 2 + 2 + 1. *Common mistakes:* using µs as ms (off by 1,000); MB vs MiB confusion (accept
41.1 MiB/s if labelled).

## 14.2 Metadata path versus data path (5 points)

`open()` → metadata server (MDS, serving an MDT): name lookup, permission check, and the file's
**layout** (stripe count, stripe size, list of OSTs and object IDs). `read()` → the object storage
servers (OSS) holding those OSTs, directly, using the layout. `close()` → MDS (updates attributes;
releases open state). Stripe count = how many OSTs a file is spread over; stripe size = bytes written
to one OST before moving to the next. Wider striping does not help when many clients each write their
own file concurrently (file count already spreads load; more stripes add objects, locks, and
per-file overhead), or for small files (smaller than one stripe).

*Marking:* 2 for the RPC sequence, 2 for stripe semantics, 1 for a valid counter-case.

## 14.3 What is in a checkpoint (5 points)

Training state 16 B/param = 2 (BF16 weights) + 2 (BF16 gradients) + 12 (FP32 master, Adam m, Adam
v). Gradients are recomputed in the first step after resume, so are not saved: 14 B/param.
Non-tensor items (any three): step counter / learning-rate scheduler state (otherwise LR schedule
restarts — warm-up repeats, loss jumps); data-loader position and shuffle seed (data replayed or
skipped — biased training, non-reproducibility); RNG states (dropout/augmentation streams change —
non-reproducible, and for some methods non-equivalent); loss-scaler state for FP16 (overflow
behaviour changes).

*Marking:* 2 for the breakdown, 1 per item → consequence pair.

## 14.4 Blocking time versus completion latency (5 points)

Blocking time: time the training loop is stalled (snapshot to staging buffer + coordination).
Completion latency L: snapshot start → commit marker durable. A failure at uniform time u after the
latest snapshot (interval τ): if u ≥ L, the latest checkpoint is usable and lost work is u; if u < L
(probability L/τ), it is not, and lost work is u + τ. E[lost] = τ/2 + τ · L/τ = **τ/2 + L** (for
L ≤ τ). Blocking time does not appear because training is not lost during it; it is a cost paid on
every checkpoint (overhead), not on failure.

*Marking:* 2 definitions, 3 derivation. *Common mistake:* saying async checkpointing reduces RPO;
it reduces overhead, which makes a shorter τ affordable.

## 14.5 Commit protocol (5 points)

1. write shard files → 2. fsync shard files (shard data durable before anything references it) →
3. barrier (every rank succeeded) → 4. write manifest → 5. fsync manifest (the description of the
checkpoint is durable before the commit refers to it) → 6. write `COMMIT.tmp` → 7. fsync
`COMMIT.tmp` (marker contents durable before it becomes visible) → 8. rename → `COMMIT` (atomic
visibility) → 9. fsync the directory (the rename itself — the directory entry — survives a crash) →
10. advance `latest` (preferably after validation).
Object store: no rename and no directories; upload all shards, then upload the manifest last; the
manifest's existence (plus validation) is the commit. Use conditional writes or unique keys to avoid
overwriting, and never list-then-assume.

*Marking:* 3 ordering (−1 per misplaced fsync), 2 object-store adaptation.

## 14.6 Recovery vocabulary (5 points)

| Term | Definition | Category |
|---|---|---|
| Checkpoint overhead | Training time lost per checkpoint ÷ interval (δ/τ) | Model output / measurement |
| Completion latency | Snapshot start → commit durable | Measurement |
| RPO | Max acceptable lost progress; achieved worst case τ + L | Objective |
| RTO | Max acceptable failure → training progressing again | Objective |
| Time-to-resume | Measured failure → first completed step after restart | Measurement |
| Lost accelerator-hours | GPUs × (overhead + recomputed work + time-to-resume) | Model output (or measured per incident) |

*Marking:* ~1 per two rows; category must distinguish objective from evidence.

## 14.7 Tail at scale (5 points)

P(≥ 1 read beyond p99) = 1 − 0.99^256 = **0.92**; beyond p99.9: 1 − 0.999^256 = **0.23**.
At 4,096 ranks: 1 − 0.99^4096 ≈ **1.0** (0.99^4096 ≈ e^−41); 1 − 0.999^4096 = **0.98**.
Interpretation: at scale the per-read p99.9 is the typical step's experience; accept storage on
p99.9 and reduce exposure (prefetch to absorb tails, fewer synchronous reads per step).

*Common mistake:* assuming independence holds; note that correlated tails (a slow target) make it
worse for some steps and better for others — the expectation argument still motivates p99.9.

## 14.8 Checkpoint size, write time, and RPO exposure (10 points)

(a) S = 34 × 10⁹ × 14 B = **476 GB**; per GPU 476 / 128 = **3.72 GB**.
(b) Effective bandwidth 50 × 0.80 = 40 GB/s; write = 476 / 40 = **11.9 s**; blocking =
11.9 + 1.0 = **12.9 s**.
(c) Overhead = 12.9 / 900 = **1.43 %**.
(d) RPO max = τ + L = 900 + 12.9 = **912.9 s ≈ 15.2 min**; expected lost work = τ/2 + L =
450 + 12.9 = **462.9 s**.
(e) Async: blocking 0.6 s → overhead 0.6 / 900 = 0.067 % (0.11 % including 3 % interference over the
12.9 s persist: (0.6 + 0.03 × 12.9) / 900). Completion L = 0.6 + 12.9 = 13.5 s, RPO max =
**913.5 s — unchanged**. Asynchrony cut the premium, not the exposure.
(f) τ + 13.5 ≤ 300 → τ = **286.5 s** (≈ 4.8 min); δ = 0.6 + 0.03 × 12.9 = 0.987 s; overhead =
0.987 / 286.5 = **0.34 %** — still a quarter of the original synchronous overhead with a third of
the RPO.

*Marking:* 1 + 2 + 1 + 2 + 2 + 2. *Common mistakes:* using 50 GB/s without efficiency; omitting
commit time; claiming async reduces RPO.

## 14.9 Metadata-bound versus bandwidth-bound pipeline (10 points)

(a) Per node: 8 × 2,000 = **16,000 images/s**; × 120 KB = **1.92 GB/s**. Cluster (16 nodes):
**256,000 images/s, 30.7 GB/s**.
(b) One file per image: per-sample latency 4.0 + 0.6 + 0.2 = 4.8 ms; in flight per node =
16,000 × 0.0048 = **76.8**. Cluster `open` rate **256,000/s** vs 50,000/s available → max per node
50,000 / 16 = **3,125 images/s (19.5 % of need)** → **metadata-bound** regardless of worker count.
(c) Shards: 512 MiB / 120 KB = 536,870,912 / 120,000 ≈ **4,474 images per shard**; opens per node =
16,000 / 4,474 ≈ **3.6/s** (57/s cluster-wide). PFS read share = 30.7 / 160 = **19 %**. Request rate
per node = 1.92 × 10⁹ / 16,777,216 = 114 requests/s; in flight = 114 × 0.012 = **1.4** → bandwidth-
bound in character but far from any limit.
(d) Dataset = 40 × 10⁶ × 120 KB = **4.8 TB** — fits in 30.7 TB raw per node (leave room for
checkpoint staging). Full copy on every node: 16 × 4.8 TB = 76.8 TB from the PFS at 160 GB/s =
**480 s (8 min)**, 10 GB/s per node (well under the 50 GB/s frontend). Partitioned caching (each node
caches the shards it is assigned) cuts this 16× if the sampler is partition-aware.
(e) Recommend repacking into shards (WebDataset/MDS-style) — removes the metadata bottleneck with a
5× bandwidth margin — optionally plus local staging to decouple from other tenants. Confirm on the
current pipeline with the lab's window metrics: `meta_time_share` ≥ 0.5 and `mean_read_bytes` < 1 MiB
(metadata class), and MDS ops/s at its plateau while OST throughput is low.

*Marking:* 2 + 3 + 2 + 2 + 1. *Common mistake:* recommending more workers.

## 14.10 Interval and lost GPU-hours at M = 198 h (8 points)

M = 198 × 3,600 = 712,800 s; failures/day = 86,400 / 712,800 = 0.1212.

| Strategy | τ (steps) | Overhead | RPO max | Lost GPU-h/day (ckpt + fail) |
|---|---|---|---|---|
| async PFS | 1,305.0 s (75) | 0.09 % | 1,323 s | 5.59 + 13.58 = **19.2** |
| async two-level | 1,061.4 s (61) | 0.07 % | 5,328 s | 4.54 + 19.74 = **24.3** |
| sync local + drain | 2,105.4 s (121) | 0.15 % | 2,126 s | 9.00 + 16.91 = **25.9** |
| sync PFS | 5,046.0 s (290) | 0.35 % | 5,064 s | 21.71 + 29.69 = **51.4** |

Hand check (async PFS): Young = √(2 × 1.188 × 712,800) = √1,693,786 = 1,301.5 s → 74.8 steps → 75
→ 1,305.0 s. Checkpoints/day 86,400 / 1,305 = 66.2 × 1.188 s = 78.7 s × 256 / 3,600 = 5.59 GPU-h.
E[lost] = 652.5 + 18.5 = 671.0 s; E[resume] 904.2 s; 0.1212 × 1,575.2 s × 256 / 3,600 = 13.58 GPU-h.
Total 19.2.

Ranking unchanged; losses fall ~2.9× (55.6 → 19.2 for async). Intervals stretch by √(198/48) ≈ 2.0×
(Young ∝ √M): 643.8 → 1,305 s. RPO max grows to 22 min (async) and 84 min (sync); if Halcyon's RPO
policy is, say, 15 min, the policy — not Young — sets the interval (link to 14.16).

*Marking:* 4 table, 3 hand check, 1 interpretation.

## 14.11 Lab (see lab rubric, 100 points scaled to 20)

Reference results and planted anomalies: `solutions/lab/README.md`. Memo expectations: Table 14.8
reproduced with assumptions; two-level sensitivity explained (hard-failure fraction and the k·τ RPO);
Part B diagnosis — metadata-bound epoch, bandwidth-bound shards, read-p99 inflation 13–17 s caused by
a concurrent write burst (next evidence: PFS write throughput and checkpoint log timestamps for the
same window), slow target 5 (next evidence: per-target server metrics, RAID/rebuild status), nvme2
low write bandwidth (check `LnkSta`, temperature), nvme5 tail-only fault (repeat with longer runtime;
check firmware); Part C — each defect explained and `step_001800` selected.

## 14.12 The resume that trained worse (15 points)

(a) Symptom: loss jumped from 1.82 to ~2.27 at resume and is not recovering.

| # | Hypothesis | Evidence for/against | Discriminating test |
|---|---|---|---|
| H1 | Restored an incomplete checkpoint: `latest` → step_088327, whose persist was in flight | Snapshot 03:12:55, failure 03:13:02 — 7 s into a ~19 s persist; **no COMMIT**; 31 load warnings; "missing=0" checked only file existence | Run the validator: NO_COMMIT and SIZE/CHECKSUM defects; compare shard sizes with manifest |
| H2 | LR scheduler / step state reset | Would show LR back in warm-up | Check logged LR at step 88328 vs 88327 |
| H3 | Data-loader state lost (replay/skip) | Usually a small, transient effect, not +0.45 persistent | Compare sample IDs after resume with the planned order |
| H4 | Faulty replacement hardware computing wrongly | Possible after a node swap | Per-rank grad norms; rerun one step with the new node excluded |

(b) Root cause: the trainer advanced `latest` at snapshot time, not after commit; the restart
controller trusted `latest`. The persist of step 88327 was interrupted (orion-n21's eight shards and
possibly others truncated). The 31 warnings are most likely size/shape mismatches or missing keys
when loading truncated optimizer-state shards, which the loader then default-initialised (e.g.
zeroed Adam moments for some parameters) — a "valid-looking" but corrupt state.
(c) Stop the job now; run the validator; restore from **step_088290** (committed at 03:02:30 with
completion 18.9 s); verify its first-step loss ≈ 1.82. Cost: the 2 h of training since 03:28 are
discarded: 2 × 256 = **512 GPU-h**; plus 37 steps between 88290 and 88327 = 37 × 17.4 = 643.8 s →
643.8 × 256 / 3,600 = **45.8 GPU-h**; plus another restart, ~808 s soft (Section 14.12, Step 7) →
**57.5 GPU-h**. Total ≈ **615 GPU-h**, versus continuing to train a damaged model.
(d) (1) Advance `latest` only after commit *and* validation, and make the restart controller run the
validation ladder and ignore `latest` (Section 14.10, commit step 5 and Table 14.5). (2) Add the
semantic check: compare first-step loss after resume with the loss recorded at save, alert/abort
outside tolerance — it would have caught this at 03:28.

*Marking:* 5 hypothesis table, 3 root cause, 4 recovery with arithmetic, 3 prevention.
*Common mistakes:* blaming the new node first without testing; restoring 88327 again.

## 14.13 Checkpoint strategy for ORION-XL (15 points)

YAML changes from `orion_ckpt_inputs.yaml`: `params: 405.0e9`, `gpus: 4096`, `nodes: 512`,
`step_time_s: 20.0`, `pfs_write_GBps: 400`, `pfs_read_GBps: 800`, `commit_overhead_s: 3.0`,
`job_mtbf_h: 3.0` (canonical: 1,536 node-hours / 512 nodes).

Key quantities: S = 405 × 10⁹ × 14 = **5.67 TB**; per GPU 1.38 GB; T_pfs_w = 5,670 / 300 = 18.9 s;
sync δ = 21.9 s; async blocking 1.38 / 25 + 0.5 = 0.555 s, δ = 0.555 + 0.03 × 21.9 = 1.21 s,
completion 22.5 s; failures/day = 24 / 3 = **8**.

| Strategy | τ (steps) | Overhead | RPO max | E[resume] | Lost GPU-h/day (ckpt + fail) |
|---|---|---|---|---|---|
| async PFS | 180 s (9) | 0.67 % | 202 s | 905 s | 662 + 9,265 = **9,927** |
| async two-level | 140 s (7) | 0.49 % | 726 s | 900 s | 478 + 9,964 = **10,441** |
| sync local + drain | 300 s (15) | 1.32 % | 325 s | 900 s | 1,298 + 9,667 = **10,966** |
| sync PFS | 700 s (35) | 3.13 % | 722 s | 905 s | 3,076 + 11,627 = **14,702** |

Hand check (async PFS): Young = √(2 × 1.212 × 10,800) = 161.8 s → 8.1 steps → 9 → 180 s.

Expected answer: asynchronous to PFS every 9 steps (3 min); even so ≈ 10.1 % of the 98,304
GPU-h/day is lost — at M = 3 h, failures, not checkpoints, decide the economics.
Capacity: 25 TB / 5.67 TB = 4.4 → at most **4** checkpoints: 3 validated + 1 in flight = 22.7 TB
(2.3 TB headroom); archive one checkpoint per hour (or per N) to the object store; retention counts
validated checkpoints only. RPO target ≤ 5 min (achieved max 202 s); RTO target 15 min (expected
905 s — at the limit; justify or improve). PFS burst: 5.67 TB in 18.9 s at the full 300 GB/s
effective, plus commit, every 180 s ≈ 12 % duty cycle and 7.9 % of write capacity on average —
other tenants see ~22 s of saturated writes every 3 min; propose bandwidth limiting, a dedicated
checkpoint tier, or local/peer staging.
Highest-leverage improvement: **time-to-resume**. Failure cost is 9,265 of 9,927 GPU-h/day;
8 × 905 s × 4,096 / 3,600 = 8,241 GPU-h/day is restart time. Cutting detection 300 → 60 s saves
8 × 240 × 4,096 / 3,600 = **2,185 GPU-h/day**, over three times all checkpoint overhead (662).
Spare capacity (a declared spare pool, or a pre-agreed shrink to a smaller DP), pre-pulled images, faster rendezvous, and in-memory peer checkpointing (Gemini-style,
which also shrinks τ/2 losses) follow; at this failure rate, elastic/fault-tolerant training that
avoids full-job restarts (Chapter 19) is the structural fix.

*Marking:* 4 planner + YAML, 3 capacity/retention, 3 RPO/RTO targets, 2 tenant burst, 3 leverage
argument. Accept other strategies if defended with numbers (e.g. two-level + partner copy).

## 14.14–14.17 Reflection (5 points each)

**14.14** Most uncertain: PFS efficiency (measure: full-cluster checkpoint write of real shards from
all ranks, ≥ 5 runs in a window, bytes / wall time open→commit); job MTBF and hard-failure fraction
(measure: incident records over ≥ 1 quarter, classified soft/hard); restart components (measure:
timestamps for detect/relaunch/load/first step from ≥ 5 real or drilled restarts); interference
(measure: step time during vs outside persist windows, ≥ 50 checkpoints).
**14.15** Not captured: MDS request queueing and RPC flow control (real tails worse, bursty); client
page/metadata caching (better for re-reads); lock contention on shared files (worse); server-side
caching and readahead (better for sequential); network congestion on the frontend (worse);
correlated slowdowns across targets (worse).
**14.16** (1) RPO policy: if Young's τ exceeds the RPO target, the policy sets τ — detect via "age of
newest validated checkpoint" vs target. (2) PFS fairness/capacity: burst duty cycle or quota may cap
frequency — detect via PFS write utilisation and other tenants' read p99 during bursts, or quota
usage vs retention needs. (Also accept: one-in-flight limit when L approaches τ — skipped/back-pressured
checkpoint counter.)
**14.17** Modeled (fine for design): sizes, intervals, sensitivities. Must measure: PFS efficiency
at 256 writers, snapshot time and staging memory on HX8, interference on step time, restore read
rate (incl. read amplification), time-to-resume components, real M and hard fraction, validator run
time on 980 GB.

*Marking:* specific, measurable answers; deduct for generic "test it more".

## 14.18 Deliverable (rubric, 30 points)

| Element | Points |
|---|---|
| Benchmark plan: NVMe, PFS bandwidth, PFS metadata (`mdtest`), read-under-write; exact parameters, warm-up, ≥ 5 reps, percentiles, manifest fields | 8 |
| Checkpoint design: strategy, interval with derivation, staging memory, commit protocol, validation ladder, retention, archive | 8 |
| RPO/RTO analysis: components of time-to-resume, lost GPU-h/day, sensitivity to M and detection time | 6 |
| Restore test procedure (including a planted corrupt checkpoint and a semantic loss check) | 4 |
| Measured vs modeled statement; evidence labels throughout | 4 |

## 14.19 Checkpoint benchmark and restore test (L2, 15 points)

Expected shape of results (values depend on hardware): blocking time of `async_save` a small
fraction of `save`; completion time ≥ `save` time; measurable step-time increase during persist;
pinned host memory ≈ state size (× 2 if double-buffered). Restore test must show the validator
rejecting the corrupted copy and the first-step loss matching the recorded loss within the stated
tolerance (e.g. relative 1e-3 for BF16). *Marking:* 5 manifest + method (warm-up, reps), 5 results
table with spread, 5 restore test. Reject results without repetition or without a manifest.
