# K2 — Row-remapper states: worked solution

**Relies on:** Section 19.3 ("ECC, row remapping, and page retirement", Table 19.3) and the lab's
`gpu_actions()`. Behaviour is `[VENDOR-SPEC, 2026-10]`: check NVIDIA's current *GPU Memory Error
Management* document for your GPU generation and driver branch.

## Background

On A100- and H100-class GPUs a faulty HBM row is replaced by a spare row in the same bank. The remap is
*recorded* as soon as the error is seen, but only takes effect after a GPU reset. Until then the state
is **pending**. If the bank has no spare row left, the remap **fails**.

## Answers

| State | Action | Mechanism (one line) |
|---|---|---|
| (a) Pending = Yes | Drain the node when no job needs it (or exclude it at the next restart), capture `nvidia-smi -q -d ROW_REMAPPER,ECC`, reset the GPU, verify Pending = No and no failure, run `dcgmi diag`, return to service | The spare row is reserved but not active until reset, so the bad row is still in use |
| (b) Remapping Failure Occurred = Yes | Quarantine the GPU (node) and open an RMA | No spare row remains in that bank, so the memory cannot be repaired and further errors will recur |
| (c) Correctable = 1, Pending = No, Failure = No | Healthy: monitor only; ticket only if the count starts rising quickly | A remap was applied earlier and is active; the GPU is repaired and normal |

## Why (c) matters

This is the lab's planted healthy distractor (orionxl-n046 GPU6, `monitor`). Quarantining it wastes a
good GPU and, in a pool of 55 spares already 47 deep in use, removes capacity for no gain.

## Common wrong answers

- Treating (c) as a fault and draining it (the key's named common mistake).
- For (a), resetting immediately while a job is running on the GPU, or returning it without verifying
  that Pending cleared.
- For (b), "reset and retry": a reset cannot create spare rows.
- Resetting before capturing evidence: a reset clears volatile ECC counters (Section 19.6, step 4).
