# 14.19 — Checkpoint benchmark and restore test: worked solution

This is an L2 exercise. The solution states the expected *shape* of correct results, because the values
depend on hardware. Reject any submission without repetitions or a manifest.

**Procedure.**

1. *Manifest:* GPU model and driver, CUDA, PyTorch version (DCP APIs differ between 2.x minors, so check
   `torch.distributed.checkpoint.async_save` in the installed docs `[VENDOR-SPEC, 2026-10]`), storage
   target (local NVMe or PFS mount), host memory, and the date.
2. *Model:* ≥ 1 GB of state, for example a 250 M-parameter model with Adam: 250e6 × 14 B ≈ 3.5 GB
   checkpointed state.
3. *Method:* one warm-up save, then ≥ 5 timed repetitions each of `dcp.save` and `dcp.async_save`.
   Measure blocking time (call → return), completion time (call → future done and files durable), step
   time for 20 steps before, during and after the persist, and peak pinned host memory (`torch.cuda.memory`
   host stats or `/proc/<pid>/status` VmLck/RSS deltas).

**Expected results** `[MEASURED]` on the learner's host:

| Metric | `save` | `async_save` |
|---|---|---|
| Blocking time | ≈ completion time | small fraction of `save` (the device-to-host copy) |
| Completion time | baseline | ≥ `save` (background persist, plus interference) |
| Step time during persist | — | measurably higher than before/after (interference) |
| Peak pinned host memory | ≈ 0 extra | ≈ state size (× 2 if double-buffered) |

Report median and spread (min–max or IQR) for each cell.

**Restore test log.**

1. Copy the checkpoint to a scratch directory. Corrupt one data file in the copy only (overwrite 4 KiB in
   the middle).
2. Run a checksum-based validator (manifest of SHA-256 per file): it must **reject** the corrupted copy and
   name the file.
3. Restore from the intact copy and run one fixed batch.
4. Compare the first-step loss with the value recorded at save. Pass if |Δ| / loss ≤ 1e-3 (BF16), or
   bitwise equal in FP32 with deterministic kernels. State the tolerance before running.

**Common failures.** Timing `async_save` only to its return, which reports blocking time as completion.
Corrupting the original checkpoint. No warm-up, so the first save includes allocator and plan setup.
