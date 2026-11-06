# Lab 14 L2: checkpoint blocking vs completion time, save/restore throughput and restore test

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-06T04:41:00Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-rxe+-x86_64-with-glibc2.39 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

> **Run conditions.** Swap was disabled inside the 7.8 GiB WSL2 VM for this run (`swapoff -a`, restored afterwards), so the timings cannot include paging. The previous bundle (2026-11-01) failed its invariants because the host paged (0.01 GB/s D2H, 2,247 s `dcp.load`); this run replaces it.

Checkpointed state: **1.133 GB** (94.4 M params, FP32 weights + Adam) on the GPU; target /tmp on / (ext4; rw,relatime,discard,errors=remount-ro,data=ordered).

## Blocking vs completion (timed repetitions)

| Metric | Median | p95 | Min - max | n |
|---|---|---|---|---|
| save: blocking = completion (s) | 1.048 | 1.462 | 0.821 - 1.462 | 5 |
| async_save: blocking (s) | 0.569 | 0.741 | 0.516 - 0.741 | 5 |
| async_save: completion (s) | 1.817 | 1.882 | 1.416 - 1.882 | 5 |
| async_save: step time before (ms) | 186.97 | 197.63 | 183.89 - 197.63 | 5 |
| async_save: step time during persist (ms) | 182.90 | 198.05 | 180.13 - 198.05 | 5 |
| async_save: step time after (ms) | 186.63 | 193.39 | 182.19 - 193.39 | 5 |
| async_save: staged host bytes (MB) | 1133 | 1133 | 1133 - 1133 | 5 |
| async_save: of which pinned (MB) | 0 | 0 | 0 - 0 | 5 |
| async_save: still aliasing live state (MB) | 0 | 0 | 0 - 0 | 5 |
| cached pinned: blocking (s) | 0.099 | 0.104 | 0.096 - 0.104 | 5 |
| cached pinned: completion (s) | 1.003 | 1.019 | 0.993 - 1.019 | 5 |
| cached pinned: step time during persist (ms) | 182.49 | 184.07 | 177.57 - 184.07 | 5 |
| cached pinned: pinned host bytes (MB) | 1133 | 1133 | 1133 - 1133 | 5 |
| D2H pinned snapshot (s) | 0.087 | 0.087 | 0.086 - 0.087 | 5 |
| dcp.load after page-cache eviction (s) | 1.107 | 1.181 | 0.835 - 1.181 | 5 |

| Throughput | GB/s |
|---|---|
| D2H snapshot (pinned) | 13.08 |
| save (write + fsync) | 1.08 |
| restore (dcp.load) | 1.02 |

**Consistency:** 20 of 80 tensors in an async checkpoint differ from the state at the call (0 data tensors, 20 scalars, e.g. `optim.state.0.weight.step, optim.state.0.bias.step`; 5 training steps ran during this test's own async persist, 1.5 s; it is a separate save, not one of the timed repetitions).

The weights and Adam moments were snapshotted, but Adam's `step` counters are CPU scalar tensors (non-fused, non-capturable Adam) and DCP stages host tensors by reference: the checkpoint records a later step count than its moments, which skews bias correction on resume. Copy them (or use `fused=True`/`capturable=True`, which keeps `step` on the GPU) before relying on async_save.

Interference: steps were **-2 %** slower while the persist ran; -0 % with cached pinned staging (the lab assumes +3 %, `interference_frac`).
PCIe ceiling for the snapshot: 15.8 GB/s `[MODELED]` from the maximum-capability link (pcie.link.*.max; the negotiated link can be lower).

## Lab Part A model with this host's measured rates (`async_pfs`, solutions/lab/storage_lab.py)

| Quantity | Predicted | Measured |
|---|---|---|
| sync save blocking (s) | 1.048 | 1.048 |
| async blocking = snapshot (s) | 0.087 | 0.569 |
| async completion = snapshot + persist (s) | 1.134 | 1.817 |

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

- async_save moves the write off the critical path; what remains on it is the snapshot (bounded by the D2H link) plus fixed DCP overhead. Size `snapshot_fixed_s` from the gap above, not from a guess.
- The persist is not free: steps during it run slower (CPU/PCIe/page-cache contention). That is the lab's interference term, and here it is measured.
- DCP stores no data checksums. Only the manifest validator caught the corrupted copy: verify before you load, and pick the latest *valid* checkpoint, not the `latest` pointer.

_Laptop RTX 4060 (PCIe Gen4 x8) writing to a Docker Desktop/WSL2 virtual disk, not an HX8 node with 8 x U.2 NVMe and a PFS. Compare the shape (blocking << completion; interference > 0) with Chapter 14, not the absolute GB/s._

- State = model.state_dict() + Adam state via torch.distributed.checkpoint.state_dict.get_state_dict (FP32: 4 B weight + 8 B Adam m, v = 12 B/param; the lab's 14 B/param adds a BF16 copy).
- One warm-up then 5 timed repetitions per API; the warm-up row is kept in the table and excluded from the summary. dcp.save uses FileSystemWriter(sync_files=True): completion includes fsync.
- async_save: blocking = call -> return (the staging copy), completion = call -> future resolved. Training steps run back-to-back while the future is pending ('during').
- Peak host staging memory = the bytes of the state dict DCP's stager returned (FileSystemWriter.stage is wrapped to inspect it), split into pinned (page-locked) and pageable, plus the bytes that still alias the live tensors (staged by reference). Process RSS is not used: under WSL2 pinned pages need not appear in it.
- async_save+cached_pinned = FileSystemWriter(cache_staged_state_dict=True), one writer reused for the whole series: DCP stages into pinned host buffers it keeps between saves (memory for speed); the default stages into fresh pageable copies. Finding: in torch 2.5.1 the constructor argument is silently dropped (FileSystemWriter.__init__ does not call BlockingAsyncStager.__init__); the experiment sets the stager attributes directly when it detects this.
- Consistency test: the state is cloned at the async_save call, training continues during the persist, then the checkpoint is loaded and compared tensor by tensor with the clone.
- Restore read: files fsync'd, then evicted with posix_fadvise(DONTNEED); WSL2's virtual disk may still be cached by the Windows host, so read GB/s is an upper bound for the physical drive. Target: /tmp on / (ext4; rw,relatime,discard,errors=remount-ro,data=ordered).
- Lab model source: solutions/lab/storage_lab.py.
- Not runnable here: L2 fio NVMe acceptance (randread 4k QD32, seqwrite 1M QD8, >= 5 runs) (fio on PATH: True; NVMe block devices visible: none (Docker Desktop/WSL2 exposes only a virtual disk)); L3 shared-PFS checkpoint (aggregate write, commit latency, restore read, time to resume) (single host, no parallel file system).
