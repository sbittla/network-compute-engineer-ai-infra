# 8.9 — The price of a lost packet (★★★, L1)

Type: Worked problem · kind: `computed` · 10 points

## Prompt

<!-- prompt:start -->
**8.9 The price of a lost packet** ★★★ · L1
A 1 MiB RDMA WRITE goes from GPU 2 on one ORION node to GPU 5 on another — different rails, so it
crosses a spine (path MTU 4,096; payload ceiling 392 Gb/s; cross-rail round-trip time 5 µs
`[ILLUSTRATIVE]`, docs/REFERENCE_CLUSTER.md). (a) How many packets is the message, and how long
does it take without loss? (b) Under go-back-N, estimate the extra time if packet 50 is lost.
(c) Estimate the extra time if the last packet is lost and `timeout` = 18. (d) With independent
per-packet loss probability 10⁻⁵, estimate the expected goodput of a series of such *isolated*
messages (the QP idles after each) from tail-loss timeouts alone, and say how the answer changes for
back-to-back messages. (e) How long until a QP with `timeout` = 18 and `retry_cnt` = 7 reports
`IBV_WC_RETRY_EXC_ERR` if the peer dies?
*Evidence required:* every step as formula → values → result; bandwidth-delay product computed;
assumptions stated; labelled `[MODELED]`.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 8 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
