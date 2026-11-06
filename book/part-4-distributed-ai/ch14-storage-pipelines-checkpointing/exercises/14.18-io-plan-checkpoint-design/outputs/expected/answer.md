# 14.18 — Deliverable: I/O benchmark plan and checkpoint/recovery design: worked solution

A model outline of a full-marks document. Lab checks A6 and C1–C3 must pass, and the planner and
validator outputs are attached.

**1. I/O benchmark plan (ORION)** `[VENDOR-SPEC, 2026-10]` for tool flags:

| Target | Tool and parameters | Warm-up / reps | Report |
|---|---|---|---|
| Local NVMe (per node, 8 × U.2) | `fio --ioengine=io_uring --direct=1 --rw=randread --bs=4k --iodepth=1,32,128 --numjobs=8 --time_based --runtime=120`; and `--rw=write --bs=1M --iodepth=32` | 1 warm-up (preconditioned drive), ≥ 5 reps | IOPS, GB/s, p50/p99/p99.9 latency |
| PFS bandwidth | IOR file-per-process, 256 ranks, `-t 16m -b 4g -F -e` (fsync), write then read | 1 + ≥ 5 | GB/s aggregate, per-rank spread |
| PFS metadata | `mdtest -n 10000 -F -u` from 32 nodes (create/stat/open/remove) | 1 + ≥ 5 | ops/s per op, p99 |
| Read under write | fio/IOR reads at loader rate while a 980 GB checkpoint write runs | ≥ 5 bursts | read p99/p99.9 during vs outside the burst |

Manifest fields: hosts, kernel, PFS client/server versions, stripe settings, fio/IOR/mdtest versions,
date, concurrent tenants.

**2. Checkpoint/recovery design (W-TRAIN).** Asynchronous PFS checkpoints. The interval comes from the
planner: Young floored at completion latency and rounded up to whole steps, giving a **37-step** interval
(643.8 s) at M = 48 h (A6: 55.6 GPU-h/day `[MODELED]`). Staging memory is ≈ 3.8 GB pinned per GPU
(30.6 GB per node, × 2 if double-buffered). Commit protocol as in 14.5. Validation ladder from Table 14.5.
Retention: 3 validated checkpoints + 1 in flight. Archive one checkpoint every 6 h to the object store.

**3. RPO/RTO.** RPO max = τ + L ≈ 662 s. E[time-to-resume] ≈ 904 s = detect 300 + relaunch 330 +
validate 20 + warm-up 150 + load 8.2 (+ replace 240 for hard failures). Show the sensitivity to M (14.10)
and to detection time.

**4. Restore test.** Copy the latest validated checkpoint to scratch and corrupt one shard. The validator
must reject it (CHECKSUM). Restore the intact copy and compare the first-step loss with the recorded
value within a stated tolerance. Separately, show that a missing `COMMIT` is rejected, as in the lab store,
where `step_001800` is selected over the `step_002700` pointer.

**5. Modeled vs measured.** All planner values are `[MODELED]`. The lab trace and store results are
`[SIMULATED]`. Benchmarks become `[MEASURED]` only when run on ORION.
