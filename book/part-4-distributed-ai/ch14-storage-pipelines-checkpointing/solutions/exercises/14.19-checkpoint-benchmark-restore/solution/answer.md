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

## Hardware run

`python scripts/hw_labs.py run ch14 --device gpu` runs this exercise end to end
(`lab/l2/experiment.py`). In full mode it uses an MLP with ≥ 1 GB of FP32 weights and Adam state on the
GPU. `dcp.save`, `dcp.async_save` and `async_save` with pinned cached staging each get one warm-up and
≥ 5 timed repetitions. The run reports median, p95 and min–max for blocking time, completion time,
step time before, during and after the persist, and the host bytes DCP staged (pinned and pageable). It
then performs the restore test above: SHA-256 manifest + COMMIT, a 4 KiB overwrite in a *scratch copy*,
rejection by the lab's `validate_checkpoint` (`CHECKSUM_MISMATCH`), restore from the intact copy, and a
first-step loss compared with the value recorded at save (tolerance stated first: relative 1e-6, FP32,
same kernels and batch). The bundle in `lab/l2/results/gpu-*/` is the model answer's evidence: the
environment manifest is `environment.json`, the results table is `report.md`, and the restore test log is
the fenced block in `report.md` (also under `restore_test.log` in `results.json`).

What the run shows beyond the expected shape above:

- `dcp.load` has no data checksums. Depending on where the 4 KiB lands, it either refuses the copy (the
  zip/pickle framing was hit) or loads it silently with a few tensors changed, often optimizer state, so
  the loss looks unchanged. Only the manifest validator catches both cases.
- In PyTorch 2.5.1, `FileSystemWriter(cache_staged_state_dict=True)` silently drops the flag. The
  experiment detects this and sets the stager attribute itself; a submission that "saw no pinned memory"
  may have hit it.
- With non-fused Adam, the `step` counters are CPU scalars. DCP stages host tensors by reference, so an
  async checkpoint can record a later step count than its moments. The consistency check reports it.

**Fallback.** Without a GPU (`--device cpu`, or automatically when none is visible), the same benchmark
and restore test run with the state in host memory. The pinned series and the D2H/PCIe invariants are
skipped, and the report says so. There the consistency check shows the full torn-checkpoint hazard: host
state is staged by reference, so steps taken during the persist land in the checkpoint.
