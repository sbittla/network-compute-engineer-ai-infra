# Lab 14 (Progressive Lab 6) — Storage and Checkpoint Engineering

## 1. Goal and the real-world task it mirrors

Halcyon AI's Training Infra team must answer three questions before W-TRAIN (70B, 980 GB
checkpoints) goes to production on ORION-256:

1. **How often, and how, should we checkpoint?** You build the *checkpoint planner* a training
   infrastructure engineer uses to defend a checkpoint policy: checkpoint size, blocking and
   completion time for synchronous and asynchronous strategies, overhead, Young/Daly interval,
   expected lost GPU-hours per day, recovery point objective (RPO), and time-to-resume.
2. **Is the input pipeline metadata-bound or bandwidth-bound, and where is the tail?** You build the
   *I/O trace analyzer* a storage engineer runs on a data-loader trace and an fio acceptance run:
   phase segmentation, latency percentiles, interference windows, a slow storage target, and
   NVMe acceptance outliers.
3. **Which checkpoint is safe to restore?** You build the *checkpoint validator* that a restart
   controller runs before it loads anything: it rejects incomplete and corrupt checkpoints and selects
   the latest valid one, instead of trusting a `latest` pointer.

These are the tools behind the chapter deliverable: **an I/O benchmark plan and a
checkpoint/recovery design** (manuscript Section 14.12 and Exercise 14.18).

## 2. Tier and realism boundary

**Tier L1** (laptop, Python only, < 10 s). Part A is `[MODELED]`: it is exactly as good as its
inputs and its assumptions (listed in Section 5). Parts B and C analyse `[SIMULATED]` data produced by
a seeded generator (instructor copy only, `tools/generate_data.py`); the trace is shaped like a real per-operation loader trace but no storage
system produced it. Nothing here measures a disk, a file system, or a network. Section 8 gives the
L2/L3 commands that turn the model into evidence.

## 3. Setup

```bash
cd book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                           # starter: 0/15, every check TODO
```

Python ≥ 3.10. You edit only `starter/storage_lab.py`.

## 4. Background you need

| Task | Manuscript section |
|---|---|
| Part A | 14.8 (checkpoint anatomy), 14.9 (sync vs async, DCP, Megatron-LM), 14.10 (consistency and commit), 14.11 (RPO/RTO economics, Young/Daly), 14.12 (worked example) |
| Part B | 14.2 (NVMe queues, IOPS vs bandwidth), 14.4–14.5 (parallel file systems; metadata vs bandwidth), 14.6 (fio, tail latency), 14.7 (data loaders) |
| Part C | 14.10 (commit protocol, restore validation), 14.14 (troubleshooting scenario) |

## 5. Tasks

### Part A — Checkpoint planner (inputs: `data/orion_ckpt_inputs.yaml`)

Let *S* = params × bytes/param, *e* = `pfs_efficiency`, *i* = `interference_frac`,
*k* = `pfs_every_k`, *c* = `commit_overhead_s`. Intermediate times (seconds):

| Symbol | Formula | Meaning |
|---|---|---|
| T_pfs_w | S / (pfs_write × 1e9 × e) | write full checkpoint to the parallel file system (PFS) |
| T_pfs_r | S / (pfs_read × 1e9 × e) | read full checkpoint from the PFS |
| T_snap | (S / gpus) / (d2h × 1e9) + snapshot_fixed | device-to-host snapshot (all GPUs in parallel) |
| T_loc_w, T_loc_r | (S / nodes) / (nvme_w or nvme_r × 1e9) | per-node local NVMe write/read (all nodes in parallel) |

| Strategy | blocking | delta (effective cost) | L_soft | L_hard | load soft / hard | PFS every |
|---|---|---|---|---|---|---|
| `sync_pfs` | T_pfs_w + c | blocking | blocking | blocking | T_pfs_r / T_pfs_r | 1 |
| `async_pfs` | T_snap | T_snap + i(T_pfs_w + c) | T_snap + T_pfs_w + c | = L_soft | T_pfs_r / T_pfs_r | 1 |
| `sync_local_drain` | T_loc_w + c | blocking + i·T_pfs_w | blocking | blocking + T_pfs_w + c | T_loc_r / T_pfs_r | 1 |
| `async_two_level` | T_snap | T_snap + i(T_loc_w + T_pfs_w/k) | T_snap + T_loc_w + c | L_soft + T_pfs_w + c | T_loc_r / T_pfs_r | k |

