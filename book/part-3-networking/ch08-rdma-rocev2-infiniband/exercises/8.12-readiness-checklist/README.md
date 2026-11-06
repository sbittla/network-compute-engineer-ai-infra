# 8.12 — Pre-deployment readiness checklist (★★, L1)

Type: Outline-mandated · kind: `written` · 20 points

## Prompt

<!-- prompt:start -->
**8.12 Pre-deployment readiness checklist** ★★ · L1 *(course outline, Chapter 8 exercise 3; part of the
chapter deliverable)*
Create a pre-deployment checklist for an RDMA-capable cluster covering **NIC, firmware, driver,
addressing, MTU, and peer validation** (plus QoS and GPUDirect RDMA). For each item give the command or
data source, the pass criterion, whether it is read-only, and whether your lab validator automates it.
Identify the items that cannot be verified from host captures alone and say how you would get that
evidence.
*Evidence required:* ≥ 15 items with command, criterion, read-only flag, automation flag; switch-side
items identified with an evidence source; ordering justified.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 8 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Give at least 15 items, each with command or data source, pass criterion, read-only flag and automation flag. Put every deliverable in `outputs/`:

- `outputs/checklist.md`
