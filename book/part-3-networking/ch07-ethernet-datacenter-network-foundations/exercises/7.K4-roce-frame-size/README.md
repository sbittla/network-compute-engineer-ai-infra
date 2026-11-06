# 7.K4 — RoCEv2 frame size and the RDMA path MTU (★★, L1)

Type: Knowledge check · kind: `computed` · 4 points

## Prompt

<!-- prompt:start -->
**7.K4** ★★ L1 — Compute the on-the-wire frame size (including FCS) of a RoCEv2 RDMA WRITE first
packet carrying a 4,096-byte payload over IPv4. What RDMA active MTU would a NIC select if its netdev
MTU were 1500, and why does ORION set the host MTU to 9000 when RoCE frames are only about 4.2 KB?
*Evidence required:* a header-by-header sum; the selected MTU with justification.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/7.K4-roce-frame-size/` (instructor material in the full repository; removed from student releases).

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
