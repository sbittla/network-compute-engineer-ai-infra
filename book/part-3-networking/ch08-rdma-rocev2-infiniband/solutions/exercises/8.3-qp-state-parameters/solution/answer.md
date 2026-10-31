# 8.3 — Where the QP parameters live (worked solution)

Relies on manuscript Section 8.2 (QP state machine RESET → INIT → RTR → RTS) and Section 8.6 (ACK
timeout and retries).

## (a) Path MTU and destination GID / GID index: INIT → RTR

`ibv_modify_qp` to **RTR (ready to receive)** sets the receive-side and addressing attributes:

- `path_mtu`, the RDMA path MTU (IBV_MTU_1024 … IBV_MTU_4096);
- the **address vector**: destination GID (`ah_attr.grh.dgid`), source GID index
  (`ah_attr.grh.sgid_index`; on RoCE this selects v1 or v2 and the source IP), hop limit, traffic
  class, and for IB the destination LID and SL;
- `dest_qp_num`, `rq_psn` (expected receive PSN), `max_dest_rd_atomic`, `min_rnr_timer`.

## (b) ACK timeout and retry count: RTR → RTS

`ibv_modify_qp` to **RTS (ready to send)** sets the send-side reliability attributes:

- `timeout` (T_ack = 4.096 µs × 2^timeout),
- `retry_cnt` (transport retries, at most 7), `rnr_retry`,
- `sq_psn`, `max_rd_atomic`.

## Troubleshooting implication (one sentence)

Because these values are fixed once at setup and a QP with a wrong path MTU or a marginal timeout still
reaches RTS and passes small-message tests, "it connected" proves nothing: read the actual negotiated
values (perftest's printed `Mtu` and `GID index` lines, NCCL INFO logs) and test with full-size messages
and sustained load.

Example: a path MTU of 4,096 over a switch port left at MTU 1500 connects fine and then hangs on the
first large message (8.15). A `timeout` of 14 (67 ms) turns a long PFC pause into a fatal
`IBV_WC_RETRY_EXC_ERR` only under load.

## Common mistakes

Placing timeout and retry at INIT→RTR, or path MTU at RTS. Saying the MTU "adapts" after setup: RC QPs
do not renegotiate it.
