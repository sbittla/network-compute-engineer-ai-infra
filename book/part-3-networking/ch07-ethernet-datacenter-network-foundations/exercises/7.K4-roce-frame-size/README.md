# 7.K4 — RoCEv2 frame size and the RDMA path MTU (★★, L1)

Type: Knowledge check · kind: `computed` · 4 points

## Prompt

<!-- prompt:start -->
**7.K4** ★★ L1 — Compute the on-the-wire frame size (including FCS) of a RoCEv2 RDMA WRITE first
packet carrying a 4,096-byte payload over IPv4. What RDMA active MTU would a NIC select if its netdev
MTU were 1500, and why does ORION set the host MTU to 9000 when RoCE frames are only about 4.2 KB?
*Evidence required:* a header-by-header sum; the selected MTU with justification.
<!-- prompt:end -->

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
