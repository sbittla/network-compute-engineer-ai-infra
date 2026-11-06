# K10 — From threat model to evidence (★★, L1)

Type: Knowledge check · Kind: `written` · Points: 6

## Prompt

<!-- prompt:start -->
**K10 ★★ L1 — From threat model to evidence.** A tenant's security reviewer asks ORION to prove three
claims: (a) a tenant's pod cannot read another tenant's Secrets; (b) a GPU handed from tenant A to
tenant B holds none of A's data; (c) a retired node's NVMe drives hold no tenant data. For each, name
the asset and threat, the mitigation, and one concrete check with its pass condition (Tables
19.9a–19.9b). Say which check is not read-only and where it may run, and what check (b) cannot prove.
*Evidence required:* a three-row table (claim, mitigation, check, pass condition); one paragraph on the
non-read-only check and the limits of (b).
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
