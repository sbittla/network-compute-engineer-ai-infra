# Chapter 14 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation ·
L2 one GPU host · L3 multi-node with shared storage. Unless stated, use ORION and W-TRAIN values from
`docs/REFERENCE_CLUSTER.md` and the chapter. Label every number you produce `[MODELED]`,
`[SIMULATED]`, `[MEASURED]`, or `[ILLUSTRATIVE]`. Answers: `solutions/exercises-key.md` (instructors).

Exercises marked **(outline)** are mandated by the course outline (Section 14, Section 20.1, and the
Section 21 integration map for Chapter 14 / Week 11).

---

## A. Knowledge checks

**14.1 Little's law on NVMe** ★ · L1
A drive serves 4 KiB random reads with a mean latency of 95 µs. (a) What IOPS and MB/s does it
deliver at queue depth 1? (b) `iostat -x` shows `r/s` = 330,000 and `r_await` = 0.097 ms. What is
the average queue depth? (c) Why is `%util` = 100 % not evidence that the drive is saturated?
*Evidence required:* the formula, substituted values, and results with units.

**14.2 Metadata path versus data path** ★ · L1
In a Lustre-class parallel file system, which server handles `open()`, which handles `read()`, and
what does a client obtain at open time that lets it bypass the metadata server afterwards? Explain
what stripe count and stripe size control, and give one case where *wider* striping does not help.
*Evidence required:* a labelled sketch or numbered sequence of the RPCs for open → read → close.

**14.3 What is in a checkpoint** ★ · L1
Explain why W-TRAIN's checkpoint is 14 B/param while its training state is 16 B/param. List three
non-tensor items that a checkpoint must contain for a resume to be equivalent, and what goes wrong
without each. *Evidence required:* the byte breakdown and three item → consequence pairs.

**14.4 Blocking time versus completion latency** ★ · L1
For an asynchronous checkpoint, define blocking time and completion latency. Why does completion
latency, not blocking time, enter the expected lost work per failure? *Evidence required:* the
expression τ/2 + L and a one-paragraph derivation.

**14.5 Commit protocol** ★ · L1
Put these steps in the correct order and say what failure each `fsync` protects against: write
`COMMIT.tmp`; fsync shard files; barrier; write manifest; rename `COMMIT.tmp` → `COMMIT`; fsync the
directory; fsync manifest; fsync `COMMIT.tmp`; write shard files; advance `latest`. How does the
protocol change on an object store? *Evidence required:* ordered list with one justification per
fsync.

**14.6 Recovery vocabulary** ★ · L1
Define checkpoint overhead, completion latency, RPO, RTO, time-to-resume, and lost
accelerator-hours. Which are objectives, which are measurements, and which are model outputs?
*Evidence required:* a six-row table with definition and category.

**14.7 Tail at scale** ★ · L1
256 ranks each issue one storage read per step and the step waits for all of them. What fraction of
steps sees at least one read slower than the per-read p99? The p99.9? What happens to these numbers
at 4,096 ranks? *Evidence required:* the expression 1 − q^N, values to two significant figures.

## B. Worked problems

**14.8 Checkpoint size, write time, and recovery-point exposure** ★★ · L1 **(outline)**
A 34 × 10⁹-parameter model trains with BF16 mixed precision and Adam (14 B/param checkpointed) on 128
GPUs. The PFS writes 50 GB/s aggregate; assume 80 % efficiency for a full-cluster burst and 1.0 s for
barrier + metadata + commit. The team checkpoints synchronously every 15 minutes of training.
(a) Checkpoint size and per-GPU shard size. (b) Write time and blocking time. (c) Overhead %.
(d) Worst-case RPO and expected lost work per failure. (e) They switch to asynchronous saves with a
0.6 s snapshot and keep the 15-minute interval: what happens to overhead and RPO? (f) What interval
would bring worst-case RPO to ~5 minutes, and what overhead would that cost (assume 3 %
interference while persisting)? *Evidence required:* formula → substitution → result for each part.

**14.9 Metadata-bound versus bandwidth-bound pipeline** ★★ · L1 **(outline)**
A vision job on 16 HX8 nodes needs 2,000 images/s per GPU. The dataset is 40 million images averaging
120 KB. The PFS metadata service sustains ~50,000 `open`/s for this job `[ILLUSTRATIVE]` and the PFS
reads 160 GB/s aggregate. Per sample: `open` 4.0 ms, `read` 0.6 ms, `close` 0.2 ms. Shard option:
512 MiB shards read in 16 MiB requests of 12 ms each.
(a) Required images/s and GB/s per node and cluster-wide. (b) For one file per image: requests in
flight per node, cluster `open` rate, and the maximum images/s per node the metadata service allows.
(c) For shards: opens per second per node, bandwidth share of the PFS, and requests in flight per
node. (d) Staging alternative: does the dataset fit on local NVMe, and how long does staging take if
all nodes stage at once? (e) Recommend, and say which lab metric would confirm your diagnosis on the
current pipeline. *Evidence required:* all arithmetic; a classification of each option as
metadata-bound or bandwidth-bound.

**14.10 Interval and lost accelerator-hours at a measured failure rate** ★★ · L1
Redo the worked example (Section 14.12) with M = 198 h, the rate derived from the Llama 3 report.
For synchronous and asynchronous PFS strategies, compute the Young interval (rounded up to whole
17.4 s steps), overhead, RPO max, and lost GPU-hours per day. Use your Part A planner and also verify
one strategy by hand. What changed in the ranking and the magnitudes, and why?
*Evidence required:* planner output table plus one hand calculation.

## C. Hands-on lab

