# 8.16 — ORION-XL fabric policy (★★★, L1)

Type: Design challenge · kind: `computed` · 20 points

## Prompt

<!-- prompt:start -->
**8.16 ORION-XL fabric policy** ★★★ · L1
Halcyon is building ORION-XL (512 HX8 nodes, 4,096 GPUs, 3-tier Clos; docs/REFERENCE_CLUSTER.md §4).
Choose RoCEv2 or InfiniBand for its backend and specify, with justification: the loss model (lossless
vs lossy, and the NIC capability you depend on), ACK timeout and retry values (with time-to-failure),
path MTU, GID/addressing policy, how the readiness checklist changes at 512 nodes (automation,
sampling, admission gates), and what you would do when a single NIC fails mid-job. Use numbers:
bandwidth-delay product for a 3-tier round trip you state, and the expected cost of tail loss at the
loss rate you design for.
*Evidence required:* decision with criteria; every parameter with its number and label; one
quantified trade-off; one risk you are accepting and how you would detect it in production.
<!-- prompt:end -->

## What to submit

Make the decision against stated criteria and give every parameter with its number and label. Put every deliverable in `outputs/`:

- `outputs/answer.md`