A *soft* failure (process crash, collective timeout) leaves every node's local NVMe intact; a *hard*
failure (fraction `hard_failure_frac`) removes a node, so recovery must come from the PFS copy.

1. **A1–A3.** Implement `transfer_time_s`, `young_interval_s`, `daly_interval_s`,
   `choose_interval_s`. *Accept:* 980 GB at 80 GB/s × 0.75 → 16.33 s; Young(17.83 s, 48 h) ≈ 2,483 s.
2. **A4.** Implement `strategy_timings` from the table. *Accept:* `async_pfs` blocks for 0.653 s
   but completes in 18.49 s.
3. **A5.** Implement `plan_strategy` (formulas in its docstring). *Accept:* `sync_pfs` at a fixed
   1,800 s interval costs 0.99 % overhead and 125.7 GPU-hours/day.
4. **A6.** Implement `compare_strategies`. *Accept:* ranking `async_pfs` < `async_two_level` <
   `sync_local_drain` < `sync_pfs` by lost GPU-hours/day. Then **explain in your memo** why the
   two-level strategy, which has the lowest overhead, does *not* win with these inputs, and what
   input change would make it win (try `hard_failure_frac: 0.1` and `pfs_write_GBps: 20`).

Model assumptions you must restate in your memo: failures are exponential with the given job mean
time between failures (MTBF); at most one checkpoint is in flight; a checkpoint is usable only after
its commit marker is durable; restore always reads the full checkpoint; interference is a constant
fractional slowdown while background I/O runs.

### Part B — I/O trace analyzer (inputs: `data/io_trace.csv`, `data/fio_nvme_acceptance.json`)

`io_trace.csv` has one row per operation issued by 8 data-loader workers on one HX8 node:
`t_s` (start time, s), `worker`, `op` (`open`/`read`/`close`), `target` (storage target the
operation hit), `bytes`, `lat_us` (completion latency, µs).

5. **B1.** `latency_percentiles`: p50/p99/p99.9 per op. *Accept:* matches `numpy.percentile`.
6. **B2.** `window_profile` + `classify_window` with 1 s windows. *Accept:* windows 0–5
   `metadata`, 6 `idle`, 7–18 `bandwidth`.
7. **B3.** `phases`: merge runs of equal class. *Accept:* three phases.
8. **B4.** `degraded_windows`: bandwidth windows whose p99 read latency exceeds 2× the median.
   *Accept:* exactly four windows. In your memo, name the most likely cause and the evidence you
   would collect next to prove it.
9. **B5.** `slow_targets`. *Accept:* one target.
10. **B6.** `parse_fio` and `fio_outliers` on the 8-drive acceptance run. *Accept:* Little's-law
    queue depth (IOPS × mean latency) matches `iodepth` within 5 %; exactly two (device, reason)
    outliers.

### Part C — Checkpoint validator (input: `data/checkpoints/`)

Each `step_NNNNNN/` holds `shard_RR.bin` files, a `manifest.json` (format `halcyon-ckpt-v1`: a
teaching format, **not** the PyTorch DCP on-disk format), and a `COMMIT` marker whose content is the
SHA-256 of the exact manifest bytes. The commit protocol is: write shards → fsync → write manifest →
fsync → write `COMMIT` via temp-file + rename → fsync the directory. `latest` is a convenience
pointer written by the trainer.

