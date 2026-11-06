# 8.8 — Wire efficiency and DSCP marking (★★, L1)

Type: Worked problem · kind: `computed` · 8 points

## Prompt

<!-- prompt:start -->
**8.8 Wire efficiency and marking** ★★ · L1
(a) Compute the payload ceiling of a 400 Gb/s RoCEv2 link at a 2,048-byte path MTU when a VLAN tag is
present (IPv4). (b) Compute it at 4,096 bytes over IPv6, untagged. (c) Compute the packet rate at line
rate for case (b). (d) A host is configured with `NCCL_IB_TC=26`. What DSCP and ECN codepoint do its
RoCE packets carry, and in which ORION queue do they land?
*Evidence required:* overhead per packet itemised; formula → substitution → result with units for
each part; DSCP/ECN bit arithmetic shown.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
