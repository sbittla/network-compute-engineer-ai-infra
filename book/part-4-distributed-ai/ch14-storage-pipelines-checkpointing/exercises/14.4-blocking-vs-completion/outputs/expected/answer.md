# 14.4 — Blocking time versus completion latency: worked solution

**Definitions (Section 14.9).**

- **Blocking time:** the time the training loop is stalled per checkpoint: snapshotting GPU state into
  a host staging buffer plus save-plan coordination. For W-TRAIN asynchronous saves this is about
  0.66 s.
- **Completion latency L:** the time from snapshot start until the commit marker is durable, so the
  checkpoint can be restored. It includes the background persist to the PFS (about 18.9 s for W-TRAIN).

**Derivation of E[lost work] = τ/2 + L** (checkpoints every τ, L ≤ τ, failure time uniform). Let the
failure occur u seconds after the latest snapshot started, with u uniform on [0, τ). If u ≥ L, that
snapshot has committed and the work lost is u. If u < L, which happens with probability L/τ, it has
not committed. The restore falls back to the previous checkpoint, and the work lost is u + τ. So

```text
E[lost] = E[u] + τ · P(u < L) = τ/2 + τ · (L/τ) = τ/2 + L
```

**Why completion latency, not blocking time.** Lost work is training progress that must be
recomputed: everything after the newest *restorable* checkpoint. Restorability is reached at
completion, not when the training loop resumes. Blocking time is not lost on failure. Training was
paused, not discarded. It is a cost paid on *every* checkpoint, so it enters the **overhead** term
δ/τ, not the failure term. The worst case (RPO max) is τ + L, a failure just before the next commit.

**Common wrong answer.** "Asynchronous checkpointing reduces RPO." It reduces *overhead* (blocking
0.66 s instead of about 20 s). That makes a shorter τ affordable, and only the shorter τ reduces the
exposure.