11. **C1.** `validate_checkpoint` and `audit_store`. *Accept:* every checkpoint gets the correct
    defect codes (the checker knows them; your memo must explain each one's likely cause).
12. **C2.** `select_latest_valid`. *Accept:* a step other than the one `latest` points to.
13. **C3.** Your validator must also catch defects not in the dataset (the checker builds two on the
    fly).

## 6. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # reference (instructors)
```

One line per check (`PASS`/`FAIL`/`TODO` + reason); exit code 0 only when all 15 pass.

## 7. Deliverable and grading rubric (100 points)

Deliverable: `storage_lab.py` passing all checks, plus a **two-page design memo** containing
(a) the strategy comparison table from A6 with your recommendation and the assumptions restated,
(b) the I/O findings from Part B as a diagnosis (symptom → evidence → cause → next test),
(c) a restore runbook step that uses your validator, and (d) an **I/O benchmark plan** for the L2/L3
extension below (what to run, warm-up, repetitions, what to record).

| Item | Points |
|---|---|
| A1–A3 (8), A4 (8), A5 (8), A6 (6) | 30 |
| B1 (4), B2 (6), B3 (3), B4 (4), B5 (4), B6 (6) | 27 |
| C1 (8), C2 (4), C3 (6) | 18 |
| Memo (a) recommendation with assumptions and the two-level sensitivity explained | 8 |
| Memo (b) Part B diagnosis using the diagnostic loop | 6 |
| Memo (c) restore runbook step; (d) benchmark plan with warm-up, ≥ 5 repetitions, percentiles, manifest | 11 |
| **Total** | **100** |

## 8. Extensions (L2/L3, hardware-backed)

> **Safety:** fio write tests against a raw device destroy its contents. Run write tests only
> against a scratch *file* on a dedicated lab host, or a device you own and have been told you may
> wipe. Never run these on shared training nodes or the shared PFS outside an agreed window.

**L2 — local NVMe acceptance (one Linux host).** Reproduce `fio_nvme_acceptance.json` on real drives:

```bash
nvme list                                             # model, firmware, namespace sizes (nvme-cli)
sudo nvme smart-log /dev/nvme0                        # temperature, media errors, percentage used
sudo lspci -vv -s <BDF> | grep -E 'LnkCap|LnkSta'     # negotiated PCIe speed/width vs capability
ls /sys/block/nvme0n1/mq/ | wc -l                     # blk-mq hardware queues exposed by the driver
# read-only random-read test on the raw device:
sudo fio --name=randread-4k-qd32 --filename=/dev/nvme0n1 --readonly --rw=randread --bs=4k \
    --iodepth=32 --ioengine=libaio --direct=1 --ramp_time=10 --runtime=60 --time_based \
    --output-format=json --output=nvme0-randread.json
# sequential write to a scratch FILE on a mounted lab file system:
fio --name=seqwrite-1m-qd8 --filename=/mnt/scratch/fio.dat --size=64G --rw=write --bs=1M \
    --iodepth=8 --ioengine=libaio --direct=1 --ramp_time=10 --runtime=60 --time_based \
    --output-format=json --output=nvme0-seqwrite.json
iostat -xm 1                                          # in a second terminal: r/s, rMB/s, r_await, aqu-sz
```

Run each job ≥ 5 times; report median and p95 of `bw_bytes` and of the p99.9 completion latency,
with min/max spread. Feed the JSON files to your `parse_fio` and `fio_outliers` unchanged.

**L2 — checkpoint blocking vs completion time (one GPU host, PyTorch 2.x).** Time a synchronous
`torch.distributed.checkpoint.save` against `torch.distributed.checkpoint.async_save` (which returns a
future) on a model that fits one GPU, recording blocking time (until the call returns), completion
time (until the future resolves), and step time before/during/after. These APIs are
`[VENDOR-SPEC, 2026-10]`: confirm their names and arguments in the documentation for your PyTorch
version; `async_save` requires an initialised process group in some versions.

**L3 — shared storage (2+ GPU nodes, maintenance window).** On a Lustre-class PFS, record the
striping of your checkpoint directory (`lfs getstripe <dir>`; set a stripe count and size for a new
directory with `lfs setstripe -c <count> -S <size> <dir>`), then run the checkpoint from all ranks and
measure aggregate write rate (bytes / wall time from first open to commit), commit latency, and
restore read rate; then time a full restart (kill a rank in the lab job, measure failure → first
completed step). Record every field listed under `extensions` in `manifest.yaml`, including whether
other tenants were active, since shared-storage results are meaningless without it.

## 9. Intentionally flawed inputs

The datasets contain planted anomalies that teach diagnosis. They are documented for instructors
only in `../solutions/lab/README.md`.
