# 8.1 — Keys and access rights (worked solution)

Relies on manuscript Section 8.2 ("The verbs model": memory registration, operations) and Section 8.6
(completion statuses and the ERROR state).

## Definitions

- **`lkey` (local key):** returned by `ibv_reg_mr` and used by the **local** process. It goes in the
  scatter/gather entries (SGEs) of work requests posted on the local QP. It authorizes the *local*
  NIC to DMA from or into that registered buffer when it executes the WR (the source of a SEND or
  WRITE, the landing buffer of a RECV or READ response).
- **`rkey` (remote key):** also returned by `ibv_reg_mr`, but **handed to the peer** (out of band, or in
  a SEND). The peer puts it with a remote virtual address in its RDMA READ, WRITE or atomic WR. The
  *target* NIC accepts the access only if the rkey is valid, the address range lies inside the MR, and
  the MR's access flags allow the operation.

## The failing WRITE

The target MR was registered with `IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_READ`, without
**`IBV_ACCESS_REMOTE_WRITE`**.

1. **Where it is checked:** the **target (responder) NIC** checks rkey and access rights when the WRITE
   arrives. The check fails, so **nothing is written** to the buffer, and the responder returns a
   **NAK: remote access error**.
2. **Where it is reported:** at the **initiator**. Its send CQ gets a completion with status
   **`IBV_WC_REM_ACCESS_ERR`** (enum value 10). The target *application* sees nothing, because a WRITE
   has no completion at the target (8.2), and no error CQE appears there for this WR.
3. **Resulting QP state:** the initiator's QP moves to **ERROR (IBV_QPS_ERR)**. Every WR still
   outstanding or posted afterwards completes with **`IBV_WC_WR_FLUSH_ERR`**. The QP must be reset
   (→ RESET → INIT → RTR → RTS) or destroyed to be used again. Depending on the implementation the
   responder QP may also be moved to an error state.

## Common mistakes

- Saying the target application gets an error CQE: it does not, because WRITEs are one-sided.
- Confusing the cases: a *local* access error (bad lkey) gives `IBV_WC_LOC_PROT_ERR` at the initiator,
  without a round trip.
- Expecting the WRITE to be partly applied: the access check happens before data placement.
