# Lab 14 L2: checkpoint blocking vs completion time, save/restore throughput and restore test

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:49:58Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

Checkpointed state: **0.202 GB** (16.8 M params, FP32 weights + Adam) on the CPU; target /tmp on / (overlay; rw,relatime,lowerdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotte).

## Blocking vs completion (timed repetitions)

| Metric | Median | p95 | Min - max | n |
|---|---|---|---|---|
| save: blocking = completion (s) | 0.398 | 0.623 | 0.328 - 0.623 | 5 |
| async_save: blocking (s) | 0.003 | 0.003 | 0.002 - 0.003 | 5 |
| async_save: completion (s) | 0.603 | 0.749 | 0.586 - 0.749 | 5 |
| async_save: step time before (ms) | 159.98 | 175.89 | 145.23 - 175.89 | 5 |
| async_save: step time during persist (ms) | 203.41 | 226.76 | 185.52 - 226.76 | 5 |
| async_save: step time after (ms) | 164.86 | 172.20 | 152.17 - 172.20 | 5 |
| async_save: staged host bytes (MB) | 202 | 202 | 202 - 202 | 5 |
| async_save: of which pinned (MB) | 0 | 0 | 0 - 0 | 5 |
| async_save: still aliasing live state (MB) | 202 | 202 | 202 - 202 | 5 |
| cached pinned: blocking (s) | n/a | n/a | n/a | 0 |
| cached pinned: completion (s) | n/a | n/a | n/a | 0 |
| cached pinned: step time during persist (ms) | n/a | n/a | n/a | 0 |
| cached pinned: pinned host bytes (MB) | n/a | n/a | n/a | 0 |
| host snapshot copy (s) | 0.011 | 0.011 | 0.010 - 0.011 | 5 |
| dcp.load after page-cache eviction (s) | 0.178 | 0.198 | 0.160 - 0.198 | 5 |

| Throughput | GB/s |
|---|---|
| host copy | 19.13 |
| save (write + fsync) | 0.51 |
| restore (dcp.load) | 1.13 |

**Consistency:** 76 of 128 tensors in an async checkpoint differ from the state at the call (51 data tensors, 25 scalars, e.g. `optim.state.6.weight.exp_avg_sq, optim.state.6.bias.step`; 3 training steps ran during the persist).

**Staging by reference:** 202 MB of the staged state still shares storage with the live tensors. For host-resident state DCP's default async_save does not copy, so optimizer steps taken during the persist can land in the checkpoint (a torn checkpoint); the consistency line shows whether they did. Snapshot explicitly before async_save when the state lives in host memory.

Interference: steps were **+27 %** slower while the persist ran (the lab assumes +3 %, `interference_frac`).

## Lab Part A model with this host's measured rates (`async_pfs`, solutions/lab/storage_lab.py)

| Quantity | Predicted | Measured |
|---|---|---|
| sync save blocking (s) | 0.398 | 0.398 |
| async blocking = snapshot (s) | 0.011 | 0.003 |
| async completion = snapshot + persist (s) | 0.408 | 0.603 |

Blocking above the predicted snapshot time is DCP's planning, allocation of staging buffers and metadata work: the lab's `snapshot_fixed_s`.

## Restore test

```text
recorded at save (sync_0): eval loss 0.9978762269020081; first-step loss 0.9978762269020081; tolerance rel 1e-06 (FP32, same kernels and batch), stated before running
wrote manifest.json (2 files) + COMMIT
validator on intact checkpoint: valid
corrupted 4 KiB in the middle of the scratch copy corrupt_copy/__0_0.distcp (original untouched)
validator on corrupted copy: ['CHECKSUM_MISMATCH'] -> rejected
dcp.load accepted the corrupted copy without error: 1 tensor(s) silently differ from the intact copy (state.8.weight.exp_avg); eval loss 0.9978762269020081 - unchanged, because the damage is in optimizer state and only surfaces steps later
restored from the intact copy into a fresh model (seed 123): eval loss 0.9978762269020081 (rel diff 0.0e+00)
first step after restore: loss 0.9978762269020081 vs recorded 0.9978762269020081 (rel diff 0.0e+00) -> PASS
```

## What to conclude

- async_save moves the write off the critical path; what remains on it is the snapshot (bounded by the D2H link) plus fixed DCP overhead. Size `snapshot_fixed_s` from the gap above, not from a guess.
- The persist is not free: steps during it run slower (CPU/PCIe/page-cache contention). That is the lab's interference term, and here it is measured.
- DCP stores no data checksums. Only the manifest validator caught the corrupted copy: verify before you load, and pick the latest *valid* checkpoint, not the `latest` pointer.

_CPU fallback: no GPU was used; the snapshot is a host-memory copy. D2H/PCIe invariants were skipped._

- State = model.state_dict() + Adam state via torch.distributed.checkpoint.state_dict.get_state_dict (FP32: 4 B weight + 8 B Adam m, v = 12 B/param; the lab's 14 B/param adds a BF16 copy).
- One warm-up then 5 timed repetitions per API; the warm-up row is kept in the table and excluded from the summary. dcp.save uses FileSystemWriter(sync_files=True): completion includes fsync.
- async_save: blocking = call -> return (the staging copy), completion = call -> future resolved. Training steps run back-to-back while the future is pending ('during').
- Peak host staging memory = the bytes of the state dict DCP's stager returned (FileSystemWriter.stage is wrapped to inspect it), split into pinned (page-locked) and pageable, plus the bytes that still alias the live tensors (staged by reference). Process RSS is not used: under WSL2 pinned pages need not appear in it.
- async_save+cached_pinned = FileSystemWriter(cache_staged_state_dict=True), one writer reused for the whole series: DCP stages into pinned host buffers it keeps between saves (memory for speed); the default stages into fresh pageable copies. Finding: in torch 2.5.1 the constructor argument is silently dropped (FileSystemWriter.__init__ does not call BlockingAsyncStager.__init__); the experiment sets the stager attributes directly when it detects this.
- Consistency test: the state is cloned at the async_save call, training continues during the persist, then the checkpoint is loaded and compared tensor by tensor with the clone.
- Restore read: files fsync'd, then evicted with posix_fadvise(DONTNEED); WSL2's virtual disk may still be cached by the Windows host, so read GB/s is an upper bound for the physical drive. Target: /tmp on / (overlay; rw,relatime,lowerdir=/var/lib/desktop-containerd/daemon/io.containerd.snapshotte).
- Lab model source: solutions/lab/storage_lab.py.
- Not runnable here: L2 fio NVMe acceptance (randread 4k QD32, seqwrite 1M QD8, >= 5 runs) (fio on PATH: False; NVMe block devices visible: none (Docker Desktop/WSL2 exposes only a virtual disk)); L3 shared-PFS checkpoint (aggregate write, commit latency, restore read, time to resume) (single host, no parallel file system).
- CPU fallback: the model lives in host memory, so 'snapshot' is a host-to-host copy, not PCIe D2H.
