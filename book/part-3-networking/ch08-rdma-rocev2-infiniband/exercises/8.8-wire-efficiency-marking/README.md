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

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
