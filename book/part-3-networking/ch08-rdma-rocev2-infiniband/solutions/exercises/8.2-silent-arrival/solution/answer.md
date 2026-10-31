# 8.2 — Silent arrival (worked solution)

Relies on manuscript Section 8.2 ("Operations: one-sided versus two-sided").

## Why an RDMA WRITE produces no completion at the target

A WRITE is **one-sided**. The initiator names the remote address and rkey, and the target NIC
validates the rkey and DMAs the payload straight into the registered buffer. It does this **without
consuming a receive work request (RECV WQE)**. A completion queue entry (CQE) reports that a posted work
request finished; the target posted none for this transfer, so there is nothing to complete. The
target CPU and application are not involved. That is the point of the operation (no remote CPU cost),
and it is also why the target cannot tell that the data has arrived.

## Two ways the target can learn that the data has arrived

| Method | How it works | Cost |
|---|---|---|
| **1. Poll a flag or sequence word** | The initiator writes the data, then (in a second WRITE, or as the last bytes of the same WRITE) a flag or sequence number. The target spins on that memory location. | Burns a CPU core (or GPU thread) polling. Correctness relies on placement order: write the flag *after* the data, ideally as a separate WRITE on the same QP, because ordering of bytes inside one large WRITE is not something to depend on. |
| **2. Follow with a SEND, or use RDMA WRITE-with-immediate** | The SEND, or the 32-bit immediate value, consumes a RECV that the target posted and produces a target CQE (`IBV_WC_RECV_RDMA_WITH_IMM` for WRITE-with-imm). | The target must keep RECVs posted. If none is posted, the initiator gets **RNR NAKs** and retries, and fails if they are exhausted. The target also pays for one completion per message (CQ polling or an interrupt) and a little extra latency. |

NCCL's network transport uses small control messages and flags in registered memory to signal
readiness and completion, a combination of both patterns.

## Common mistakes

- "The target gets an `IBV_WC_RDMA_WRITE` completion": that status exists only on the *initiator's*
  send CQ.
- Naming "the ACK" as the notification: ACKs go to the initiator's NIC, not to the target application.
