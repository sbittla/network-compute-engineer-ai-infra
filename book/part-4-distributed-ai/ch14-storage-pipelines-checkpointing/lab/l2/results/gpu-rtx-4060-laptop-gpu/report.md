# Lab 14 L2: checkpoint blocking vs completion time, save/restore throughput and restore test

> **Not a valid reference run (pending rerun).** This bundle FAILED its invariants and is kept only as a record
> of a failed measurement; do not read timings or shape from it. The 0.01 GB/s "D2H snapshot" (on a 15.8 GB/s
> link) and the 2,247 s `dcp.load` (0.00 GB/s) are physically implausible. The likely cause is memory pressure on
> the 7.8 GiB WSL2 VM: about 1.1 GB of pinned host buffers plus several host copies of a 1.13 GB state forced the
> host to page. That is a property of the test host, not of DCP. `experiment.py` now refuses such runs (host-memory
> headroom check) and fails them (D2H below 1 GB/s, load more than 20 x save, swap-out during the run). This
> report was re-rendered on 2026-11-01 from the unchanged `results.json` measurements with those checks; the
> invariant list below is the re-evaluated one (the original is kept in `results.json` as `invariants_original`).
> The restore-test and consistency lines are tensor comparisons and do not depend on the timings. The consistency
> line's 382 steps (x ~182 ms = ~70 s) belong to that test's own async save, which this paging host stretched far
> beyond the ~8 s timed ones; its duration was not recorded then (the experiment now records it). For the expected
> shape, read `../cpu-fallback/report.md` until a rerun on a host with at least 4 x the state in free RAM
> replaces this bundle.

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T01:14:14Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** FAILED: implausible D2H snapshot rate 0.01 GB/s < 1 GB/s: the host is paging (pinned allocation under memory pressure?); this run is not valid evidence - rerun on a host with more RAM; implausible restore: dcp.load 2246.8 s > 20 x save 6.5 s; the host is paging; this run is not valid evidence

Checkpointed state: **1.133 GB** (94.4 M params, FP32 weights + Adam) on the GPU; target /tmp on / (overlay; rw,relatime,lowerdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotte).

## Blocking vs completion (timed repetitions)

| Metric | Median | p95 | Min - max | n |
|---|---|---|---|---|
| save: blocking = completion (s) | 6.456 | 7.266 | 5.915 - 7.266 | 5 |
| async_save: blocking (s) | 0.657 | 0.817 | 0.631 - 0.817 | 5 |
| async_save: completion (s) | 8.000 | 8.664 | 5.575 - 8.664 | 5 |
| async_save: step time before (ms) | 182.11 | 192.71 | 181.33 - 192.71 | 5 |
| async_save: step time during persist (ms) | 182.24 | 190.21 | 181.28 - 190.21 | 5 |
| async_save: step time after (ms) | 181.87 | 185.48 | 177.79 - 185.48 | 5 |
| async_save: staged host bytes (MB) | 1133 | 1133 | 1133 - 1133 | 5 |
| async_save: of which pinned (MB) | 0 | 0 | 0 - 0 | 5 |
| async_save: still aliasing live state (MB) | 0 | 0 | 0 - 0 | 5 |
| cached pinned: blocking (s) | 0.281 | 0.389 | 0.192 - 0.389 | 5 |
| cached pinned: completion (s) | 9.911 | 12.660 | 9.323 - 12.660 | 5 |
| cached pinned: step time during persist (ms) | 182.95 | 183.45 | 182.28 - 183.45 | 5 |
| cached pinned: pinned host bytes (MB) | 1133 | 1133 | 1133 - 1133 | 5 |
| D2H pinned snapshot (s) | 193.509 | 228.181 | 125.629 - 228.181 | 5 |
| dcp.load after page-cache eviction (s) | 2246.845 | 2301.337 | 2192.782 - 2301.337 | 5 |

| Throughput | GB/s |
|---|---|
| D2H snapshot (pinned) | 0.01 |
| save (write + fsync) | 0.18 |
| restore (dcp.load) | 0.00 |

