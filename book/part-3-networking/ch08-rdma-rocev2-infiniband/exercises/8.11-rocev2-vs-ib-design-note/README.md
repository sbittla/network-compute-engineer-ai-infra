# 8.11 — RoCEv2 versus InfiniBand design note (★★, L1)

Type: Outline-mandated · kind: `written` · 20 points

## Prompt

<!-- prompt:start -->
**8.11 RoCEv2 versus InfiniBand design note** ★★ · L1 *(course outline, Chapter 8 exercise 2; part of the
chapter deliverable)*
Write a one- to two-page RDMA design note for ORION's backend that compares RoCEv2 and InfiniBand
across **transport, fabric management, operational model, and troubleshooting evidence**, and makes a
recommendation for Halcyon AI. Include: addressing and GID policy, QoS marking (DSCP/TC values with
arithmetic), MTU policy at all three layers, ACK timeout/retry choice with its time-to-failure,
multi-rail failure behaviour, and the three most likely failure signatures for your choice.
*Evidence required:* comparison table with all four dimensions; recommendation tied to stated
criteria; every number labelled; at least one cross-reference to Chapter 9 (congestion) and Chapter 10
(physical layer).
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 8 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write a one- to two-page design note with a comparison table across the four dimensions. Put every deliverable in `outputs/`:

- `outputs/design_note.md`
