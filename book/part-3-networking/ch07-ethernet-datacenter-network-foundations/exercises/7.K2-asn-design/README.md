# 7.K2 — Shared spine ASN, unique leaf ASNs (★, L1)

Type: Knowledge check · kind: `written` · 4 points

## Prompt

<!-- prompt:start -->
**7.K2** ★ L1 — In an RFC 7938 fabric, why do all spines share one ASN while every leaf has a unique
ASN? Describe precisely what goes wrong if two leaves are given the same ASN.
*Evidence required:* the loop-prevention mechanism in one sentence for each half of the question.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/7.K2-asn-design/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
