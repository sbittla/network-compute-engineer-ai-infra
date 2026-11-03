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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
