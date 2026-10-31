# 11.6 — Why the first rank to time out is usually not the faulty one

**Explanation** (Section 11.11). A collective completes only when every rank in the communicator
joins it. If one rank dies, hangs, or is stuck in a different operation, every *healthy* rank
enters the collective and blocks. Each rank's NCCL watchdog runs the same timeout (≈ 10 minutes by
default), so they all expire at roughly the same moment; whichever watchdog thread happens to fire
first logs first. That rank is a **victim**, not the cause. The faulty rank may leave no log at all
(process killed by a GPU Xid or OOM), may be stuck elsewhere (its last completed collective has a
*lower* sequence number than everyone else's), or may have entered a different collective (an op or
size mismatch after a code-path divergence).

**Two artifacts that identify the faulty rank.**

1. **NCCL flight-recorder dumps from every rank** (PyTorch's `TORCH_NCCL_TRACE_BUFFER_SIZE`, dumped on
   timeout): compare the last `SeqNum` and op type per rank; the rank whose sequence number is lowest,
   or whose op differs, is the culprit.
2. **`py-spy dump` stacks of all ranks**, taken before the restart: the healthy ranks sit in the
   collective; the faulty one is somewhere else (data loader, checkpoint I/O, a deadlock) — or absent.

Also accepted: host kernel logs (`dmesg` Xid events with timestamps), scheduler/node health events,
and the launcher's exit summary naming the first rank that *exited* (not the first that timed out).

**Operational rule** (runbook, Table 11.7): collect flight-recorder dumps and stacks from all ranks
*before* restarting, or the evidence is lost.

**Common wrong answer.** Draining the node of the first rank that logged the timeout.