**14.11 Progressive Lab 6 — Storage and checkpoint** ★★ · L1 (L2/L3 extensions) **(outline)**
Complete [lab/README.md](lab/README.md) Parts A–C until `python check.py` reports 15/15, and write
the two-page memo described in lab Section 7. *Evidence required:* checker output and the memo.

## D. Troubleshooting case

**14.12 The resume that trained worse** ★★★ · L1
After a node failure at 03:13, W-TRAIN restarted automatically at 03:28, at the same 256-GPU
layout using a replacement node from Halcyon's spare pool outside ORION-256 (Section 14.12, Step 7),
and has been running for two hours. The training loss before the failure was 1.82 and falling; since the restart it has been
2.25–2.31 and is not recovering. Evidence available:

```text
03:02:11 rank0 ckpt step=88290 phase=snapshot blocking_s=0.65
03:02:30 rank0 ckpt step=88290 phase=commit completion_s=18.9
03:12:55 rank0 ckpt step=88327 phase=snapshot blocking_s=0.66
03:13:02 scheduler: node orion-n21 NOT_RESPONDING; job 4471 failed
03:26:10 restart-controller: resolved checkpoint via /pfs/ckpt/w-train/latest -> step_088327
03:27:21 rank0 load step=88327 shards_loaded=256 missing=0 warnings=31
03:28:00 rank0 step=88328 loss=2.27
```

```console
$ ls /pfs/ckpt/w-train/step_088327/ | head -3; ls /pfs/ckpt/w-train/step_088327/ | wc -l
manifest.json
shard_000.bin
shard_001.bin
257
$ ls /pfs/ckpt/w-train/step_088327/COMMIT
ls: cannot access '/pfs/ckpt/w-train/step_088327/COMMIT': No such file or directory
```

(a) Apply the diagnostic loop: state the symptom, rank at least three hypotheses, and give the
discriminating evidence for each. (b) What is the most likely root cause, and what would the 31 load
warnings probably say? (c) What is the safe recovery action now, and what does it cost in GPU-hours?
(d) What two changes prevent recurrence? *Evidence required:* hypothesis table, the recovery
decision with arithmetic, and the two changes mapped to Section 14.10.

## E. Design challenge

**14.13 Checkpoint strategy for ORION-XL** ★★★ · L1 **(outline)**
Halcyon will train a 405 × 10⁹-parameter model on ORION-XL (4,096 GPUs, 512 HX8 nodes) with a 20 s
step. Assume `[ILLUSTRATIVE]`: PFS 400 GB/s write and 800 GB/s read at 75 % efficiency, commit 3 s,
a PFS checkpoint quota of 25 TB, the canonical ORION-XL job MTBF of 3 h (`docs/REFERENCE_CLUSTER.md`),
40 % hard failures; other inputs, including restart components, as in `orion_ckpt_inputs.yaml`. Design a checkpoint strategy that balances checkpoint
overhead, storage capacity, restart time, and failure frequency. Your answer must include the
strategy comparison (from your planner with a modified YAML), the chosen interval, retention policy
that fits the quota, RPO and time-to-resume targets, the PFS burst every other tenant will see, and
the single highest-leverage improvement beyond checkpointing. *Evidence required:* the YAML you used,
the planner table, a capacity calculation, and a one-page defended recommendation.

## F. Reflection and review

**14.14** ★ · L1 — Which three inputs to the Part A planner are most uncertain for ORION, and what
specific measurement (tool, procedure, number of repetitions) would replace each?
*Evidence required:* three input → measurement pairs.

**14.15** ★ · L1 — List four behaviours of a real parallel file system that the lab's simulated
trace does not capture, and for each say whether it would make the real tail better or worse.
*Evidence required:* four items with a direction and a reason.

**14.16** ★★ · L1 — Young's formula ignores storage capacity and other tenants. Describe two
situations in which the checkpoint interval should be set by a constraint other than Young, and how
you would detect each from metrics. *Evidence required:* two constraints with a metric each.

**14.17** ★ · L1 — Before you approve the worked example's recommendation for production, what
evidence is still missing? Distinguish what can be modeled from what must be measured.
*Evidence required:* a list separated into "modeled" and "must measure".

## G. Chapter deliverable and hardware-backed exercises

**14.18 Deliverable: I/O benchmark plan and checkpoint/recovery design** ★★★ · L1 (L2/L3 optional)
**(outline)**
Produce a document (≤ 6 pages) containing: (1) an I/O benchmark plan for ORION covering local
NVMe, PFS bandwidth, PFS metadata rate, and read-under-write interference — each with tool, exact
parameters, warm-up, ≥ 5 repetitions, percentiles reported, and the manifest fields recorded; (2) a
checkpoint/recovery design for W-TRAIN: strategy, interval, staging buffers, commit protocol,
validation ladder, retention, and archive; (3) an RPO/RTO analysis with time-to-resume broken into
components and lost accelerator-hours per day; (4) a restore test procedure; (5) an explicit
statement of which values are modeled and which are measured. *Evidence required:* the document,
the planner output it cites, and the validator run on the lab store.

**14.19 Checkpoint benchmark and restore test** ★★ · L2 **(outline)**
On one GPU host with PyTorch 2.x, checkpoint a model of ≥ 1 GB of state with
`torch.distributed.checkpoint.save` and with `async_save` (verify the API for your version). Measure,
over ≥ 5 repetitions after one warm-up: blocking time, completion time, step time before/during/
after, and peak pinned host memory. Then corrupt a copy of one data file (on a scratch copy only),
show that a checksum-based validator rejects it, restore from the intact copy, and show that the
first step's loss matches the value recorded at save within a stated tolerance.
*Evidence required:* environment manifest, a results table with median and spread, and the restore
test log.