**Consistency:** 20 of 80 tensors in an async checkpoint differ from the state at the call (0 data tensors, 20 scalars, e.g. `optim.state.0.weight.step, optim.state.0.bias.step`; 382 training steps ran during this test's own async persist; it is a separate save, not one of the timed repetitions).

The weights and Adam moments were snapshotted, but Adam's `step` counters are CPU scalar tensors (non-fused, non-capturable Adam) and DCP stages host tensors by reference: the checkpoint records a later step count than its moments, which skews bias correction on resume. Copy them (or use `fused=True`/`capturable=True`, which keeps `step` on the GPU) before relying on async_save.

Interference: steps were **+0 %** slower while the persist ran; +0 % with cached pinned staging (the lab assumes +3 %, `interference_frac`).
PCIe ceiling for the snapshot: 15.8 GB/s `[MODELED]` from the maximum-capability link (pcie.link.*.max; the negotiated link can be lower).

## Lab Part A model with this host's measured rates (`async_pfs`, solutions/lab/storage_lab.py)

| Quantity | Predicted | Measured |
|---|---|---|
| sync save blocking (s) | 6.456 | 6.456 |
| async blocking = snapshot (s) | 193.509 | 0.657 |
| async completion = snapshot + persist (s) | 199.966 | 8.000 |

Blocking above the predicted snapshot time is DCP's planning, allocation of staging buffers and metadata work: the lab's `snapshot_fixed_s`.

## Restore test

```text
recorded at save (sync_0): eval loss 0.9990174174308777; first-step loss 0.9990169405937195; tolerance rel 1e-06 (FP32, same kernels and batch), stated before running
wrote manifest.json (2 files) + COMMIT
validator on intact checkpoint: valid
corrupted 4 KiB in the middle of the scratch copy corrupt_copy/__0_0.distcp (original untouched)
validator on corrupted copy: ['CHECKSUM_MISMATCH'] -> rejected
dcp.load accepted the corrupted copy without error: 1 tensor(s) silently differ from the intact copy (state.4.weight.exp_avg); eval loss 0.9990174174308777 - unchanged, because the damage is in optimizer state and only surfaces steps later
restored from the intact copy into a fresh model (seed 123): eval loss 0.9990174174308777 (rel diff 0.0e+00)
first step after restore: loss 0.9990169405937195 vs recorded 0.9990169405937195 (rel diff 0.0e+00) -> PASS
```

## What to conclude

Nothing about timing. The invariants failed, so the throughput, blocking, completion, interference and model-comparison rows above describe this host's condition (for example paging), not DCP. Invariants that tripped:

- implausible D2H snapshot rate 0.01 GB/s < 1 GB/s: the host is paging (pinned allocation under memory pressure?); this run is not valid evidence - rerun on a host with more RAM
- implausible restore: dcp.load 2246.8 s > 20 x save 6.5 s; the host is paging; this run is not valid evidence

The restore test and the consistency comparison are tensor-by-tensor checks and do not depend on the timings. Rerun on a host with enough free memory before drawing any timing conclusion.

- State = model.state_dict() + Adam state via torch.distributed.checkpoint.state_dict.get_state_dict (FP32: 4 B weight + 8 B Adam m, v = 12 B/param; the lab's 14 B/param adds a BF16 copy).
- One warm-up then 5 timed repetitions per API; the warm-up row is kept in the table and excluded from the summary. dcp.save uses FileSystemWriter(sync_files=True): completion includes fsync.
- async_save: blocking = call -> return (the staging copy), completion = call -> future resolved. Training steps run back-to-back while the future is pending ('during').
- Peak host staging memory = the bytes of the state dict DCP's stager returned (FileSystemWriter.stage is wrapped to inspect it), split into pinned (page-locked) and pageable, plus the bytes that still alias the live tensors (staged by reference). Process RSS is not used: under WSL2 pinned pages need not appear in it.
- async_save+cached_pinned = FileSystemWriter(cache_staged_state_dict=True), one writer reused for the whole series: DCP stages into pinned host buffers it keeps between saves (memory for speed); the default stages into fresh pageable copies. Finding: in torch 2.5.1 the constructor argument is silently dropped (FileSystemWriter.__init__ does not call BlockingAsyncStager.__init__); the experiment sets the stager attributes directly when it detects this.
- Consistency test: the state is cloned at the async_save call, training continues during the persist, then the checkpoint is loaded and compared tensor by tensor with the clone.
- Restore read: files fsync'd, then evicted with posix_fadvise(DONTNEED); WSL2's virtual disk may still be cached by the Windows host, so read GB/s is an upper bound for the physical drive. Target: /tmp on / (overlay; rw,relatime,lowerdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotte).
- Lab model source: solutions/lab/storage_lab.py.
- Not runnable here: L2 fio NVMe acceptance (randread 4k QD32, seqwrite 1M QD8, >= 5 runs) (fio on PATH: False; NVMe block devices visible: none (Docker Desktop/WSL2 exposes only a virtual disk)); L3 shared-PFS checkpoint (aggregate write, commit latency, restore read, time to resume) (single host, no parallel file system).
